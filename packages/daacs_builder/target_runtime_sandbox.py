"""DAACS target runtime sandbox preflight contract.

This module defines the no-call preflight boundary that must sit between a
dry-run RunnerPlan and any future target runtime adapter. It validates
workspace, path, operation, rollback, and live-open readiness contracts without
running DAACS code, spawning subprocesses, writing files, or opening network
connections.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

from packages.core.exposure import sanitize_public_payload
from packages.core.live_open_policy import (
    DAACS_TARGET_RUNTIME_SURFACE,
    LIVE_OPEN_REQUIRED_CONTROLS,
    LiveOpenRequest,
    evaluate_live_open_request,
)
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash

from .runner_provider import is_safe_run_id, safe_public_run_id


TARGET_RUNTIME_PREFLIGHT_VERSION = "target-runtime-preflight-public-v1"
TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT = "target_runtime_disabled_preflight"
CONTRACT_HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")
ABSOLUTE_PATH_PATTERN = re.compile(r"^(?:[A-Za-z]:|/|//)")

BLOCKED_OPERATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("package_install", re.compile(r"\b(?:npm|pnpm|yarn|pip|poetry)\s+(?:install|add)\b", re.I)),
    ("server_start", re.compile(r"\b(?:uvicorn|vite|next\s+dev|npm\s+run\s+dev|flask\s+run)\b", re.I)),
    ("network_call", re.compile(r"\b(?:curl|wget|http://|https://|requests\.|httpx\.|fetch\()\b", re.I)),
    ("subprocess", re.compile(r"\b(?:subprocess|Popen|os\.system|shell=True)\b", re.I)),
    ("cli_agent", re.compile(r"\b(?:codex|claude|gemini)\b", re.I)),
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeSandboxPolicy:
    """Readiness controls for a future DAACS target runtime workspace."""

    approval_policy_ready: bool = False
    replay_persistence_ready: bool = False
    cost_quota_guard_ready: bool = False
    timeout_guard_ready: bool = False
    workspace_sandbox_ready: bool = False
    write_allowlist_ready: bool = False
    rollback_plan_ready: bool = False
    secret_redaction_ready: bool = False
    artifact_sanitizer_ready: bool = False
    audit_projection_ready: bool = False
    timeout_seconds: int | None = None
    max_planned_files: int | None = None
    max_subprocess_calls: int = 0
    max_package_installs: int = 0
    max_server_starts: int = 0
    max_network_calls: int = 0
    max_target_runtime_calls: int = 0


@dataclass(frozen=True, slots=True)
class TargetRuntimeWorkspaceIntent:
    """Run-scoped workspace and planned path envelope."""

    workspace_root: str = ""
    allowed_write_paths: list[str] = field(default_factory=list)
    requested_write_paths: list[str] = field(default_factory=list)
    expected_output_paths: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class TargetRuntimeCommandPolicy:
    """Operation envelope for no-call command policy validation."""

    requested_operations: list[str] = field(default_factory=list)
    allowed_operation_labels: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class TargetRuntimeRollbackPolicy:
    """Rollback/abort evidence required before runtime admission."""

    rollback_plan_id: str = ""
    abort_criteria: list[str] = field(default_factory=list)
    cleanup_steps: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class TargetRuntimePreflightRequest:
    """Hash-only request for DAACS target runtime readiness."""

    run_id: str
    runner_plan_hash: str
    mode: str = TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT
    sandbox_policy: TargetRuntimeSandboxPolicy = field(default_factory=TargetRuntimeSandboxPolicy)
    workspace_intent: TargetRuntimeWorkspaceIntent = field(
        default_factory=TargetRuntimeWorkspaceIntent
    )
    command_policy: TargetRuntimeCommandPolicy = field(default_factory=TargetRuntimeCommandPolicy)
    rollback_policy: TargetRuntimeRollbackPolicy = field(
        default_factory=TargetRuntimeRollbackPolicy
    )
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TargetRuntimePreflightResult:
    """Public-safe target runtime preflight projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    runner_plan_hash: str
    preflight_hash: str
    sandbox_policy_hash: str
    workspace_intent_hash: str
    command_policy_hash: str
    rollback_policy_hash: str
    checks: list[JsonDict]
    path_findings: list[JsonDict]
    operation_findings: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("target runtime preflight projection must be a mapping")
        assert_public_projection_safe(payload)
        return payload


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def _non_negative_int(value: object) -> bool:
    return type(value) is int and value >= 0


def _check(
    checks: list[JsonDict],
    failures: list[str],
    *,
    name: str,
    passed: bool,
    reason: str,
) -> None:
    checks.append({"name": name, "passed": bool(passed), "reason": "" if passed else reason})
    if not passed:
        failures.append(reason)


def _normalize_workspace_path(value: str) -> tuple[str, str]:
    if not isinstance(value, str) or not value.strip():
        return "", "path_missing"
    raw = value.strip().replace("\\", "/")
    if "\x00" in raw:
        return "", "null_byte"
    if ABSOLUTE_PATH_PATTERN.match(raw):
        return "", "absolute_path"
    parts = [part for part in raw.split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        return "", "path_traversal"
    if not parts:
        return "", "path_missing"
    return "/".join(parts), ""


def _under(path: str, prefix: str) -> bool:
    normalized_prefix = prefix.rstrip("/")
    return path == normalized_prefix or path.startswith(f"{normalized_prefix}/")


def _path_finding(*, category: str, reason: str, path_value: str) -> JsonDict:
    return {
        "category": category,
        "reason": reason,
        "path_hash": stable_contract_hash({"path": path_value, "category": category}),
    }


def _operation_finding(*, operation: str, reason: str, operation_value: str) -> JsonDict:
    return {
        "operation": operation,
        "reason": reason,
        "operation_hash": stable_contract_hash(
            {"operation": operation, "value": operation_value}
        ),
    }


def _policy_hash(policy: TargetRuntimeSandboxPolicy) -> str:
    return stable_contract_hash(asdict(policy))


def _workspace_hash(intent: TargetRuntimeWorkspaceIntent) -> str:
    normalized_root, root_reason = _normalize_workspace_path(intent.workspace_root)
    normalized_allowed = [
        _normalize_workspace_path(path)[0]
        for path in intent.allowed_write_paths
        if _normalize_workspace_path(path)[1] == ""
    ]
    return stable_contract_hash(
        {
            "workspace_root": normalized_root if not root_reason else "",
            "allowed_write_path_count": len(normalized_allowed),
            "requested_write_path_count": len(intent.requested_write_paths),
            "expected_output_path_count": len(intent.expected_output_paths),
        }
    )


def _command_hash(policy: TargetRuntimeCommandPolicy) -> str:
    return stable_contract_hash(
        {
            "requested_operation_count": len(policy.requested_operations),
            "allowed_operation_label_count": len(policy.allowed_operation_labels),
            "requested_operation_hashes": [
                stable_contract_hash({"operation": value})
                for value in policy.requested_operations
            ],
        }
    )


def _rollback_hash(policy: TargetRuntimeRollbackPolicy) -> str:
    return stable_contract_hash(
        {
            "rollback_plan_id_present": bool(policy.rollback_plan_id.strip()),
            "abort_criteria_count": len(policy.abort_criteria),
            "cleanup_step_count": len(policy.cleanup_steps),
        }
    )


def _zero_execution_boundary() -> JsonDict:
    return {
        "target_runtime_calls": 0,
        "filesystem_writes": 0,
        "subprocess_calls": 0,
        "package_install_calls": 0,
        "server_start_calls": 0,
        "network_calls": 0,
        "provider_calls": 0,
        "live_api_calls": 0,
        "live_llm_calls": 0,
        "runtime_imports": 0,
        "execution_permission_count": 0,
    }


def _claim_boundary() -> JsonDict:
    return {
        "scope": "target runtime sandbox preflight only",
        "dry_run_runner_remains_source": True,
        "target_runtime_outcome": False,
        "generated_artifact_body": False,
        "hosted_behavior": False,
        "production_trust_claim": False,
    }


def _live_open_decision(request: TargetRuntimePreflightRequest) -> JsonDict:
    policy = request.sandbox_policy
    readiness = {
        field_name: getattr(policy, field_name) is True
        for field_name in LIVE_OPEN_REQUIRED_CONTROLS
    }
    return evaluate_live_open_request(
        LiveOpenRequest(
            run_id=request.run_id,
            surface=DAACS_TARGET_RUNTIME_SURFACE,
            env_key_name="",
            **readiness,
        )
    ).to_dict()


def _path_findings(request: TargetRuntimePreflightRequest) -> tuple[list[JsonDict], JsonDict]:
    intent = request.workspace_intent
    run_id = safe_public_run_id(request.run_id)
    expected_root_prefix = f"runs/{run_id}"
    workspace_root, root_reason = _normalize_workspace_path(intent.workspace_root)
    findings: list[JsonDict] = []

    if root_reason:
        findings.append(
            _path_finding(
                category="workspace_root",
                reason=root_reason,
                path_value=intent.workspace_root,
            )
        )
    elif not _under(workspace_root, expected_root_prefix):
        findings.append(
            _path_finding(
                category="workspace_root",
                reason="workspace_not_run_scoped",
                path_value=workspace_root,
            )
        )

    allowed_paths: list[str] = []
    for path in intent.allowed_write_paths:
        normalized, reason = _normalize_workspace_path(path)
        if reason:
            findings.append(
                _path_finding(category="allowed_write_path", reason=reason, path_value=path)
            )
            continue
        if workspace_root and not _under(normalized, workspace_root):
            findings.append(
                _path_finding(
                    category="allowed_write_path",
                    reason="allowed_path_outside_workspace",
                    path_value=normalized,
                )
            )
            continue
        allowed_paths.append(normalized)

    for path in intent.requested_write_paths:
        normalized, reason = _normalize_workspace_path(path)
        if reason:
            findings.append(
                _path_finding(category="requested_write_path", reason=reason, path_value=path)
            )
            continue
        if workspace_root and not _under(normalized, workspace_root):
            findings.append(
                _path_finding(
                    category="requested_write_path",
                    reason="requested_write_outside_workspace",
                    path_value=normalized,
                )
            )
            continue
        if not any(_under(normalized, allowed_path) for allowed_path in allowed_paths):
            findings.append(
                _path_finding(
                    category="requested_write_path",
                    reason="requested_write_outside_allowlist",
                    path_value=normalized,
                )
            )

    for path in intent.expected_output_paths:
        normalized, reason = _normalize_workspace_path(path)
        if reason:
            findings.append(
                _path_finding(category="expected_output_path", reason=reason, path_value=path)
            )
        elif workspace_root and not _under(normalized, workspace_root):
            findings.append(
                _path_finding(
                    category="expected_output_path",
                    reason="expected_output_outside_workspace",
                    path_value=normalized,
                )
            )

    counts = {
        "allowed_write_path_count": len(allowed_paths),
        "requested_write_path_count": len(intent.requested_write_paths),
        "expected_output_path_count": len(intent.expected_output_paths),
        "denied_path_count": len(findings),
        "path_traversal_block_count": sum(
            1 for finding in findings if finding["reason"] == "path_traversal"
        ),
        "absolute_path_block_count": sum(
            1 for finding in findings if finding["reason"] == "absolute_path"
        ),
        "disallowed_write_block_count": sum(
            1
            for finding in findings
            if finding["reason"]
            in {
                "requested_write_outside_workspace",
                "requested_write_outside_allowlist",
                "allowed_path_outside_workspace",
            }
        ),
    }
    return findings, counts


def _operation_findings(
    request: TargetRuntimePreflightRequest,
) -> tuple[list[JsonDict], JsonDict]:
    findings: list[JsonDict] = []
    for operation_value in request.command_policy.requested_operations:
        value = str(operation_value)
        for operation, pattern in BLOCKED_OPERATION_PATTERNS:
            if pattern.search(value):
                findings.append(
                    _operation_finding(
                        operation=operation,
                        reason=f"{operation}_blocked",
                        operation_value=value,
                    )
                )
                break

    counts = {
        "requested_operation_count": len(request.command_policy.requested_operations),
        "allowed_operation_label_count": len(request.command_policy.allowed_operation_labels),
        "blocked_operation_count": len(findings),
        "package_install_block_count": sum(
            1 for finding in findings if finding["operation"] == "package_install"
        ),
        "server_start_block_count": sum(
            1 for finding in findings if finding["operation"] == "server_start"
        ),
        "network_command_block_count": sum(
            1 for finding in findings if finding["operation"] == "network_call"
        ),
        "subprocess_block_count": sum(
            1 for finding in findings if finding["operation"] == "subprocess"
        ),
        "cli_agent_block_count": sum(
            1 for finding in findings if finding["operation"] == "cli_agent"
        ),
    }
    return findings, counts


def _counts(
    *,
    checks: list[JsonDict],
    path_counts: JsonDict,
    operation_counts: JsonDict,
    rollback_policy: TargetRuntimeRollbackPolicy,
    live_open_status: str,
) -> JsonDict:
    failed_check_count = sum(1 for check in checks if not check["passed"])
    return {
        "preflight_count": 1,
        "comparison_variant_count": 1,
        "check_count": len(checks),
        "failed_check_count": failed_check_count,
        "sandbox_policy_hash_count": 1,
        "workspace_intent_hash_count": 1,
        "command_policy_hash_count": 1,
        "rollback_policy_hash_count": 1,
        "rollback_plan_count": 1 if rollback_policy.rollback_plan_id.strip() else 0,
        "abort_criteria_count": len(rollback_policy.abort_criteria),
        "cleanup_step_count": len(rollback_policy.cleanup_steps),
        "live_open_eligible_count": 1
        if live_open_status == "eligible_for_separate_live_implementation"
        else 0,
        "target_runtime_call_count": 0,
        "filesystem_write_count": 0,
        "subprocess_call_count": 0,
        "network_call_count": 0,
        **path_counts,
        **operation_counts,
    }


class TargetRuntimePreflightService:
    """Fail-closed no-call DAACS target runtime preflight evaluator."""

    def preflight(self, request: TargetRuntimePreflightRequest) -> TargetRuntimePreflightResult:
        checks: list[JsonDict] = []
        failures: list[str] = []
        policy = request.sandbox_policy

        _check(
            checks,
            failures,
            name="mode_disabled_preflight",
            passed=request.mode == TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT,
            reason="target_runtime_mode_invalid",
        )
        _check(
            checks,
            failures,
            name="run_id_safe",
            passed=is_safe_run_id(request.run_id),
            reason="run_id_invalid",
        )
        _check(
            checks,
            failures,
            name="runner_plan_hash_valid",
            passed=isinstance(request.runner_plan_hash, str)
            and CONTRACT_HASH_PATTERN.fullmatch(request.runner_plan_hash) is not None,
            reason="runner_plan_hash_invalid",
        )
        _check(
            checks,
            failures,
            name="timeout_configured",
            passed=_positive_int(policy.timeout_seconds),
            reason="timeout_missing",
        )
        _check(
            checks,
            failures,
            name="planned_file_limit_configured",
            passed=_positive_int(policy.max_planned_files),
            reason="planned_file_limit_missing",
        )
        for field_name in (
            "max_subprocess_calls",
            "max_package_installs",
            "max_server_starts",
            "max_network_calls",
            "max_target_runtime_calls",
        ):
            _check(
                checks,
                failures,
                name=f"{field_name}_zero",
                passed=_non_negative_int(getattr(policy, field_name))
                and getattr(policy, field_name) == 0,
                reason=f"{field_name}_not_zero",
            )

        live_decision = _live_open_decision(request)
        live_open_status = str(live_decision.get("status", "unknown"))
        _check(
            checks,
            failures,
            name="live_open_policy_eligible",
            passed=live_open_status == "eligible_for_separate_live_implementation",
            reason="live_open_policy_not_eligible",
        )

        path_findings, path_counts = _path_findings(request)
        operation_findings, operation_counts = _operation_findings(request)
        _check(
            checks,
            failures,
            name="workspace_intent_run_scoped",
            passed=bool(request.workspace_intent.workspace_root.strip())
            and path_counts["denied_path_count"] == 0,
            reason="workspace_intent_invalid",
        )
        _check(
            checks,
            failures,
            name="write_allowlist_present",
            passed=path_counts["allowed_write_path_count"] > 0,
            reason="write_allowlist_missing",
        )
        _check(
            checks,
            failures,
            name="path_allowlist_clean",
            passed=path_counts["denied_path_count"] == 0,
            reason="path_boundary_violation",
        )
        _check(
            checks,
            failures,
            name="command_policy_clean",
            passed=operation_counts["blocked_operation_count"] == 0,
            reason="blocked_operation_requested",
        )
        _check(
            checks,
            failures,
            name="rollback_plan_present",
            passed=bool(request.rollback_policy.rollback_plan_id.strip()),
            reason="rollback_plan_missing",
        )
        _check(
            checks,
            failures,
            name="abort_criteria_present",
            passed=len(request.rollback_policy.abort_criteria) > 0,
            reason="abort_criteria_missing",
        )
        _check(
            checks,
            failures,
            name="cleanup_steps_present",
            passed=len(request.rollback_policy.cleanup_steps) > 0,
            reason="cleanup_steps_missing",
        )
        _check(
            checks,
            failures,
            name="target_runtime_execution_closed",
            passed=False,
            reason="target_runtime_execution_closed",
        )

        sandbox_policy_hash = _policy_hash(policy)
        workspace_intent_hash = _workspace_hash(request.workspace_intent)
        command_policy_hash = _command_hash(request.command_policy)
        rollback_policy_hash = _rollback_hash(request.rollback_policy)
        preflight_hash = stable_contract_hash(
            {
                "run_id": safe_public_run_id(request.run_id),
                "runner_plan_hash": request.runner_plan_hash,
                "mode": request.mode,
                "sandbox_policy_hash": sandbox_policy_hash,
                "workspace_intent_hash": workspace_intent_hash,
                "command_policy_hash": command_policy_hash,
                "rollback_policy_hash": rollback_policy_hash,
                "path_finding_count": len(path_findings),
                "operation_finding_count": len(operation_findings),
            }
        )
        return TargetRuntimePreflightResult(
            projection_version=TARGET_RUNTIME_PREFLIGHT_VERSION,
            run_id=safe_public_run_id(request.run_id),
            mode=request.mode,
            status="blocked",
            reason=failures[0] if failures else "target_runtime_execution_closed",
            runner_plan_hash=request.runner_plan_hash
            if CONTRACT_HASH_PATTERN.fullmatch(str(request.runner_plan_hash))
            else "",
            preflight_hash=preflight_hash,
            sandbox_policy_hash=sandbox_policy_hash,
            workspace_intent_hash=workspace_intent_hash,
            command_policy_hash=command_policy_hash,
            rollback_policy_hash=rollback_policy_hash,
            checks=checks,
            path_findings=path_findings,
            operation_findings=operation_findings,
            counts=_counts(
                checks=checks,
                path_counts=path_counts,
                operation_counts=operation_counts,
                rollback_policy=request.rollback_policy,
                live_open_status=live_open_status,
            ),
            execution_boundary=_zero_execution_boundary(),
            claim_boundary=_claim_boundary(),
        )


def ready_target_runtime_sandbox_policy(**overrides: Any) -> TargetRuntimeSandboxPolicy:
    """Return explicit ready controls for no-call target runtime preflight tests."""
    fields: dict[str, Any] = {field_name: True for field_name in LIVE_OPEN_REQUIRED_CONTROLS}
    fields.update(
        {
            "timeout_seconds": 60,
            "max_planned_files": 20,
            "max_subprocess_calls": 0,
            "max_package_installs": 0,
            "max_server_starts": 0,
            "max_network_calls": 0,
            "max_target_runtime_calls": 0,
        }
    )
    fields.update(overrides)
    return TargetRuntimeSandboxPolicy(**fields)


def ready_target_runtime_workspace_intent(run_id: str) -> TargetRuntimeWorkspaceIntent:
    workspace_root = f"runs/{run_id}/workspace"
    return TargetRuntimeWorkspaceIntent(
        workspace_root=workspace_root,
        allowed_write_paths=[
            f"{workspace_root}/backend",
            f"{workspace_root}/frontend",
            f"{workspace_root}/reports",
        ],
        requested_write_paths=[
            f"{workspace_root}/backend/main.py",
            f"{workspace_root}/frontend/App.tsx",
            f"{workspace_root}/reports/verification.json",
        ],
        expected_output_paths=[
            f"{workspace_root}/backend",
            f"{workspace_root}/frontend",
            f"{workspace_root}/reports",
        ],
    )


def ready_target_runtime_command_policy() -> TargetRuntimeCommandPolicy:
    return TargetRuntimeCommandPolicy(
        requested_operations=["render backend files", "render frontend files", "render report"],
        allowed_operation_labels=["render_backend", "render_frontend", "render_report"],
    )


def ready_target_runtime_rollback_policy() -> TargetRuntimeRollbackPolicy:
    return TargetRuntimeRollbackPolicy(
        rollback_plan_id="rollback-local-target-runtime-preflight",
        abort_criteria=[
            "any path boundary finding",
            "any non-zero side-effect counter",
        ],
        cleanup_steps=[
            "discard run-scoped workspace",
            "keep sanitized audit projection only",
        ],
    )


def default_target_runtime_preflight_service() -> TargetRuntimePreflightService:
    return TargetRuntimePreflightService()


__all__ = [
    "TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT",
    "TARGET_RUNTIME_PREFLIGHT_VERSION",
    "TargetRuntimeCommandPolicy",
    "TargetRuntimePreflightRequest",
    "TargetRuntimePreflightResult",
    "TargetRuntimePreflightService",
    "TargetRuntimeRollbackPolicy",
    "TargetRuntimeSandboxPolicy",
    "TargetRuntimeWorkspaceIntent",
    "default_target_runtime_preflight_service",
    "ready_target_runtime_command_policy",
    "ready_target_runtime_rollback_policy",
    "ready_target_runtime_sandbox_policy",
    "ready_target_runtime_workspace_intent",
]

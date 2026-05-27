"""Gated fake live runner boundary.

This module intentionally connects only a fake runtime. It does not import
DAACS runtime modules, LLM providers, subprocess helpers, package installers,
servers, or filesystem writers.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from packages.core.pathing import PathBoundaryError, normalize_public_relative_path
from packages.core.schemas import VerificationReport, stable_contract_hash

from .offline_runner import DAACSOfflineRunner
from .runner_provider import (
    ApprovalRecord,
    RunnerRequest,
    RunnerResult,
    is_safe_run_id,
    safe_public_run_id,
)


FAKE_LIVE_OPERATION = "fake_runtime"

LIVE_LIMIT_FIELDS = (
    "max_provider_calls",
    "max_subprocess_calls",
    "max_package_installs",
    "max_server_starts",
    "max_files_written",
)

LIVE_POLICY_FLAGS = (
    "allow_provider_calls",
    "allow_cli_agent",
    "allow_subprocess",
    "allow_package_install",
    "allow_server_start",
    "allow_filesystem_write",
    "allow_network",
)

ZERO_FAKE_LIVE_SIDE_EFFECTS: dict[str, int] = {
    "live_llm_calls": 0,
    "live_api_calls": 0,
    "provider_calls": 0,
    "cli_agent_invocations": 0,
    "subprocess_calls": 0,
    "package_install_calls": 0,
    "server_start_calls": 0,
    "filesystem_writes": 0,
    "provider_imports": 0,
    "network_calls": 0,
    "approval_bypass_count": 0,
}

ZERO_FAKE_LIVE_RUNTIME_METRICS: dict[str, int] = {
    "fake_live_runtime_invocations": 0,
    "real_daacs_invocations": 0,
    "solar_provider_calls": 0,
    "executed_action_count": 0,
}


def _metrics(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        **ZERO_FAKE_LIVE_SIDE_EFFECTS,
        **ZERO_FAKE_LIVE_RUNTIME_METRICS,
        "boundary_mode": "live",
        **(extra or {}),
    }


def _parse_aware_timestamp(
    value: str,
    *,
    field_name: str,
    failures: list[tuple[str, str]],
) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        failures.append(("live_approval_valid", f"{field_name} is required."))
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        failures.append(("live_approval_valid", f"{field_name} must be ISO-8601."))
        return None
    if parsed.tzinfo is None:
        failures.append(("live_approval_valid", f"{field_name} must include timezone."))
        return None
    return parsed.astimezone(timezone.utc)


def _validate_workspace(
    approval: ApprovalRecord,
    request: RunnerRequest,
    failures: list[tuple[str, str]],
) -> None:
    if not is_safe_run_id(request.run_id):
        return
    expected_prefix = f"runs/{request.run_id}"
    try:
        approval_workspace = normalize_public_relative_path(approval.workspace_root)
    except (PathBoundaryError, ValueError):
        failures.append(("live_workspace_valid", "approval workspace_root must be a safe relative path."))
        return

    if approval_workspace != expected_prefix and not approval_workspace.startswith(
        f"{expected_prefix}/"
    ):
        failures.append(("live_workspace_valid", "approval workspace_root must stay inside the run workspace."))

    if not isinstance(request.policy.workspace_root, str) or not request.policy.workspace_root.strip():
        failures.append(("live_workspace_valid", "runner policy workspace_root is required for live mode."))
        return
    try:
        policy_workspace = normalize_public_relative_path(request.policy.workspace_root)
    except (PathBoundaryError, ValueError):
        failures.append(("live_workspace_valid", "runner policy workspace_root must be a safe relative path."))
        return

    if policy_workspace != approval_workspace:
        failures.append(("live_workspace_valid", "approval and policy workspace roots must match."))


def _validate_approval(
    request: RunnerRequest,
    failures: list[tuple[str, str]],
) -> None:
    approval = request.approval
    if not isinstance(approval, ApprovalRecord):
        failures.append(("live_approval_valid", "live runner requires ApprovalRecord approval."))
        return

    if not isinstance(approval.approved_by, str) or not approval.approved_by.strip():
        failures.append(("live_approval_valid", "approved_by is required."))
    if approval.run_id != request.run_id:
        failures.append(("live_approval_valid", "approval run_id must match the request run_id."))
    if approval.mode != "live":
        failures.append(("live_approval_valid", "approval mode must be live."))

    allowed_operations_valid = (
        isinstance(approval.allowed_operations, list)
        and all(isinstance(item, str) for item in approval.allowed_operations)
        and set(approval.allowed_operations) == {FAKE_LIVE_OPERATION}
    )
    if not allowed_operations_valid:
        failures.append(("live_approval_valid", "allowed_operations must allow only fake_runtime."))

    for field_name in LIVE_LIMIT_FIELDS:
        value = getattr(approval, field_name)
        if type(value) is not int or value != 0:
            failures.append(("live_approval_valid", f"{field_name} must be explicit zero."))

    approved_at = _parse_aware_timestamp(
        approval.approved_at,
        field_name="approved_at",
        failures=failures,
    )
    expires_at = _parse_aware_timestamp(
        approval.expires_at,
        field_name="expires_at",
        failures=failures,
    )
    if approved_at is not None and expires_at is not None:
        if expires_at <= approved_at:
            failures.append(("live_approval_valid", "expires_at must be after approved_at."))
        if expires_at <= datetime.now(timezone.utc):
            failures.append(("live_approval_valid", "approval is expired."))

    if not isinstance(approval.rollback_plan_id, str) or not approval.rollback_plan_id.strip():
        failures.append(("live_rollback_configured", "rollback_plan_id is required."))
    if not isinstance(approval.audit_log_id, str) or not approval.audit_log_id.strip():
        failures.append(("live_audit_configured", "audit_log_id is required."))

    _validate_workspace(approval, request, failures)


def _validate_policy(request: RunnerRequest, failures: list[tuple[str, str]]) -> None:
    for flag in LIVE_POLICY_FLAGS:
        if bool(getattr(request.policy, flag)):
            failures.append(("live_policy_fake_only", f"{flag} must stay disabled for fake live mode."))


def _validate_dry_run_plan(request: RunnerRequest, failures: list[tuple[str, str]]) -> None:
    plan = request.plan
    if plan is None:
        failures.append(("dry_run_plan_present", "dry-run RunnerPlan is required before fake live mode."))
        return

    try:
        plan.validate()
    except ValueError as exc:
        failures.append(("dry_run_plan_valid", str(exc)))
        return

    if plan.run_id != request.run_id:
        failures.append(("dry_run_plan_valid", "RunnerPlan run_id must match the request run_id."))
    if not any(item.get("approval_type") == "live_runner" for item in plan.required_approvals):
        failures.append(("dry_run_plan_valid", "RunnerPlan must request live_runner approval."))
    if request.state.get("spec_approval_status") != "approved":
        failures.append(("dry_run_plan_valid", "approved BuildSpec state is required before live mode."))
    if request.state.get("implementation_brief_hash") != plan.implementation_brief_hash:
        failures.append(("dry_run_plan_valid", "RunnerPlan implementation brief hash must match state."))
    if request.state.get("approved_build_spec_hash") != plan.build_spec_hash:
        failures.append(("dry_run_plan_valid", "RunnerPlan BuildSpec hash must match approved state."))


def validate_fake_live_request(request: RunnerRequest) -> list[tuple[str, str]]:
    """Return sanitized gate failures for fake live admission."""
    failures: list[tuple[str, str]] = []
    if not is_safe_run_id(request.run_id):
        failures.append(("live_run_id_valid", "run_id contains unsupported characters."))
    _validate_approval(request, failures)
    _validate_policy(request, failures)
    _validate_dry_run_plan(request, failures)
    return failures


def _blocked_result(
    *,
    request: RunnerRequest,
    failures: list[tuple[str, str]],
    extra_metrics: dict[str, Any] | None = None,
) -> RunnerResult:
    check_name = failures[0][0] if failures else "fake_live_runner_blocked"
    errors = [message for _, message in failures] or ["fake live runner blocked."]
    report_run_id = safe_public_run_id(request.run_id)
    report = VerificationReport(
        run_id=report_run_id,
        passed=False,
        checks=[{"name": check_name, "passed": False}],
        errors=errors,
        generated_files=[],
        metrics=_metrics(
            {
                "runner_admission_block_count": 1,
                "approval_validation_failure_count": 1,
                **(extra_metrics or {}),
            }
        ),
    )
    return RunnerResult(
        run_id=report_run_id,
        mode="live",
        status="blocked",
        verification_report=report,
        artifact_manifest=[],
        audit_events=[
            {
                "event": "fake_live_blocked",
                "run_id": report_run_id,
                "failed_gate": check_name,
                "side_effects": ZERO_FAKE_LIVE_SIDE_EFFECTS,
            }
        ],
    )


class FakeLiveRuntime:
    """Runtime stub that records admission evidence without external effects."""

    name = "fake_live_runtime"

    def run(
        self,
        *,
        request: RunnerRequest,
        approval_hash: str,
        state_hash: str,
        plan_hash: str,
    ) -> dict[str, Any]:
        return {
            "runtime": self.name,
            "run_id": request.run_id,
            "approval_hash": approval_hash,
            "state_hash": state_hash,
            "plan_hash": plan_hash,
            "real_daacs_invocations": 0,
            "solar_provider_calls": 0,
            "executed_action_count": 0,
            "generated_file_count": 0,
        }


class LiveRunnerProvider:
    """Live provider skeleton that admits only a fake runtime."""

    mode = "live"

    def __init__(
        self,
        *,
        runtime: FakeLiveRuntime | None = None,
        offline_runner: DAACSOfflineRunner | None = None,
    ) -> None:
        self.runtime = runtime or FakeLiveRuntime()
        self.offline_runner = offline_runner or DAACSOfflineRunner()

    def run(self, request: RunnerRequest) -> RunnerResult:
        failures = validate_fake_live_request(request)
        if failures:
            return _blocked_result(
                request=request,
                failures=failures,
                extra_metrics={"approval_bypass_count": 1},
            )

        offline_report = self.offline_runner.run(request.state)
        if not offline_report.passed:
            return _blocked_result(
                request=request,
                failures=[
                    (
                        "offline_state_contract_passed",
                        "approved state must pass offline contract checks before fake live mode.",
                    )
                ],
                extra_metrics={
                    "offline_state_rejection_count": 1,
                    "approval_bypass_count": 0,
                },
            )

        approval_payload = asdict(request.approval)
        plan_payload = request.plan.to_dict() if request.plan is not None else {}
        approval_hash = stable_contract_hash(approval_payload)
        state_hash = stable_contract_hash(
            {
                "run_id": request.run_id,
                "state": request.state,
            }
        )
        plan_hash = str(plan_payload["plan_hash"])
        runtime_evidence = self.runtime.run(
            request=request,
            approval_hash=approval_hash,
            state_hash=state_hash,
            plan_hash=plan_hash,
        )
        metrics = _metrics(
            {
                "fake_live_runtime_invocations": 1,
                "dry_run_plan_verified_count": 1,
                "rollback_plan_configured_count": 1,
                "audit_log_configured_count": 1,
                "fake_runtime_evidence_count": 1,
                "planned_action_count": len(request.plan.planned_actions)
                if request.plan is not None
                else 0,
            }
        )
        report = VerificationReport(
            run_id=request.run_id,
            passed=True,
            checks=[
                {"name": "live_approval_valid", "passed": True},
                {"name": "live_workspace_valid", "passed": True},
                {"name": "live_policy_fake_only", "passed": True},
                {"name": "dry_run_plan_present", "passed": True},
                {"name": "dry_run_plan_valid", "passed": True},
                {"name": "offline_state_contract_passed", "passed": True},
                {"name": "fake_runtime_only", "passed": True},
                {"name": "side_effects_zero", "passed": True},
            ],
            errors=[],
            generated_files=[],
            metrics=metrics,
        )
        return RunnerResult(
            run_id=request.run_id,
            mode="live",
            status="passed",
            verification_report=report,
            plan=request.plan,
            artifact_manifest=[],
            audit_events=[
                {
                    "event": "fake_live_runtime_verified",
                    "run_id": request.run_id,
                    "approval_hash": approval_hash,
                    "state_hash": state_hash,
                    "plan_hash": plan_hash,
                    "runtime": runtime_evidence["runtime"],
                    "side_effects": ZERO_FAKE_LIVE_SIDE_EFFECTS,
                }
            ],
        )

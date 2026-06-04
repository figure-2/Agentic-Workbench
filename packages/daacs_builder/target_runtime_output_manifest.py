"""Disabled DAACS target runtime output manifest contract.

This module defines the no-call evidence shape for future target runtime
outputs. It never writes generated files, stores source bodies, starts servers,
spawns subprocesses, imports provider SDKs, or opens network connections.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import re

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys, sanitize_public_payload
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash

from .runner_provider import is_safe_run_id, safe_public_run_id
from .target_runtime_admission_store import (
    target_runtime_adapter_admission_public_read_model,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_OUTPUT_MANIFEST_VERSION = "target-runtime-output-manifest-public-v1"
TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED = (
    "target_runtime_disabled_output_manifest"
)
TARGET_RUNTIME_OUTPUT_GROUP_LABELS = (
    "backend",
    "frontend",
    "verification_report",
)
OUTPUT_GROUP_LABEL_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


@dataclass(frozen=True, slots=True)
class TargetRuntimeOutputManifestRequest:
    """Hash-only request for disabled target runtime output manifest evidence."""

    run_id: str
    runner_plan_hash: str
    adapter_admission_hash: str
    adapter_admission_read_model: JsonDict = field(default_factory=dict)
    output_groups: list[JsonDict] = field(default_factory=list)
    mode: str = TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TargetRuntimeOutputManifestResult:
    """Public-safe disabled target runtime output manifest projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    runner_plan_hash: str
    adapter_admission_hash: str
    adapter_admission_read_model_hash: str
    output_manifest_hash: str
    output_groups: list[JsonDict]
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("target runtime output manifest must be a mapping")
        _assert_projection_safe(payload)
        return payload


def _is_contract_hash(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


def _as_int(value: object) -> int:
    if type(value) is int and value >= 0:
        return value
    return 0


def _zero_execution_boundary() -> JsonDict:
    return {
        "target_runtime_calls": 0,
        "filesystem_writes": 0,
        "subprocess_calls": 0,
        "network_calls": 0,
        "package_install_calls": 0,
        "server_start_calls": 0,
        "provider_calls": 0,
        "live_api_calls": 0,
        "execution_permission_count": 0,
        "generated_artifact_body_write_count": 0,
    }


def _claim_boundary() -> JsonDict:
    return {
        "scope": "disabled target runtime output manifest contract only",
        "adapter_admission_read_model_required": True,
        "target_runtime_outcome": False,
        "generated_artifact_body": False,
        "generated_file_content": False,
        "source_body": False,
        "hosted_behavior": False,
        "production_trust_claim": False,
    }


def _assert_projection_safe(value: JsonDict) -> None:
    public = sanitize_public_payload(value)
    if not isinstance(public, dict):
        raise ValueError("target runtime output manifest projection must be a mapping")
    if find_forbidden_public_keys(public):
        raise ValueError("target runtime output manifest contains forbidden public keys")
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError("target runtime output manifest contains forbidden claims")
    assert_public_projection_safe(public)


def _default_output_groups() -> list[JsonDict]:
    groups: list[JsonDict] = []
    for label in TARGET_RUNTIME_OUTPUT_GROUP_LABELS:
        group = {
            "label": label,
            "expected_artifact_kind": label,
            "expected_file_count": 0,
            "body_included": False,
            "path_included": False,
            "group_hash": stable_contract_hash(
                {
                    "label": label,
                    "expected_artifact_kind": label,
                    "expected_file_count": 0,
                }
            ),
        }
        groups.append(group)
    return groups


def _safe_output_groups(value: list[JsonDict]) -> list[JsonDict]:
    if not value:
        return _default_output_groups()
    groups: list[JsonDict] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError("target runtime output group must be a mapping")
        label = str(item.get("label", "")).strip().lower()
        if not OUTPUT_GROUP_LABEL_PATTERN.fullmatch(label):
            raise ValueError("target runtime output group label is unsafe")
        expected_artifact_kind = str(
            item.get("expected_artifact_kind", label)
        ).strip().lower()
        if not OUTPUT_GROUP_LABEL_PATTERN.fullmatch(expected_artifact_kind):
            raise ValueError("target runtime output group kind is unsafe")
        expected_file_count = _as_int(item.get("expected_file_count", 0))
        group = {
            "label": label,
            "expected_artifact_kind": expected_artifact_kind,
            "expected_file_count": expected_file_count,
            "body_included": False,
            "path_included": False,
            "group_hash": stable_contract_hash(
                {
                    "label": label,
                    "expected_artifact_kind": expected_artifact_kind,
                    "expected_file_count": expected_file_count,
                    "index": index,
                }
            ),
        }
        groups.append(group)
    if len({group["label"] for group in groups}) != len(groups):
        raise ValueError("target runtime output group labels must be unique")
    return groups


def _adapter_read_model_hash(read_model: JsonDict) -> str:
    sanitized = sanitize_public_payload(read_model)
    if not isinstance(sanitized, dict):
        return ""
    _assert_projection_safe(sanitized)
    return stable_contract_hash(sanitized)


def _adapter_read_model_counts(read_model: JsonDict) -> JsonDict:
    counts = read_model.get("counts", {})
    return counts if isinstance(counts, dict) else {}


def _adapter_read_model_execution(read_model: JsonDict) -> JsonDict:
    execution = read_model.get("execution_boundary", {})
    return execution if isinstance(execution, dict) else {}


def _adapter_admissions(read_model: JsonDict) -> list[JsonDict]:
    admissions = read_model.get("adapter_admissions", [])
    return admissions if isinstance(admissions, list) else []


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


def _counts(
    *,
    checks: list[JsonDict],
    read_model: JsonDict,
    output_groups: list[JsonDict],
    adapter_hash_match_count: int,
) -> JsonDict:
    read_counts = _adapter_read_model_counts(read_model)
    failed_check_count = sum(1 for check in checks if not check["passed"])
    return {
        "output_manifest_count": 1,
        "comparison_variant_count": 1,
        "check_count": len(checks),
        "failed_check_count": failed_check_count,
        "adapter_admission_read_model_count": 1 if read_model else 0,
        "adapter_admission_record_count": _as_int(
            read_counts.get("adapter_admission_record_count")
        ),
        "adapter_admission_hash_count": _as_int(
            read_counts.get("adapter_admission_hash_count")
        ),
        "adapter_admission_hash_match_count": adapter_hash_match_count,
        "output_group_count": len(output_groups),
        "output_group_hash_count": len({group["group_hash"] for group in output_groups}),
        "generated_artifact_body_write_count": 0,
        "target_runtime_call_count": 0,
        "filesystem_write_count": 0,
        "subprocess_call_count": 0,
        "network_call_count": 0,
        "execution_permission_count": 0,
    }


def _hash_for_manifest(
    *,
    request: TargetRuntimeOutputManifestRequest,
    read_model_hash: str,
    output_groups: list[JsonDict],
    status: str,
    reason: str,
    failed_check_count: int,
) -> str:
    return stable_contract_hash(
        {
            "projection_version": TARGET_RUNTIME_OUTPUT_MANIFEST_VERSION,
            "run_id": safe_public_run_id(request.run_id),
            "mode": request.mode,
            "runner_plan_hash": request.runner_plan_hash,
            "adapter_admission_hash": request.adapter_admission_hash,
            "adapter_admission_read_model_hash": read_model_hash,
            "output_group_hashes": [group["group_hash"] for group in output_groups],
            "status": status,
            "reason": reason,
            "failed_check_count": failed_check_count,
        }
    )


def _result(
    *,
    request: TargetRuntimeOutputManifestRequest,
    status: str,
    reason: str,
    checks: list[JsonDict],
    output_groups: list[JsonDict],
    read_model_hash: str,
    adapter_hash_match_count: int = 0,
) -> TargetRuntimeOutputManifestResult:
    failed_check_count = sum(1 for check in checks if not check["passed"])
    output_manifest_hash = _hash_for_manifest(
        request=request,
        read_model_hash=read_model_hash,
        output_groups=output_groups,
        status=status,
        reason=reason,
        failed_check_count=failed_check_count,
    )
    return TargetRuntimeOutputManifestResult(
        projection_version=TARGET_RUNTIME_OUTPUT_MANIFEST_VERSION,
        run_id=safe_public_run_id(request.run_id),
        mode=request.mode,
        status=status,
        reason=reason,
        runner_plan_hash=request.runner_plan_hash
        if _is_contract_hash(request.runner_plan_hash)
        else "",
        adapter_admission_hash=request.adapter_admission_hash
        if _is_contract_hash(request.adapter_admission_hash)
        else "",
        adapter_admission_read_model_hash=read_model_hash
        if _is_contract_hash(read_model_hash)
        else "",
        output_manifest_hash=output_manifest_hash,
        output_groups=output_groups,
        checks=checks,
        counts=_counts(
            checks=checks,
            read_model=request.adapter_admission_read_model,
            output_groups=output_groups,
            adapter_hash_match_count=adapter_hash_match_count,
        ),
        execution_boundary=_zero_execution_boundary(),
        claim_boundary=_claim_boundary(),
    )


class TargetRuntimeOutputManifestService:
    """Build a disabled output manifest after adapter admission evidence exists."""

    def build(
        self,
        request: TargetRuntimeOutputManifestRequest,
    ) -> TargetRuntimeOutputManifestResult:
        read_model = (
            request.adapter_admission_read_model
            if isinstance(request.adapter_admission_read_model, dict)
            else {}
        )
        output_groups = _safe_output_groups(request.output_groups)
        read_model_hash = _adapter_read_model_hash(read_model) if read_model else ""
        read_counts = _adapter_read_model_counts(read_model)
        read_execution = _adapter_read_model_execution(read_model)
        admissions = _adapter_admissions(read_model)
        adapter_hashes = {
            str(admission.get("adapter_admission_hash", ""))
            for admission in admissions
            if isinstance(admission, dict)
        }
        adapter_hash_match = (
            _is_contract_hash(request.adapter_admission_hash)
            and request.adapter_admission_hash in adapter_hashes
        )
        checks: list[JsonDict] = []
        failures: list[str] = []

        _check(
            checks,
            failures,
            name="output_manifest_mode_disabled",
            passed=request.mode == TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
            reason="target_runtime_output_manifest_mode_invalid",
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
            passed=_is_contract_hash(request.runner_plan_hash),
            reason="runner_plan_hash_invalid",
        )
        _check(
            checks,
            failures,
            name="adapter_admission_hash_valid",
            passed=_is_contract_hash(request.adapter_admission_hash),
            reason="adapter_admission_hash_invalid",
        )
        _check(
            checks,
            failures,
            name="adapter_admission_read_model_present",
            passed=bool(read_model),
            reason="adapter_admission_read_model_missing",
        )
        _check(
            checks,
            failures,
            name="adapter_admission_read_model_version",
            passed=read_model.get("projection_version")
            == "target-runtime-adapter-admission-read-model-public-v1",
            reason="adapter_admission_read_model_version_invalid",
        )
        _check(
            checks,
            failures,
            name="adapter_admission_read_model_available",
            passed=read_model.get("status") == "available",
            reason="adapter_admission_read_model_unavailable",
        )
        _check(
            checks,
            failures,
            name="adapter_admission_read_model_run_matches",
            passed=read_model.get("run_id") == safe_public_run_id(request.run_id),
            reason="adapter_admission_read_model_run_mismatch",
        )
        _check(
            checks,
            failures,
            name="adapter_admission_read_model_has_record",
            passed=_as_int(read_counts.get("adapter_admission_record_count")) >= 1,
            reason="adapter_admission_read_model_record_missing",
        )
        _check(
            checks,
            failures,
            name="adapter_admission_hash_matches_read_model",
            passed=adapter_hash_match,
            reason="adapter_admission_hash_mismatch",
        )
        _check(
            checks,
            failures,
            name="adapter_admission_read_model_zero_call_boundary",
            passed=_as_int(read_execution.get("target_runtime_calls")) == 0
            and _as_int(read_execution.get("filesystem_writes")) == 0
            and _as_int(read_execution.get("subprocess_calls")) == 0
            and _as_int(read_execution.get("network_calls")) == 0
            and _as_int(read_counts.get("execution_permission_count")) == 0,
            reason="adapter_admission_read_model_zero_call_boundary_invalid",
        )
        _check(
            checks,
            failures,
            name="output_groups_present",
            passed=len(output_groups) >= 3,
            reason="output_groups_missing",
        )
        _check(
            checks,
            failures,
            name="output_groups_hash_only",
            passed=all(
                group.get("body_included") is False
                and group.get("path_included") is False
                and _is_contract_hash(group.get("group_hash"))
                for group in output_groups
            ),
            reason="output_groups_not_hash_only",
        )

        status = "blocked"
        reason = failures[0] if failures else "target_runtime_output_manifest_execution_closed"
        return _result(
            request=request,
            status=status,
            reason=reason,
            checks=checks,
            output_groups=output_groups,
            read_model_hash=read_model_hash,
            adapter_hash_match_count=1 if adapter_hash_match else 0,
        )


def default_target_runtime_output_manifest_service() -> TargetRuntimeOutputManifestService:
    return TargetRuntimeOutputManifestService()


def build_disabled_target_runtime_output_manifest(
    *,
    request: TargetRuntimeOutputManifestRequest,
    service: TargetRuntimeOutputManifestService | None = None,
) -> TargetRuntimeOutputManifestResult:
    """Build the disabled output manifest projection without runtime execution."""
    selected_service = service or default_target_runtime_output_manifest_service()
    return selected_service.build(request)


def build_disabled_target_runtime_output_manifest_from_repository(
    *,
    repository,
    run_id: str,
    runner_plan_hash: str,
    adapter_admission_hash: str,
    output_groups: list[JsonDict] | None = None,
) -> TargetRuntimeOutputManifestResult:
    read_model = target_runtime_adapter_admission_public_read_model(
        repository,
        run_id=run_id,
    )
    request = TargetRuntimeOutputManifestRequest(
        run_id=run_id,
        runner_plan_hash=runner_plan_hash,
        adapter_admission_hash=adapter_admission_hash,
        adapter_admission_read_model=read_model,
        output_groups=output_groups or [],
    )
    return build_disabled_target_runtime_output_manifest(request=request)


__all__ = [
    "TARGET_RUNTIME_OUTPUT_GROUP_LABELS",
    "TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED",
    "TARGET_RUNTIME_OUTPUT_MANIFEST_VERSION",
    "TargetRuntimeOutputManifestRequest",
    "TargetRuntimeOutputManifestResult",
    "TargetRuntimeOutputManifestService",
    "build_disabled_target_runtime_output_manifest",
    "build_disabled_target_runtime_output_manifest_from_repository",
    "default_target_runtime_output_manifest_service",
]

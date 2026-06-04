"""Disabled DAACS target runtime adapter admission boundary.

This module wires the hash-only target runtime preflight projection to a
future adapter entrance without executing the adapter runtime. It validates
that preflight evidence exists, matches the expected hash, and preserves the
zero-call boundary before returning a blocked disabled-adapter projection.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol

from packages.core.exposure import sanitize_public_payload
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash

from .runner_provider import is_safe_run_id, safe_public_run_id
from .target_runtime_sandbox import (
    CONTRACT_HASH_PATTERN,
    TARGET_RUNTIME_PREFLIGHT_VERSION,
)


TARGET_RUNTIME_ADAPTER_ADMISSION_VERSION = "target-runtime-adapter-admission-public-v1"
TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION = (
    "target_runtime_disabled_adapter_admission"
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeAdapterAdmissionRequest:
    """Hash-only request for disabled target runtime adapter admission."""

    run_id: str
    runner_plan_hash: str
    expected_preflight_hash: str
    preflight_projection: JsonDict = field(default_factory=dict)
    mode: str = TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TargetRuntimeAdapterAdmissionResult:
    """Public-safe admission or disabled-adapter projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    runner_plan_hash: str
    expected_preflight_hash: str
    preflight_hash: str
    adapter_admission_hash: str
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("target runtime adapter admission projection must be a mapping")
        assert_public_projection_safe(payload)
        return payload


class TargetRuntimeAdapter(Protocol):
    """Minimal disabled adapter shape used by the admission wrapper."""

    def invoke(
        self,
        request: TargetRuntimeAdapterAdmissionRequest,
        admission: TargetRuntimeAdapterAdmissionResult,
    ) -> TargetRuntimeAdapterAdmissionResult:
        ...


def _is_contract_hash(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


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
        "scope": "disabled target runtime adapter admission only",
        "preflight_required": True,
        "target_runtime_outcome": False,
        "generated_artifact_body": False,
        "hosted_behavior": False,
        "production_trust_claim": False,
    }


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


def _projection_counts(preflight_projection: JsonDict) -> JsonDict:
    counts = preflight_projection.get("counts", {})
    if not isinstance(counts, dict):
        counts = {}
    execution = preflight_projection.get("execution_boundary", {})
    if not isinstance(execution, dict):
        execution = {}
    return {
        "preflight_projection_count": 1 if preflight_projection else 0,
        "preflight_check_count": int(counts.get("check_count", 0))
        if type(counts.get("check_count", 0)) is int
        else 0,
        "preflight_failed_check_count": int(counts.get("failed_check_count", 0))
        if type(counts.get("failed_check_count", 0)) is int
        else 0,
        "preflight_denied_path_count": int(counts.get("denied_path_count", 0))
        if type(counts.get("denied_path_count", 0)) is int
        else 0,
        "preflight_blocked_operation_count": int(counts.get("blocked_operation_count", 0))
        if type(counts.get("blocked_operation_count", 0)) is int
        else 0,
        "preflight_execution_permission_count": int(
            execution.get("execution_permission_count", 0)
        )
        if type(execution.get("execution_permission_count", 0)) is int
        else 0,
        "preflight_target_runtime_call_count": int(execution.get("target_runtime_calls", 0))
        if type(execution.get("target_runtime_calls", 0)) is int
        else 0,
        "preflight_filesystem_write_count": int(execution.get("filesystem_writes", 0))
        if type(execution.get("filesystem_writes", 0)) is int
        else 0,
        "preflight_subprocess_call_count": int(execution.get("subprocess_calls", 0))
        if type(execution.get("subprocess_calls", 0)) is int
        else 0,
        "preflight_network_call_count": int(execution.get("network_calls", 0))
        if type(execution.get("network_calls", 0)) is int
        else 0,
    }


def _counts(
    *,
    checks: list[JsonDict],
    preflight_projection: JsonDict,
    hash_match_count: int,
    adapter_reach_count: int,
    block_count: int,
) -> JsonDict:
    failed_check_count = sum(1 for check in checks if not check["passed"])
    return {
        "adapter_admission_count": 1,
        "comparison_variant_count": 1,
        "check_count": len(checks),
        "failed_check_count": failed_check_count,
        "preflight_hash_required_count": 1,
        "preflight_hash_match_count": hash_match_count,
        "adapter_reach_count": adapter_reach_count,
        "adapter_disabled_block_count": block_count,
        "target_runtime_call_count": 0,
        "filesystem_write_count": 0,
        "subprocess_call_count": 0,
        "network_call_count": 0,
        "execution_permission_count": 0,
        **_projection_counts(preflight_projection),
    }


def _hash_for_request(
    *,
    request: TargetRuntimeAdapterAdmissionRequest,
    preflight_hash: str,
    status: str,
    reason: str,
    failed_check_count: int,
) -> str:
    return stable_contract_hash(
        {
            "projection_version": TARGET_RUNTIME_ADAPTER_ADMISSION_VERSION,
            "run_id": safe_public_run_id(request.run_id),
            "mode": request.mode,
            "runner_plan_hash": request.runner_plan_hash,
            "expected_preflight_hash": request.expected_preflight_hash,
            "preflight_hash": preflight_hash,
            "status": status,
            "reason": reason,
            "failed_check_count": failed_check_count,
        }
    )


def _result(
    *,
    request: TargetRuntimeAdapterAdmissionRequest,
    status: str,
    reason: str,
    checks: list[JsonDict],
    preflight_hash: str = "",
    hash_match_count: int = 0,
    adapter_reach_count: int = 0,
    block_count: int = 1,
) -> TargetRuntimeAdapterAdmissionResult:
    failed_check_count = sum(1 for check in checks if not check["passed"])
    adapter_admission_hash = _hash_for_request(
        request=request,
        preflight_hash=preflight_hash,
        status=status,
        reason=reason,
        failed_check_count=failed_check_count,
    )
    return TargetRuntimeAdapterAdmissionResult(
        projection_version=TARGET_RUNTIME_ADAPTER_ADMISSION_VERSION,
        run_id=safe_public_run_id(request.run_id),
        mode=request.mode,
        status=status,
        reason=reason,
        runner_plan_hash=request.runner_plan_hash if _is_contract_hash(request.runner_plan_hash) else "",
        expected_preflight_hash=(
            request.expected_preflight_hash
            if _is_contract_hash(request.expected_preflight_hash)
            else ""
        ),
        preflight_hash=preflight_hash if _is_contract_hash(preflight_hash) else "",
        adapter_admission_hash=adapter_admission_hash,
        checks=checks,
        counts=_counts(
            checks=checks,
            preflight_projection=request.preflight_projection,
            hash_match_count=hash_match_count,
            adapter_reach_count=adapter_reach_count,
            block_count=block_count,
        ),
        execution_boundary=_zero_execution_boundary(),
        claim_boundary=_claim_boundary(),
    )


class TargetRuntimeAdapterAdmissionService:
    """Validate preflight evidence before a disabled adapter can be reached."""

    def admit(
        self,
        request: TargetRuntimeAdapterAdmissionRequest,
    ) -> TargetRuntimeAdapterAdmissionResult:
        checks: list[JsonDict] = []
        failures: list[str] = []
        projection = request.preflight_projection if isinstance(request.preflight_projection, dict) else {}
        execution = projection.get("execution_boundary", {})
        claim_boundary = projection.get("claim_boundary", {})
        counts = projection.get("counts", {})
        preflight_hash = str(projection.get("preflight_hash", ""))

        _check(
            checks,
            failures,
            name="adapter_admission_mode_disabled",
            passed=request.mode == TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION,
            reason="target_runtime_adapter_admission_mode_invalid",
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
            name="expected_preflight_hash_present",
            passed=_is_contract_hash(request.expected_preflight_hash),
            reason="expected_preflight_hash_missing",
        )
        _check(
            checks,
            failures,
            name="preflight_projection_present",
            passed=bool(projection),
            reason="preflight_projection_missing",
        )
        _check(
            checks,
            failures,
            name="preflight_projection_version",
            passed=projection.get("projection_version") == TARGET_RUNTIME_PREFLIGHT_VERSION,
            reason="preflight_projection_version_invalid",
        )
        _check(
            checks,
            failures,
            name="preflight_run_matches_request",
            passed=projection.get("run_id") == safe_public_run_id(request.run_id)
            and projection.get("runner_plan_hash") == request.runner_plan_hash,
            reason="preflight_request_mismatch",
        )
        _check(
            checks,
            failures,
            name="preflight_hash_matches_expected",
            passed=_is_contract_hash(preflight_hash)
            and preflight_hash == request.expected_preflight_hash,
            reason="preflight_hash_mismatch",
        )
        _check(
            checks,
            failures,
            name="preflight_execution_closed",
            passed=projection.get("status") == "blocked"
            and projection.get("reason") == "target_runtime_execution_closed",
            reason="preflight_not_execution_closed",
        )
        _check(
            checks,
            failures,
            name="preflight_boundary_clean",
            passed=isinstance(counts, dict)
            and counts.get("denied_path_count") == 0
            and counts.get("blocked_operation_count") == 0,
            reason="preflight_boundary_not_clean",
        )
        _check(
            checks,
            failures,
            name="preflight_zero_call_boundary",
            passed=isinstance(execution, dict)
            and execution.get("target_runtime_calls") == 0
            and execution.get("filesystem_writes") == 0
            and execution.get("subprocess_calls") == 0
            and execution.get("network_calls") == 0
            and execution.get("execution_permission_count") == 0,
            reason="preflight_zero_call_boundary_invalid",
        )
        _check(
            checks,
            failures,
            name="preflight_claim_boundary_no_runtime_outcome",
            passed=isinstance(claim_boundary, dict)
            and claim_boundary.get("target_runtime_outcome") is False,
            reason="preflight_claim_boundary_invalid",
        )

        if failures:
            return _result(
                request=request,
                status="blocked",
                reason=failures[0],
                checks=checks,
                preflight_hash=preflight_hash,
                hash_match_count=0,
                adapter_reach_count=0,
                block_count=1,
            )

        return _result(
            request=request,
            status="admitted",
            reason="target_runtime_preflight_admitted",
            checks=checks,
            preflight_hash=preflight_hash,
            hash_match_count=1,
            adapter_reach_count=0,
            block_count=0,
        )


class DisabledTargetRuntimeAdapter:
    """Adapter skeleton that never runs DAACS target runtime code."""

    def invoke(
        self,
        request: TargetRuntimeAdapterAdmissionRequest,
        admission: TargetRuntimeAdapterAdmissionResult,
    ) -> TargetRuntimeAdapterAdmissionResult:
        checks = [
            {"name": "target_runtime_preflight_admission_passed", "passed": True, "reason": ""},
            *admission.checks,
            {
                "name": "target_runtime_adapter_disabled",
                "passed": False,
                "reason": "target_runtime_adapter_disabled",
            },
        ]
        return _result(
            request=request,
            status="blocked",
            reason="target_runtime_adapter_disabled",
            checks=checks,
            preflight_hash=admission.preflight_hash,
            hash_match_count=1,
            adapter_reach_count=1,
            block_count=1,
        )


def invoke_disabled_target_runtime_adapter_after_preflight_admission(
    *,
    adapter: TargetRuntimeAdapter,
    request: TargetRuntimeAdapterAdmissionRequest,
    admission_service: TargetRuntimeAdapterAdmissionService | None,
) -> TargetRuntimeAdapterAdmissionResult:
    """Reach a disabled adapter only after hash-only preflight admission passes."""
    if admission_service is None:
        checks = [
            {
                "name": "target_runtime_adapter_admission_service_present",
                "passed": False,
                "reason": "target_runtime_adapter_admission_service_missing",
            }
        ]
        return _result(
            request=request,
            status="blocked",
            reason="target_runtime_adapter_admission_service_missing",
            checks=checks,
        )

    admission = admission_service.admit(request)
    if admission.status != "admitted":
        checks = [
            {
                "name": "target_runtime_preflight_admission_passed",
                "passed": False,
                "reason": admission.reason,
            },
            *admission.checks,
        ]
        return _result(
            request=request,
            status="blocked",
            reason=admission.reason,
            checks=checks,
            preflight_hash=admission.preflight_hash,
            hash_match_count=0,
            adapter_reach_count=0,
            block_count=1,
        )

    try:
        return adapter.invoke(request, admission)
    except Exception:
        checks = [
            {
                "name": "target_runtime_adapter_available",
                "passed": False,
                "reason": "target_runtime_adapter_unavailable",
            },
            *admission.checks,
        ]
        return _result(
            request=request,
            status="blocked",
            reason="target_runtime_adapter_unavailable",
            checks=checks,
            preflight_hash=admission.preflight_hash,
            hash_match_count=1,
            adapter_reach_count=0,
            block_count=1,
        )


def default_target_runtime_adapter_admission_service() -> TargetRuntimeAdapterAdmissionService:
    return TargetRuntimeAdapterAdmissionService()


__all__ = [
    "TARGET_RUNTIME_ADAPTER_ADMISSION_VERSION",
    "TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION",
    "DisabledTargetRuntimeAdapter",
    "TargetRuntimeAdapter",
    "TargetRuntimeAdapterAdmissionRequest",
    "TargetRuntimeAdapterAdmissionResult",
    "TargetRuntimeAdapterAdmissionService",
    "default_target_runtime_adapter_admission_service",
    "invoke_disabled_target_runtime_adapter_after_preflight_admission",
]

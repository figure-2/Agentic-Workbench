"""Local build preflight projection for the generated fixture app.

This boundary checks whether the buildable fixture manifest is eligible for a
later local-only build attempt. It never runs package installation, build,
server start, provider calls, network calls, subprocess calls, or the DAACS
target runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys, sanitize_public_payload
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash

from .runner_provider import is_safe_run_id, safe_public_run_id
from .target_runtime_buildable_fixture_manifest import (
    TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION = (
    "target-runtime-local-build-preflight-public-v1"
)
TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE = "target_runtime_local_build_preflight"
LOCAL_BUILD_PREFLIGHT_COMMAND_LABELS = (
    "npm install",
    "npm run verify",
    "npm run build",
    "npm run preview",
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeLocalBuildPreflightRequest:
    """Request to project local build preflight eligibility."""

    run_id: str
    buildable_fixture_manifest_hash: str
    buildable_fixture_manifest_projection: JsonDict = field(default_factory=dict)
    mode: str = TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE
    operator_opt_in: bool = False
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TargetRuntimeLocalBuildPreflightResult:
    """Public-safe local build preflight projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    local_build_eligible: bool
    local_build_opt_in_required: bool
    operator_opt_in_present: bool
    buildable_fixture_manifest_hash: str
    buildable_fixture_manifest_projection_hash: str
    local_build_preflight_hash: str
    command_plan: list[JsonDict]
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    repository_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("local build preflight must be a mapping")
        _assert_projection_safe(payload)
        return payload


def _is_contract_hash(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


def _assert_projection_safe(value: JsonDict) -> None:
    public = sanitize_public_payload(value)
    if not isinstance(public, dict):
        raise ValueError("local build preflight must be a mapping")
    if find_forbidden_public_keys(public):
        raise ValueError("local build preflight contains forbidden keys")
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError("local build preflight contains forbidden claims")
    assert_public_projection_safe(public)


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


def _projection_hash(projection: JsonDict) -> str:
    sanitized = sanitize_public_payload(projection)
    if not isinstance(sanitized, dict):
        return ""
    _assert_projection_safe(sanitized)
    return stable_contract_hash(sanitized)


def _command_plan() -> list[JsonDict]:
    records: list[JsonDict] = []
    for index, label in enumerate(LOCAL_BUILD_PREFLIGHT_COMMAND_LABELS, start=1):
        records.append(
            {
                "order": index,
                "label": label,
                "requires_local_opt_in": True,
                "executed": False,
                "command_label_hash": stable_contract_hash(label),
            }
        )
    return records


def _zero_execution_boundary() -> JsonDict:
    return {
        "target_runtime_calls": 0,
        "provider_calls": 0,
        "live_api_calls": 0,
        "sdk_imports": 0,
        "env_key_value_reads": 0,
        "subprocess_calls": 0,
        "network_calls": 0,
        "package_install_calls": 0,
        "build_calls": 0,
        "server_start_calls": 0,
        "execution_permission_count": 0,
        "local_build_preflight_only": True,
        "dependency_value_return_count": 0,
        "generated_file_content_public_return_count": 0,
        "local_root_path_public_return_count": 0,
    }


def _repository_boundary() -> JsonDict:
    return {
        "local_build_preflight_backend": "projection_only",
        "root_path_returned": False,
        "raw_row_returned": False,
        "file_content_returned": False,
        "dependency_value_returned": False,
    }


def _claim_boundary(*, local_build_eligible: bool, operator_opt_in: bool) -> JsonDict:
    return {
        "scope": "local build preflight only",
        "local_build_eligible": local_build_eligible,
        "local_build_opt_in_required": True,
        "operator_opt_in_present": operator_opt_in,
        "package_install_executed": False,
        "build_executed": False,
        "server_started": False,
        "target_runtime_outcome": False,
        "external_provider_outcome": False,
        "hosted_behavior": False,
        "production_success_claim": False,
    }


def _counts(
    *,
    checks: list[JsonDict],
    command_plan: list[JsonDict],
    local_build_eligible: bool,
    operator_opt_in: bool,
) -> JsonDict:
    return {
        "local_build_preflight_scenario_count": 1 if local_build_eligible else 0,
        "check_count": len(checks),
        "passed_check_count": sum(1 for check in checks if check.get("passed") is True),
        "failed_check_count": sum(1 for check in checks if check.get("passed") is not True),
        "command_plan_label_count": len(command_plan),
        "required_command_plan_label_count": 2,
        "command_plan_hash_count": sum(
            1 for record in command_plan if _is_contract_hash(record.get("command_label_hash"))
        ),
        "local_build_eligible_count": 1 if local_build_eligible else 0,
        "local_build_opt_in_required_count": 1,
        "operator_opt_in_present_count": 1 if operator_opt_in else 0,
        "default_execution_permission_count": 0,
        "dependency_value_return_count": 0,
        "file_content_public_return_count": 0,
        "local_root_path_return_count": 0,
        "target_runtime_call_count": 0,
        "provider_call_count": 0,
        "sdk_import_count": 0,
        "env_value_read_count": 0,
        "subprocess_call_count": 0,
        "network_call_count": 0,
        "package_install_call_count": 0,
        "build_call_count": 0,
        "server_start_call_count": 0,
        "execution_permission_count": 0,
    }


def _result(
    *,
    request: TargetRuntimeLocalBuildPreflightRequest,
    status: str,
    reason: str,
    checks: list[JsonDict],
    command_plan: list[JsonDict],
    buildable_projection_hash: str,
) -> TargetRuntimeLocalBuildPreflightResult:
    local_build_eligible = status == "passed"
    claim_boundary = _claim_boundary(
        local_build_eligible=local_build_eligible,
        operator_opt_in=request.operator_opt_in,
    )
    payload_to_hash = {
        "projection_version": TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION,
        "run_id": safe_public_run_id(request.run_id),
        "mode": request.mode,
        "status": status,
        "reason": reason,
        "local_build_eligible": local_build_eligible,
        "local_build_opt_in_required": True,
        "operator_opt_in_present": request.operator_opt_in,
        "buildable_fixture_manifest_hash": request.buildable_fixture_manifest_hash,
        "buildable_fixture_manifest_projection_hash": buildable_projection_hash,
        "command_plan": command_plan,
        "claim_boundary": claim_boundary,
    }
    return TargetRuntimeLocalBuildPreflightResult(
        projection_version=TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION,
        run_id=safe_public_run_id(request.run_id),
        mode=request.mode,
        status=status,
        reason=reason,
        local_build_eligible=local_build_eligible,
        local_build_opt_in_required=True,
        operator_opt_in_present=request.operator_opt_in,
        buildable_fixture_manifest_hash=request.buildable_fixture_manifest_hash,
        buildable_fixture_manifest_projection_hash=buildable_projection_hash,
        local_build_preflight_hash=stable_contract_hash(payload_to_hash),
        command_plan=command_plan,
        checks=checks,
        counts=_counts(
            checks=checks,
            command_plan=command_plan,
            local_build_eligible=local_build_eligible,
            operator_opt_in=request.operator_opt_in,
        ),
        execution_boundary=_zero_execution_boundary(),
        repository_boundary=_repository_boundary(),
        claim_boundary=claim_boundary,
    )


class TargetRuntimeLocalBuildPreflightService:
    """Project a local build preflight without executing package commands."""

    def create_preflight(
        self,
        request: TargetRuntimeLocalBuildPreflightRequest,
    ) -> TargetRuntimeLocalBuildPreflightResult:
        buildable_projection = (
            request.buildable_fixture_manifest_projection
            if isinstance(request.buildable_fixture_manifest_projection, dict)
            else {}
        )
        buildable_projection_hash = (
            _projection_hash(buildable_projection) if buildable_projection else ""
        )
        command_plan = _command_plan()
        checks: list[JsonDict] = []
        failures: list[str] = []
        package_manifest = buildable_projection.get("package_manifest", {})
        counts = buildable_projection.get("counts", {})
        execution = buildable_projection.get("execution_boundary", {})

        _check(
            checks,
            failures,
            name="local_build_preflight_mode_valid",
            passed=request.mode == TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE,
            reason="local_build_preflight_mode_invalid",
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
            name="buildable_fixture_manifest_hash_valid",
            passed=_is_contract_hash(request.buildable_fixture_manifest_hash),
            reason="buildable_fixture_manifest_hash_missing_or_invalid",
        )
        _check(
            checks,
            failures,
            name="buildable_fixture_manifest_projection_present",
            passed=bool(buildable_projection),
            reason="buildable_fixture_manifest_projection_missing",
        )
        _check(
            checks,
            failures,
            name="buildable_fixture_manifest_projection_version",
            passed=buildable_projection.get("projection_version")
            == TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION,
            reason="buildable_fixture_manifest_projection_version_invalid",
        )
        _check(
            checks,
            failures,
            name="buildable_fixture_manifest_projection_passed",
            passed=buildable_projection.get("status") == "passed"
            and buildable_projection.get("build_ready_candidate") is True,
            reason="buildable_fixture_manifest_projection_status_invalid",
        )
        _check(
            checks,
            failures,
            name="buildable_fixture_manifest_run_matches",
            passed=buildable_projection.get("run_id") == safe_public_run_id(request.run_id),
            reason="buildable_fixture_manifest_run_mismatch",
        )
        _check(
            checks,
            failures,
            name="buildable_fixture_manifest_hash_matches_projection",
            passed=request.buildable_fixture_manifest_hash
            == buildable_projection.get("buildable_fixture_manifest_hash"),
            reason="buildable_fixture_manifest_hash_mismatch",
        )
        _check(
            checks,
            failures,
            name="buildable_fixture_manifest_public_values_sanitized",
            passed=package_manifest.get("dependency_value_returned") is False
            and int(counts.get("package_manifest_value_return_count", -1)) == 0,
            reason="buildable_fixture_manifest_public_values_not_sanitized",
        )
        _check(
            checks,
            failures,
            name="buildable_fixture_manifest_execution_zero",
            passed=int(execution.get("package_install_calls", -1)) == 0
            and int(execution.get("build_calls", -1)) == 0
            and int(execution.get("server_start_calls", -1)) == 0
            and int(execution.get("subprocess_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
            and int(execution.get("target_runtime_calls", -1)) == 0,
            reason="buildable_fixture_manifest_execution_nonzero",
        )
        _check(
            checks,
            failures,
            name="local_build_command_plan_labels_present",
            passed=len(command_plan) >= 2,
            reason="local_build_command_plan_labels_missing",
        )

        if failures:
            return _result(
                request=request,
                status="blocked",
                reason=failures[0],
                checks=checks,
                command_plan=[],
                buildable_projection_hash=buildable_projection_hash,
            )

        return _result(
            request=request,
            status="passed",
            reason="local_build_preflight_ready",
            checks=[
                *checks,
                {
                    "name": "local_build_opt_in_required",
                    "passed": True,
                    "reason": "",
                },
                {
                    "name": "local_build_execution_closed_by_default",
                    "passed": True,
                    "reason": "",
                },
            ],
            command_plan=command_plan,
            buildable_projection_hash=buildable_projection_hash,
        )


def default_target_runtime_local_build_preflight_service() -> (
    TargetRuntimeLocalBuildPreflightService
):
    return TargetRuntimeLocalBuildPreflightService()


def create_target_runtime_local_build_preflight(
    *,
    request: TargetRuntimeLocalBuildPreflightRequest,
    service: TargetRuntimeLocalBuildPreflightService | None = None,
) -> TargetRuntimeLocalBuildPreflightResult:
    selected_service = service or default_target_runtime_local_build_preflight_service()
    return selected_service.create_preflight(request)


__all__ = [
    "LOCAL_BUILD_PREFLIGHT_COMMAND_LABELS",
    "TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE",
    "TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION",
    "TargetRuntimeLocalBuildPreflightRequest",
    "TargetRuntimeLocalBuildPreflightResult",
    "TargetRuntimeLocalBuildPreflightService",
    "create_target_runtime_local_build_preflight",
    "default_target_runtime_local_build_preflight_service",
]

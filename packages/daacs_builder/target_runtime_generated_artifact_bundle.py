"""Disabled DAACS generated artifact bundle contract.

This module defines the public evidence shape for the future bundle of files
that a DAACS target runtime may generate. It consumes the persisted output
manifest read model and returns hashes, status, reasons, and counts only. It
does not write files, store source bodies, spawn subprocesses, import provider
SDKs, read environment values, or open network connections.
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
from .target_runtime_output_manifest_store import (
    target_runtime_output_manifest_public_read_model,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION = (
    "target-runtime-generated-artifact-bundle-public-v1"
)
TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED = (
    "target_runtime_disabled_generated_artifact_bundle"
)
TARGET_RUNTIME_GENERATED_ARTIFACT_UNIT_LABELS = (
    "backend",
    "frontend",
    "verification_report",
)
ARTIFACT_UNIT_LABEL_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


@dataclass(frozen=True, slots=True)
class TargetRuntimeGeneratedArtifactBundleRequest:
    """Hash-only request for disabled generated artifact bundle evidence."""

    run_id: str
    runner_plan_hash: str
    output_manifest_hash: str
    output_manifest_read_model: JsonDict = field(default_factory=dict)
    artifact_units: list[JsonDict] = field(default_factory=list)
    mode: str = TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TargetRuntimeGeneratedArtifactBundleResult:
    """Public-safe disabled generated artifact bundle projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    runner_plan_hash: str
    output_manifest_hash: str
    output_manifest_read_model_hash: str
    generated_artifact_bundle_hash: str
    artifact_units: list[JsonDict]
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("target runtime generated artifact bundle must be a mapping")
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
        "generated_artifact_body_write_count": 0,
        "execution_permission_count": 0,
    }


def _claim_boundary() -> JsonDict:
    return {
        "scope": "disabled target runtime generated artifact bundle contract only",
        "output_manifest_read_model_required": True,
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
        raise ValueError(
            "target runtime generated artifact bundle projection must be a mapping"
        )
    if find_forbidden_public_keys(public):
        raise ValueError(
            "target runtime generated artifact bundle contains forbidden public keys"
        )
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError(
            "target runtime generated artifact bundle contains forbidden claims"
        )
    assert_public_projection_safe(public)


def _default_artifact_units() -> list[JsonDict]:
    units: list[JsonDict] = []
    for label in TARGET_RUNTIME_GENERATED_ARTIFACT_UNIT_LABELS:
        unit = {
            "label": label,
            "artifact_kind": label,
            "expected_file_count": 0,
            "body_included": False,
            "path_included": False,
            "unit_hash": stable_contract_hash(
                {
                    "label": label,
                    "artifact_kind": label,
                    "expected_file_count": 0,
                }
            ),
        }
        units.append(unit)
    return units


def _safe_artifact_units(value: list[JsonDict]) -> list[JsonDict]:
    if not value:
        return _default_artifact_units()
    units: list[JsonDict] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError("target runtime artifact unit must be a mapping")
        label = str(item.get("label", "")).strip().lower()
        if not ARTIFACT_UNIT_LABEL_PATTERN.fullmatch(label):
            raise ValueError("target runtime artifact unit label is unsafe")
        artifact_kind = str(item.get("artifact_kind", label)).strip().lower()
        if not ARTIFACT_UNIT_LABEL_PATTERN.fullmatch(artifact_kind):
            raise ValueError("target runtime artifact unit kind is unsafe")
        expected_file_count = _as_int(item.get("expected_file_count", 0))
        unit = {
            "label": label,
            "artifact_kind": artifact_kind,
            "expected_file_count": expected_file_count,
            "body_included": False,
            "path_included": False,
            "unit_hash": stable_contract_hash(
                {
                    "label": label,
                    "artifact_kind": artifact_kind,
                    "expected_file_count": expected_file_count,
                    "index": index,
                }
            ),
        }
        units.append(unit)
    if len({unit["label"] for unit in units}) != len(units):
        raise ValueError("target runtime artifact unit labels must be unique")
    return units


def _output_manifest_read_model_hash(read_model: JsonDict) -> str:
    sanitized = sanitize_public_payload(read_model)
    if not isinstance(sanitized, dict):
        return ""
    _assert_projection_safe(sanitized)
    return stable_contract_hash(sanitized)


def _output_manifest_read_model_counts(read_model: JsonDict) -> JsonDict:
    counts = read_model.get("counts", {})
    return counts if isinstance(counts, dict) else {}


def _output_manifest_read_model_execution(read_model: JsonDict) -> JsonDict:
    execution = read_model.get("execution_boundary", {})
    return execution if isinstance(execution, dict) else {}


def _output_manifests(read_model: JsonDict) -> list[JsonDict]:
    manifests = read_model.get("output_manifests", [])
    return manifests if isinstance(manifests, list) else []


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
    artifact_units: list[JsonDict],
    output_manifest_hash_match_count: int,
) -> JsonDict:
    read_counts = _output_manifest_read_model_counts(read_model)
    failed_check_count = sum(1 for check in checks if not check["passed"])
    return {
        "generated_artifact_bundle_count": 1,
        "comparison_variant_count": 1,
        "check_count": len(checks),
        "failed_check_count": failed_check_count,
        "output_manifest_read_model_count": 1 if read_model else 0,
        "output_manifest_record_count": _as_int(
            read_counts.get("output_manifest_record_count")
        ),
        "output_manifest_hash_count": _as_int(
            read_counts.get("output_manifest_hash_count")
        ),
        "output_manifest_hash_match_count": output_manifest_hash_match_count,
        "artifact_unit_count": len(artifact_units),
        "artifact_unit_hash_count": len(
            {unit["unit_hash"] for unit in artifact_units}
        ),
        "generated_artifact_body_write_count": 0,
        "target_runtime_call_count": 0,
        "filesystem_write_count": 0,
        "subprocess_call_count": 0,
        "network_call_count": 0,
        "execution_permission_count": 0,
    }


def _hash_for_bundle(
    *,
    request: TargetRuntimeGeneratedArtifactBundleRequest,
    read_model_hash: str,
    artifact_units: list[JsonDict],
    status: str,
    reason: str,
    failed_check_count: int,
) -> str:
    return stable_contract_hash(
        {
            "projection_version": TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
            "run_id": safe_public_run_id(request.run_id),
            "mode": request.mode,
            "runner_plan_hash": request.runner_plan_hash,
            "output_manifest_hash": request.output_manifest_hash,
            "output_manifest_read_model_hash": read_model_hash,
            "artifact_unit_hashes": [unit["unit_hash"] for unit in artifact_units],
            "status": status,
            "reason": reason,
            "failed_check_count": failed_check_count,
        }
    )


def _result(
    *,
    request: TargetRuntimeGeneratedArtifactBundleRequest,
    status: str,
    reason: str,
    checks: list[JsonDict],
    artifact_units: list[JsonDict],
    read_model_hash: str,
    output_manifest_hash_match_count: int = 0,
) -> TargetRuntimeGeneratedArtifactBundleResult:
    failed_check_count = sum(1 for check in checks if not check["passed"])
    generated_artifact_bundle_hash = _hash_for_bundle(
        request=request,
        read_model_hash=read_model_hash,
        artifact_units=artifact_units,
        status=status,
        reason=reason,
        failed_check_count=failed_check_count,
    )
    return TargetRuntimeGeneratedArtifactBundleResult(
        projection_version=TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
        run_id=safe_public_run_id(request.run_id),
        mode=request.mode,
        status=status,
        reason=reason,
        runner_plan_hash=request.runner_plan_hash
        if _is_contract_hash(request.runner_plan_hash)
        else "",
        output_manifest_hash=request.output_manifest_hash
        if _is_contract_hash(request.output_manifest_hash)
        else "",
        output_manifest_read_model_hash=read_model_hash
        if _is_contract_hash(read_model_hash)
        else "",
        generated_artifact_bundle_hash=generated_artifact_bundle_hash,
        artifact_units=artifact_units,
        checks=checks,
        counts=_counts(
            checks=checks,
            read_model=request.output_manifest_read_model,
            artifact_units=artifact_units,
            output_manifest_hash_match_count=output_manifest_hash_match_count,
        ),
        execution_boundary=_zero_execution_boundary(),
        claim_boundary=_claim_boundary(),
    )


class TargetRuntimeGeneratedArtifactBundleService:
    """Build a disabled generated artifact bundle from manifest read-model evidence."""

    def build(
        self,
        request: TargetRuntimeGeneratedArtifactBundleRequest,
    ) -> TargetRuntimeGeneratedArtifactBundleResult:
        read_model = (
            request.output_manifest_read_model
            if isinstance(request.output_manifest_read_model, dict)
            else {}
        )
        artifact_units = _safe_artifact_units(request.artifact_units)
        read_model_hash = _output_manifest_read_model_hash(read_model) if read_model else ""
        read_counts = _output_manifest_read_model_counts(read_model)
        read_execution = _output_manifest_read_model_execution(read_model)
        output_manifest_hashes = {
            str(manifest.get("output_manifest_hash", ""))
            for manifest in _output_manifests(read_model)
            if isinstance(manifest, dict)
        }
        output_manifest_hash_match = (
            _is_contract_hash(request.output_manifest_hash)
            and request.output_manifest_hash in output_manifest_hashes
        )
        checks: list[JsonDict] = []
        failures: list[str] = []

        _check(
            checks,
            failures,
            name="generated_artifact_bundle_mode_disabled",
            passed=request.mode == TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED,
            reason="target_runtime_generated_artifact_bundle_mode_invalid",
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
            name="output_manifest_hash_valid",
            passed=_is_contract_hash(request.output_manifest_hash),
            reason="output_manifest_hash_invalid",
        )
        _check(
            checks,
            failures,
            name="output_manifest_read_model_present",
            passed=bool(read_model),
            reason="output_manifest_read_model_missing",
        )
        _check(
            checks,
            failures,
            name="output_manifest_read_model_version",
            passed=read_model.get("projection_version")
            == "target-runtime-output-manifest-read-model-public-v1",
            reason="output_manifest_read_model_version_invalid",
        )
        _check(
            checks,
            failures,
            name="output_manifest_read_model_available",
            passed=read_model.get("status") == "available",
            reason="output_manifest_read_model_unavailable",
        )
        _check(
            checks,
            failures,
            name="output_manifest_read_model_run_matches",
            passed=read_model.get("run_id") == safe_public_run_id(request.run_id),
            reason="output_manifest_read_model_run_mismatch",
        )
        _check(
            checks,
            failures,
            name="output_manifest_read_model_has_record",
            passed=_as_int(read_counts.get("output_manifest_record_count")) >= 1,
            reason="output_manifest_read_model_record_missing",
        )
        _check(
            checks,
            failures,
            name="output_manifest_hash_matches_read_model",
            passed=output_manifest_hash_match,
            reason="output_manifest_hash_mismatch",
        )
        _check(
            checks,
            failures,
            name="output_manifest_read_model_zero_call_boundary",
            passed=_as_int(read_execution.get("target_runtime_calls")) == 0
            and _as_int(read_execution.get("filesystem_writes")) == 0
            and _as_int(read_execution.get("subprocess_calls")) == 0
            and _as_int(read_execution.get("network_calls")) == 0
            and _as_int(read_counts.get("execution_permission_count")) == 0
            and _as_int(read_counts.get("generated_artifact_body_write_count")) == 0,
            reason="output_manifest_read_model_zero_call_boundary_invalid",
        )
        _check(
            checks,
            failures,
            name="artifact_units_present",
            passed=len(artifact_units) >= 3,
            reason="artifact_units_missing",
        )
        _check(
            checks,
            failures,
            name="artifact_units_hash_only",
            passed=all(
                unit.get("body_included") is False
                and unit.get("path_included") is False
                and _is_contract_hash(unit.get("unit_hash"))
                for unit in artifact_units
            ),
            reason="artifact_units_not_hash_only",
        )

        status = "blocked"
        reason = (
            failures[0]
            if failures
            else "target_runtime_generated_artifact_bundle_execution_closed"
        )
        return _result(
            request=request,
            status=status,
            reason=reason,
            checks=checks,
            artifact_units=artifact_units,
            read_model_hash=read_model_hash,
            output_manifest_hash_match_count=1 if output_manifest_hash_match else 0,
        )


def default_target_runtime_generated_artifact_bundle_service() -> (
    TargetRuntimeGeneratedArtifactBundleService
):
    return TargetRuntimeGeneratedArtifactBundleService()


def build_disabled_target_runtime_generated_artifact_bundle(
    *,
    request: TargetRuntimeGeneratedArtifactBundleRequest,
    service: TargetRuntimeGeneratedArtifactBundleService | None = None,
) -> TargetRuntimeGeneratedArtifactBundleResult:
    """Build the disabled generated artifact bundle projection."""
    selected_service = service or default_target_runtime_generated_artifact_bundle_service()
    return selected_service.build(request)


def build_disabled_target_runtime_generated_artifact_bundle_from_repository(
    *,
    repository,
    run_id: str,
    runner_plan_hash: str,
    output_manifest_hash: str,
    artifact_units: list[JsonDict] | None = None,
) -> TargetRuntimeGeneratedArtifactBundleResult:
    read_model = target_runtime_output_manifest_public_read_model(
        repository,
        run_id=run_id,
    )
    request = TargetRuntimeGeneratedArtifactBundleRequest(
        run_id=run_id,
        runner_plan_hash=runner_plan_hash,
        output_manifest_hash=output_manifest_hash,
        output_manifest_read_model=read_model,
        artifact_units=artifact_units or [],
    )
    return build_disabled_target_runtime_generated_artifact_bundle(request=request)


__all__ = [
    "TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED",
    "TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION",
    "TARGET_RUNTIME_GENERATED_ARTIFACT_UNIT_LABELS",
    "TargetRuntimeGeneratedArtifactBundleRequest",
    "TargetRuntimeGeneratedArtifactBundleResult",
    "TargetRuntimeGeneratedArtifactBundleService",
    "build_disabled_target_runtime_generated_artifact_bundle",
    "build_disabled_target_runtime_generated_artifact_bundle_from_repository",
    "default_target_runtime_generated_artifact_bundle_service",
]

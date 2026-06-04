"""Fixture-backed target runtime artifact materialization.

This module writes sanitized fixture files into a run-scoped workspace so the
local demo can show tangible artifact output without executing DAACS target
runtime code. Public projections expose only relative paths, hashes, counts,
status, and claim boundaries. File bodies, generated source bodies, local root
paths, provider payloads, subprocess output, and raw prompts are never returned.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys, sanitize_public_payload
from packages.core.pathing import PathBoundaryError, resolve_within_root
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash, utc_now

from .runner_provider import is_safe_run_id, safe_public_run_id
from .target_runtime_generated_artifact_bundle import (
    TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_FIXTURE_MATERIALIZATION_VERSION = (
    "target-runtime-fixture-materialization-public-v1"
)
TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE = (
    "target_runtime_fixture_artifact_materialization"
)
FIXTURE_ARTIFACT_PATHS = {
    "backend": "backend/main.py",
    "frontend": "frontend/App.tsx",
    "verification_report": "reports/verification.json",
}


@dataclass(frozen=True, slots=True)
class TargetRuntimeFixtureMaterializationRequest:
    """Request to write sanitized fixture artifacts under a run workspace."""

    run_id: str
    runner_plan_hash: str
    generated_artifact_bundle_hash: str
    generated_artifact_bundle_projection: JsonDict = field(default_factory=dict)
    workspace_root: str | Path | None = None
    mode: str = TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TargetRuntimeFixtureArtifactRecord:
    """Public-safe record for one materialized fixture artifact."""

    artifact_id: str
    run_id: str
    label: str
    artifact_kind: str
    workspace_relative_path: str
    content_hash: str
    byte_count: int
    body_included: bool
    root_path_returned: bool
    created_at: str

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("fixture artifact record must be a mapping")
        _assert_projection_safe(payload)
        return payload


@dataclass(frozen=True, slots=True)
class TargetRuntimeFixtureMaterializationResult:
    """Public-safe fixture materialization projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    runner_plan_hash: str
    generated_artifact_bundle_hash: str
    generated_artifact_bundle_projection_hash: str
    materialization_hash: str
    artifact_records: list[JsonDict]
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    repository_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("fixture materialization result must be a mapping")
        _assert_projection_safe(payload)
        return payload


def _is_contract_hash(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


def _as_int(value: object) -> int:
    if type(value) is int and value >= 0:
        return value
    return 0


def _assert_projection_safe(value: JsonDict) -> None:
    public = sanitize_public_payload(value)
    if not isinstance(public, dict):
        raise ValueError("fixture materialization projection must be a mapping")
    if find_forbidden_public_keys(public):
        raise ValueError("fixture materialization projection contains forbidden keys")
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError("fixture materialization projection contains forbidden claims")
    assert_public_projection_safe(public)


def _zero_or_fixture_execution_boundary(*, file_write_count: int = 0) -> JsonDict:
    return {
        "target_runtime_calls": 0,
        "provider_calls": 0,
        "live_api_calls": 0,
        "subprocess_calls": 0,
        "network_calls": 0,
        "package_install_calls": 0,
        "server_start_calls": 0,
        "execution_permission_count": 0,
        "fixture_workspace_file_write_count": file_write_count,
        "filesystem_writes_outside_workspace": 0,
        "generated_artifact_body_public_return_count": 0,
    }


def _repository_boundary(*, configured: bool) -> JsonDict:
    return {
        "fixture_workspace_backend": "local" if configured else "unconfigured",
        "root_path_returned": False,
        "raw_row_returned": False,
        "artifact_content_returned": False,
    }


def _claim_boundary() -> JsonDict:
    return {
        "scope": "fixture-backed local artifact materialization only",
        "fixture_materialization": True,
        "target_runtime_outcome": False,
        "external_provider_outcome": False,
        "generated_artifact_body_public": False,
        "source_body_public": False,
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


def _bundle_counts(bundle: JsonDict) -> JsonDict:
    counts = bundle.get("counts", {})
    return counts if isinstance(counts, dict) else {}


def _bundle_execution(bundle: JsonDict) -> JsonDict:
    execution = bundle.get("execution_boundary", {})
    return execution if isinstance(execution, dict) else {}


def _bundle_artifact_units(bundle: JsonDict) -> list[JsonDict]:
    units = bundle.get("artifact_units", [])
    return units if isinstance(units, list) else []


def _bundle_projection_hash(bundle: JsonDict) -> str:
    sanitized = sanitize_public_payload(bundle)
    if not isinstance(sanitized, dict):
        return ""
    _assert_projection_safe(sanitized)
    return stable_contract_hash(sanitized)


def _fixture_content(*, run_id: str, label: str, artifact_kind: str) -> str:
    if label == "backend":
        return (
            "# Agentic Workbench fixture backend artifact\n"
            f"RUN_ID = {run_id!r}\n"
            "FEATURES = ['task_creation', 'assignee_tracking', 'status_tracking']\n"
            "\n"
            "def describe_fixture():\n"
            "    return {'runtime': 'fixture', 'artifact': 'backend'}\n"
        )
    if label == "frontend":
        return (
            "// Agentic Workbench fixture frontend artifact\n"
            f"export const runId = {json.dumps(run_id)};\n"
            "export const dashboardCards = ['Tasks', 'Assignees', 'Due dates'];\n"
            "export function describeFixture() { return 'frontend fixture'; }\n"
        )
    if label == "verification_report":
        return json.dumps(
            {
                "runtime": "fixture",
                "run_id": run_id,
                "artifact": "verification_report",
                "checks": [
                    {"name": "fixture_materialized", "passed": True},
                    {"name": "target_runtime_calls", "count": 0},
                ],
            },
            ensure_ascii=True,
            sort_keys=True,
            indent=2,
        )
    return (
        f"# Agentic Workbench fixture artifact\nrun_id={run_id}\n"
        f"label={label}\nartifact_kind={artifact_kind}\n"
    )


def _relative_artifact_path(*, run_id: str, label: str) -> str:
    suffix = FIXTURE_ARTIFACT_PATHS.get(label, f"{label}/artifact.txt")
    return f"runs/{safe_public_run_id(run_id)}/{suffix}"


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{stable_contract_hash(content)[:12]}.tmp")
    try:
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(path)
    except OSError:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass
        raise


def _artifact_record(
    *,
    run_id: str,
    label: str,
    artifact_kind: str,
    relative_path: str,
    content: str,
    created_at: str,
) -> TargetRuntimeFixtureArtifactRecord:
    content_bytes = content.encode("utf-8")
    content_hash = stable_contract_hash(
        {
            "relative_path": relative_path,
            "content": content,
        }
    )
    return TargetRuntimeFixtureArtifactRecord(
        artifact_id=f"fixture-artifact-{content_hash[:16]}",
        run_id=safe_public_run_id(run_id),
        label=label,
        artifact_kind=artifact_kind,
        workspace_relative_path=relative_path,
        content_hash=content_hash,
        byte_count=len(content_bytes),
        body_included=False,
        root_path_returned=False,
        created_at=created_at,
    )


def _counts(
    *,
    checks: list[JsonDict],
    artifact_records: list[JsonDict],
    bundle: JsonDict,
    bundle_hash_match_count: int,
    write_count: int,
) -> JsonDict:
    bundle_counts = _bundle_counts(bundle)
    failed_check_count = sum(1 for check in checks if not check["passed"])
    return {
        "fixture_materialization_count": 1 if write_count else 0,
        "comparison_variant_count": 1,
        "check_count": len(checks),
        "failed_check_count": failed_check_count,
        "generated_artifact_bundle_projection_count": 1 if bundle else 0,
        "generated_artifact_bundle_hash_match_count": bundle_hash_match_count,
        "generated_artifact_bundle_artifact_unit_count": _as_int(
            bundle_counts.get("artifact_unit_count")
        ),
        "fixture_artifact_record_count": len(artifact_records),
        "fixture_artifact_content_hash_count": len(
            {record["content_hash"] for record in artifact_records}
        ),
        "fixture_workspace_file_write_count": write_count,
        "artifact_content_public_return_count": 0,
        "target_runtime_call_count": 0,
        "provider_call_count": 0,
        "subprocess_call_count": 0,
        "network_call_count": 0,
        "filesystem_write_outside_workspace_count": 0,
        "execution_permission_count": 0,
    }


def _hash_for_materialization(
    *,
    request: TargetRuntimeFixtureMaterializationRequest,
    bundle_projection_hash: str,
    artifact_records: list[JsonDict],
    status: str,
    reason: str,
    failed_check_count: int,
) -> str:
    return stable_contract_hash(
        {
            "projection_version": TARGET_RUNTIME_FIXTURE_MATERIALIZATION_VERSION,
            "run_id": safe_public_run_id(request.run_id),
            "mode": request.mode,
            "runner_plan_hash": request.runner_plan_hash,
            "generated_artifact_bundle_hash": request.generated_artifact_bundle_hash,
            "generated_artifact_bundle_projection_hash": bundle_projection_hash,
            "artifact_record_hashes": [
                record["content_hash"] for record in artifact_records
            ],
            "status": status,
            "reason": reason,
            "failed_check_count": failed_check_count,
        }
    )


def _result(
    *,
    request: TargetRuntimeFixtureMaterializationRequest,
    status: str,
    reason: str,
    checks: list[JsonDict],
    artifact_records: list[JsonDict],
    bundle_projection_hash: str,
    bundle_hash_match_count: int,
    write_count: int,
    configured: bool,
) -> TargetRuntimeFixtureMaterializationResult:
    failed_check_count = sum(1 for check in checks if not check["passed"])
    materialization_hash = _hash_for_materialization(
        request=request,
        bundle_projection_hash=bundle_projection_hash,
        artifact_records=artifact_records,
        status=status,
        reason=reason,
        failed_check_count=failed_check_count,
    )
    return TargetRuntimeFixtureMaterializationResult(
        projection_version=TARGET_RUNTIME_FIXTURE_MATERIALIZATION_VERSION,
        run_id=safe_public_run_id(request.run_id),
        mode=request.mode,
        status=status,
        reason=reason,
        runner_plan_hash=request.runner_plan_hash
        if _is_contract_hash(request.runner_plan_hash)
        else "",
        generated_artifact_bundle_hash=request.generated_artifact_bundle_hash
        if _is_contract_hash(request.generated_artifact_bundle_hash)
        else "",
        generated_artifact_bundle_projection_hash=bundle_projection_hash
        if _is_contract_hash(bundle_projection_hash)
        else "",
        materialization_hash=materialization_hash,
        artifact_records=artifact_records,
        checks=checks,
        counts=_counts(
            checks=checks,
            artifact_records=artifact_records,
            bundle=request.generated_artifact_bundle_projection,
            bundle_hash_match_count=bundle_hash_match_count,
            write_count=write_count,
        ),
        execution_boundary=_zero_or_fixture_execution_boundary(
            file_write_count=write_count
        ),
        repository_boundary=_repository_boundary(configured=configured),
        claim_boundary=_claim_boundary(),
    )


class TargetRuntimeFixtureMaterializationService:
    """Materialize sanitized fixture artifacts inside a run-scoped workspace."""

    def materialize(
        self,
        request: TargetRuntimeFixtureMaterializationRequest,
    ) -> TargetRuntimeFixtureMaterializationResult:
        bundle = (
            request.generated_artifact_bundle_projection
            if isinstance(request.generated_artifact_bundle_projection, dict)
            else {}
        )
        bundle_counts = _bundle_counts(bundle)
        bundle_execution = _bundle_execution(bundle)
        bundle_projection_hash = _bundle_projection_hash(bundle) if bundle else ""
        bundle_hash_match = (
            _is_contract_hash(request.generated_artifact_bundle_hash)
            and request.generated_artifact_bundle_hash
            == bundle.get("generated_artifact_bundle_hash")
        )
        workspace_root = Path(request.workspace_root) if request.workspace_root else None
        configured = workspace_root is not None
        units = _bundle_artifact_units(bundle)
        checks: list[JsonDict] = []
        failures: list[str] = []

        _check(
            checks,
            failures,
            name="fixture_materialization_mode_valid",
            passed=request.mode == TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE,
            reason="target_runtime_fixture_materialization_mode_invalid",
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
            name="generated_artifact_bundle_hash_valid",
            passed=_is_contract_hash(request.generated_artifact_bundle_hash),
            reason="generated_artifact_bundle_hash_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_projection_present",
            passed=bool(bundle),
            reason="generated_artifact_bundle_projection_missing",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_projection_version",
            passed=bundle.get("projection_version")
            == TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
            reason="generated_artifact_bundle_projection_version_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_projection_blocked",
            passed=bundle.get("status") == "blocked",
            reason="generated_artifact_bundle_projection_status_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_run_matches",
            passed=bundle.get("run_id") == safe_public_run_id(request.run_id),
            reason="generated_artifact_bundle_run_mismatch",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_hash_matches_projection",
            passed=bundle_hash_match,
            reason="generated_artifact_bundle_hash_mismatch",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_prerequisite_complete",
            passed=_as_int(bundle_counts.get("output_manifest_hash_match_count")) == 1
            and _as_int(bundle_counts.get("artifact_unit_count")) >= 3
            and _as_int(bundle_counts.get("generated_artifact_body_write_count")) == 0,
            reason="generated_artifact_bundle_prerequisite_incomplete",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_zero_call_boundary",
            passed=_as_int(bundle_execution.get("target_runtime_calls")) == 0
            and _as_int(bundle_execution.get("filesystem_writes")) == 0
            and _as_int(bundle_execution.get("subprocess_calls")) == 0
            and _as_int(bundle_execution.get("network_calls")) == 0
            and _as_int(bundle_execution.get("execution_permission_count")) == 0
            and _as_int(bundle_execution.get("generated_artifact_body_write_count")) == 0,
            reason="generated_artifact_bundle_zero_call_boundary_invalid",
        )
        _check(
            checks,
            failures,
            name="fixture_workspace_root_configured",
            passed=configured,
            reason="fixture_workspace_root_unconfigured",
        )

        artifact_records: list[JsonDict] = []
        write_count = 0
        if failures:
            return _result(
                request=request,
                status="blocked",
                reason=failures[0],
                checks=checks,
                artifact_records=artifact_records,
                bundle_projection_hash=bundle_projection_hash,
                bundle_hash_match_count=1 if bundle_hash_match else 0,
                write_count=write_count,
                configured=configured,
            )

        assert workspace_root is not None
        created_at = utc_now()
        try:
            for unit in units:
                if not isinstance(unit, dict):
                    continue
                label = str(unit.get("label", "")).strip().lower()
                artifact_kind = str(unit.get("artifact_kind", label)).strip().lower()
                if label not in FIXTURE_ARTIFACT_PATHS:
                    continue
                content = _fixture_content(
                    run_id=safe_public_run_id(request.run_id),
                    label=label,
                    artifact_kind=artifact_kind,
                )
                relative_path = _relative_artifact_path(
                    run_id=request.run_id,
                    label=label,
                )
                target_path = resolve_within_root(workspace_root, relative_path)
                _write_text_atomic(target_path, content)
                record = _artifact_record(
                    run_id=request.run_id,
                    label=label,
                    artifact_kind=artifact_kind,
                    relative_path=relative_path,
                    content=content,
                    created_at=created_at,
                ).to_dict()
                artifact_records.append(record)
                write_count += 1
        except (OSError, PathBoundaryError, ValueError):
            return _result(
                request=request,
                status="blocked",
                reason="fixture_workspace_materialization_failed",
                checks=[
                    *checks,
                    {
                        "name": "fixture_workspace_materialized",
                        "passed": False,
                        "reason": "fixture_workspace_materialization_failed",
                    },
                ],
                artifact_records=[],
                bundle_projection_hash=bundle_projection_hash,
                bundle_hash_match_count=1 if bundle_hash_match else 0,
                write_count=0,
                configured=configured,
            )

        materialized = len(artifact_records) >= 3
        final_checks = [
            *checks,
            {
                "name": "fixture_workspace_materialized",
                "passed": materialized,
                "reason": "" if materialized else "fixture_workspace_materialization_incomplete",
            },
        ]
        status = "passed" if materialized else "blocked"
        reason = (
            "target_runtime_fixture_artifacts_materialized"
            if materialized
            else "fixture_workspace_materialization_incomplete"
        )
        return _result(
            request=request,
            status=status,
            reason=reason,
            checks=final_checks,
            artifact_records=artifact_records,
            bundle_projection_hash=bundle_projection_hash,
            bundle_hash_match_count=1 if bundle_hash_match else 0,
            write_count=write_count,
            configured=configured,
        )


def default_target_runtime_fixture_materialization_service() -> (
    TargetRuntimeFixtureMaterializationService
):
    return TargetRuntimeFixtureMaterializationService()


def materialize_target_runtime_fixture_artifacts(
    *,
    request: TargetRuntimeFixtureMaterializationRequest,
    service: TargetRuntimeFixtureMaterializationService | None = None,
) -> TargetRuntimeFixtureMaterializationResult:
    selected_service = service or default_target_runtime_fixture_materialization_service()
    return selected_service.materialize(request)


__all__ = [
    "TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE",
    "TARGET_RUNTIME_FIXTURE_MATERIALIZATION_VERSION",
    "TargetRuntimeFixtureArtifactRecord",
    "TargetRuntimeFixtureMaterializationRequest",
    "TargetRuntimeFixtureMaterializationResult",
    "TargetRuntimeFixtureMaterializationService",
    "default_target_runtime_fixture_materialization_service",
    "materialize_target_runtime_fixture_artifacts",
]

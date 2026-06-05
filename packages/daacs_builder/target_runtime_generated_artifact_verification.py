"""Hash-only verification for restricted generated fixture workspace files."""

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
from .target_runtime_restricted_workspace_generation import (
    RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS,
    TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION = (
    "target-runtime-generated-artifact-verification-public-v1"
)
TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE = (
    "target_runtime_generated_artifact_fixture_verification"
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeGeneratedArtifactVerificationRequest:
    """Request to verify generated fixture workspace file records."""

    run_id: str
    generated_workspace_hash: str
    generated_workspace_projection: JsonDict = field(default_factory=dict)
    workspace_root: str | Path | None = None
    expected_template_ids: tuple[str, ...] = RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS
    mode: str = TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TargetRuntimeGeneratedArtifactFileCheckRecord:
    """Public-safe verification result for one generated fixture file."""

    label: str
    artifact_kind: str
    workspace_relative_path: str
    expected_content_hash: str
    actual_content_hash: str
    expected_byte_count: int
    actual_byte_count: int
    file_exists: bool
    content_hash_matched: bool
    byte_count_matched: bool
    content_included: bool
    root_path_returned: bool
    checked_at: str

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("generated artifact file check must be a mapping")
        _assert_projection_safe(payload)
        return payload


@dataclass(frozen=True, slots=True)
class TargetRuntimeGeneratedArtifactVerificationResult:
    """Public-safe generated fixture artifact verification projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    generated_workspace_hash: str
    generated_workspace_projection_hash: str
    generated_artifact_verification_hash: str
    file_check_records: list[JsonDict]
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    repository_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("generated artifact verification result must be a mapping")
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
        raise ValueError("generated artifact verification projection must be a mapping")
    if find_forbidden_public_keys(public):
        raise ValueError(
            "generated artifact verification projection contains forbidden keys"
        )
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError(
            "generated artifact verification projection contains forbidden claims"
        )
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


def _workspace_projection_hash(projection: JsonDict) -> str:
    sanitized = sanitize_public_payload(projection)
    if not isinstance(sanitized, dict):
        return ""
    _assert_projection_safe(sanitized)
    return stable_contract_hash(sanitized)


def _workspace_file_records(projection: JsonDict) -> list[JsonDict]:
    records = projection.get("file_records", [])
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def _zero_execution_boundary(*, file_read_count: int = 0) -> JsonDict:
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
        "generated_workspace_file_read_count": file_read_count,
        "generated_file_content_public_return_count": 0,
        "local_root_path_public_return_count": 0,
    }


def _repository_boundary(*, configured: bool) -> JsonDict:
    return {
        "generated_artifact_verification_backend": "local" if configured else "unconfigured",
        "root_path_returned": False,
        "raw_row_returned": False,
        "file_content_returned": False,
    }


def _claim_boundary() -> JsonDict:
    return {
        "scope": "restricted generated fixture file verification only",
        "fixture_verification": True,
        "target_runtime_outcome": False,
        "external_provider_outcome": False,
        "generated_file_content_public": False,
        "source_body_public": False,
        "build_executed": False,
        "server_started": False,
        "hosted_behavior": False,
        "production_trust_claim": False,
    }


def _record_label(record: JsonDict) -> str:
    return str(record.get("label") or "").strip()


def _record_path(record: JsonDict) -> str:
    return str(record.get("workspace_relative_path") or "").strip()


def _expected_prefix(run_id: str) -> str:
    return f"runs/{safe_public_run_id(run_id)}/generated-app/"


def _is_absolute_like(path: str) -> bool:
    candidate = Path(path)
    return candidate.is_absolute() or bool(candidate.drive)


def _content_hash_for_record(record: JsonDict, content: str) -> str:
    return stable_contract_hash(
        {
            "template_id": _record_label(record),
            "relative_path": _record_path(record),
            "content": content,
        }
    )


def _file_check_record(
    *,
    record: JsonDict,
    content: str,
    content_hash_matched: bool,
    byte_count_matched: bool,
    checked_at: str,
) -> JsonDict:
    actual_content_hash = _content_hash_for_record(record, content)
    actual_byte_count = len(content.encode("utf-8"))
    return TargetRuntimeGeneratedArtifactFileCheckRecord(
        label=_record_label(record),
        artifact_kind=str(record.get("artifact_kind") or "").strip(),
        workspace_relative_path=_record_path(record),
        expected_content_hash=str(record.get("content_hash") or ""),
        actual_content_hash=actual_content_hash,
        expected_byte_count=_as_int(record.get("byte_count")),
        actual_byte_count=actual_byte_count,
        file_exists=True,
        content_hash_matched=content_hash_matched,
        byte_count_matched=byte_count_matched,
        content_included=False,
        root_path_returned=False,
        checked_at=checked_at,
    ).to_dict()


def _counts(
    *,
    checks: list[JsonDict],
    file_check_records: list[JsonDict],
    workspace: JsonDict,
    workspace_hash_match_count: int,
    expected_file_count: int,
    expected_file_present_count: int,
    file_read_count: int,
    missing_expected_file_count: int,
    missing_local_file_count: int,
    path_traversal_block_count: int,
    absolute_path_block_count: int,
) -> JsonDict:
    failed_check_count = sum(1 for check in checks if not check["passed"])
    workspace_counts = workspace.get("counts", {})
    if not isinstance(workspace_counts, dict):
        workspace_counts = {}
    content_hash_match_count = sum(
        1 for record in file_check_records if record.get("content_hash_matched") is True
    )
    byte_count_match_count = sum(
        1 for record in file_check_records if record.get("byte_count_matched") is True
    )
    return {
        "generated_artifact_verification_count": (
            1 if file_check_records and failed_check_count == 0 else 0
        ),
        "comparison_variant_count": 1,
        "check_count": len(checks),
        "failed_check_count": failed_check_count,
        "generated_workspace_projection_count": 1 if workspace else 0,
        "generated_workspace_hash_match_count": workspace_hash_match_count,
        "generated_workspace_file_record_count": _as_int(
            workspace_counts.get("generated_workspace_file_record_count")
        ),
        "expected_file_count": expected_file_count,
        "expected_file_present_count": expected_file_present_count,
        "file_check_record_count": len(file_check_records),
        "file_exists_count": len(file_check_records),
        "file_read_count": file_read_count,
        "content_hash_match_count": content_hash_match_count,
        "byte_count_match_count": byte_count_match_count,
        "missing_expected_file_count": missing_expected_file_count,
        "missing_local_file_count": missing_local_file_count,
        "path_traversal_block_count": path_traversal_block_count,
        "absolute_path_block_count": absolute_path_block_count,
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


def _verification_hash(
    *,
    request: TargetRuntimeGeneratedArtifactVerificationRequest,
    workspace_projection_hash: str,
    file_check_records: list[JsonDict],
    status: str,
    reason: str,
    failed_check_count: int,
) -> str:
    return stable_contract_hash(
        {
            "projection_version": TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION,
            "run_id": safe_public_run_id(request.run_id),
            "mode": request.mode,
            "generated_workspace_hash": request.generated_workspace_hash,
            "generated_workspace_projection_hash": workspace_projection_hash,
            "file_check_hashes": [
                stable_contract_hash(record) for record in file_check_records
            ],
            "status": status,
            "reason": reason,
            "failed_check_count": failed_check_count,
        }
    )


def _result(
    *,
    request: TargetRuntimeGeneratedArtifactVerificationRequest,
    status: str,
    reason: str,
    checks: list[JsonDict],
    file_check_records: list[JsonDict],
    workspace_projection_hash: str,
    workspace_hash_match_count: int,
    configured: bool,
    expected_file_count: int,
    expected_file_present_count: int,
    file_read_count: int,
    missing_expected_file_count: int,
    missing_local_file_count: int,
    path_traversal_block_count: int,
    absolute_path_block_count: int,
) -> TargetRuntimeGeneratedArtifactVerificationResult:
    failed_check_count = sum(1 for check in checks if not check["passed"])
    verification_hash = _verification_hash(
        request=request,
        workspace_projection_hash=workspace_projection_hash,
        file_check_records=file_check_records,
        status=status,
        reason=reason,
        failed_check_count=failed_check_count,
    )
    return TargetRuntimeGeneratedArtifactVerificationResult(
        projection_version=TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION,
        run_id=safe_public_run_id(request.run_id),
        mode=request.mode,
        status=status,
        reason=reason,
        generated_workspace_hash=(
            request.generated_workspace_hash
            if _is_contract_hash(request.generated_workspace_hash)
            else ""
        ),
        generated_workspace_projection_hash=(
            workspace_projection_hash if _is_contract_hash(workspace_projection_hash) else ""
        ),
        generated_artifact_verification_hash=verification_hash,
        file_check_records=file_check_records,
        checks=checks,
        counts=_counts(
            checks=checks,
            file_check_records=file_check_records,
            workspace=request.generated_workspace_projection,
            workspace_hash_match_count=workspace_hash_match_count,
            expected_file_count=expected_file_count,
            expected_file_present_count=expected_file_present_count,
            file_read_count=file_read_count,
            missing_expected_file_count=missing_expected_file_count,
            missing_local_file_count=missing_local_file_count,
            path_traversal_block_count=path_traversal_block_count,
            absolute_path_block_count=absolute_path_block_count,
        ),
        execution_boundary=_zero_execution_boundary(file_read_count=file_read_count),
        repository_boundary=_repository_boundary(configured=configured),
        claim_boundary=_claim_boundary(),
    )


class TargetRuntimeGeneratedArtifactVerificationService:
    """Verify restricted generated fixture files without executing them."""

    def verify(
        self,
        request: TargetRuntimeGeneratedArtifactVerificationRequest,
    ) -> TargetRuntimeGeneratedArtifactVerificationResult:
        workspace = (
            request.generated_workspace_projection
            if isinstance(request.generated_workspace_projection, dict)
            else {}
        )
        workspace_root = Path(request.workspace_root) if request.workspace_root else None
        configured = workspace_root is not None
        records = _workspace_file_records(workspace)
        workspace_projection_hash = _workspace_projection_hash(workspace) if workspace else ""
        workspace_hash_match = (
            _is_contract_hash(request.generated_workspace_hash)
            and request.generated_workspace_hash == workspace.get("generated_workspace_hash")
        )
        expected_labels = tuple(str(label) for label in request.expected_template_ids)
        record_by_label = {_record_label(record): record for record in records}
        expected_file_present_count = sum(
            1 for label in expected_labels if label in record_by_label
        )
        missing_expected_file_count = len(expected_labels) - expected_file_present_count
        checks: list[JsonDict] = []
        failures: list[str] = []

        _check(
            checks,
            failures,
            name="generated_artifact_verification_mode_valid",
            passed=request.mode == TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE,
            reason="generated_artifact_verification_mode_invalid",
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
            name="generated_workspace_hash_valid",
            passed=_is_contract_hash(request.generated_workspace_hash),
            reason="generated_workspace_hash_missing_or_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_workspace_projection_present",
            passed=bool(workspace),
            reason="generated_workspace_projection_missing",
        )
        _check(
            checks,
            failures,
            name="generated_workspace_projection_version",
            passed=workspace.get("projection_version")
            == TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION,
            reason="generated_workspace_projection_version_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_workspace_projection_passed",
            passed=workspace.get("status") == "passed",
            reason="generated_workspace_projection_status_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_workspace_run_matches",
            passed=workspace.get("run_id") == safe_public_run_id(request.run_id),
            reason="generated_workspace_run_mismatch",
        )
        _check(
            checks,
            failures,
            name="generated_workspace_hash_matches_projection",
            passed=workspace_hash_match,
            reason="generated_workspace_hash_mismatch",
        )
        _check(
            checks,
            failures,
            name="generated_workspace_file_records_present",
            passed=len(records) > 0,
            reason="generated_workspace_file_records_missing",
        )
        _check(
            checks,
            failures,
            name="expected_file_records_present",
            passed=missing_expected_file_count == 0,
            reason="generated_workspace_expected_file_missing",
        )
        _check(
            checks,
            failures,
            name="restricted_workspace_root_configured",
            passed=configured,
            reason="restricted_workspace_root_unconfigured",
        )

        file_check_records: list[JsonDict] = []
        file_read_count = 0
        missing_local_file_count = 0
        path_traversal_block_count = 0
        absolute_path_block_count = 0

        if failures:
            return _result(
                request=request,
                status="blocked",
                reason=failures[0],
                checks=checks,
                file_check_records=file_check_records,
                workspace_projection_hash=workspace_projection_hash,
                workspace_hash_match_count=1 if workspace_hash_match else 0,
                configured=configured,
                expected_file_count=len(expected_labels),
                expected_file_present_count=expected_file_present_count,
                file_read_count=file_read_count,
                missing_expected_file_count=missing_expected_file_count,
                missing_local_file_count=missing_local_file_count,
                path_traversal_block_count=path_traversal_block_count,
                absolute_path_block_count=absolute_path_block_count,
            )

        assert workspace_root is not None
        checked_at = utc_now()
        file_failures: list[str] = []
        for label in expected_labels:
            record = record_by_label[label]
            relative_path = _record_path(record)
            if _is_absolute_like(relative_path):
                file_failures.append("generated_workspace_file_path_absolute")
                absolute_path_block_count += 1
                continue
            if not relative_path.startswith(_expected_prefix(request.run_id)):
                file_failures.append("generated_workspace_file_path_outside_run")
                path_traversal_block_count += 1
                continue
            try:
                target_path = resolve_within_root(workspace_root, relative_path)
            except PathBoundaryError:
                file_failures.append("generated_workspace_file_path_traversal")
                path_traversal_block_count += 1
                continue
            if not target_path.exists() or not target_path.is_file():
                file_failures.append("generated_workspace_file_missing")
                missing_local_file_count += 1
                continue
            try:
                content = target_path.read_text(encoding="utf-8")
            except OSError:
                file_failures.append("generated_workspace_file_unreadable")
                missing_local_file_count += 1
                continue
            file_read_count += 1
            actual_hash = _content_hash_for_record(record, content)
            actual_byte_count = len(content.encode("utf-8"))
            content_hash_matched = actual_hash == str(record.get("content_hash") or "")
            byte_count_matched = actual_byte_count == _as_int(record.get("byte_count"))
            if not content_hash_matched:
                file_failures.append("generated_workspace_content_hash_mismatch")
            if not byte_count_matched:
                file_failures.append("generated_workspace_byte_count_mismatch")
            file_check_records.append(
                _file_check_record(
                    record=record,
                    content=content,
                    content_hash_matched=content_hash_matched,
                    byte_count_matched=byte_count_matched,
                    checked_at=checked_at,
                )
            )

        file_checks_passed = not file_failures and len(file_check_records) == len(expected_labels)
        final_checks = [
            *checks,
            {
                "name": "generated_workspace_files_verified",
                "passed": file_checks_passed,
                "reason": "" if file_checks_passed else file_failures[0],
            },
        ]
        status = "passed" if file_checks_passed else "blocked"
        reason = (
            "generated_artifact_files_verified"
            if file_checks_passed
            else file_failures[0]
        )
        return _result(
            request=request,
            status=status,
            reason=reason,
            checks=final_checks,
            file_check_records=file_check_records,
            workspace_projection_hash=workspace_projection_hash,
            workspace_hash_match_count=1 if workspace_hash_match else 0,
            configured=configured,
            expected_file_count=len(expected_labels),
            expected_file_present_count=expected_file_present_count,
            file_read_count=file_read_count,
            missing_expected_file_count=missing_expected_file_count,
            missing_local_file_count=missing_local_file_count,
            path_traversal_block_count=path_traversal_block_count,
            absolute_path_block_count=absolute_path_block_count,
        )


def default_target_runtime_generated_artifact_verification_service() -> (
    TargetRuntimeGeneratedArtifactVerificationService
):
    return TargetRuntimeGeneratedArtifactVerificationService()


def verify_target_runtime_generated_artifacts(
    *,
    request: TargetRuntimeGeneratedArtifactVerificationRequest,
    service: TargetRuntimeGeneratedArtifactVerificationService | None = None,
) -> TargetRuntimeGeneratedArtifactVerificationResult:
    selected_service = (
        service or default_target_runtime_generated_artifact_verification_service()
    )
    return selected_service.verify(request)


__all__ = [
    "TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE",
    "TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION",
    "TargetRuntimeGeneratedArtifactFileCheckRecord",
    "TargetRuntimeGeneratedArtifactVerificationRequest",
    "TargetRuntimeGeneratedArtifactVerificationResult",
    "TargetRuntimeGeneratedArtifactVerificationService",
    "default_target_runtime_generated_artifact_verification_service",
    "verify_target_runtime_generated_artifacts",
]

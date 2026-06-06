"""Static validation for the restricted generated fixture workspace.

The validation reads verified fixture files under a configured run-scoped
workspace and returns only status, hashes, counts, and reasons. It does not
install packages, run a build, start a server, invoke the DAACS target runtime,
or call a provider.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys, sanitize_public_payload
from packages.core.pathing import PathBoundaryError, resolve_within_root
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash, utc_now

from .runner_provider import is_safe_run_id, safe_public_run_id
from .target_runtime_generated_artifact_verification import (
    TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION,
)
from .target_runtime_restricted_workspace_generation import (
    RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION = (
    "target-runtime-generated-workspace-static-validation-public-v1"
)
TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE = (
    "target_runtime_generated_workspace_static_validation"
)
REQUIRED_PACKAGE_SCRIPT_LABELS = ("dev", "build", "preview", "verify")
APP_COMPONENT_MARKERS = (
    "export default function App",
    "Agentic Workbench Fixture App",
    "Workflow Stages",
    "Artifact Cards",
    "Runner Plan",
    "Verification Summary",
    "Execution Boundary",
    "Action Center",
    "Evidence Timeline",
    "Task Board",
    "Owner Filter",
    "Reviewer Decision",
    "Interaction Ready",
)
API_CLIENT_MARKERS = (
    "export type WorkflowStage",
    "export type FixtureRunSummary",
    "export type FixtureAction",
    "export type EvidenceEvent",
    "export function getFixtureRunSummary",
    "export function getFixtureActions",
    "export function getEvidenceTimeline",
    "executionBoundary",
)
VERIFICATION_BOUNDARY_MARKERS = (
    "Verification Summary",
    "Execution Boundary",
    "Provider calls",
    "DAACS target runtime calls",
)
ZERO_CALL_MARKERS = (
    "| Provider calls | 0 |",
    "| DAACS target runtime calls | 0 |",
    "| Package installs | 0 |",
    "| Builds | 0 |",
    "| Server starts | 0 |",
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeGeneratedWorkspaceStaticValidationRequest:
    """Request to statically validate verified generated fixture files."""

    run_id: str
    generated_artifact_verification_hash: str
    generated_artifact_verification_projection: JsonDict = field(default_factory=dict)
    workspace_root: str | Path | None = None
    mode: str = TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TargetRuntimeGeneratedWorkspaceStaticValidationResult:
    """Public-safe static validation result for a generated fixture workspace."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    generated_artifact_verification_hash: str
    generated_artifact_verification_projection_hash: str
    generated_workspace_static_validation_hash: str
    checks: list[JsonDict]
    validation_records: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    repository_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("generated workspace static validation must be a mapping")
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
        raise ValueError("generated workspace static validation must be a mapping")
    if find_forbidden_public_keys(public):
        raise ValueError(
            "generated workspace static validation contains forbidden keys"
        )
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError(
            "generated workspace static validation contains forbidden claims"
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


def _verification_projection_hash(projection: JsonDict) -> str:
    sanitized = sanitize_public_payload(projection)
    if not isinstance(sanitized, dict):
        return ""
    _assert_projection_safe(sanitized)
    return stable_contract_hash(sanitized)


def _verification_file_records(projection: JsonDict) -> list[JsonDict]:
    records = projection.get("file_check_records", [])
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def _record_label(record: JsonDict) -> str:
    return str(record.get("label") or "").strip()


def _record_path(record: JsonDict) -> str:
    return str(record.get("workspace_relative_path") or "").strip()


def _expected_prefix(run_id: str) -> str:
    return f"runs/{safe_public_run_id(run_id)}/generated-app/"


def _is_absolute_like(path: str) -> bool:
    candidate = Path(path)
    return candidate.is_absolute() or bool(candidate.drive)


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
        "static_validation_file_read_count": file_read_count,
        "generated_file_content_public_return_count": 0,
        "local_root_path_public_return_count": 0,
    }


def _repository_boundary(*, configured: bool) -> JsonDict:
    return {
        "generated_workspace_static_validation_backend": (
            "local" if configured else "unconfigured"
        ),
        "root_path_returned": False,
        "raw_row_returned": False,
        "file_content_returned": False,
    }


def _claim_boundary() -> JsonDict:
    return {
        "scope": "restricted generated fixture workspace static validation only",
        "fixture_validation": True,
        "target_runtime_outcome": False,
        "external_provider_outcome": False,
        "generated_file_content_public": False,
        "source_body_public": False,
        "package_install_executed": False,
        "build_executed": False,
        "server_started": False,
        "hosted_behavior": False,
        "production_trust_claim": False,
    }


def _validation_record(
    *,
    name: str,
    passed: bool,
    reason: str = "",
    evidence_hash: str = "",
    count: int = 0,
) -> JsonDict:
    return {
        "name": name,
        "passed": bool(passed),
        "reason": "" if passed else reason,
        "evidence_hash": evidence_hash,
        "count": count,
    }


def _validated_files(
    *,
    records: list[JsonDict],
    workspace_root: Path,
    run_id: str,
) -> tuple[dict[str, str], int, str]:
    content_by_label: dict[str, str] = {}
    file_read_count = 0
    for record in records:
        label = _record_label(record)
        relative_path = _record_path(record)
        if _is_absolute_like(relative_path):
            return content_by_label, file_read_count, "static_validation_file_path_absolute"
        if not relative_path.startswith(_expected_prefix(run_id)):
            return content_by_label, file_read_count, "static_validation_file_path_outside_run"
        try:
            target_path = resolve_within_root(workspace_root, relative_path)
        except PathBoundaryError:
            return content_by_label, file_read_count, "static_validation_file_path_traversal"
        if not target_path.exists() or not target_path.is_file():
            return content_by_label, file_read_count, "static_validation_file_missing"
        try:
            content_by_label[label] = target_path.read_text(encoding="utf-8")
        except OSError:
            return content_by_label, file_read_count, "static_validation_file_unreadable"
        file_read_count += 1
    return content_by_label, file_read_count, ""


def _package_json_result(content: str) -> tuple[dict[str, Any] | None, str]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None, "static_validation_package_json_invalid"
    if not isinstance(parsed, dict):
        return None, "static_validation_package_json_not_mapping"
    return parsed, ""


def _script_labels(package_json: dict[str, Any] | None) -> tuple[int, str]:
    if package_json is None:
        return 0, "static_validation_package_json_missing"
    scripts = package_json.get("scripts", {})
    if not isinstance(scripts, dict):
        return 0, "static_validation_package_scripts_missing"
    present = sum(1 for label in REQUIRED_PACKAGE_SCRIPT_LABELS if label in scripts)
    if present != len(REQUIRED_PACKAGE_SCRIPT_LABELS):
        return present, "static_validation_package_required_scripts_missing"
    return present, ""


def _contains_all(content: str, markers: tuple[str, ...]) -> tuple[int, str]:
    present = sum(1 for marker in markers if marker in content)
    return present, stable_contract_hash({"markers": markers, "present": present})


def _counts(
    *,
    checks: list[JsonDict],
    records: list[JsonDict],
    validation_records: list[JsonDict],
    file_read_count: int,
    script_present_count: int,
    app_marker_count: int,
    api_marker_count: int,
    verification_boundary_marker_count: int,
    zero_call_marker_count: int,
    readme_marker_count: int,
    verification_hash_match_count: int,
) -> JsonDict:
    return {
        "check_count": len(checks),
        "passed_check_count": sum(1 for check in checks if check.get("passed") is True),
        "failed_check_count": sum(1 for check in checks if check.get("passed") is not True),
        "validation_record_count": len(validation_records),
        "passed_validation_record_count": sum(
            1 for record in validation_records if record.get("passed") is True
        ),
        "failed_validation_record_count": sum(
            1 for record in validation_records if record.get("passed") is not True
        ),
        "verification_hash_match_count": verification_hash_match_count,
        "verified_file_record_count": len(records),
        "expected_file_count": len(RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS),
        "static_file_checked_count": len(records),
        "file_read_count": file_read_count,
        "package_json_parse_check_count": 1,
        "package_json_parse_pass_count": 1
        if any(
            record.get("name") == "package_json_parse" and record.get("passed") is True
            for record in validation_records
        )
        else 0,
        "required_script_count": len(REQUIRED_PACKAGE_SCRIPT_LABELS),
        "required_script_present_count": script_present_count,
        "app_component_marker_check_count": len(APP_COMPONENT_MARKERS),
        "app_component_marker_present_count": app_marker_count,
        "api_marker_check_count": len(API_CLIENT_MARKERS),
        "api_marker_present_count": api_marker_count,
        "verification_boundary_marker_check_count": len(
            VERIFICATION_BOUNDARY_MARKERS
        ),
        "verification_boundary_marker_present_count": (
            verification_boundary_marker_count
        ),
        "zero_call_marker_check_count": len(ZERO_CALL_MARKERS),
        "zero_call_marker_present_count": zero_call_marker_count,
        "readme_marker_check_count": 2,
        "readme_marker_present_count": readme_marker_count,
        "file_content_public_return_count": 0,
        "local_root_path_return_count": 0,
        "target_runtime_call_count": 0,
        "provider_call_count": 0,
        "subprocess_call_count": 0,
        "network_call_count": 0,
        "package_install_call_count": 0,
        "build_call_count": 0,
        "server_start_call_count": 0,
        "execution_permission_count": 0,
    }


def _result(
    *,
    request: TargetRuntimeGeneratedWorkspaceStaticValidationRequest,
    status: str,
    reason: str,
    checks: list[JsonDict],
    validation_records: list[JsonDict],
    verification_projection_hash: str,
    verification_hash_match_count: int,
    configured: bool,
    file_read_count: int,
    script_present_count: int = 0,
    app_marker_count: int = 0,
    api_marker_count: int = 0,
    verification_boundary_marker_count: int = 0,
    zero_call_marker_count: int = 0,
    readme_marker_count: int = 0,
) -> TargetRuntimeGeneratedWorkspaceStaticValidationResult:
    safe_run_id = safe_public_run_id(request.run_id)
    records = _verification_file_records(request.generated_artifact_verification_projection)
    claim_boundary = _claim_boundary()
    payload_to_hash = {
        "projection_version": TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION,
        "run_id": safe_run_id,
        "mode": request.mode,
        "status": status,
        "reason": reason,
        "generated_artifact_verification_hash": (
            request.generated_artifact_verification_hash
        ),
        "generated_artifact_verification_projection_hash": verification_projection_hash,
        "validation_records": validation_records,
        "claim_boundary": claim_boundary,
    }
    return TargetRuntimeGeneratedWorkspaceStaticValidationResult(
        projection_version=TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION,
        run_id=safe_run_id,
        mode=request.mode,
        status=status,
        reason=reason,
        generated_artifact_verification_hash=request.generated_artifact_verification_hash,
        generated_artifact_verification_projection_hash=verification_projection_hash,
        generated_workspace_static_validation_hash=stable_contract_hash(payload_to_hash),
        checks=checks,
        validation_records=validation_records,
        counts=_counts(
            checks=checks,
            records=records,
            validation_records=validation_records,
            file_read_count=file_read_count,
            script_present_count=script_present_count,
            app_marker_count=app_marker_count,
            api_marker_count=api_marker_count,
            verification_boundary_marker_count=verification_boundary_marker_count,
            zero_call_marker_count=zero_call_marker_count,
            readme_marker_count=readme_marker_count,
            verification_hash_match_count=verification_hash_match_count,
        ),
        execution_boundary=_zero_execution_boundary(file_read_count=file_read_count),
        repository_boundary=_repository_boundary(configured=configured),
        claim_boundary=claim_boundary,
    )


class TargetRuntimeGeneratedWorkspaceStaticValidationService:
    """Validate the generated fixture app skeleton without executing it."""

    def validate(
        self,
        request: TargetRuntimeGeneratedWorkspaceStaticValidationRequest,
    ) -> TargetRuntimeGeneratedWorkspaceStaticValidationResult:
        verification = (
            request.generated_artifact_verification_projection
            if isinstance(request.generated_artifact_verification_projection, dict)
            else {}
        )
        workspace_root = Path(request.workspace_root) if request.workspace_root else None
        configured = workspace_root is not None
        records = _verification_file_records(verification)
        verification_projection_hash = (
            _verification_projection_hash(verification) if verification else ""
        )
        verification_hash_match = (
            _is_contract_hash(request.generated_artifact_verification_hash)
            and request.generated_artifact_verification_hash
            == verification.get("generated_artifact_verification_hash")
        )
        record_by_label = {_record_label(record): record for record in records}
        required_records_present = all(
            label in record_by_label for label in RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS
        )
        checks: list[JsonDict] = []
        failures: list[str] = []

        _check(
            checks,
            failures,
            name="generated_workspace_static_validation_mode_valid",
            passed=request.mode == TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE,
            reason="generated_workspace_static_validation_mode_invalid",
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
            name="generated_artifact_verification_hash_valid",
            passed=_is_contract_hash(request.generated_artifact_verification_hash),
            reason="generated_artifact_verification_hash_missing_or_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_verification_projection_present",
            passed=bool(verification),
            reason="generated_artifact_verification_projection_missing",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_verification_projection_version",
            passed=verification.get("projection_version")
            == TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION,
            reason="generated_artifact_verification_projection_version_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_verification_projection_passed",
            passed=verification.get("status") == "passed",
            reason="generated_artifact_verification_projection_status_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_verification_run_matches",
            passed=verification.get("run_id") == safe_public_run_id(request.run_id),
            reason="generated_artifact_verification_run_mismatch",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_verification_hash_matches_projection",
            passed=verification_hash_match,
            reason="generated_artifact_verification_hash_mismatch",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_file_checks_complete",
            passed=required_records_present
            and len(records) >= len(RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS),
            reason="generated_artifact_file_checks_incomplete",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_file_checks_passed",
            passed=all(
                record.get("file_exists") is True
                and record.get("content_hash_matched") is True
                and record.get("byte_count_matched") is True
                for record in records
            ),
            reason="generated_artifact_file_checks_not_passed",
        )
        _check(
            checks,
            failures,
            name="restricted_workspace_root_configured",
            passed=configured,
            reason="restricted_workspace_root_unconfigured",
        )

        validation_records: list[JsonDict] = []
        file_read_count = 0
        if failures:
            return _result(
                request=request,
                status="blocked",
                reason=failures[0],
                checks=checks,
                validation_records=validation_records,
                verification_projection_hash=verification_projection_hash,
                verification_hash_match_count=1 if verification_hash_match else 0,
                configured=configured,
                file_read_count=file_read_count,
            )

        assert workspace_root is not None
        content_by_label, file_read_count, file_failure = _validated_files(
            records=records,
            workspace_root=workspace_root,
            run_id=request.run_id,
        )
        if file_failure:
            return _result(
                request=request,
                status="blocked",
                reason=file_failure,
                checks=[
                    *checks,
                    {
                        "name": "generated_workspace_static_files_readable",
                        "passed": False,
                        "reason": file_failure,
                    },
                ],
                validation_records=validation_records,
                verification_projection_hash=verification_projection_hash,
                verification_hash_match_count=1 if verification_hash_match else 0,
                configured=configured,
                file_read_count=file_read_count,
            )

        package_json, package_failure = _package_json_result(
            content_by_label.get("package_json", "")
        )
        script_present_count, script_failure = _script_labels(package_json)
        app_marker_count, app_marker_hash = _contains_all(
            content_by_label.get("app_component", ""),
            APP_COMPONENT_MARKERS,
        )
        api_marker_count, api_marker_hash = _contains_all(
            content_by_label.get("api_client", ""),
            API_CLIENT_MARKERS,
        )
        verification_boundary_content = "\n".join(
            (
                content_by_label.get("app_component", ""),
                content_by_label.get("verification_notes", ""),
            )
        )
        (
            verification_boundary_marker_count,
            verification_boundary_marker_hash,
        ) = _contains_all(
            verification_boundary_content,
            VERIFICATION_BOUNDARY_MARKERS,
        )
        zero_call_marker_count, zero_call_marker_hash = _contains_all(
            content_by_label.get("verification_notes", ""),
            ZERO_CALL_MARKERS,
        )
        readme_marker_count, readme_marker_hash = _contains_all(
            content_by_label.get("readme", ""),
            (
                "Agentic Workbench Portfolio Fixture App",
                "DAACS target runtime calls: 0",
            ),
        )
        validation_records = [
            _validation_record(
                name="package_json_parse",
                passed=package_failure == "",
                reason=package_failure,
                evidence_hash=stable_contract_hash(
                    {"package_json_keys": sorted(package_json.keys())}
                    if package_json
                    else {"package_json": "invalid"}
                ),
                count=1 if package_failure == "" else 0,
            ),
            _validation_record(
                name="package_required_scripts",
                passed=script_failure == "",
                reason=script_failure,
                evidence_hash=stable_contract_hash(
                    {
                        "required_scripts": REQUIRED_PACKAGE_SCRIPT_LABELS,
                        "present_count": script_present_count,
                    }
                ),
                count=script_present_count,
            ),
            _validation_record(
                name="app_component_markers",
                passed=app_marker_count == len(APP_COMPONENT_MARKERS),
                reason="static_validation_app_component_markers_missing",
                evidence_hash=app_marker_hash,
                count=app_marker_count,
            ),
            _validation_record(
                name="api_client_markers",
                passed=api_marker_count == len(API_CLIENT_MARKERS),
                reason="static_validation_api_client_markers_missing",
                evidence_hash=api_marker_hash,
                count=api_marker_count,
            ),
            _validation_record(
                name="verification_boundary_markers",
                passed=verification_boundary_marker_count
                == len(VERIFICATION_BOUNDARY_MARKERS),
                reason="static_validation_verification_boundary_markers_missing",
                evidence_hash=verification_boundary_marker_hash,
                count=verification_boundary_marker_count,
            ),
            _validation_record(
                name="verification_notes_zero_call_markers",
                passed=zero_call_marker_count == len(ZERO_CALL_MARKERS),
                reason="static_validation_zero_call_markers_missing",
                evidence_hash=zero_call_marker_hash,
                count=zero_call_marker_count,
            ),
            _validation_record(
                name="readme_boundary_markers",
                passed=readme_marker_count == 2,
                reason="static_validation_readme_boundary_markers_missing",
                evidence_hash=readme_marker_hash,
                count=readme_marker_count,
            ),
        ]
        validation_failures = [
            record["reason"]
            for record in validation_records
            if record.get("passed") is not True
        ]
        status = "passed" if not validation_failures else "blocked"
        reason = (
            "generated_workspace_static_validation_passed"
            if status == "passed"
            else str(validation_failures[0])
        )
        return _result(
            request=request,
            status=status,
            reason=reason,
            checks=[
                *checks,
                {
                    "name": "generated_workspace_static_validation_passed",
                    "passed": status == "passed",
                    "reason": "" if status == "passed" else reason,
                },
            ],
            validation_records=validation_records,
            verification_projection_hash=verification_projection_hash,
            verification_hash_match_count=1 if verification_hash_match else 0,
            configured=configured,
            file_read_count=file_read_count,
            script_present_count=script_present_count,
            app_marker_count=app_marker_count,
            api_marker_count=api_marker_count,
            verification_boundary_marker_count=verification_boundary_marker_count,
            zero_call_marker_count=zero_call_marker_count,
            readme_marker_count=readme_marker_count,
        )


def default_target_runtime_generated_workspace_static_validation_service() -> (
    TargetRuntimeGeneratedWorkspaceStaticValidationService
):
    return TargetRuntimeGeneratedWorkspaceStaticValidationService()


def validate_target_runtime_generated_workspace_static(
    *,
    request: TargetRuntimeGeneratedWorkspaceStaticValidationRequest,
    service: TargetRuntimeGeneratedWorkspaceStaticValidationService | None = None,
) -> TargetRuntimeGeneratedWorkspaceStaticValidationResult:
    selected_service = (
        service
        or default_target_runtime_generated_workspace_static_validation_service()
    )
    return selected_service.validate(request)


__all__ = [
    "REQUIRED_PACKAGE_SCRIPT_LABELS",
    "TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE",
    "TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION",
    "TargetRuntimeGeneratedWorkspaceStaticValidationRequest",
    "TargetRuntimeGeneratedWorkspaceStaticValidationResult",
    "TargetRuntimeGeneratedWorkspaceStaticValidationService",
    "default_target_runtime_generated_workspace_static_validation_service",
    "validate_target_runtime_generated_workspace_static",
]

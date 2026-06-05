"""Build-ready manifest projection for the generated fixture app workspace.

This boundary turns the verified static fixture app into a build-ready
candidate manifest. It reads local fixture files for validation only and never
runs package installation, build, server start, provider calls, network calls,
or the DAACS target runtime.
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
from packages.core.schemas import JsonDict, stable_contract_hash

from .runner_provider import is_safe_run_id, safe_public_run_id
from .target_runtime_generated_workspace_static_validation import (
    REQUIRED_PACKAGE_SCRIPT_LABELS,
    TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION = (
    "target-runtime-buildable-fixture-manifest-public-v1"
)
TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE = (
    "target_runtime_buildable_fixture_app_manifest"
)
BUILD_READY_REQUIRED_FILE_PATHS = {
    "package_json": "package.json",
    "index_html": "index.html",
    "main_entrypoint": "src/main.tsx",
    "vite_config": "vite.config.ts",
    "tsconfig_json": "tsconfig.json",
}
PLACEHOLDER_DEPENDENCY_VALUES = {"fixture-reference", "placeholder", "todo"}


@dataclass(frozen=True, slots=True)
class TargetRuntimeBuildableFixtureManifestRequest:
    """Request to project a build-ready candidate manifest for a fixture app."""

    run_id: str
    generated_workspace_static_validation_hash: str
    generated_workspace_static_validation_projection: JsonDict = field(
        default_factory=dict
    )
    workspace_root: str | Path | None = None
    mode: str = TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TargetRuntimeBuildableFixtureManifestResult:
    """Public-safe build-ready candidate manifest projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    build_ready_candidate: bool
    generated_workspace_static_validation_hash: str
    generated_workspace_static_validation_projection_hash: str
    buildable_fixture_manifest_hash: str
    package_manifest: JsonDict
    build_readiness_records: list[JsonDict]
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    repository_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("buildable fixture manifest must be a mapping")
        _assert_projection_safe(payload)
        return payload


def _is_contract_hash(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


def _assert_projection_safe(value: JsonDict) -> None:
    public = sanitize_public_payload(value)
    if not isinstance(public, dict):
        raise ValueError("buildable fixture manifest must be a mapping")
    if find_forbidden_public_keys(public):
        raise ValueError("buildable fixture manifest contains forbidden keys")
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError("buildable fixture manifest contains forbidden claims")
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


def _static_projection_hash(projection: JsonDict) -> str:
    sanitized = sanitize_public_payload(projection)
    if not isinstance(sanitized, dict):
        return ""
    _assert_projection_safe(sanitized)
    return stable_contract_hash(sanitized)


def _expected_relative_path(*, run_id: str, path: str) -> str:
    return f"runs/{safe_public_run_id(run_id)}/generated-app/{path}"


def _read_required_files(
    *,
    workspace_root: Path,
    run_id: str,
) -> tuple[dict[str, str], int, str]:
    content_by_label: dict[str, str] = {}
    file_read_count = 0
    for label, relative in BUILD_READY_REQUIRED_FILE_PATHS.items():
        try:
            target_path = resolve_within_root(
                workspace_root,
                _expected_relative_path(run_id=run_id, path=relative),
            )
        except PathBoundaryError:
            return content_by_label, file_read_count, "build_manifest_path_traversal"
        if not target_path.exists() or not target_path.is_file():
            return content_by_label, file_read_count, "build_manifest_required_file_missing"
        try:
            content_by_label[label] = target_path.read_text(encoding="utf-8")
        except OSError:
            return content_by_label, file_read_count, "build_manifest_file_unreadable"
        file_read_count += 1
    return content_by_label, file_read_count, ""


def _package_json(content: str) -> tuple[dict[str, Any] | None, str]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None, "build_manifest_package_json_invalid"
    if not isinstance(parsed, dict):
        return None, "build_manifest_package_json_not_mapping"
    return parsed, ""


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_string_map(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, str] = {}
    for key, item in value.items():
        if isinstance(key, str) and isinstance(item, str) and key and item:
            result[key] = item
    return result


def _placeholder_dependency_count(*, dependencies: dict[str, str]) -> int:
    count = 0
    for value in dependencies.values():
        normalized = value.strip().lower()
        if (
            normalized in PLACEHOLDER_DEPENDENCY_VALUES
            or "fixture-reference" in normalized
            or "placeholder" in normalized
        ):
            count += 1
    return count


def _script_labels(package_json: dict[str, Any] | None) -> tuple[list[str], int]:
    scripts = _mapping(package_json.get("scripts") if package_json else {})
    labels = sorted(label for label in scripts if isinstance(label, str))
    present = sum(1 for label in REQUIRED_PACKAGE_SCRIPT_LABELS if label in labels)
    return labels, present


def _dependency_labels(
    package_json: dict[str, Any] | None,
) -> tuple[list[str], list[str], int]:
    dependencies = _safe_string_map(package_json.get("dependencies") if package_json else {})
    dev_dependencies = _safe_string_map(
        package_json.get("devDependencies") if package_json else {}
    )
    all_dependencies = {**dependencies, **dev_dependencies}
    return (
        sorted(dependencies),
        sorted(dev_dependencies),
        _placeholder_dependency_count(dependencies=all_dependencies),
    )


def _contains_count(content: str, markers: tuple[str, ...]) -> int:
    return sum(1 for marker in markers if marker in content)


def _record(
    *,
    name: str,
    passed: bool,
    reason: str,
    count: int,
    evidence: object,
) -> JsonDict:
    return {
        "name": name,
        "passed": bool(passed),
        "reason": "" if passed else reason,
        "count": count,
        "evidence_hash": stable_contract_hash(evidence),
    }


def _zero_execution_boundary(*, file_read_count: int) -> JsonDict:
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
        "buildable_manifest_file_read_count": file_read_count,
        "package_manifest_values_returned": 0,
        "generated_file_content_public_return_count": 0,
        "local_root_path_public_return_count": 0,
    }


def _repository_boundary(*, configured: bool) -> JsonDict:
    return {
        "buildable_fixture_manifest_backend": "local" if configured else "unconfigured",
        "root_path_returned": False,
        "raw_row_returned": False,
        "file_content_returned": False,
    }


def _claim_boundary(*, build_ready_candidate: bool) -> JsonDict:
    return {
        "scope": "restricted fixture app build-readiness manifest only",
        "build_ready_candidate": build_ready_candidate,
        "fixture_manifest": True,
        "target_runtime_outcome": False,
        "external_provider_outcome": False,
        "package_install_executed": False,
        "build_executed": False,
        "server_started": False,
        "hosted_behavior": False,
        "production_success_claim": False,
    }


def _counts(
    *,
    checks: list[JsonDict],
    records: list[JsonDict],
    file_read_count: int,
    script_present_count: int,
    dependency_label_count: int,
    dev_dependency_label_count: int,
    placeholder_dependency_count: int,
    index_marker_count: int,
    main_marker_count: int,
    vite_marker_count: int,
    tsconfig_marker_count: int,
    build_ready_candidate: bool,
) -> JsonDict:
    return {
        "build_readiness_scenario_count": 1 if build_ready_candidate else 0,
        "check_count": len(checks),
        "passed_check_count": sum(1 for check in checks if check.get("passed") is True),
        "failed_check_count": sum(1 for check in checks if check.get("passed") is not True),
        "build_readiness_record_count": len(records),
        "passed_build_readiness_record_count": sum(
            1 for record in records if record.get("passed") is True
        ),
        "failed_build_readiness_record_count": sum(
            1 for record in records if record.get("passed") is not True
        ),
        "required_file_count": len(BUILD_READY_REQUIRED_FILE_PATHS),
        "required_file_read_count": file_read_count,
        "required_script_count": len(REQUIRED_PACKAGE_SCRIPT_LABELS),
        "required_script_present_count": script_present_count,
        "dependency_label_count": dependency_label_count,
        "dev_dependency_label_count": dev_dependency_label_count,
        "total_dependency_label_count": dependency_label_count
        + dev_dependency_label_count,
        "placeholder_dependency_value_count": placeholder_dependency_count,
        "index_html_marker_check_count": 2,
        "index_html_marker_present_count": index_marker_count,
        "main_entrypoint_marker_check_count": 2,
        "main_entrypoint_marker_present_count": main_marker_count,
        "vite_config_marker_check_count": 2,
        "vite_config_marker_present_count": vite_marker_count,
        "tsconfig_marker_check_count": 2,
        "tsconfig_marker_present_count": tsconfig_marker_count,
        "build_ready_candidate_count": 1 if build_ready_candidate else 0,
        "package_manifest_value_return_count": 0,
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
    request: TargetRuntimeBuildableFixtureManifestRequest,
    status: str,
    reason: str,
    checks: list[JsonDict],
    build_readiness_records: list[JsonDict],
    static_projection_hash: str,
    configured: bool,
    file_read_count: int,
    package_manifest: JsonDict | None = None,
    script_present_count: int = 0,
    dependency_label_count: int = 0,
    dev_dependency_label_count: int = 0,
    placeholder_dependency_count: int = 0,
    index_marker_count: int = 0,
    main_marker_count: int = 0,
    vite_marker_count: int = 0,
    tsconfig_marker_count: int = 0,
) -> TargetRuntimeBuildableFixtureManifestResult:
    build_ready_candidate = status == "passed"
    public_package_manifest = package_manifest or {
        "package_name_hash": "",
        "script_labels": [],
        "dependency_labels": [],
        "dev_dependency_labels": [],
        "dependency_value_returned": False,
        "package_manifest_hash": "",
    }
    claim_boundary = _claim_boundary(build_ready_candidate=build_ready_candidate)
    payload_to_hash = {
        "projection_version": TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION,
        "run_id": safe_public_run_id(request.run_id),
        "mode": request.mode,
        "status": status,
        "reason": reason,
        "build_ready_candidate": build_ready_candidate,
        "generated_workspace_static_validation_hash": (
            request.generated_workspace_static_validation_hash
        ),
        "generated_workspace_static_validation_projection_hash": static_projection_hash,
        "package_manifest": public_package_manifest,
        "build_readiness_records": build_readiness_records,
        "claim_boundary": claim_boundary,
    }
    return TargetRuntimeBuildableFixtureManifestResult(
        projection_version=TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION,
        run_id=safe_public_run_id(request.run_id),
        mode=request.mode,
        status=status,
        reason=reason,
        build_ready_candidate=build_ready_candidate,
        generated_workspace_static_validation_hash=(
            request.generated_workspace_static_validation_hash
        ),
        generated_workspace_static_validation_projection_hash=static_projection_hash,
        buildable_fixture_manifest_hash=stable_contract_hash(payload_to_hash),
        package_manifest=public_package_manifest,
        build_readiness_records=build_readiness_records,
        checks=checks,
        counts=_counts(
            checks=checks,
            records=build_readiness_records,
            file_read_count=file_read_count,
            script_present_count=script_present_count,
            dependency_label_count=dependency_label_count,
            dev_dependency_label_count=dev_dependency_label_count,
            placeholder_dependency_count=placeholder_dependency_count,
            index_marker_count=index_marker_count,
            main_marker_count=main_marker_count,
            vite_marker_count=vite_marker_count,
            tsconfig_marker_count=tsconfig_marker_count,
            build_ready_candidate=build_ready_candidate,
        ),
        execution_boundary=_zero_execution_boundary(file_read_count=file_read_count),
        repository_boundary=_repository_boundary(configured=configured),
        claim_boundary=claim_boundary,
    )


class TargetRuntimeBuildableFixtureManifestService:
    """Project build-readiness for the generated fixture app without executing it."""

    def create_manifest(
        self,
        request: TargetRuntimeBuildableFixtureManifestRequest,
    ) -> TargetRuntimeBuildableFixtureManifestResult:
        static_projection = (
            request.generated_workspace_static_validation_projection
            if isinstance(request.generated_workspace_static_validation_projection, dict)
            else {}
        )
        workspace_root = Path(request.workspace_root) if request.workspace_root else None
        configured = workspace_root is not None
        static_projection_hash = (
            _static_projection_hash(static_projection) if static_projection else ""
        )
        static_hash_match = (
            _is_contract_hash(request.generated_workspace_static_validation_hash)
            and request.generated_workspace_static_validation_hash
            == static_projection.get("generated_workspace_static_validation_hash")
        )
        checks: list[JsonDict] = []
        failures: list[str] = []

        _check(
            checks,
            failures,
            name="buildable_fixture_manifest_mode_valid",
            passed=request.mode == TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE,
            reason="buildable_fixture_manifest_mode_invalid",
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
            name="generated_workspace_static_validation_hash_valid",
            passed=_is_contract_hash(request.generated_workspace_static_validation_hash),
            reason="generated_workspace_static_validation_hash_missing_or_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_workspace_static_validation_projection_present",
            passed=bool(static_projection),
            reason="generated_workspace_static_validation_projection_missing",
        )
        _check(
            checks,
            failures,
            name="generated_workspace_static_validation_projection_version",
            passed=static_projection.get("projection_version")
            == TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION,
            reason="generated_workspace_static_validation_projection_version_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_workspace_static_validation_projection_passed",
            passed=static_projection.get("status") == "passed",
            reason="generated_workspace_static_validation_projection_status_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_workspace_static_validation_run_matches",
            passed=static_projection.get("run_id") == safe_public_run_id(request.run_id),
            reason="generated_workspace_static_validation_run_mismatch",
        )
        _check(
            checks,
            failures,
            name="generated_workspace_static_validation_hash_matches_projection",
            passed=static_hash_match,
            reason="generated_workspace_static_validation_hash_mismatch",
        )
        _check(
            checks,
            failures,
            name="restricted_workspace_root_configured",
            passed=configured,
            reason="restricted_workspace_root_unconfigured",
        )

        if failures:
            return _result(
                request=request,
                status="blocked",
                reason=failures[0],
                checks=checks,
                build_readiness_records=[],
                static_projection_hash=static_projection_hash,
                configured=configured,
                file_read_count=0,
            )

        assert workspace_root is not None
        content_by_label, file_read_count, file_failure = _read_required_files(
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
                        "name": "build_manifest_required_files_readable",
                        "passed": False,
                        "reason": file_failure,
                    },
                ],
                build_readiness_records=[],
                static_projection_hash=static_projection_hash,
                configured=configured,
                file_read_count=file_read_count,
            )

        package_json, package_failure = _package_json(content_by_label["package_json"])
        script_labels, script_present_count = _script_labels(package_json)
        dependency_labels, dev_dependency_labels, placeholder_count = _dependency_labels(
            package_json
        )
        index_marker_count = _contains_count(
            content_by_label["index_html"],
            ("<div id=\"root\"></div>", "/src/main.tsx"),
        )
        main_marker_count = _contains_count(
            content_by_label["main_entrypoint"],
            ("createRoot", "<App />"),
        )
        vite_marker_count = _contains_count(
            content_by_label["vite_config"],
            ("defineConfig", "@vitejs/plugin-react"),
        )
        tsconfig_marker_count = _contains_count(
            content_by_label["tsconfig_json"],
            ('"jsx": "react-jsx"', '"strict": true'),
        )
        package_name = str(package_json.get("name") or "") if package_json else ""
        package_manifest = {
            "package_name_hash": stable_contract_hash(package_name),
            "script_labels": script_labels,
            "dependency_labels": dependency_labels,
            "dev_dependency_labels": dev_dependency_labels,
            "dependency_value_returned": False,
            "package_manifest_hash": stable_contract_hash(
                {
                    "package_name": package_name,
                    "script_labels": script_labels,
                    "dependency_labels": dependency_labels,
                    "dev_dependency_labels": dev_dependency_labels,
                }
            ),
        }
        dependency_total = len(dependency_labels) + len(dev_dependency_labels)
        build_readiness_records = [
            _record(
                name="package_json_parse",
                passed=package_failure == "",
                reason=package_failure,
                count=1 if package_failure == "" else 0,
                evidence={"package_json_keys": sorted(package_json or {})},
            ),
            _record(
                name="required_script_labels",
                passed=script_present_count == len(REQUIRED_PACKAGE_SCRIPT_LABELS),
                reason="build_manifest_required_scripts_missing",
                count=script_present_count,
                evidence={"script_labels": script_labels},
            ),
            _record(
                name="dependency_labels",
                passed=dependency_total >= 4,
                reason="build_manifest_dependency_labels_insufficient",
                count=dependency_total,
                evidence={
                    "dependency_labels": dependency_labels,
                    "dev_dependency_labels": dev_dependency_labels,
                },
            ),
            _record(
                name="placeholder_dependency_values",
                passed=placeholder_count == 0,
                reason="build_manifest_placeholder_dependency_values_present",
                count=placeholder_count,
                evidence={"placeholder_dependency_value_count": placeholder_count},
            ),
            _record(
                name="index_html_entry",
                passed=index_marker_count == 2,
                reason="build_manifest_index_html_entry_missing",
                count=index_marker_count,
                evidence={"index_html_marker_count": index_marker_count},
            ),
            _record(
                name="main_entrypoint",
                passed=main_marker_count == 2,
                reason="build_manifest_main_entrypoint_missing",
                count=main_marker_count,
                evidence={"main_entrypoint_marker_count": main_marker_count},
            ),
            _record(
                name="vite_config",
                passed=vite_marker_count == 2,
                reason="build_manifest_vite_config_missing",
                count=vite_marker_count,
                evidence={"vite_config_marker_count": vite_marker_count},
            ),
            _record(
                name="tsconfig",
                passed=tsconfig_marker_count == 2,
                reason="build_manifest_tsconfig_missing",
                count=tsconfig_marker_count,
                evidence={"tsconfig_marker_count": tsconfig_marker_count},
            ),
        ]
        record_failures = [
            str(record["reason"])
            for record in build_readiness_records
            if record.get("passed") is not True
        ]
        status = "passed" if not record_failures else "blocked"
        reason = (
            "buildable_fixture_manifest_ready"
            if status == "passed"
            else record_failures[0]
        )
        return _result(
            request=request,
            status=status,
            reason=reason,
            checks=[
                *checks,
                {
                    "name": "buildable_fixture_manifest_ready",
                    "passed": status == "passed",
                    "reason": "" if status == "passed" else reason,
                },
            ],
            build_readiness_records=build_readiness_records,
            static_projection_hash=static_projection_hash,
            configured=configured,
            file_read_count=file_read_count,
            package_manifest=package_manifest,
            script_present_count=script_present_count,
            dependency_label_count=len(dependency_labels),
            dev_dependency_label_count=len(dev_dependency_labels),
            placeholder_dependency_count=placeholder_count,
            index_marker_count=index_marker_count,
            main_marker_count=main_marker_count,
            vite_marker_count=vite_marker_count,
            tsconfig_marker_count=tsconfig_marker_count,
        )


def default_target_runtime_buildable_fixture_manifest_service() -> (
    TargetRuntimeBuildableFixtureManifestService
):
    return TargetRuntimeBuildableFixtureManifestService()


def create_target_runtime_buildable_fixture_manifest(
    *,
    request: TargetRuntimeBuildableFixtureManifestRequest,
    service: TargetRuntimeBuildableFixtureManifestService | None = None,
) -> TargetRuntimeBuildableFixtureManifestResult:
    selected_service = (
        service or default_target_runtime_buildable_fixture_manifest_service()
    )
    return selected_service.create_manifest(request)


__all__ = [
    "BUILD_READY_REQUIRED_FILE_PATHS",
    "TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE",
    "TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION",
    "TargetRuntimeBuildableFixtureManifestRequest",
    "TargetRuntimeBuildableFixtureManifestResult",
    "TargetRuntimeBuildableFixtureManifestService",
    "create_target_runtime_buildable_fixture_manifest",
    "default_target_runtime_buildable_fixture_manifest_service",
]

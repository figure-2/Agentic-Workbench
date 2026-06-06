import builtins
import json
import os
import socket
import subprocess
import urllib.request

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_generated_artifact_bundle import (
    TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
)
from packages.daacs_builder.target_runtime_generated_artifact_verification import (
    TargetRuntimeGeneratedArtifactVerificationRequest,
    verify_target_runtime_generated_artifacts,
)
from packages.daacs_builder.target_runtime_generated_workspace_static_validation import (
    TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE,
    TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION,
    TargetRuntimeGeneratedWorkspaceStaticValidationRequest,
    validate_target_runtime_generated_workspace_static,
)
from packages.daacs_builder.target_runtime_restricted_workspace_generation import (
    TargetRuntimeRestrictedWorkspaceGenerationRequest,
    generate_target_runtime_restricted_workspace,
)


RUN_ID = "run-build-01"


def _runner_plan_hash() -> str:
    return stable_contract_hash({"purpose": "static validation"})


def _implementation_brief_hash() -> str:
    return stable_contract_hash({"artifact": "implementation_brief", "run_id": RUN_ID})


def _bundle(run_id: str = RUN_ID) -> dict:
    bundle_hash = stable_contract_hash(
        {"run_id": run_id, "bundle": "generated-workspace-static-validation"}
    )
    return {
        "projection_version": TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
        "run_id": run_id,
        "status": "blocked",
        "reason": "target_runtime_generated_artifact_bundle_execution_closed",
        "generated_artifact_bundle_hash": bundle_hash,
        "counts": {
            "output_manifest_hash_match_count": 1,
            "artifact_unit_count": 3,
            "generated_artifact_body_write_count": 0,
        },
        "execution_boundary": {
            "target_runtime_calls": 0,
            "filesystem_writes": 0,
            "subprocess_calls": 0,
            "network_calls": 0,
            "execution_permission_count": 0,
            "generated_artifact_body_write_count": 0,
        },
    }


def _workspace_root(tmp_path):
    return tmp_path / "restricted-workspace"


def _generated_workspace(tmp_path, run_id: str = RUN_ID) -> dict:
    bundle = _bundle(run_id)
    return generate_target_runtime_restricted_workspace(
        request=TargetRuntimeRestrictedWorkspaceGenerationRequest(
            run_id=run_id,
            runner_plan_hash=_runner_plan_hash(),
            implementation_brief_hash=_implementation_brief_hash(),
            generated_artifact_bundle_hash=bundle["generated_artifact_bundle_hash"],
            generated_artifact_bundle_projection=bundle,
            workspace_root=_workspace_root(tmp_path),
        )
    ).to_dict()


def _verification(tmp_path, run_id: str = RUN_ID) -> dict:
    generated_workspace = _generated_workspace(tmp_path, run_id)
    return verify_target_runtime_generated_artifacts(
        request=TargetRuntimeGeneratedArtifactVerificationRequest(
            run_id=run_id,
            generated_workspace_hash=generated_workspace["generated_workspace_hash"],
            generated_workspace_projection=generated_workspace,
            workspace_root=_workspace_root(tmp_path),
        )
    ).to_dict()


def _request(
    tmp_path,
    *,
    verification: dict | None = None,
    **overrides,
) -> TargetRuntimeGeneratedWorkspaceStaticValidationRequest:
    selected_verification = verification or _verification(tmp_path)
    fields = {
        "run_id": RUN_ID,
        "generated_artifact_verification_hash": selected_verification[
            "generated_artifact_verification_hash"
        ],
        "generated_artifact_verification_projection": selected_verification,
        "workspace_root": _workspace_root(tmp_path),
        "metadata": {
            "raw_file_body": "AW_BUILD_01_RAW_SENTINEL",
            "provider_payload": "AW_BUILD_01_PROVIDER_SENTINEL",
        },
    }
    fields.update(overrides)
    return TargetRuntimeGeneratedWorkspaceStaticValidationRequest(**fields)


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def _path_for_label(verification: dict, label: str, tmp_path):
    for record in verification["file_check_records"]:
        if record["label"] == label:
            return _workspace_root(tmp_path) / record["workspace_relative_path"]
    raise AssertionError(f"missing label {label}")


def test_static_validation_passes_for_verified_generated_workspace(tmp_path):
    result = validate_target_runtime_generated_workspace_static(
        request=_request(tmp_path)
    ).to_dict()
    serialized = _serialized(result)

    assert result["projection_version"] == (
        TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION
    )
    assert result["mode"] == TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE
    assert result["status"] == "passed"
    assert result["reason"] == "generated_workspace_static_validation_passed"
    assert result["counts"]["verified_file_record_count"] == 9
    assert result["counts"]["static_file_checked_count"] == 9
    assert result["counts"]["file_read_count"] == 9
    assert result["counts"]["package_json_parse_pass_count"] == 1
    assert result["counts"]["required_script_present_count"] == 4
    assert result["counts"]["app_component_marker_present_count"] == 13
    assert result["counts"]["api_marker_present_count"] == 8
    assert result["counts"]["verification_boundary_marker_present_count"] == 4
    assert result["counts"]["zero_call_marker_present_count"] == 5
    assert result["execution_boundary"]["package_install_calls"] == 0
    assert result["execution_boundary"]["build_calls"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert result["repository_boundary"]["file_content_returned"] is False
    assert result["repository_boundary"]["root_path_returned"] is False
    assert str(tmp_path) not in serialized
    assert_public_projection_safe(result)


def test_static_validation_blocks_missing_verification_hash(tmp_path):
    result = validate_target_runtime_generated_workspace_static(
        request=_request(tmp_path, generated_artifact_verification_hash="")
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_artifact_verification_hash_missing_or_invalid"
    assert result["counts"]["file_read_count"] == 0


def test_static_validation_blocks_verification_hash_mismatch(tmp_path):
    result = validate_target_runtime_generated_workspace_static(
        request=_request(tmp_path, generated_artifact_verification_hash="a" * 64)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_artifact_verification_hash_mismatch"
    assert result["counts"]["verification_hash_match_count"] == 0


def test_static_validation_blocks_unpassed_verification_projection(tmp_path):
    verification = _verification(tmp_path)
    verification = {**verification, "status": "blocked"}

    result = validate_target_runtime_generated_workspace_static(
        request=_request(tmp_path, verification=verification)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_artifact_verification_projection_status_invalid"


def test_static_validation_blocks_incomplete_file_checks(tmp_path):
    verification = _verification(tmp_path)
    verification = {
        **verification,
        "file_check_records": verification["file_check_records"][:-1],
    }

    result = validate_target_runtime_generated_workspace_static(
        request=_request(tmp_path, verification=verification)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_artifact_file_checks_incomplete"


def test_static_validation_blocks_invalid_package_json(tmp_path):
    verification = _verification(tmp_path)
    _path_for_label(verification, "package_json", tmp_path).write_text(
        "{invalid json\n",
        encoding="utf-8",
    )

    result = validate_target_runtime_generated_workspace_static(
        request=_request(tmp_path, verification=verification)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "static_validation_package_json_invalid"
    assert result["counts"]["package_json_parse_pass_count"] == 0


def test_static_validation_blocks_missing_required_script_label(tmp_path):
    verification = _verification(tmp_path)
    package_path = _path_for_label(verification, "package_json", tmp_path)
    package = json.loads(package_path.read_text(encoding="utf-8"))
    del package["scripts"]["verify"]
    package_path.write_text(json.dumps(package, ensure_ascii=True), encoding="utf-8")

    result = validate_target_runtime_generated_workspace_static(
        request=_request(tmp_path, verification=verification)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "static_validation_package_required_scripts_missing"
    assert result["counts"]["required_script_present_count"] == 3


def test_static_validation_blocks_missing_app_marker(tmp_path):
    verification = _verification(tmp_path)
    app_path = _path_for_label(verification, "app_component", tmp_path)
    content = app_path.read_text(encoding="utf-8")
    app_path.write_text(
        content.replace("export default function App", "function NotApp"),
        encoding="utf-8",
    )

    result = validate_target_runtime_generated_workspace_static(
        request=_request(tmp_path, verification=verification)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "static_validation_app_component_markers_missing"
    assert result["counts"]["app_component_marker_present_count"] == 12


def test_static_validation_exposes_no_private_material(tmp_path):
    result = validate_target_runtime_generated_workspace_static(
        request=_request(tmp_path)
    ).to_dict()
    serialized = _serialized(result)

    assert "AW_BUILD_01_RAW_SENTINEL" not in serialized
    assert "AW_BUILD_01_PROVIDER_SENTINEL" not in serialized
    assert str(tmp_path) not in serialized
    assert "provider_payload" not in serialized
    assert "raw_file_body" not in serialized
    assert result["counts"]["file_content_public_return_count"] == 0
    assert result["counts"]["local_root_path_return_count"] == 0
    assert_public_projection_safe(result)


def test_static_validation_does_not_import_or_call_external_boundaries(
    tmp_path,
    monkeypatch,
):
    def fail_import(name, *args, **kwargs):
        if name.startswith(("requests", "httpx", "openai", "upstage")):
            raise AssertionError(f"unexpected import {name}")
        return original_import(name, *args, **kwargs)

    def fail_call(*args, **kwargs):
        raise AssertionError("unexpected external call")

    original_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", fail_import)
    monkeypatch.setattr(socket, "create_connection", fail_call)
    monkeypatch.setattr(urllib.request, "urlopen", fail_call)
    monkeypatch.setattr(subprocess, "run", fail_call)
    monkeypatch.setattr(os, "getenv", fail_call)

    result = validate_target_runtime_generated_workspace_static(
        request=_request(tmp_path)
    ).to_dict()

    assert result["status"] == "passed"
    assert result["execution_boundary"]["env_key_value_reads"] == 0
    assert result["execution_boundary"]["sdk_imports"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0

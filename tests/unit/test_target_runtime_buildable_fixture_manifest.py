import builtins
import json
import os
import socket
import subprocess
import urllib.request

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_buildable_fixture_manifest import (
    TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE,
    TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION,
    TargetRuntimeBuildableFixtureManifestRequest,
    create_target_runtime_buildable_fixture_manifest,
)
from packages.daacs_builder.target_runtime_generated_artifact_bundle import (
    TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
)
from packages.daacs_builder.target_runtime_generated_artifact_verification import (
    TargetRuntimeGeneratedArtifactVerificationRequest,
    verify_target_runtime_generated_artifacts,
)
from packages.daacs_builder.target_runtime_generated_workspace_static_validation import (
    TargetRuntimeGeneratedWorkspaceStaticValidationRequest,
    validate_target_runtime_generated_workspace_static,
)
from packages.daacs_builder.target_runtime_restricted_workspace_generation import (
    TargetRuntimeRestrictedWorkspaceGenerationRequest,
    generate_target_runtime_restricted_workspace,
)


RUN_ID = "run-build-02"


def _runner_plan_hash() -> str:
    return stable_contract_hash({"purpose": "buildable manifest"})


def _implementation_brief_hash() -> str:
    return stable_contract_hash({"artifact": "implementation_brief", "run_id": RUN_ID})


def _workspace_root(tmp_path):
    return tmp_path / "restricted-workspace"


def _bundle(run_id: str = RUN_ID) -> dict:
    bundle_hash = stable_contract_hash(
        {"run_id": run_id, "bundle": "buildable-fixture-manifest"}
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


def _static_validation(tmp_path, run_id: str = RUN_ID) -> dict:
    verification = _verification(tmp_path, run_id)
    return validate_target_runtime_generated_workspace_static(
        request=TargetRuntimeGeneratedWorkspaceStaticValidationRequest(
            run_id=run_id,
            generated_artifact_verification_hash=verification[
                "generated_artifact_verification_hash"
            ],
            generated_artifact_verification_projection=verification,
            workspace_root=_workspace_root(tmp_path),
        )
    ).to_dict()


def _request(
    tmp_path,
    *,
    static_validation: dict | None = None,
    **overrides,
) -> TargetRuntimeBuildableFixtureManifestRequest:
    selected_static_validation = static_validation or _static_validation(tmp_path)
    fields = {
        "run_id": RUN_ID,
        "generated_workspace_static_validation_hash": selected_static_validation[
            "generated_workspace_static_validation_hash"
        ],
        "generated_workspace_static_validation_projection": selected_static_validation,
        "workspace_root": _workspace_root(tmp_path),
        "metadata": {
            "raw_file_body": "AW_BUILD_02_RAW_SENTINEL",
            "provider_payload": "AW_BUILD_02_PROVIDER_SENTINEL",
        },
    }
    fields.update(overrides)
    return TargetRuntimeBuildableFixtureManifestRequest(**fields)


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def _path(relative: str, tmp_path):
    return _workspace_root(tmp_path) / f"runs/{RUN_ID}/generated-app/{relative}"


def test_buildable_fixture_manifest_passes_for_static_validated_workspace(tmp_path):
    result = create_target_runtime_buildable_fixture_manifest(
        request=_request(tmp_path)
    ).to_dict()
    serialized = _serialized(result)

    assert result["projection_version"] == TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION
    assert result["mode"] == TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE
    assert result["status"] == "passed"
    assert result["reason"] == "buildable_fixture_manifest_ready"
    assert result["build_ready_candidate"] is True
    assert result["counts"]["required_file_read_count"] == 5
    assert result["counts"]["required_script_present_count"] == 4
    assert result["counts"]["total_dependency_label_count"] >= 4
    assert result["counts"]["placeholder_dependency_value_count"] == 0
    assert result["counts"]["index_html_marker_present_count"] == 2
    assert result["counts"]["main_entrypoint_marker_present_count"] == 2
    assert result["counts"]["vite_config_marker_present_count"] == 2
    assert result["counts"]["tsconfig_marker_present_count"] == 2
    assert result["execution_boundary"]["package_install_calls"] == 0
    assert result["execution_boundary"]["build_calls"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert result["repository_boundary"]["root_path_returned"] is False
    assert result["repository_boundary"]["file_content_returned"] is False
    assert result["package_manifest"]["dependency_value_returned"] is False
    assert str(tmp_path) not in serialized
    assert "fixture-reference" not in serialized
    assert_public_projection_safe(result)


def test_buildable_fixture_manifest_blocks_missing_static_hash(tmp_path):
    result = create_target_runtime_buildable_fixture_manifest(
        request=_request(tmp_path, generated_workspace_static_validation_hash="")
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_workspace_static_validation_hash_missing_or_invalid"
    assert result["counts"]["required_file_read_count"] == 0


def test_buildable_fixture_manifest_blocks_static_hash_mismatch(tmp_path):
    result = create_target_runtime_buildable_fixture_manifest(
        request=_request(tmp_path, generated_workspace_static_validation_hash="a" * 64)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_workspace_static_validation_hash_mismatch"


def test_buildable_fixture_manifest_blocks_unpassed_static_validation(tmp_path):
    static_validation = _static_validation(tmp_path)
    static_validation = {**static_validation, "status": "blocked"}

    result = create_target_runtime_buildable_fixture_manifest(
        request=_request(tmp_path, static_validation=static_validation)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_workspace_static_validation_projection_status_invalid"


def test_buildable_fixture_manifest_blocks_invalid_package_json(tmp_path):
    static_validation = _static_validation(tmp_path)
    _path("package.json", tmp_path).write_text("{invalid json\n", encoding="utf-8")

    result = create_target_runtime_buildable_fixture_manifest(
        request=_request(tmp_path, static_validation=static_validation)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "build_manifest_package_json_invalid"


def test_buildable_fixture_manifest_blocks_placeholder_dependency_value(tmp_path):
    static_validation = _static_validation(tmp_path)
    package_path = _path("package.json", tmp_path)
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["dependencies"]["react"] = "fixture-reference"
    package_path.write_text(json.dumps(package, ensure_ascii=True), encoding="utf-8")

    result = create_target_runtime_buildable_fixture_manifest(
        request=_request(tmp_path, static_validation=static_validation)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "build_manifest_placeholder_dependency_values_present"
    assert result["counts"]["placeholder_dependency_value_count"] == 1


def test_buildable_fixture_manifest_blocks_missing_index_entry(tmp_path):
    static_validation = _static_validation(tmp_path)
    index_path = _path("index.html", tmp_path)
    content = index_path.read_text(encoding="utf-8")
    index_path.write_text(content.replace("/src/main.tsx", ""), encoding="utf-8")

    result = create_target_runtime_buildable_fixture_manifest(
        request=_request(tmp_path, static_validation=static_validation)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "build_manifest_index_html_entry_missing"
    assert result["counts"]["index_html_marker_present_count"] == 1


def test_buildable_fixture_manifest_exposes_no_private_material(tmp_path):
    result = create_target_runtime_buildable_fixture_manifest(
        request=_request(tmp_path)
    ).to_dict()
    serialized = _serialized(result)

    for forbidden in (
        "AW_BUILD_02_RAW_SENTINEL",
        "AW_BUILD_02_PROVIDER_SENTINEL",
        "raw_file_body",
        "provider_payload",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    assert result["counts"]["file_content_public_return_count"] == 0
    assert result["counts"]["local_root_path_return_count"] == 0
    assert result["counts"]["package_manifest_value_return_count"] == 0
    assert_public_projection_safe(result)


def test_buildable_fixture_manifest_does_not_spawn_read_env_or_call_network(
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

    result = create_target_runtime_buildable_fixture_manifest(
        request=_request(tmp_path)
    ).to_dict()

    assert result["status"] == "passed"
    assert result["execution_boundary"]["env_key_value_reads"] == 0
    assert result["execution_boundary"]["sdk_imports"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0

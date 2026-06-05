import builtins
import json
import os
import socket
import subprocess
import urllib.request

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_buildable_fixture_manifest import (
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
from packages.daacs_builder.target_runtime_local_build_preflight import (
    LOCAL_BUILD_PREFLIGHT_COMMAND_LABELS,
    TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE,
    TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION,
    TargetRuntimeLocalBuildPreflightRequest,
    create_target_runtime_local_build_preflight,
)
from packages.daacs_builder.target_runtime_restricted_workspace_generation import (
    TargetRuntimeRestrictedWorkspaceGenerationRequest,
    generate_target_runtime_restricted_workspace,
)


RUN_ID = "run-build-03"


def _runner_plan_hash() -> str:
    return stable_contract_hash({"purpose": "local build preflight"})


def _implementation_brief_hash() -> str:
    return stable_contract_hash({"artifact": "implementation_brief", "run_id": RUN_ID})


def _workspace_root(tmp_path):
    return tmp_path / "restricted-workspace"


def _bundle(run_id: str = RUN_ID) -> dict:
    bundle_hash = stable_contract_hash(
        {"run_id": run_id, "bundle": "local-build-preflight"}
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


def _buildable_manifest(tmp_path, run_id: str = RUN_ID) -> dict:
    static_validation = _static_validation(tmp_path, run_id)
    return create_target_runtime_buildable_fixture_manifest(
        request=TargetRuntimeBuildableFixtureManifestRequest(
            run_id=run_id,
            generated_workspace_static_validation_hash=static_validation[
                "generated_workspace_static_validation_hash"
            ],
            generated_workspace_static_validation_projection=static_validation,
            workspace_root=_workspace_root(tmp_path),
        )
    ).to_dict()


def _request(
    tmp_path,
    *,
    buildable_manifest: dict | None = None,
    operator_opt_in: bool = False,
    **overrides,
) -> TargetRuntimeLocalBuildPreflightRequest:
    selected_manifest = buildable_manifest or _buildable_manifest(tmp_path)
    fields = {
        "run_id": RUN_ID,
        "buildable_fixture_manifest_hash": selected_manifest[
            "buildable_fixture_manifest_hash"
        ],
        "buildable_fixture_manifest_projection": selected_manifest,
        "mode": TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE,
        "operator_opt_in": operator_opt_in,
        "metadata": {
            "raw_file_body": "AW_BUILD_03_RAW_SENTINEL",
            "provider_payload": "AW_BUILD_03_PROVIDER_SENTINEL",
        },
    }
    fields.update(overrides)
    return TargetRuntimeLocalBuildPreflightRequest(**fields)


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def test_local_build_preflight_passes_over_buildable_manifest(tmp_path):
    result = create_target_runtime_local_build_preflight(
        request=_request(tmp_path)
    ).to_dict()
    serialized = _serialized(result)

    assert result["projection_version"] == TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION
    assert result["mode"] == TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE
    assert result["status"] == "passed"
    assert result["reason"] == "local_build_preflight_ready"
    assert result["local_build_eligible"] is True
    assert result["local_build_opt_in_required"] is True
    assert result["operator_opt_in_present"] is False
    assert result["counts"]["command_plan_label_count"] == len(
        LOCAL_BUILD_PREFLIGHT_COMMAND_LABELS
    )
    assert result["counts"]["command_plan_hash_count"] == len(
        LOCAL_BUILD_PREFLIGHT_COMMAND_LABELS
    )
    assert result["counts"]["default_execution_permission_count"] == 0
    assert result["execution_boundary"]["package_install_calls"] == 0
    assert result["execution_boundary"]["build_calls"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert result["repository_boundary"]["root_path_returned"] is False
    assert result["repository_boundary"]["file_content_returned"] is False
    assert result["repository_boundary"]["dependency_value_returned"] is False
    assert "AW_BUILD_03_RAW_SENTINEL" not in serialized
    assert "AW_BUILD_03_PROVIDER_SENTINEL" not in serialized
    assert str(tmp_path) not in serialized
    assert_public_projection_safe(result)


def test_local_build_preflight_blocks_missing_manifest_hash(tmp_path):
    result = create_target_runtime_local_build_preflight(
        request=_request(tmp_path, buildable_fixture_manifest_hash="")
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "buildable_fixture_manifest_hash_missing_or_invalid"
    assert result["local_build_eligible"] is False
    assert result["counts"]["command_plan_label_count"] == 0
    assert result["execution_boundary"]["execution_permission_count"] == 0


def test_local_build_preflight_blocks_manifest_hash_mismatch(tmp_path):
    result = create_target_runtime_local_build_preflight(
        request=_request(tmp_path, buildable_fixture_manifest_hash="a" * 64)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "buildable_fixture_manifest_hash_mismatch"
    assert result["local_build_eligible"] is False


def test_local_build_preflight_blocks_unpassed_manifest(tmp_path):
    manifest = _buildable_manifest(tmp_path)
    manifest = {**manifest, "status": "blocked"}

    result = create_target_runtime_local_build_preflight(
        request=_request(tmp_path, buildable_manifest=manifest)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "buildable_fixture_manifest_projection_status_invalid"


def test_local_build_preflight_blocks_run_mismatch(tmp_path):
    manifest = _buildable_manifest(tmp_path)
    manifest = {**manifest, "run_id": "run-other"}

    result = create_target_runtime_local_build_preflight(
        request=_request(tmp_path, buildable_manifest=manifest)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "buildable_fixture_manifest_run_mismatch"


def test_local_build_preflight_blocks_unsanitized_package_values(tmp_path):
    manifest = _buildable_manifest(tmp_path)
    package_manifest = {**manifest["package_manifest"], "dependency_value_returned": True}
    counts = {**manifest["counts"], "package_manifest_value_return_count": 1}
    manifest = {**manifest, "package_manifest": package_manifest, "counts": counts}

    result = create_target_runtime_local_build_preflight(
        request=_request(tmp_path, buildable_manifest=manifest)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "buildable_fixture_manifest_public_values_not_sanitized"


def test_local_build_preflight_operator_opt_in_does_not_grant_execution(tmp_path):
    result = create_target_runtime_local_build_preflight(
        request=_request(tmp_path, operator_opt_in=True)
    ).to_dict()

    assert result["status"] == "passed"
    assert result["operator_opt_in_present"] is True
    assert result["counts"]["operator_opt_in_present_count"] == 1
    assert result["counts"]["default_execution_permission_count"] == 0
    assert result["execution_boundary"]["execution_permission_count"] == 0
    assert result["execution_boundary"]["package_install_calls"] == 0
    assert result["execution_boundary"]["build_calls"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0


def test_local_build_preflight_does_not_spawn_read_env_or_call_network(
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

    result = create_target_runtime_local_build_preflight(
        request=_request(tmp_path)
    ).to_dict()

    assert result["status"] == "passed"
    assert result["execution_boundary"]["env_key_value_reads"] == 0
    assert result["execution_boundary"]["sdk_imports"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0

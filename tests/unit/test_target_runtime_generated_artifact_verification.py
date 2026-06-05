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
    TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE,
    TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION,
    TargetRuntimeGeneratedArtifactVerificationRequest,
    verify_target_runtime_generated_artifacts,
)
from packages.daacs_builder.target_runtime_restricted_workspace_generation import (
    TargetRuntimeRestrictedWorkspaceGenerationRequest,
    generate_target_runtime_restricted_workspace,
)


RUN_ID = "run-verify-01"


def _runner_plan_hash() -> str:
    return stable_contract_hash({"purpose": "verify generated artifact"})


def _implementation_brief_hash() -> str:
    return stable_contract_hash({"artifact": "implementation_brief", "run_id": RUN_ID})


def _bundle(run_id: str = RUN_ID) -> dict:
    bundle_hash = stable_contract_hash(
        {"run_id": run_id, "bundle": "generated-artifact-verification"}
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
            workspace_root=tmp_path / "restricted-workspace",
        )
    ).to_dict()


def _request(tmp_path, **overrides) -> TargetRuntimeGeneratedArtifactVerificationRequest:
    generated_workspace = _generated_workspace(tmp_path)
    fields = {
        "run_id": RUN_ID,
        "generated_workspace_hash": generated_workspace["generated_workspace_hash"],
        "generated_workspace_projection": generated_workspace,
        "workspace_root": tmp_path / "restricted-workspace",
        "metadata": {
            "raw_file_body": "AW_VERIFY_01_RAW_SENTINEL",
            "runtime_payload": "AW_VERIFY_01_RUNTIME_SENTINEL",
        },
    }
    fields.update(overrides)
    return TargetRuntimeGeneratedArtifactVerificationRequest(**fields)


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def test_generated_artifact_verification_passes_for_generated_workspace(tmp_path):
    result = verify_target_runtime_generated_artifacts(
        request=_request(tmp_path)
    ).to_dict()
    serialized = _serialized(result)

    assert result["projection_version"] == (
        TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION
    )
    assert result["mode"] == TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE
    assert result["status"] == "passed"
    assert result["reason"] == "generated_artifact_files_verified"
    assert result["counts"]["expected_file_count"] == 9
    assert result["counts"]["expected_file_present_count"] == 9
    assert result["counts"]["file_check_record_count"] == 9
    assert result["counts"]["file_exists_count"] == 9
    assert result["counts"]["file_read_count"] == 9
    assert result["counts"]["content_hash_match_count"] == 9
    assert result["counts"]["byte_count_match_count"] == 9
    assert result["counts"]["file_content_public_return_count"] == 0
    assert result["counts"]["local_root_path_return_count"] == 0
    assert result["execution_boundary"]["generated_workspace_file_read_count"] == 9
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["execution_boundary"]["provider_calls"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert result["execution_boundary"]["package_install_calls"] == 0
    assert result["execution_boundary"]["build_calls"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert result["repository_boundary"]["root_path_returned"] is False
    assert result["repository_boundary"]["file_content_returned"] is False
    assert str(tmp_path) not in serialized
    assert_public_projection_safe(result)


def test_generated_artifact_verification_blocks_missing_workspace_hash(tmp_path):
    result = verify_target_runtime_generated_artifacts(
        request=_request(tmp_path, generated_workspace_hash="")
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_workspace_hash_missing_or_invalid"
    assert result["counts"]["file_read_count"] == 0


def test_generated_artifact_verification_blocks_workspace_hash_mismatch(tmp_path):
    result = verify_target_runtime_generated_artifacts(
        request=_request(tmp_path, generated_workspace_hash="a" * 64)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_workspace_hash_mismatch"
    assert result["counts"]["generated_workspace_hash_match_count"] == 0
    assert result["counts"]["file_read_count"] == 0


def test_generated_artifact_verification_blocks_missing_expected_file_record(tmp_path):
    generated_workspace = _generated_workspace(tmp_path)
    generated_workspace["file_records"] = generated_workspace["file_records"][:-1]

    result = verify_target_runtime_generated_artifacts(
        request=TargetRuntimeGeneratedArtifactVerificationRequest(
            run_id=RUN_ID,
            generated_workspace_hash=generated_workspace["generated_workspace_hash"],
            generated_workspace_projection=generated_workspace,
            workspace_root=tmp_path / "restricted-workspace",
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_workspace_expected_file_missing"
    assert result["counts"]["missing_expected_file_count"] == 1
    assert result["counts"]["file_read_count"] == 0


def test_generated_artifact_verification_blocks_missing_local_file(tmp_path):
    generated_workspace = _generated_workspace(tmp_path)
    record = generated_workspace["file_records"][0]
    (tmp_path / "restricted-workspace" / record["workspace_relative_path"]).unlink()

    result = verify_target_runtime_generated_artifacts(
        request=TargetRuntimeGeneratedArtifactVerificationRequest(
            run_id=RUN_ID,
            generated_workspace_hash=generated_workspace["generated_workspace_hash"],
            generated_workspace_projection=generated_workspace,
            workspace_root=tmp_path / "restricted-workspace",
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_workspace_file_missing"
    assert result["counts"]["missing_local_file_count"] == 1
    assert result["counts"]["file_content_public_return_count"] == 0


def test_generated_artifact_verification_blocks_content_hash_mismatch(tmp_path):
    generated_workspace = _generated_workspace(tmp_path)
    record = generated_workspace["file_records"][0]
    output_path = tmp_path / "restricted-workspace" / record["workspace_relative_path"]
    output_path.write_text("tampered fixture content\n", encoding="utf-8")

    result = verify_target_runtime_generated_artifacts(
        request=TargetRuntimeGeneratedArtifactVerificationRequest(
            run_id=RUN_ID,
            generated_workspace_hash=generated_workspace["generated_workspace_hash"],
            generated_workspace_projection=generated_workspace,
            workspace_root=tmp_path / "restricted-workspace",
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_workspace_content_hash_mismatch"
    assert result["counts"]["content_hash_match_count"] == 8


def test_generated_artifact_verification_blocks_path_traversal_record(tmp_path):
    generated_workspace = _generated_workspace(tmp_path)
    generated_workspace["file_records"][0] = {
        **generated_workspace["file_records"][0],
        "workspace_relative_path": "../outside.md",
    }

    result = verify_target_runtime_generated_artifacts(
        request=TargetRuntimeGeneratedArtifactVerificationRequest(
            run_id=RUN_ID,
            generated_workspace_hash=generated_workspace["generated_workspace_hash"],
            generated_workspace_projection=generated_workspace,
            workspace_root=tmp_path / "restricted-workspace",
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_workspace_file_path_outside_run"
    assert result["counts"]["path_traversal_block_count"] == 1
    assert result["counts"]["file_content_public_return_count"] == 0


def test_generated_artifact_verification_blocks_absolute_record_path(tmp_path):
    generated_workspace = _generated_workspace(tmp_path)
    generated_workspace["file_records"][0] = {
        **generated_workspace["file_records"][0],
        "workspace_relative_path": "C:/outside.md",
    }

    result = verify_target_runtime_generated_artifacts(
        request=TargetRuntimeGeneratedArtifactVerificationRequest(
            run_id=RUN_ID,
            generated_workspace_hash=generated_workspace["generated_workspace_hash"],
            generated_workspace_projection=generated_workspace,
            workspace_root=tmp_path / "restricted-workspace",
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_workspace_file_path_absolute"
    assert result["counts"]["absolute_path_block_count"] == 1
    assert result["counts"]["file_content_public_return_count"] == 0


def test_generated_artifact_verification_exposes_no_private_material(tmp_path):
    result = verify_target_runtime_generated_artifacts(
        request=_request(tmp_path)
    ).to_dict()
    serialized = _serialized(result)

    for forbidden in (
        "AW_VERIFY_01_RAW_SENTINEL",
        "AW_VERIFY_01_RUNTIME_SENTINEL",
        "raw_file_body",
        "runtime_payload",
        "provider_payload",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    for record in result["file_check_records"]:
        assert record["content_included"] is False
        assert record["root_path_returned"] is False
    assert_public_projection_safe(result)


def test_generated_artifact_verification_does_not_spawn_read_env_or_call_network(
    tmp_path,
    monkeypatch,
):
    def blocked_run(*args, **kwargs):
        raise AssertionError("subprocess attempted")

    def blocked_getenv(*args, **kwargs):
        raise AssertionError("env value read attempted")

    def blocked_socket(*args, **kwargs):
        raise AssertionError("network socket attempted")

    def blocked_urlopen(*args, **kwargs):
        raise AssertionError("network urlopen attempted")

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".", 1)[0] in {"upstage", "openai", "requests", "httpx"}:
            raise AssertionError(f"runtime/provider SDK import attempted: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(os, "getenv", blocked_getenv)
    monkeypatch.setattr(socket, "socket", blocked_socket)
    monkeypatch.setattr(urllib.request, "urlopen", blocked_urlopen)
    monkeypatch.setattr(subprocess, "run", blocked_run)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    result = verify_target_runtime_generated_artifacts(
        request=_request(tmp_path)
    ).to_dict()

    assert result["status"] == "passed"
    assert result["counts"]["file_read_count"] == 9
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["execution_boundary"]["provider_calls"] == 0
    assert result["execution_boundary"]["sdk_imports"] == 0
    assert result["execution_boundary"]["env_key_value_reads"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0
    assert result["execution_boundary"]["network_calls"] == 0

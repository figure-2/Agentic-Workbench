import builtins
import json
import os
import socket
import subprocess
import urllib.request

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_admission import (
    DisabledTargetRuntimeAdapter,
    TargetRuntimeAdapterAdmissionRequest,
    TargetRuntimeAdapterAdmissionService,
    invoke_disabled_target_runtime_adapter_after_preflight_admission,
)
from packages.daacs_builder.target_runtime_admission_store import (
    InMemoryTargetRuntimeAdapterAdmissionRepository,
    target_runtime_adapter_admission_public_read_model,
    target_runtime_adapter_admission_record_from_result,
)
from packages.daacs_builder.target_runtime_generated_artifact_bundle import (
    TargetRuntimeGeneratedArtifactBundleRequest,
    build_disabled_target_runtime_generated_artifact_bundle,
)
from packages.daacs_builder.target_runtime_output_manifest import (
    TargetRuntimeOutputManifestRequest,
    build_disabled_target_runtime_output_manifest,
)
from packages.daacs_builder.target_runtime_output_manifest_store import (
    InMemoryTargetRuntimeOutputManifestRepository,
    target_runtime_output_manifest_public_read_model,
    target_runtime_output_manifest_record_from_result,
)
from packages.daacs_builder.target_runtime_restricted_workspace_generation import (
    RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS,
    TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE,
    TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION,
    TargetRuntimeRestrictedWorkspaceGenerationRequest,
    generate_target_runtime_restricted_workspace,
)
from packages.daacs_builder.target_runtime_sandbox import (
    TargetRuntimePreflightRequest,
    TargetRuntimePreflightService,
    ready_target_runtime_command_policy,
    ready_target_runtime_rollback_policy,
    ready_target_runtime_sandbox_policy,
    ready_target_runtime_workspace_intent,
)


RUN_ID = "run-daacs-runtime-mvp-01"


def _runner_plan_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "restricted workspace generation",
            "runner_plan": "hash-only",
        }
    )


def _implementation_brief_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "implementation brief",
            "artifact": "hash-only",
        }
    )


def _planning_blueprint_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "planning blueprint",
            "artifact": "hash-only",
        }
    )


def _prd_package_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "prd package",
            "artifact": "hash-only",
        }
    )


def _preflight(run_id: str = RUN_ID) -> dict:
    request = TargetRuntimePreflightRequest(
        run_id=run_id,
        runner_plan_hash=_runner_plan_hash(),
        sandbox_policy=ready_target_runtime_sandbox_policy(),
        workspace_intent=ready_target_runtime_workspace_intent(run_id),
        command_policy=ready_target_runtime_command_policy(),
        rollback_policy=ready_target_runtime_rollback_policy(),
        metadata={
            "raw_prompt": "DAACS_RUNTIME_MVP_01_PREFLIGHT_RAW_SENTINEL",
            "runtime_payload": "DAACS_RUNTIME_MVP_01_PREFLIGHT_PAYLOAD_SENTINEL",
        },
    )
    return TargetRuntimePreflightService().preflight(request).to_dict()


def _admission_result(run_id: str = RUN_ID) -> dict:
    preflight = _preflight(run_id)
    request = TargetRuntimeAdapterAdmissionRequest(
        run_id=run_id,
        runner_plan_hash=_runner_plan_hash(),
        expected_preflight_hash=preflight["preflight_hash"],
        preflight_projection=preflight,
        metadata={
            "raw_file_body": "DAACS_RUNTIME_MVP_01_ADMISSION_RAW_SENTINEL",
        },
    )
    return invoke_disabled_target_runtime_adapter_after_preflight_admission(
        adapter=DisabledTargetRuntimeAdapter(),
        request=request,
        admission_service=TargetRuntimeAdapterAdmissionService(),
    ).to_dict()


def _adapter_read_model(run_id: str = RUN_ID):
    repository = InMemoryTargetRuntimeAdapterAdmissionRepository()
    record = target_runtime_adapter_admission_record_from_result(
        _admission_result(run_id)
    )
    repository.save(record)
    read_model = target_runtime_adapter_admission_public_read_model(
        repository,
        run_id=run_id,
    )
    return repository, record, read_model


def _output_manifest_read_model(run_id: str = RUN_ID):
    _, adapter_record, adapter_read_model = _adapter_read_model(run_id)
    manifest = build_disabled_target_runtime_output_manifest(
        request=TargetRuntimeOutputManifestRequest(
            run_id=run_id,
            runner_plan_hash=_runner_plan_hash(),
            adapter_admission_hash=adapter_record.adapter_admission_hash,
            adapter_admission_read_model=adapter_read_model,
            metadata={
                "raw_file_body": "DAACS_RUNTIME_MVP_01_MANIFEST_RAW_SENTINEL",
            },
        )
    ).to_dict()
    repository = InMemoryTargetRuntimeOutputManifestRepository()
    record = target_runtime_output_manifest_record_from_result(manifest)
    repository.save(record)
    read_model = target_runtime_output_manifest_public_read_model(
        repository,
        run_id=run_id,
    )
    return repository, record, read_model


def _bundle(run_id: str = RUN_ID) -> dict:
    _, manifest_record, manifest_read_model = _output_manifest_read_model(run_id)
    return build_disabled_target_runtime_generated_artifact_bundle(
        request=TargetRuntimeGeneratedArtifactBundleRequest(
            run_id=run_id,
            runner_plan_hash=_runner_plan_hash(),
            output_manifest_hash=manifest_record.output_manifest_hash,
            output_manifest_read_model=manifest_read_model,
            metadata={
                "raw_file_body": "DAACS_RUNTIME_MVP_01_BUNDLE_RAW_SENTINEL",
            },
        )
    ).to_dict()


def _request(tmp_path, **overrides) -> TargetRuntimeRestrictedWorkspaceGenerationRequest:
    bundle = _bundle()
    fields = {
        "run_id": RUN_ID,
        "runner_plan_hash": _runner_plan_hash(),
        "planning_blueprint_hash": _planning_blueprint_hash(),
        "prd_package_hash": _prd_package_hash(),
        "implementation_brief_hash": _implementation_brief_hash(),
        "generated_artifact_bundle_hash": bundle["generated_artifact_bundle_hash"],
        "generated_artifact_bundle_projection": bundle,
        "workspace_root": tmp_path / "restricted-workspace",
        "metadata": {
            "raw_file_body": "DAACS_RUNTIME_MVP_01_REQUEST_RAW_SENTINEL",
            "runtime_payload": "DAACS_RUNTIME_MVP_01_REQUEST_PAYLOAD_SENTINEL",
        },
    }
    fields.update(overrides)
    return TargetRuntimeRestrictedWorkspaceGenerationRequest(**fields)


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def test_restricted_workspace_generation_writes_minimal_skeleton(tmp_path):
    result = generate_target_runtime_restricted_workspace(
        request=_request(tmp_path)
    ).to_dict()
    serialized = _serialized(result)

    assert result["projection_version"] == (
        TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION
    )
    assert result["mode"] == TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE
    assert result["status"] == "passed"
    assert result["reason"] == "target_runtime_restricted_workspace_generated"
    assert result["counts"]["generated_artifact_bundle_hash_match_count"] == 1
    assert result["counts"]["codegen_input_hash_count"] == 1
    assert result["counts"]["codegen_input_document_hash_count"] == 3
    assert result["counts"]["planning_blueprint_hash_present_count"] == 1
    assert result["counts"]["prd_package_hash_present_count"] == 1
    assert result["counts"]["implementation_brief_hash_present_count"] == 1
    assert result["counts"]["generated_workspace_file_record_count"] == 9
    assert result["counts"]["generated_workspace_file_hash_count"] == 9
    assert result["counts"]["restricted_workspace_file_write_count"] == 9
    assert result["counts"]["file_content_public_return_count"] == 0
    assert result["counts"]["local_root_path_return_count"] == 0
    assert result["execution_boundary"]["restricted_workspace_file_write_count"] == 9
    assert result["execution_boundary"]["filesystem_writes_outside_workspace"] == 0
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["execution_boundary"]["provider_calls"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert result["execution_boundary"]["package_install_calls"] == 0
    assert result["execution_boundary"]["build_calls"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert result["repository_boundary"]["root_path_returned"] is False
    assert result["repository_boundary"]["file_content_returned"] is False
    assert result["document_input_summary"]["source"] == "fixture_planning_documents"
    assert result["document_input_summary"]["document_hash_count"] == 3
    assert len(result["codegen_input_hash"]) == 64
    assert str(tmp_path) not in serialized

    expected_paths = {
        "runs/run-daacs-runtime-mvp-01/generated-app/README.md",
        "runs/run-daacs-runtime-mvp-01/generated-app/index.html",
        "runs/run-daacs-runtime-mvp-01/generated-app/package.json",
        "runs/run-daacs-runtime-mvp-01/generated-app/src/App.tsx",
        "runs/run-daacs-runtime-mvp-01/generated-app/src/api.ts",
        "runs/run-daacs-runtime-mvp-01/generated-app/src/main.tsx",
        "runs/run-daacs-runtime-mvp-01/generated-app/tests/verification.md",
        "runs/run-daacs-runtime-mvp-01/generated-app/tsconfig.json",
        "runs/run-daacs-runtime-mvp-01/generated-app/vite.config.ts",
    }
    assert {record["workspace_relative_path"] for record in result["file_records"]} == expected_paths
    for record in result["file_records"]:
        assert record["content_included"] is False
        assert record["root_path_returned"] is False
        output_path = tmp_path / "restricted-workspace" / record["workspace_relative_path"]
        assert output_path.exists()
        assert output_path.read_text(encoding="utf-8").strip()
    app_content = (
        tmp_path
        / "restricted-workspace"
        / "runs/run-daacs-runtime-mvp-01/generated-app/src/App.tsx"
    ).read_text(encoding="utf-8")
    api_content = (
        tmp_path
        / "restricted-workspace"
        / "runs/run-daacs-runtime-mvp-01/generated-app/src/api.ts"
    ).read_text(encoding="utf-8")
    assert "Task Board" in app_content
    assert "getFixtureTasks" in app_content
    assert "export type FixtureTask" in api_content
    assert "codegenInputHash" in api_content
    assert_public_projection_safe(result)


def test_restricted_workspace_generation_blocks_missing_bundle_projection(tmp_path):
    result = generate_target_runtime_restricted_workspace(
        request=_request(
            tmp_path,
            generated_artifact_bundle_projection={},
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_artifact_bundle_projection_missing"
    assert result["counts"]["restricted_workspace_file_write_count"] == 0
    assert not (tmp_path / "restricted-workspace").exists()


def test_restricted_workspace_generation_blocks_bundle_hash_mismatch(tmp_path):
    result = generate_target_runtime_restricted_workspace(
        request=_request(
            tmp_path,
            generated_artifact_bundle_hash="a" * 64,
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "generated_artifact_bundle_hash_mismatch"
    assert result["counts"]["generated_artifact_bundle_hash_match_count"] == 0
    assert result["counts"]["restricted_workspace_file_write_count"] == 0
    assert not (tmp_path / "restricted-workspace").exists()


def test_restricted_workspace_generation_blocks_unsafe_run_id(tmp_path):
    bundle = _bundle()
    result = generate_target_runtime_restricted_workspace(
        request=TargetRuntimeRestrictedWorkspaceGenerationRequest(
            run_id="../bad-run",
            runner_plan_hash=_runner_plan_hash(),
            implementation_brief_hash=_implementation_brief_hash(),
            generated_artifact_bundle_hash=bundle["generated_artifact_bundle_hash"],
            generated_artifact_bundle_projection=bundle,
            workspace_root=tmp_path / "restricted-workspace",
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "run_id_invalid"
    assert result["counts"]["restricted_workspace_file_write_count"] == 0
    assert not (tmp_path / "restricted-workspace").exists()


def test_restricted_workspace_generation_blocks_template_path_escape(tmp_path):
    result = generate_target_runtime_restricted_workspace(
        request=_request(
            tmp_path,
            template_ids=("../bad", *RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS),
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "restricted_workspace_template_id_unsafe"
    assert result["counts"]["restricted_workspace_file_write_count"] == 0
    assert not (tmp_path / "restricted-workspace").exists()


def test_restricted_workspace_generation_blocks_absolute_template_id(tmp_path):
    result = generate_target_runtime_restricted_workspace(
        request=_request(
            tmp_path,
            template_ids=("/tmp/bad", *RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS),
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "restricted_workspace_template_id_unsafe"
    assert result["counts"]["restricted_workspace_file_write_count"] == 0
    assert not (tmp_path / "restricted-workspace").exists()


def test_restricted_workspace_generation_requires_implementation_brief_hash(tmp_path):
    result = generate_target_runtime_restricted_workspace(
        request=_request(
            tmp_path,
            implementation_brief_hash="not-a-contract-hash",
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "implementation_brief_hash_invalid"
    assert result["counts"]["restricted_workspace_file_write_count"] == 0
    assert not (tmp_path / "restricted-workspace").exists()


def test_restricted_workspace_generation_exposes_no_private_material(tmp_path):
    result = generate_target_runtime_restricted_workspace(
        request=_request(tmp_path)
    ).to_dict()
    serialized = _serialized(result)
    file_text = "\n".join(
        (tmp_path / "restricted-workspace" / record["workspace_relative_path"])
        .read_text(encoding="utf-8")
        for record in result["file_records"]
    )

    for forbidden in (
        "DAACS_RUNTIME_MVP_01_PREFLIGHT_RAW_SENTINEL",
        "DAACS_RUNTIME_MVP_01_PREFLIGHT_PAYLOAD_SENTINEL",
        "DAACS_RUNTIME_MVP_01_ADMISSION_RAW_SENTINEL",
        "DAACS_RUNTIME_MVP_01_MANIFEST_RAW_SENTINEL",
        "DAACS_RUNTIME_MVP_01_BUNDLE_RAW_SENTINEL",
        "DAACS_RUNTIME_MVP_01_REQUEST_RAW_SENTINEL",
        "DAACS_RUNTIME_MVP_01_REQUEST_PAYLOAD_SENTINEL",
        "raw_prompt",
        "runtime_payload",
        "raw_file_body",
        "provider_payload",
        str(tmp_path),
    ):
        assert forbidden not in serialized
        assert forbidden not in file_text
    assert_public_projection_safe(result)


def test_restricted_workspace_generation_does_not_spawn_read_env_or_call_network(
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

    result = generate_target_runtime_restricted_workspace(
        request=_request(tmp_path)
    ).to_dict()

    assert result["status"] == "passed"
    assert result["execution_boundary"]["restricted_workspace_file_write_count"] == 9
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["execution_boundary"]["provider_calls"] == 0
    assert result["execution_boundary"]["sdk_imports"] == 0
    assert result["execution_boundary"]["env_key_value_reads"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0
    assert result["execution_boundary"]["network_calls"] == 0

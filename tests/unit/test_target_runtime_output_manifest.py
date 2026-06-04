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
from packages.daacs_builder.target_runtime_output_manifest import (
    TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
    TARGET_RUNTIME_OUTPUT_MANIFEST_VERSION,
    TargetRuntimeOutputManifestRequest,
    build_disabled_target_runtime_output_manifest,
    build_disabled_target_runtime_output_manifest_from_repository,
)
from packages.daacs_builder.target_runtime_sandbox import (
    TargetRuntimePreflightRequest,
    TargetRuntimePreflightService,
    ready_target_runtime_command_policy,
    ready_target_runtime_rollback_policy,
    ready_target_runtime_sandbox_policy,
    ready_target_runtime_workspace_intent,
)


RUN_ID = "run-daacs-runtime-03"


def _runner_plan_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "target runtime output manifest",
            "runner_plan": "hash-only",
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
            "raw_prompt": "DAACS_OUTPUT_MANIFEST_RAW_PROMPT_SENTINEL",
            "runtime_payload": "DAACS_OUTPUT_MANIFEST_RUNTIME_SENTINEL",
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
            "raw_file_body": "DAACS_OUTPUT_MANIFEST_RAW_FILE_SENTINEL",
        },
    )
    return invoke_disabled_target_runtime_adapter_after_preflight_admission(
        adapter=DisabledTargetRuntimeAdapter(),
        request=request,
        admission_service=TargetRuntimeAdapterAdmissionService(),
    ).to_dict()


def _repository_and_read_model(run_id: str = RUN_ID):
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


def _manifest_request(**overrides) -> TargetRuntimeOutputManifestRequest:
    _, record, read_model = _repository_and_read_model()
    fields = {
        "run_id": RUN_ID,
        "runner_plan_hash": _runner_plan_hash(),
        "adapter_admission_hash": record.adapter_admission_hash,
        "adapter_admission_read_model": read_model,
        "metadata": {
            "raw_file_body": "DAACS_OUTPUT_MANIFEST_REQUEST_RAW_SENTINEL",
            "runtime_payload": "DAACS_OUTPUT_MANIFEST_REQUEST_PAYLOAD_SENTINEL",
        },
    }
    fields.update(overrides)
    return TargetRuntimeOutputManifestRequest(**fields)


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def test_target_runtime_output_manifest_builds_blocked_hash_only_contract():
    result = build_disabled_target_runtime_output_manifest(
        request=_manifest_request()
    )
    public = result.to_dict()

    assert public["projection_version"] == TARGET_RUNTIME_OUTPUT_MANIFEST_VERSION
    assert public["mode"] == TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED
    assert public["status"] == "blocked"
    assert public["reason"] == "target_runtime_output_manifest_execution_closed"
    assert public["counts"]["adapter_admission_read_model_count"] == 1
    assert public["counts"]["adapter_admission_hash_match_count"] == 1
    assert public["counts"]["output_group_count"] == 3
    assert public["counts"]["output_group_hash_count"] == 3
    assert public["counts"]["generated_artifact_body_write_count"] == 0
    assert public["execution_boundary"]["execution_permission_count"] == 0
    assert public["execution_boundary"]["target_runtime_calls"] == 0
    assert public["execution_boundary"]["filesystem_writes"] == 0
    assert public["execution_boundary"]["subprocess_calls"] == 0
    assert public["execution_boundary"]["network_calls"] == 0
    assert public["claim_boundary"]["target_runtime_outcome"] is False
    assert public["claim_boundary"]["generated_artifact_body"] is False
    assert_public_projection_safe(public)


def test_target_runtime_output_manifest_can_build_from_repository_read_model():
    repository, record, _ = _repository_and_read_model()

    result = build_disabled_target_runtime_output_manifest_from_repository(
        repository=repository,
        run_id=RUN_ID,
        runner_plan_hash=_runner_plan_hash(),
        adapter_admission_hash=record.adapter_admission_hash,
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "target_runtime_output_manifest_execution_closed"
    assert result["counts"]["adapter_admission_hash_match_count"] == 1
    assert result["counts"]["output_group_count"] == 3


def test_target_runtime_output_manifest_blocks_missing_read_model():
    result = build_disabled_target_runtime_output_manifest(
        request=_manifest_request(adapter_admission_read_model={})
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "adapter_admission_read_model_missing"
    assert result["counts"]["adapter_admission_read_model_count"] == 0
    assert result["counts"]["execution_permission_count"] == 0


def test_target_runtime_output_manifest_blocks_unavailable_read_model():
    _, record, read_model = _repository_and_read_model()
    read_model["status"] = "blocked"

    result = build_disabled_target_runtime_output_manifest(
        request=_manifest_request(
            adapter_admission_hash=record.adapter_admission_hash,
            adapter_admission_read_model=read_model,
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "adapter_admission_read_model_unavailable"
    assert result["counts"]["adapter_admission_hash_match_count"] == 1


def test_target_runtime_output_manifest_blocks_adapter_hash_mismatch():
    result = build_disabled_target_runtime_output_manifest(
        request=_manifest_request(adapter_admission_hash="a" * 64)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "adapter_admission_hash_mismatch"
    assert result["counts"]["adapter_admission_hash_match_count"] == 0
    assert result["counts"]["execution_permission_count"] == 0


def test_target_runtime_output_manifest_exposes_no_raw_body_or_generated_source():
    result = build_disabled_target_runtime_output_manifest(
        request=_manifest_request(
            output_groups=[
                {
                    "label": "backend",
                    "expected_artifact_kind": "backend",
                    "expected_file_count": 0,
                    "raw_file_body": "DAACS_OUTPUT_MANIFEST_GROUP_RAW_SENTINEL",
                    "source_code": "DAACS_OUTPUT_MANIFEST_SOURCE_SENTINEL",
                },
                {"label": "frontend", "expected_artifact_kind": "frontend"},
                {
                    "label": "verification_report",
                    "expected_artifact_kind": "verification_report",
                },
            ]
        )
    ).to_dict()
    serialized = _serialized(result)

    for forbidden in (
        "DAACS_OUTPUT_MANIFEST_RAW_PROMPT_SENTINEL",
        "DAACS_OUTPUT_MANIFEST_RUNTIME_SENTINEL",
        "DAACS_OUTPUT_MANIFEST_RAW_FILE_SENTINEL",
        "DAACS_OUTPUT_MANIFEST_REQUEST_RAW_SENTINEL",
        "DAACS_OUTPUT_MANIFEST_REQUEST_PAYLOAD_SENTINEL",
        "DAACS_OUTPUT_MANIFEST_GROUP_RAW_SENTINEL",
        "DAACS_OUTPUT_MANIFEST_SOURCE_SENTINEL",
        "raw_prompt",
        "runtime_payload",
        "raw_file_body",
        "source_code",
        "provider_payload",
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(result)


def test_target_runtime_output_manifest_does_not_write_spawn_read_env_or_call_network(
    monkeypatch,
):
    def blocked_write(*args, **kwargs):
        raise AssertionError("filesystem write attempted")

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

    request = _manifest_request()
    monkeypatch.setattr(os, "getenv", blocked_getenv)
    monkeypatch.setattr(socket, "socket", blocked_socket)
    monkeypatch.setattr(urllib.request, "urlopen", blocked_urlopen)
    monkeypatch.setattr(subprocess, "run", blocked_run)
    monkeypatch.setattr(builtins, "open", blocked_write)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    result = build_disabled_target_runtime_output_manifest(request=request).to_dict()

    assert result["status"] == "blocked"
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["execution_boundary"]["filesystem_writes"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0
    assert result["execution_boundary"]["network_calls"] == 0

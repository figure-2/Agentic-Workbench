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
    TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED,
    TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
    TargetRuntimeGeneratedArtifactBundleRequest,
    build_disabled_target_runtime_generated_artifact_bundle,
    build_disabled_target_runtime_generated_artifact_bundle_from_repository,
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
from packages.daacs_builder.target_runtime_sandbox import (
    TargetRuntimePreflightRequest,
    TargetRuntimePreflightService,
    ready_target_runtime_command_policy,
    ready_target_runtime_rollback_policy,
    ready_target_runtime_sandbox_policy,
    ready_target_runtime_workspace_intent,
)


RUN_ID = "run-daacs-runtime-05"


def _runner_plan_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "target runtime generated artifact bundle",
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
            "raw_prompt": "DAACS_GENERATED_BUNDLE_RAW_PROMPT_SENTINEL",
            "runtime_payload": "DAACS_GENERATED_BUNDLE_RUNTIME_SENTINEL",
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
            "raw_file_body": "DAACS_GENERATED_BUNDLE_ADMISSION_RAW_SENTINEL",
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


def _output_manifest_result(run_id: str = RUN_ID) -> dict:
    _, adapter_record, adapter_read_model = _adapter_read_model(run_id)
    request = TargetRuntimeOutputManifestRequest(
        run_id=run_id,
        runner_plan_hash=_runner_plan_hash(),
        adapter_admission_hash=adapter_record.adapter_admission_hash,
        adapter_admission_read_model=adapter_read_model,
        metadata={
            "raw_file_body": "DAACS_GENERATED_BUNDLE_MANIFEST_RAW_SENTINEL",
        },
    )
    return build_disabled_target_runtime_output_manifest(request=request).to_dict()


def _output_manifest_read_model(run_id: str = RUN_ID):
    repository = InMemoryTargetRuntimeOutputManifestRepository()
    record = target_runtime_output_manifest_record_from_result(
        _output_manifest_result(run_id)
    )
    repository.save(record)
    read_model = target_runtime_output_manifest_public_read_model(
        repository,
        run_id=run_id,
    )
    return repository, record, read_model


def _bundle_request(**overrides) -> TargetRuntimeGeneratedArtifactBundleRequest:
    _, record, read_model = _output_manifest_read_model()
    fields = {
        "run_id": RUN_ID,
        "runner_plan_hash": _runner_plan_hash(),
        "output_manifest_hash": record.output_manifest_hash,
        "output_manifest_read_model": read_model,
        "metadata": {
            "raw_file_body": "DAACS_GENERATED_BUNDLE_REQUEST_RAW_SENTINEL",
            "runtime_payload": "DAACS_GENERATED_BUNDLE_REQUEST_PAYLOAD_SENTINEL",
        },
    }
    fields.update(overrides)
    return TargetRuntimeGeneratedArtifactBundleRequest(**fields)


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def test_target_runtime_generated_artifact_bundle_builds_blocked_hash_only_contract():
    result = build_disabled_target_runtime_generated_artifact_bundle(
        request=_bundle_request()
    )
    public = result.to_dict()

    assert public["projection_version"] == TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION
    assert public["mode"] == TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED
    assert public["status"] == "blocked"
    assert public["reason"] == (
        "target_runtime_generated_artifact_bundle_execution_closed"
    )
    assert public["counts"]["output_manifest_read_model_count"] == 1
    assert public["counts"]["output_manifest_hash_match_count"] == 1
    assert public["counts"]["artifact_unit_count"] == 3
    assert public["counts"]["artifact_unit_hash_count"] == 3
    assert public["counts"]["generated_artifact_body_write_count"] == 0
    assert public["execution_boundary"]["execution_permission_count"] == 0
    assert public["execution_boundary"]["target_runtime_calls"] == 0
    assert public["execution_boundary"]["filesystem_writes"] == 0
    assert public["execution_boundary"]["subprocess_calls"] == 0
    assert public["execution_boundary"]["network_calls"] == 0
    assert public["claim_boundary"]["target_runtime_outcome"] is False
    assert public["claim_boundary"]["generated_artifact_body"] is False
    assert_public_projection_safe(public)


def test_target_runtime_generated_artifact_bundle_can_build_from_repository_read_model():
    repository, record, _ = _output_manifest_read_model()

    result = build_disabled_target_runtime_generated_artifact_bundle_from_repository(
        repository=repository,
        run_id=RUN_ID,
        runner_plan_hash=_runner_plan_hash(),
        output_manifest_hash=record.output_manifest_hash,
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == (
        "target_runtime_generated_artifact_bundle_execution_closed"
    )
    assert result["counts"]["output_manifest_hash_match_count"] == 1
    assert result["counts"]["artifact_unit_count"] == 3


def test_target_runtime_generated_artifact_bundle_blocks_missing_read_model():
    result = build_disabled_target_runtime_generated_artifact_bundle(
        request=_bundle_request(output_manifest_read_model={})
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "output_manifest_read_model_missing"
    assert result["counts"]["output_manifest_read_model_count"] == 0
    assert result["counts"]["execution_permission_count"] == 0


def test_target_runtime_generated_artifact_bundle_blocks_unavailable_read_model():
    _, record, read_model = _output_manifest_read_model()
    read_model["status"] = "blocked"

    result = build_disabled_target_runtime_generated_artifact_bundle(
        request=_bundle_request(
            output_manifest_hash=record.output_manifest_hash,
            output_manifest_read_model=read_model,
        )
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "output_manifest_read_model_unavailable"
    assert result["counts"]["output_manifest_hash_match_count"] == 1


def test_target_runtime_generated_artifact_bundle_blocks_manifest_hash_mismatch():
    result = build_disabled_target_runtime_generated_artifact_bundle(
        request=_bundle_request(output_manifest_hash="a" * 64)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "output_manifest_hash_mismatch"
    assert result["counts"]["output_manifest_hash_match_count"] == 0
    assert result["counts"]["execution_permission_count"] == 0


def test_target_runtime_generated_artifact_bundle_exposes_no_raw_body_or_source():
    result = build_disabled_target_runtime_generated_artifact_bundle(
        request=_bundle_request(
            artifact_units=[
                {
                    "label": "backend",
                    "artifact_kind": "backend",
                    "expected_file_count": 0,
                    "raw_file_body": "DAACS_GENERATED_BUNDLE_UNIT_RAW_SENTINEL",
                    "source_code": "DAACS_GENERATED_BUNDLE_SOURCE_SENTINEL",
                },
                {"label": "frontend", "artifact_kind": "frontend"},
                {
                    "label": "verification_report",
                    "artifact_kind": "verification_report",
                },
            ]
        )
    ).to_dict()
    serialized = _serialized(result)

    for forbidden in (
        "DAACS_GENERATED_BUNDLE_RAW_PROMPT_SENTINEL",
        "DAACS_GENERATED_BUNDLE_RUNTIME_SENTINEL",
        "DAACS_GENERATED_BUNDLE_ADMISSION_RAW_SENTINEL",
        "DAACS_GENERATED_BUNDLE_MANIFEST_RAW_SENTINEL",
        "DAACS_GENERATED_BUNDLE_REQUEST_RAW_SENTINEL",
        "DAACS_GENERATED_BUNDLE_REQUEST_PAYLOAD_SENTINEL",
        "DAACS_GENERATED_BUNDLE_UNIT_RAW_SENTINEL",
        "DAACS_GENERATED_BUNDLE_SOURCE_SENTINEL",
        "raw_prompt",
        "runtime_payload",
        "raw_file_body",
        "source_code",
        "provider_payload",
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(result)


def test_target_runtime_generated_artifact_bundle_does_not_write_spawn_read_env_or_call_network(
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

    request = _bundle_request()
    monkeypatch.setattr(os, "getenv", blocked_getenv)
    monkeypatch.setattr(socket, "socket", blocked_socket)
    monkeypatch.setattr(urllib.request, "urlopen", blocked_urlopen)
    monkeypatch.setattr(subprocess, "run", blocked_run)
    monkeypatch.setattr(builtins, "open", blocked_write)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    result = build_disabled_target_runtime_generated_artifact_bundle(
        request=request
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["execution_boundary"]["filesystem_writes"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0
    assert result["execution_boundary"]["network_calls"] == 0

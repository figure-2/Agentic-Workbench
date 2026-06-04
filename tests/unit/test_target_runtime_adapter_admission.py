import builtins
import json
import os
import socket
import subprocess
import urllib.request

from packages.core.exposure import find_forbidden_public_keys
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_admission import (
    TARGET_RUNTIME_ADAPTER_ADMISSION_VERSION,
    TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION,
    DisabledTargetRuntimeAdapter,
    TargetRuntimeAdapterAdmissionRequest,
    TargetRuntimeAdapterAdmissionService,
    invoke_disabled_target_runtime_adapter_after_preflight_admission,
)
from packages.daacs_builder.target_runtime_sandbox import (
    TargetRuntimePreflightRequest,
    TargetRuntimePreflightService,
    ready_target_runtime_command_policy,
    ready_target_runtime_rollback_policy,
    ready_target_runtime_sandbox_policy,
    ready_target_runtime_workspace_intent,
)


RUN_ID = "run-daacs-runtime-01"


def _runner_plan_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "target runtime adapter admission",
            "runner_plan": "hash-only",
        }
    )


def _preflight() -> dict:
    request = TargetRuntimePreflightRequest(
        run_id=RUN_ID,
        runner_plan_hash=_runner_plan_hash(),
        sandbox_policy=ready_target_runtime_sandbox_policy(),
        workspace_intent=ready_target_runtime_workspace_intent(RUN_ID),
        command_policy=ready_target_runtime_command_policy(),
        rollback_policy=ready_target_runtime_rollback_policy(),
        metadata={
            "raw_prompt": "DAACS_RUNTIME_ADMISSION_RAW_PROMPT_SENTINEL",
            "runtime_payload": "DAACS_RUNTIME_ADMISSION_PAYLOAD_SENTINEL",
        },
    )
    return TargetRuntimePreflightService().preflight(request).to_dict()


def _request(**overrides) -> TargetRuntimeAdapterAdmissionRequest:
    preflight = _preflight()
    fields = {
        "run_id": RUN_ID,
        "runner_plan_hash": _runner_plan_hash(),
        "expected_preflight_hash": preflight["preflight_hash"],
        "preflight_projection": preflight,
        "metadata": {
            "raw_file_body": "DAACS_RUNTIME_ADMISSION_RAW_FILE_SENTINEL",
        },
    }
    fields.update(overrides)
    return TargetRuntimeAdapterAdmissionRequest(**fields)


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


class SpyTargetRuntimeAdapter:
    def __init__(self) -> None:
        self.invocation_count = 0

    def invoke(self, request, admission):
        self.invocation_count += 1
        return DisabledTargetRuntimeAdapter().invoke(request, admission)


def _checks(result) -> dict:
    payload = result.to_dict() if hasattr(result, "to_dict") else result
    return {check["name"]: check["passed"] for check in payload["checks"]}


def test_target_runtime_adapter_admission_reaches_disabled_adapter_after_preflight_hash():
    adapter = SpyTargetRuntimeAdapter()
    request = _request()

    result = invoke_disabled_target_runtime_adapter_after_preflight_admission(
        adapter=adapter,
        request=request,
        admission_service=TargetRuntimeAdapterAdmissionService(),
    )
    public = result.to_dict()
    checks = _checks(result)

    assert adapter.invocation_count == 1
    assert public["projection_version"] == TARGET_RUNTIME_ADAPTER_ADMISSION_VERSION
    assert public["mode"] == TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION
    assert public["status"] == "blocked"
    assert public["reason"] == "target_runtime_adapter_disabled"
    assert checks["target_runtime_preflight_admission_passed"] is True
    assert checks["preflight_hash_matches_expected"] is True
    assert checks["target_runtime_adapter_disabled"] is False
    assert public["counts"]["preflight_hash_match_count"] == 1
    assert public["counts"]["adapter_reach_count"] == 1
    assert public["counts"]["adapter_disabled_block_count"] == 1
    assert public["execution_boundary"]["target_runtime_calls"] == 0
    assert public["execution_boundary"]["filesystem_writes"] == 0
    assert public["execution_boundary"]["subprocess_calls"] == 0
    assert public["execution_boundary"]["network_calls"] == 0
    assert public["execution_boundary"]["execution_permission_count"] == 0
    assert public["claim_boundary"]["target_runtime_outcome"] is False
    assert_public_projection_safe(public)


def test_target_runtime_adapter_admission_blocks_missing_service_before_adapter():
    adapter = SpyTargetRuntimeAdapter()

    result = invoke_disabled_target_runtime_adapter_after_preflight_admission(
        adapter=adapter,
        request=_request(),
        admission_service=None,
    )
    public = result.to_dict()
    checks = _checks(result)

    assert adapter.invocation_count == 0
    assert public["status"] == "blocked"
    assert public["reason"] == "target_runtime_adapter_admission_service_missing"
    assert checks["target_runtime_adapter_admission_service_present"] is False
    assert public["counts"]["adapter_reach_count"] == 0
    assert public["execution_boundary"]["target_runtime_calls"] == 0


def test_target_runtime_adapter_admission_blocks_missing_preflight_before_adapter():
    adapter = SpyTargetRuntimeAdapter()
    request = _request(
        expected_preflight_hash="",
        preflight_projection={},
    )

    result = invoke_disabled_target_runtime_adapter_after_preflight_admission(
        adapter=adapter,
        request=request,
        admission_service=TargetRuntimeAdapterAdmissionService(),
    )
    public = result.to_dict()
    checks = _checks(result)

    assert adapter.invocation_count == 0
    assert public["status"] == "blocked"
    assert public["reason"] == "expected_preflight_hash_missing"
    assert checks["expected_preflight_hash_present"] is False
    assert checks["preflight_projection_present"] is False
    assert public["counts"]["adapter_reach_count"] == 0


def test_target_runtime_adapter_admission_blocks_preflight_hash_mismatch_before_adapter():
    adapter = SpyTargetRuntimeAdapter()
    request = _request(expected_preflight_hash="a" * 64)

    result = invoke_disabled_target_runtime_adapter_after_preflight_admission(
        adapter=adapter,
        request=request,
        admission_service=TargetRuntimeAdapterAdmissionService(),
    )
    checks = _checks(result)
    public = result.to_dict()

    assert adapter.invocation_count == 0
    assert public["status"] == "blocked"
    assert public["reason"] == "preflight_hash_mismatch"
    assert checks["preflight_hash_matches_expected"] is False
    assert public["counts"]["preflight_hash_match_count"] == 0
    assert public["counts"]["adapter_reach_count"] == 0


def test_target_runtime_adapter_admission_blocks_unclean_preflight_before_adapter():
    adapter = SpyTargetRuntimeAdapter()
    preflight = _preflight()
    preflight["counts"]["denied_path_count"] = 1
    request = _request(preflight_projection=preflight)

    result = invoke_disabled_target_runtime_adapter_after_preflight_admission(
        adapter=adapter,
        request=request,
        admission_service=TargetRuntimeAdapterAdmissionService(),
    )
    checks = _checks(result)
    public = result.to_dict()

    assert adapter.invocation_count == 0
    assert public["status"] == "blocked"
    assert public["reason"] == "preflight_boundary_not_clean"
    assert checks["preflight_boundary_clean"] is False
    assert public["counts"]["adapter_reach_count"] == 0


def test_target_runtime_adapter_admission_public_result_exposes_no_raw_values():
    result = invoke_disabled_target_runtime_adapter_after_preflight_admission(
        adapter=DisabledTargetRuntimeAdapter(),
        request=_request(),
        admission_service=TargetRuntimeAdapterAdmissionService(),
    )
    public = result.to_dict()
    serialized = _serialized(public)

    for sentinel in (
        "DAACS_RUNTIME_ADMISSION_RAW_PROMPT_SENTINEL",
        "DAACS_RUNTIME_ADMISSION_PAYLOAD_SENTINEL",
        "DAACS_RUNTIME_ADMISSION_RAW_FILE_SENTINEL",
        "raw_prompt",
        "runtime_payload",
        "raw_file_body",
    ):
        assert sentinel not in serialized
    assert find_forbidden_public_keys(public) == []
    assert_public_projection_safe(public)


def test_target_runtime_adapter_admission_does_not_write_spawn_import_or_call_network(
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

    monkeypatch.setattr(os, "getenv", blocked_getenv)
    monkeypatch.setattr(socket, "socket", blocked_socket)
    monkeypatch.setattr(urllib.request, "urlopen", blocked_urlopen)
    monkeypatch.setattr(subprocess, "run", blocked_run)
    monkeypatch.setattr(builtins, "open", blocked_write)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    result = invoke_disabled_target_runtime_adapter_after_preflight_admission(
        adapter=DisabledTargetRuntimeAdapter(),
        request=_request(),
        admission_service=TargetRuntimeAdapterAdmissionService(),
    )
    public = result.to_dict()

    assert public["counts"]["target_runtime_call_count"] == 0
    assert public["counts"]["filesystem_write_count"] == 0
    assert public["counts"]["subprocess_call_count"] == 0
    assert public["counts"]["network_call_count"] == 0
    assert public["execution_boundary"]["target_runtime_calls"] == 0

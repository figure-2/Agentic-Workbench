import builtins
import json
import os
import socket
import subprocess
import urllib.request
from pathlib import Path

from packages.core.exposure import find_forbidden_public_keys
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_sandbox import (
    TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT,
    TargetRuntimeCommandPolicy,
    TargetRuntimePreflightRequest,
    TargetRuntimePreflightService,
    TargetRuntimeRollbackPolicy,
    ready_target_runtime_command_policy,
    ready_target_runtime_rollback_policy,
    ready_target_runtime_sandbox_policy,
    ready_target_runtime_workspace_intent,
)
from apps.api.agentic_workbench_api.services.target_runtime_preflight import (
    run_target_runtime_preflight,
)


RUN_ID = "run-target-runtime"


def _runner_plan_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "target runtime preflight",
            "runner_plan": "hash only",
        }
    )


def _request(**overrides) -> TargetRuntimePreflightRequest:
    fields = {
        "run_id": RUN_ID,
        "runner_plan_hash": _runner_plan_hash(),
        "mode": TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT,
        "sandbox_policy": ready_target_runtime_sandbox_policy(),
        "workspace_intent": ready_target_runtime_workspace_intent(RUN_ID),
        "command_policy": ready_target_runtime_command_policy(),
        "rollback_policy": ready_target_runtime_rollback_policy(),
    }
    fields.update(overrides)
    return TargetRuntimePreflightRequest(**fields)


def _public(request: TargetRuntimePreflightRequest | None = None) -> dict:
    result = TargetRuntimePreflightService().preflight(request or _request())
    return result.to_dict()


def _checks(public: dict) -> dict[str, bool]:
    return {check["name"]: check["passed"] for check in public["checks"]}


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_target_runtime_preflight_ready_contract_still_blocks_execution():
    public = _public()
    checks = _checks(public)

    assert public["projection_version"] == "target-runtime-preflight-public-v1"
    assert public["status"] == "blocked"
    assert public["reason"] == "target_runtime_execution_closed"
    assert checks["live_open_policy_eligible"] is True
    assert checks["target_runtime_execution_closed"] is False
    assert public["counts"]["live_open_eligible_count"] == 1
    assert public["counts"]["denied_path_count"] == 0
    assert public["counts"]["blocked_operation_count"] == 0
    assert public["execution_boundary"]["target_runtime_calls"] == 0
    assert public["execution_boundary"]["filesystem_writes"] == 0
    assert public["execution_boundary"]["subprocess_calls"] == 0
    assert public["execution_boundary"]["network_calls"] == 0
    assert public["execution_boundary"]["execution_permission_count"] == 0
    assert public["claim_boundary"]["target_runtime_outcome"] is False
    assert find_forbidden_public_keys(public) == []
    assert_public_projection_safe(public)


def test_target_runtime_preflight_blocks_missing_policy_and_workspace():
    public = _public(
        TargetRuntimePreflightRequest(
            run_id=RUN_ID,
            runner_plan_hash=_runner_plan_hash(),
        )
    )
    checks = _checks(public)

    assert public["status"] == "blocked"
    assert checks["timeout_configured"] is False
    assert checks["planned_file_limit_configured"] is False
    assert checks["live_open_policy_eligible"] is False
    assert checks["workspace_intent_run_scoped"] is False
    assert checks["write_allowlist_present"] is False
    assert checks["rollback_plan_present"] is False
    assert public["execution_boundary"]["target_runtime_calls"] == 0


def test_target_runtime_preflight_blocks_path_traversal():
    intent = ready_target_runtime_workspace_intent(RUN_ID)
    intent = type(intent)(
        workspace_root=intent.workspace_root,
        allowed_write_paths=intent.allowed_write_paths,
        requested_write_paths=["../escape.py"],
        expected_output_paths=intent.expected_output_paths,
    )

    public = _public(_request(workspace_intent=intent))

    assert public["status"] == "blocked"
    assert public["counts"]["path_traversal_block_count"] == 1
    assert public["counts"]["denied_path_count"] >= 1
    assert public["execution_boundary"]["filesystem_writes"] == 0
    assert "../escape.py" not in _serialized(public)


def test_target_runtime_preflight_blocks_absolute_path_outside_workspace():
    intent = ready_target_runtime_workspace_intent(RUN_ID)
    intent = type(intent)(
        workspace_root="C:\\Users\\figure.2\\Desktop",
        allowed_write_paths=intent.allowed_write_paths,
        requested_write_paths=intent.requested_write_paths,
        expected_output_paths=intent.expected_output_paths,
    )

    public = _public(_request(workspace_intent=intent))

    assert public["status"] == "blocked"
    assert public["counts"]["absolute_path_block_count"] == 1
    assert public["execution_boundary"]["filesystem_writes"] == 0
    assert "C:\\Users" not in _serialized(public)


def test_target_runtime_preflight_blocks_write_outside_allowlist():
    intent = ready_target_runtime_workspace_intent(RUN_ID)
    intent = type(intent)(
        workspace_root=intent.workspace_root,
        allowed_write_paths=[f"runs/{RUN_ID}/workspace/backend"],
        requested_write_paths=[f"runs/{RUN_ID}/workspace/frontend/App.tsx"],
        expected_output_paths=intent.expected_output_paths,
    )

    public = _public(_request(workspace_intent=intent))

    assert public["status"] == "blocked"
    assert public["counts"]["disallowed_write_block_count"] == 1
    assert public["execution_boundary"]["filesystem_writes"] == 0
    assert "App.tsx" not in _serialized(public)


def test_target_runtime_preflight_blocks_install_server_and_network_operations():
    public = _public(
        _request(
            command_policy=TargetRuntimeCommandPolicy(
                requested_operations=[
                    "npm install",
                    "uvicorn app:app --reload",
                    "curl https://example.com",
                ],
                allowed_operation_labels=[],
            )
        )
    )

    assert public["status"] == "blocked"
    assert public["counts"]["package_install_block_count"] == 1
    assert public["counts"]["server_start_block_count"] == 1
    assert public["counts"]["network_command_block_count"] == 1
    assert public["execution_boundary"]["subprocess_calls"] == 0
    assert public["execution_boundary"]["network_calls"] == 0
    assert "npm install" not in _serialized(public)
    assert "https://example.com" not in _serialized(public)


def test_target_runtime_preflight_blocks_missing_rollback_and_abort_policy():
    public = _public(_request(rollback_policy=TargetRuntimeRollbackPolicy()))
    checks = _checks(public)

    assert public["status"] == "blocked"
    assert checks["rollback_plan_present"] is False
    assert checks["abort_criteria_present"] is False
    assert checks["cleanup_steps_present"] is False
    assert public["counts"]["rollback_plan_count"] == 0
    assert public["execution_boundary"]["target_runtime_calls"] == 0


def test_target_runtime_preflight_does_not_write_spawn_or_open_network(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("target runtime preflight attempted a side effect")

    monkeypatch.setattr(builtins, "open", fail_if_called)
    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "mkdir", fail_if_called)
    monkeypatch.setattr(subprocess, "run", fail_if_called)
    monkeypatch.setattr(subprocess, "Popen", fail_if_called)
    monkeypatch.setattr(os, "system", fail_if_called)
    monkeypatch.setattr(socket, "socket", fail_if_called)
    monkeypatch.setattr(urllib.request, "urlopen", fail_if_called)

    public = _public()

    assert public["execution_boundary"]["target_runtime_calls"] == 0
    assert public["execution_boundary"]["filesystem_writes"] == 0
    assert public["execution_boundary"]["subprocess_calls"] == 0
    assert public["execution_boundary"]["network_calls"] == 0


def test_target_runtime_preflight_sanitizes_metadata_and_api_truthy_strings():
    policy = {field: "true" for field in (
        "approval_policy_ready",
        "replay_persistence_ready",
        "cost_quota_guard_ready",
        "timeout_guard_ready",
        "workspace_sandbox_ready",
        "write_allowlist_ready",
        "rollback_plan_ready",
        "secret_redaction_ready",
        "artifact_sanitizer_ready",
        "audit_projection_ready",
    )}
    policy.update(
        {
            "timeout_seconds": 60,
            "max_planned_files": 20,
            "max_subprocess_calls": 0,
            "max_package_installs": 0,
            "max_server_starts": 0,
            "max_network_calls": 0,
            "max_target_runtime_calls": 0,
        }
    )
    intent = ready_target_runtime_workspace_intent(RUN_ID)
    public = run_target_runtime_preflight(
        {
            "run_id": RUN_ID,
            "runner_plan_hash": _runner_plan_hash(),
            "sandbox_policy": policy,
            "workspace_intent": {
                "workspace_root": intent.workspace_root,
                "allowed_write_paths": intent.allowed_write_paths,
                "requested_write_paths": intent.requested_write_paths,
                "expected_output_paths": intent.expected_output_paths,
            },
            "command_policy": {
                "requested_operations": ["render backend files"],
                "allowed_operation_labels": ["render_backend"],
            },
            "rollback_policy": {
                "rollback_plan_id": "rollback-local-target-runtime-preflight",
                "abort_criteria": ["abort on finding"],
                "cleanup_steps": ["discard workspace"],
            },
            "raw_log": "DAACS_RUNTIME_RAW_LOG_SENTINEL",
        }
    )
    serialized = _serialized(public)
    checks = _checks(public)

    assert public["status"] == "blocked"
    assert checks["live_open_policy_eligible"] is False
    assert "DAACS_RUNTIME_RAW_LOG_SENTINEL" not in serialized
    assert "raw_log" not in serialized
    assert find_forbidden_public_keys(public) == []

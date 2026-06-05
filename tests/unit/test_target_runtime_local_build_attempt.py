import builtins
import json
import os
import socket
import subprocess
import urllib.request

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_local_build_attempt import (
    TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE,
    TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION,
    LocalBuildCommandOutcome,
    TargetRuntimeLocalBuildAttemptRequest,
    create_target_runtime_local_build_attempt,
)
from packages.daacs_builder.target_runtime_local_build_preflight import (
    TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE,
    TargetRuntimeLocalBuildPreflightRequest,
    create_target_runtime_local_build_preflight,
)
from tests.unit.test_target_runtime_local_build_preflight import (
    RUN_ID,
    _buildable_manifest,
    _workspace_root,
)


class FakeLocalBuildRunner:
    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.calls = []

    def run(self, *, label, argv, cwd, timeout_seconds):
        self.calls.append(
            {
                "label": label,
                "argv_label_hash": stable_contract_hash(tuple(argv)),
                "cwd_exists": cwd.exists(),
                "timeout_seconds": timeout_seconds,
            }
        )
        if not self._outcomes:
            raise AssertionError("unexpected local build command")
        return self._outcomes.pop(0)


def _outcome(label: str, *, exit_code: int = 0, reason: str = "local_command_completed"):
    return LocalBuildCommandOutcome(
        label=label,
        attempted=True,
        exit_code=exit_code,
        timed_out=False,
        output_hash=stable_contract_hash(
            f"{label}:{exit_code}:AW_BUILD_04_OUTPUT_SENTINEL"
        ),
        output_byte_count=64,
        duration_ms=7,
        reason=reason,
    )


def _preflight(tmp_path, run_id: str = RUN_ID) -> dict:
    manifest = _buildable_manifest(tmp_path, run_id)
    return create_target_runtime_local_build_preflight(
        request=TargetRuntimeLocalBuildPreflightRequest(
            run_id=run_id,
            buildable_fixture_manifest_hash=manifest[
                "buildable_fixture_manifest_hash"
            ],
            buildable_fixture_manifest_projection=manifest,
            mode=TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE,
        )
    ).to_dict()


def _request(
    tmp_path,
    *,
    preflight: dict | None = None,
    operator_opt_in: bool = False,
    allow_local_command_execution: bool = False,
    **overrides,
) -> TargetRuntimeLocalBuildAttemptRequest:
    selected_preflight = preflight or _preflight(tmp_path)
    fields = {
        "run_id": RUN_ID,
        "local_build_preflight_hash": selected_preflight[
            "local_build_preflight_hash"
        ],
        "local_build_preflight_projection": selected_preflight,
        "workspace_root": _workspace_root(tmp_path),
        "mode": TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE,
        "operator_opt_in": operator_opt_in,
        "allow_local_command_execution": allow_local_command_execution,
        "install_timeout_seconds": 3,
        "build_timeout_seconds": 3,
        "metadata": {
            "raw_file_body": "AW_BUILD_04_RAW_SENTINEL",
            "provider_payload": "AW_BUILD_04_PROVIDER_SENTINEL",
        },
    }
    fields.update(overrides)
    return TargetRuntimeLocalBuildAttemptRequest(**fields)


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def test_local_build_attempt_blocks_without_explicit_opt_in(tmp_path):
    runner = FakeLocalBuildRunner([_outcome("npm install")])

    result = create_target_runtime_local_build_attempt(
        request=_request(tmp_path),
        command_runner=runner,
    ).to_dict()

    assert result["projection_version"] == TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION
    assert result["mode"] == TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE
    assert result["status"] == "blocked"
    assert result["reason"] == "local_build_attempt_opt_in_required"
    assert result["local_build_attempted"] is False
    assert result["counts"]["package_install_attempt_count"] == 0
    assert result["counts"]["build_attempt_count"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert runner.calls == []
    assert_public_projection_safe(result)


def test_local_build_attempt_records_success_with_fake_runner(tmp_path):
    runner = FakeLocalBuildRunner(
        [
            _outcome("npm install"),
            _outcome("npm run build"),
        ]
    )

    result = create_target_runtime_local_build_attempt(
        request=_request(
            tmp_path,
            operator_opt_in=True,
            allow_local_command_execution=True,
        ),
        command_runner=runner,
    ).to_dict()
    serialized = _serialized(result)

    assert result["status"] == "passed"
    assert result["reason"] == "local_fixture_app_build_passed"
    assert result["local_build_attempted"] is True
    assert result["local_build_opt_in_present"] is True
    assert result["local_command_execution_allowed"] is True
    assert result["counts"]["command_result_count"] == 2
    assert result["counts"]["command_output_hash_count"] == 2
    assert result["counts"]["package_install_attempt_count"] == 1
    assert result["counts"]["build_attempt_count"] == 1
    assert result["counts"]["server_start_attempt_count"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 2
    assert result["execution_boundary"]["network_calls"] == 1
    assert result["execution_boundary"]["package_install_calls"] == 1
    assert result["execution_boundary"]["build_calls"] == 1
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["execution_boundary"]["provider_calls"] == 0
    assert result["repository_boundary"]["root_path_returned"] is False
    assert result["repository_boundary"]["command_output_returned"] is False
    assert result["command_results"][0]["raw_output_returned"] is False
    assert result["command_results"][1]["root_path_returned"] is False
    assert len(runner.calls) == 2
    assert "AW_BUILD_04_RAW_SENTINEL" not in serialized
    assert "AW_BUILD_04_PROVIDER_SENTINEL" not in serialized
    assert "AW_BUILD_04_OUTPUT_SENTINEL" not in serialized
    assert str(tmp_path) not in serialized
    assert_public_projection_safe(result)


def test_local_build_attempt_records_install_failure_without_build(tmp_path):
    runner = FakeLocalBuildRunner(
        [_outcome("npm install", exit_code=1, reason="local_command_failed")]
    )

    result = create_target_runtime_local_build_attempt(
        request=_request(
            tmp_path,
            operator_opt_in=True,
            allow_local_command_execution=True,
        ),
        command_runner=runner,
    ).to_dict()

    assert result["status"] == "failed"
    assert result["reason"] == "local_package_install_failed"
    assert result["counts"]["command_result_count"] == 1
    assert result["counts"]["package_install_attempt_count"] == 1
    assert result["counts"]["build_attempt_count"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 1
    assert result["execution_boundary"]["build_calls"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert len(runner.calls) == 1
    assert_public_projection_safe(result)


def test_local_build_attempt_blocks_preflight_hash_mismatch(tmp_path):
    preflight = _preflight(tmp_path)
    runner = FakeLocalBuildRunner([_outcome("npm install")])

    result = create_target_runtime_local_build_attempt(
        request=_request(
            tmp_path,
            preflight=preflight,
            local_build_preflight_hash="a" * 64,
            operator_opt_in=True,
            allow_local_command_execution=True,
        ),
        command_runner=runner,
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "local_build_preflight_hash_mismatch"
    assert result["counts"]["package_install_attempt_count"] == 0
    assert runner.calls == []


def test_local_build_attempt_blocks_unconfigured_workspace(tmp_path):
    runner = FakeLocalBuildRunner([_outcome("npm install")])

    result = create_target_runtime_local_build_attempt(
        request=_request(
            tmp_path,
            workspace_root=None,
            operator_opt_in=True,
            allow_local_command_execution=True,
        ),
        command_runner=runner,
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "restricted_workspace_root_unconfigured"
    assert result["repository_boundary"]["root_path_returned"] is False
    assert runner.calls == []


def test_local_build_attempt_no_opt_in_does_not_spawn_read_env_or_call_network(
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

    result = create_target_runtime_local_build_attempt(
        request=_request(tmp_path),
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["execution_boundary"]["env_key_value_reads"] == 0
    assert result["execution_boundary"]["sdk_imports"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0

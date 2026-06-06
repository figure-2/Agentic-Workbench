import builtins
import json
import os
import socket
import subprocess
import urllib.request

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_local_preview_attempt import (
    BROWSER_RUNTIME_PREFLIGHT_VERSION,
    LOCAL_PREVIEW_REQUIRED_MARKERS,
    TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE,
    TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_VERSION,
    BrowserRuntimePreflightResult,
    LocalPreviewOutcome,
    TargetRuntimeLocalPreviewAttemptRequest,
    create_target_runtime_local_preview_attempt,
)
from tests.unit.test_target_runtime_local_build_attempt import (
    FakeLocalBuildRunner,
    _outcome,
    _request as _build_attempt_request,
)
from tests.unit.test_target_runtime_local_build_preflight import RUN_ID, _workspace_root
from packages.daacs_builder.target_runtime_local_build_attempt import (
    create_target_runtime_local_build_attempt,
)


class FakeLocalPreviewRunner:
    def __init__(self, outcome: LocalPreviewOutcome):
        self._outcome = outcome
        self.calls = []

    def run(self, *, app_dir, screenshot_path, timeout_seconds):
        self.calls.append(
            {
                "app_dir_exists": app_dir.exists(),
                "screenshot_label_hash": stable_contract_hash(screenshot_path.name),
                "timeout_seconds": timeout_seconds,
            }
        )
        return self._outcome


class FakeBrowserRuntimeProbe:
    def __init__(self, result: BrowserRuntimePreflightResult):
        self._result = result
        self.calls = 0

    def probe(self) -> BrowserRuntimePreflightResult:
        self.calls += 1
        return self._result


def _browser_runtime_result(
    *,
    available: bool = True,
    reason: str = "browser_runtime_available",
) -> BrowserRuntimePreflightResult:
    return BrowserRuntimePreflightResult(
        available=available,
        status="passed" if available else "environment_blocked",
        reason=reason,
        import_checked=True,
        launch_checked=available,
        browser_engine="chromium",
        duration_ms=3,
    )


def _preview_outcome(
    *,
    reason: str = "local_preview_browser_verified",
    server_started: bool = True,
    server_stopped: bool = True,
    screenshot_written: bool = True,
    visible_marker_count: int | None = None,
    owner_filter_click_attempted: bool = False,
    owner_filter_click_status: str = "not_attempted",
    owner_filter_before_task_count: int = 0,
    owner_filter_after_task_count: int = 0,
    reviewer_decision_click_attempted: bool = False,
    reviewer_decision_click_status: str = "not_attempted",
) -> LocalPreviewOutcome:
    return LocalPreviewOutcome(
        attempted=True,
        server_started=server_started,
        server_stopped=server_stopped,
        screenshot_written=screenshot_written,
        screenshot_hash=stable_contract_hash("AW_PREVIEW_01_SCREENSHOT_SENTINEL")
        if screenshot_written
        else "",
        screenshot_byte_count=2048 if screenshot_written else 0,
        visible_marker_count=(
            len(LOCAL_PREVIEW_REQUIRED_MARKERS)
            if visible_marker_count is None
            else visible_marker_count
        ),
        page_title_hash=stable_contract_hash("Agentic Workbench Fixture App"),
        preview_url_hash=stable_contract_hash("http://127.0.0.1:4173/"),
        duration_ms=25,
        reason=reason,
        owner_filter_click_attempted=owner_filter_click_attempted,
        owner_filter_click_status=owner_filter_click_status,
        owner_filter_click_target_label_hash=stable_contract_hash("Frontend")
        if owner_filter_click_attempted
        else "",
        owner_filter_before_task_count=owner_filter_before_task_count,
        owner_filter_after_task_count=owner_filter_after_task_count,
        owner_filter_changed_count=max(
            0,
            owner_filter_before_task_count - owner_filter_after_task_count,
        ),
        reviewer_decision_click_attempted=reviewer_decision_click_attempted,
        reviewer_decision_click_status=reviewer_decision_click_status,
        reviewer_decision_click_target_label_hash=stable_contract_hash(
            "approve-next-pass"
        )
        if reviewer_decision_click_attempted
        else "",
        reviewer_decision_before_state_hash=stable_contract_hash("Needs review")
        if reviewer_decision_click_attempted
        else "",
        reviewer_decision_after_state_hash=stable_contract_hash(
            "Approved for next pass"
        )
        if reviewer_decision_click_attempted
        else "",
        reviewer_decision_state_changed_count=(
            1 if reviewer_decision_click_status == "passed" else 0
        ),
    )


def _build_attempt(tmp_path, run_id: str = RUN_ID) -> dict:
    runner = FakeLocalBuildRunner(
        [
            _outcome("npm install"),
            _outcome("npm run build"),
        ]
    )
    return create_target_runtime_local_build_attempt(
        request=_build_attempt_request(
            tmp_path,
            operator_opt_in=True,
            allow_local_command_execution=True,
            run_id=run_id,
        ),
        command_runner=runner,
    ).to_dict()


def _request(
    tmp_path,
    *,
    build_attempt: dict | None = None,
    operator_opt_in: bool = False,
    allow_local_preview_server: bool = False,
    allow_browser_verification: bool = False,
    **overrides,
) -> TargetRuntimeLocalPreviewAttemptRequest:
    selected_build_attempt = build_attempt or _build_attempt(tmp_path)
    fields = {
        "run_id": selected_build_attempt["run_id"],
        "local_build_attempt_hash": selected_build_attempt[
            "local_build_attempt_hash"
        ],
        "local_build_attempt_projection": selected_build_attempt,
        "workspace_root": _workspace_root(tmp_path),
        "mode": TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE,
        "operator_opt_in": operator_opt_in,
        "allow_local_preview_server": allow_local_preview_server,
        "allow_browser_verification": allow_browser_verification,
        "preview_timeout_seconds": 3,
        "metadata": {
            "raw_file_body": "AW_PREVIEW_01_RAW_SENTINEL",
            "provider_payload": "AW_PREVIEW_01_PROVIDER_SENTINEL",
        },
    }
    fields.update(overrides)
    return TargetRuntimeLocalPreviewAttemptRequest(**fields)


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def test_local_preview_attempt_blocks_without_explicit_opt_in(tmp_path):
    runner = FakeLocalPreviewRunner(_preview_outcome())
    probe = FakeBrowserRuntimeProbe(_browser_runtime_result())

    result = create_target_runtime_local_preview_attempt(
        request=_request(tmp_path),
        preview_runner=runner,
        browser_runtime_probe=probe,
    ).to_dict()

    assert result["projection_version"] == TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_VERSION
    assert result["mode"] == TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE
    assert result["status"] == "blocked"
    assert result["reason"] == "local_preview_opt_in_required"
    assert result["local_preview_attempted"] is False
    assert result["local_preview_opt_in_present"] is False
    assert result["local_preview_server_allowed"] is False
    assert result["browser_verification_allowed"] is False
    assert result["counts"]["preview_server_start_attempt_count"] == 0
    assert result["counts"]["preview_server_stop_count"] == 0
    assert result["counts"]["browser_runtime_preflight_count"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert runner.calls == []
    assert probe.calls == 0
    assert_public_projection_safe(result)


def test_local_preview_attempt_records_success_with_fake_runner(tmp_path):
    runner = FakeLocalPreviewRunner(_preview_outcome())
    probe = FakeBrowserRuntimeProbe(_browser_runtime_result())

    result = create_target_runtime_local_preview_attempt(
        request=_request(
            tmp_path,
            operator_opt_in=True,
            allow_local_preview_server=True,
            allow_browser_verification=True,
        ),
        preview_runner=runner,
        browser_runtime_probe=probe,
    ).to_dict()
    serialized = _serialized(result)

    assert result["status"] == "passed"
    assert result["reason"] == "local_fixture_app_preview_verified"
    assert result["local_preview_attempted"] is True
    assert result["local_preview_opt_in_present"] is True
    assert result["local_preview_server_allowed"] is True
    assert result["browser_verification_allowed"] is True
    assert result["browser_runtime_preflight"]["projection_version"] == (
        BROWSER_RUNTIME_PREFLIGHT_VERSION
    )
    assert result["browser_runtime_preflight"]["available"] is True
    assert result["preview_record"]["server_started"] is True
    assert result["preview_record"]["server_stopped"] is True
    assert result["preview_record"]["screenshot_written"] is True
    assert result["counts"]["server_start_count"] == 1
    assert result["counts"]["preview_server_stop_count"] == 1
    assert result["counts"]["browser_runtime_preflight_count"] == 1
    assert result["counts"]["browser_runtime_available_count"] == 1
    assert result["counts"]["browser_runtime_install_guidance_label_count"] == 2
    assert result["counts"]["browser_runtime_install_guidance_hash_count"] == 2
    assert result["counts"]["server_stop_count"] == 1
    assert result["counts"]["screenshot_evidence_count"] == 1
    assert result["counts"]["screenshot_hash_count"] == 1
    assert result["counts"]["visible_marker_count"] == len(
        LOCAL_PREVIEW_REQUIRED_MARKERS
    )
    assert result["execution_boundary"]["subprocess_calls"] == 1
    assert result["execution_boundary"]["server_start_calls"] == 1
    assert result["execution_boundary"]["server_stop_calls"] == 1
    assert result["execution_boundary"]["provider_calls"] == 0
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["repository_boundary"]["root_path_returned"] is False
    assert result["repository_boundary"]["screenshot_path_returned"] is False
    assert len(runner.calls) == 1
    assert probe.calls == 1
    assert "AW_PREVIEW_01_RAW_SENTINEL" not in serialized
    assert "AW_PREVIEW_01_PROVIDER_SENTINEL" not in serialized
    assert str(tmp_path) not in serialized
    assert_public_projection_safe(result)


def test_local_preview_attempt_records_owner_filter_click_evidence(tmp_path):
    runner = FakeLocalPreviewRunner(
        _preview_outcome(
            owner_filter_click_attempted=True,
            owner_filter_click_status="passed",
            owner_filter_before_task_count=3,
            owner_filter_after_task_count=1,
        )
    )
    probe = FakeBrowserRuntimeProbe(_browser_runtime_result())

    result = create_target_runtime_local_preview_attempt(
        request=_request(
            tmp_path,
            operator_opt_in=True,
            allow_local_preview_server=True,
            allow_browser_verification=True,
        ),
        preview_runner=runner,
        browser_runtime_probe=probe,
    ).to_dict()
    preview_record = result["preview_record"]

    assert result["status"] == "passed"
    assert preview_record["owner_filter_click_attempted"] is True
    assert preview_record["owner_filter_click_status"] == "passed"
    assert preview_record["owner_filter_before_task_count"] == 3
    assert preview_record["owner_filter_after_task_count"] == 1
    assert preview_record["owner_filter_changed_count"] == 2
    assert result["counts"]["owner_filter_click_attempt_count"] == 1
    assert result["counts"]["owner_filter_click_pass_count"] == 1
    assert result["counts"]["owner_filter_click_target_label_hash_count"] == 1
    assert result["counts"]["owner_filter_before_task_count"] == 3
    assert result["counts"]["owner_filter_after_task_count"] == 1
    assert result["counts"]["owner_filter_changed_count"] == 2
    assert result["counts"]["owner_filter_dom_text_return_count"] == 0
    assert result["counts"]["owner_filter_raw_event_return_count"] == 0
    assert result["execution_boundary"]["browser_click_actions"] == 1
    assert result["claim_boundary"]["owner_filter_click_verified"] is True
    assert_public_projection_safe(result)


def test_local_preview_attempt_records_reviewer_decision_click_evidence(tmp_path):
    runner = FakeLocalPreviewRunner(
        _preview_outcome(
            reviewer_decision_click_attempted=True,
            reviewer_decision_click_status="passed",
        )
    )
    probe = FakeBrowserRuntimeProbe(_browser_runtime_result())

    result = create_target_runtime_local_preview_attempt(
        request=_request(
            tmp_path,
            operator_opt_in=True,
            allow_local_preview_server=True,
            allow_browser_verification=True,
        ),
        preview_runner=runner,
        browser_runtime_probe=probe,
    ).to_dict()
    preview_record = result["preview_record"]

    assert result["status"] == "passed"
    assert preview_record["reviewer_decision_click_attempted"] is True
    assert preview_record["reviewer_decision_click_status"] == "passed"
    assert result["counts"]["reviewer_decision_click_attempt_count"] == 1
    assert result["counts"]["reviewer_decision_click_pass_count"] == 1
    assert (
        result["counts"]["reviewer_decision_click_target_label_hash_count"] == 1
    )
    assert result["counts"]["reviewer_decision_state_hash_count"] == 2
    assert result["counts"]["reviewer_decision_state_changed_count"] == 1
    assert result["counts"]["reviewer_decision_dom_text_return_count"] == 0
    assert result["counts"]["reviewer_decision_raw_event_return_count"] == 0
    assert result["execution_boundary"]["browser_click_actions"] == 1
    assert result["claim_boundary"]["reviewer_decision_click_verified"] is True
    assert_public_projection_safe(result)


def test_local_preview_attempt_blocks_build_hash_mismatch(tmp_path):
    build_attempt = _build_attempt(tmp_path)
    runner = FakeLocalPreviewRunner(_preview_outcome())
    probe = FakeBrowserRuntimeProbe(_browser_runtime_result())

    result = create_target_runtime_local_preview_attempt(
        request=_request(
            tmp_path,
            build_attempt=build_attempt,
            local_build_attempt_hash="a" * 64,
            operator_opt_in=True,
            allow_local_preview_server=True,
            allow_browser_verification=True,
        ),
        preview_runner=runner,
        browser_runtime_probe=probe,
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "local_build_attempt_hash_mismatch"
    assert result["counts"]["server_start_count"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert runner.calls == []
    assert probe.calls == 0


def test_local_preview_attempt_preflight_blocks_missing_browser_runtime(tmp_path):
    runner = FakeLocalPreviewRunner(_preview_outcome())
    probe = FakeBrowserRuntimeProbe(
        _browser_runtime_result(
            available=False,
            reason="playwright_python_package_missing",
        )
    )

    result = create_target_runtime_local_preview_attempt(
        request=_request(
            tmp_path,
            operator_opt_in=True,
            allow_local_preview_server=True,
            allow_browser_verification=True,
        ),
        preview_runner=runner,
        browser_runtime_probe=probe,
    ).to_dict()

    assert result["status"] == "environment_blocked"
    assert result["reason"] == "playwright_python_package_missing"
    assert result["browser_runtime_preflight"]["available"] is False
    assert result["counts"]["browser_runtime_preflight_count"] == 1
    assert result["counts"]["browser_runtime_available_count"] == 0
    assert result["counts"]["preview_server_start_attempt_count"] == 0
    assert result["counts"]["preview_server_stop_count"] == 0
    assert result["counts"]["server_start_count"] == 0
    assert result["counts"]["server_stop_count"] == 0
    assert result["counts"]["screenshot_evidence_count"] == 0
    assert result["execution_boundary"]["provider_calls"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert runner.calls == []
    assert probe.calls == 1
    assert_public_projection_safe(result)


def test_local_preview_attempt_no_opt_in_does_not_spawn_read_env_or_call_network(
    tmp_path,
    monkeypatch,
):
    def fail_import(name, *args, **kwargs):
        if name.startswith(("requests", "httpx", "openai", "upstage", "playwright")):
            raise AssertionError(f"unexpected import {name}")
        return original_import(name, *args, **kwargs)

    def fail_call(*args, **kwargs):
        raise AssertionError("unexpected external call")

    original_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", fail_import)
    monkeypatch.setattr(socket, "create_connection", fail_call)
    monkeypatch.setattr(urllib.request, "urlopen", fail_call)
    monkeypatch.setattr(subprocess, "Popen", fail_call)
    monkeypatch.setattr(os, "getenv", fail_call)

    result = create_target_runtime_local_preview_attempt(
        request=_request(tmp_path),
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["execution_boundary"]["env_key_value_reads"] == 0
    assert result["execution_boundary"]["sdk_imports"] == 0
    assert result["execution_boundary"]["network_calls"] == 0
    assert result["execution_boundary"]["subprocess_calls"] == 0

from __future__ import annotations

import json

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_browser_setup_attempt import (
    BROWSER_RUNTIME_SETUP_COMMAND_LABELS,
    TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE,
    TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_VERSION,
    BrowserRuntimeSetupCommandOutcome,
    TargetRuntimeBrowserSetupAttemptRequest,
    create_target_runtime_browser_setup_attempt,
)
from packages.daacs_builder.target_runtime_local_preview_attempt import (
    BROWSER_RUNTIME_PREFLIGHT_VERSION,
    BrowserRuntimePreflightResult,
)


class FakeBrowserRuntimeSetupCommandRunner:
    def __init__(self, *, exit_code: int = 0):
        self.exit_code = exit_code
        self.calls: list[dict[str, object]] = []

    def run(self, *, label, argv, cwd, timeout_seconds):
        self.calls.append(
            {
                "label": label,
                "argv_hash": stable_contract_hash(tuple(argv)),
                "timeout_seconds": timeout_seconds,
            }
        )
        return BrowserRuntimeSetupCommandOutcome(
            label=label,
            attempted=True,
            exit_code=self.exit_code,
            timed_out=False,
            output_hash=stable_contract_hash(f"{label}:{self.exit_code}"),
            output_byte_count=32,
            duration_ms=1,
            reason="browser_runtime_setup_command_completed"
            if self.exit_code == 0
            else "browser_runtime_setup_command_failed",
        )


class FakeBrowserRuntimeProbe:
    def __init__(self, result: BrowserRuntimePreflightResult):
        self.result = result
        self.calls = 0

    def probe(self) -> BrowserRuntimePreflightResult:
        self.calls += 1
        return self.result


def _browser_runtime_result(
    *,
    available: bool,
    reason: str,
) -> BrowserRuntimePreflightResult:
    return BrowserRuntimePreflightResult(
        available=available,
        status="passed" if available else "environment_blocked",
        reason=reason,
        import_checked=True,
        launch_checked=available,
        browser_engine="chromium",
        duration_ms=1,
    )


def _preflight_projection(*, available: bool = False) -> dict:
    return _browser_runtime_result(
        available=available,
        reason="browser_runtime_available"
        if available
        else "playwright_python_package_missing",
    ).to_public_record()


def _request(
    *,
    preflight_projection: dict | None = None,
    preflight_hash: str | None = None,
    operator_opt_in: bool = False,
    allow_browser_runtime_setup: bool = False,
) -> TargetRuntimeBrowserSetupAttemptRequest:
    projection = preflight_projection or _preflight_projection()
    return TargetRuntimeBrowserSetupAttemptRequest(
        run_id="preview-03-run",
        browser_runtime_preflight_hash=(
            preflight_hash or stable_contract_hash(projection)
        ),
        browser_runtime_preflight_projection=projection,
        mode=TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE,
        operator_opt_in=operator_opt_in,
        allow_browser_runtime_setup=allow_browser_runtime_setup,
        setup_timeout_seconds=3,
    )


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def test_browser_runtime_setup_blocks_without_explicit_opt_in():
    runner = FakeBrowserRuntimeSetupCommandRunner()
    probe = FakeBrowserRuntimeProbe(
        _browser_runtime_result(
            available=True,
            reason="browser_runtime_available",
        )
    )

    result = create_target_runtime_browser_setup_attempt(
        request=_request(),
        command_runner=runner,
        browser_runtime_probe=probe,
    ).to_dict()
    serialized = _serialized(result)

    assert result["projection_version"] == TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_VERSION
    assert result["status"] == "blocked"
    assert result["reason"] == "browser_runtime_setup_opt_in_required"
    assert result["setup_attempted"] is False
    assert result["counts"]["default_setup_command_execution_count"] == 0
    assert result["counts"]["setup_command_attempt_count"] == 0
    assert result["counts"]["browser_runtime_available_after_setup_count"] == 0
    assert result["execution_boundary"]["local_process_calls"] == 0
    assert result["browser_runtime_preflight"]["projection_version"] == (
        BROWSER_RUNTIME_PREFLIGHT_VERSION
    )
    assert runner.calls == []
    assert probe.calls == 0
    assert "pip install playwright" not in serialized
    assert "playwright install chromium" not in serialized
    assert_public_projection_safe(result)


def test_browser_runtime_setup_records_success_with_fake_runner_and_probe():
    preflight = _preflight_projection(available=False)
    runner = FakeBrowserRuntimeSetupCommandRunner(exit_code=0)
    probe = FakeBrowserRuntimeProbe(
        _browser_runtime_result(
            available=True,
            reason="browser_runtime_available",
        )
    )

    result = create_target_runtime_browser_setup_attempt(
        request=_request(
            preflight_projection=preflight,
            operator_opt_in=True,
            allow_browser_runtime_setup=True,
        ),
        command_runner=runner,
        browser_runtime_probe=probe,
    ).to_dict()

    assert result["status"] == "passed"
    assert result["reason"] == "browser_runtime_setup_verified"
    assert result["setup_attempted"] is True
    assert result["counts"]["explicit_setup_opt_in_count"] == 1
    assert result["counts"]["setup_command_attempt_count"] == len(
        BROWSER_RUNTIME_SETUP_COMMAND_LABELS
    )
    assert result["counts"]["setup_command_pass_count"] == len(
        BROWSER_RUNTIME_SETUP_COMMAND_LABELS
    )
    assert result["counts"]["browser_runtime_available_before_setup_count"] == 0
    assert result["counts"]["browser_runtime_available_after_setup_count"] == 1
    assert result["counts"]["raw_output_public_return_count"] == 0
    assert result["execution_boundary"]["provider_calls"] == 0
    assert result["execution_boundary"]["solar_live_calls"] == 0
    assert result["execution_boundary"]["daacs_target_runtime_calls"] == 0
    assert len(runner.calls) == len(BROWSER_RUNTIME_SETUP_COMMAND_LABELS)
    assert probe.calls == 1
    assert_public_projection_safe(result)


def test_browser_runtime_setup_blocks_preflight_hash_mismatch():
    preflight = _preflight_projection(available=False)
    runner = FakeBrowserRuntimeSetupCommandRunner()
    probe = FakeBrowserRuntimeProbe(
        _browser_runtime_result(
            available=True,
            reason="browser_runtime_available",
        )
    )

    result = create_target_runtime_browser_setup_attempt(
        request=_request(
            preflight_projection=preflight,
            preflight_hash="a" * 64,
            operator_opt_in=True,
            allow_browser_runtime_setup=True,
        ),
        command_runner=runner,
        browser_runtime_probe=probe,
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "browser_runtime_setup_preflight_invalid"
    assert result["counts"]["setup_command_attempt_count"] == 0
    assert runner.calls == []
    assert probe.calls == 0
    assert_public_projection_safe(result)

"""API service for explicit browser runtime setup attempts."""

from __future__ import annotations

from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_browser_setup_attempt import (
    BrowserRuntimeSetupCommandRunner,
    TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE,
    TargetRuntimeBrowserSetupAttemptRequest,
    create_target_runtime_browser_setup_attempt,
)
from packages.daacs_builder.target_runtime_local_preview_attempt import (
    BrowserRuntimeProbe,
)


class TargetRuntimeBrowserSetupAttemptProvider:
    """Optional runner/probe injection for AW-PREVIEW-03 tests."""

    def __init__(
        self,
        *,
        command_runner: BrowserRuntimeSetupCommandRunner | None = None,
        browser_runtime_probe: BrowserRuntimeProbe | None = None,
    ) -> None:
        self._command_runner = command_runner
        self._browser_runtime_probe = browser_runtime_probe

    def command_runner(self) -> BrowserRuntimeSetupCommandRunner | None:
        return self._command_runner

    def browser_runtime_probe(self) -> BrowserRuntimeProbe | None:
        return self._browser_runtime_probe


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def run_target_runtime_browser_setup_attempt(
    payload: dict[str, Any],
    *,
    provider: TargetRuntimeBrowserSetupAttemptProvider | None = None,
) -> dict[str, Any]:
    """Run an explicit browser runtime setup attempt and return sanitized evidence."""
    selected = provider or TargetRuntimeBrowserSetupAttemptProvider()
    request = TargetRuntimeBrowserSetupAttemptRequest(
        run_id=str(payload["run_id"]),
        browser_runtime_preflight_hash=str(payload["browser_runtime_preflight_hash"]),
        browser_runtime_preflight_projection=_mapping(
            payload.get("browser_runtime_preflight_projection", {}),
            field_name="browser_runtime_preflight_projection",
        ),
        mode=str(payload.get("mode", TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE)),
        operator_opt_in=bool(payload.get("operator_opt_in", False)),
        allow_browser_runtime_setup=bool(
            payload.get("allow_browser_runtime_setup", False)
        ),
        setup_timeout_seconds=int(payload.get("setup_timeout_seconds", 180)),
        metadata={},
    )
    result = create_target_runtime_browser_setup_attempt(
        request=request,
        command_runner=selected.command_runner(),
        browser_runtime_probe=selected.browser_runtime_probe(),
    ).to_dict()
    assert_public_projection_safe(result)
    return result


__all__ = [
    "TargetRuntimeBrowserSetupAttemptProvider",
    "run_target_runtime_browser_setup_attempt",
]

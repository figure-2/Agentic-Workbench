"""API service for explicit local fixture app preview attempts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_local_preview_attempt import (
    BrowserRuntimeProbe,
    LocalPreviewRunner,
    TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE,
    TargetRuntimeLocalPreviewAttemptRequest,
    create_target_runtime_local_preview_attempt,
)


@dataclass(slots=True)
class TargetRuntimeLocalPreviewAttemptConfig:
    """Local workspace root for AW-PREVIEW-01 preview attempts."""

    root: Path


class TargetRuntimeLocalPreviewAttemptProvider:
    """Resolve local preview attempt config and optional preview runner."""

    def __init__(
        self,
        config: TargetRuntimeLocalPreviewAttemptConfig | None = None,
        *,
        preview_runner: LocalPreviewRunner | None = None,
        browser_runtime_probe: BrowserRuntimeProbe | None = None,
    ) -> None:
        self._config = config
        self._preview_runner = preview_runner
        self._browser_runtime_probe = browser_runtime_probe

    @property
    def configured(self) -> bool:
        return self._config is not None

    def root(self) -> Path | None:
        return self._config.root if self._config else None

    def preview_runner(self) -> LocalPreviewRunner | None:
        return self._preview_runner

    def browser_runtime_probe(self) -> BrowserRuntimeProbe | None:
        return self._browser_runtime_probe


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def run_target_runtime_local_preview_attempt(
    payload: dict[str, Any],
    *,
    workspace_provider: TargetRuntimeLocalPreviewAttemptProvider | None = None,
) -> dict[str, Any]:
    """Run an explicit local preview attempt and return sanitized evidence."""
    provider = workspace_provider or TargetRuntimeLocalPreviewAttemptProvider()
    request = TargetRuntimeLocalPreviewAttemptRequest(
        run_id=str(payload["run_id"]),
        local_build_attempt_hash=str(payload["local_build_attempt_hash"]),
        local_build_attempt_projection=_mapping(
            payload.get("local_build_attempt_projection", {}),
            field_name="local_build_attempt_projection",
        ),
        workspace_root=provider.root(),
        mode=str(payload.get("mode", TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE)),
        operator_opt_in=bool(payload.get("operator_opt_in", False)),
        allow_local_preview_server=bool(
            payload.get("allow_local_preview_server", False)
        ),
        allow_browser_verification=bool(
            payload.get("allow_browser_verification", False)
        ),
        require_browser_runtime_preflight=bool(
            payload.get("require_browser_runtime_preflight", True)
        ),
        preview_timeout_seconds=int(payload.get("preview_timeout_seconds", 45)),
        metadata={},
    )
    result = create_target_runtime_local_preview_attempt(
        request=request,
        preview_runner=provider.preview_runner(),
        browser_runtime_probe=provider.browser_runtime_probe(),
    ).to_dict()
    assert_public_projection_safe(result)
    return result


__all__ = [
    "TargetRuntimeLocalPreviewAttemptConfig",
    "TargetRuntimeLocalPreviewAttemptProvider",
    "run_target_runtime_local_preview_attempt",
]

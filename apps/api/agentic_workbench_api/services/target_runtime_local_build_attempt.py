"""API service for explicit local fixture app build attempts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_local_build_attempt import (
    LocalBuildCommandRunner,
    TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE,
    TargetRuntimeLocalBuildAttemptRequest,
    create_target_runtime_local_build_attempt,
)


@dataclass(slots=True)
class TargetRuntimeLocalBuildAttemptConfig:
    """Local workspace root for AW-BUILD-04 build attempts."""

    root: Path


class TargetRuntimeLocalBuildAttemptProvider:
    """Resolve local build attempt config and optional command runner."""

    def __init__(
        self,
        config: TargetRuntimeLocalBuildAttemptConfig | None = None,
        *,
        command_runner: LocalBuildCommandRunner | None = None,
    ) -> None:
        self._config = config
        self._command_runner = command_runner

    @property
    def configured(self) -> bool:
        return self._config is not None

    def root(self) -> Path | None:
        return self._config.root if self._config else None

    def command_runner(self) -> LocalBuildCommandRunner | None:
        return self._command_runner


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def run_target_runtime_local_build_attempt(
    payload: dict[str, Any],
    *,
    workspace_provider: TargetRuntimeLocalBuildAttemptProvider | None = None,
) -> dict[str, Any]:
    """Run an explicit local build attempt and return sanitized evidence."""
    provider = workspace_provider or TargetRuntimeLocalBuildAttemptProvider()
    request = TargetRuntimeLocalBuildAttemptRequest(
        run_id=str(payload["run_id"]),
        local_build_preflight_hash=str(payload["local_build_preflight_hash"]),
        local_build_preflight_projection=_mapping(
            payload.get("local_build_preflight_projection", {}),
            field_name="local_build_preflight_projection",
        ),
        workspace_root=provider.root(),
        mode=str(payload.get("mode", TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE)),
        operator_opt_in=bool(payload.get("operator_opt_in", False)),
        allow_local_command_execution=bool(
            payload.get("allow_local_command_execution", False)
        ),
        install_timeout_seconds=int(payload.get("install_timeout_seconds", 180)),
        build_timeout_seconds=int(payload.get("build_timeout_seconds", 180)),
        metadata={},
    )
    result = create_target_runtime_local_build_attempt(
        request=request,
        command_runner=provider.command_runner(),
    ).to_dict()
    assert_public_projection_safe(result)
    return result


__all__ = [
    "TargetRuntimeLocalBuildAttemptConfig",
    "TargetRuntimeLocalBuildAttemptProvider",
    "run_target_runtime_local_build_attempt",
]

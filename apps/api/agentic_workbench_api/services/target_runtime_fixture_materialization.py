"""API service for fixture-backed target runtime artifact materialization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_fixture_materialization import (
    TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE,
    TargetRuntimeFixtureMaterializationRequest,
    materialize_target_runtime_fixture_artifacts,
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeFixtureMaterializationConfig:
    """Server-side workspace selector for fixture artifact materialization."""

    root: str | Path | None = None


@dataclass(slots=True)
class TargetRuntimeFixtureMaterializationProvider:
    """Workspace provider that never exposes its root in public responses."""

    config: TargetRuntimeFixtureMaterializationConfig | None = None

    @property
    def configured(self) -> bool:
        return self.config is not None and self.config.root is not None

    @property
    def backend(self) -> str:
        return "local" if self.configured else "unconfigured"

    def root(self) -> Path:
        if not self.configured or self.config is None or self.config.root is None:
            raise ValueError("target runtime fixture materialization root is unconfigured")
        return Path(self.config.root)


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def run_target_runtime_fixture_materialization(
    payload: dict[str, Any],
    *,
    workspace_provider: TargetRuntimeFixtureMaterializationProvider | None = None,
) -> dict[str, Any]:
    """Materialize sanitized fixture artifacts in a configured workspace."""
    selected_provider = (
        workspace_provider or TargetRuntimeFixtureMaterializationProvider()
    )
    workspace_root = selected_provider.root() if selected_provider.configured else None
    request = TargetRuntimeFixtureMaterializationRequest(
        run_id=str(payload["run_id"]),
        runner_plan_hash=str(payload["runner_plan_hash"]),
        generated_artifact_bundle_hash=str(payload["generated_artifact_bundle_hash"]),
        generated_artifact_bundle_projection=_mapping(
            payload.get("generated_artifact_bundle_projection", {}),
            field_name="generated_artifact_bundle_projection",
        ),
        workspace_root=workspace_root,
        mode=str(payload.get("mode", TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE)),
        metadata={},
    )
    result = materialize_target_runtime_fixture_artifacts(request=request).to_dict()
    assert_public_projection_safe(result)
    return result


__all__ = [
    "TargetRuntimeFixtureMaterializationConfig",
    "TargetRuntimeFixtureMaterializationProvider",
    "run_target_runtime_fixture_materialization",
]

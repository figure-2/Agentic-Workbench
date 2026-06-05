"""API service for buildable fixture app manifest projection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_buildable_fixture_manifest import (
    TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE,
    TargetRuntimeBuildableFixtureManifestRequest,
    create_target_runtime_buildable_fixture_manifest,
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeBuildableFixtureManifestConfig:
    """Server-side root selector for build-ready fixture manifest projection."""

    root: str | Path | None = None


@dataclass(slots=True)
class TargetRuntimeBuildableFixtureManifestProvider:
    """Workspace provider that never exposes the configured local root."""

    config: TargetRuntimeBuildableFixtureManifestConfig | None = None

    @property
    def configured(self) -> bool:
        return self.config is not None and self.config.root is not None

    @property
    def backend(self) -> str:
        return "local" if self.configured else "unconfigured"

    def root(self) -> Path:
        if not self.configured or self.config is None or self.config.root is None:
            raise ValueError("target runtime buildable fixture manifest root is unconfigured")
        return Path(self.config.root)


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def run_target_runtime_buildable_fixture_manifest(
    payload: dict[str, Any],
    *,
    workspace_provider: TargetRuntimeBuildableFixtureManifestProvider | None = None,
) -> dict[str, Any]:
    """Project build-readiness for a generated fixture app workspace."""
    selected_provider = (
        workspace_provider or TargetRuntimeBuildableFixtureManifestProvider()
    )
    workspace_root = selected_provider.root() if selected_provider.configured else None
    request = TargetRuntimeBuildableFixtureManifestRequest(
        run_id=str(payload["run_id"]),
        generated_workspace_static_validation_hash=str(
            payload["generated_workspace_static_validation_hash"]
        ),
        generated_workspace_static_validation_projection=_mapping(
            payload.get("generated_workspace_static_validation_projection", {}),
            field_name="generated_workspace_static_validation_projection",
        ),
        workspace_root=workspace_root,
        mode=str(
            payload.get("mode", TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE)
        ),
        metadata={},
    )
    result = create_target_runtime_buildable_fixture_manifest(
        request=request
    ).to_dict()
    assert_public_projection_safe(result)
    return result


__all__ = [
    "TargetRuntimeBuildableFixtureManifestConfig",
    "TargetRuntimeBuildableFixtureManifestProvider",
    "run_target_runtime_buildable_fixture_manifest",
]

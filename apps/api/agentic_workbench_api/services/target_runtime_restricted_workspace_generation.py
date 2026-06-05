"""API service for restricted target runtime fixture workspace generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_restricted_workspace_generation import (
    RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS,
    TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE,
    TargetRuntimeRestrictedWorkspaceGenerationRequest,
    generate_target_runtime_restricted_workspace,
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeRestrictedWorkspaceGenerationConfig:
    """Server-side workspace selector for fixture app skeleton generation."""

    root: str | Path | None = None


@dataclass(slots=True)
class TargetRuntimeRestrictedWorkspaceGenerationProvider:
    """Workspace provider that never exposes its root in public responses."""

    config: TargetRuntimeRestrictedWorkspaceGenerationConfig | None = None

    @property
    def configured(self) -> bool:
        return self.config is not None and self.config.root is not None

    @property
    def backend(self) -> str:
        return "local" if self.configured else "unconfigured"

    def root(self) -> Path:
        if not self.configured or self.config is None or self.config.root is None:
            raise ValueError(
                "target runtime restricted workspace generation root is unconfigured"
            )
        return Path(self.config.root)


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _template_ids(value: Any) -> tuple[str, ...]:
    if value is None:
        return RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS
    if not isinstance(value, list | tuple):
        raise ValueError("template_ids must be a list")
    return tuple(str(item) for item in value)


def run_target_runtime_restricted_workspace_generation(
    payload: dict[str, Any],
    *,
    workspace_provider: TargetRuntimeRestrictedWorkspaceGenerationProvider | None = None,
) -> dict[str, Any]:
    """Generate sanitized fixture app skeleton files in a configured workspace."""
    selected_provider = (
        workspace_provider or TargetRuntimeRestrictedWorkspaceGenerationProvider()
    )
    workspace_root = selected_provider.root() if selected_provider.configured else None
    request = TargetRuntimeRestrictedWorkspaceGenerationRequest(
        run_id=str(payload["run_id"]),
        runner_plan_hash=str(payload["runner_plan_hash"]),
        implementation_brief_hash=str(payload["implementation_brief_hash"]),
        generated_artifact_bundle_hash=str(payload["generated_artifact_bundle_hash"]),
        generated_artifact_bundle_projection=_mapping(
            payload.get("generated_artifact_bundle_projection", {}),
            field_name="generated_artifact_bundle_projection",
        ),
        workspace_root=workspace_root,
        template_ids=_template_ids(payload.get("template_ids")),
        mode=str(
            payload.get("mode", TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE)
        ),
        metadata={},
    )
    result = generate_target_runtime_restricted_workspace(request=request).to_dict()
    assert_public_projection_safe(result)
    return result


__all__ = [
    "TargetRuntimeRestrictedWorkspaceGenerationConfig",
    "TargetRuntimeRestrictedWorkspaceGenerationProvider",
    "run_target_runtime_restricted_workspace_generation",
]

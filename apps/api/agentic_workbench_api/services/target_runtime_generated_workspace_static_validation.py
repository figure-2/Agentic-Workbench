"""API service for generated fixture workspace static validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_generated_workspace_static_validation import (
    TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE,
    TargetRuntimeGeneratedWorkspaceStaticValidationRequest,
    validate_target_runtime_generated_workspace_static,
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeGeneratedWorkspaceStaticValidationConfig:
    """Server-side root selector for generated workspace static validation."""

    root: str | Path | None = None


@dataclass(slots=True)
class TargetRuntimeGeneratedWorkspaceStaticValidationProvider:
    """Workspace provider that never exposes the local root."""

    config: TargetRuntimeGeneratedWorkspaceStaticValidationConfig | None = None

    @property
    def configured(self) -> bool:
        return self.config is not None and self.config.root is not None

    @property
    def backend(self) -> str:
        return "local" if self.configured else "unconfigured"

    def root(self) -> Path:
        if not self.configured or self.config is None or self.config.root is None:
            raise ValueError(
                "target runtime generated workspace static validation root is unconfigured"
            )
        return Path(self.config.root)


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def run_target_runtime_generated_workspace_static_validation(
    payload: dict[str, Any],
    *,
    workspace_provider: TargetRuntimeGeneratedWorkspaceStaticValidationProvider | None = None,
) -> dict[str, Any]:
    """Statically validate a verified generated fixture workspace."""
    selected_provider = (
        workspace_provider or TargetRuntimeGeneratedWorkspaceStaticValidationProvider()
    )
    workspace_root = selected_provider.root() if selected_provider.configured else None
    request = TargetRuntimeGeneratedWorkspaceStaticValidationRequest(
        run_id=str(payload["run_id"]),
        generated_artifact_verification_hash=str(
            payload["generated_artifact_verification_hash"]
        ),
        generated_artifact_verification_projection=_mapping(
            payload.get("generated_artifact_verification_projection", {}),
            field_name="generated_artifact_verification_projection",
        ),
        workspace_root=workspace_root,
        mode=str(
            payload.get(
                "mode",
                TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE,
            )
        ),
        metadata={},
    )
    result = validate_target_runtime_generated_workspace_static(request=request).to_dict()
    assert_public_projection_safe(result)
    return result


__all__ = [
    "TargetRuntimeGeneratedWorkspaceStaticValidationConfig",
    "TargetRuntimeGeneratedWorkspaceStaticValidationProvider",
    "run_target_runtime_generated_workspace_static_validation",
]

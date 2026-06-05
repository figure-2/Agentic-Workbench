"""API service for restricted generated fixture artifact verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_generated_artifact_verification import (
    TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE,
    TargetRuntimeGeneratedArtifactVerificationRequest,
    verify_target_runtime_generated_artifacts,
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeGeneratedArtifactVerificationConfig:
    """Server-side root selector for generated fixture artifact verification."""

    root: str | Path | None = None


@dataclass(slots=True)
class TargetRuntimeGeneratedArtifactVerificationProvider:
    """Workspace provider that never exposes its root in public responses."""

    config: TargetRuntimeGeneratedArtifactVerificationConfig | None = None

    @property
    def configured(self) -> bool:
        return self.config is not None and self.config.root is not None

    @property
    def backend(self) -> str:
        return "local" if self.configured else "unconfigured"

    def root(self) -> Path:
        if not self.configured or self.config is None or self.config.root is None:
            raise ValueError(
                "target runtime generated artifact verification root is unconfigured"
            )
        return Path(self.config.root)


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def run_target_runtime_generated_artifact_verification(
    payload: dict[str, Any],
    *,
    workspace_provider: TargetRuntimeGeneratedArtifactVerificationProvider | None = None,
) -> dict[str, Any]:
    """Verify generated fixture app skeleton files in a configured workspace."""
    selected_provider = (
        workspace_provider or TargetRuntimeGeneratedArtifactVerificationProvider()
    )
    workspace_root = selected_provider.root() if selected_provider.configured else None
    request = TargetRuntimeGeneratedArtifactVerificationRequest(
        run_id=str(payload["run_id"]),
        generated_workspace_hash=str(payload["generated_workspace_hash"]),
        generated_workspace_projection=_mapping(
            payload.get("generated_workspace_projection", {}),
            field_name="generated_workspace_projection",
        ),
        workspace_root=workspace_root,
        mode=str(
            payload.get("mode", TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE)
        ),
        metadata={},
    )
    result = verify_target_runtime_generated_artifacts(request=request).to_dict()
    assert_public_projection_safe(result)
    return result


__all__ = [
    "TargetRuntimeGeneratedArtifactVerificationConfig",
    "TargetRuntimeGeneratedArtifactVerificationProvider",
    "run_target_runtime_generated_artifact_verification",
]

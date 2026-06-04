"""API service for disabled DAACS generated artifact bundle contract."""

from __future__ import annotations

from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_generated_artifact_bundle import (
    TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED,
    TargetRuntimeGeneratedArtifactBundleRequest,
    build_disabled_target_runtime_generated_artifact_bundle,
)


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _list_of_mappings(value: Any, *, field_name: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    output: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} items must be mappings")
        output.append(item)
    return output


def run_target_runtime_generated_artifact_bundle(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Return the disabled generated artifact bundle projection."""
    request = TargetRuntimeGeneratedArtifactBundleRequest(
        run_id=str(payload["run_id"]),
        runner_plan_hash=str(payload["runner_plan_hash"]),
        output_manifest_hash=str(payload["output_manifest_hash"]),
        output_manifest_read_model=_mapping(
            payload.get("output_manifest_read_model", {}),
            field_name="output_manifest_read_model",
        ),
        artifact_units=_list_of_mappings(
            payload.get("artifact_units", []),
            field_name="artifact_units",
        ),
        mode=str(
            payload.get(
                "mode",
                TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED,
            )
        ),
        metadata={},
    )
    result = build_disabled_target_runtime_generated_artifact_bundle(
        request=request
    ).to_dict()
    assert_public_projection_safe(result)
    return result


__all__ = ["run_target_runtime_generated_artifact_bundle"]

"""API service for disabled DAACS target runtime output manifest contract."""

from __future__ import annotations

from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_output_manifest import (
    TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
    TargetRuntimeOutputManifestRequest,
    build_disabled_target_runtime_output_manifest,
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


def run_target_runtime_output_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the disabled output manifest projection."""
    request = TargetRuntimeOutputManifestRequest(
        run_id=str(payload["run_id"]),
        runner_plan_hash=str(payload["runner_plan_hash"]),
        adapter_admission_hash=str(payload["adapter_admission_hash"]),
        adapter_admission_read_model=_mapping(
            payload.get("adapter_admission_read_model", {}),
            field_name="adapter_admission_read_model",
        ),
        output_groups=_list_of_mappings(
            payload.get("output_groups", []),
            field_name="output_groups",
        ),
        mode=str(
            payload.get("mode", TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED)
        ),
        metadata={},
    )
    result = build_disabled_target_runtime_output_manifest(request=request).to_dict()
    assert_public_projection_safe(result)
    return result


__all__ = ["run_target_runtime_output_manifest"]

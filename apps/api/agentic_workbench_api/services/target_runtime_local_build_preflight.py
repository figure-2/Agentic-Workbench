"""API service for local build preflight projection."""

from __future__ import annotations

from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_local_build_preflight import (
    TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE,
    TargetRuntimeLocalBuildPreflightRequest,
    create_target_runtime_local_build_preflight,
)


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def run_target_runtime_local_build_preflight(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Project local build preflight without executing package commands."""
    request = TargetRuntimeLocalBuildPreflightRequest(
        run_id=str(payload["run_id"]),
        buildable_fixture_manifest_hash=str(
            payload["buildable_fixture_manifest_hash"]
        ),
        buildable_fixture_manifest_projection=_mapping(
            payload.get("buildable_fixture_manifest_projection", {}),
            field_name="buildable_fixture_manifest_projection",
        ),
        mode=str(payload.get("mode", TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE)),
        operator_opt_in=bool(payload.get("operator_opt_in", False)),
        metadata={},
    )
    result = create_target_runtime_local_build_preflight(request=request).to_dict()
    assert_public_projection_safe(result)
    return result


__all__ = ["run_target_runtime_local_build_preflight"]

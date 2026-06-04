"""API service for DAACS target runtime sandbox preflight projections."""

from __future__ import annotations

from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.target_runtime_sandbox import (
    TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT,
    TargetRuntimeCommandPolicy,
    TargetRuntimePreflightRequest,
    TargetRuntimeRollbackPolicy,
    TargetRuntimeSandboxPolicy,
    TargetRuntimeWorkspaceIntent,
    default_target_runtime_preflight_service,
)


def _policy_bool(policy: dict[str, Any], key: str) -> bool:
    return policy.get(key) is True


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item.strip()]


def _sandbox_policy_from_payload(payload: dict[str, Any]) -> TargetRuntimeSandboxPolicy:
    policy = payload.get("sandbox_policy", {})
    if not isinstance(policy, dict):
        raise ValueError("sandbox_policy must be a mapping")
    return TargetRuntimeSandboxPolicy(
        approval_policy_ready=_policy_bool(policy, "approval_policy_ready"),
        replay_persistence_ready=_policy_bool(policy, "replay_persistence_ready"),
        cost_quota_guard_ready=_policy_bool(policy, "cost_quota_guard_ready"),
        timeout_guard_ready=_policy_bool(policy, "timeout_guard_ready"),
        workspace_sandbox_ready=_policy_bool(policy, "workspace_sandbox_ready"),
        write_allowlist_ready=_policy_bool(policy, "write_allowlist_ready"),
        rollback_plan_ready=_policy_bool(policy, "rollback_plan_ready"),
        secret_redaction_ready=_policy_bool(policy, "secret_redaction_ready"),
        artifact_sanitizer_ready=_policy_bool(policy, "artifact_sanitizer_ready"),
        audit_projection_ready=_policy_bool(policy, "audit_projection_ready"),
        timeout_seconds=policy.get("timeout_seconds"),
        max_planned_files=policy.get("max_planned_files"),
        max_subprocess_calls=policy.get("max_subprocess_calls", 0),
        max_package_installs=policy.get("max_package_installs", 0),
        max_server_starts=policy.get("max_server_starts", 0),
        max_network_calls=policy.get("max_network_calls", 0),
        max_target_runtime_calls=policy.get("max_target_runtime_calls", 0),
    )


def _workspace_intent_from_payload(payload: dict[str, Any]) -> TargetRuntimeWorkspaceIntent:
    intent = payload.get("workspace_intent", {})
    if not isinstance(intent, dict):
        raise ValueError("workspace_intent must be a mapping")
    return TargetRuntimeWorkspaceIntent(
        workspace_root=str(intent.get("workspace_root", "")),
        allowed_write_paths=_string_list(intent.get("allowed_write_paths", [])),
        requested_write_paths=_string_list(intent.get("requested_write_paths", [])),
        expected_output_paths=_string_list(intent.get("expected_output_paths", [])),
    )


def _command_policy_from_payload(payload: dict[str, Any]) -> TargetRuntimeCommandPolicy:
    policy = payload.get("command_policy", {})
    if not isinstance(policy, dict):
        raise ValueError("command_policy must be a mapping")
    return TargetRuntimeCommandPolicy(
        requested_operations=_string_list(policy.get("requested_operations", [])),
        allowed_operation_labels=_string_list(policy.get("allowed_operation_labels", [])),
    )


def _rollback_policy_from_payload(payload: dict[str, Any]) -> TargetRuntimeRollbackPolicy:
    policy = payload.get("rollback_policy", {})
    if not isinstance(policy, dict):
        raise ValueError("rollback_policy must be a mapping")
    return TargetRuntimeRollbackPolicy(
        rollback_plan_id=str(policy.get("rollback_plan_id", "")),
        abort_criteria=_string_list(policy.get("abort_criteria", [])),
        cleanup_steps=_string_list(policy.get("cleanup_steps", [])),
    )


def run_target_runtime_preflight(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the disabled DAACS target runtime preflight projection."""
    request = TargetRuntimePreflightRequest(
        run_id=str(payload["run_id"]),
        runner_plan_hash=str(payload["runner_plan_hash"]),
        mode=str(payload.get("mode", TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT)),
        sandbox_policy=_sandbox_policy_from_payload(payload),
        workspace_intent=_workspace_intent_from_payload(payload),
        command_policy=_command_policy_from_payload(payload),
        rollback_policy=_rollback_policy_from_payload(payload),
        metadata={},
    )
    result = default_target_runtime_preflight_service().preflight(request).to_dict()
    assert_public_projection_safe(result)
    return result

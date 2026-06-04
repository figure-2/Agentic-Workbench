"""API service for planner provider preflight projections.

The service is a no-call boundary. It validates the future Solar planner path
using hashes and policy flags only; it never reads provider secrets or invokes
the provider.
"""

from __future__ import annotations

from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.div_planner.provider_boundary import (
    PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
    PlannerProviderPolicy,
    PlannerProviderPreflightRequest,
    default_planner_provider_selector,
)


def _policy_bool(policy: dict[str, Any], key: str) -> bool:
    return policy.get(key) is True


def _policy_from_payload(payload: dict[str, Any]) -> PlannerProviderPolicy:
    policy = payload.get("policy", {})
    if not isinstance(policy, dict):
        raise ValueError("policy must be a mapping")
    return PlannerProviderPolicy(
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
        request_timeout_seconds=policy.get("request_timeout_seconds"),
        max_cost_units=policy.get("max_cost_units"),
        max_output_tokens=policy.get("max_output_tokens"),
        max_live_api_calls=policy.get("max_live_api_calls"),
        retry_count=policy.get("retry_count", 0),
    )


def run_planner_provider_preflight(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the disabled Solar planner preflight projection."""
    request = PlannerProviderPreflightRequest(
        run_id=str(payload["run_id"]),
        prompt_contract_hash=str(payload["prompt_contract_hash"]),
        planner_provider_mode=str(
            payload.get("planner_provider_mode", PLANNER_PROVIDER_MODE_SOLAR_DISABLED)
        ),
        stage_target=str(payload.get("stage_target", "PlanningBlueprint")),
        env_key_name=str(payload.get("env_key_name", "UPSTAGE_API_KEY")),
        policy=_policy_from_payload(payload),
        metadata={},
    )
    result = default_planner_provider_selector().preflight(request).to_dict()
    assert_public_projection_safe(result)
    return result

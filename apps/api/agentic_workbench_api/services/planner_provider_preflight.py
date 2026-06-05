"""API service for planner provider preflight and spike projections.

The default preflight and mock spike paths are no-call boundaries. The explicit
Solar live spike path is operator-opted, bounded to one call, and returns only
sanitized hash/status/count evidence.
"""

from __future__ import annotations

from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.div_planner.provider_boundary import (
    PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
    PlannerProviderPolicy,
    PlannerProviderPreflightRequest,
    build_solar_planner_mock_response_projection,
    default_planner_provider_selector,
)
from packages.div_planner.solar_live_spike import (
    SolarPlannerLiveRunner,
    run_solar_planner_live_spike,
    solar_live_spike_request_from_payload,
)
from packages.div_planner.solar_quality_comparison import (
    compare_solar_planner_quality,
    solar_quality_comparison_request_from_payload,
)
from packages.div_planner.solar_draft_projection import (
    project_solar_planner_drafts,
    solar_draft_projection_request_from_payload,
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
        operator_approval_hash=str(payload.get("operator_approval_hash", "")),
        model_family=str(payload.get("model_family", "solar-pro3")),
        cost_limit_label=str(payload.get("cost_limit_label", "one-shot-bounded")),
        metadata={},
    )
    result = default_planner_provider_selector().preflight(request).to_dict()
    assert_public_projection_safe(result)
    return result


def run_planner_provider_spike_mock_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a sanitized mocked Solar planner response projection."""
    preflight = run_planner_provider_preflight(payload)
    result = build_solar_planner_mock_response_projection(
        preflight,
        response_summary=str(
            payload.get(
                "response_summary",
                "sanitized Solar planner spike summary",
            )
        ),
        summary_section_count=payload.get("summary_section_count", 0),
        raw_response_body=payload.get("raw_response_body"),
    )
    assert_public_projection_safe(result)
    return result


def run_planner_provider_solar_live_spike(
    payload: dict[str, Any],
    *,
    live_runner: SolarPlannerLiveRunner | None = None,
) -> dict[str, Any]:
    """Run one explicit Solar planner live spike and return sanitized evidence."""
    request = solar_live_spike_request_from_payload(payload)
    result = run_solar_planner_live_spike(
        request,
        live_runner=live_runner,
    ).to_dict()
    assert_public_projection_safe(result)
    return result


def run_planner_provider_solar_quality_comparison(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Compare fixture planner evidence with Solar public projection."""
    request = solar_quality_comparison_request_from_payload(payload)
    result = compare_solar_planner_quality(request).to_dict()
    assert_public_projection_safe(result)
    return result


def run_planner_provider_solar_draft_projection(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Project reviewer-approved Solar quality evidence into draft artifacts."""
    request = solar_draft_projection_request_from_payload(payload)
    result = project_solar_planner_drafts(request).to_dict()
    assert_public_projection_safe(result)
    return result

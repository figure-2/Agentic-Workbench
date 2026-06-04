"""Planner provider preflight boundary for future Solar Pro 3 planning.

This module prepares the planner-provider seam without opening any external
provider path. It never reads env values, imports provider SDKs, opens network
sockets, or stores raw prompt/provider bodies.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

from packages.core.exposure import sanitize_public_payload
from packages.core.live_open_policy import (
    LIVE_OPEN_REQUIRED_CONTROLS,
    SOLAR_PRO_3_ENV_KEY_NAME,
    SOLAR_PROVIDER_SURFACE,
    LiveOpenRequest,
    evaluate_live_open_request,
)
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash


PLANNER_PROVIDER_PREFLIGHT_VERSION = "planner-provider-preflight-public-v1"
PLANNER_PROVIDER_MODE_FIXTURE = "fixture"
PLANNER_PROVIDER_MODE_SOLAR_DISABLED = "solar_pro_3_disabled"
PLANNER_PROVIDER_STAGE_TARGET = "PlanningBlueprint"
SAFE_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
CONTRACT_HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True, slots=True)
class PlannerProviderPolicy:
    """Controls that must be explicit before planner provider preflight passes."""

    approval_policy_ready: bool = False
    replay_persistence_ready: bool = False
    cost_quota_guard_ready: bool = False
    timeout_guard_ready: bool = False
    workspace_sandbox_ready: bool = False
    write_allowlist_ready: bool = False
    rollback_plan_ready: bool = False
    secret_redaction_ready: bool = False
    artifact_sanitizer_ready: bool = False
    audit_projection_ready: bool = False
    request_timeout_seconds: int | None = None
    max_cost_units: int | None = None
    max_output_tokens: int | None = None
    max_live_api_calls: int | None = None
    retry_count: int = 0


@dataclass(frozen=True, slots=True)
class PlannerProviderPreflightRequest:
    """Hash-only request for a planner provider readiness check."""

    run_id: str
    prompt_contract_hash: str
    planner_provider_mode: str = PLANNER_PROVIDER_MODE_SOLAR_DISABLED
    stage_target: str = PLANNER_PROVIDER_STAGE_TARGET
    env_key_name: str = SOLAR_PRO_3_ENV_KEY_NAME
    policy: PlannerProviderPolicy = field(default_factory=PlannerProviderPolicy)
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PlannerProviderPreflightResult:
    """Public-safe planner provider readiness projection."""

    projection_version: str
    run_id: str
    planner_provider_mode: str
    stage_target: str
    status: str
    reason: str
    request_contract_hash: str
    policy_hash: str
    cost_timeout_quota_hash: str
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("planner preflight projection must be a mapping")
        assert_public_projection_safe(payload)
        return payload


def _safe_run_id(run_id: str) -> str:
    if isinstance(run_id, str) and SAFE_RUN_ID_PATTERN.fullmatch(run_id):
        return run_id
    return "run-redacted"


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def _check(
    checks: list[JsonDict],
    failures: list[str],
    *,
    name: str,
    passed: bool,
    reason: str,
) -> None:
    checks.append({"name": name, "passed": bool(passed)})
    if not passed:
        failures.append(reason)


def _zero_execution_boundary() -> JsonDict:
    return {
        "provider_calls": 0,
        "solar_provider_calls": 0,
        "live_api_calls": 0,
        "live_llm_calls": 0,
        "sdk_imports": 0,
        "env_key_value_reads": 0,
        "network_calls": 0,
        "subprocess_calls": 0,
        "filesystem_writes": 0,
        "target_runtime_calls": 0,
        "response_projection_parsed": False,
    }


def _claim_boundary(status: str) -> JsonDict:
    return {
        "scope": "planner provider preflight only",
        "status": status,
        "fixture_planner_default": True,
        "provider_generated_blueprint": False,
        "provider_success_claim": False,
        "external_provider_outcome": False,
        "target_runtime_outcome": False,
        "production_trust_claim": False,
    }


def _policy_hash(policy: PlannerProviderPolicy) -> str:
    policy_fields = asdict(policy)
    return stable_contract_hash(
        {
            "approval_policy_ready": policy_fields["approval_policy_ready"],
            "replay_persistence_ready": policy_fields["replay_persistence_ready"],
            "secret_redaction_ready": policy_fields["secret_redaction_ready"],
            "artifact_sanitizer_ready": policy_fields["artifact_sanitizer_ready"],
            "audit_projection_ready": policy_fields["audit_projection_ready"],
        }
    )


def _cost_timeout_quota_hash(policy: PlannerProviderPolicy) -> str:
    return stable_contract_hash(
        {
            "request_timeout_seconds": policy.request_timeout_seconds,
            "max_cost_units": policy.max_cost_units,
            "max_output_tokens": policy.max_output_tokens,
            "max_live_api_calls": policy.max_live_api_calls,
            "retry_count": policy.retry_count,
        }
    )


def _live_open_decision(request: PlannerProviderPreflightRequest) -> JsonDict:
    policy = request.policy
    readiness = {
        field_name: bool(getattr(policy, field_name))
        for field_name in LIVE_OPEN_REQUIRED_CONTROLS
    }
    decision = evaluate_live_open_request(
        LiveOpenRequest(
            run_id=request.run_id,
            surface=SOLAR_PROVIDER_SURFACE,
            env_key_name=request.env_key_name,
            **readiness,
        )
    ).to_dict()
    return decision


def _counts(
    *,
    status: str,
    check_count: int,
    failed_check_count: int,
    live_open_status: str,
) -> JsonDict:
    return {
        "preflight_count": 1,
        "comparison_variant_count": 1,
        "check_count": check_count,
        "failed_check_count": failed_check_count,
        "policy_hash_count": 1,
        "cost_timeout_quota_hash_count": 1,
        "request_contract_hash_count": 1,
        "planner_provider_success_count": 0,
        "provider_generated_blueprint_count": 0,
        "provider_call_count": 0,
        "sdk_import_count": 0,
        "env_value_read_count": 0,
        "network_call_count": 0,
        "status_blocked_count": 1 if status == "blocked" else 0,
        "status_preflight_only_count": 1 if status == "preflight_only" else 0,
        "live_open_eligible_count": 1
        if live_open_status == "eligible_for_separate_live_implementation"
        else 0,
    }


class PlannerProviderSelector:
    """Fail-closed selector for fixture planning and disabled Solar preflight."""

    def preflight(self, request: PlannerProviderPreflightRequest) -> PlannerProviderPreflightResult:
        checks: list[JsonDict] = []
        failures: list[str] = []
        policy = request.policy

        _check(
            checks,
            failures,
            name="planner_provider_mode_explicit",
            passed=request.planner_provider_mode
            in {PLANNER_PROVIDER_MODE_FIXTURE, PLANNER_PROVIDER_MODE_SOLAR_DISABLED},
            reason="planner_provider_mode_unknown",
        )
        _check(
            checks,
            failures,
            name="run_id_safe",
            passed=isinstance(request.run_id, str)
            and SAFE_RUN_ID_PATTERN.fullmatch(request.run_id) is not None,
            reason="run_id_invalid",
        )
        _check(
            checks,
            failures,
            name="prompt_contract_hash_valid",
            passed=isinstance(request.prompt_contract_hash, str)
            and CONTRACT_HASH_PATTERN.fullmatch(request.prompt_contract_hash) is not None,
            reason="prompt_contract_hash_invalid",
        )
        _check(
            checks,
            failures,
            name="stage_target_planning_blueprint",
            passed=request.stage_target == PLANNER_PROVIDER_STAGE_TARGET,
            reason="stage_target_invalid",
        )

        if request.planner_provider_mode == PLANNER_PROVIDER_MODE_FIXTURE:
            _check(
                checks,
                failures,
                name="fixture_planner_remains_default",
                passed=True,
                reason="fixture_planner_unavailable",
            )
            status = "fixture_default"
            reason = "fixture_planner_selected"
            live_open_status = "not_required"
        else:
            _check(
                checks,
                failures,
                name="solar_planner_preflight_explicit",
                passed=request.planner_provider_mode == PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
                reason="solar_planner_mode_not_explicit",
            )
            _check(
                checks,
                failures,
                name="env_key_name_reference_only",
                passed=request.env_key_name == SOLAR_PRO_3_ENV_KEY_NAME,
                reason="env_key_name_invalid",
            )
            _check(
                checks,
                failures,
                name="timeout_configured",
                passed=_positive_int(policy.request_timeout_seconds),
                reason="timeout_missing",
            )
            _check(
                checks,
                failures,
                name="cost_quota_configured",
                passed=_positive_int(policy.max_cost_units)
                and _positive_int(policy.max_live_api_calls),
                reason="cost_quota_missing",
            )
            _check(
                checks,
                failures,
                name="output_token_quota_configured",
                passed=_positive_int(policy.max_output_tokens),
                reason="output_token_quota_missing",
            )
            _check(
                checks,
                failures,
                name="retry_count_non_negative",
                passed=type(policy.retry_count) is int and policy.retry_count >= 0,
                reason="retry_count_invalid",
            )
            live_decision = _live_open_decision(request)
            live_open_status = str(live_decision.get("status", "unknown"))
            _check(
                checks,
                failures,
                name="live_open_policy_eligible",
                passed=live_open_status == "eligible_for_separate_live_implementation",
                reason="live_open_policy_not_eligible",
            )
            _check(
                checks,
                failures,
                name="planner_provider_call_disabled_by_design",
                passed=True,
                reason="planner_provider_call_enabled",
            )
            status = "preflight_only" if not failures else "blocked"
            reason = "provider_call_disabled_by_design" if status == "preflight_only" else failures[0]

        request_contract_hash = stable_contract_hash(
            {
                "run_id": _safe_run_id(request.run_id),
                "prompt_contract_hash": request.prompt_contract_hash,
                "planner_provider_mode": request.planner_provider_mode,
                "stage_target": request.stage_target,
                "env_key_name": request.env_key_name,
                "policy_hash": _policy_hash(policy),
                "cost_timeout_quota_hash": _cost_timeout_quota_hash(policy),
            }
        )
        failed_count = sum(1 for check in checks if not check["passed"])
        return PlannerProviderPreflightResult(
            projection_version=PLANNER_PROVIDER_PREFLIGHT_VERSION,
            run_id=_safe_run_id(request.run_id),
            planner_provider_mode=request.planner_provider_mode,
            stage_target=request.stage_target,
            status=status,
            reason=reason,
            request_contract_hash=request_contract_hash,
            policy_hash=_policy_hash(policy),
            cost_timeout_quota_hash=_cost_timeout_quota_hash(policy),
            checks=checks,
            counts=_counts(
                status=status,
                check_count=len(checks),
                failed_check_count=failed_count,
                live_open_status=live_open_status,
            ),
            execution_boundary=_zero_execution_boundary(),
            claim_boundary=_claim_boundary(status),
        )


def ready_planner_provider_policy(**overrides: Any) -> PlannerProviderPolicy:
    """Return an explicit ready policy for no-call Solar planner preflight tests."""
    fields: dict[str, Any] = {field_name: True for field_name in LIVE_OPEN_REQUIRED_CONTROLS}
    fields.update(
        {
            "request_timeout_seconds": 30,
            "max_cost_units": 1,
            "max_output_tokens": 512,
            "max_live_api_calls": 1,
            "retry_count": 0,
        }
    )
    fields.update(overrides)
    return PlannerProviderPolicy(**fields)


def default_planner_provider_selector() -> PlannerProviderSelector:
    return PlannerProviderSelector()


__all__ = [
    "PLANNER_PROVIDER_MODE_FIXTURE",
    "PLANNER_PROVIDER_MODE_SOLAR_DISABLED",
    "PLANNER_PROVIDER_PREFLIGHT_VERSION",
    "PLANNER_PROVIDER_STAGE_TARGET",
    "PlannerProviderPolicy",
    "PlannerProviderPreflightRequest",
    "PlannerProviderPreflightResult",
    "PlannerProviderSelector",
    "default_planner_provider_selector",
    "ready_planner_provider_policy",
]

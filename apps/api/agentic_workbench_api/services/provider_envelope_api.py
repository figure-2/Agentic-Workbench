"""API/read-model hook for provider envelope admission prechecks.

This service wires the no-call provider envelope admission boundary into API
and demo paths. It stores and returns only sanitized hash/count/status
projections; it never reads env values, imports provider SDKs, opens network
sockets, or calls external APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
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
from packages.daacs_builder.provider_boundary import (
    SOLAR_PRO_3_MODEL,
    SOLAR_PRO_3_PROVIDER,
    ProviderApprovalRecord,
    ProviderRequest,
    zero_provider_side_effect_metrics,
)
from packages.daacs_builder.provider_envelope_admission import (
    ProviderEnvelopeAdmissionService,
    invoke_adapter_after_provider_envelope_admission,
)
from packages.daacs_builder.provider_envelope_store import (
    PROVIDER_ENVELOPE_DB_NAME,
    SQLiteProviderEnvelopeStore,
    provider_envelope_public_read_model,
    provider_review_packet_export_public_read_model,
    provider_review_packet_export_record_from_projection,
)
from packages.daacs_builder.runner_provider import safe_public_run_id
from packages.daacs_builder.solar_contracts import (
    SolarCostTimeoutPolicy,
    attach_solar_response_projection_fixture,
    build_solar_request_contract_fixture,
)
from packages.daacs_builder.solar_live_adapter import (
    SOLAR_LIVE_ADAPTER_MODE,
    DisabledSolarPro3LiveAdapter,
    SolarPro3LiveAdapterConfig,
)


PROVIDER_ENVELOPE_API_PROJECTION_VERSION = "provider-envelope-admission-api-public-v1"
PROVIDER_ENVELOPE_PRECHECK_MODE = "live_admission_precheck"
OPERATOR_POLICY_SUMMARY_VERSION = "provider-precheck-operator-policy-summary-v1"
OPERATOR_APPROVAL_ENVELOPE_VERSION = "provider-precheck-operator-approval-envelope-v1"
LIVE_PROVIDER_DRY_ADMISSION_VERSION = "live-provider-dry-admission-checklist-v1"
MANUAL_PROVIDER_TEST_PROPOSAL_VERSION = "manual-provider-test-proposal-gate-v1"
MANUAL_PROVIDER_TEST_EXECUTOR_VERSION = "manual-provider-test-executor-boundary-v1"
ONE_SHOT_LIVE_PERMISSION_VERSION = "one-shot-live-call-permission-contract-v1"
MANUAL_PROVIDER_TEST_PREFLIGHT_AUDIT_VERSION = (
    "manual-provider-test-preflight-audit-bundle-v1"
)
MANUAL_PROVIDER_TEST_READINESS_DECISION_VERSION = (
    "manual-provider-test-readiness-decision-record-v1"
)
MANUAL_PROVIDER_TEST_REVIEW_PACKET_VERSION = (
    "manual-provider-test-review-packet-v1"
)
MANUAL_PROVIDER_TEST_REVIEW_PACKET_EXPORT_VERSION = (
    "manual-provider-test-review-packet-export-v1"
)
MANUAL_PROVIDER_TEST_HANDOFF_PACKET_VERSION = (
    "manual-provider-test-final-handoff-packet-v1"
)
MANUAL_PROVIDER_TEST_OPERATOR_OPT_IN_VERSION = (
    "manual-provider-test-operator-opt-in-checklist-v1"
)


@dataclass(slots=True)
class ProviderEnvelopeRepositoryConfig:
    """Server-side provider envelope store selector."""

    root: str | Path | None = None
    filename: str = PROVIDER_ENVELOPE_DB_NAME


@dataclass(slots=True)
class ProviderEnvelopeRepositoryProvider:
    """Cached SQLite provider envelope repository provider for API paths."""

    config: ProviderEnvelopeRepositoryConfig | None = None
    _cached_store: SQLiteProviderEnvelopeStore | None = None

    @property
    def configured(self) -> bool:
        return self.config is not None and self.config.root is not None

    @property
    def backend(self) -> str:
        return "sqlite" if self.configured else "unconfigured"

    def store(self) -> SQLiteProviderEnvelopeStore:
        if not self.configured or self.config is None or self.config.root is None:
            raise ValueError("provider envelope repository is not configured")
        if self._cached_store is None:
            self._cached_store = SQLiteProviderEnvelopeStore(
                root=self.config.root,
                filename=self.config.filename,
            )
        return self._cached_store

    def repository(self):
        return self.store().repository()


def _dataclass_payload(payload: dict[str, Any], cls: type) -> dict[str, Any]:
    allowed = {field.name for field in fields(cls)}
    return {key: value for key, value in payload.items() if key in allowed}


def _safe_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = sanitize_public_payload(payload)
    if not isinstance(sanitized, dict):
        raise ValueError("provider envelope public projection must be a mapping")
    assert_public_projection_safe(sanitized)
    return sanitized


def _check_map(checks: list[JsonDict]) -> list[JsonDict]:
    return [
        {
            "name": str(check.get("name", "")),
            "passed": bool(check.get("passed")),
        }
        for check in checks
    ]


def _zero_execution_boundary(extra: dict[str, Any] | None = None) -> JsonDict:
    return {
        **zero_provider_side_effect_metrics(),
        "provider_envelope_sdk_imports": 0,
        "provider_envelope_env_value_reads": 0,
        "provider_envelope_api_calls": 0,
        "provider_envelope_network_calls": 0,
        "solar_live_sdk_imports": 0,
        "solar_live_env_value_reads": 0,
        "solar_live_api_calls": 0,
        "adapter_invocation_count": 0,
        **(extra or {}),
    }


def _dry_admission_bool(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else False


def _live_provider_dry_admission_checklist(
    *,
    run_id: str,
    operator_policy_summary: JsonDict | None = None,
    operator_approval_envelope: JsonDict | None = None,
) -> JsonDict:
    policy_summary = operator_policy_summary or {}
    approval_envelope = operator_approval_envelope or _operator_approval_missing_projection()
    policy = policy_summary.get("policy") if isinstance(policy_summary.get("policy"), dict) else {}
    readiness = (
        policy_summary.get("readiness")
        if isinstance(policy_summary.get("readiness"), dict)
        else {}
    )
    expected_policy_hash = str(policy_summary.get("policy_summary_hash", ""))
    approved_policy_hash = str(approval_envelope.get("policy_summary_hash", ""))
    approval_status = str(approval_envelope.get("status", "missing"))
    approval_hash_match = bool(expected_policy_hash) and approved_policy_hash == expected_policy_hash
    checklist = [
        {
            "id": "operator_approval_envelope_present",
            "status": "passed" if approval_status == "approved" else "blocked",
            "passed": approval_status == "approved",
            "manual_review": False,
        },
        {
            "id": "policy_summary_hash_bound",
            "status": "passed" if approval_hash_match else "blocked",
            "passed": approval_hash_match,
            "manual_review": False,
        },
        {
            "id": "cost_limit_reviewed",
            "status": "passed" if int(policy.get("max_cost_units", 0)) > 0 else "blocked",
            "passed": int(policy.get("max_cost_units", 0)) > 0,
            "manual_review": False,
        },
        {
            "id": "timeout_limit_reviewed",
            "status": "passed"
            if int(policy.get("request_timeout_seconds", 0)) > 0
            else "blocked",
            "passed": int(policy.get("request_timeout_seconds", 0)) > 0,
            "manual_review": False,
        },
        {
            "id": "api_quota_reviewed",
            "status": "passed" if int(policy.get("max_live_api_calls", 0)) > 0 else "blocked",
            "passed": int(policy.get("max_live_api_calls", 0)) > 0,
            "manual_review": False,
        },
        {
            "id": "output_budget_reviewed",
            "status": "passed"
            if int(policy.get("max_output_unit_budget", 0)) > 0
            else "blocked",
            "passed": int(policy.get("max_output_unit_budget", 0)) > 0,
            "manual_review": False,
        },
        {
            "id": "rollback_plan_documented",
            "status": "manual_required",
            "passed": False,
            "manual_review": True,
        },
        {
            "id": "manual_operator_final_review",
            "status": "manual_required",
            "passed": False,
            "manual_review": True,
        },
        {
            "id": "execution_permission_closed",
            "status": "closed",
            "passed": not _dry_admission_bool(readiness.get("allowed_to_execute")),
            "manual_review": False,
        },
    ]
    passed_count = sum(1 for item in checklist if item["passed"] is True)
    blocked_count = sum(1 for item in checklist if item["status"] == "blocked")
    manual_required_count = sum(1 for item in checklist if item["manual_review"] is True)
    projection = {
        "projection_version": LIVE_PROVIDER_DRY_ADMISSION_VERSION,
        "status": "dry_admission_only",
        "run_id": safe_public_run_id(run_id),
        "provider_name": str(policy_summary.get("provider_name", SOLAR_PRO_3_PROVIDER)),
        "model_name": str(policy_summary.get("model_name", SOLAR_PRO_3_MODEL)),
        "runtime_mode": PROVIDER_ENVELOPE_PRECHECK_MODE,
        "live_ready": False,
        "allowed_to_execute": False,
        "checklist_item_count": len(checklist),
        "passed_check_count": passed_count,
        "blocked_check_count": blocked_count,
        "manual_required_count": manual_required_count,
        "checklist": checklist,
        "operator_approval": {
            "status": approval_status,
            "policy_summary_hash_present": bool(expected_policy_hash),
            "policy_summary_hash_match": approval_hash_match,
            "envelope_hash_present": bool(approval_envelope.get("envelope_hash")),
        },
        "policy_summary": {
            "cost_limit_configured": int(policy.get("max_cost_units", 0)) > 0,
            "timeout_configured": int(policy.get("request_timeout_seconds", 0)) > 0,
            "api_quota_configured": int(policy.get("max_live_api_calls", 0)) > 0,
            "output_budget_configured": int(policy.get("max_output_unit_budget", 0)) > 0,
            "required_control_count": int(readiness.get("required_control_count", 0)),
            "missing_control_count": int(readiness.get("missing_control_count", 0)),
            "eligible_for_later_live_open": _dry_admission_bool(
                readiness.get("eligible_for_live_open")
            ),
            "execution_permission_closed": not _dry_admission_bool(
                readiness.get("allowed_to_execute")
            ),
        },
        "execution_boundary": {
            "sdk_imports": 0,
            "env_value_reads": 0,
            "api_calls": 0,
            "network_calls": 0,
            "solar_provider_calls": 0,
            "target_runtime_calls": 0,
        },
        "claim_boundary": {
            "scope": "local provider dry-admission checklist only",
            "external_provider_outcome": False,
            "target_runtime_outcome": False,
            "production_trust_claim": False,
        },
    }
    projection["dry_admission_hash"] = stable_contract_hash(projection)
    return _safe_public_payload(projection)


def _manual_provider_test_proposal_not_applicable(run_id: str) -> JsonDict:
    return _safe_public_payload(
        {
            "projection_version": MANUAL_PROVIDER_TEST_PROPOSAL_VERSION,
            "status": "not_applicable",
            "run_id": safe_public_run_id(run_id),
            "proposal_present": False,
            "operator_approval_present": False,
            "proposal_hash": "",
            "live_ready": False,
            "allowed_to_execute": False,
            "disabled_by_default": True,
            "checks": [],
            "execution_boundary": {
                "sdk_imports": 0,
                "env_value_reads": 0,
                "api_calls": 0,
                "network_calls": 0,
                "solar_provider_calls": 0,
                "target_runtime_calls": 0,
            },
            "claim_boundary": {
                "scope": "local manual provider test proposal gate only",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
                "production_trust_claim": False,
            },
        }
    )


def _manual_provider_test_executor_projection(
    *,
    request: ProviderRequest,
    manual_provider_test_proposal: JsonDict,
    executor_enable_requested: bool,
) -> JsonDict:
    proposal_status = str(manual_provider_test_proposal.get("status", "blocked"))
    proposal_hash = str(manual_provider_test_proposal.get("proposal_hash", ""))
    planned_call_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_EXECUTOR_VERSION,
                "run_id": request.run_id,
                "prompt_contract_hash": request.prompt_contract_hash,
                "provider_name": request.provider_name,
                "model_name": request.model_name,
                "proposal_hash": proposal_hash,
                "executor_enable_requested": bool(executor_enable_requested),
            }
        )
        if proposal_hash
        else ""
    )
    if proposal_status != "approved_disabled":
        reason = "manual_provider_test_proposal_required"
    elif not executor_enable_requested:
        reason = "executor_enable_required"
    else:
        reason = "executor_disabled_by_default"
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "planned_call_hash": planned_call_hash,
        }
    )


def _one_shot_live_permission_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "permission_contract_hash": "",
            "expires_at": "",
            "permission_field_count": 0,
        }
    )


def _manual_provider_test_preflight_audit_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "preflight_audit_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 0,
            "no_call_counter_count": 0,
            "no_call_counter_mismatch_count": 0,
        }
    )


def _manual_provider_test_readiness_decision_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "readiness_decision_hash": "",
            "decision_count": 0,
            "approve_decision_count": 0,
            "reject_decision_count": 0,
            "defer_decision_count": 0,
            "mismatch_count": 1,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_review_packet_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "review_packet_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_review_packet_export_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "review_packet_hash": "",
            "review_packet_export_hash": "",
            "export_count": 0,
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_handoff_packet_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "handoff_packet_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "export_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_operator_opt_in_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "operator_opt_in_hash": "",
            "handoff_packet_hash": "",
            "checklist_item_count": 0,
            "passed_check_count": 0,
            "mismatch_count": 1,
            "execution_permission_count": 0,
        }
    )


def _manual_test_proposal_policy(policy: SolarCostTimeoutPolicy) -> JsonDict:
    return {
        "request_timeout_seconds": int(policy.request_timeout_seconds or 0),
        "max_cost_units": int(policy.max_cost_units or 0),
        "max_live_api_calls": int(policy.max_live_api_calls or 0),
        "max_output_unit_budget": int(policy.max_output_tokens or 0),
        "retry_count": int(policy.retry_count),
    }


def _coerce_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _one_shot_live_permission_projection(
    *,
    payload: dict[str, Any],
    request: ProviderRequest,
    policy: SolarCostTimeoutPolicy,
    manual_provider_test_proposal: JsonDict,
    manual_provider_test_executor: JsonDict,
) -> JsonDict:
    permission_payload = (
        payload.get("one_shot_live_permission")
        if isinstance(payload.get("one_shot_live_permission"), dict)
        else {}
    )
    if not permission_payload:
        return _one_shot_live_permission_blocked("one_shot_permission_required")

    proposal_fields = (
        manual_provider_test_proposal.get("proposal_fields")
        if isinstance(manual_provider_test_proposal.get("proposal_fields"), dict)
        else {}
    )
    policy_limits = _manual_test_proposal_policy(policy)
    proposal_hash = str(manual_provider_test_proposal.get("proposal_hash", "")).strip()
    planned_call_hash = str(manual_provider_test_executor.get("planned_call_hash", "")).strip()
    rollback_plan_id = str(proposal_fields.get("rollback_plan_id", "")).strip()
    abort_criteria_hash = str(proposal_fields.get("abort_criteria_hash", "")).strip()
    abort_criteria_count = _coerce_int(proposal_fields.get("abort_criteria_count", 0))
    expires_at = str(permission_payload.get("expires_at", "")).strip()

    canonical_permission = {
        "projection_version": ONE_SHOT_LIVE_PERMISSION_VERSION,
        "run_id": request.run_id,
        "proposal_hash": proposal_hash,
        "planned_call_hash": planned_call_hash,
        "request_timeout_seconds": policy_limits["request_timeout_seconds"],
        "max_cost_units": policy_limits["max_cost_units"],
        "max_live_api_calls": policy_limits["max_live_api_calls"],
        "max_output_unit_budget": policy_limits["max_output_unit_budget"],
        "rollback_plan_id": rollback_plan_id,
        "abort_criteria_hash": abort_criteria_hash,
        "abort_criteria_count": abort_criteria_count,
        "expires_at": expires_at,
    }
    required_checks = [
        str(permission_payload.get("run_id", "")).strip() == request.run_id,
        str(permission_payload.get("proposal_hash", "")).strip() == proposal_hash,
        str(permission_payload.get("planned_call_hash", "")).strip() == planned_call_hash,
        _coerce_int(permission_payload.get("request_timeout_seconds", 0))
        == policy_limits["request_timeout_seconds"],
        _coerce_int(permission_payload.get("max_cost_units", 0))
        == policy_limits["max_cost_units"],
        _coerce_int(permission_payload.get("max_live_api_calls", 0))
        == policy_limits["max_live_api_calls"],
        _coerce_int(permission_payload.get("max_output_unit_budget", 0))
        == policy_limits["max_output_unit_budget"],
        str(permission_payload.get("rollback_plan_id", "")).strip() == rollback_plan_id,
        str(permission_payload.get("abort_criteria_hash", "")).strip()
        == abort_criteria_hash,
        _coerce_int(permission_payload.get("abort_criteria_count", 0))
        == abort_criteria_count,
        bool(expires_at),
    ]
    structural_checks = [
        bool(proposal_hash),
        bool(planned_call_hash),
        bool(rollback_plan_id),
        bool(abort_criteria_hash),
        abort_criteria_count > 0,
    ]
    contract_matches = all(required_checks) and all(structural_checks)
    executor_status = str(manual_provider_test_executor.get("status", "blocked"))
    if not contract_matches:
        reason = "one_shot_permission_contract_mismatch"
        permission_contract_hash = ""
    else:
        reason = (
            "executor_blocked"
            if executor_status == "blocked"
            else "execution_disabled_by_default"
        )
        permission_contract_hash = stable_contract_hash(canonical_permission)

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "permission_contract_hash": permission_contract_hash,
            "expires_at": expires_at if contract_matches else "",
            "permission_field_count": len(required_checks) if contract_matches else 0,
        }
    )


_PREFLIGHT_NO_CALL_COUNTERS = (
    "live_llm_calls",
    "live_api_calls",
    "provider_calls",
    "provider_imports",
    "provider_secret_value_reads",
    "network_calls",
    "provider_envelope_sdk_imports",
    "provider_envelope_env_value_reads",
    "provider_envelope_api_calls",
    "provider_envelope_network_calls",
    "solar_live_sdk_imports",
    "solar_live_env_value_reads",
    "solar_live_api_calls",
)


def _manual_provider_test_preflight_audit_projection(
    *,
    live_provider_dry_admission: JsonDict,
    manual_provider_test_proposal: JsonDict,
    manual_provider_test_executor: JsonDict,
    one_shot_live_permission: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    proposal_hash = str(manual_provider_test_proposal.get("proposal_hash", "")).strip()
    planned_call_hash = str(manual_provider_test_executor.get("planned_call_hash", "")).strip()
    permission_hash = str(one_shot_live_permission.get("permission_contract_hash", "")).strip()
    dry_admission_hash = str(live_provider_dry_admission.get("dry_admission_hash", "")).strip()
    no_call_counter_values = {
        counter_name: _coerce_int(execution_boundary.get(counter_name, 0))
        for counter_name in _PREFLIGHT_NO_CALL_COUNTERS
    }
    no_call_counter_mismatch_count = sum(
        1 for value in no_call_counter_values.values() if value != 0
    )
    component_checks = [
        str(manual_provider_test_proposal.get("status", "")) == "approved_disabled"
        and bool(proposal_hash),
        str(manual_provider_test_executor.get("status", "")) == "blocked"
        and str(manual_provider_test_executor.get("reason", "")) == "executor_disabled_by_default"
        and bool(planned_call_hash),
        str(one_shot_live_permission.get("status", "")) == "blocked"
        and str(one_shot_live_permission.get("reason", "")) == "executor_blocked"
        and bool(permission_hash),
        str(live_provider_dry_admission.get("status", "")) == "dry_admission_only"
        and live_provider_dry_admission.get("live_ready") is False
        and live_provider_dry_admission.get("allowed_to_execute") is False
        and _coerce_int(live_provider_dry_admission.get("checklist_item_count", 0)) > 0,
        no_call_counter_mismatch_count == 0,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    if not component_checks[0]:
        reason = "proposal_component_missing_or_blocked"
    elif not component_checks[1]:
        reason = "executor_component_missing_or_mismatch"
    elif not component_checks[2]:
        reason = "permission_component_missing_or_mismatch"
    elif not component_checks[3]:
        reason = "operator_checklist_missing_or_mismatch"
    elif not component_checks[4]:
        reason = "no_call_counter_mismatch"
    else:
        reason = "preflight_execution_closed"

    preflight_audit_hash = ""
    if mismatch_count == 0:
        preflight_audit_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_PREFLIGHT_AUDIT_VERSION,
                "proposal_hash": proposal_hash,
                "planned_call_hash": planned_call_hash,
                "permission_contract_hash": permission_hash,
                "dry_admission_hash": dry_admission_hash,
                "checklist_item_count": _coerce_int(
                    live_provider_dry_admission.get("checklist_item_count", 0)
                ),
                "manual_required_count": _coerce_int(
                    live_provider_dry_admission.get("manual_required_count", 0)
                ),
                "no_call_counter_hash": stable_contract_hash(no_call_counter_values),
                "no_call_counter_count": len(_PREFLIGHT_NO_CALL_COUNTERS),
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "preflight_audit_hash": preflight_audit_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "no_call_counter_count": len(_PREFLIGHT_NO_CALL_COUNTERS),
            "no_call_counter_mismatch_count": no_call_counter_mismatch_count,
        }
    )


def _manual_provider_test_readiness_decision_projection(
    *,
    payload: dict[str, Any],
    preflight_audit: JsonDict,
) -> JsonDict:
    decision_payload = (
        payload.get("manual_test_readiness_decision")
        if isinstance(payload.get("manual_test_readiness_decision"), dict)
        else {}
    )
    if not decision_payload:
        return _manual_provider_test_readiness_decision_blocked(
            "readiness_decision_required"
        )

    expected_preflight_hash = str(preflight_audit.get("preflight_audit_hash", "")).strip()
    supplied_preflight_hash = str(decision_payload.get("preflight_audit_hash", "")).strip()
    decision = str(decision_payload.get("decision", "")).strip().lower()
    operator_ref = str(decision_payload.get("operator_ref", "")).strip()
    decided_at = str(decision_payload.get("decided_at", "")).strip()
    reason_code = str(decision_payload.get("decision_reason_code", "")).strip()
    decision_allowed = decision in {"approve", "reject", "defer"}
    checks = [
        bool(expected_preflight_hash),
        bool(supplied_preflight_hash) and supplied_preflight_hash == expected_preflight_hash,
        decision_allowed,
        bool(operator_ref),
        bool(decided_at),
    ]
    mismatch_count = sum(1 for check in checks if not check)
    if not expected_preflight_hash:
        reason = "preflight_audit_missing_or_mismatched"
    elif supplied_preflight_hash != expected_preflight_hash:
        reason = "preflight_hash_mismatch"
    elif not decision_allowed:
        reason = "readiness_decision_invalid"
    elif not operator_ref or not decided_at:
        reason = "readiness_decision_incomplete"
    elif decision == "approve":
        reason = "readiness_execution_closed"
    elif decision == "reject":
        reason = "readiness_rejected"
    else:
        reason = "readiness_deferred"

    readiness_decision_hash = ""
    if mismatch_count == 0:
        readiness_decision_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_READINESS_DECISION_VERSION,
                "preflight_audit_hash": expected_preflight_hash,
                "decision": decision,
                "operator_ref": operator_ref,
                "decided_at": decided_at,
                "decision_reason_code": reason_code,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "readiness_decision_hash": readiness_decision_hash,
            "decision_count": 1 if decision_allowed else 0,
            "approve_decision_count": 1 if decision == "approve" and decision_allowed else 0,
            "reject_decision_count": 1 if decision == "reject" and decision_allowed else 0,
            "defer_decision_count": 1 if decision == "defer" and decision_allowed else 0,
            "mismatch_count": mismatch_count,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_review_packet_projection(
    *,
    operator_policy_summary: JsonDict,
    preflight_audit: JsonDict,
    readiness_decision: JsonDict,
) -> JsonDict:
    policy_hash = str(operator_policy_summary.get("policy_summary_hash", "")).strip()
    preflight_hash = str(preflight_audit.get("preflight_audit_hash", "")).strip()
    decision_hash = str(readiness_decision.get("readiness_decision_hash", "")).strip()
    execution_permission_count = _coerce_int(
        readiness_decision.get("execution_permission_count", 0)
    )
    component_checks = [
        bool(policy_hash),
        str(preflight_audit.get("status", "")) == "blocked"
        and str(preflight_audit.get("reason", "")) == "preflight_execution_closed"
        and bool(preflight_hash),
        str(readiness_decision.get("status", "")) == "blocked"
        and bool(decision_hash)
        and execution_permission_count == 0,
    ]
    component_hash_count = sum(
        1 for value in (policy_hash, preflight_hash, decision_hash) if value
    )
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    if not component_checks[0]:
        reason = "policy_summary_missing_or_mismatched"
    elif not component_checks[1]:
        reason = "preflight_component_missing_or_mismatched"
    elif not component_checks[2]:
        reason = "readiness_decision_missing_or_mismatched"
    else:
        reason = "review_packet_execution_closed"

    review_packet_hash = ""
    if mismatch_count == 0:
        review_packet_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_REVIEW_PACKET_VERSION,
                "policy_summary_hash": policy_hash,
                "preflight_audit_hash": preflight_hash,
                "readiness_decision_hash": decision_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "review_packet_hash": review_packet_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_handoff_packet_projection(
    *,
    operator_policy_summary: JsonDict,
    preflight_audit: JsonDict,
    readiness_decision: JsonDict,
    review_packet: JsonDict,
    review_packet_export: JsonDict,
) -> JsonDict:
    policy_hash = str(operator_policy_summary.get("policy_summary_hash", "")).strip()
    preflight_hash = str(preflight_audit.get("preflight_audit_hash", "")).strip()
    decision_hash = str(readiness_decision.get("readiness_decision_hash", "")).strip()
    review_hash = str(review_packet.get("review_packet_hash", "")).strip()
    export_hash = str(review_packet_export.get("review_packet_export_hash", "")).strip()
    export_review_hash = str(review_packet_export.get("review_packet_hash", "")).strip()
    execution_permission_count = (
        _coerce_int(readiness_decision.get("execution_permission_count", 0))
        + _coerce_int(review_packet.get("execution_permission_count", 0))
        + _coerce_int(review_packet_export.get("execution_permission_count", 0))
    )
    export_count = _coerce_int(review_packet_export.get("export_count", 0))
    component_checks = [
        bool(policy_hash),
        str(preflight_audit.get("status", "")) == "blocked"
        and str(preflight_audit.get("reason", "")) == "preflight_execution_closed"
        and bool(preflight_hash),
        str(readiness_decision.get("status", "")) == "blocked"
        and bool(decision_hash)
        and _coerce_int(readiness_decision.get("execution_permission_count", 0)) == 0,
        str(review_packet.get("status", "")) == "blocked"
        and str(review_packet.get("reason", "")) == "review_packet_execution_closed"
        and bool(review_hash)
        and _coerce_int(review_packet.get("execution_permission_count", 0)) == 0,
        str(review_packet_export.get("status", "")) == "blocked"
        and str(review_packet_export.get("reason", "")) == "review_packet_execution_closed"
        and bool(export_hash)
        and bool(review_hash)
        and export_review_hash == review_hash
        and _coerce_int(review_packet_export.get("execution_permission_count", 0)) == 0,
    ]
    component_hash_count = sum(
        1
        for value in (
            policy_hash,
            preflight_hash,
            decision_hash,
            review_hash,
            export_hash,
        )
        if value
    )
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    if not component_checks[0]:
        reason = "policy_summary_missing_or_mismatched"
    elif not component_checks[1]:
        reason = "preflight_component_missing_or_mismatched"
    elif not component_checks[2]:
        reason = "readiness_decision_missing_or_mismatched"
    elif not component_checks[3]:
        reason = "review_packet_missing_or_mismatched"
    elif not component_checks[4] and export_hash and review_hash:
        reason = "review_packet_export_hash_mismatch"
    elif not component_checks[4]:
        reason = "review_packet_export_missing_or_mismatched"
    else:
        reason = "handoff_packet_execution_closed"

    handoff_packet_hash = ""
    if mismatch_count == 0 and execution_permission_count == 0:
        handoff_packet_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_HANDOFF_PACKET_VERSION,
                "policy_summary_hash": policy_hash,
                "preflight_audit_hash": preflight_hash,
                "readiness_decision_hash": decision_hash,
                "review_packet_hash": review_hash,
                "review_packet_export_hash": export_hash,
                "component_count": component_count,
                "export_count": export_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "handoff_packet_hash": handoff_packet_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "export_count": export_count,
            "execution_permission_count": execution_permission_count,
        }
    )


def _manual_provider_test_operator_opt_in_projection(
    *,
    payload: dict[str, Any],
    handoff_packet: JsonDict,
) -> JsonDict:
    handoff_hash = str(handoff_packet.get("handoff_packet_hash", "")).strip()
    opt_in_payload = (
        payload.get("manual_test_operator_opt_in")
        if isinstance(payload.get("manual_test_operator_opt_in"), dict)
        else {}
    )
    expected_handoff_hash = str(
        opt_in_payload.get("handoff_packet_hash")
        or opt_in_payload.get("approved_handoff_packet_hash")
        or ""
    ).strip()
    decision = str(opt_in_payload.get("decision", "")).strip().lower()
    operator_ref = str(opt_in_payload.get("operator_ref", "")).strip()
    opted_in_at = str(opt_in_payload.get("opted_in_at", "")).strip()

    component_checks = [
        bool(handoff_hash),
        bool(opt_in_payload),
        bool(expected_handoff_hash) and expected_handoff_hash == handoff_hash,
        decision == "opt_in",
        bool(operator_ref) and bool(opted_in_at),
    ]
    checklist_item_count = len(component_checks)
    passed_check_count = sum(1 for check in component_checks if check)
    mismatch_count = checklist_item_count - passed_check_count

    if not component_checks[0]:
        reason = "handoff_packet_missing_or_mismatched"
    elif not component_checks[1]:
        reason = "operator_opt_in_required"
    elif not component_checks[2]:
        reason = "handoff_packet_hash_mismatch"
    elif not component_checks[3]:
        reason = "operator_opt_in_decision_invalid"
    elif not component_checks[4]:
        reason = "operator_opt_in_incomplete"
    else:
        reason = "operator_opt_in_execution_closed"

    operator_opt_in_hash = ""
    if mismatch_count == 0:
        operator_opt_in_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_OPERATOR_OPT_IN_VERSION,
                "handoff_packet_hash": handoff_hash,
                "decision": decision,
                "operator_ref": operator_ref,
                "opted_in_at": opted_in_at,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "operator_opt_in_hash": operator_opt_in_hash,
            "handoff_packet_hash": handoff_hash,
            "checklist_item_count": checklist_item_count,
            "passed_check_count": passed_check_count,
            "mismatch_count": mismatch_count,
            "execution_permission_count": 0,
        }
    )


def _manual_test_proposal_projection(
    *,
    payload: dict[str, Any],
    request: ProviderRequest,
    policy: SolarCostTimeoutPolicy,
) -> JsonDict:
    proposal_payload = (
        payload.get("manual_test_proposal")
        if isinstance(payload.get("manual_test_proposal"), dict)
        else {}
    )
    approval_payload = (
        payload.get("manual_test_operator_approval")
        if isinstance(payload.get("manual_test_operator_approval"), dict)
        else {}
    )
    policy_limits = _manual_test_proposal_policy(policy)
    abort_criteria = (
        proposal_payload.get("abort_criteria")
        if isinstance(proposal_payload.get("abort_criteria"), list)
        else []
    )
    safe_abort_criteria = [str(item) for item in abort_criteria if str(item).strip()]
    rollback_plan_id = str(proposal_payload.get("rollback_plan_id", "")).strip()
    proposal_id = str(proposal_payload.get("proposal_id", "")).strip()
    proposal_run_id = str(proposal_payload.get("run_id", "")).strip()
    proposal_prompt_hash = str(proposal_payload.get("prompt_contract_hash", "")).strip()
    proposal_policy = {
        "request_timeout_seconds": int(proposal_payload.get("request_timeout_seconds", 0) or 0),
        "max_cost_units": int(proposal_payload.get("max_cost_units", 0) or 0),
        "max_live_api_calls": int(proposal_payload.get("max_live_api_calls", 0) or 0),
        "max_output_unit_budget": int(
            proposal_payload.get(
                "max_output_unit_budget",
                proposal_payload.get("max_output_tokens", 0),
            )
            or 0
        ),
    }
    canonical_proposal = {
        "proposal_id": proposal_id,
        "run_id": proposal_run_id,
        "prompt_contract_hash": proposal_prompt_hash,
        "provider_name": str(proposal_payload.get("provider_name", request.provider_name)),
        "model_name": str(proposal_payload.get("model_name", request.model_name)),
        "policy": proposal_policy,
        "rollback_plan_id": rollback_plan_id,
        "abort_criteria_hash": stable_contract_hash({"abort_criteria": safe_abort_criteria})
        if safe_abort_criteria
        else "",
        "abort_criteria_count": len(safe_abort_criteria),
    }
    proposal_hash = stable_contract_hash(canonical_proposal) if proposal_payload else ""
    approved_hash = str(approval_payload.get("approved_proposal_hash", "")).strip()
    operator_decision = str(approval_payload.get("decision", "")).strip().lower()
    operator_ref = str(approval_payload.get("operator_ref", "")).strip()
    approved_at = str(approval_payload.get("approved_at", "")).strip()
    checks = [
        {"name": "manual_test_proposal_present", "passed": bool(proposal_payload)},
        {
            "name": "manual_test_proposal_run_id_match",
            "passed": bool(proposal_payload) and proposal_run_id == request.run_id,
        },
        {
            "name": "manual_test_proposal_prompt_contract_hash_match",
            "passed": bool(proposal_payload)
            and proposal_prompt_hash == request.prompt_contract_hash,
        },
        {
            "name": "manual_test_proposal_cost_timeout_quota_present",
            "passed": bool(proposal_payload)
            and proposal_policy["request_timeout_seconds"] == policy_limits["request_timeout_seconds"]
            and proposal_policy["max_cost_units"] == policy_limits["max_cost_units"]
            and proposal_policy["max_live_api_calls"] == policy_limits["max_live_api_calls"]
            and proposal_policy["max_output_unit_budget"]
            == policy_limits["max_output_unit_budget"],
        },
        {
            "name": "manual_test_proposal_rollback_plan_present",
            "passed": bool(rollback_plan_id),
        },
        {
            "name": "manual_test_proposal_abort_criteria_present",
            "passed": len(safe_abort_criteria) > 0,
        },
        {"name": "manual_test_operator_approval_present", "passed": bool(approval_payload)},
        {
            "name": "manual_test_operator_approval_identity_present",
            "passed": bool(operator_ref),
        },
        {
            "name": "manual_test_operator_approval_timestamp_present",
            "passed": bool(approved_at),
        },
        {
            "name": "manual_test_operator_approval_decision_approved",
            "passed": operator_decision == "approved",
        },
        {
            "name": "manual_test_operator_approval_proposal_hash_match",
            "passed": bool(proposal_hash) and approved_hash == proposal_hash,
        },
        {"name": "manual_test_execution_disabled_by_default", "passed": True},
    ]
    gate_passed = all(check["passed"] for check in checks[:-1])
    status = "approved_disabled" if gate_passed else "blocked"
    projection = {
        "projection_version": MANUAL_PROVIDER_TEST_PROPOSAL_VERSION,
        "status": status,
        "run_id": safe_public_run_id(request.run_id),
        "provider_name": request.provider_name,
        "model_name": request.model_name,
        "proposal_present": bool(proposal_payload),
        "operator_approval_present": bool(approval_payload),
        "proposal_id": proposal_id,
        "proposal_hash": proposal_hash,
        "prompt_contract_hash": request.prompt_contract_hash if proposal_payload else "",
        "policy_limits": policy_limits,
        "proposal_fields": {
            "run_id_match": proposal_run_id == request.run_id if proposal_payload else False,
            "prompt_contract_hash_match": (
                proposal_prompt_hash == request.prompt_contract_hash
                if proposal_payload
                else False
            ),
            "policy_limits_match": checks[3]["passed"],
            "rollback_plan_present": bool(rollback_plan_id),
            "rollback_plan_id": rollback_plan_id,
            "abort_criteria_count": len(safe_abort_criteria),
            "abort_criteria_hash": canonical_proposal["abort_criteria_hash"],
        },
        "operator_approval": {
            "status": "approved" if gate_passed else ("blocked" if approval_payload else "missing"),
            "decision": operator_decision or "missing",
            "operator_ref": operator_ref,
            "approved_at": approved_at,
            "proposal_hash_match": bool(proposal_hash) and approved_hash == proposal_hash,
            "envelope_hash": stable_contract_hash(
                {
                    "run_id": request.run_id,
                    "operator_ref": operator_ref,
                    "approved_at": approved_at,
                    "decision": operator_decision,
                    "proposal_hash": proposal_hash,
                }
            )
            if operator_ref and approved_at and operator_decision and proposal_hash
            else "",
            "auth_material_returned": False,
        },
        "live_ready": False,
        "allowed_to_execute": False,
        "disabled_by_default": True,
        "checks": checks,
        "execution_boundary": {
            "sdk_imports": 0,
            "env_value_reads": 0,
            "api_calls": 0,
            "network_calls": 0,
            "solar_provider_calls": 0,
            "target_runtime_calls": 0,
        },
        "claim_boundary": {
            "scope": "local manual provider test proposal gate only",
            "external_provider_outcome": False,
            "target_runtime_outcome": False,
            "production_trust_claim": False,
        },
    }
    projection["proposal_gate_hash"] = stable_contract_hash(projection)
    return _safe_public_payload(projection)


def provider_manual_test_proposal_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public manual provider test proposal gate projection."""
    request = _request_from_payload(payload)
    policy = _policy_from_payload(payload)
    return _manual_test_proposal_projection(
        payload=payload,
        request=request,
        policy=policy,
    )


def provider_manual_test_preflight_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public manual provider test preflight audit projection."""
    request = _request_from_payload(payload)
    policy = _policy_from_payload(payload)
    live_open_decision = _ready_live_open_decision(payload, request.run_id)
    operator_policy_summary = _operator_policy_summary(
        request=request,
        policy=policy,
        live_open_decision=live_open_decision,
    )
    operator_approval, _, _ = _operator_approval_projection(
        payload=payload,
        policy_summary=operator_policy_summary,
    )
    live_provider_dry_admission = _live_provider_dry_admission_checklist(
        run_id=request.run_id,
        operator_policy_summary=operator_policy_summary,
        operator_approval_envelope=operator_approval,
    )
    manual_provider_test_proposal = _manual_test_proposal_projection(
        payload=payload,
        request=request,
        policy=policy,
    )
    manual_provider_test_executor = _manual_provider_test_executor_projection(
        request=request,
        manual_provider_test_proposal=manual_provider_test_proposal,
        executor_enable_requested=payload.get("manual_test_executor_enable") is True,
    )
    one_shot_live_permission = _one_shot_live_permission_projection(
        payload=payload,
        request=request,
        policy=policy,
        manual_provider_test_proposal=manual_provider_test_proposal,
        manual_provider_test_executor=manual_provider_test_executor,
    )
    return _manual_provider_test_preflight_audit_projection(
        live_provider_dry_admission=live_provider_dry_admission,
        manual_provider_test_proposal=manual_provider_test_proposal,
        manual_provider_test_executor=manual_provider_test_executor,
        one_shot_live_permission=one_shot_live_permission,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_review_packet_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public manual provider test review packet projection."""
    request = _request_from_payload(payload)
    policy = _policy_from_payload(payload)
    live_open_decision = _ready_live_open_decision(payload, request.run_id)
    operator_policy_summary = _operator_policy_summary(
        request=request,
        policy=policy,
        live_open_decision=live_open_decision,
    )
    preflight_audit = provider_manual_test_preflight_summary(payload)
    readiness_decision = _manual_provider_test_readiness_decision_projection(
        payload=payload,
        preflight_audit=preflight_audit,
    )
    return _manual_provider_test_review_packet_projection(
        operator_policy_summary=operator_policy_summary,
        preflight_audit=preflight_audit,
        readiness_decision=readiness_decision,
    )


def _review_packet_export_preview(run_id: str, review_packet: JsonDict) -> JsonDict:
    try:
        record = provider_review_packet_export_record_from_projection(
            review_packet,
            run_id=run_id,
        )
    except Exception:
        return _manual_provider_test_review_packet_export_blocked(
            "review_packet_export_not_available"
        )
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": record.reason,
            "review_packet_hash": record.review_packet_hash,
            "review_packet_export_hash": record.content_hash,
            "export_count": 1,
            "component_count": record.component_count,
            "passed_component_count": record.passed_component_count,
            "mismatch_count": record.mismatch_count,
            "component_hash_count": record.component_hash_count,
            "execution_permission_count": record.execution_permission_count,
        }
    )


def provider_manual_test_handoff_packet_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public final no-call handoff packet projection."""
    request = _request_from_payload(payload)
    policy = _policy_from_payload(payload)
    live_open_decision = _ready_live_open_decision(payload, request.run_id)
    operator_policy_summary = _operator_policy_summary(
        request=request,
        policy=policy,
        live_open_decision=live_open_decision,
    )
    preflight_audit = provider_manual_test_preflight_summary(payload)
    readiness_decision = _manual_provider_test_readiness_decision_projection(
        payload=payload,
        preflight_audit=preflight_audit,
    )
    review_packet = _manual_provider_test_review_packet_projection(
        operator_policy_summary=operator_policy_summary,
        preflight_audit=preflight_audit,
        readiness_decision=readiness_decision,
    )
    review_packet_export = _review_packet_export_preview(
        request.run_id,
        review_packet,
    )
    return _manual_provider_test_handoff_packet_projection(
        operator_policy_summary=operator_policy_summary,
        preflight_audit=preflight_audit,
        readiness_decision=readiness_decision,
        review_packet=review_packet,
        review_packet_export=review_packet_export,
    )


def provider_manual_test_operator_opt_in_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public no-call operator opt-in checklist projection."""
    handoff_packet = provider_manual_test_handoff_packet_summary(payload)
    return _manual_provider_test_operator_opt_in_projection(
        payload=payload,
        handoff_packet=handoff_packet,
    )


def _review_packet_export_from_read_model(read_model: JsonDict) -> JsonDict:
    if str(read_model.get("status", "")) == "blocked":
        return _manual_provider_test_review_packet_export_blocked(
            "review_packet_export_store_unavailable"
        )
    exports = (
        read_model.get("review_packet_exports")
        if isinstance(read_model.get("review_packet_exports"), list)
        else []
    )
    if not exports:
        return _manual_provider_test_review_packet_export_blocked(
            "review_packet_export_not_found"
        )
    selected = exports[-1] if isinstance(exports[-1], dict) else {}
    counts = read_model.get("counts") if isinstance(read_model.get("counts"), dict) else {}
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": str(selected.get("reason", "review_packet_export_execution_closed")),
            "review_packet_hash": str(selected.get("review_packet_hash", "")),
            "review_packet_export_hash": str(selected.get("review_packet_export_hash", "")),
            "export_count": _coerce_int(counts.get("review_packet_export_count", 0)),
            "component_count": _coerce_int(selected.get("component_count", 0)),
            "passed_component_count": _coerce_int(
                selected.get("passed_component_count", 0)
            ),
            "mismatch_count": _coerce_int(selected.get("mismatch_count", 0)),
            "component_hash_count": _coerce_int(selected.get("component_hash_count", 0)),
            "execution_permission_count": _coerce_int(
                selected.get("execution_permission_count", 0)
            ),
        }
    )


def _persist_review_packet_export(
    *,
    run_id: str,
    repository_provider: ProviderEnvelopeRepositoryProvider,
    review_packet: JsonDict,
    expected_review_packet_hash: str = "",
    expected_review_packet_export_hash: str = "",
) -> tuple[JsonDict, JsonDict]:
    actual_hash = str(review_packet.get("review_packet_hash", "")).strip()
    if expected_review_packet_hash and expected_review_packet_hash != actual_hash:
        return (
            _manual_provider_test_review_packet_export_blocked(
                "review_packet_hash_mismatch"
            ),
            {},
        )
    if not actual_hash:
        return (
            _manual_provider_test_review_packet_export_blocked(
                "review_packet_hash_missing"
            ),
            {},
        )
    try:
        repository = repository_provider.repository()
        record = provider_review_packet_export_record_from_projection(
            review_packet,
            run_id=run_id,
        )
        if (
            expected_review_packet_export_hash
            and expected_review_packet_export_hash != record.content_hash
        ):
            return (
                _manual_provider_test_review_packet_export_blocked(
                    "review_packet_export_hash_mismatch"
                ),
                {},
            )
        try:
            repository.save_review_packet_export(record)
        except ValueError as exc:
            if "duplicate" not in str(exc).lower() and "conflict" not in str(exc).lower():
                return (
                    _manual_provider_test_review_packet_export_blocked(
                        "review_packet_export_store_unavailable"
                    ),
                    {},
                )
        read_model = provider_review_packet_export_public_read_model(
            repository,
            run_id=run_id,
        )
    except Exception:
        return (
            _manual_provider_test_review_packet_export_blocked(
                "review_packet_export_store_unavailable"
            ),
            {},
        )
    return _review_packet_export_from_read_model(read_model), read_model


def _blocked_projection(
    *,
    run_id: str,
    repository_provider: ProviderEnvelopeRepositoryProvider,
    check_name: str,
    message: str,
    read_model: JsonDict | None = None,
    adapter_invocation_count: int = 0,
    operator_policy_summary: JsonDict | None = None,
    operator_approval_envelope: JsonDict | None = None,
    live_provider_dry_admission: JsonDict | None = None,
    manual_provider_test_proposal: JsonDict | None = None,
    manual_provider_test_executor: JsonDict | None = None,
    one_shot_live_permission: JsonDict | None = None,
    manual_provider_test_readiness_decision: JsonDict | None = None,
    manual_provider_test_review_packet: JsonDict | None = None,
    manual_provider_test_review_packet_export: JsonDict | None = None,
    manual_provider_test_review_packet_export_read_model: JsonDict | None = None,
    manual_provider_test_handoff_packet: JsonDict | None = None,
    manual_provider_test_operator_opt_in: JsonDict | None = None,
) -> dict[str, Any]:
    selected_operator_approval = operator_approval_envelope or _operator_approval_missing_projection()
    selected_dry_admission = live_provider_dry_admission or _live_provider_dry_admission_checklist(
        run_id=run_id,
        operator_policy_summary=operator_policy_summary,
        operator_approval_envelope=selected_operator_approval,
    )
    selected_manual_proposal = (
        manual_provider_test_proposal or _manual_provider_test_proposal_not_applicable(run_id)
    )
    selected_manual_executor = manual_provider_test_executor or {
        "status": "blocked",
        "reason": "manual_provider_test_proposal_required",
        "planned_call_hash": "",
    }
    selected_one_shot_permission = one_shot_live_permission or _one_shot_live_permission_blocked(
        "one_shot_permission_required"
    )
    execution_boundary = _zero_execution_boundary(
        {"adapter_invocation_count": adapter_invocation_count}
    )
    selected_preflight_audit = _manual_provider_test_preflight_audit_projection(
        live_provider_dry_admission=selected_dry_admission,
        manual_provider_test_proposal=selected_manual_proposal,
        manual_provider_test_executor=selected_manual_executor,
        one_shot_live_permission=selected_one_shot_permission,
        execution_boundary=execution_boundary,
    )
    selected_readiness_decision = (
        manual_provider_test_readiness_decision
        or _manual_provider_test_readiness_decision_blocked(
            "readiness_decision_required"
        )
    )
    selected_review_packet = (
        manual_provider_test_review_packet
        or _manual_provider_test_review_packet_projection(
            operator_policy_summary=operator_policy_summary or {},
            preflight_audit=selected_preflight_audit,
            readiness_decision=selected_readiness_decision,
        )
    )
    selected_review_packet_export = (
        manual_provider_test_review_packet_export
        or _manual_provider_test_review_packet_export_blocked(
            "review_packet_export_not_available"
        )
    )
    selected_handoff_packet = (
        manual_provider_test_handoff_packet
        or _manual_provider_test_handoff_packet_projection(
            operator_policy_summary=operator_policy_summary or {},
            preflight_audit=selected_preflight_audit,
            readiness_decision=selected_readiness_decision,
            review_packet=selected_review_packet,
            review_packet_export=selected_review_packet_export,
        )
    )
    selected_operator_opt_in = (
        manual_provider_test_operator_opt_in
        or _manual_provider_test_operator_opt_in_blocked(
            "operator_opt_in_not_evaluated"
        )
    )
    return _safe_public_payload(
        {
            "projection_version": PROVIDER_ENVELOPE_API_PROJECTION_VERSION,
            "admission_kind": "provider_envelope",
            "runtime_mode": PROVIDER_ENVELOPE_PRECHECK_MODE,
            "fixture_mode": False,
            "durable_user_approval": False,
            "run_id": safe_public_run_id(run_id),
            "status": "blocked",
            "provider_envelope_admission": {
                "status": "blocked",
                "adapter_reached": False,
                "request_contract_hash": "",
                "response_contract_hash": "",
                "counts": {
                    "provider_envelope_count": 0,
                    "request_contract_hash_count": 0,
                    "response_contract_hash_count": 0,
                },
            },
            "operator_policy_summary": operator_policy_summary or {},
            "operator_approval_envelope": selected_operator_approval,
            "live_provider_dry_admission": selected_dry_admission,
            "manual_provider_test_proposal": selected_manual_proposal,
            "manual_provider_test_executor": selected_manual_executor,
            "one_shot_live_permission": selected_one_shot_permission,
            "manual_provider_test_preflight_audit": selected_preflight_audit,
            "manual_provider_test_readiness_decision": selected_readiness_decision,
            "manual_provider_test_review_packet": selected_review_packet,
            "manual_provider_test_review_packet_export": selected_review_packet_export,
            "manual_provider_test_review_packet_export_read_model": (
                manual_provider_test_review_packet_export_read_model or {}
            ),
            "manual_provider_test_handoff_packet": selected_handoff_packet,
            "manual_provider_test_operator_opt_in": selected_operator_opt_in,
            "provider_envelope_read_model": read_model or {},
            "checks": [{"name": check_name, "passed": False}],
            "errors": [message],
            "repository_boundary": {
                "provider_envelope_backend": repository_provider.backend,
                "provider_envelope_store_configured": repository_provider.configured,
                "raw_row_returned": False,
                "root_path_returned": False,
            },
            "execution_boundary": execution_boundary,
            "claim_boundary": {
                "scope": "local provider envelope precheck only",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
                "production_trust_claim": False,
            },
        }
    )


def _policy_from_payload(payload: dict[str, Any]) -> SolarCostTimeoutPolicy:
    policy_payload = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    return SolarCostTimeoutPolicy(
        request_timeout_seconds=policy_payload.get("request_timeout_seconds"),
        max_cost_units=policy_payload.get("max_cost_units"),
        max_live_api_calls=policy_payload.get("max_live_api_calls"),
        max_output_tokens=policy_payload.get("max_output_tokens"),
        retry_count=int(policy_payload.get("retry_count", 0)),
    )


def _approval_from_payload(payload: dict[str, Any]) -> ProviderApprovalRecord:
    approval_payload = payload.get("approval")
    if not isinstance(approval_payload, dict):
        raise ValueError("provider envelope approval payload is required")
    return ProviderApprovalRecord(**_dataclass_payload(approval_payload, ProviderApprovalRecord))


def _request_from_payload(payload: dict[str, Any]) -> ProviderRequest:
    run_id = str(payload["run_id"])
    expected_hash = payload.get("expected_request_contract_hash")
    metadata: JsonDict = {}
    if isinstance(expected_hash, str) and expected_hash:
        metadata["expected_request_contract_hash"] = expected_hash
    return ProviderRequest(
        run_id=run_id,
        prompt_contract_hash=str(payload["prompt_contract_hash"]),
        provider_name=str(payload.get("provider_name", SOLAR_PRO_3_PROVIDER)),
        model_name=str(payload.get("model_name", SOLAR_PRO_3_MODEL)),
        mode=SOLAR_LIVE_ADAPTER_MODE,
        env_key_name=SOLAR_PRO_3_ENV_KEY_NAME,
        approval=_approval_from_payload(payload),
        metadata=metadata,
    )


def _operator_policy_summary(
    *,
    request: ProviderRequest,
    policy: SolarCostTimeoutPolicy,
    live_open_decision,
) -> JsonDict:
    checks = getattr(live_open_decision, "checks", [])
    missing_controls = [
        str(check.get("name", ""))
        for check in checks
        if check.get("passed") is False and str(check.get("name", "")) in LIVE_OPEN_REQUIRED_CONTROLS
    ]
    summary = {
        "projection_version": OPERATOR_POLICY_SUMMARY_VERSION,
        "run_id": safe_public_run_id(request.run_id),
        "provider_name": request.provider_name,
        "model_name": request.model_name,
        "runtime_mode": PROVIDER_ENVELOPE_PRECHECK_MODE,
        "env_key_name": SOLAR_PRO_3_ENV_KEY_NAME,
        "policy": {
            "request_timeout_seconds": int(policy.request_timeout_seconds or 0),
            "max_cost_units": int(policy.max_cost_units or 0),
            "max_live_api_calls": int(policy.max_live_api_calls or 0),
            "max_output_unit_budget": int(policy.max_output_tokens or 0),
            "retry_count": int(policy.retry_count),
        },
        "readiness": {
            "surface": SOLAR_PROVIDER_SURFACE,
            "required_control_count": len(LIVE_OPEN_REQUIRED_CONTROLS),
            "satisfied_control_count": len(LIVE_OPEN_REQUIRED_CONTROLS) - len(missing_controls),
            "missing_control_count": len(missing_controls),
            "missing_controls": missing_controls,
            "eligible_for_live_open": bool(
                getattr(live_open_decision, "eligible_for_live_open", False)
            ),
            "allowed_to_execute": bool(getattr(live_open_decision, "allowed_to_execute", False)),
        },
        "approval_target": {
            "prompt_contract_hash": request.prompt_contract_hash,
            "input_text_included": False,
            "provider_body_included": False,
            "auth_material_included": False,
        },
        "execution_boundary": {
            "sdk_imports": 0,
            "env_value_reads": 0,
            "api_calls": 0,
            "network_calls": 0,
            "solar_provider_calls": 0,
            "target_runtime_calls": 0,
        },
        "claim_boundary": {
            "scope": "local provider precheck policy summary",
            "external_provider_outcome": False,
            "target_runtime_outcome": False,
            "production_trust_claim": False,
        },
    }
    summary["policy_summary_hash"] = stable_contract_hash(summary)
    return _safe_public_payload(summary)


def provider_precheck_operator_policy_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public policy summary an operator must approve."""
    request = _request_from_payload(payload)
    policy = _policy_from_payload(payload)
    decision = _ready_live_open_decision(payload, request.run_id)
    return _operator_policy_summary(
        request=request,
        policy=policy,
        live_open_decision=decision,
    )


def _operator_approval_missing_projection() -> JsonDict:
    return {
        "projection_version": OPERATOR_APPROVAL_ENVELOPE_VERSION,
        "status": "missing",
        "decision": "missing",
        "operator_ref": "",
        "approved_at": "",
        "policy_summary_hash": "",
        "envelope_hash": "",
        "auth_material_returned": False,
    }


def _operator_approval_projection(
    *,
    payload: dict[str, Any],
    policy_summary: JsonDict,
) -> tuple[JsonDict, list[JsonDict], list[str]]:
    approval_payload = payload.get("operator_approval")
    checks: list[JsonDict] = []
    errors: list[str] = []
    expected_hash = str(policy_summary.get("policy_summary_hash", ""))
    if not isinstance(approval_payload, dict):
        checks.append({"name": "operator_approval_envelope_present", "passed": False})
        errors.append("operator approval envelope is required before provider precheck.")
        return _operator_approval_missing_projection(), checks, errors

    operator_ref = str(approval_payload.get("operator_ref", "")).strip()
    approved_at = str(approval_payload.get("approved_at", "")).strip()
    decision = str(approval_payload.get("decision", "")).strip().lower()
    approved_hash = str(approval_payload.get("approved_policy_summary_hash", "")).strip()
    checks.extend(
        [
            {
                "name": "operator_approval_envelope_present",
                "passed": True,
            },
            {
                "name": "operator_approval_identity_present",
                "passed": bool(operator_ref),
            },
            {
                "name": "operator_approval_timestamp_present",
                "passed": bool(approved_at),
            },
            {
                "name": "operator_approval_decision_approved",
                "passed": decision == "approved",
            },
            {
                "name": "operator_approval_policy_summary_hash_match",
                "passed": bool(expected_hash) and approved_hash == expected_hash,
            },
        ]
    )
    if not operator_ref:
        errors.append("operator approval identity is required.")
    if not approved_at:
        errors.append("operator approval timestamp is required.")
    if decision != "approved":
        errors.append("operator approval decision must be approved.")
    if approved_hash != expected_hash:
        errors.append("operator approval must reference the exact policy summary hash.")

    status = "approved" if not errors else "blocked"
    envelope = {
        "projection_version": OPERATOR_APPROVAL_ENVELOPE_VERSION,
        "status": status,
        "decision": decision or "missing",
        "operator_ref": operator_ref,
        "approved_at": approved_at,
        "policy_summary_hash": expected_hash,
        "envelope_hash": stable_contract_hash(
            {
                "run_id": policy_summary.get("run_id", ""),
                "operator_ref": operator_ref,
                "approved_at": approved_at,
                "decision": decision,
                "policy_summary_hash": expected_hash,
            }
        )
        if operator_ref and approved_at and decision
        else "",
        "auth_material_returned": False,
    }
    return _safe_public_payload(envelope), checks, errors


def _ready_live_open_decision(payload: dict[str, Any], run_id: str):
    controls_payload = (
        payload.get("live_open_controls")
        if isinstance(payload.get("live_open_controls"), dict)
        else {}
    )
    controls = {
        field_name: bool(controls_payload.get(field_name, False))
        for field_name in LIVE_OPEN_REQUIRED_CONTROLS
    }
    return evaluate_live_open_request(
        LiveOpenRequest(
            run_id=run_id,
            surface=SOLAR_PROVIDER_SURFACE,
            env_key_name=SOLAR_PRO_3_ENV_KEY_NAME,
            **controls,
        )
    )


def _adapter_config(policy: SolarCostTimeoutPolicy) -> SolarPro3LiveAdapterConfig:
    return SolarPro3LiveAdapterConfig(
        enabled=True,
        request_timeout_seconds=policy.request_timeout_seconds,
        max_cost_units=policy.max_cost_units,
        max_output_tokens=policy.max_output_tokens,
        max_live_api_calls=policy.max_live_api_calls,
        allow_network=False,
    )


def _read_model_counts(read_model: JsonDict) -> JsonDict:
    counts = read_model.get("counts") if isinstance(read_model.get("counts"), dict) else {}
    return {
        "provider_envelope_count": int(counts.get("provider_envelope_count", 0)),
        "request_contract_hash_count": int(counts.get("request_contract_hash_count", 0)),
        "response_contract_hash_count": int(counts.get("response_contract_hash_count", 0)),
    }


def _projection_from_result(
    *,
    run_id: str,
    result,
    read_model: JsonDict,
    repository_provider: ProviderEnvelopeRepositoryProvider,
    operator_policy_summary: JsonDict,
    operator_approval_envelope: JsonDict,
    live_provider_dry_admission: JsonDict,
    manual_provider_test_proposal: JsonDict,
    manual_provider_test_executor: JsonDict,
    one_shot_live_permission: JsonDict,
    payload: dict[str, Any],
) -> dict[str, Any]:
    metrics = dict(result.metrics)
    request_hash = ""
    response_hash = ""
    if result.audit_events:
        first_event = result.audit_events[0]
        if isinstance(first_event, dict):
            request_hash = str(first_event.get("request_contract_hash", ""))
            response_hash = str(first_event.get("response_contract_hash", ""))
    admission_status = (
        "admitted"
        if int(metrics.get("provider_envelope_admission_hash_match_count", 0)) == 1
        else "blocked"
    )
    adapter_reached = int(metrics.get("provider_envelope_adapter_invocation_count", 0)) == 1
    execution_boundary = _zero_execution_boundary(
        {
            **metrics,
            "adapter_invocation_count": int(
                metrics.get("provider_envelope_adapter_invocation_count", 0)
            ),
        }
    )
    preflight_audit = _manual_provider_test_preflight_audit_projection(
        live_provider_dry_admission=live_provider_dry_admission,
        manual_provider_test_proposal=manual_provider_test_proposal,
        manual_provider_test_executor=manual_provider_test_executor,
        one_shot_live_permission=one_shot_live_permission,
        execution_boundary=execution_boundary,
    )
    readiness_decision = _manual_provider_test_readiness_decision_projection(
        payload=payload,
        preflight_audit=preflight_audit,
    )
    review_packet = _manual_provider_test_review_packet_projection(
        operator_policy_summary=operator_policy_summary,
        preflight_audit=preflight_audit,
        readiness_decision=readiness_decision,
    )
    review_packet_export, review_packet_export_read_model = _persist_review_packet_export(
        run_id=run_id,
        repository_provider=repository_provider,
        review_packet=review_packet,
        expected_review_packet_hash=str(payload.get("expected_review_packet_hash", "")).strip(),
        expected_review_packet_export_hash=str(
            payload.get("expected_review_packet_export_hash", "")
        ).strip(),
    )
    handoff_packet = _manual_provider_test_handoff_packet_projection(
        operator_policy_summary=operator_policy_summary,
        preflight_audit=preflight_audit,
        readiness_decision=readiness_decision,
        review_packet=review_packet,
        review_packet_export=review_packet_export,
    )
    expected_handoff_packet_hash = str(
        payload.get("expected_handoff_packet_hash", "")
    ).strip()
    if (
        expected_handoff_packet_hash
        and expected_handoff_packet_hash != handoff_packet.get("handoff_packet_hash")
    ):
        handoff_packet = _manual_provider_test_handoff_packet_blocked(
            "handoff_packet_hash_mismatch"
        )
    operator_opt_in = _manual_provider_test_operator_opt_in_projection(
        payload=payload,
        handoff_packet=handoff_packet,
    )
    return _safe_public_payload(
        {
            "projection_version": PROVIDER_ENVELOPE_API_PROJECTION_VERSION,
            "admission_kind": "provider_envelope",
            "runtime_mode": PROVIDER_ENVELOPE_PRECHECK_MODE,
            "fixture_mode": False,
            "durable_user_approval": False,
            "run_id": safe_public_run_id(run_id),
            "status": result.status,
            "provider_envelope_admission": {
                "status": admission_status,
                "adapter_reached": adapter_reached,
                "request_contract_hash": request_hash,
                "response_contract_hash": response_hash,
                "counts": _read_model_counts(read_model),
            },
            "operator_policy_summary": operator_policy_summary,
            "operator_approval_envelope": operator_approval_envelope,
            "live_provider_dry_admission": live_provider_dry_admission,
            "manual_provider_test_proposal": manual_provider_test_proposal,
            "manual_provider_test_executor": manual_provider_test_executor,
            "one_shot_live_permission": one_shot_live_permission,
            "manual_provider_test_preflight_audit": preflight_audit,
            "manual_provider_test_readiness_decision": readiness_decision,
            "manual_provider_test_review_packet": review_packet,
            "manual_provider_test_review_packet_export": review_packet_export,
            "manual_provider_test_review_packet_export_read_model": (
                review_packet_export_read_model
            ),
            "manual_provider_test_handoff_packet": handoff_packet,
            "manual_provider_test_operator_opt_in": operator_opt_in,
            "provider_envelope_read_model": read_model,
            "checks": _check_map(result.checks),
            "errors": [str(error) for error in result.errors],
            "repository_boundary": {
                "provider_envelope_backend": repository_provider.backend,
                "provider_envelope_store_configured": repository_provider.configured,
                "raw_row_returned": False,
                "root_path_returned": False,
            },
            "execution_boundary": execution_boundary,
            "claim_boundary": {
                "scope": "local provider envelope precheck only",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
                "production_trust_claim": False,
            },
        }
    )


def run_provider_envelope_precheck(
    payload: dict[str, Any],
    *,
    repository_provider: ProviderEnvelopeRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Run a local no-call provider envelope admission precheck."""
    selected_provider = repository_provider or ProviderEnvelopeRepositoryProvider()
    if payload.get("fixture_mode") is True or str(payload.get("runtime_mode", "")) in {
        "fixture",
        "dry_run",
    }:
        raise ValueError("fixture/dry-run paths cannot use provider envelope live precheck")

    request = _request_from_payload(payload)
    policy = _policy_from_payload(payload)
    live_open_decision = _ready_live_open_decision(payload, request.run_id)
    operator_policy_summary = _operator_policy_summary(
        request=request,
        policy=policy,
        live_open_decision=live_open_decision,
    )
    operator_approval, operator_checks, operator_errors = _operator_approval_projection(
        payload=payload,
        policy_summary=operator_policy_summary,
    )
    live_provider_dry_admission = _live_provider_dry_admission_checklist(
        run_id=request.run_id,
        operator_policy_summary=operator_policy_summary,
        operator_approval_envelope=operator_approval,
    )
    manual_provider_test_proposal = _manual_test_proposal_projection(
        payload=payload,
        request=request,
        policy=policy,
    )
    manual_provider_test_executor = _manual_provider_test_executor_projection(
        request=request,
        manual_provider_test_proposal=manual_provider_test_proposal,
        executor_enable_requested=payload.get("manual_test_executor_enable") is True,
    )
    one_shot_live_permission = _one_shot_live_permission_projection(
        payload=payload,
        request=request,
        policy=policy,
        manual_provider_test_proposal=manual_provider_test_proposal,
        manual_provider_test_executor=manual_provider_test_executor,
    )
    preflight_audit_for_decision = _manual_provider_test_preflight_audit_projection(
        live_provider_dry_admission=live_provider_dry_admission,
        manual_provider_test_proposal=manual_provider_test_proposal,
        manual_provider_test_executor=manual_provider_test_executor,
        one_shot_live_permission=one_shot_live_permission,
        execution_boundary=_zero_execution_boundary(),
    )
    manual_provider_test_readiness_decision = (
        _manual_provider_test_readiness_decision_projection(
            payload=payload,
            preflight_audit=preflight_audit_for_decision,
        )
    )
    manual_provider_test_review_packet = _manual_provider_test_review_packet_projection(
        operator_policy_summary=operator_policy_summary,
        preflight_audit=preflight_audit_for_decision,
        readiness_decision=manual_provider_test_readiness_decision,
    )
    expected_review_packet_hash = str(payload.get("expected_review_packet_hash", "")).strip()
    actual_review_packet_hash = str(
        manual_provider_test_review_packet.get("review_packet_hash", "")
    ).strip()
    if expected_review_packet_hash and expected_review_packet_hash != actual_review_packet_hash:
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name="manual_provider_test_review_packet_hash_match",
            message="manual provider test review packet hash mismatch.",
            operator_policy_summary=operator_policy_summary,
            operator_approval_envelope=operator_approval,
            live_provider_dry_admission=live_provider_dry_admission,
            manual_provider_test_proposal=manual_provider_test_proposal,
            manual_provider_test_executor=manual_provider_test_executor,
            one_shot_live_permission=one_shot_live_permission,
            manual_provider_test_readiness_decision=manual_provider_test_readiness_decision,
            manual_provider_test_review_packet=manual_provider_test_review_packet,
            manual_provider_test_review_packet_export=(
                _manual_provider_test_review_packet_export_blocked(
                    "review_packet_hash_mismatch"
                )
            ),
        )
    manual_provider_test_review_packet_export_preview = _review_packet_export_preview(
        request.run_id,
        manual_provider_test_review_packet,
    )
    expected_review_packet_export_hash = str(
        payload.get("expected_review_packet_export_hash", "")
    ).strip()
    actual_review_packet_export_hash = str(
        manual_provider_test_review_packet_export_preview.get(
            "review_packet_export_hash",
            "",
        )
    ).strip()
    if (
        expected_review_packet_export_hash
        and expected_review_packet_export_hash != actual_review_packet_export_hash
    ):
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name="manual_provider_test_review_packet_export_hash_match",
            message="manual provider test review packet export hash mismatch.",
            operator_policy_summary=operator_policy_summary,
            operator_approval_envelope=operator_approval,
            live_provider_dry_admission=live_provider_dry_admission,
            manual_provider_test_proposal=manual_provider_test_proposal,
            manual_provider_test_executor=manual_provider_test_executor,
            one_shot_live_permission=one_shot_live_permission,
            manual_provider_test_readiness_decision=manual_provider_test_readiness_decision,
            manual_provider_test_review_packet=manual_provider_test_review_packet,
            manual_provider_test_review_packet_export=(
                _manual_provider_test_review_packet_export_blocked(
                    "review_packet_export_hash_mismatch"
                )
            ),
            manual_provider_test_handoff_packet=(
                _manual_provider_test_handoff_packet_blocked(
                    "review_packet_export_hash_mismatch"
                )
            ),
            manual_provider_test_operator_opt_in=(
                _manual_provider_test_operator_opt_in_blocked(
                    "handoff_packet_missing_or_mismatched"
                )
            ),
        )
    manual_provider_test_handoff_packet_preview = (
        _manual_provider_test_handoff_packet_projection(
            operator_policy_summary=operator_policy_summary,
            preflight_audit=preflight_audit_for_decision,
            readiness_decision=manual_provider_test_readiness_decision,
            review_packet=manual_provider_test_review_packet,
            review_packet_export=manual_provider_test_review_packet_export_preview,
        )
    )
    expected_handoff_packet_hash = str(
        payload.get("expected_handoff_packet_hash", "")
    ).strip()
    actual_handoff_packet_hash = str(
        manual_provider_test_handoff_packet_preview.get("handoff_packet_hash", "")
    ).strip()
    if expected_handoff_packet_hash and expected_handoff_packet_hash != actual_handoff_packet_hash:
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name="manual_provider_test_handoff_packet_hash_match",
            message="manual provider test handoff packet hash mismatch.",
            operator_policy_summary=operator_policy_summary,
            operator_approval_envelope=operator_approval,
            live_provider_dry_admission=live_provider_dry_admission,
            manual_provider_test_proposal=manual_provider_test_proposal,
            manual_provider_test_executor=manual_provider_test_executor,
            one_shot_live_permission=one_shot_live_permission,
            manual_provider_test_readiness_decision=manual_provider_test_readiness_decision,
            manual_provider_test_review_packet=manual_provider_test_review_packet,
            manual_provider_test_review_packet_export=(
                manual_provider_test_review_packet_export_preview
            ),
            manual_provider_test_handoff_packet=(
                _manual_provider_test_handoff_packet_blocked(
                    "handoff_packet_hash_mismatch"
                )
            ),
            manual_provider_test_operator_opt_in=(
                _manual_provider_test_operator_opt_in_blocked(
                    "handoff_packet_hash_mismatch"
                )
            ),
        )
    if operator_errors:
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name=operator_checks[-1]["name"] if operator_checks else "operator_approval_blocked",
            message=operator_errors[0],
            operator_policy_summary=operator_policy_summary,
            operator_approval_envelope=operator_approval,
            live_provider_dry_admission=live_provider_dry_admission,
            manual_provider_test_proposal=manual_provider_test_proposal,
            manual_provider_test_executor=manual_provider_test_executor,
            one_shot_live_permission=one_shot_live_permission,
            manual_provider_test_readiness_decision=manual_provider_test_readiness_decision,
            manual_provider_test_review_packet=manual_provider_test_review_packet,
        )

    if not selected_provider.configured:
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_repository_configured",
            message="provider envelope repository is required before adapter admission.",
            operator_policy_summary=operator_policy_summary,
            operator_approval_envelope=operator_approval,
            live_provider_dry_admission=live_provider_dry_admission,
            manual_provider_test_proposal=manual_provider_test_proposal,
            manual_provider_test_executor=manual_provider_test_executor,
            one_shot_live_permission=one_shot_live_permission,
            manual_provider_test_readiness_decision=manual_provider_test_readiness_decision,
            manual_provider_test_review_packet=manual_provider_test_review_packet,
        )

    request_result = build_solar_request_contract_fixture(request, policy)
    contract_result = attach_solar_response_projection_fixture(
        request_result,
        response_summary=str(
            payload.get("response_summary") or "sanitized provider envelope precheck projection"
        ),
        raw_response_body=None,
    )
    if contract_result.status != "projected_fixture":
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_contract_projected",
            message="provider envelope contract fixture could not be projected.",
            adapter_invocation_count=0,
            operator_policy_summary=operator_policy_summary,
            operator_approval_envelope=operator_approval,
            live_provider_dry_admission=live_provider_dry_admission,
            manual_provider_test_proposal=manual_provider_test_proposal,
            manual_provider_test_executor=manual_provider_test_executor,
            one_shot_live_permission=one_shot_live_permission,
            manual_provider_test_readiness_decision=manual_provider_test_readiness_decision,
            manual_provider_test_review_packet=manual_provider_test_review_packet,
        )

    try:
        repository = selected_provider.repository()
    except Exception:
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_repository_available",
            message="provider envelope repository is unavailable.",
            operator_policy_summary=operator_policy_summary,
            operator_approval_envelope=operator_approval,
            live_provider_dry_admission=live_provider_dry_admission,
            manual_provider_test_proposal=manual_provider_test_proposal,
            manual_provider_test_executor=manual_provider_test_executor,
            one_shot_live_permission=one_shot_live_permission,
            manual_provider_test_readiness_decision=manual_provider_test_readiness_decision,
            manual_provider_test_review_packet=manual_provider_test_review_packet,
        )

    service = ProviderEnvelopeAdmissionService(repository)
    adapter = DisabledSolarPro3LiveAdapter(
        config=_adapter_config(policy),
        live_open_decision=live_open_decision,
    )
    result = invoke_adapter_after_provider_envelope_admission(
        adapter=adapter,
        request=request,
        contract_result=contract_result,
        admission_service=service,
    )
    try:
        read_model = provider_envelope_public_read_model(repository, run_id=request.run_id)
    except Exception:
        read_model = {}
    return _projection_from_result(
        run_id=request.run_id,
        result=result,
        read_model=read_model,
        repository_provider=selected_provider,
        operator_policy_summary=operator_policy_summary,
        operator_approval_envelope=operator_approval,
        live_provider_dry_admission=live_provider_dry_admission,
        manual_provider_test_proposal=manual_provider_test_proposal,
        manual_provider_test_executor=manual_provider_test_executor,
        one_shot_live_permission=one_shot_live_permission,
        payload=payload,
    )


def read_provider_envelope_precheck(
    run_id: str,
    *,
    repository_provider: ProviderEnvelopeRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Read sanitized provider envelope evidence for API/demo responses."""
    selected_provider = repository_provider or ProviderEnvelopeRepositoryProvider()
    if not selected_provider.configured:
        return _blocked_projection(
            run_id=run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_repository_configured",
            message="provider envelope repository is not configured.",
        )
    try:
        repository = selected_provider.repository()
        read_model = provider_envelope_public_read_model(
            repository,
            run_id=run_id,
        )
        review_packet_export_read_model = provider_review_packet_export_public_read_model(
            repository,
            run_id=run_id,
        )
    except Exception:
        return _blocked_projection(
            run_id=run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_repository_available",
            message="provider envelope repository is unavailable.",
        )
    review_packet_export = _review_packet_export_from_read_model(
        review_packet_export_read_model
    )
    return _safe_public_payload(
        {
            "projection_version": PROVIDER_ENVELOPE_API_PROJECTION_VERSION,
            "admission_kind": "provider_envelope",
            "runtime_mode": PROVIDER_ENVELOPE_PRECHECK_MODE,
            "fixture_mode": False,
            "durable_user_approval": False,
            "run_id": safe_public_run_id(run_id),
            "status": read_model.get("status", "blocked"),
            "provider_envelope_admission": {
                "status": "read_model_only",
                "adapter_reached": False,
                "request_contract_hash": "",
                "response_contract_hash": "",
                "counts": _read_model_counts(read_model),
            },
            "operator_policy_summary": {},
            "operator_approval_envelope": {
                "projection_version": OPERATOR_APPROVAL_ENVELOPE_VERSION,
                "status": "not_applicable",
                "decision": "not_applicable",
                "operator_ref": "",
                "approved_at": "",
                "policy_summary_hash": "",
                "envelope_hash": "",
                "auth_material_returned": False,
            },
            "live_provider_dry_admission": _live_provider_dry_admission_checklist(
                run_id=run_id,
                operator_policy_summary=None,
                operator_approval_envelope={
                    "projection_version": OPERATOR_APPROVAL_ENVELOPE_VERSION,
                    "status": "not_applicable",
                    "decision": "not_applicable",
                    "operator_ref": "",
                    "approved_at": "",
                    "policy_summary_hash": "",
                    "envelope_hash": "",
                    "auth_material_returned": False,
                },
            ),
            "manual_provider_test_proposal": _manual_provider_test_proposal_not_applicable(
                run_id
            ),
            "manual_provider_test_executor": {
                "status": "blocked",
                "reason": "manual_provider_test_proposal_required",
                "planned_call_hash": "",
            },
            "one_shot_live_permission": _one_shot_live_permission_blocked(
                "one_shot_permission_required"
            ),
            "manual_provider_test_preflight_audit": _manual_provider_test_preflight_audit_blocked(
                "proposal_component_missing_or_blocked"
            ),
            "manual_provider_test_readiness_decision": _manual_provider_test_readiness_decision_blocked(
                "readiness_decision_required"
            ),
            "manual_provider_test_review_packet": _manual_provider_test_review_packet_blocked(
                "policy_summary_missing_or_mismatched"
            ),
            "manual_provider_test_review_packet_export": review_packet_export,
            "manual_provider_test_review_packet_export_read_model": (
                review_packet_export_read_model
            ),
            "manual_provider_test_handoff_packet": _manual_provider_test_handoff_packet_projection(
                operator_policy_summary={},
                preflight_audit=_manual_provider_test_preflight_audit_blocked(
                    "proposal_component_missing_or_blocked"
                ),
                readiness_decision=_manual_provider_test_readiness_decision_blocked(
                    "readiness_decision_required"
                ),
                review_packet=_manual_provider_test_review_packet_blocked(
                    "policy_summary_missing_or_mismatched"
                ),
                review_packet_export=review_packet_export,
            ),
            "manual_provider_test_operator_opt_in": _manual_provider_test_operator_opt_in_blocked(
                "handoff_packet_missing_or_mismatched"
            ),
            "provider_envelope_read_model": read_model,
            "checks": [{"name": "provider_envelope_read_model_available", "passed": True}],
            "errors": [],
            "repository_boundary": {
                "provider_envelope_backend": selected_provider.backend,
                "provider_envelope_store_configured": selected_provider.configured,
                "raw_row_returned": False,
                "root_path_returned": False,
            },
            "execution_boundary": _zero_execution_boundary(),
            "claim_boundary": {
                "scope": "local provider envelope read model only",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
                "production_trust_claim": False,
            },
        }
    )


__all__ = [
    "ProviderEnvelopeRepositoryConfig",
    "ProviderEnvelopeRepositoryProvider",
    "LIVE_PROVIDER_DRY_ADMISSION_VERSION",
    "MANUAL_PROVIDER_TEST_PROPOSAL_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTOR_VERSION",
    "ONE_SHOT_LIVE_PERMISSION_VERSION",
    "MANUAL_PROVIDER_TEST_PREFLIGHT_AUDIT_VERSION",
    "MANUAL_PROVIDER_TEST_READINESS_DECISION_VERSION",
    "MANUAL_PROVIDER_TEST_REVIEW_PACKET_VERSION",
    "MANUAL_PROVIDER_TEST_REVIEW_PACKET_EXPORT_VERSION",
    "MANUAL_PROVIDER_TEST_HANDOFF_PACKET_VERSION",
    "MANUAL_PROVIDER_TEST_OPERATOR_OPT_IN_VERSION",
    "provider_manual_test_proposal_summary",
    "provider_manual_test_preflight_summary",
    "provider_manual_test_review_packet_summary",
    "provider_manual_test_handoff_packet_summary",
    "provider_manual_test_operator_opt_in_summary",
    "provider_precheck_operator_policy_summary",
    "read_provider_envelope_precheck",
    "run_provider_envelope_precheck",
]

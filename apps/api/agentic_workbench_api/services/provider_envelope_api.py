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
MANUAL_PROVIDER_TEST_SEALED_PRE_EXECUTION_PACKET_VERSION = (
    "manual-provider-test-sealed-pre-execution-packet-v1"
)
MANUAL_PROVIDER_TEST_ARMING_RECORD_VERSION = (
    "manual-provider-test-live-execution-arming-record-v1"
)
MANUAL_PROVIDER_TEST_RELEASE_PROPOSAL_VERSION = (
    "manual-provider-test-execution-release-proposal-v1"
)
MANUAL_PROVIDER_TEST_FINAL_RELEASE_PACKET_VERSION = (
    "manual-provider-test-final-release-packet-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_SWITCH_VERSION = (
    "manual-provider-test-disabled-first-call-execution-switch-v1"
)
MANUAL_PROVIDER_TEST_EXECUTOR_PREFLIGHT_VERSION = (
    "manual-provider-test-disabled-first-call-executor-preflight-v1"
)
MANUAL_PROVIDER_TEST_EXECUTOR_DISPATCH_VERSION = (
    "manual-provider-test-disabled-first-call-executor-dispatch-record-v1"
)
MANUAL_PROVIDER_TEST_INVOCATION_RECEIPT_VERSION = (
    "manual-provider-test-disabled-first-call-executor-invocation-receipt-v1"
)
MANUAL_PROVIDER_TEST_POST_INVOCATION_AUDIT_VERSION = (
    "manual-provider-test-disabled-first-call-post-invocation-audit-v1"
)
MANUAL_PROVIDER_TEST_COMPLETION_SUMMARY_VERSION = (
    "manual-provider-test-disabled-first-call-completion-summary-v1"
)
MANUAL_PROVIDER_TEST_CLOSEOUT_RECORD_VERSION = (
    "manual-provider-test-disabled-first-call-closeout-record-v1"
)
MANUAL_PROVIDER_TEST_OPERATOR_HANDBACK_VERSION = (
    "manual-provider-test-disabled-first-call-operator-handback-v1"
)
MANUAL_PROVIDER_TEST_OPERATOR_DECISION_PACKET_VERSION = (
    "manual-provider-test-disabled-first-call-operator-decision-packet-v1"
)
MANUAL_PROVIDER_TEST_OPERATOR_RELEASE_ATTESTATION_VERSION = (
    "manual-provider-test-disabled-first-call-operator-release-attestation-v1"
)
MANUAL_PROVIDER_TEST_RELEASE_AUTHORIZATION_SEAL_VERSION = (
    "manual-provider-test-disabled-first-call-release-authorization-seal-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_AUTHORIZATION_CAPSULE_VERSION = (
    "manual-provider-test-disabled-first-call-execution-authorization-capsule-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_EXPORT_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-export-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_HANDOFF_PACKET_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-handoff-packet-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_REVIEW_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-operator-review-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_DECISION_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-operator-decision-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_ATTESTATION_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-release-attestation-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_SEAL_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-release-seal-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_FINAL_AUTHORIZATION_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-final-authorization-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_EXPORT_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-export-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_HANDOFF_PACKET_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-handoff-packet-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_REVIEW_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-operator-review-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_DECISION_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-operator-decision-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_ATTESTATION_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-release-attestation-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_SEAL_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-release-seal-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHORIZATION_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-final-authorization-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_EXPORT_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-final-authz-export-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_HANDOFF_PACKET_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-final-authz-handoff-packet-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_REVIEW_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-final-authz-operator-review-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_DECISION_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-final-authz-operator-decision-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_ATTESTATION_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-final-authz-release-attestation-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_SEAL_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-final-authz-release-seal-v1"
)
MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_FINAL_AUTHORIZATION_VERSION = (
    "manual-provider-test-disabled-first-call-execution-capsule-authz-final-authz-final-authorization-v1"
)

EXECUTOR_PREFLIGHT_NO_CALL_COUNTER_FIELDS = (
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


def _manual_provider_test_sealed_packet_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "sealed_packet_hash": "",
            "handoff_packet_hash": "",
            "operator_opt_in_hash": "",
            "cost_timeout_quota_hash": "",
            "rollback_abort_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_arming_record_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "arming_record_hash": "",
            "sealed_packet_hash": "",
            "operator_hash": "",
            "expiry_hash": "",
            "rollback_abort_hash": "",
            "abort_policy_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_release_proposal_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "release_proposal_hash": "",
            "arming_record_hash": "",
            "operator_hash": "",
            "release_window_hash": "",
            "rollback_abort_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_final_release_packet_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "final_release_packet_hash": "",
            "release_proposal_hash": "",
            "arming_record_hash": "",
            "operator_hash": "",
            "release_window_hash": "",
            "rollback_abort_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_switch_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_switch_hash": "",
            "final_release_packet_hash": "",
            "switch_enable_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "enable_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_executor_preflight_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "executor_preflight_hash": "",
            "execution_switch_hash": "",
            "final_release_packet_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_executor_dispatch_record_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "dispatch_record_hash": "",
            "executor_preflight_hash": "",
            "planned_dispatch_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "dispatch_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_invocation_receipt_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "invocation_receipt_hash": "",
            "dispatch_record_hash": "",
            "result_placeholder_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "receipt_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_post_invocation_audit_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "post_invocation_audit_hash": "",
            "invocation_receipt_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "audit_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_completion_summary_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "completion_summary_hash": "",
            "post_invocation_audit_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "summary_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_closeout_record_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "closeout_record_hash": "",
            "completion_summary_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "closeout_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_operator_handback_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "operator_handback_hash": "",
            "closeout_record_hash": "",
            "operator_review_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "operator_review_count": 0,
            "handback_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_operator_decision_packet_blocked(reason: str) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "operator_decision_packet_hash": "",
            "operator_handback_hash": "",
            "operator_decision_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "operator_decision_count": 0,
            "decision_packet_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_operator_release_attestation_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "operator_release_attestation_hash": "",
            "operator_decision_packet_hash": "",
            "operator_attestation_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "operator_attestation_count": 0,
            "attestation_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_release_authorization_seal_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "release_seal_hash": "",
            "operator_release_attestation_hash": "",
            "seal_material_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "seal_material_count": 0,
            "seal_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_authorization_capsule_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_hash": "",
            "release_seal_hash": "",
            "final_authz_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "final_authz_count": 0,
            "capsule_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_export_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_export_hash": "",
            "execution_capsule_hash": "",
            "export_metadata_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "export_count": 0,
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "export_metadata_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_export_read_model_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "latest_execution_capsule_export_hash": "",
            "counts": {
                "execution_capsule_export_count": 0,
                "component_count": 0,
                "execution_permission_count": 0,
            },
        }
    )


def _manual_provider_test_execution_capsule_handoff_packet_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_handoff_packet_hash": "",
            "execution_capsule_export_hash": "",
            "execution_capsule_export_read_model_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "packet_count": 0,
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "export_read_model_count": 0,
            "handoff_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_operator_review_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_operator_review_hash": "",
            "execution_capsule_handoff_packet_hash": "",
            "operator_review_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "operator_review_count": 0,
            "review_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_operator_decision_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_operator_decision_hash": "",
            "execution_capsule_operator_review_hash": "",
            "operator_decision_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "operator_decision_count": 0,
            "decision_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_release_attestation_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_release_attestation_hash": "",
            "execution_capsule_operator_decision_hash": "",
            "release_attestation_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "release_attestation_count": 0,
            "attestation_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_release_seal_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_release_seal_hash": "",
            "execution_capsule_release_attestation_hash": "",
            "seal_material_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "seal_material_count": 0,
            "seal_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_final_authorization_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_final_authz_hash": "",
            "execution_capsule_release_seal_hash": "",
            "final_authz_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "final_authz_count": 0,
            "authz_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_export_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_export_hash": "",
            "execution_capsule_final_authz_hash": "",
            "export_metadata_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "export_count": 0,
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "export_metadata_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_export_read_model_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "latest_execution_capsule_authz_export_hash": "",
            "counts": {
                "execution_capsule_authz_export_count": 0,
                "component_count": 0,
                "execution_permission_count": 0,
            },
        }
    )


def _manual_provider_test_execution_capsule_authz_handoff_packet_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_handoff_packet_hash": "",
            "execution_capsule_authz_export_hash": "",
            "execution_capsule_authz_export_read_model_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "packet_count": 0,
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "export_read_model_count": 0,
            "handoff_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_operator_review_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_operator_review_hash": "",
            "execution_capsule_authz_handoff_packet_hash": "",
            "operator_review_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "operator_review_count": 0,
            "review_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_operator_decision_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_operator_decision_hash": "",
            "execution_capsule_authz_operator_review_hash": "",
            "operator_decision_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "operator_decision_count": 0,
            "decision_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_release_attestation_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_release_attestation_hash": "",
            "execution_capsule_authz_operator_decision_hash": "",
            "release_attestation_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "release_attestation_count": 0,
            "attestation_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_release_seal_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_release_seal_hash": "",
            "execution_capsule_authz_release_attestation_hash": "",
            "seal_material_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "seal_material_count": 0,
            "seal_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authorization_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_hash": "",
            "execution_capsule_authz_release_seal_hash": "",
            "final_authz_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "final_authz_count": 0,
            "authz_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_export_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_export_hash": "",
            "execution_capsule_authz_final_authz_hash": "",
            "export_metadata_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "export_count": 0,
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "export_metadata_count": 0,
            "export_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_export_read_model_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "latest_execution_capsule_authz_final_authz_export_hash": "",
            "counts": {
                "execution_capsule_authz_final_authz_export_count": 0,
                "component_count": 0,
                "execution_permission_count": 0,
            },
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_handoff_packet_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_handoff_packet_hash": "",
            "execution_capsule_authz_final_authz_export_hash": "",
            "execution_capsule_authz_final_authz_export_read_model_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "packet_count": 0,
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "export_read_model_count": 0,
            "handoff_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_operator_review_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_operator_review_hash": "",
            "execution_capsule_authz_final_authz_handoff_packet_hash": "",
            "operator_review_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "operator_review_count": 0,
            "review_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_operator_decision_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_operator_decision_hash": "",
            "execution_capsule_authz_final_authz_operator_review_hash": "",
            "operator_decision_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "operator_decision_count": 0,
            "decision_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_release_attestation_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_release_attestation_hash": "",
            "execution_capsule_authz_final_authz_operator_decision_hash": "",
            "release_attestation_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "release_attestation_count": 0,
            "attestation_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_release_seal_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_release_seal_hash": "",
            "execution_capsule_authz_final_authz_release_attestation_hash": "",
            "seal_material_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "seal_material_count": 0,
            "seal_request_count": 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_final_authorization_blocked(
    reason: str,
) -> JsonDict:
    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_final_authz_hash": "",
            "execution_capsule_authz_final_authz_release_seal_hash": "",
            "final_authz_hash": "",
            "claim_boundary_hash": "",
            "no_call_counters_hash": "",
            "component_count": 0,
            "passed_component_count": 0,
            "mismatch_count": 1,
            "component_hash_count": 0,
            "no_call_counter_count": 0,
            "claim_boundary_check_count": 0,
            "final_authz_count": 0,
            "authz_request_count": 0,
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


def _manual_provider_test_sealed_packet_projection(
    *,
    payload: dict[str, Any],
    operator_policy_summary: JsonDict,
    manual_provider_test_proposal: JsonDict,
    handoff_packet: JsonDict,
    operator_opt_in: JsonDict,
) -> JsonDict:
    handoff_hash = str(handoff_packet.get("handoff_packet_hash", "")).strip()
    operator_opt_in_hash = str(
        operator_opt_in.get("operator_opt_in_hash", "")
    ).strip()
    expected_operator_opt_in_hash = str(
        payload.get("expected_operator_opt_in_hash", "")
    ).strip()
    policy = (
        operator_policy_summary.get("policy")
        if isinstance(operator_policy_summary.get("policy"), dict)
        else {}
    )
    policy_counts = {
        "request_timeout_seconds": _coerce_int(policy.get("request_timeout_seconds", 0)),
        "max_cost_units": _coerce_int(policy.get("max_cost_units", 0)),
        "max_live_api_calls": _coerce_int(policy.get("max_live_api_calls", 0)),
        "max_output_unit_budget": _coerce_int(
            policy.get("max_output_unit_budget", 0)
        ),
    }
    cost_timeout_quota_ready = all(value > 0 for value in policy_counts.values())
    cost_timeout_quota_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_SEALED_PRE_EXECUTION_PACKET_VERSION,
                "policy": policy_counts,
            }
        )
        if cost_timeout_quota_ready
        else ""
    )
    proposal_fields = (
        manual_provider_test_proposal.get("proposal_fields")
        if isinstance(manual_provider_test_proposal.get("proposal_fields"), dict)
        else {}
    )
    rollback_plan_present = bool(proposal_fields.get("rollback_plan_present"))
    abort_criteria_hash = str(proposal_fields.get("abort_criteria_hash", "")).strip()
    abort_criteria_count = _coerce_int(
        proposal_fields.get("abort_criteria_count", 0)
    )
    rollback_abort_ready = (
        rollback_plan_present and bool(abort_criteria_hash) and abort_criteria_count > 0
    )
    rollback_abort_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_SEALED_PRE_EXECUTION_PACKET_VERSION,
                "rollback_plan_present": rollback_plan_present,
                "abort_criteria_hash": abort_criteria_hash,
                "abort_criteria_count": abort_criteria_count,
            }
        )
        if rollback_abort_ready
        else ""
    )
    execution_permission_count = _coerce_int(
        handoff_packet.get("execution_permission_count", 0)
    ) + _coerce_int(operator_opt_in.get("execution_permission_count", 0))
    component_checks = [
        str(handoff_packet.get("status", "")) == "blocked"
        and str(handoff_packet.get("reason", "")) == "handoff_packet_execution_closed"
        and bool(handoff_hash),
        str(operator_opt_in.get("status", "")) == "blocked"
        and str(operator_opt_in.get("reason", "")) == "operator_opt_in_execution_closed"
        and bool(operator_opt_in_hash),
        bool(expected_operator_opt_in_hash)
        and expected_operator_opt_in_hash == operator_opt_in_hash,
        bool(cost_timeout_quota_hash),
        bool(rollback_abort_hash),
        execution_permission_count == 0,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            handoff_hash,
            operator_opt_in_hash,
            cost_timeout_quota_hash,
            rollback_abort_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "handoff_packet_missing_or_mismatched"
    elif not component_checks[1]:
        reason = "operator_opt_in_missing_or_mismatched"
    elif not expected_operator_opt_in_hash:
        reason = "expected_operator_opt_in_hash_required"
    elif expected_operator_opt_in_hash != operator_opt_in_hash:
        reason = "operator_opt_in_hash_mismatch"
    elif not component_checks[3]:
        reason = "cost_timeout_quota_policy_missing"
    elif not component_checks[4]:
        reason = "rollback_abort_criteria_missing"
    elif not component_checks[5]:
        reason = "execution_permission_not_closed"
    else:
        reason = "sealed_pre_execution_packet_execution_closed"

    sealed_packet_hash = ""
    if mismatch_count == 0:
        sealed_packet_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_SEALED_PRE_EXECUTION_PACKET_VERSION,
                "handoff_packet_hash": handoff_hash,
                "operator_opt_in_hash": operator_opt_in_hash,
                "cost_timeout_quota_hash": cost_timeout_quota_hash,
                "rollback_abort_hash": rollback_abort_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "sealed_packet_hash": sealed_packet_hash,
            "handoff_packet_hash": handoff_hash,
            "operator_opt_in_hash": operator_opt_in_hash,
            "cost_timeout_quota_hash": cost_timeout_quota_hash,
            "rollback_abort_hash": rollback_abort_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_arming_record_projection(
    *,
    payload: dict[str, Any],
    sealed_pre_execution_packet: JsonDict,
) -> JsonDict:
    sealed_packet_hash = str(
        sealed_pre_execution_packet.get("sealed_packet_hash", "")
    ).strip()
    expected_sealed_packet_hash = str(
        payload.get("expected_sealed_packet_hash", "")
    ).strip()
    arming_payload = (
        payload.get("manual_test_live_execution_arming")
        if isinstance(payload.get("manual_test_live_execution_arming"), dict)
        else {}
    )
    supplied_sealed_packet_hash = str(
        arming_payload.get("sealed_packet_hash", "")
    ).strip()
    operator_ref = str(arming_payload.get("operator_ref", "")).strip()
    armed_at = str(arming_payload.get("armed_at", "")).strip()
    expires_at = str(arming_payload.get("expires_at", "")).strip()
    supplied_rollback_abort_hash = str(
        arming_payload.get("rollback_abort_hash", "")
    ).strip()
    supplied_abort_policy_hash = str(arming_payload.get("abort_policy_hash", "")).strip()
    sealed_rollback_abort_hash = str(
        sealed_pre_execution_packet.get("rollback_abort_hash", "")
    ).strip()
    operator_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_ARMING_RECORD_VERSION,
                "operator_ref": operator_ref,
                "armed_at": armed_at,
            }
        )
        if operator_ref and armed_at
        else ""
    )
    expiry_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_ARMING_RECORD_VERSION,
                "expires_at": expires_at,
            }
        )
        if expires_at
        else ""
    )
    component_checks = [
        str(sealed_pre_execution_packet.get("status", "")) == "blocked"
        and str(sealed_pre_execution_packet.get("reason", ""))
        == "sealed_pre_execution_packet_execution_closed"
        and bool(sealed_packet_hash),
        bool(expected_sealed_packet_hash)
        and expected_sealed_packet_hash == sealed_packet_hash,
        bool(arming_payload),
        bool(supplied_sealed_packet_hash)
        and supplied_sealed_packet_hash == sealed_packet_hash,
        bool(operator_hash),
        bool(expiry_hash),
        bool(supplied_rollback_abort_hash)
        and supplied_rollback_abort_hash == sealed_rollback_abort_hash,
        bool(supplied_abort_policy_hash),
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            sealed_packet_hash,
            operator_hash,
            expiry_hash,
            supplied_rollback_abort_hash,
            supplied_abort_policy_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "sealed_packet_missing_or_mismatched"
    elif not expected_sealed_packet_hash:
        reason = "expected_sealed_packet_hash_required"
    elif expected_sealed_packet_hash != sealed_packet_hash:
        reason = "sealed_packet_hash_mismatch"
    elif not component_checks[2]:
        reason = "arming_record_required"
    elif not component_checks[3]:
        reason = "arming_record_sealed_hash_mismatch"
    elif not component_checks[4]:
        reason = "arming_operator_required"
    elif not component_checks[5]:
        reason = "arming_expiry_required"
    elif not component_checks[6]:
        reason = "rollback_hash_mismatch"
    elif not component_checks[7]:
        reason = "abort_policy_hash_required"
    else:
        reason = "arming_record_execution_closed"

    arming_record_hash = ""
    if mismatch_count == 0:
        arming_record_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_ARMING_RECORD_VERSION,
                "sealed_packet_hash": sealed_packet_hash,
                "operator_hash": operator_hash,
                "expiry_hash": expiry_hash,
                "rollback_abort_hash": supplied_rollback_abort_hash,
                "abort_policy_hash": supplied_abort_policy_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "arming_record_hash": arming_record_hash,
            "sealed_packet_hash": sealed_packet_hash,
            "operator_hash": operator_hash,
            "expiry_hash": expiry_hash,
            "rollback_abort_hash": supplied_rollback_abort_hash,
            "abort_policy_hash": supplied_abort_policy_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_release_proposal_projection(
    *,
    payload: dict[str, Any],
    arming_record: JsonDict,
) -> JsonDict:
    arming_record_hash = str(arming_record.get("arming_record_hash", "")).strip()
    expected_arming_record_hash = str(
        payload.get("expected_arming_record_hash", "")
    ).strip()
    release_payload = (
        payload.get("manual_test_execution_release_proposal")
        if isinstance(payload.get("manual_test_execution_release_proposal"), dict)
        else {}
    )
    supplied_arming_record_hash = str(
        release_payload.get("arming_record_hash", "")
    ).strip()
    operator_ref = str(release_payload.get("operator_ref", "")).strip()
    proposed_at = str(release_payload.get("proposed_at", "")).strip()
    release_window_start = str(
        release_payload.get("release_window_start", "")
    ).strip()
    release_window_end = str(release_payload.get("release_window_end", "")).strip()
    supplied_rollback_abort_hash = str(
        release_payload.get("rollback_abort_hash", "")
    ).strip()
    arming_rollback_abort_hash = str(
        arming_record.get("rollback_abort_hash", "")
    ).strip()
    operator_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_RELEASE_PROPOSAL_VERSION,
                "operator_ref": operator_ref,
                "proposed_at": proposed_at,
            }
        )
        if operator_ref and proposed_at
        else ""
    )
    release_window_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_RELEASE_PROPOSAL_VERSION,
                "release_window_start": release_window_start,
                "release_window_end": release_window_end,
            }
        )
        if release_window_start and release_window_end
        else ""
    )
    component_checks = [
        str(arming_record.get("status", "")) == "blocked"
        and str(arming_record.get("reason", "")) == "arming_record_execution_closed"
        and bool(arming_record_hash),
        bool(expected_arming_record_hash)
        and expected_arming_record_hash == arming_record_hash,
        bool(release_payload),
        bool(supplied_arming_record_hash)
        and supplied_arming_record_hash == arming_record_hash,
        bool(operator_hash),
        bool(release_window_hash),
        bool(supplied_rollback_abort_hash)
        and supplied_rollback_abort_hash == arming_rollback_abort_hash,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            arming_record_hash,
            operator_hash,
            release_window_hash,
            supplied_rollback_abort_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "arming_record_missing_or_mismatched"
    elif not expected_arming_record_hash:
        reason = "expected_arming_record_hash_required"
    elif expected_arming_record_hash != arming_record_hash:
        reason = "arming_record_hash_mismatch"
    elif not component_checks[2]:
        reason = "release_proposal_required"
    elif not component_checks[3]:
        reason = "release_proposal_arming_hash_mismatch"
    elif not component_checks[4]:
        reason = "release_operator_required"
    elif not component_checks[5]:
        reason = "release_window_required"
    elif not component_checks[6]:
        reason = "rollback_hash_mismatch"
    else:
        reason = "release_proposal_execution_closed"

    release_proposal_hash = ""
    if mismatch_count == 0:
        release_proposal_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_RELEASE_PROPOSAL_VERSION,
                "arming_record_hash": arming_record_hash,
                "operator_hash": operator_hash,
                "release_window_hash": release_window_hash,
                "rollback_abort_hash": supplied_rollback_abort_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "release_proposal_hash": release_proposal_hash,
            "arming_record_hash": arming_record_hash,
            "operator_hash": operator_hash,
            "release_window_hash": release_window_hash,
            "rollback_abort_hash": supplied_rollback_abort_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_final_release_packet_projection(
    *,
    payload: dict[str, Any],
    release_proposal: JsonDict,
) -> JsonDict:
    release_proposal_hash = str(
        release_proposal.get("release_proposal_hash", "")
    ).strip()
    expected_release_proposal_hash = str(
        payload.get("expected_release_proposal_hash", "")
    ).strip()
    packet_payload = (
        payload.get("manual_test_final_release_packet")
        if isinstance(payload.get("manual_test_final_release_packet"), dict)
        else {}
    )
    supplied_release_proposal_hash = str(
        packet_payload.get("release_proposal_hash", "")
    ).strip()
    arming_record_hash = str(release_proposal.get("arming_record_hash", "")).strip()
    operator_hash = str(release_proposal.get("operator_hash", "")).strip()
    release_window_hash = str(
        release_proposal.get("release_window_hash", "")
    ).strip()
    rollback_abort_hash = str(release_proposal.get("rollback_abort_hash", "")).strip()
    component_checks = [
        str(release_proposal.get("status", "")) == "blocked"
        and str(release_proposal.get("reason", ""))
        == "release_proposal_execution_closed"
        and bool(release_proposal_hash),
        bool(expected_release_proposal_hash)
        and expected_release_proposal_hash == release_proposal_hash,
        bool(packet_payload),
        bool(supplied_release_proposal_hash)
        and supplied_release_proposal_hash == release_proposal_hash,
        bool(arming_record_hash),
        bool(operator_hash),
        bool(release_window_hash),
        bool(rollback_abort_hash),
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            release_proposal_hash,
            arming_record_hash,
            operator_hash,
            release_window_hash,
            rollback_abort_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "release_proposal_missing_or_mismatched"
    elif not expected_release_proposal_hash:
        reason = "expected_release_proposal_hash_required"
    elif expected_release_proposal_hash != release_proposal_hash:
        reason = "release_proposal_hash_mismatch"
    elif not component_checks[2]:
        reason = "final_release_packet_required"
    elif not component_checks[3]:
        reason = "final_release_packet_proposal_hash_mismatch"
    elif not component_checks[4]:
        reason = "arming_record_hash_required"
    elif not component_checks[5]:
        reason = "release_operator_hash_required"
    elif not component_checks[6]:
        reason = "release_window_hash_required"
    elif not component_checks[7]:
        reason = "rollback_hash_required"
    else:
        reason = "final_release_packet_execution_closed"

    final_release_packet_hash = ""
    if mismatch_count == 0:
        final_release_packet_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_FINAL_RELEASE_PACKET_VERSION,
                "release_proposal_hash": release_proposal_hash,
                "arming_record_hash": arming_record_hash,
                "operator_hash": operator_hash,
                "release_window_hash": release_window_hash,
                "rollback_abort_hash": rollback_abort_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "final_release_packet_hash": final_release_packet_hash,
            "release_proposal_hash": release_proposal_hash,
            "arming_record_hash": arming_record_hash,
            "operator_hash": operator_hash,
            "release_window_hash": release_window_hash,
            "rollback_abort_hash": rollback_abort_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_switch_projection(
    *,
    payload: dict[str, Any],
    final_release_packet: JsonDict,
) -> JsonDict:
    final_release_packet_hash = str(
        final_release_packet.get("final_release_packet_hash", "")
    ).strip()
    expected_final_release_packet_hash = str(
        payload.get("expected_final_release_packet_hash", "")
    ).strip()
    switch_payload = (
        payload.get("manual_test_execution_switch")
        if isinstance(payload.get("manual_test_execution_switch"), dict)
        else {}
    )
    supplied_final_release_packet_hash = str(
        switch_payload.get("final_release_packet_hash", "")
    ).strip()
    switch_enable_requested = switch_payload.get("enable_requested") is True
    switch_enable_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_EXECUTION_SWITCH_VERSION,
                "enable_requested": True,
            }
        )
        if switch_enable_requested
        else ""
    )
    component_checks = [
        str(final_release_packet.get("status", "")) == "blocked"
        and str(final_release_packet.get("reason", ""))
        == "final_release_packet_execution_closed"
        and bool(final_release_packet_hash),
        bool(expected_final_release_packet_hash)
        and expected_final_release_packet_hash == final_release_packet_hash,
        bool(switch_payload),
        bool(supplied_final_release_packet_hash)
        and supplied_final_release_packet_hash == final_release_packet_hash,
        switch_enable_requested,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            final_release_packet_hash,
            switch_enable_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "final_release_packet_missing_or_mismatched"
    elif not expected_final_release_packet_hash:
        reason = "expected_final_release_packet_hash_required"
    elif expected_final_release_packet_hash != final_release_packet_hash:
        reason = "final_release_packet_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_switch_required"
    elif not component_checks[3]:
        reason = "execution_switch_final_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_switch_enable_required"
    else:
        reason = "execution_switch_disabled_by_default"

    execution_switch_hash = ""
    if mismatch_count == 0:
        execution_switch_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_EXECUTION_SWITCH_VERSION,
                "final_release_packet_hash": final_release_packet_hash,
                "switch_enable_hash": switch_enable_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_switch_hash": execution_switch_hash,
            "final_release_packet_hash": final_release_packet_hash,
            "switch_enable_hash": switch_enable_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "enable_request_count": 1 if switch_enable_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _executor_preflight_no_call_counters(execution_boundary: JsonDict) -> JsonDict:
    return {
        field_name: _coerce_int(execution_boundary.get(field_name, 0))
        for field_name in EXECUTOR_PREFLIGHT_NO_CALL_COUNTER_FIELDS
    }


def _manual_provider_test_executor_preflight_projection(
    *,
    payload: dict[str, Any],
    execution_switch: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    execution_switch_hash = str(
        execution_switch.get("execution_switch_hash", "")
    ).strip()
    final_release_packet_hash = str(
        execution_switch.get("final_release_packet_hash", "")
    ).strip()
    expected_execution_switch_hash = str(
        payload.get("expected_execution_switch_hash", "")
    ).strip()
    preflight_payload = (
        payload.get("manual_test_executor_preflight")
        if isinstance(payload.get("manual_test_executor_preflight"), dict)
        else {}
    )
    supplied_execution_switch_hash = str(
        preflight_payload.get("execution_switch_hash", "")
    ).strip()
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_EXECUTOR_PREFLIGHT_VERSION,
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_switch.get("status", "")) == "blocked"
        and str(execution_switch.get("reason", ""))
        == "execution_switch_disabled_by_default"
        and bool(execution_switch_hash),
        bool(expected_execution_switch_hash)
        and expected_execution_switch_hash == execution_switch_hash,
        bool(preflight_payload),
        bool(supplied_execution_switch_hash)
        and supplied_execution_switch_hash == execution_switch_hash,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            final_release_packet_hash,
            execution_switch_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_switch_missing_or_mismatched"
    elif not expected_execution_switch_hash:
        reason = "expected_execution_switch_hash_required"
    elif expected_execution_switch_hash != execution_switch_hash:
        reason = "execution_switch_hash_mismatch"
    elif not component_checks[2]:
        reason = "executor_preflight_required"
    elif not component_checks[3]:
        reason = "executor_preflight_switch_hash_mismatch"
    elif not component_checks[4]:
        reason = "executor_preflight_no_call_counters_mismatch"
    else:
        reason = "executor_preflight_execution_closed"

    executor_preflight_hash = ""
    if mismatch_count == 0:
        executor_preflight_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_EXECUTOR_PREFLIGHT_VERSION,
                "final_release_packet_hash": final_release_packet_hash,
                "execution_switch_hash": execution_switch_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "executor_preflight_hash": executor_preflight_hash,
            "execution_switch_hash": execution_switch_hash,
            "final_release_packet_hash": final_release_packet_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_executor_dispatch_record_projection(
    *,
    payload: dict[str, Any],
    executor_preflight: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    executor_preflight_hash = str(
        executor_preflight.get("executor_preflight_hash", "")
    ).strip()
    expected_executor_preflight_hash = str(
        payload.get("expected_executor_preflight_hash", "")
    ).strip()
    dispatch_payload = (
        payload.get("manual_test_executor_dispatch_record")
        if isinstance(payload.get("manual_test_executor_dispatch_record"), dict)
        else {}
    )
    supplied_executor_preflight_hash = str(
        dispatch_payload.get("executor_preflight_hash", "")
    ).strip()
    dispatch_requested = dispatch_payload.get("dispatch_requested") is True
    planned_dispatch_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_EXECUTOR_DISPATCH_VERSION,
                "executor_preflight_hash": executor_preflight_hash,
                "dispatch_kind": "disabled_first_call_provider_executor",
                "dispatch_request": "local_no_call",
            }
        )
        if dispatch_requested and executor_preflight_hash
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_EXECUTOR_DISPATCH_VERSION,
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(executor_preflight.get("status", "")) == "blocked"
        and str(executor_preflight.get("reason", ""))
        == "executor_preflight_execution_closed"
        and bool(executor_preflight_hash),
        bool(expected_executor_preflight_hash)
        and expected_executor_preflight_hash == executor_preflight_hash,
        bool(dispatch_payload),
        bool(supplied_executor_preflight_hash)
        and supplied_executor_preflight_hash == executor_preflight_hash,
        dispatch_requested,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            executor_preflight_hash,
            planned_dispatch_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "executor_preflight_missing_or_mismatched"
    elif not expected_executor_preflight_hash:
        reason = "expected_executor_preflight_hash_required"
    elif expected_executor_preflight_hash != executor_preflight_hash:
        reason = "executor_preflight_hash_mismatch"
    elif not component_checks[2]:
        reason = "executor_dispatch_record_required"
    elif not component_checks[3]:
        reason = "executor_dispatch_preflight_hash_mismatch"
    elif not component_checks[4]:
        reason = "executor_dispatch_planned_dispatch_required"
    elif not component_checks[5]:
        reason = "executor_dispatch_no_call_counters_mismatch"
    else:
        reason = "executor_dispatch_record_execution_closed"

    dispatch_record_hash = ""
    if mismatch_count == 0:
        dispatch_record_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_EXECUTOR_DISPATCH_VERSION,
                "executor_preflight_hash": executor_preflight_hash,
                "planned_dispatch_hash": planned_dispatch_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "dispatch_record_hash": dispatch_record_hash,
            "executor_preflight_hash": executor_preflight_hash,
            "planned_dispatch_hash": planned_dispatch_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "dispatch_request_count": 1 if dispatch_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_invocation_receipt_projection(
    *,
    payload: dict[str, Any],
    dispatch_record: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    dispatch_record_hash = str(
        dispatch_record.get("dispatch_record_hash", "")
    ).strip()
    expected_dispatch_record_hash = str(
        payload.get("expected_dispatch_record_hash", "")
    ).strip()
    receipt_payload = (
        payload.get("manual_test_executor_invocation_receipt")
        if isinstance(payload.get("manual_test_executor_invocation_receipt"), dict)
        else {}
    )
    supplied_dispatch_record_hash = str(
        receipt_payload.get("dispatch_record_hash", "")
    ).strip()
    receipt_requested = receipt_payload.get("receipt_requested") is True
    result_placeholder_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_INVOCATION_RECEIPT_VERSION,
                "dispatch_record_hash": dispatch_record_hash,
                "provider_result": "not_invoked",
                "target_runtime_result": "not_invoked",
            }
        )
        if receipt_requested and dispatch_record_hash
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_INVOCATION_RECEIPT_VERSION,
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(dispatch_record.get("status", "")) == "blocked"
        and str(dispatch_record.get("reason", ""))
        == "executor_dispatch_record_execution_closed"
        and bool(dispatch_record_hash),
        bool(expected_dispatch_record_hash)
        and expected_dispatch_record_hash == dispatch_record_hash,
        bool(receipt_payload),
        bool(supplied_dispatch_record_hash)
        and supplied_dispatch_record_hash == dispatch_record_hash,
        receipt_requested,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            dispatch_record_hash,
            result_placeholder_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "dispatch_record_missing_or_mismatched"
    elif not expected_dispatch_record_hash:
        reason = "expected_dispatch_record_hash_required"
    elif expected_dispatch_record_hash != dispatch_record_hash:
        reason = "dispatch_record_hash_mismatch"
    elif not component_checks[2]:
        reason = "invocation_receipt_required"
    elif not component_checks[3]:
        reason = "invocation_receipt_dispatch_hash_mismatch"
    elif not component_checks[4]:
        reason = "invocation_receipt_result_placeholder_required"
    elif not component_checks[5]:
        reason = "invocation_receipt_no_call_counters_mismatch"
    else:
        reason = "invocation_receipt_execution_closed"

    invocation_receipt_hash = ""
    if mismatch_count == 0:
        invocation_receipt_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_INVOCATION_RECEIPT_VERSION,
                "dispatch_record_hash": dispatch_record_hash,
                "result_placeholder_hash": result_placeholder_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "invocation_receipt_hash": invocation_receipt_hash,
            "dispatch_record_hash": dispatch_record_hash,
            "result_placeholder_hash": result_placeholder_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "receipt_request_count": 1 if receipt_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _provider_envelope_claim_boundary_projection() -> JsonDict:
    return {
        "scope": "local provider envelope precheck only",
        "external_provider_outcome": False,
        "target_runtime_outcome": False,
        "production_trust_claim": False,
    }


def _manual_provider_test_post_invocation_audit_projection(
    *,
    payload: dict[str, Any],
    invocation_receipt: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    invocation_receipt_hash = str(
        invocation_receipt.get("invocation_receipt_hash", "")
    ).strip()
    expected_invocation_receipt_hash = str(
        payload.get("expected_invocation_receipt_hash", "")
    ).strip()
    audit_payload = (
        payload.get("manual_test_post_invocation_audit")
        if isinstance(payload.get("manual_test_post_invocation_audit"), dict)
        else {}
    )
    supplied_invocation_receipt_hash = str(
        audit_payload.get("invocation_receipt_hash", "")
    ).strip()
    audit_requested = audit_payload.get("audit_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_POST_INVOCATION_AUDIT_VERSION,
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_POST_INVOCATION_AUDIT_VERSION,
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(invocation_receipt.get("status", "")) == "blocked"
        and str(invocation_receipt.get("reason", ""))
        == "invocation_receipt_execution_closed"
        and bool(invocation_receipt_hash),
        bool(expected_invocation_receipt_hash)
        and expected_invocation_receipt_hash == invocation_receipt_hash,
        bool(audit_payload),
        bool(supplied_invocation_receipt_hash)
        and supplied_invocation_receipt_hash == invocation_receipt_hash,
        audit_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            invocation_receipt_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "invocation_receipt_missing_or_mismatched"
    elif not expected_invocation_receipt_hash:
        reason = "expected_invocation_receipt_hash_required"
    elif expected_invocation_receipt_hash != invocation_receipt_hash:
        reason = "invocation_receipt_hash_mismatch"
    elif not component_checks[2]:
        reason = "post_invocation_audit_required"
    elif not component_checks[3]:
        reason = "post_invocation_audit_receipt_hash_mismatch"
    elif not component_checks[4]:
        reason = "post_invocation_audit_request_required"
    elif not component_checks[5]:
        reason = "post_invocation_audit_claim_boundary_mismatch"
    elif not component_checks[6]:
        reason = "post_invocation_audit_no_call_counters_mismatch"
    else:
        reason = "post_invocation_audit_execution_closed"

    post_invocation_audit_hash = ""
    if mismatch_count == 0:
        post_invocation_audit_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_POST_INVOCATION_AUDIT_VERSION,
                "invocation_receipt_hash": invocation_receipt_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "post_invocation_audit_hash": post_invocation_audit_hash,
            "invocation_receipt_hash": invocation_receipt_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "audit_request_count": 1 if audit_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_completion_summary_projection(
    *,
    payload: dict[str, Any],
    post_invocation_audit: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    post_invocation_audit_hash = str(
        post_invocation_audit.get("post_invocation_audit_hash", "")
    ).strip()
    expected_post_invocation_audit_hash = str(
        payload.get("expected_post_invocation_audit_hash", "")
    ).strip()
    completion_payload = (
        payload.get("manual_test_completion_summary")
        if isinstance(payload.get("manual_test_completion_summary"), dict)
        else {}
    )
    supplied_post_invocation_audit_hash = str(
        completion_payload.get("post_invocation_audit_hash", "")
    ).strip()
    summary_requested = completion_payload.get("summary_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_COMPLETION_SUMMARY_VERSION,
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_COMPLETION_SUMMARY_VERSION,
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(post_invocation_audit.get("status", "")) == "blocked"
        and str(post_invocation_audit.get("reason", ""))
        == "post_invocation_audit_execution_closed"
        and bool(post_invocation_audit_hash),
        bool(expected_post_invocation_audit_hash)
        and expected_post_invocation_audit_hash == post_invocation_audit_hash,
        bool(completion_payload),
        bool(supplied_post_invocation_audit_hash)
        and supplied_post_invocation_audit_hash == post_invocation_audit_hash,
        summary_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            post_invocation_audit_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "post_invocation_audit_missing_or_mismatched"
    elif not expected_post_invocation_audit_hash:
        reason = "expected_post_invocation_audit_hash_required"
    elif expected_post_invocation_audit_hash != post_invocation_audit_hash:
        reason = "post_invocation_audit_hash_mismatch"
    elif not component_checks[2]:
        reason = "completion_summary_required"
    elif not component_checks[3]:
        reason = "completion_summary_audit_hash_mismatch"
    elif not component_checks[4]:
        reason = "completion_summary_request_required"
    elif not component_checks[5]:
        reason = "completion_summary_claim_boundary_mismatch"
    elif not component_checks[6]:
        reason = "completion_summary_no_call_counters_mismatch"
    else:
        reason = "completion_summary_execution_closed"

    completion_summary_hash = ""
    if mismatch_count == 0:
        completion_summary_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_COMPLETION_SUMMARY_VERSION,
                "post_invocation_audit_hash": post_invocation_audit_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "completion_summary_hash": completion_summary_hash,
            "post_invocation_audit_hash": post_invocation_audit_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "summary_request_count": 1 if summary_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_closeout_record_projection(
    *,
    payload: dict[str, Any],
    completion_summary: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    completion_summary_hash = str(
        completion_summary.get("completion_summary_hash", "")
    ).strip()
    expected_completion_summary_hash = str(
        payload.get("expected_completion_summary_hash", "")
    ).strip()
    closeout_payload = (
        payload.get("manual_test_closeout_record")
        if isinstance(payload.get("manual_test_closeout_record"), dict)
        else {}
    )
    supplied_completion_summary_hash = str(
        closeout_payload.get("completion_summary_hash", "")
    ).strip()
    closeout_requested = closeout_payload.get("closeout_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_CLOSEOUT_RECORD_VERSION,
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_CLOSEOUT_RECORD_VERSION,
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(completion_summary.get("status", "")) == "blocked"
        and str(completion_summary.get("reason", ""))
        == "completion_summary_execution_closed"
        and bool(completion_summary_hash),
        bool(expected_completion_summary_hash)
        and expected_completion_summary_hash == completion_summary_hash,
        bool(closeout_payload),
        bool(supplied_completion_summary_hash)
        and supplied_completion_summary_hash == completion_summary_hash,
        closeout_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            completion_summary_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "completion_summary_missing_or_mismatched"
    elif not expected_completion_summary_hash:
        reason = "expected_completion_summary_hash_required"
    elif expected_completion_summary_hash != completion_summary_hash:
        reason = "completion_summary_hash_mismatch"
    elif not component_checks[2]:
        reason = "closeout_record_required"
    elif not component_checks[3]:
        reason = "closeout_record_summary_hash_mismatch"
    elif not component_checks[4]:
        reason = "closeout_record_request_required"
    elif not component_checks[5]:
        reason = "closeout_record_claim_boundary_mismatch"
    elif not component_checks[6]:
        reason = "closeout_record_no_call_counters_mismatch"
    else:
        reason = "closeout_record_execution_closed"

    closeout_record_hash = ""
    if mismatch_count == 0:
        closeout_record_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_CLOSEOUT_RECORD_VERSION,
                "completion_summary_hash": completion_summary_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "closeout_record_hash": closeout_record_hash,
            "completion_summary_hash": completion_summary_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "closeout_request_count": 1 if closeout_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_operator_handback_projection(
    *,
    payload: dict[str, Any],
    closeout_record: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    closeout_record_hash = str(
        closeout_record.get("closeout_record_hash", "")
    ).strip()
    expected_closeout_record_hash = str(
        payload.get("expected_closeout_record_hash", "")
    ).strip()
    handback_payload = (
        payload.get("manual_test_operator_handback")
        if isinstance(payload.get("manual_test_operator_handback"), dict)
        else {}
    )
    supplied_closeout_record_hash = str(
        handback_payload.get("closeout_record_hash", "")
    ).strip()
    operator_review = (
        handback_payload.get("operator_review")
        if isinstance(handback_payload.get("operator_review"), dict)
        else {}
    )
    operator_review_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_OPERATOR_HANDBACK_VERSION,
                "review_decision": str(
                    operator_review.get("review_decision", "")
                ).strip(),
                "review_reason_code": str(
                    operator_review.get("review_reason_code", "")
                ).strip(),
                "reviewed_at": str(operator_review.get("reviewed_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            operator_review.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(operator_review.get("operator_ref", "")).strip()
                else "",
            }
        )
        if operator_review
        else ""
    )
    handback_requested = handback_payload.get("handback_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_OPERATOR_HANDBACK_VERSION,
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_OPERATOR_HANDBACK_VERSION,
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(closeout_record.get("status", "")) == "blocked"
        and str(closeout_record.get("reason", ""))
        == "closeout_record_execution_closed"
        and bool(closeout_record_hash),
        bool(expected_closeout_record_hash)
        and expected_closeout_record_hash == closeout_record_hash,
        bool(handback_payload),
        bool(supplied_closeout_record_hash)
        and supplied_closeout_record_hash == closeout_record_hash,
        bool(operator_review_hash),
        handback_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            closeout_record_hash,
            operator_review_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "closeout_record_missing_or_mismatched"
    elif not expected_closeout_record_hash:
        reason = "expected_closeout_record_hash_required"
    elif expected_closeout_record_hash != closeout_record_hash:
        reason = "closeout_record_hash_mismatch"
    elif not component_checks[2]:
        reason = "operator_handback_required"
    elif not component_checks[3]:
        reason = "operator_handback_closeout_hash_mismatch"
    elif not component_checks[4]:
        reason = "operator_handback_review_required"
    elif not component_checks[5]:
        reason = "operator_handback_request_required"
    elif not component_checks[6]:
        reason = "operator_handback_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "operator_handback_no_call_counters_mismatch"
    else:
        reason = "operator_handback_execution_closed"

    operator_handback_hash = ""
    if mismatch_count == 0:
        operator_handback_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_OPERATOR_HANDBACK_VERSION,
                "closeout_record_hash": closeout_record_hash,
                "operator_review_hash": operator_review_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "operator_handback_hash": operator_handback_hash,
            "closeout_record_hash": closeout_record_hash,
            "operator_review_hash": operator_review_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "operator_review_count": 1 if operator_review_hash else 0,
            "handback_request_count": 1 if handback_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_operator_decision_packet_projection(
    *,
    payload: dict[str, Any],
    operator_handback: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    operator_handback_hash = str(
        operator_handback.get("operator_handback_hash", "")
    ).strip()
    expected_operator_handback_hash = str(
        payload.get("expected_operator_handback_hash", "")
    ).strip()
    packet_payload = (
        payload.get("manual_test_operator_decision_packet")
        if isinstance(payload.get("manual_test_operator_decision_packet"), dict)
        else {}
    )
    supplied_operator_handback_hash = str(
        packet_payload.get("operator_handback_hash", "")
    ).strip()
    operator_decision = (
        packet_payload.get("operator_decision")
        if isinstance(packet_payload.get("operator_decision"), dict)
        else {}
    )
    operator_decision_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_OPERATOR_DECISION_PACKET_VERSION
                ),
                "decision": str(operator_decision.get("decision", "")).strip(),
                "decision_reason_code": str(
                    operator_decision.get("decision_reason_code", "")
                ).strip(),
                "decided_at": str(operator_decision.get("decided_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            operator_decision.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(operator_decision.get("operator_ref", "")).strip()
                else "",
            }
        )
        if operator_decision
        else ""
    )
    packet_requested = packet_payload.get("packet_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_OPERATOR_DECISION_PACKET_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_OPERATOR_DECISION_PACKET_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(operator_handback.get("status", "")) == "blocked"
        and str(operator_handback.get("reason", ""))
        == "operator_handback_execution_closed"
        and bool(operator_handback_hash),
        bool(expected_operator_handback_hash)
        and expected_operator_handback_hash == operator_handback_hash,
        bool(packet_payload),
        bool(supplied_operator_handback_hash)
        and supplied_operator_handback_hash == operator_handback_hash,
        bool(operator_decision_hash),
        packet_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            operator_handback_hash,
            operator_decision_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "operator_handback_missing_or_mismatched"
    elif not expected_operator_handback_hash:
        reason = "expected_operator_handback_hash_required"
    elif expected_operator_handback_hash != operator_handback_hash:
        reason = "operator_handback_hash_mismatch"
    elif not component_checks[2]:
        reason = "operator_decision_packet_required"
    elif not component_checks[3]:
        reason = "operator_decision_packet_handback_hash_mismatch"
    elif not component_checks[4]:
        reason = "operator_decision_required"
    elif not component_checks[5]:
        reason = "operator_decision_packet_request_required"
    elif not component_checks[6]:
        reason = "operator_decision_packet_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "operator_decision_packet_no_call_counters_mismatch"
    else:
        reason = "operator_decision_packet_execution_closed"

    operator_decision_packet_hash = ""
    if mismatch_count == 0:
        operator_decision_packet_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_OPERATOR_DECISION_PACKET_VERSION
                ),
                "operator_handback_hash": operator_handback_hash,
                "operator_decision_hash": operator_decision_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "operator_decision_packet_hash": operator_decision_packet_hash,
            "operator_handback_hash": operator_handback_hash,
            "operator_decision_hash": operator_decision_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "operator_decision_count": 1 if operator_decision_hash else 0,
            "decision_packet_request_count": 1 if packet_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_operator_release_attestation_projection(
    *,
    payload: dict[str, Any],
    operator_decision_packet: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    operator_decision_packet_hash = str(
        operator_decision_packet.get("operator_decision_packet_hash", "")
    ).strip()
    expected_operator_decision_packet_hash = str(
        payload.get("expected_operator_decision_packet_hash", "")
    ).strip()
    attestation_payload = (
        payload.get("manual_test_operator_release_attestation")
        if isinstance(payload.get("manual_test_operator_release_attestation"), dict)
        else {}
    )
    supplied_operator_decision_packet_hash = str(
        attestation_payload.get("operator_decision_packet_hash", "")
    ).strip()
    operator_attestation = (
        attestation_payload.get("operator_attestation")
        if isinstance(attestation_payload.get("operator_attestation"), dict)
        else {}
    )
    operator_attestation_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_OPERATOR_RELEASE_ATTESTATION_VERSION
                ),
                "attestation": str(
                    operator_attestation.get("attestation", "")
                ).strip(),
                "attestation_reason_code": str(
                    operator_attestation.get("attestation_reason_code", "")
                ).strip(),
                "attested_at": str(
                    operator_attestation.get("attested_at", "")
                ).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            operator_attestation.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(operator_attestation.get("operator_ref", "")).strip()
                else "",
            }
        )
        if operator_attestation
        else ""
    )
    attestation_requested = attestation_payload.get("attestation_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_OPERATOR_RELEASE_ATTESTATION_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_OPERATOR_RELEASE_ATTESTATION_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(operator_decision_packet.get("status", "")) == "blocked"
        and str(operator_decision_packet.get("reason", ""))
        == "operator_decision_packet_execution_closed"
        and bool(operator_decision_packet_hash),
        bool(expected_operator_decision_packet_hash)
        and expected_operator_decision_packet_hash == operator_decision_packet_hash,
        bool(attestation_payload),
        bool(supplied_operator_decision_packet_hash)
        and supplied_operator_decision_packet_hash == operator_decision_packet_hash,
        bool(operator_attestation_hash),
        attestation_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            operator_decision_packet_hash,
            operator_attestation_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "operator_decision_packet_missing_or_mismatched"
    elif not expected_operator_decision_packet_hash:
        reason = "expected_operator_decision_packet_hash_required"
    elif expected_operator_decision_packet_hash != operator_decision_packet_hash:
        reason = "operator_decision_packet_hash_mismatch"
    elif not component_checks[2]:
        reason = "operator_release_attestation_required"
    elif not component_checks[3]:
        reason = "operator_release_attestation_decision_packet_hash_mismatch"
    elif not component_checks[4]:
        reason = "operator_attestation_required"
    elif not component_checks[5]:
        reason = "operator_release_attestation_request_required"
    elif not component_checks[6]:
        reason = "operator_release_attestation_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "operator_release_attestation_no_call_counters_mismatch"
    else:
        reason = "operator_release_attestation_execution_closed"

    operator_release_attestation_hash = ""
    if mismatch_count == 0:
        operator_release_attestation_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_OPERATOR_RELEASE_ATTESTATION_VERSION
                ),
                "operator_decision_packet_hash": operator_decision_packet_hash,
                "operator_attestation_hash": operator_attestation_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "operator_release_attestation_hash": operator_release_attestation_hash,
            "operator_decision_packet_hash": operator_decision_packet_hash,
            "operator_attestation_hash": operator_attestation_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "operator_attestation_count": 1 if operator_attestation_hash else 0,
            "attestation_request_count": 1 if attestation_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_release_authorization_seal_projection(
    *,
    payload: dict[str, Any],
    operator_release_attestation: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    operator_release_attestation_hash = str(
        operator_release_attestation.get("operator_release_attestation_hash", "")
    ).strip()
    expected_operator_release_attestation_hash = str(
        payload.get("expected_operator_release_attestation_hash", "")
    ).strip()
    seal_payload = (
        payload.get("manual_test_release_authorization_seal")
        if isinstance(payload.get("manual_test_release_authorization_seal"), dict)
        else {}
    )
    supplied_operator_release_attestation_hash = str(
        seal_payload.get("operator_release_attestation_hash", "")
    ).strip()
    seal_material = (
        seal_payload.get("seal_material")
        if isinstance(seal_payload.get("seal_material"), dict)
        else {}
    )
    seal_material_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_RELEASE_AUTHORIZATION_SEAL_VERSION
                ),
                "seal_decision": str(
                    seal_material.get("seal_decision", "")
                ).strip(),
                "seal_reason_code": str(
                    seal_material.get("seal_reason_code", "")
                ).strip(),
                "sealed_at": str(seal_material.get("sealed_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            seal_material.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(seal_material.get("operator_ref", "")).strip()
                else "",
            }
        )
        if seal_material
        else ""
    )
    seal_requested = seal_payload.get("seal_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_RELEASE_AUTHORIZATION_SEAL_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_RELEASE_AUTHORIZATION_SEAL_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(operator_release_attestation.get("status", "")) == "blocked"
        and str(operator_release_attestation.get("reason", ""))
        == "operator_release_attestation_execution_closed"
        and bool(operator_release_attestation_hash),
        bool(expected_operator_release_attestation_hash)
        and expected_operator_release_attestation_hash
        == operator_release_attestation_hash,
        bool(seal_payload),
        bool(supplied_operator_release_attestation_hash)
        and supplied_operator_release_attestation_hash
        == operator_release_attestation_hash,
        bool(seal_material_hash),
        seal_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            operator_release_attestation_hash,
            seal_material_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "operator_release_attestation_missing_or_mismatched"
    elif not expected_operator_release_attestation_hash:
        reason = "expected_operator_release_attestation_hash_required"
    elif (
        expected_operator_release_attestation_hash
        != operator_release_attestation_hash
    ):
        reason = "operator_release_attestation_hash_mismatch"
    elif not component_checks[2]:
        reason = "release_authorization_seal_required"
    elif not component_checks[3]:
        reason = "release_authorization_seal_attestation_hash_mismatch"
    elif not component_checks[4]:
        reason = "seal_material_required"
    elif not component_checks[5]:
        reason = "release_authorization_seal_request_required"
    elif not component_checks[6]:
        reason = "release_authorization_seal_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "release_authorization_seal_no_call_counters_mismatch"
    else:
        reason = "release_authorization_seal_execution_closed"

    release_authorization_seal_hash = ""
    if mismatch_count == 0:
        release_authorization_seal_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_RELEASE_AUTHORIZATION_SEAL_VERSION
                ),
                "operator_release_attestation_hash": (
                    operator_release_attestation_hash
                ),
                "seal_material_hash": seal_material_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "release_seal_hash": release_authorization_seal_hash,
            "operator_release_attestation_hash": operator_release_attestation_hash,
            "seal_material_hash": seal_material_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "seal_material_count": 1 if seal_material_hash else 0,
            "seal_request_count": 1 if seal_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_authorization_capsule_projection(
    *,
    payload: dict[str, Any],
    release_seal: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    release_seal_hash = str(release_seal.get("release_seal_hash", "")).strip()
    expected_release_seal_hash = str(
        payload.get("expected_release_seal_hash", "")
    ).strip()
    capsule_payload = (
        payload.get("manual_test_execution_authorization_capsule")
        if isinstance(payload.get("manual_test_execution_authorization_capsule"), dict)
        else {}
    )
    supplied_release_seal_hash = str(
        capsule_payload.get("release_seal_hash", "")
    ).strip()
    final_authorization = (
        capsule_payload.get("final_authorization")
        if isinstance(capsule_payload.get("final_authorization"), dict)
        else {}
    )
    final_authz_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_AUTHORIZATION_CAPSULE_VERSION
                ),
                "decision": str(final_authorization.get("decision", "")).strip(),
                "reason_code": str(
                    final_authorization.get("reason_code", "")
                ).strip(),
                "authorized_at": str(
                    final_authorization.get("authorized_at", "")
                ).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            final_authorization.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(final_authorization.get("operator_ref", "")).strip()
                else "",
            }
        )
        if final_authorization
        else ""
    )
    capsule_requested = capsule_payload.get("capsule_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_AUTHORIZATION_CAPSULE_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_AUTHORIZATION_CAPSULE_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(release_seal.get("status", "")) == "blocked"
        and str(release_seal.get("reason", ""))
        == "release_authorization_seal_execution_closed"
        and bool(release_seal_hash),
        bool(expected_release_seal_hash)
        and expected_release_seal_hash == release_seal_hash,
        bool(capsule_payload),
        bool(supplied_release_seal_hash)
        and supplied_release_seal_hash == release_seal_hash,
        bool(final_authz_hash),
        capsule_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            release_seal_hash,
            final_authz_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "release_seal_missing_or_mismatched"
    elif not expected_release_seal_hash:
        reason = "expected_release_seal_hash_required"
    elif expected_release_seal_hash != release_seal_hash:
        reason = "release_seal_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_authorization_capsule_required"
    elif not component_checks[3]:
        reason = "execution_authorization_capsule_release_seal_hash_mismatch"
    elif not component_checks[4]:
        reason = "final_authorization_required"
    elif not component_checks[5]:
        reason = "execution_authorization_capsule_request_required"
    elif not component_checks[6]:
        reason = "execution_authorization_capsule_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_authorization_capsule_no_call_counters_mismatch"
    else:
        reason = "execution_authorization_capsule_execution_closed"

    execution_capsule_hash = ""
    if mismatch_count == 0:
        execution_capsule_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_AUTHORIZATION_CAPSULE_VERSION
                ),
                "release_seal_hash": release_seal_hash,
                "final_authz_hash": final_authz_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_hash": execution_capsule_hash,
            "release_seal_hash": release_seal_hash,
            "final_authz_hash": final_authz_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "final_authz_count": 1 if final_authz_hash else 0,
            "capsule_request_count": 1 if capsule_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_export_projection(
    *,
    payload: dict[str, Any],
    execution_capsule: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    execution_capsule_hash = str(
        execution_capsule.get("execution_capsule_hash", "")
    ).strip()
    expected_execution_capsule_hash = str(
        payload.get("expected_execution_capsule_hash", "")
    ).strip()
    export_payload = (
        payload.get("manual_test_execution_capsule_export")
        if isinstance(payload.get("manual_test_execution_capsule_export"), dict)
        else {}
    )
    supplied_execution_capsule_hash = str(
        export_payload.get("execution_capsule_hash", "")
    ).strip()
    export_metadata = (
        export_payload.get("export_metadata")
        if isinstance(export_payload.get("export_metadata"), dict)
        else {}
    )
    export_metadata_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_EXPORT_VERSION
                ),
                "export_kind": str(export_metadata.get("export_kind", "")).strip(),
                "export_reason_code": str(
                    export_metadata.get("export_reason_code", "")
                ).strip(),
                "exported_at": str(export_metadata.get("exported_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            export_metadata.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(export_metadata.get("operator_ref", "")).strip()
                else "",
            }
        )
        if export_metadata
        else ""
    )
    export_requested = export_payload.get("export_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_EXPORT_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_EXPORT_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule.get("status", "")) == "blocked"
        and str(execution_capsule.get("reason", ""))
        == "execution_authorization_capsule_execution_closed"
        and bool(execution_capsule_hash),
        bool(expected_execution_capsule_hash)
        and expected_execution_capsule_hash == execution_capsule_hash,
        bool(export_payload),
        bool(supplied_execution_capsule_hash)
        and supplied_execution_capsule_hash == execution_capsule_hash,
        bool(export_metadata_hash),
        export_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            execution_capsule_hash,
            export_metadata_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_missing_or_mismatched"
    elif not expected_execution_capsule_hash:
        reason = "expected_execution_capsule_hash_required"
    elif expected_execution_capsule_hash != execution_capsule_hash:
        reason = "execution_capsule_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_export_required"
    elif not component_checks[3]:
        reason = "execution_capsule_export_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_export_metadata_required"
    elif not component_checks[5]:
        reason = "execution_capsule_export_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_export_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_export_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_export_execution_closed"

    execution_capsule_export_hash = ""
    if mismatch_count == 0:
        execution_capsule_export_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_EXPORT_VERSION
                ),
                "execution_capsule_hash": execution_capsule_hash,
                "export_metadata_hash": export_metadata_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_export_hash": execution_capsule_export_hash,
            "execution_capsule_hash": execution_capsule_hash,
            "export_metadata_hash": export_metadata_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "export_count": 1 if execution_capsule_export_hash else 0,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "export_metadata_count": 1 if export_metadata_hash else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_export_read_model_projection(
    export_projection: JsonDict,
) -> JsonDict:
    if (
        str(export_projection.get("status", "")) == "blocked"
        and str(export_projection.get("reason", ""))
        == "execution_capsule_export_execution_closed"
        and str(export_projection.get("execution_capsule_export_hash", "")).strip()
    ):
        return _safe_public_payload(
            {
                "status": "available",
                "reason": "execution_capsule_export_read_model_available",
                "latest_execution_capsule_export_hash": str(
                    export_projection.get("execution_capsule_export_hash", "")
                ),
                "counts": {
                    "execution_capsule_export_count": int(
                        export_projection.get("export_count", 0)
                    ),
                    "component_count": int(
                        export_projection.get("component_count", 0)
                    ),
                    "execution_permission_count": int(
                        export_projection.get("execution_permission_count", 0)
                    ),
                },
            }
        )
    return _manual_provider_test_execution_capsule_export_read_model_blocked(
        "execution_capsule_export_not_available"
    )


def _manual_provider_test_execution_capsule_handoff_packet_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_export: JsonDict,
    execution_capsule_export_read_model: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    execution_capsule_export_hash = str(
        execution_capsule_export.get("execution_capsule_export_hash", "")
    ).strip()
    expected_execution_capsule_export_hash = str(
        payload.get("expected_execution_capsule_export_hash", "")
    ).strip()
    handoff_payload = (
        payload.get("manual_test_execution_capsule_handoff_packet")
        if isinstance(payload.get("manual_test_execution_capsule_handoff_packet"), dict)
        else {}
    )
    supplied_execution_capsule_export_hash = str(
        handoff_payload.get("execution_capsule_export_hash", "")
    ).strip()
    read_model_hash = str(
        execution_capsule_export_read_model.get(
            "latest_execution_capsule_export_hash", ""
        )
    ).strip()
    handoff_requested = handoff_payload.get("handoff_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_HANDOFF_PACKET_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_HANDOFF_PACKET_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    read_model_available = (
        str(execution_capsule_export_read_model.get("status", "")) == "available"
        and str(execution_capsule_export_read_model.get("reason", ""))
        == "execution_capsule_export_read_model_available"
        and bool(read_model_hash)
        and read_model_hash == execution_capsule_export_hash
        and _coerce_int(
            execution_capsule_export_read_model.get("counts", {}).get(
                "execution_permission_count", 0
            )
            if isinstance(
                execution_capsule_export_read_model.get("counts", {}), dict
            )
            else 0
        )
        == 0
    )
    component_checks = [
        str(execution_capsule_export.get("status", "")) == "blocked"
        and str(execution_capsule_export.get("reason", ""))
        == "execution_capsule_export_execution_closed"
        and bool(execution_capsule_export_hash)
        and _coerce_int(execution_capsule_export.get("execution_permission_count", 0))
        == 0,
        bool(expected_execution_capsule_export_hash)
        and expected_execution_capsule_export_hash == execution_capsule_export_hash,
        bool(handoff_payload),
        bool(supplied_execution_capsule_export_hash)
        and supplied_execution_capsule_export_hash == execution_capsule_export_hash,
        read_model_available,
        handoff_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            execution_capsule_export_hash,
            read_model_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_export_missing_or_mismatched"
    elif not expected_execution_capsule_export_hash:
        reason = "expected_execution_capsule_export_hash_required"
    elif expected_execution_capsule_export_hash != execution_capsule_export_hash:
        reason = "execution_capsule_export_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_handoff_packet_required"
    elif not component_checks[3]:
        reason = "execution_capsule_handoff_packet_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_export_read_model_missing_or_mismatched"
    elif not component_checks[5]:
        reason = "execution_capsule_handoff_packet_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_handoff_packet_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_handoff_packet_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_handoff_packet_execution_closed"

    execution_capsule_handoff_packet_hash = ""
    if mismatch_count == 0:
        execution_capsule_handoff_packet_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_HANDOFF_PACKET_VERSION
                ),
                "execution_capsule_export_hash": execution_capsule_export_hash,
                "execution_capsule_export_read_model_hash": read_model_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_handoff_packet_hash": (
                execution_capsule_handoff_packet_hash
            ),
            "execution_capsule_export_hash": execution_capsule_export_hash,
            "execution_capsule_export_read_model_hash": read_model_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "packet_count": 1 if execution_capsule_handoff_packet_hash else 0,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "export_read_model_count": 1 if read_model_available else 0,
            "handoff_request_count": 1 if handoff_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_operator_review_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_handoff_packet: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    handoff_packet_hash = str(
        execution_capsule_handoff_packet.get(
            "execution_capsule_handoff_packet_hash", ""
        )
    ).strip()
    expected_handoff_packet_hash = str(
        payload.get("expected_execution_capsule_handoff_packet_hash", "")
    ).strip()
    review_payload = (
        payload.get("manual_test_execution_capsule_operator_review")
        if isinstance(payload.get("manual_test_execution_capsule_operator_review"), dict)
        else {}
    )
    supplied_handoff_packet_hash = str(
        review_payload.get("execution_capsule_handoff_packet_hash", "")
    ).strip()
    operator_review = (
        review_payload.get("operator_review")
        if isinstance(review_payload.get("operator_review"), dict)
        else {}
    )
    operator_review_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_REVIEW_VERSION
                ),
                "review_decision": str(
                    operator_review.get("review_decision", "")
                ).strip(),
                "review_reason_code": str(
                    operator_review.get("review_reason_code", "")
                ).strip(),
                "reviewed_at": str(operator_review.get("reviewed_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            operator_review.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(operator_review.get("operator_ref", "")).strip()
                else "",
            }
        )
        if operator_review
        else ""
    )
    review_requested = review_payload.get("review_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_REVIEW_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_REVIEW_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_handoff_packet.get("status", "")) == "blocked"
        and str(execution_capsule_handoff_packet.get("reason", ""))
        == "execution_capsule_handoff_packet_execution_closed"
        and bool(handoff_packet_hash)
        and _coerce_int(
            execution_capsule_handoff_packet.get("execution_permission_count", 0)
        )
        == 0,
        bool(expected_handoff_packet_hash)
        and expected_handoff_packet_hash == handoff_packet_hash,
        bool(review_payload),
        bool(supplied_handoff_packet_hash)
        and supplied_handoff_packet_hash == handoff_packet_hash,
        bool(operator_review_hash),
        review_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            handoff_packet_hash,
            operator_review_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_handoff_packet_missing_or_mismatched"
    elif not expected_handoff_packet_hash:
        reason = "expected_execution_capsule_handoff_packet_hash_required"
    elif expected_handoff_packet_hash != handoff_packet_hash:
        reason = "execution_capsule_handoff_packet_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_operator_review_required"
    elif not component_checks[3]:
        reason = "execution_capsule_operator_review_handoff_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_operator_review_required"
    elif not component_checks[5]:
        reason = "execution_capsule_operator_review_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_operator_review_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_operator_review_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_operator_review_execution_closed"

    execution_capsule_operator_review_hash = ""
    if mismatch_count == 0:
        execution_capsule_operator_review_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_REVIEW_VERSION
                ),
                "execution_capsule_handoff_packet_hash": handoff_packet_hash,
                "operator_review_hash": operator_review_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_operator_review_hash": (
                execution_capsule_operator_review_hash
            ),
            "execution_capsule_handoff_packet_hash": handoff_packet_hash,
            "operator_review_hash": operator_review_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "operator_review_count": 1 if operator_review_hash else 0,
            "review_request_count": 1 if review_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_operator_decision_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_operator_review: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    operator_review_hash = str(
        execution_capsule_operator_review.get(
            "execution_capsule_operator_review_hash", ""
        )
    ).strip()
    expected_operator_review_hash = str(
        payload.get("expected_execution_capsule_operator_review_hash", "")
    ).strip()
    decision_payload = (
        payload.get("manual_test_execution_capsule_operator_decision")
        if isinstance(payload.get("manual_test_execution_capsule_operator_decision"), dict)
        else {}
    )
    supplied_operator_review_hash = str(
        decision_payload.get("execution_capsule_operator_review_hash", "")
    ).strip()
    operator_decision = (
        decision_payload.get("operator_decision")
        if isinstance(decision_payload.get("operator_decision"), dict)
        else {}
    )
    operator_decision_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_DECISION_VERSION
                ),
                "decision": str(operator_decision.get("decision", "")).strip(),
                "decision_reason_code": str(
                    operator_decision.get("decision_reason_code", "")
                ).strip(),
                "decided_at": str(operator_decision.get("decided_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            operator_decision.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(operator_decision.get("operator_ref", "")).strip()
                else "",
            }
        )
        if operator_decision
        else ""
    )
    decision_requested = decision_payload.get("decision_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_DECISION_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_DECISION_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_operator_review.get("status", "")) == "blocked"
        and str(execution_capsule_operator_review.get("reason", ""))
        == "execution_capsule_operator_review_execution_closed"
        and bool(operator_review_hash)
        and _coerce_int(
            execution_capsule_operator_review.get("execution_permission_count", 0)
        )
        == 0,
        bool(expected_operator_review_hash)
        and expected_operator_review_hash == operator_review_hash,
        bool(decision_payload),
        bool(supplied_operator_review_hash)
        and supplied_operator_review_hash == operator_review_hash,
        bool(operator_decision_hash),
        decision_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            operator_review_hash,
            operator_decision_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_operator_review_missing_or_mismatched"
    elif not expected_operator_review_hash:
        reason = "expected_execution_capsule_operator_review_hash_required"
    elif expected_operator_review_hash != operator_review_hash:
        reason = "execution_capsule_operator_review_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_operator_decision_required"
    elif not component_checks[3]:
        reason = "execution_capsule_operator_decision_review_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_operator_decision_required"
    elif not component_checks[5]:
        reason = "execution_capsule_operator_decision_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_operator_decision_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_operator_decision_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_operator_decision_execution_closed"

    execution_capsule_operator_decision_hash = ""
    if mismatch_count == 0:
        execution_capsule_operator_decision_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_DECISION_VERSION
                ),
                "execution_capsule_operator_review_hash": operator_review_hash,
                "operator_decision_hash": operator_decision_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_operator_decision_hash": (
                execution_capsule_operator_decision_hash
            ),
            "execution_capsule_operator_review_hash": operator_review_hash,
            "operator_decision_hash": operator_decision_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "operator_decision_count": 1 if operator_decision_hash else 0,
            "decision_request_count": 1 if decision_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_release_attestation_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_operator_decision: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    operator_decision_hash = str(
        execution_capsule_operator_decision.get(
            "execution_capsule_operator_decision_hash", ""
        )
    ).strip()
    expected_operator_decision_hash = str(
        payload.get("expected_execution_capsule_operator_decision_hash", "")
    ).strip()
    attestation_payload = (
        payload.get("manual_test_execution_capsule_release_attestation")
        if isinstance(
            payload.get("manual_test_execution_capsule_release_attestation"), dict
        )
        else {}
    )
    supplied_operator_decision_hash = str(
        attestation_payload.get("execution_capsule_operator_decision_hash", "")
    ).strip()
    release_attestation = (
        attestation_payload.get("release_attestation")
        if isinstance(attestation_payload.get("release_attestation"), dict)
        else {}
    )
    release_attestation_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_ATTESTATION_VERSION
                ),
                "attestation": str(
                    release_attestation.get("attestation", "")
                ).strip(),
                "attestation_reason_code": str(
                    release_attestation.get("attestation_reason_code", "")
                ).strip(),
                "attested_at": str(
                    release_attestation.get("attested_at", "")
                ).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            release_attestation.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(release_attestation.get("operator_ref", "")).strip()
                else "",
            }
        )
        if release_attestation
        else ""
    )
    attestation_requested = attestation_payload.get("attestation_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_ATTESTATION_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_ATTESTATION_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_operator_decision.get("status", "")) == "blocked"
        and str(execution_capsule_operator_decision.get("reason", ""))
        == "execution_capsule_operator_decision_execution_closed"
        and bool(operator_decision_hash)
        and _coerce_int(
            execution_capsule_operator_decision.get("execution_permission_count", 0)
        )
        == 0,
        bool(expected_operator_decision_hash)
        and expected_operator_decision_hash == operator_decision_hash,
        bool(attestation_payload),
        bool(supplied_operator_decision_hash)
        and supplied_operator_decision_hash == operator_decision_hash,
        bool(release_attestation_hash),
        attestation_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            operator_decision_hash,
            release_attestation_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_operator_decision_missing_or_mismatched"
    elif not expected_operator_decision_hash:
        reason = "expected_execution_capsule_operator_decision_hash_required"
    elif expected_operator_decision_hash != operator_decision_hash:
        reason = "execution_capsule_operator_decision_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_release_attestation_required"
    elif not component_checks[3]:
        reason = "execution_capsule_release_attestation_decision_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_release_attestation_required"
    elif not component_checks[5]:
        reason = "execution_capsule_release_attestation_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_release_attestation_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_release_attestation_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_release_attestation_execution_closed"

    execution_capsule_release_attestation_hash = ""
    if mismatch_count == 0:
        execution_capsule_release_attestation_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_ATTESTATION_VERSION
                ),
                "execution_capsule_operator_decision_hash": operator_decision_hash,
                "release_attestation_hash": release_attestation_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_release_attestation_hash": (
                execution_capsule_release_attestation_hash
            ),
            "execution_capsule_operator_decision_hash": operator_decision_hash,
            "release_attestation_hash": release_attestation_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "release_attestation_count": 1 if release_attestation_hash else 0,
            "attestation_request_count": 1 if attestation_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_release_seal_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_release_attestation: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    release_attestation_hash = str(
        execution_capsule_release_attestation.get(
            "execution_capsule_release_attestation_hash", ""
        )
    ).strip()
    expected_release_attestation_hash = str(
        payload.get("expected_execution_capsule_release_attestation_hash", "")
    ).strip()
    seal_payload = (
        payload.get("manual_test_execution_capsule_release_seal")
        if isinstance(payload.get("manual_test_execution_capsule_release_seal"), dict)
        else {}
    )
    supplied_release_attestation_hash = str(
        seal_payload.get("execution_capsule_release_attestation_hash", "")
    ).strip()
    seal_material = (
        seal_payload.get("seal_material")
        if isinstance(seal_payload.get("seal_material"), dict)
        else {}
    )
    seal_material_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_SEAL_VERSION
                ),
                "seal_decision": str(
                    seal_material.get("seal_decision", "")
                ).strip(),
                "seal_reason_code": str(
                    seal_material.get("seal_reason_code", "")
                ).strip(),
                "sealed_at": str(seal_material.get("sealed_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            seal_material.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(seal_material.get("operator_ref", "")).strip()
                else "",
            }
        )
        if seal_material
        else ""
    )
    seal_requested = seal_payload.get("seal_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_SEAL_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_SEAL_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_release_attestation.get("status", "")) == "blocked"
        and str(execution_capsule_release_attestation.get("reason", ""))
        == "execution_capsule_release_attestation_execution_closed"
        and bool(release_attestation_hash)
        and _coerce_int(
            execution_capsule_release_attestation.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_release_attestation_hash)
        and expected_release_attestation_hash == release_attestation_hash,
        bool(seal_payload),
        bool(supplied_release_attestation_hash)
        and supplied_release_attestation_hash == release_attestation_hash,
        bool(seal_material_hash),
        seal_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            release_attestation_hash,
            seal_material_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_release_attestation_missing_or_mismatched"
    elif not expected_release_attestation_hash:
        reason = "expected_execution_capsule_release_attestation_hash_required"
    elif expected_release_attestation_hash != release_attestation_hash:
        reason = "execution_capsule_release_attestation_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_release_seal_required"
    elif not component_checks[3]:
        reason = "execution_capsule_release_seal_attestation_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_release_seal_material_required"
    elif not component_checks[5]:
        reason = "execution_capsule_release_seal_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_release_seal_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_release_seal_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_release_seal_execution_closed"

    execution_capsule_release_seal_hash = ""
    if mismatch_count == 0:
        execution_capsule_release_seal_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_SEAL_VERSION
                ),
                "execution_capsule_release_attestation_hash": (
                    release_attestation_hash
                ),
                "seal_material_hash": seal_material_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_release_seal_hash": (
                execution_capsule_release_seal_hash
            ),
            "execution_capsule_release_attestation_hash": (
                release_attestation_hash
            ),
            "seal_material_hash": seal_material_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "seal_material_count": 1 if seal_material_hash else 0,
            "seal_request_count": 1 if seal_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_final_authorization_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_release_seal: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    release_seal_hash = str(
        execution_capsule_release_seal.get("execution_capsule_release_seal_hash", "")
    ).strip()
    expected_release_seal_hash = str(
        payload.get("expected_execution_capsule_release_seal_hash", "")
    ).strip()
    authorization_payload = (
        payload.get("manual_test_execution_capsule_final_authorization")
        if isinstance(
            payload.get("manual_test_execution_capsule_final_authorization"), dict
        )
        else {}
    )
    supplied_release_seal_hash = str(
        authorization_payload.get("execution_capsule_release_seal_hash", "")
    ).strip()
    final_authorization = (
        authorization_payload.get("final_authorization")
        if isinstance(authorization_payload.get("final_authorization"), dict)
        else {}
    )
    final_authz_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_FINAL_AUTHORIZATION_VERSION
                ),
                "authorization_decision": str(
                    final_authorization.get("authorization_decision", "")
                ).strip(),
                "authorization_reason_code": str(
                    final_authorization.get("authorization_reason_code", "")
                ).strip(),
                "authorized_at": str(
                    final_authorization.get("authorized_at", "")
                ).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            final_authorization.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(final_authorization.get("operator_ref", "")).strip()
                else "",
            }
        )
        if final_authorization
        else ""
    )
    authz_requested = (
        authorization_payload.get("authorization_requested") is True
    )
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_FINAL_AUTHORIZATION_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_FINAL_AUTHORIZATION_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_release_seal.get("status", "")) == "blocked"
        and str(execution_capsule_release_seal.get("reason", ""))
        == "execution_capsule_release_seal_execution_closed"
        and bool(release_seal_hash)
        and _coerce_int(
            execution_capsule_release_seal.get("execution_permission_count", 0)
        )
        == 0,
        bool(expected_release_seal_hash)
        and expected_release_seal_hash == release_seal_hash,
        bool(authorization_payload),
        bool(supplied_release_seal_hash)
        and supplied_release_seal_hash == release_seal_hash,
        bool(final_authz_hash),
        authz_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            release_seal_hash,
            final_authz_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_release_seal_missing_or_mismatched"
    elif not expected_release_seal_hash:
        reason = "expected_execution_capsule_release_seal_hash_required"
    elif expected_release_seal_hash != release_seal_hash:
        reason = "execution_capsule_release_seal_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_final_authz_required"
    elif not component_checks[3]:
        reason = "execution_capsule_final_authz_seal_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_final_authz_required"
    elif not component_checks[5]:
        reason = "execution_capsule_final_authz_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_final_authz_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_final_authz_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_final_authz_execution_closed"

    execution_capsule_final_authz_hash = ""
    if mismatch_count == 0:
        execution_capsule_final_authz_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_FINAL_AUTHORIZATION_VERSION
                ),
                "execution_capsule_release_seal_hash": release_seal_hash,
                "final_authz_hash": final_authz_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_final_authz_hash": (
                execution_capsule_final_authz_hash
            ),
            "execution_capsule_release_seal_hash": release_seal_hash,
            "final_authz_hash": final_authz_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "final_authz_count": 1 if final_authz_hash else 0,
            "authz_request_count": 1 if authz_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_export_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_final_authz: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    final_authz_hash = str(
        execution_capsule_final_authz.get("execution_capsule_final_authz_hash", "")
    ).strip()
    expected_final_authz_hash = str(
        payload.get("expected_execution_capsule_final_authz_hash", "")
    ).strip()
    export_payload = (
        payload.get("manual_test_execution_capsule_authz_export")
        if isinstance(payload.get("manual_test_execution_capsule_authz_export"), dict)
        else {}
    )
    supplied_final_authz_hash = str(
        export_payload.get("execution_capsule_final_authz_hash", "")
    ).strip()
    export_metadata = (
        export_payload.get("export_metadata")
        if isinstance(export_payload.get("export_metadata"), dict)
        else {}
    )
    export_metadata_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_EXPORT_VERSION
                ),
                "export_kind": str(export_metadata.get("export_kind", "")).strip(),
                "export_reason_code": str(
                    export_metadata.get("export_reason_code", "")
                ).strip(),
                "exported_at": str(export_metadata.get("exported_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            export_metadata.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(export_metadata.get("operator_ref", "")).strip()
                else "",
            }
        )
        if export_metadata
        else ""
    )
    export_requested = export_payload.get("export_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_EXPORT_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_EXPORT_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_final_authz.get("status", "")) == "blocked"
        and str(execution_capsule_final_authz.get("reason", ""))
        == "execution_capsule_final_authz_execution_closed"
        and bool(final_authz_hash)
        and _coerce_int(
            execution_capsule_final_authz.get("execution_permission_count", 0)
        )
        == 0,
        bool(expected_final_authz_hash)
        and expected_final_authz_hash == final_authz_hash,
        bool(export_payload),
        bool(supplied_final_authz_hash)
        and supplied_final_authz_hash == final_authz_hash,
        bool(export_metadata_hash),
        export_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            final_authz_hash,
            export_metadata_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_final_authz_missing_or_mismatched"
    elif not expected_final_authz_hash:
        reason = "expected_execution_capsule_final_authz_hash_required"
    elif expected_final_authz_hash != final_authz_hash:
        reason = "execution_capsule_final_authz_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_export_required"
    elif not component_checks[3]:
        reason = "execution_capsule_authz_export_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_authz_export_metadata_required"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_export_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_authz_export_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_authz_export_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_authz_export_execution_closed"

    execution_capsule_authz_export_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_export_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_EXPORT_VERSION
                ),
                "execution_capsule_final_authz_hash": final_authz_hash,
                "export_metadata_hash": export_metadata_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_export_hash": execution_capsule_authz_export_hash,
            "execution_capsule_final_authz_hash": final_authz_hash,
            "export_metadata_hash": export_metadata_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "export_count": 1 if execution_capsule_authz_export_hash else 0,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "export_metadata_count": 1 if export_metadata_hash else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_export_read_model_projection(
    export_projection: JsonDict,
) -> JsonDict:
    if (
        str(export_projection.get("status", "")) == "blocked"
        and str(export_projection.get("reason", ""))
        == "execution_capsule_authz_export_execution_closed"
        and str(
            export_projection.get("execution_capsule_authz_export_hash", "")
        ).strip()
    ):
        return _safe_public_payload(
            {
                "status": "available",
                "reason": "execution_capsule_authz_export_read_model_available",
                "latest_execution_capsule_authz_export_hash": str(
                    export_projection.get("execution_capsule_authz_export_hash", "")
                ),
                "counts": {
                    "execution_capsule_authz_export_count": int(
                        export_projection.get("export_count", 0)
                    ),
                    "component_count": int(
                        export_projection.get("component_count", 0)
                    ),
                    "execution_permission_count": int(
                        export_projection.get("execution_permission_count", 0)
                    ),
                },
            }
        )
    return _manual_provider_test_execution_capsule_authz_export_read_model_blocked(
        "execution_capsule_authz_export_not_available"
    )


def _manual_provider_test_execution_capsule_authz_handoff_packet_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_export: JsonDict,
    execution_capsule_authz_export_read_model: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    execution_capsule_authz_export_hash = str(
        execution_capsule_authz_export.get("execution_capsule_authz_export_hash", "")
    ).strip()
    expected_execution_capsule_authz_export_hash = str(
        payload.get("expected_execution_capsule_authz_export_hash", "")
    ).strip()
    handoff_payload = (
        payload.get("manual_test_execution_capsule_authz_handoff_packet")
        if isinstance(
            payload.get("manual_test_execution_capsule_authz_handoff_packet"), dict
        )
        else {}
    )
    supplied_execution_capsule_authz_export_hash = str(
        handoff_payload.get("execution_capsule_authz_export_hash", "")
    ).strip()
    read_model_hash = str(
        execution_capsule_authz_export_read_model.get(
            "latest_execution_capsule_authz_export_hash", ""
        )
    ).strip()
    handoff_requested = handoff_payload.get("handoff_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_HANDOFF_PACKET_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_HANDOFF_PACKET_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    read_model_available = (
        str(execution_capsule_authz_export_read_model.get("status", ""))
        == "available"
        and str(execution_capsule_authz_export_read_model.get("reason", ""))
        == "execution_capsule_authz_export_read_model_available"
        and bool(read_model_hash)
        and read_model_hash == execution_capsule_authz_export_hash
        and _coerce_int(
            execution_capsule_authz_export_read_model.get("counts", {}).get(
                "execution_permission_count", 0
            )
            if isinstance(
                execution_capsule_authz_export_read_model.get("counts", {}), dict
            )
            else 0
        )
        == 0
    )
    component_checks = [
        str(execution_capsule_authz_export.get("status", "")) == "blocked"
        and str(execution_capsule_authz_export.get("reason", ""))
        == "execution_capsule_authz_export_execution_closed"
        and bool(execution_capsule_authz_export_hash)
        and _coerce_int(
            execution_capsule_authz_export.get("execution_permission_count", 0)
        )
        == 0,
        bool(expected_execution_capsule_authz_export_hash)
        and expected_execution_capsule_authz_export_hash
        == execution_capsule_authz_export_hash,
        bool(handoff_payload),
        bool(supplied_execution_capsule_authz_export_hash)
        and supplied_execution_capsule_authz_export_hash
        == execution_capsule_authz_export_hash,
        read_model_available,
        handoff_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            execution_capsule_authz_export_hash,
            read_model_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_authz_export_missing_or_mismatched"
    elif not expected_execution_capsule_authz_export_hash:
        reason = "expected_execution_capsule_authz_export_hash_required"
    elif (
        expected_execution_capsule_authz_export_hash
        != execution_capsule_authz_export_hash
    ):
        reason = "execution_capsule_authz_export_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_handoff_packet_required"
    elif not component_checks[3]:
        reason = "execution_capsule_authz_handoff_packet_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_authz_export_read_model_missing_or_mismatched"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_handoff_packet_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_authz_handoff_packet_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_authz_handoff_packet_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_authz_handoff_packet_execution_closed"

    execution_capsule_authz_handoff_packet_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_handoff_packet_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_HANDOFF_PACKET_VERSION
                ),
                "execution_capsule_authz_export_hash": (
                    execution_capsule_authz_export_hash
                ),
                "execution_capsule_authz_export_read_model_hash": read_model_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_handoff_packet_hash": (
                execution_capsule_authz_handoff_packet_hash
            ),
            "execution_capsule_authz_export_hash": (
                execution_capsule_authz_export_hash
            ),
            "execution_capsule_authz_export_read_model_hash": read_model_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "packet_count": (
                1 if execution_capsule_authz_handoff_packet_hash else 0
            ),
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "export_read_model_count": 1 if read_model_available else 0,
            "handoff_request_count": 1 if handoff_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_operator_review_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_handoff_packet: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    handoff_packet_hash = str(
        execution_capsule_authz_handoff_packet.get(
            "execution_capsule_authz_handoff_packet_hash", ""
        )
    ).strip()
    expected_handoff_packet_hash = str(
        payload.get("expected_execution_capsule_authz_handoff_packet_hash", "")
    ).strip()
    review_payload = (
        payload.get("manual_test_execution_capsule_authz_operator_review")
        if isinstance(
            payload.get("manual_test_execution_capsule_authz_operator_review"), dict
        )
        else {}
    )
    supplied_handoff_packet_hash = str(
        review_payload.get("execution_capsule_authz_handoff_packet_hash", "")
    ).strip()
    operator_review = (
        review_payload.get("operator_review")
        if isinstance(review_payload.get("operator_review"), dict)
        else {}
    )
    operator_review_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_REVIEW_VERSION
                ),
                "review_decision": str(
                    operator_review.get("review_decision", "")
                ).strip(),
                "review_reason_code": str(
                    operator_review.get("review_reason_code", "")
                ).strip(),
                "reviewed_at": str(operator_review.get("reviewed_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            operator_review.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(operator_review.get("operator_ref", "")).strip()
                else "",
            }
        )
        if operator_review
        else ""
    )
    review_requested = review_payload.get("review_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_REVIEW_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_REVIEW_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_authz_handoff_packet.get("status", "")) == "blocked"
        and str(execution_capsule_authz_handoff_packet.get("reason", ""))
        == "execution_capsule_authz_handoff_packet_execution_closed"
        and bool(handoff_packet_hash)
        and _coerce_int(
            execution_capsule_authz_handoff_packet.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_handoff_packet_hash)
        and expected_handoff_packet_hash == handoff_packet_hash,
        bool(review_payload),
        bool(supplied_handoff_packet_hash)
        and supplied_handoff_packet_hash == handoff_packet_hash,
        bool(operator_review_hash),
        review_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            handoff_packet_hash,
            operator_review_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_authz_handoff_packet_missing_or_mismatched"
    elif not expected_handoff_packet_hash:
        reason = "expected_execution_capsule_authz_handoff_packet_hash_required"
    elif expected_handoff_packet_hash != handoff_packet_hash:
        reason = "execution_capsule_authz_handoff_packet_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_operator_review_required"
    elif not component_checks[3]:
        reason = "execution_capsule_authz_operator_review_handoff_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_authz_operator_review_required"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_operator_review_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_authz_operator_review_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_authz_operator_review_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_authz_operator_review_execution_closed"

    execution_capsule_authz_operator_review_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_operator_review_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_REVIEW_VERSION
                ),
                "execution_capsule_authz_handoff_packet_hash": handoff_packet_hash,
                "operator_review_hash": operator_review_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_operator_review_hash": (
                execution_capsule_authz_operator_review_hash
            ),
            "execution_capsule_authz_handoff_packet_hash": handoff_packet_hash,
            "operator_review_hash": operator_review_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "operator_review_count": 1 if operator_review_hash else 0,
            "review_request_count": 1 if review_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_operator_decision_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_operator_review: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    operator_review_hash = str(
        execution_capsule_authz_operator_review.get(
            "execution_capsule_authz_operator_review_hash", ""
        )
    ).strip()
    expected_operator_review_hash = str(
        payload.get("expected_execution_capsule_authz_operator_review_hash", "")
    ).strip()
    decision_payload = (
        payload.get("manual_test_execution_capsule_authz_operator_decision")
        if isinstance(
            payload.get("manual_test_execution_capsule_authz_operator_decision"), dict
        )
        else {}
    )
    supplied_operator_review_hash = str(
        decision_payload.get("execution_capsule_authz_operator_review_hash", "")
    ).strip()
    operator_decision = (
        decision_payload.get("operator_decision")
        if isinstance(decision_payload.get("operator_decision"), dict)
        else {}
    )
    operator_decision_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_DECISION_VERSION
                ),
                "decision": str(operator_decision.get("decision", "")).strip(),
                "decision_reason_code": str(
                    operator_decision.get("decision_reason_code", "")
                ).strip(),
                "decided_at": str(operator_decision.get("decided_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            operator_decision.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(operator_decision.get("operator_ref", "")).strip()
                else "",
            }
        )
        if operator_decision
        else ""
    )
    decision_requested = decision_payload.get("decision_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_DECISION_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_DECISION_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_authz_operator_review.get("status", "")) == "blocked"
        and str(execution_capsule_authz_operator_review.get("reason", ""))
        == "execution_capsule_authz_operator_review_execution_closed"
        and bool(operator_review_hash)
        and _coerce_int(
            execution_capsule_authz_operator_review.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_operator_review_hash)
        and expected_operator_review_hash == operator_review_hash,
        bool(decision_payload),
        bool(supplied_operator_review_hash)
        and supplied_operator_review_hash == operator_review_hash,
        bool(operator_decision_hash),
        decision_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            operator_review_hash,
            operator_decision_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_authz_operator_review_missing_or_mismatched"
    elif not expected_operator_review_hash:
        reason = "expected_execution_capsule_authz_operator_review_hash_required"
    elif expected_operator_review_hash != operator_review_hash:
        reason = "execution_capsule_authz_operator_review_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_operator_decision_required"
    elif not component_checks[3]:
        reason = "execution_capsule_authz_operator_decision_review_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_authz_operator_decision_required"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_operator_decision_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_authz_operator_decision_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_authz_operator_decision_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_authz_operator_decision_execution_closed"

    execution_capsule_authz_operator_decision_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_operator_decision_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_DECISION_VERSION
                ),
                "execution_capsule_authz_operator_review_hash": (
                    operator_review_hash
                ),
                "operator_decision_hash": operator_decision_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_operator_decision_hash": (
                execution_capsule_authz_operator_decision_hash
            ),
            "execution_capsule_authz_operator_review_hash": operator_review_hash,
            "operator_decision_hash": operator_decision_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "operator_decision_count": 1 if operator_decision_hash else 0,
            "decision_request_count": 1 if decision_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_release_attestation_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_operator_decision: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    operator_decision_hash = str(
        execution_capsule_authz_operator_decision.get(
            "execution_capsule_authz_operator_decision_hash", ""
        )
    ).strip()
    expected_operator_decision_hash = str(
        payload.get("expected_execution_capsule_authz_operator_decision_hash", "")
    ).strip()
    attestation_payload = (
        payload.get("manual_test_execution_capsule_authz_release_attestation")
        if isinstance(
            payload.get("manual_test_execution_capsule_authz_release_attestation"),
            dict,
        )
        else {}
    )
    supplied_operator_decision_hash = str(
        attestation_payload.get(
            "execution_capsule_authz_operator_decision_hash", ""
        )
    ).strip()
    release_attestation = (
        attestation_payload.get("release_attestation")
        if isinstance(attestation_payload.get("release_attestation"), dict)
        else {}
    )
    release_attestation_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_ATTESTATION_VERSION
                ),
                "attestation": str(
                    release_attestation.get("attestation", "")
                ).strip(),
                "attestation_reason_code": str(
                    release_attestation.get("attestation_reason_code", "")
                ).strip(),
                "attested_at": str(
                    release_attestation.get("attested_at", "")
                ).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            release_attestation.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(release_attestation.get("operator_ref", "")).strip()
                else "",
            }
        )
        if release_attestation
        else ""
    )
    attestation_requested = attestation_payload.get("attestation_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_ATTESTATION_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_ATTESTATION_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_authz_operator_decision.get("status", "")) == "blocked"
        and str(execution_capsule_authz_operator_decision.get("reason", ""))
        == "execution_capsule_authz_operator_decision_execution_closed"
        and bool(operator_decision_hash)
        and _coerce_int(
            execution_capsule_authz_operator_decision.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_operator_decision_hash)
        and expected_operator_decision_hash == operator_decision_hash,
        bool(attestation_payload),
        bool(supplied_operator_decision_hash)
        and supplied_operator_decision_hash == operator_decision_hash,
        bool(release_attestation_hash),
        attestation_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            operator_decision_hash,
            release_attestation_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_authz_operator_decision_missing_or_mismatched"
    elif not expected_operator_decision_hash:
        reason = "expected_execution_capsule_authz_operator_decision_hash_required"
    elif expected_operator_decision_hash != operator_decision_hash:
        reason = "execution_capsule_authz_operator_decision_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_release_attestation_required"
    elif not component_checks[3]:
        reason = "execution_capsule_authz_release_attestation_decision_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_authz_release_attestation_required"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_release_attestation_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_authz_release_attestation_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_authz_release_attestation_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_authz_release_attestation_execution_closed"

    execution_capsule_authz_release_attestation_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_release_attestation_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_ATTESTATION_VERSION
                ),
                "execution_capsule_authz_operator_decision_hash": (
                    operator_decision_hash
                ),
                "release_attestation_hash": release_attestation_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_release_attestation_hash": (
                execution_capsule_authz_release_attestation_hash
            ),
            "execution_capsule_authz_operator_decision_hash": operator_decision_hash,
            "release_attestation_hash": release_attestation_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "release_attestation_count": 1 if release_attestation_hash else 0,
            "attestation_request_count": 1 if attestation_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_release_seal_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_release_attestation: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    release_attestation_hash = str(
        execution_capsule_authz_release_attestation.get(
            "execution_capsule_authz_release_attestation_hash", ""
        )
    ).strip()
    expected_release_attestation_hash = str(
        payload.get("expected_execution_capsule_authz_release_attestation_hash", "")
    ).strip()
    seal_payload = (
        payload.get("manual_test_execution_capsule_authz_release_seal")
        if isinstance(
            payload.get("manual_test_execution_capsule_authz_release_seal"), dict
        )
        else {}
    )
    supplied_release_attestation_hash = str(
        seal_payload.get("execution_capsule_authz_release_attestation_hash", "")
    ).strip()
    seal_material = (
        seal_payload.get("seal_material")
        if isinstance(seal_payload.get("seal_material"), dict)
        else {}
    )
    seal_material_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_SEAL_VERSION
                ),
                "seal_decision": str(
                    seal_material.get("seal_decision", "")
                ).strip(),
                "seal_reason_code": str(
                    seal_material.get("seal_reason_code", "")
                ).strip(),
                "sealed_at": str(seal_material.get("sealed_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            seal_material.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(seal_material.get("operator_ref", "")).strip()
                else "",
            }
        )
        if seal_material
        else ""
    )
    seal_requested = seal_payload.get("seal_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_SEAL_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_SEAL_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_authz_release_attestation.get("status", ""))
        == "blocked"
        and str(execution_capsule_authz_release_attestation.get("reason", ""))
        == "execution_capsule_authz_release_attestation_execution_closed"
        and bool(release_attestation_hash)
        and _coerce_int(
            execution_capsule_authz_release_attestation.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_release_attestation_hash)
        and expected_release_attestation_hash == release_attestation_hash,
        bool(seal_payload),
        bool(supplied_release_attestation_hash)
        and supplied_release_attestation_hash == release_attestation_hash,
        bool(seal_material_hash),
        seal_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            release_attestation_hash,
            seal_material_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_authz_release_attestation_missing_or_mismatched"
    elif not expected_release_attestation_hash:
        reason = "expected_execution_capsule_authz_release_attestation_hash_required"
    elif expected_release_attestation_hash != release_attestation_hash:
        reason = "execution_capsule_authz_release_attestation_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_release_seal_required"
    elif not component_checks[3]:
        reason = "execution_capsule_authz_release_seal_attestation_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_authz_release_seal_material_required"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_release_seal_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_authz_release_seal_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_authz_release_seal_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_authz_release_seal_execution_closed"

    execution_capsule_authz_release_seal_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_release_seal_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_SEAL_VERSION
                ),
                "execution_capsule_authz_release_attestation_hash": (
                    release_attestation_hash
                ),
                "seal_material_hash": seal_material_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_release_seal_hash": (
                execution_capsule_authz_release_seal_hash
            ),
            "execution_capsule_authz_release_attestation_hash": (
                release_attestation_hash
            ),
            "seal_material_hash": seal_material_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "seal_material_count": 1 if seal_material_hash else 0,
            "seal_request_count": 1 if seal_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authorization_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_release_seal: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    release_seal_hash = str(
        execution_capsule_authz_release_seal.get(
            "execution_capsule_authz_release_seal_hash", ""
        )
    ).strip()
    expected_release_seal_hash = str(
        payload.get("expected_execution_capsule_authz_release_seal_hash", "")
    ).strip()
    authorization_payload = (
        payload.get("manual_test_execution_capsule_authz_final_authorization")
        if isinstance(
            payload.get("manual_test_execution_capsule_authz_final_authorization"),
            dict,
        )
        else {}
    )
    supplied_release_seal_hash = str(
        authorization_payload.get("execution_capsule_authz_release_seal_hash", "")
    ).strip()
    final_authorization = (
        authorization_payload.get("final_authorization")
        if isinstance(authorization_payload.get("final_authorization"), dict)
        else {}
    )
    final_authz_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHORIZATION_VERSION
                ),
                "authorization_decision": str(
                    final_authorization.get("authorization_decision", "")
                ).strip(),
                "authorization_reason_code": str(
                    final_authorization.get("authorization_reason_code", "")
                ).strip(),
                "authorized_at": str(
                    final_authorization.get("authorized_at", "")
                ).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            final_authorization.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(final_authorization.get("operator_ref", "")).strip()
                else "",
            }
        )
        if final_authorization
        else ""
    )
    authz_requested = authorization_payload.get("authorization_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHORIZATION_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHORIZATION_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_authz_release_seal.get("status", "")) == "blocked"
        and str(execution_capsule_authz_release_seal.get("reason", ""))
        == "execution_capsule_authz_release_seal_execution_closed"
        and bool(release_seal_hash)
        and _coerce_int(
            execution_capsule_authz_release_seal.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_release_seal_hash)
        and expected_release_seal_hash == release_seal_hash,
        bool(authorization_payload),
        bool(supplied_release_seal_hash)
        and supplied_release_seal_hash == release_seal_hash,
        bool(final_authz_hash),
        authz_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            release_seal_hash,
            final_authz_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_authz_release_seal_missing_or_mismatched"
    elif not expected_release_seal_hash:
        reason = "expected_execution_capsule_authz_release_seal_hash_required"
    elif expected_release_seal_hash != release_seal_hash:
        reason = "execution_capsule_authz_release_seal_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_final_authz_required"
    elif not component_checks[3]:
        reason = "execution_capsule_authz_final_authz_seal_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_authz_final_authz_required"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_final_authz_request_required"
    elif not component_checks[6]:
        reason = "execution_capsule_authz_final_authz_claim_boundary_mismatch"
    elif not component_checks[7]:
        reason = "execution_capsule_authz_final_authz_no_call_counters_mismatch"
    else:
        reason = "execution_capsule_authz_final_authz_execution_closed"

    execution_capsule_authz_final_authz_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_final_authz_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHORIZATION_VERSION
                ),
                "execution_capsule_authz_release_seal_hash": release_seal_hash,
                "final_authz_hash": final_authz_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_hash": (
                execution_capsule_authz_final_authz_hash
            ),
            "execution_capsule_authz_release_seal_hash": release_seal_hash,
            "final_authz_hash": final_authz_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "final_authz_count": 1 if final_authz_hash else 0,
            "authz_request_count": 1 if authz_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_export_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_final_authz: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    final_authz_hash = str(
        execution_capsule_authz_final_authz.get(
            "execution_capsule_authz_final_authz_hash", ""
        )
    ).strip()
    expected_final_authz_hash = str(
        payload.get("expected_execution_capsule_authz_final_authz_hash", "")
    ).strip()
    export_payload = (
        payload.get("manual_test_execution_capsule_authz_final_authz_export")
        if isinstance(
            payload.get("manual_test_execution_capsule_authz_final_authz_export"),
            dict,
        )
        else {}
    )
    supplied_final_authz_hash = str(
        export_payload.get("execution_capsule_authz_final_authz_hash", "")
    ).strip()
    export_metadata = (
        export_payload.get("export_metadata")
        if isinstance(export_payload.get("export_metadata"), dict)
        else {}
    )
    export_metadata_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_EXPORT_VERSION
                ),
                "export_kind": str(export_metadata.get("export_kind", "")).strip(),
                "export_reason_code": str(
                    export_metadata.get("export_reason_code", "")
                ).strip(),
                "exported_at": str(export_metadata.get("exported_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            export_metadata.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(export_metadata.get("operator_ref", "")).strip()
                else "",
            }
        )
        if export_metadata
        else ""
    )
    export_requested = export_payload.get("export_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_EXPORT_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_EXPORT_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_authz_final_authz.get("status", "")) == "blocked"
        and str(execution_capsule_authz_final_authz.get("reason", ""))
        == "execution_capsule_authz_final_authz_execution_closed"
        and bool(final_authz_hash)
        and _coerce_int(
            execution_capsule_authz_final_authz.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_final_authz_hash)
        and expected_final_authz_hash == final_authz_hash,
        bool(export_payload),
        bool(supplied_final_authz_hash)
        and supplied_final_authz_hash == final_authz_hash,
        bool(export_metadata_hash),
        export_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            final_authz_hash,
            export_metadata_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_authz_final_authz_missing_or_mismatched"
    elif not expected_final_authz_hash:
        reason = "expected_execution_capsule_authz_final_authz_hash_required"
    elif expected_final_authz_hash != final_authz_hash:
        reason = "execution_capsule_authz_final_authz_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_final_authz_export_required"
    elif not component_checks[3]:
        reason = "execution_capsule_authz_final_authz_export_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_authz_final_authz_export_metadata_required"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_final_authz_export_request_required"
    elif not component_checks[6]:
        reason = (
            "execution_capsule_authz_final_authz_export_claim_boundary_mismatch"
        )
    elif not component_checks[7]:
        reason = (
            "execution_capsule_authz_final_authz_export_no_call_counters_mismatch"
        )
    else:
        reason = "execution_capsule_authz_final_authz_export_execution_closed"

    execution_capsule_authz_final_authz_export_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_final_authz_export_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_EXPORT_VERSION
                ),
                "execution_capsule_authz_final_authz_hash": final_authz_hash,
                "export_metadata_hash": export_metadata_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_export_hash": (
                execution_capsule_authz_final_authz_export_hash
            ),
            "execution_capsule_authz_final_authz_hash": final_authz_hash,
            "export_metadata_hash": export_metadata_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "export_count": (
                1 if execution_capsule_authz_final_authz_export_hash else 0
            ),
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "export_metadata_count": 1 if export_metadata_hash else 0,
            "export_request_count": 1 if export_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_export_read_model_projection(
    export_projection: JsonDict,
) -> JsonDict:
    if (
        str(export_projection.get("status", "")) == "blocked"
        and str(export_projection.get("reason", ""))
        == "execution_capsule_authz_final_authz_export_execution_closed"
        and str(
            export_projection.get(
                "execution_capsule_authz_final_authz_export_hash", ""
            )
        ).strip()
    ):
        return _safe_public_payload(
            {
                "status": "available",
                "reason": (
                    "execution_capsule_authz_final_authz_export_read_model_available"
                ),
                "latest_execution_capsule_authz_final_authz_export_hash": str(
                    export_projection.get(
                        "execution_capsule_authz_final_authz_export_hash", ""
                    )
                ),
                "counts": {
                    "execution_capsule_authz_final_authz_export_count": int(
                        export_projection.get("export_count", 0)
                    ),
                    "component_count": int(
                        export_projection.get("component_count", 0)
                    ),
                    "execution_permission_count": int(
                        export_projection.get("execution_permission_count", 0)
                    ),
                },
            }
        )
    return (
        _manual_provider_test_execution_capsule_authz_final_authz_export_read_model_blocked(
            "execution_capsule_authz_final_authz_export_not_available"
        )
    )


def _manual_provider_test_execution_capsule_authz_final_authz_handoff_packet_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_final_authz_export: JsonDict,
    execution_capsule_authz_final_authz_export_read_model: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    export_hash = str(
        execution_capsule_authz_final_authz_export.get(
            "execution_capsule_authz_final_authz_export_hash", ""
        )
    ).strip()
    expected_export_hash = str(
        payload.get("expected_execution_capsule_authz_final_authz_export_hash", "")
    ).strip()
    handoff_payload = (
        payload.get("manual_test_execution_capsule_authz_final_authz_handoff_packet")
        if isinstance(
            payload.get(
                "manual_test_execution_capsule_authz_final_authz_handoff_packet"
            ),
            dict,
        )
        else {}
    )
    supplied_export_hash = str(
        handoff_payload.get("execution_capsule_authz_final_authz_export_hash", "")
    ).strip()
    read_model_hash = str(
        execution_capsule_authz_final_authz_export_read_model.get(
            "latest_execution_capsule_authz_final_authz_export_hash", ""
        )
    ).strip()
    handoff_requested = handoff_payload.get("handoff_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_HANDOFF_PACKET_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_HANDOFF_PACKET_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    read_model_available = (
        str(execution_capsule_authz_final_authz_export_read_model.get("status", ""))
        == "available"
        and str(
            execution_capsule_authz_final_authz_export_read_model.get("reason", "")
        )
        == "execution_capsule_authz_final_authz_export_read_model_available"
        and bool(read_model_hash)
        and read_model_hash == export_hash
        and _coerce_int(
            execution_capsule_authz_final_authz_export_read_model.get(
                "counts", {}
            ).get("execution_permission_count", 0)
            if isinstance(
                execution_capsule_authz_final_authz_export_read_model.get(
                    "counts", {}
                ),
                dict,
            )
            else 0
        )
        == 0
    )
    component_checks = [
        str(execution_capsule_authz_final_authz_export.get("status", ""))
        == "blocked"
        and str(execution_capsule_authz_final_authz_export.get("reason", ""))
        == "execution_capsule_authz_final_authz_export_execution_closed"
        and bool(export_hash)
        and _coerce_int(
            execution_capsule_authz_final_authz_export.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_export_hash) and expected_export_hash == export_hash,
        bool(handoff_payload),
        bool(supplied_export_hash) and supplied_export_hash == export_hash,
        read_model_available,
        handoff_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            export_hash,
            read_model_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_authz_final_authz_export_missing_or_mismatched"
    elif not expected_export_hash:
        reason = "expected_execution_capsule_authz_final_authz_export_hash_required"
    elif expected_export_hash != export_hash:
        reason = "execution_capsule_authz_final_authz_export_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_final_authz_handoff_packet_required"
    elif not component_checks[3]:
        reason = "execution_capsule_authz_final_authz_handoff_packet_hash_mismatch"
    elif not component_checks[4]:
        reason = (
            "execution_capsule_authz_final_authz_export_read_model_missing_or_mismatched"
        )
    elif not component_checks[5]:
        reason = "execution_capsule_authz_final_authz_handoff_packet_request_required"
    elif not component_checks[6]:
        reason = (
            "execution_capsule_authz_final_authz_handoff_packet_claim_boundary_mismatch"
        )
    elif not component_checks[7]:
        reason = (
            "execution_capsule_authz_final_authz_handoff_packet_no_call_counters_mismatch"
        )
    else:
        reason = "execution_capsule_authz_final_authz_handoff_packet_execution_closed"

    handoff_packet_hash = ""
    if mismatch_count == 0:
        handoff_packet_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_HANDOFF_PACKET_VERSION
                ),
                "execution_capsule_authz_final_authz_export_hash": export_hash,
                "execution_capsule_authz_final_authz_export_read_model_hash": (
                    read_model_hash
                ),
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_handoff_packet_hash": (
                handoff_packet_hash
            ),
            "execution_capsule_authz_final_authz_export_hash": export_hash,
            "execution_capsule_authz_final_authz_export_read_model_hash": (
                read_model_hash
            ),
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "packet_count": 1 if handoff_packet_hash else 0,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "export_read_model_count": 1 if read_model_available else 0,
            "handoff_request_count": 1 if handoff_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_operator_review_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_final_authz_handoff_packet: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    handoff_packet_hash = str(
        execution_capsule_authz_final_authz_handoff_packet.get(
            "execution_capsule_authz_final_authz_handoff_packet_hash", ""
        )
    ).strip()
    expected_handoff_packet_hash = str(
        payload.get(
            "expected_execution_capsule_authz_final_authz_handoff_packet_hash", ""
        )
    ).strip()
    review_payload = (
        payload.get("manual_test_execution_capsule_authz_final_authz_operator_review")
        if isinstance(
            payload.get(
                "manual_test_execution_capsule_authz_final_authz_operator_review"
            ),
            dict,
        )
        else {}
    )
    supplied_handoff_packet_hash = str(
        review_payload.get(
            "execution_capsule_authz_final_authz_handoff_packet_hash", ""
        )
    ).strip()
    operator_review = (
        review_payload.get("operator_review")
        if isinstance(review_payload.get("operator_review"), dict)
        else {}
    )
    operator_review_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_REVIEW_VERSION
                ),
                "review_decision": str(
                    operator_review.get("review_decision", "")
                ).strip(),
                "review_reason_code": str(
                    operator_review.get("review_reason_code", "")
                ).strip(),
                "reviewed_at": str(operator_review.get("reviewed_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            operator_review.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(operator_review.get("operator_ref", "")).strip()
                else "",
            }
        )
        if operator_review
        else ""
    )
    review_requested = review_payload.get("review_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_REVIEW_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_REVIEW_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_authz_final_authz_handoff_packet.get("status", ""))
        == "blocked"
        and str(
            execution_capsule_authz_final_authz_handoff_packet.get("reason", "")
        )
        == "execution_capsule_authz_final_authz_handoff_packet_execution_closed"
        and bool(handoff_packet_hash)
        and _coerce_int(
            execution_capsule_authz_final_authz_handoff_packet.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_handoff_packet_hash)
        and expected_handoff_packet_hash == handoff_packet_hash,
        bool(review_payload),
        bool(supplied_handoff_packet_hash)
        and supplied_handoff_packet_hash == handoff_packet_hash,
        bool(operator_review_hash),
        review_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            handoff_packet_hash,
            operator_review_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = (
            "execution_capsule_authz_final_authz_handoff_packet_missing_or_mismatched"
        )
    elif not expected_handoff_packet_hash:
        reason = (
            "expected_execution_capsule_authz_final_authz_handoff_packet_hash_required"
        )
    elif expected_handoff_packet_hash != handoff_packet_hash:
        reason = "execution_capsule_authz_final_authz_handoff_packet_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_final_authz_operator_review_required"
    elif not component_checks[3]:
        reason = (
            "execution_capsule_authz_final_authz_operator_review_handoff_hash_mismatch"
        )
    elif not component_checks[4]:
        reason = "execution_capsule_authz_final_authz_operator_review_required"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_final_authz_operator_review_request_required"
    elif not component_checks[6]:
        reason = (
            "execution_capsule_authz_final_authz_operator_review_claim_boundary_mismatch"
        )
    elif not component_checks[7]:
        reason = (
            "execution_capsule_authz_final_authz_operator_review_no_call_counters_mismatch"
        )
    else:
        reason = "execution_capsule_authz_final_authz_operator_review_execution_closed"

    execution_capsule_authz_final_authz_operator_review_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_final_authz_operator_review_hash = (
            stable_contract_hash(
                {
                    "projection_version": (
                        MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_REVIEW_VERSION
                    ),
                    "execution_capsule_authz_final_authz_handoff_packet_hash": (
                        handoff_packet_hash
                    ),
                    "operator_review_hash": operator_review_hash,
                    "claim_boundary_hash": claim_boundary_hash,
                    "no_call_counters_hash": no_call_counters_hash,
                    "component_count": component_count,
                    "execution_permission": "closed",
                }
            )
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_operator_review_hash": (
                execution_capsule_authz_final_authz_operator_review_hash
            ),
            "execution_capsule_authz_final_authz_handoff_packet_hash": (
                handoff_packet_hash
            ),
            "operator_review_hash": operator_review_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "operator_review_count": 1 if operator_review_hash else 0,
            "review_request_count": 1 if review_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_operator_decision_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_final_authz_operator_review: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    operator_review_hash = str(
        execution_capsule_authz_final_authz_operator_review.get(
            "execution_capsule_authz_final_authz_operator_review_hash", ""
        )
    ).strip()
    expected_operator_review_hash = str(
        payload.get(
            "expected_execution_capsule_authz_final_authz_operator_review_hash", ""
        )
    ).strip()
    decision_payload = (
        payload.get("manual_test_execution_capsule_authz_final_authz_operator_decision")
        if isinstance(
            payload.get(
                "manual_test_execution_capsule_authz_final_authz_operator_decision"
            ),
            dict,
        )
        else {}
    )
    supplied_operator_review_hash = str(
        decision_payload.get(
            "execution_capsule_authz_final_authz_operator_review_hash", ""
        )
    ).strip()
    operator_decision = (
        decision_payload.get("operator_decision")
        if isinstance(decision_payload.get("operator_decision"), dict)
        else {}
    )
    operator_decision_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_DECISION_VERSION
                ),
                "decision": str(operator_decision.get("decision", "")).strip(),
                "decision_reason_code": str(
                    operator_decision.get("decision_reason_code", "")
                ).strip(),
                "decided_at": str(operator_decision.get("decided_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            operator_decision.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(operator_decision.get("operator_ref", "")).strip()
                else "",
            }
        )
        if operator_decision
        else ""
    )
    decision_requested = decision_payload.get("decision_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_DECISION_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_DECISION_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_authz_final_authz_operator_review.get("status", ""))
        == "blocked"
        and str(
            execution_capsule_authz_final_authz_operator_review.get("reason", "")
        )
        == "execution_capsule_authz_final_authz_operator_review_execution_closed"
        and bool(operator_review_hash)
        and _coerce_int(
            execution_capsule_authz_final_authz_operator_review.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_operator_review_hash)
        and expected_operator_review_hash == operator_review_hash,
        bool(decision_payload),
        bool(supplied_operator_review_hash)
        and supplied_operator_review_hash == operator_review_hash,
        bool(operator_decision_hash),
        decision_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            operator_review_hash,
            operator_decision_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = (
            "execution_capsule_authz_final_authz_operator_review_missing_or_mismatched"
        )
    elif not expected_operator_review_hash:
        reason = (
            "expected_execution_capsule_authz_final_authz_operator_review_hash_required"
        )
    elif expected_operator_review_hash != operator_review_hash:
        reason = "execution_capsule_authz_final_authz_operator_review_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_final_authz_operator_decision_required"
    elif not component_checks[3]:
        reason = (
            "execution_capsule_authz_final_authz_operator_decision_review_hash_mismatch"
        )
    elif not component_checks[4]:
        reason = "execution_capsule_authz_final_authz_operator_decision_required"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_final_authz_operator_decision_request_required"
    elif not component_checks[6]:
        reason = (
            "execution_capsule_authz_final_authz_operator_decision_claim_boundary_mismatch"
        )
    elif not component_checks[7]:
        reason = (
            "execution_capsule_authz_final_authz_operator_decision_no_call_counters_mismatch"
        )
    else:
        reason = "execution_capsule_authz_final_authz_operator_decision_execution_closed"

    execution_capsule_authz_final_authz_operator_decision_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_final_authz_operator_decision_hash = (
            stable_contract_hash(
                {
                    "projection_version": (
                        MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_DECISION_VERSION
                    ),
                    "execution_capsule_authz_final_authz_operator_review_hash": (
                        operator_review_hash
                    ),
                    "operator_decision_hash": operator_decision_hash,
                    "claim_boundary_hash": claim_boundary_hash,
                    "no_call_counters_hash": no_call_counters_hash,
                    "component_count": component_count,
                    "execution_permission": "closed",
                }
            )
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_operator_decision_hash": (
                execution_capsule_authz_final_authz_operator_decision_hash
            ),
            "execution_capsule_authz_final_authz_operator_review_hash": (
                operator_review_hash
            ),
            "operator_decision_hash": operator_decision_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "operator_decision_count": 1 if operator_decision_hash else 0,
            "decision_request_count": 1 if decision_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_release_attestation_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_final_authz_operator_decision: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    operator_decision_hash = str(
        execution_capsule_authz_final_authz_operator_decision.get(
            "execution_capsule_authz_final_authz_operator_decision_hash", ""
        )
    ).strip()
    expected_operator_decision_hash = str(
        payload.get(
            "expected_execution_capsule_authz_final_authz_operator_decision_hash", ""
        )
    ).strip()
    attestation_payload = (
        payload.get("manual_test_execution_capsule_authz_final_authz_release_attestation")
        if isinstance(
            payload.get(
                "manual_test_execution_capsule_authz_final_authz_release_attestation"
            ),
            dict,
        )
        else {}
    )
    supplied_operator_decision_hash = str(
        attestation_payload.get(
            "execution_capsule_authz_final_authz_operator_decision_hash", ""
        )
    ).strip()
    release_attestation = (
        attestation_payload.get("release_attestation")
        if isinstance(attestation_payload.get("release_attestation"), dict)
        else {}
    )
    release_attestation_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_ATTESTATION_VERSION
                ),
                "attestation": str(
                    release_attestation.get("attestation", "")
                ).strip(),
                "attestation_reason_code": str(
                    release_attestation.get("attestation_reason_code", "")
                ).strip(),
                "attested_at": str(
                    release_attestation.get("attested_at", "")
                ).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            release_attestation.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(release_attestation.get("operator_ref", "")).strip()
                else "",
            }
        )
        if release_attestation
        else ""
    )
    attestation_requested = attestation_payload.get("attestation_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_ATTESTATION_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_ATTESTATION_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_authz_final_authz_operator_decision.get("status", ""))
        == "blocked"
        and str(
            execution_capsule_authz_final_authz_operator_decision.get("reason", "")
        )
        == "execution_capsule_authz_final_authz_operator_decision_execution_closed"
        and bool(operator_decision_hash)
        and _coerce_int(
            execution_capsule_authz_final_authz_operator_decision.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_operator_decision_hash)
        and expected_operator_decision_hash == operator_decision_hash,
        bool(attestation_payload),
        bool(supplied_operator_decision_hash)
        and supplied_operator_decision_hash == operator_decision_hash,
        bool(release_attestation_hash),
        attestation_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            operator_decision_hash,
            release_attestation_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = (
            "execution_capsule_authz_final_authz_operator_decision_missing_or_mismatched"
        )
    elif not expected_operator_decision_hash:
        reason = (
            "expected_execution_capsule_authz_final_authz_operator_decision_hash_required"
        )
    elif expected_operator_decision_hash != operator_decision_hash:
        reason = "execution_capsule_authz_final_authz_operator_decision_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_final_authz_release_attestation_required"
    elif not component_checks[3]:
        reason = (
            "execution_capsule_authz_final_authz_release_attestation_decision_hash_mismatch"
        )
    elif not component_checks[4]:
        reason = "execution_capsule_authz_final_authz_release_attestation_required"
    elif not component_checks[5]:
        reason = (
            "execution_capsule_authz_final_authz_release_attestation_request_required"
        )
    elif not component_checks[6]:
        reason = (
            "execution_capsule_authz_final_authz_release_attestation_claim_boundary_mismatch"
        )
    elif not component_checks[7]:
        reason = (
            "execution_capsule_authz_final_authz_release_attestation_no_call_counters_mismatch"
        )
    else:
        reason = (
            "execution_capsule_authz_final_authz_release_attestation_execution_closed"
        )

    execution_capsule_authz_final_authz_release_attestation_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_final_authz_release_attestation_hash = (
            stable_contract_hash(
                {
                    "projection_version": (
                        MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_ATTESTATION_VERSION
                    ),
                    "execution_capsule_authz_final_authz_operator_decision_hash": (
                        operator_decision_hash
                    ),
                    "release_attestation_hash": release_attestation_hash,
                    "claim_boundary_hash": claim_boundary_hash,
                    "no_call_counters_hash": no_call_counters_hash,
                    "component_count": component_count,
                    "execution_permission": "closed",
                }
            )
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_release_attestation_hash": (
                execution_capsule_authz_final_authz_release_attestation_hash
            ),
            "execution_capsule_authz_final_authz_operator_decision_hash": (
                operator_decision_hash
            ),
            "release_attestation_hash": release_attestation_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "release_attestation_count": 1 if release_attestation_hash else 0,
            "attestation_request_count": 1 if attestation_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_release_seal_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_final_authz_release_attestation: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    release_attestation_hash = str(
        execution_capsule_authz_final_authz_release_attestation.get(
            "execution_capsule_authz_final_authz_release_attestation_hash", ""
        )
    ).strip()
    expected_release_attestation_hash = str(
        payload.get(
            "expected_execution_capsule_authz_final_authz_release_attestation_hash",
            "",
        )
    ).strip()
    seal_payload = (
        payload.get("manual_test_execution_capsule_authz_final_authz_release_seal")
        if isinstance(
            payload.get("manual_test_execution_capsule_authz_final_authz_release_seal"),
            dict,
        )
        else {}
    )
    supplied_release_attestation_hash = str(
        seal_payload.get(
            "execution_capsule_authz_final_authz_release_attestation_hash", ""
        )
    ).strip()
    seal_material = (
        seal_payload.get("seal_material")
        if isinstance(seal_payload.get("seal_material"), dict)
        else {}
    )
    seal_material_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_SEAL_VERSION
                ),
                "seal_decision": str(
                    seal_material.get("seal_decision", "")
                ).strip(),
                "seal_reason_code": str(
                    seal_material.get("seal_reason_code", "")
                ).strip(),
                "sealed_at": str(seal_material.get("sealed_at", "")).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            seal_material.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(seal_material.get("operator_ref", "")).strip()
                else "",
            }
        )
        if seal_material
        else ""
    )
    seal_requested = seal_payload.get("seal_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_SEAL_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_SEAL_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_authz_final_authz_release_attestation.get("status", ""))
        == "blocked"
        and str(
            execution_capsule_authz_final_authz_release_attestation.get(
                "reason", ""
            )
        )
        == "execution_capsule_authz_final_authz_release_attestation_execution_closed"
        and bool(release_attestation_hash)
        and _coerce_int(
            execution_capsule_authz_final_authz_release_attestation.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_release_attestation_hash)
        and expected_release_attestation_hash == release_attestation_hash,
        bool(seal_payload),
        bool(supplied_release_attestation_hash)
        and supplied_release_attestation_hash == release_attestation_hash,
        bool(seal_material_hash),
        seal_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            release_attestation_hash,
            seal_material_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = (
            "execution_capsule_authz_final_authz_release_attestation_missing_or_mismatched"
        )
    elif not expected_release_attestation_hash:
        reason = (
            "expected_execution_capsule_authz_final_authz_release_attestation_hash_required"
        )
    elif expected_release_attestation_hash != release_attestation_hash:
        reason = (
            "execution_capsule_authz_final_authz_release_attestation_hash_mismatch"
        )
    elif not component_checks[2]:
        reason = "execution_capsule_authz_final_authz_release_seal_required"
    elif not component_checks[3]:
        reason = (
            "execution_capsule_authz_final_authz_release_seal_attestation_hash_mismatch"
        )
    elif not component_checks[4]:
        reason = "execution_capsule_authz_final_authz_release_seal_material_required"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_final_authz_release_seal_request_required"
    elif not component_checks[6]:
        reason = (
            "execution_capsule_authz_final_authz_release_seal_claim_boundary_mismatch"
        )
    elif not component_checks[7]:
        reason = (
            "execution_capsule_authz_final_authz_release_seal_no_call_counters_mismatch"
        )
    else:
        reason = "execution_capsule_authz_final_authz_release_seal_execution_closed"

    execution_capsule_authz_final_authz_release_seal_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_final_authz_release_seal_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_SEAL_VERSION
                ),
                "execution_capsule_authz_final_authz_release_attestation_hash": (
                    release_attestation_hash
                ),
                "seal_material_hash": seal_material_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_release_seal_hash": (
                execution_capsule_authz_final_authz_release_seal_hash
            ),
            "execution_capsule_authz_final_authz_release_attestation_hash": (
                release_attestation_hash
            ),
            "seal_material_hash": seal_material_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "seal_material_count": 1 if seal_material_hash else 0,
            "seal_request_count": 1 if seal_requested else 0,
            "execution_permission_count": 0,
        }
    )


def _manual_provider_test_execution_capsule_authz_final_authz_final_authorization_projection(
    *,
    payload: dict[str, Any],
    execution_capsule_authz_final_authz_release_seal: JsonDict,
    execution_boundary: JsonDict,
) -> JsonDict:
    release_seal_hash = str(
        execution_capsule_authz_final_authz_release_seal.get(
            "execution_capsule_authz_final_authz_release_seal_hash", ""
        )
    ).strip()
    expected_release_seal_hash = str(
        payload.get(
            "expected_execution_capsule_authz_final_authz_release_seal_hash",
            "",
        )
    ).strip()
    authorization_payload = (
        payload.get(
            "manual_test_execution_capsule_authz_final_authz_final_authorization"
        )
        if isinstance(
            payload.get(
                "manual_test_execution_capsule_authz_final_authz_final_authorization"
            ),
            dict,
        )
        else {}
    )
    supplied_release_seal_hash = str(
        authorization_payload.get(
            "execution_capsule_authz_final_authz_release_seal_hash", ""
        )
    ).strip()
    final_authorization = (
        authorization_payload.get("final_authorization")
        if isinstance(authorization_payload.get("final_authorization"), dict)
        else {}
    )
    final_authz_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_FINAL_AUTHORIZATION_VERSION
                ),
                "authorization_decision": str(
                    final_authorization.get("authorization_decision", "")
                ).strip(),
                "authorization_reason_code": str(
                    final_authorization.get("authorization_reason_code", "")
                ).strip(),
                "authorized_at": str(
                    final_authorization.get("authorized_at", "")
                ).strip(),
                "operator_ref_hash": stable_contract_hash(
                    {
                        "operator_ref": str(
                            final_authorization.get("operator_ref", "")
                        ).strip()
                    }
                )
                if str(final_authorization.get("operator_ref", "")).strip()
                else "",
            }
        )
        if final_authorization
        else ""
    )
    authz_requested = authorization_payload.get("authorization_requested") is True
    claim_boundary = _provider_envelope_claim_boundary_projection()
    claim_boundary_closed = (
        claim_boundary.get("external_provider_outcome") is False
        and claim_boundary.get("target_runtime_outcome") is False
        and claim_boundary.get("production_trust_claim") is False
    )
    claim_boundary_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_FINAL_AUTHORIZATION_VERSION
                ),
                "claim_boundary": claim_boundary,
            }
        )
        if claim_boundary_closed
        else ""
    )
    no_call_counters = _executor_preflight_no_call_counters(execution_boundary)
    no_call_counters_closed = all(value == 0 for value in no_call_counters.values())
    no_call_counters_hash = (
        stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_FINAL_AUTHORIZATION_VERSION
                ),
                "no_call_counters": no_call_counters,
            }
        )
        if no_call_counters_closed
        else ""
    )
    component_checks = [
        str(execution_capsule_authz_final_authz_release_seal.get("status", ""))
        == "blocked"
        and str(execution_capsule_authz_final_authz_release_seal.get("reason", ""))
        == "execution_capsule_authz_final_authz_release_seal_execution_closed"
        and bool(release_seal_hash)
        and _coerce_int(
            execution_capsule_authz_final_authz_release_seal.get(
                "execution_permission_count", 0
            )
        )
        == 0,
        bool(expected_release_seal_hash)
        and expected_release_seal_hash == release_seal_hash,
        bool(authorization_payload),
        bool(supplied_release_seal_hash)
        and supplied_release_seal_hash == release_seal_hash,
        bool(final_authz_hash),
        authz_requested,
        claim_boundary_closed,
        no_call_counters_closed,
    ]
    component_count = len(component_checks)
    passed_component_count = sum(1 for check in component_checks if check)
    mismatch_count = component_count - passed_component_count
    component_hash_count = sum(
        1
        for value in (
            release_seal_hash,
            final_authz_hash,
            claim_boundary_hash,
            no_call_counters_hash,
        )
        if value
    )

    if not component_checks[0]:
        reason = "execution_capsule_authz_final_authz_release_seal_missing_or_mismatched"
    elif not expected_release_seal_hash:
        reason = (
            "expected_execution_capsule_authz_final_authz_release_seal_hash_required"
        )
    elif expected_release_seal_hash != release_seal_hash:
        reason = "execution_capsule_authz_final_authz_release_seal_hash_mismatch"
    elif not component_checks[2]:
        reason = "execution_capsule_authz_final_authz_final_authz_required"
    elif not component_checks[3]:
        reason = "execution_capsule_authz_final_authz_final_authz_seal_hash_mismatch"
    elif not component_checks[4]:
        reason = "execution_capsule_authz_final_authz_final_authz_required"
    elif not component_checks[5]:
        reason = "execution_capsule_authz_final_authz_final_authz_request_required"
    elif not component_checks[6]:
        reason = (
            "execution_capsule_authz_final_authz_final_authz_claim_boundary_mismatch"
        )
    elif not component_checks[7]:
        reason = (
            "execution_capsule_authz_final_authz_final_authz_no_call_counters_mismatch"
        )
    else:
        reason = "execution_capsule_authz_final_authz_final_authz_execution_closed"

    execution_capsule_authz_final_authz_final_authz_hash = ""
    if mismatch_count == 0:
        execution_capsule_authz_final_authz_final_authz_hash = stable_contract_hash(
            {
                "projection_version": (
                    MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_FINAL_AUTHORIZATION_VERSION
                ),
                "execution_capsule_authz_final_authz_release_seal_hash": (
                    release_seal_hash
                ),
                "final_authz_hash": final_authz_hash,
                "claim_boundary_hash": claim_boundary_hash,
                "no_call_counters_hash": no_call_counters_hash,
                "component_count": component_count,
                "execution_permission": "closed",
            }
        )

    return _safe_public_payload(
        {
            "status": "blocked",
            "reason": reason,
            "execution_capsule_authz_final_authz_final_authz_hash": (
                execution_capsule_authz_final_authz_final_authz_hash
            ),
            "execution_capsule_authz_final_authz_release_seal_hash": (
                release_seal_hash
            ),
            "final_authz_hash": final_authz_hash,
            "claim_boundary_hash": claim_boundary_hash,
            "no_call_counters_hash": no_call_counters_hash,
            "component_count": component_count,
            "passed_component_count": passed_component_count,
            "mismatch_count": mismatch_count,
            "component_hash_count": component_hash_count,
            "no_call_counter_count": len(no_call_counters),
            "claim_boundary_check_count": 3,
            "final_authz_count": 1 if final_authz_hash else 0,
            "authz_request_count": 1 if authz_requested else 0,
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


def provider_manual_test_sealed_pre_execution_packet_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call sealed pre-execution packet projection."""
    request = _request_from_payload(payload)
    policy = _policy_from_payload(payload)
    live_open_decision = _ready_live_open_decision(payload, request.run_id)
    operator_policy_summary = _operator_policy_summary(
        request=request,
        policy=policy,
        live_open_decision=live_open_decision,
    )
    manual_provider_test_proposal = _manual_test_proposal_projection(
        payload=payload,
        request=request,
        policy=policy,
    )
    handoff_packet = provider_manual_test_handoff_packet_summary(payload)
    operator_opt_in = _manual_provider_test_operator_opt_in_projection(
        payload=payload,
        handoff_packet=handoff_packet,
    )
    return _manual_provider_test_sealed_packet_projection(
        payload=payload,
        operator_policy_summary=operator_policy_summary,
        manual_provider_test_proposal=manual_provider_test_proposal,
        handoff_packet=handoff_packet,
        operator_opt_in=operator_opt_in,
    )


def provider_manual_test_arming_record_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public no-call live execution arming record projection."""
    sealed_pre_execution_packet = provider_manual_test_sealed_pre_execution_packet_summary(
        payload
    )
    return _manual_provider_test_arming_record_projection(
        payload=payload,
        sealed_pre_execution_packet=sealed_pre_execution_packet,
    )


def provider_manual_test_release_proposal_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public no-call execution authorization release proposal projection."""
    arming_record = provider_manual_test_arming_record_summary(payload)
    return _manual_provider_test_release_proposal_projection(
        payload=payload,
        arming_record=arming_record,
    )


def provider_manual_test_final_release_packet_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public no-call final release packet projection."""
    release_proposal = provider_manual_test_release_proposal_summary(payload)
    return _manual_provider_test_final_release_packet_projection(
        payload=payload,
        release_proposal=release_proposal,
    )


def provider_manual_test_execution_switch_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public no-call disabled execution switch projection."""
    final_release_packet = provider_manual_test_final_release_packet_summary(payload)
    return _manual_provider_test_execution_switch_projection(
        payload=payload,
        final_release_packet=final_release_packet,
    )


def provider_manual_test_executor_preflight_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public no-call first-call executor preflight projection."""
    execution_switch = provider_manual_test_execution_switch_summary(payload)
    return _manual_provider_test_executor_preflight_projection(
        payload=payload,
        execution_switch=execution_switch,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_executor_dispatch_record_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call executor dispatch record projection."""
    executor_preflight = provider_manual_test_executor_preflight_summary(payload)
    return _manual_provider_test_executor_dispatch_record_projection(
        payload=payload,
        executor_preflight=executor_preflight,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_invocation_receipt_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call invocation receipt projection."""
    dispatch_record = provider_manual_test_executor_dispatch_record_summary(payload)
    return _manual_provider_test_invocation_receipt_projection(
        payload=payload,
        dispatch_record=dispatch_record,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_post_invocation_audit_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call post-invocation audit projection."""
    invocation_receipt = provider_manual_test_invocation_receipt_summary(payload)
    return _manual_provider_test_post_invocation_audit_projection(
        payload=payload,
        invocation_receipt=invocation_receipt,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_completion_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public no-call first-call completion summary projection."""
    post_invocation_audit = provider_manual_test_post_invocation_audit_summary(
        payload
    )
    return _manual_provider_test_completion_summary_projection(
        payload=payload,
        post_invocation_audit=post_invocation_audit,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_closeout_record_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call closeout record projection."""
    completion_summary = provider_manual_test_completion_summary(payload)
    return _manual_provider_test_closeout_record_projection(
        payload=payload,
        completion_summary=completion_summary,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_operator_handback_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call operator handback projection."""
    closeout_record = provider_manual_test_closeout_record_summary(payload)
    return _manual_provider_test_operator_handback_projection(
        payload=payload,
        closeout_record=closeout_record,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_operator_decision_packet_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call operator decision packet projection."""
    operator_handback = provider_manual_test_operator_handback_summary(payload)
    return _manual_provider_test_operator_decision_packet_projection(
        payload=payload,
        operator_handback=operator_handback,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_operator_release_attestation_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call operator release attestation projection."""
    operator_decision_packet = provider_manual_test_operator_decision_packet_summary(
        payload
    )
    return _manual_provider_test_operator_release_attestation_projection(
        payload=payload,
        operator_decision_packet=operator_decision_packet,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_release_authorization_seal_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call release authorization seal projection."""
    operator_release_attestation = provider_manual_test_operator_release_attestation_summary(
        payload
    )
    return _manual_provider_test_release_authorization_seal_projection(
        payload=payload,
        operator_release_attestation=operator_release_attestation,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_authorization_capsule_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule projection."""
    release_seal = provider_manual_test_release_authorization_seal_summary(payload)
    return _manual_provider_test_execution_authorization_capsule_projection(
        payload=payload,
        release_seal=release_seal,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_export_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule export projection."""
    execution_capsule = provider_manual_test_execution_authorization_capsule_summary(
        payload
    )
    return _manual_provider_test_execution_capsule_export_projection(
        payload=payload,
        execution_capsule=execution_capsule,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_handoff_packet_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule handoff packet."""
    execution_capsule_export = provider_manual_test_execution_capsule_export_summary(
        payload
    )
    execution_capsule_export_read_model = (
        _manual_provider_test_execution_capsule_export_read_model_projection(
            execution_capsule_export
        )
    )
    return _manual_provider_test_execution_capsule_handoff_packet_projection(
        payload=payload,
        execution_capsule_export=execution_capsule_export,
        execution_capsule_export_read_model=execution_capsule_export_read_model,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_operator_review_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule operator review."""
    handoff_packet = provider_manual_test_execution_capsule_handoff_packet_summary(
        payload
    )
    return _manual_provider_test_execution_capsule_operator_review_projection(
        payload=payload,
        execution_capsule_handoff_packet=handoff_packet,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_operator_decision_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule operator decision."""
    operator_review = provider_manual_test_execution_capsule_operator_review_summary(
        payload
    )
    return _manual_provider_test_execution_capsule_operator_decision_projection(
        payload=payload,
        execution_capsule_operator_review=operator_review,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_release_attestation_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule release attestation."""
    operator_decision = (
        provider_manual_test_execution_capsule_operator_decision_summary(payload)
    )
    return _manual_provider_test_execution_capsule_release_attestation_projection(
        payload=payload,
        execution_capsule_operator_decision=operator_decision,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_release_seal_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule release seal."""
    release_attestation = (
        provider_manual_test_execution_capsule_release_attestation_summary(payload)
    )
    return _manual_provider_test_execution_capsule_release_seal_projection(
        payload=payload,
        execution_capsule_release_attestation=release_attestation,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_final_authorization_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule final authorization."""
    release_seal = provider_manual_test_execution_capsule_release_seal_summary(payload)
    return _manual_provider_test_execution_capsule_final_authorization_projection(
        payload=payload,
        execution_capsule_release_seal=release_seal,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_authz_export_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz export."""
    final_authz = provider_manual_test_execution_capsule_final_authorization_summary(
        payload
    )
    return _manual_provider_test_execution_capsule_authz_export_projection(
        payload=payload,
        execution_capsule_final_authz=final_authz,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_authz_export_read_model_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz export read model."""
    authz_export = provider_manual_test_execution_capsule_authz_export_summary(payload)
    return _manual_provider_test_execution_capsule_authz_export_read_model_projection(
        authz_export
    )


def provider_manual_test_execution_capsule_authz_handoff_packet_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz handoff packet."""
    authz_export = provider_manual_test_execution_capsule_authz_export_summary(payload)
    authz_export_read_model = (
        _manual_provider_test_execution_capsule_authz_export_read_model_projection(
            authz_export
        )
    )
    return _manual_provider_test_execution_capsule_authz_handoff_packet_projection(
        payload=payload,
        execution_capsule_authz_export=authz_export,
        execution_capsule_authz_export_read_model=authz_export_read_model,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_authz_operator_review_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz operator review."""
    authz_handoff = (
        provider_manual_test_execution_capsule_authz_handoff_packet_summary(payload)
    )
    return _manual_provider_test_execution_capsule_authz_operator_review_projection(
        payload=payload,
        execution_capsule_authz_handoff_packet=authz_handoff,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_authz_operator_decision_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz operator decision."""
    authz_review = (
        provider_manual_test_execution_capsule_authz_operator_review_summary(payload)
    )
    return _manual_provider_test_execution_capsule_authz_operator_decision_projection(
        payload=payload,
        execution_capsule_authz_operator_review=authz_review,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_authz_release_attestation_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz release attestation."""
    authz_decision = (
        provider_manual_test_execution_capsule_authz_operator_decision_summary(
            payload
        )
    )
    return (
        _manual_provider_test_execution_capsule_authz_release_attestation_projection(
            payload=payload,
            execution_capsule_authz_operator_decision=authz_decision,
            execution_boundary=_zero_execution_boundary(),
        )
    )


def provider_manual_test_execution_capsule_authz_release_seal_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz release seal."""
    authz_attestation = (
        provider_manual_test_execution_capsule_authz_release_attestation_summary(
            payload
        )
    )
    return _manual_provider_test_execution_capsule_authz_release_seal_projection(
        payload=payload,
        execution_capsule_authz_release_attestation=authz_attestation,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_authz_final_authorization_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz final authorization."""
    authz_release_seal = (
        provider_manual_test_execution_capsule_authz_release_seal_summary(payload)
    )
    return _manual_provider_test_execution_capsule_authz_final_authorization_projection(
        payload=payload,
        execution_capsule_authz_release_seal=authz_release_seal,
        execution_boundary=_zero_execution_boundary(),
    )


def provider_manual_test_execution_capsule_authz_final_authz_export_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz final authz export."""
    authz_final_authz = (
        provider_manual_test_execution_capsule_authz_final_authorization_summary(
            payload
        )
    )
    return (
        _manual_provider_test_execution_capsule_authz_final_authz_export_projection(
            payload=payload,
            execution_capsule_authz_final_authz=authz_final_authz,
            execution_boundary=_zero_execution_boundary(),
        )
    )


def provider_manual_test_execution_capsule_authz_final_authz_export_read_model_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz final authz export read model."""
    authz_final_authz_export = (
        provider_manual_test_execution_capsule_authz_final_authz_export_summary(
            payload
        )
    )
    return (
        _manual_provider_test_execution_capsule_authz_final_authz_export_read_model_projection(
            authz_final_authz_export
        )
    )


def provider_manual_test_execution_capsule_authz_final_authz_handoff_packet_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz final authz handoff packet."""
    authz_final_authz_export = (
        provider_manual_test_execution_capsule_authz_final_authz_export_summary(
            payload
        )
    )
    authz_final_authz_export_read_model = (
        _manual_provider_test_execution_capsule_authz_final_authz_export_read_model_projection(
            authz_final_authz_export
        )
    )
    return (
        _manual_provider_test_execution_capsule_authz_final_authz_handoff_packet_projection(
            payload=payload,
            execution_capsule_authz_final_authz_export=(
                authz_final_authz_export
            ),
            execution_capsule_authz_final_authz_export_read_model=(
                authz_final_authz_export_read_model
            ),
            execution_boundary=_zero_execution_boundary(),
        )
    )


def provider_manual_test_execution_capsule_authz_final_authz_operator_review_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz final authz operator review."""
    authz_final_authz_handoff_packet = (
        provider_manual_test_execution_capsule_authz_final_authz_handoff_packet_summary(
            payload
        )
    )
    return (
        _manual_provider_test_execution_capsule_authz_final_authz_operator_review_projection(
            payload=payload,
            execution_capsule_authz_final_authz_handoff_packet=(
                authz_final_authz_handoff_packet
            ),
            execution_boundary=_zero_execution_boundary(),
        )
    )


def provider_manual_test_execution_capsule_authz_final_authz_operator_decision_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz final authz operator decision."""
    authz_final_authz_operator_review = (
        provider_manual_test_execution_capsule_authz_final_authz_operator_review_summary(
            payload
        )
    )
    return (
        _manual_provider_test_execution_capsule_authz_final_authz_operator_decision_projection(
            payload=payload,
            execution_capsule_authz_final_authz_operator_review=(
                authz_final_authz_operator_review
            ),
            execution_boundary=_zero_execution_boundary(),
        )
    )


def provider_manual_test_execution_capsule_authz_final_authz_release_attestation_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz final authz release attestation."""
    authz_final_authz_operator_decision = (
        provider_manual_test_execution_capsule_authz_final_authz_operator_decision_summary(
            payload
        )
    )
    return (
        _manual_provider_test_execution_capsule_authz_final_authz_release_attestation_projection(
            payload=payload,
            execution_capsule_authz_final_authz_operator_decision=(
                authz_final_authz_operator_decision
            ),
            execution_boundary=_zero_execution_boundary(),
        )
    )


def provider_manual_test_execution_capsule_authz_final_authz_release_seal_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz final authz release seal."""
    authz_final_authz_release_attestation = (
        provider_manual_test_execution_capsule_authz_final_authz_release_attestation_summary(
            payload
        )
    )
    return (
        _manual_provider_test_execution_capsule_authz_final_authz_release_seal_projection(
            payload=payload,
            execution_capsule_authz_final_authz_release_attestation=(
                authz_final_authz_release_attestation
            ),
            execution_boundary=_zero_execution_boundary(),
        )
    )


def provider_manual_test_execution_capsule_authz_final_authz_final_authorization_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the public no-call first-call execution capsule authz final authz final authorization."""
    authz_final_authz_release_seal = (
        provider_manual_test_execution_capsule_authz_final_authz_release_seal_summary(
            payload
        )
    )
    return (
        _manual_provider_test_execution_capsule_authz_final_authz_final_authorization_projection(
            payload=payload,
            execution_capsule_authz_final_authz_release_seal=(
                authz_final_authz_release_seal
            ),
            execution_boundary=_zero_execution_boundary(),
        )
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
    manual_provider_test_sealed_pre_execution_packet: JsonDict | None = None,
    manual_provider_test_arming_record: JsonDict | None = None,
    manual_provider_test_release_proposal: JsonDict | None = None,
    manual_provider_test_final_release_packet: JsonDict | None = None,
    manual_provider_test_execution_switch: JsonDict | None = None,
    manual_provider_test_executor_preflight: JsonDict | None = None,
    manual_provider_test_executor_dispatch_record: JsonDict | None = None,
    manual_provider_test_invocation_receipt: JsonDict | None = None,
    manual_provider_test_post_invocation_audit: JsonDict | None = None,
    manual_provider_test_completion_summary: JsonDict | None = None,
    manual_provider_test_closeout_record: JsonDict | None = None,
    manual_provider_test_operator_handback: JsonDict | None = None,
    manual_provider_test_operator_decision_packet: JsonDict | None = None,
    manual_provider_test_operator_release_attestation: JsonDict | None = None,
    manual_provider_test_release_authorization_seal: JsonDict | None = None,
    manual_provider_test_execution_authorization_capsule: JsonDict | None = None,
    manual_provider_test_execution_capsule_export: JsonDict | None = None,
    manual_provider_test_execution_capsule_export_read_model: JsonDict | None = None,
    manual_provider_test_execution_capsule_handoff_packet: JsonDict | None = None,
    manual_provider_test_execution_capsule_operator_review: JsonDict | None = None,
    manual_provider_test_execution_capsule_operator_decision: JsonDict | None = None,
    manual_provider_test_execution_capsule_release_attestation: JsonDict | None = None,
    manual_provider_test_execution_capsule_release_seal: JsonDict | None = None,
    manual_provider_test_execution_capsule_final_authorization: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_export: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_export_read_model: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_handoff_packet: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_operator_review: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_operator_decision: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_release_attestation: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_release_seal: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_final_authorization: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_final_authz_export: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_final_authz_export_read_model: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_final_authz_handoff_packet: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_final_authz_operator_review: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_final_authz_operator_decision: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_final_authz_release_attestation: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_final_authz_release_seal: JsonDict | None = None,
    manual_provider_test_execution_capsule_authz_final_authz_final_authorization: JsonDict | None = None,
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
    selected_sealed_packet = (
        manual_provider_test_sealed_pre_execution_packet
        or _manual_provider_test_sealed_packet_blocked("sealed_packet_not_evaluated")
    )
    selected_arming_record = (
        manual_provider_test_arming_record
        or _manual_provider_test_arming_record_blocked("arming_record_not_evaluated")
    )
    selected_release_proposal = (
        manual_provider_test_release_proposal
        or _manual_provider_test_release_proposal_blocked("arming_record_not_evaluated")
    )
    selected_final_release_packet = (
        manual_provider_test_final_release_packet
        or _manual_provider_test_final_release_packet_blocked(
            "release_proposal_not_evaluated"
        )
    )
    selected_execution_switch = (
        manual_provider_test_execution_switch
        or _manual_provider_test_execution_switch_blocked(
            "final_release_packet_not_evaluated"
        )
    )
    selected_executor_preflight = (
        manual_provider_test_executor_preflight
        or _manual_provider_test_executor_preflight_blocked(
            "execution_switch_not_evaluated"
        )
    )
    selected_executor_dispatch_record = (
        manual_provider_test_executor_dispatch_record
        or _manual_provider_test_executor_dispatch_record_blocked(
            "executor_preflight_not_evaluated"
        )
    )
    selected_invocation_receipt = (
        manual_provider_test_invocation_receipt
        or _manual_provider_test_invocation_receipt_blocked(
            "dispatch_record_not_evaluated"
        )
    )
    selected_post_invocation_audit = (
        manual_provider_test_post_invocation_audit
        or _manual_provider_test_post_invocation_audit_blocked(
            "invocation_receipt_not_evaluated"
        )
    )
    selected_completion_summary = (
        manual_provider_test_completion_summary
        or _manual_provider_test_completion_summary_blocked(
            "post_invocation_audit_not_evaluated"
        )
    )
    selected_closeout_record = (
        manual_provider_test_closeout_record
        or _manual_provider_test_closeout_record_blocked(
            "completion_summary_not_evaluated"
        )
    )
    selected_operator_handback = (
        manual_provider_test_operator_handback
        or _manual_provider_test_operator_handback_blocked(
            "closeout_record_not_evaluated"
        )
    )
    selected_operator_decision_packet = (
        manual_provider_test_operator_decision_packet
        or _manual_provider_test_operator_decision_packet_blocked(
            "operator_handback_not_evaluated"
        )
    )
    selected_operator_release_attestation = (
        manual_provider_test_operator_release_attestation
        or _manual_provider_test_operator_release_attestation_blocked(
            "operator_decision_packet_not_evaluated"
        )
    )
    selected_release_authorization_seal = (
        manual_provider_test_release_authorization_seal
        or _manual_provider_test_release_authorization_seal_blocked(
            "operator_release_attestation_not_evaluated"
        )
    )
    selected_execution_capsule = (
        manual_provider_test_execution_authorization_capsule
        or _manual_provider_test_execution_authorization_capsule_blocked(
            "release_seal_not_evaluated"
        )
    )
    selected_execution_capsule_export = (
        manual_provider_test_execution_capsule_export
        or _manual_provider_test_execution_capsule_export_blocked(
            "execution_capsule_not_evaluated"
        )
    )
    selected_execution_capsule_export_read_model = (
        manual_provider_test_execution_capsule_export_read_model
        or _manual_provider_test_execution_capsule_export_read_model_projection(
            selected_execution_capsule_export
        )
    )
    selected_execution_capsule_handoff_packet = (
        manual_provider_test_execution_capsule_handoff_packet
        or _manual_provider_test_execution_capsule_handoff_packet_blocked(
            "execution_capsule_export_not_evaluated"
        )
    )
    selected_execution_capsule_operator_review = (
        manual_provider_test_execution_capsule_operator_review
        or _manual_provider_test_execution_capsule_operator_review_blocked(
            "execution_capsule_handoff_packet_not_evaluated"
        )
    )
    selected_execution_capsule_operator_decision = (
        manual_provider_test_execution_capsule_operator_decision
        or _manual_provider_test_execution_capsule_operator_decision_blocked(
            "execution_capsule_operator_review_not_evaluated"
        )
    )
    selected_execution_capsule_release_attestation = (
        manual_provider_test_execution_capsule_release_attestation
        or _manual_provider_test_execution_capsule_release_attestation_blocked(
            "execution_capsule_operator_decision_not_evaluated"
        )
    )
    selected_execution_capsule_release_seal = (
        manual_provider_test_execution_capsule_release_seal
        or _manual_provider_test_execution_capsule_release_seal_blocked(
            "execution_capsule_release_attestation_not_evaluated"
        )
    )
    selected_execution_capsule_final_authorization = (
        manual_provider_test_execution_capsule_final_authorization
        or _manual_provider_test_execution_capsule_final_authorization_blocked(
            "execution_capsule_release_seal_not_evaluated"
        )
    )
    selected_execution_capsule_authz_export = (
        manual_provider_test_execution_capsule_authz_export
        or _manual_provider_test_execution_capsule_authz_export_blocked(
            "execution_capsule_final_authz_not_evaluated"
        )
    )
    selected_execution_capsule_authz_export_read_model = (
        manual_provider_test_execution_capsule_authz_export_read_model
        or _manual_provider_test_execution_capsule_authz_export_read_model_projection(
            selected_execution_capsule_authz_export
        )
    )
    selected_execution_capsule_authz_handoff_packet = (
        manual_provider_test_execution_capsule_authz_handoff_packet
        or _manual_provider_test_execution_capsule_authz_handoff_packet_blocked(
            "execution_capsule_authz_export_not_evaluated"
        )
    )
    selected_execution_capsule_authz_operator_review = (
        manual_provider_test_execution_capsule_authz_operator_review
        or _manual_provider_test_execution_capsule_authz_operator_review_blocked(
            "execution_capsule_authz_handoff_packet_not_evaluated"
        )
    )
    selected_execution_capsule_authz_operator_decision = (
        manual_provider_test_execution_capsule_authz_operator_decision
        or _manual_provider_test_execution_capsule_authz_operator_decision_blocked(
            "execution_capsule_authz_operator_review_not_evaluated"
        )
    )
    selected_execution_capsule_authz_release_attestation = (
        manual_provider_test_execution_capsule_authz_release_attestation
        or _manual_provider_test_execution_capsule_authz_release_attestation_blocked(
            "execution_capsule_authz_operator_decision_not_evaluated"
        )
    )
    selected_execution_capsule_authz_release_seal = (
        manual_provider_test_execution_capsule_authz_release_seal
        or _manual_provider_test_execution_capsule_authz_release_seal_blocked(
            "execution_capsule_authz_release_attestation_not_evaluated"
        )
    )
    selected_execution_capsule_authz_final_authorization = (
        manual_provider_test_execution_capsule_authz_final_authorization
        or _manual_provider_test_execution_capsule_authz_final_authorization_blocked(
            "execution_capsule_authz_release_seal_not_evaluated"
        )
    )
    selected_execution_capsule_authz_final_authz_export = (
        manual_provider_test_execution_capsule_authz_final_authz_export
        or _manual_provider_test_execution_capsule_authz_final_authz_export_blocked(
            "execution_capsule_authz_final_authz_not_evaluated"
        )
    )
    selected_execution_capsule_authz_final_authz_export_read_model = (
        manual_provider_test_execution_capsule_authz_final_authz_export_read_model
        or _manual_provider_test_execution_capsule_authz_final_authz_export_read_model_projection(
            selected_execution_capsule_authz_final_authz_export
        )
    )
    selected_execution_capsule_authz_final_authz_handoff_packet = (
        manual_provider_test_execution_capsule_authz_final_authz_handoff_packet
        or _manual_provider_test_execution_capsule_authz_final_authz_handoff_packet_blocked(
            "execution_capsule_authz_final_authz_export_not_evaluated"
        )
    )
    selected_execution_capsule_authz_final_authz_operator_review = (
        manual_provider_test_execution_capsule_authz_final_authz_operator_review
        or _manual_provider_test_execution_capsule_authz_final_authz_operator_review_blocked(
            "execution_capsule_authz_final_authz_handoff_packet_not_evaluated"
        )
    )
    selected_execution_capsule_authz_final_authz_operator_decision = (
        manual_provider_test_execution_capsule_authz_final_authz_operator_decision
        or _manual_provider_test_execution_capsule_authz_final_authz_operator_decision_blocked(
            "execution_capsule_authz_final_authz_operator_review_not_evaluated"
        )
    )
    selected_execution_capsule_authz_final_authz_release_attestation = (
        manual_provider_test_execution_capsule_authz_final_authz_release_attestation
        or _manual_provider_test_execution_capsule_authz_final_authz_release_attestation_blocked(
            "execution_capsule_authz_final_authz_operator_decision_not_evaluated"
        )
    )
    selected_execution_capsule_authz_final_authz_release_seal = (
        manual_provider_test_execution_capsule_authz_final_authz_release_seal
        or _manual_provider_test_execution_capsule_authz_final_authz_release_seal_blocked(
            "execution_capsule_authz_final_authz_release_attestation_not_evaluated"
        )
    )
    selected_execution_capsule_authz_final_authz_final_authorization = (
        manual_provider_test_execution_capsule_authz_final_authz_final_authorization
        or _manual_provider_test_execution_capsule_authz_final_authz_final_authorization_blocked(
            "execution_capsule_authz_final_authz_release_seal_not_evaluated"
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
            "manual_provider_test_sealed_pre_execution_packet": selected_sealed_packet,
            "manual_provider_test_arming_record": selected_arming_record,
            "manual_provider_test_release_proposal": selected_release_proposal,
            "manual_provider_test_final_release_packet": selected_final_release_packet,
            "manual_provider_test_execution_switch": selected_execution_switch,
            "manual_provider_test_executor_preflight": selected_executor_preflight,
            "manual_provider_test_executor_dispatch_record": (
                selected_executor_dispatch_record
            ),
            "manual_provider_test_invocation_receipt": selected_invocation_receipt,
            "manual_provider_test_post_invocation_audit": (
                selected_post_invocation_audit
            ),
            "manual_provider_test_completion_summary": selected_completion_summary,
            "manual_provider_test_closeout_record": selected_closeout_record,
            "manual_provider_test_operator_handback": selected_operator_handback,
            "manual_provider_test_operator_decision_packet": (
                selected_operator_decision_packet
            ),
            "manual_provider_test_operator_release_attestation": (
                selected_operator_release_attestation
            ),
            "manual_provider_test_release_seal": (
                selected_release_authorization_seal
            ),
            "manual_provider_test_execution_capsule": selected_execution_capsule,
            "manual_provider_test_execution_capsule_export": (
                selected_execution_capsule_export
            ),
            "manual_provider_test_execution_capsule_export_read_model": (
                selected_execution_capsule_export_read_model
            ),
            "manual_provider_test_execution_capsule_handoff_packet": (
                selected_execution_capsule_handoff_packet
            ),
            "manual_provider_test_execution_capsule_operator_review": (
                selected_execution_capsule_operator_review
            ),
            "manual_provider_test_execution_capsule_operator_decision": (
                selected_execution_capsule_operator_decision
            ),
            "manual_provider_test_execution_capsule_release_attestation": (
                selected_execution_capsule_release_attestation
            ),
            "manual_provider_test_execution_capsule_release_seal": (
                selected_execution_capsule_release_seal
            ),
            "manual_provider_test_execution_capsule_final_authz": (
                selected_execution_capsule_final_authorization
            ),
            "manual_provider_test_execution_capsule_authz_export": (
                selected_execution_capsule_authz_export
            ),
            "manual_provider_test_execution_capsule_authz_export_read_model": (
                selected_execution_capsule_authz_export_read_model
            ),
            "manual_provider_test_execution_capsule_authz_handoff_packet": (
                selected_execution_capsule_authz_handoff_packet
            ),
            "manual_provider_test_execution_capsule_authz_operator_review": (
                selected_execution_capsule_authz_operator_review
            ),
            "manual_provider_test_execution_capsule_authz_operator_decision": (
                selected_execution_capsule_authz_operator_decision
            ),
            "manual_provider_test_execution_capsule_authz_release_attestation": (
                selected_execution_capsule_authz_release_attestation
            ),
            "manual_provider_test_execution_capsule_authz_release_seal": (
                selected_execution_capsule_authz_release_seal
            ),
            "manual_provider_test_execution_capsule_authz_final_authz": (
                selected_execution_capsule_authz_final_authorization
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_export": (
                selected_execution_capsule_authz_final_authz_export
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_export_read_model": (
                selected_execution_capsule_authz_final_authz_export_read_model
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet": (
                selected_execution_capsule_authz_final_authz_handoff_packet
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_operator_review": (
                selected_execution_capsule_authz_final_authz_operator_review
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_operator_decision": (
                selected_execution_capsule_authz_final_authz_operator_decision
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_release_attestation": (
                selected_execution_capsule_authz_final_authz_release_attestation
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_release_seal": (
                selected_execution_capsule_authz_final_authz_release_seal
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_final_authz": (
                selected_execution_capsule_authz_final_authz_final_authorization
            ),
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
    sealed_pre_execution_packet = _manual_provider_test_sealed_packet_projection(
        payload=payload,
        operator_policy_summary=operator_policy_summary,
        manual_provider_test_proposal=manual_provider_test_proposal,
        handoff_packet=handoff_packet,
        operator_opt_in=operator_opt_in,
    )
    arming_record = _manual_provider_test_arming_record_projection(
        payload=payload,
        sealed_pre_execution_packet=sealed_pre_execution_packet,
    )
    release_proposal = _manual_provider_test_release_proposal_projection(
        payload=payload,
        arming_record=arming_record,
    )
    final_release_packet = _manual_provider_test_final_release_packet_projection(
        payload=payload,
        release_proposal=release_proposal,
    )
    execution_switch = _manual_provider_test_execution_switch_projection(
        payload=payload,
        final_release_packet=final_release_packet,
    )
    executor_preflight = _manual_provider_test_executor_preflight_projection(
        payload=payload,
        execution_switch=execution_switch,
        execution_boundary=execution_boundary,
    )
    executor_dispatch_record = _manual_provider_test_executor_dispatch_record_projection(
        payload=payload,
        executor_preflight=executor_preflight,
        execution_boundary=execution_boundary,
    )
    invocation_receipt = _manual_provider_test_invocation_receipt_projection(
        payload=payload,
        dispatch_record=executor_dispatch_record,
        execution_boundary=execution_boundary,
    )
    post_invocation_audit = _manual_provider_test_post_invocation_audit_projection(
        payload=payload,
        invocation_receipt=invocation_receipt,
        execution_boundary=execution_boundary,
    )
    completion_summary = _manual_provider_test_completion_summary_projection(
        payload=payload,
        post_invocation_audit=post_invocation_audit,
        execution_boundary=execution_boundary,
    )
    closeout_record = _manual_provider_test_closeout_record_projection(
        payload=payload,
        completion_summary=completion_summary,
        execution_boundary=execution_boundary,
    )
    operator_handback = _manual_provider_test_operator_handback_projection(
        payload=payload,
        closeout_record=closeout_record,
        execution_boundary=execution_boundary,
    )
    operator_decision_packet = _manual_provider_test_operator_decision_packet_projection(
        payload=payload,
        operator_handback=operator_handback,
        execution_boundary=execution_boundary,
    )
    operator_release_attestation = (
        _manual_provider_test_operator_release_attestation_projection(
            payload=payload,
            operator_decision_packet=operator_decision_packet,
            execution_boundary=execution_boundary,
        )
    )
    release_authorization_seal = (
        _manual_provider_test_release_authorization_seal_projection(
            payload=payload,
            operator_release_attestation=operator_release_attestation,
            execution_boundary=execution_boundary,
        )
    )
    execution_authorization_capsule = (
        _manual_provider_test_execution_authorization_capsule_projection(
            payload=payload,
            release_seal=release_authorization_seal,
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_export = (
        _manual_provider_test_execution_capsule_export_projection(
            payload=payload,
            execution_capsule=execution_authorization_capsule,
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_export_read_model = (
        _manual_provider_test_execution_capsule_export_read_model_projection(
            execution_capsule_export
        )
    )
    execution_capsule_handoff_packet = (
        _manual_provider_test_execution_capsule_handoff_packet_projection(
            payload=payload,
            execution_capsule_export=execution_capsule_export,
            execution_capsule_export_read_model=execution_capsule_export_read_model,
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_operator_review = (
        _manual_provider_test_execution_capsule_operator_review_projection(
            payload=payload,
            execution_capsule_handoff_packet=execution_capsule_handoff_packet,
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_operator_decision = (
        _manual_provider_test_execution_capsule_operator_decision_projection(
            payload=payload,
            execution_capsule_operator_review=execution_capsule_operator_review,
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_release_attestation = (
        _manual_provider_test_execution_capsule_release_attestation_projection(
            payload=payload,
            execution_capsule_operator_decision=execution_capsule_operator_decision,
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_release_seal = (
        _manual_provider_test_execution_capsule_release_seal_projection(
            payload=payload,
            execution_capsule_release_attestation=execution_capsule_release_attestation,
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_final_authorization = (
        _manual_provider_test_execution_capsule_final_authorization_projection(
            payload=payload,
            execution_capsule_release_seal=execution_capsule_release_seal,
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_export = (
        _manual_provider_test_execution_capsule_authz_export_projection(
            payload=payload,
            execution_capsule_final_authz=execution_capsule_final_authorization,
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_export_read_model = (
        _manual_provider_test_execution_capsule_authz_export_read_model_projection(
            execution_capsule_authz_export
        )
    )
    execution_capsule_authz_handoff_packet = (
        _manual_provider_test_execution_capsule_authz_handoff_packet_projection(
            payload=payload,
            execution_capsule_authz_export=execution_capsule_authz_export,
            execution_capsule_authz_export_read_model=(
                execution_capsule_authz_export_read_model
            ),
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_operator_review = (
        _manual_provider_test_execution_capsule_authz_operator_review_projection(
            payload=payload,
            execution_capsule_authz_handoff_packet=(
                execution_capsule_authz_handoff_packet
            ),
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_operator_decision = (
        _manual_provider_test_execution_capsule_authz_operator_decision_projection(
            payload=payload,
            execution_capsule_authz_operator_review=(
                execution_capsule_authz_operator_review
            ),
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_release_attestation = (
        _manual_provider_test_execution_capsule_authz_release_attestation_projection(
            payload=payload,
            execution_capsule_authz_operator_decision=(
                execution_capsule_authz_operator_decision
            ),
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_release_seal = (
        _manual_provider_test_execution_capsule_authz_release_seal_projection(
            payload=payload,
            execution_capsule_authz_release_attestation=(
                execution_capsule_authz_release_attestation
            ),
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_final_authorization = (
        _manual_provider_test_execution_capsule_authz_final_authorization_projection(
            payload=payload,
            execution_capsule_authz_release_seal=execution_capsule_authz_release_seal,
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_final_authz_export = (
        _manual_provider_test_execution_capsule_authz_final_authz_export_projection(
            payload=payload,
            execution_capsule_authz_final_authz=(
                execution_capsule_authz_final_authorization
            ),
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_final_authz_export_read_model = (
        _manual_provider_test_execution_capsule_authz_final_authz_export_read_model_projection(
            execution_capsule_authz_final_authz_export
        )
    )
    execution_capsule_authz_final_authz_handoff_packet = (
        _manual_provider_test_execution_capsule_authz_final_authz_handoff_packet_projection(
            payload=payload,
            execution_capsule_authz_final_authz_export=(
                execution_capsule_authz_final_authz_export
            ),
            execution_capsule_authz_final_authz_export_read_model=(
                execution_capsule_authz_final_authz_export_read_model
            ),
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_final_authz_operator_review = (
        _manual_provider_test_execution_capsule_authz_final_authz_operator_review_projection(
            payload=payload,
            execution_capsule_authz_final_authz_handoff_packet=(
                execution_capsule_authz_final_authz_handoff_packet
            ),
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_final_authz_operator_decision = (
        _manual_provider_test_execution_capsule_authz_final_authz_operator_decision_projection(
            payload=payload,
            execution_capsule_authz_final_authz_operator_review=(
                execution_capsule_authz_final_authz_operator_review
            ),
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_final_authz_release_attestation = (
        _manual_provider_test_execution_capsule_authz_final_authz_release_attestation_projection(
            payload=payload,
            execution_capsule_authz_final_authz_operator_decision=(
                execution_capsule_authz_final_authz_operator_decision
            ),
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_final_authz_release_seal = (
        _manual_provider_test_execution_capsule_authz_final_authz_release_seal_projection(
            payload=payload,
            execution_capsule_authz_final_authz_release_attestation=(
                execution_capsule_authz_final_authz_release_attestation
            ),
            execution_boundary=execution_boundary,
        )
    )
    execution_capsule_authz_final_authz_final_authorization = (
        _manual_provider_test_execution_capsule_authz_final_authz_final_authorization_projection(
            payload=payload,
            execution_capsule_authz_final_authz_release_seal=(
                execution_capsule_authz_final_authz_release_seal
            ),
            execution_boundary=execution_boundary,
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
            "manual_provider_test_sealed_pre_execution_packet": sealed_pre_execution_packet,
            "manual_provider_test_arming_record": arming_record,
            "manual_provider_test_release_proposal": release_proposal,
            "manual_provider_test_final_release_packet": final_release_packet,
            "manual_provider_test_execution_switch": execution_switch,
            "manual_provider_test_executor_preflight": executor_preflight,
            "manual_provider_test_executor_dispatch_record": executor_dispatch_record,
            "manual_provider_test_invocation_receipt": invocation_receipt,
            "manual_provider_test_post_invocation_audit": post_invocation_audit,
            "manual_provider_test_completion_summary": completion_summary,
            "manual_provider_test_closeout_record": closeout_record,
            "manual_provider_test_operator_handback": operator_handback,
            "manual_provider_test_operator_decision_packet": (
                operator_decision_packet
            ),
            "manual_provider_test_operator_release_attestation": (
                operator_release_attestation
            ),
            "manual_provider_test_release_seal": (
                release_authorization_seal
            ),
            "manual_provider_test_execution_capsule": (
                execution_authorization_capsule
            ),
            "manual_provider_test_execution_capsule_export": (
                execution_capsule_export
            ),
            "manual_provider_test_execution_capsule_export_read_model": (
                execution_capsule_export_read_model
            ),
            "manual_provider_test_execution_capsule_handoff_packet": (
                execution_capsule_handoff_packet
            ),
            "manual_provider_test_execution_capsule_operator_review": (
                execution_capsule_operator_review
            ),
            "manual_provider_test_execution_capsule_operator_decision": (
                execution_capsule_operator_decision
            ),
            "manual_provider_test_execution_capsule_release_attestation": (
                execution_capsule_release_attestation
            ),
            "manual_provider_test_execution_capsule_release_seal": (
                execution_capsule_release_seal
            ),
            "manual_provider_test_execution_capsule_final_authz": (
                execution_capsule_final_authorization
            ),
            "manual_provider_test_execution_capsule_authz_export": (
                execution_capsule_authz_export
            ),
            "manual_provider_test_execution_capsule_authz_export_read_model": (
                execution_capsule_authz_export_read_model
            ),
            "manual_provider_test_execution_capsule_authz_handoff_packet": (
                execution_capsule_authz_handoff_packet
            ),
            "manual_provider_test_execution_capsule_authz_operator_review": (
                execution_capsule_authz_operator_review
            ),
            "manual_provider_test_execution_capsule_authz_operator_decision": (
                execution_capsule_authz_operator_decision
            ),
            "manual_provider_test_execution_capsule_authz_release_attestation": (
                execution_capsule_authz_release_attestation
            ),
            "manual_provider_test_execution_capsule_authz_release_seal": (
                execution_capsule_authz_release_seal
            ),
            "manual_provider_test_execution_capsule_authz_final_authz": (
                execution_capsule_authz_final_authorization
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_export": (
                execution_capsule_authz_final_authz_export
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_export_read_model": (
                execution_capsule_authz_final_authz_export_read_model
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet": (
                execution_capsule_authz_final_authz_handoff_packet
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_operator_review": (
                execution_capsule_authz_final_authz_operator_review
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_operator_decision": (
                execution_capsule_authz_final_authz_operator_decision
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_release_attestation": (
                execution_capsule_authz_final_authz_release_attestation
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_release_seal": (
                execution_capsule_authz_final_authz_release_seal
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_final_authz": (
                execution_capsule_authz_final_authz_final_authorization
            ),
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
            manual_provider_test_sealed_pre_execution_packet=(
                _manual_provider_test_sealed_packet_blocked(
                    "handoff_packet_missing_or_mismatched"
                )
            ),
            manual_provider_test_arming_record=(
                _manual_provider_test_arming_record_blocked(
                    "sealed_packet_missing_or_mismatched"
                )
            ),
            manual_provider_test_release_proposal=(
                _manual_provider_test_release_proposal_blocked(
                    "arming_record_missing_or_mismatched"
                )
            ),
            manual_provider_test_final_release_packet=(
                _manual_provider_test_final_release_packet_blocked(
                    "release_proposal_missing_or_mismatched"
                )
            ),
            manual_provider_test_execution_switch=(
                _manual_provider_test_execution_switch_blocked(
                    "final_release_packet_missing_or_mismatched"
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
            manual_provider_test_sealed_pre_execution_packet=(
                _manual_provider_test_sealed_packet_blocked(
                    "handoff_packet_hash_mismatch"
                )
            ),
            manual_provider_test_arming_record=(
                _manual_provider_test_arming_record_blocked(
                    "sealed_packet_missing_or_mismatched"
                )
            ),
            manual_provider_test_release_proposal=(
                _manual_provider_test_release_proposal_blocked(
                    "arming_record_missing_or_mismatched"
                )
            ),
            manual_provider_test_final_release_packet=(
                _manual_provider_test_final_release_packet_blocked(
                    "release_proposal_missing_or_mismatched"
                )
            ),
            manual_provider_test_execution_switch=(
                _manual_provider_test_execution_switch_blocked(
                    "final_release_packet_missing_or_mismatched"
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
            "manual_provider_test_sealed_pre_execution_packet": _manual_provider_test_sealed_packet_blocked(
                "operator_opt_in_missing_or_mismatched"
            ),
            "manual_provider_test_arming_record": _manual_provider_test_arming_record_blocked(
                "sealed_packet_missing_or_mismatched"
            ),
            "manual_provider_test_release_proposal": _manual_provider_test_release_proposal_blocked(
                "arming_record_missing_or_mismatched"
            ),
            "manual_provider_test_final_release_packet": _manual_provider_test_final_release_packet_blocked(
                "release_proposal_missing_or_mismatched"
            ),
            "manual_provider_test_execution_switch": _manual_provider_test_execution_switch_blocked(
                "final_release_packet_missing_or_mismatched"
            ),
            "manual_provider_test_executor_preflight": _manual_provider_test_executor_preflight_blocked(
                "execution_switch_missing_or_mismatched"
            ),
            "manual_provider_test_executor_dispatch_record": (
                _manual_provider_test_executor_dispatch_record_blocked(
                    "executor_preflight_missing_or_mismatched"
                )
            ),
            "manual_provider_test_invocation_receipt": (
                _manual_provider_test_invocation_receipt_blocked(
                    "dispatch_record_missing_or_mismatched"
                )
            ),
            "manual_provider_test_post_invocation_audit": (
                _manual_provider_test_post_invocation_audit_blocked(
                    "invocation_receipt_missing_or_mismatched"
                )
            ),
            "manual_provider_test_completion_summary": (
                _manual_provider_test_completion_summary_blocked(
                    "post_invocation_audit_missing_or_mismatched"
                )
            ),
            "manual_provider_test_closeout_record": (
                _manual_provider_test_closeout_record_blocked(
                    "completion_summary_missing_or_mismatched"
                )
            ),
            "manual_provider_test_operator_handback": (
                _manual_provider_test_operator_handback_blocked(
                    "closeout_record_missing_or_mismatched"
                )
            ),
            "manual_provider_test_operator_decision_packet": (
                _manual_provider_test_operator_decision_packet_blocked(
                    "operator_handback_missing_or_mismatched"
                )
            ),
            "manual_provider_test_operator_release_attestation": (
                _manual_provider_test_operator_release_attestation_blocked(
                    "operator_decision_packet_missing_or_mismatched"
                )
            ),
            "manual_provider_test_release_seal": (
                _manual_provider_test_release_authorization_seal_blocked(
                    "operator_release_attestation_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule": (
                _manual_provider_test_execution_authorization_capsule_blocked(
                    "release_seal_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_export": (
                _manual_provider_test_execution_capsule_export_blocked(
                    "execution_capsule_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_export_read_model": (
                _manual_provider_test_execution_capsule_export_read_model_blocked(
                    "execution_capsule_export_not_available"
                )
            ),
            "manual_provider_test_execution_capsule_handoff_packet": (
                _manual_provider_test_execution_capsule_handoff_packet_blocked(
                    "execution_capsule_export_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_operator_review": (
                _manual_provider_test_execution_capsule_operator_review_blocked(
                    "execution_capsule_handoff_packet_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_operator_decision": (
                _manual_provider_test_execution_capsule_operator_decision_blocked(
                    "execution_capsule_operator_review_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_release_attestation": (
                _manual_provider_test_execution_capsule_release_attestation_blocked(
                    "execution_capsule_operator_decision_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_release_seal": (
                _manual_provider_test_execution_capsule_release_seal_blocked(
                    "execution_capsule_release_attestation_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_final_authz": (
                _manual_provider_test_execution_capsule_final_authorization_blocked(
                    "execution_capsule_release_seal_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_export": (
                _manual_provider_test_execution_capsule_authz_export_blocked(
                    "execution_capsule_final_authz_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_export_read_model": (
                _manual_provider_test_execution_capsule_authz_export_read_model_blocked(
                    "execution_capsule_authz_export_not_available"
                )
            ),
            "manual_provider_test_execution_capsule_authz_handoff_packet": (
                _manual_provider_test_execution_capsule_authz_handoff_packet_blocked(
                    "execution_capsule_authz_export_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_operator_review": (
                _manual_provider_test_execution_capsule_authz_operator_review_blocked(
                    "execution_capsule_authz_handoff_packet_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_operator_decision": (
                _manual_provider_test_execution_capsule_authz_operator_decision_blocked(
                    "execution_capsule_authz_operator_review_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_release_attestation": (
                _manual_provider_test_execution_capsule_authz_release_attestation_blocked(
                    "execution_capsule_authz_operator_decision_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_release_seal": (
                _manual_provider_test_execution_capsule_authz_release_seal_blocked(
                    "execution_capsule_authz_release_attestation_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_final_authz": (
                _manual_provider_test_execution_capsule_authz_final_authorization_blocked(
                    "execution_capsule_authz_release_seal_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_export": (
                _manual_provider_test_execution_capsule_authz_final_authz_export_blocked(
                    "execution_capsule_authz_final_authz_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_export_read_model": (
                _manual_provider_test_execution_capsule_authz_final_authz_export_read_model_blocked(
                    "execution_capsule_authz_final_authz_export_not_available"
                )
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet": (
                _manual_provider_test_execution_capsule_authz_final_authz_handoff_packet_blocked(
                    "execution_capsule_authz_final_authz_export_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_operator_review": (
                _manual_provider_test_execution_capsule_authz_final_authz_operator_review_blocked(
                    "execution_capsule_authz_final_authz_handoff_packet_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_operator_decision": (
                _manual_provider_test_execution_capsule_authz_final_authz_operator_decision_blocked(
                    "execution_capsule_authz_final_authz_operator_review_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_release_attestation": (
                _manual_provider_test_execution_capsule_authz_final_authz_release_attestation_blocked(
                    "execution_capsule_authz_final_authz_operator_decision_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_release_seal": (
                _manual_provider_test_execution_capsule_authz_final_authz_release_seal_blocked(
                    "execution_capsule_authz_final_authz_release_attestation_missing_or_mismatched"
                )
            ),
            "manual_provider_test_execution_capsule_authz_final_authz_final_authz": (
                _manual_provider_test_execution_capsule_authz_final_authz_final_authorization_blocked(
                    "execution_capsule_authz_final_authz_release_seal_missing_or_mismatched"
                )
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
    "MANUAL_PROVIDER_TEST_SEALED_PRE_EXECUTION_PACKET_VERSION",
    "MANUAL_PROVIDER_TEST_ARMING_RECORD_VERSION",
    "MANUAL_PROVIDER_TEST_RELEASE_PROPOSAL_VERSION",
    "MANUAL_PROVIDER_TEST_FINAL_RELEASE_PACKET_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_SWITCH_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTOR_PREFLIGHT_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTOR_DISPATCH_VERSION",
    "MANUAL_PROVIDER_TEST_INVOCATION_RECEIPT_VERSION",
    "MANUAL_PROVIDER_TEST_POST_INVOCATION_AUDIT_VERSION",
    "MANUAL_PROVIDER_TEST_COMPLETION_SUMMARY_VERSION",
    "MANUAL_PROVIDER_TEST_CLOSEOUT_RECORD_VERSION",
    "MANUAL_PROVIDER_TEST_OPERATOR_HANDBACK_VERSION",
    "MANUAL_PROVIDER_TEST_OPERATOR_DECISION_PACKET_VERSION",
    "MANUAL_PROVIDER_TEST_OPERATOR_RELEASE_ATTESTATION_VERSION",
    "MANUAL_PROVIDER_TEST_RELEASE_AUTHORIZATION_SEAL_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_AUTHORIZATION_CAPSULE_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_EXPORT_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_HANDOFF_PACKET_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_REVIEW_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_OPERATOR_DECISION_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_ATTESTATION_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_RELEASE_SEAL_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_FINAL_AUTHORIZATION_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_EXPORT_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_HANDOFF_PACKET_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_REVIEW_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_OPERATOR_DECISION_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_ATTESTATION_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_RELEASE_SEAL_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHORIZATION_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_EXPORT_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_HANDOFF_PACKET_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_REVIEW_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_OPERATOR_DECISION_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_ATTESTATION_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_RELEASE_SEAL_VERSION",
    "MANUAL_PROVIDER_TEST_EXECUTION_CAPSULE_AUTHZ_FINAL_AUTHZ_FINAL_AUTHORIZATION_VERSION",
    "provider_manual_test_proposal_summary",
    "provider_manual_test_preflight_summary",
    "provider_manual_test_review_packet_summary",
    "provider_manual_test_handoff_packet_summary",
    "provider_manual_test_operator_opt_in_summary",
    "provider_manual_test_sealed_pre_execution_packet_summary",
    "provider_manual_test_arming_record_summary",
    "provider_manual_test_release_proposal_summary",
    "provider_manual_test_final_release_packet_summary",
    "provider_manual_test_execution_switch_summary",
    "provider_manual_test_executor_preflight_summary",
    "provider_manual_test_executor_dispatch_record_summary",
    "provider_manual_test_invocation_receipt_summary",
    "provider_manual_test_post_invocation_audit_summary",
    "provider_manual_test_completion_summary",
    "provider_manual_test_closeout_record_summary",
    "provider_manual_test_operator_handback_summary",
    "provider_manual_test_operator_decision_packet_summary",
    "provider_manual_test_operator_release_attestation_summary",
    "provider_manual_test_release_authorization_seal_summary",
    "provider_manual_test_execution_authorization_capsule_summary",
    "provider_manual_test_execution_capsule_export_summary",
    "provider_manual_test_execution_capsule_handoff_packet_summary",
    "provider_manual_test_execution_capsule_operator_review_summary",
    "provider_manual_test_execution_capsule_operator_decision_summary",
    "provider_manual_test_execution_capsule_release_attestation_summary",
    "provider_manual_test_execution_capsule_release_seal_summary",
    "provider_manual_test_execution_capsule_final_authorization_summary",
    "provider_manual_test_execution_capsule_authz_export_summary",
    "provider_manual_test_execution_capsule_authz_export_read_model_summary",
    "provider_manual_test_execution_capsule_authz_handoff_packet_summary",
    "provider_manual_test_execution_capsule_authz_operator_review_summary",
    "provider_manual_test_execution_capsule_authz_operator_decision_summary",
    "provider_manual_test_execution_capsule_authz_release_attestation_summary",
    "provider_manual_test_execution_capsule_authz_release_seal_summary",
    "provider_manual_test_execution_capsule_authz_final_authorization_summary",
    "provider_manual_test_execution_capsule_authz_final_authz_export_summary",
    "provider_manual_test_execution_capsule_authz_final_authz_export_read_model_summary",
    "provider_manual_test_execution_capsule_authz_final_authz_handoff_packet_summary",
    "provider_manual_test_execution_capsule_authz_final_authz_operator_review_summary",
    "provider_manual_test_execution_capsule_authz_final_authz_operator_decision_summary",
    "provider_manual_test_execution_capsule_authz_final_authz_release_attestation_summary",
    "provider_manual_test_execution_capsule_authz_final_authz_release_seal_summary",
    "provider_manual_test_execution_capsule_authz_final_authz_final_authorization_summary",
    "provider_precheck_operator_policy_summary",
    "read_provider_envelope_precheck",
    "run_provider_envelope_precheck",
]

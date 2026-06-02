import json
from dataclasses import asdict

from fastapi.testclient import TestClient

from apps.api.agentic_workbench_api.main import create_app
from apps.api.agentic_workbench_api.services.canonical_run_store import RunArtifactRepositoryConfig
from apps.api.agentic_workbench_api.services.evidence_read_model import EvidenceRepositoryConfig
from apps.api.agentic_workbench_api.services.provider_envelope_api import (
    MANUAL_PROVIDER_TEST_EXECUTOR_VERSION,
    ProviderEnvelopeRepositoryConfig,
    provider_manual_test_executor_dispatch_record_summary,
    provider_manual_test_execution_switch_summary,
    provider_manual_test_executor_preflight_summary,
    provider_manual_test_invocation_receipt_summary,
    provider_manual_test_post_invocation_audit_summary,
    provider_manual_test_completion_summary,
    provider_manual_test_closeout_record_summary,
    provider_manual_test_operator_handback_summary,
    provider_manual_test_operator_decision_packet_summary,
    provider_manual_test_operator_release_attestation_summary,
    provider_manual_test_release_authorization_seal_summary,
    provider_manual_test_execution_authorization_capsule_summary,
    provider_manual_test_execution_capsule_export_summary,
    provider_manual_test_execution_capsule_handoff_packet_summary,
    provider_manual_test_execution_capsule_operator_review_summary,
    provider_manual_test_execution_capsule_operator_decision_summary,
    provider_manual_test_execution_capsule_release_attestation_summary,
    provider_manual_test_execution_capsule_release_seal_summary,
    provider_manual_test_execution_capsule_final_authorization_summary,
    provider_manual_test_execution_capsule_authz_export_summary,
    provider_manual_test_execution_capsule_authz_handoff_packet_summary,
    provider_manual_test_execution_capsule_authz_operator_review_summary,
    provider_manual_test_execution_capsule_authz_operator_decision_summary,
    provider_manual_test_execution_capsule_authz_release_attestation_summary,
    provider_manual_test_execution_capsule_authz_release_seal_summary,
    provider_manual_test_execution_capsule_authz_final_authorization_summary,
    provider_manual_test_execution_capsule_authz_final_authz_export_summary,
    provider_manual_test_execution_capsule_authz_final_authz_handoff_packet_summary,
    provider_manual_test_execution_capsule_authz_final_authz_operator_review_summary,
    provider_manual_test_execution_capsule_authz_final_authz_operator_decision_summary,
    provider_manual_test_execution_capsule_authz_final_authz_release_attestation_summary,
    provider_manual_test_execution_capsule_authz_final_authz_release_seal_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_export_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_attestation_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_export_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export_read_model_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_handoff_packet_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal_summary,
    provider_manual_test_arming_record_summary,
    provider_manual_test_final_release_packet_summary,
    provider_manual_test_handoff_packet_summary,
    provider_manual_test_operator_opt_in_summary,
    provider_manual_test_preflight_summary,
    provider_manual_test_proposal_summary,
    provider_manual_test_release_proposal_summary,
    provider_manual_test_review_packet_summary,
    provider_manual_test_sealed_pre_execution_packet_summary,
    provider_precheck_operator_policy_summary,
)
from packages.core.approval_replay_factory import ApprovalReplayRepositoryConfig
from packages.core.live_open_policy import LIVE_OPEN_REQUIRED_CONTROLS
from packages.core.repositories import (
    ArtifactRecord,
    audit_event_record_from_event,
    runner_plan_record_from_plan,
    verification_report_record_from_report,
)
from packages.core.schemas import VerificationReport, stable_contract_hash
from packages.core.sqlite_repositories import SQLiteRunnerReportAuditStore
from packages.daacs_builder.adapters import (
    build_spec_to_daacs_initial_state,
    create_spec_approval,
    implementation_brief_from_prd_package,
    planning_to_build_spec,
)
from packages.daacs_builder.approval_security import sign_approval_for_tests
from packages.daacs_builder.live_runner import live_replay_scope_for_request
from packages.daacs_builder.provider_boundary import (
    ProviderApprovalRecord,
    ProviderRequest,
    provider_replay_scope_for_request,
)
from packages.daacs_builder.runner_provider import (
    ApprovalRecord,
    RunnerPlan,
    RunnerPolicy,
    RunnerRequest,
    default_runner_provider_registry,
)
from packages.div_planner.adapters import planning_blueprint_from_div_state, planning_to_prd_package


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _prompt_contract_hash() -> str:
    return stable_contract_hash({"purpose": "api provider admission demo"})


def _provider_admission_payload(
    *,
    run_id: str = "run-api-provider",
    signature_id: str = "sig-api-provider-admission",
    nonce: str = "nonce-api-provider-admission",
) -> dict:
    approval = ProviderApprovalRecord(
        approved_by="local-user",
        approved_at="2026-05-31T00:00:00Z",
        run_id=run_id,
        provider_name="solar-pro-3",
        model_name="solar-pro-3",
        mode="fake",
        env_key_name="UPSTAGE_API_KEY",
        max_live_api_calls=0,
        max_live_llm_calls=0,
        expires_at="2099-01-01T00:00:00Z",
        audit_log_id=f"audit-{run_id}",
    )
    request = ProviderRequest(
        run_id=run_id,
        prompt_contract_hash=_prompt_contract_hash(),
        approval=approval,
    )
    sign_approval_for_tests(
        approval,
        scope=provider_replay_scope_for_request(request),
        signature_id=signature_id,
        nonce=nonce,
    )
    return {
        "run_id": request.run_id,
        "prompt_contract_hash": request.prompt_contract_hash,
        "approval_lifecycle": "durable",
        "approval": asdict(approval),
    }


def _provider_envelope_precheck_payload(
    *,
    run_id: str = "run-api-envelope",
    prompt_contract_hash: str | None = None,
    include_operator_approval: bool = True,
    approved_policy_summary_hash: str | None = None,
    include_manual_test_proposal: bool = False,
    include_manual_test_operator_approval: bool = True,
    manual_test_executor_enable: bool = False,
    include_one_shot_live_permission: bool = False,
    include_readiness_decision: bool = False,
    readiness_decision: str = "approve",
    readiness_preflight_hash_override: str | None = None,
    include_operator_opt_in: bool = False,
    operator_opt_in_handoff_hash_override: str | None = None,
    include_sealed_pre_execution_packet: bool = False,
    sealed_operator_opt_in_hash_override: str | None = None,
    include_arming_record: bool = False,
    arming_expected_sealed_hash_override: str | None = None,
    arming_record_sealed_hash_override: str | None = None,
    include_release_proposal: bool = False,
    release_expected_arming_hash_override: str | None = None,
    release_proposal_arming_hash_override: str | None = None,
    include_final_release_packet: bool = False,
    final_expected_release_hash_override: str | None = None,
    final_packet_release_hash_override: str | None = None,
    include_execution_switch: bool = False,
    execution_switch_expected_final_hash_override: str | None = None,
    execution_switch_final_hash_override: str | None = None,
    execution_switch_enable: bool = False,
    include_executor_preflight: bool = False,
    executor_preflight_expected_switch_hash_override: str | None = None,
    executor_preflight_switch_hash_override: str | None = None,
    include_executor_dispatch_record: bool = False,
    executor_dispatch_expected_preflight_hash_override: str | None = None,
    executor_dispatch_preflight_hash_override: str | None = None,
    include_invocation_receipt: bool = False,
    invocation_receipt_expected_dispatch_hash_override: str | None = None,
    invocation_receipt_dispatch_hash_override: str | None = None,
    include_post_invocation_audit: bool = False,
    post_invocation_expected_receipt_hash_override: str | None = None,
    post_invocation_receipt_hash_override: str | None = None,
    include_completion_summary: bool = False,
    completion_expected_audit_hash_override: str | None = None,
    completion_audit_hash_override: str | None = None,
    include_closeout_record: bool = False,
    closeout_expected_summary_hash_override: str | None = None,
    closeout_summary_hash_override: str | None = None,
    include_operator_handback: bool = False,
    handback_expected_closeout_hash_override: str | None = None,
    handback_closeout_hash_override: str | None = None,
    include_operator_decision_packet: bool = False,
    decision_expected_handback_hash_override: str | None = None,
    decision_packet_handback_hash_override: str | None = None,
    include_operator_release_attestation: bool = False,
    attestation_expected_decision_packet_hash_override: str | None = None,
    attestation_decision_packet_hash_override: str | None = None,
    include_release_authorization_seal: bool = False,
    seal_expected_release_attestation_hash_override: str | None = None,
    seal_release_attestation_hash_override: str | None = None,
    include_execution_authorization_capsule: bool = False,
    capsule_expected_release_seal_hash_override: str | None = None,
    capsule_release_seal_hash_override: str | None = None,
    include_execution_capsule_export: bool = False,
    export_expected_execution_capsule_hash_override: str | None = None,
    export_execution_capsule_hash_override: str | None = None,
    include_execution_capsule_handoff_packet: bool = False,
    handoff_expected_execution_capsule_export_hash_override: str | None = None,
    handoff_execution_capsule_export_hash_override: str | None = None,
    include_execution_capsule_operator_review: bool = False,
    review_expected_execution_capsule_handoff_hash_override: str | None = None,
    review_execution_capsule_handoff_hash_override: str | None = None,
    include_execution_capsule_operator_decision: bool = False,
    decision_expected_execution_capsule_operator_review_hash_override: str | None = None,
    decision_execution_capsule_operator_review_hash_override: str | None = None,
    include_execution_capsule_release_attestation: bool = False,
    release_attestation_expected_execution_capsule_operator_decision_hash_override: (
        str | None
    ) = None,
    release_attestation_execution_capsule_operator_decision_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_release_seal: bool = False,
    release_seal_expected_execution_capsule_release_attestation_hash_override: (
        str | None
    ) = None,
    release_seal_execution_capsule_release_attestation_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_final_authorization: bool = False,
    final_authorization_expected_execution_capsule_release_seal_hash_override: (
        str | None
    ) = None,
    final_authorization_execution_capsule_release_seal_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_export: bool = False,
    authz_export_expected_execution_capsule_final_authz_hash_override: (
        str | None
    ) = None,
    authz_export_execution_capsule_final_authz_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_handoff_packet: bool = False,
    authz_handoff_expected_execution_capsule_authz_export_hash_override: (
        str | None
    ) = None,
    authz_handoff_execution_capsule_authz_export_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_operator_review: bool = False,
    authz_review_expected_execution_capsule_authz_handoff_hash_override: (
        str | None
    ) = None,
    authz_review_execution_capsule_authz_handoff_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_operator_decision: bool = False,
    authz_decision_expected_execution_capsule_authz_operator_review_hash_override: (
        str | None
    ) = None,
    authz_decision_execution_capsule_authz_operator_review_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_release_attestation: bool = False,
    authz_attestation_expected_execution_capsule_authz_operator_decision_hash_override: (
        str | None
    ) = None,
    authz_attestation_execution_capsule_authz_operator_decision_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_release_seal: bool = False,
    authz_release_seal_expected_execution_capsule_authz_release_attestation_hash_override: (
        str | None
    ) = None,
    authz_release_seal_execution_capsule_authz_release_attestation_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authorization: bool = False,
    authz_final_authorization_expected_execution_capsule_authz_release_seal_hash_override: (
        str | None
    ) = None,
    authz_final_authorization_execution_capsule_authz_release_seal_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_export: bool = False,
    authz_final_export_expected_execution_capsule_authz_final_authz_hash_override: (
        str | None
    ) = None,
    authz_final_export_execution_capsule_authz_final_authz_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_handoff_packet: bool = False,
    authz_final_handoff_expected_execution_capsule_authz_final_authz_export_hash_override: (
        str | None
    ) = None,
    authz_final_handoff_execution_capsule_authz_final_authz_export_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_operator_review: bool = False,
    authz_final_review_expected_execution_capsule_authz_final_authz_handoff_hash_override: (
        str | None
    ) = None,
    authz_final_review_execution_capsule_authz_final_authz_handoff_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_operator_decision: bool = False,
    authz_final_decision_expected_execution_capsule_authz_final_authz_operator_review_hash_override: (
        str | None
    ) = None,
    authz_final_decision_execution_capsule_authz_final_authz_operator_review_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_release_attestation: bool = False,
    authz_final_attestation_expected_execution_capsule_authz_final_authz_operator_decision_hash_override: (
        str | None
    ) = None,
    authz_final_attestation_execution_capsule_authz_final_authz_operator_decision_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_release_seal: bool = False,
    authz_final_seal_expected_execution_capsule_authz_final_authz_release_attestation_hash_override: (
        str | None
    ) = None,
    authz_final_seal_execution_capsule_authz_final_authz_release_attestation_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization: bool = False,
    authz_final_final_expected_execution_capsule_authz_final_authz_release_seal_hash_override: (
        str | None
    ) = None,
    authz_final_final_execution_capsule_authz_final_authz_release_seal_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_export: bool = False,
    authz_final_export_expected_execution_capsule_authz_final_authz_final_authz_hash_override: (
        str | None
    ) = None,
    authz_final_export_execution_capsule_authz_final_authz_final_authz_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_handoff_packet: bool = False,
    authz_final_handoff_expected_execution_capsule_authz_final_authz_final_authz_export_hash_override: (
        str | None
    ) = None,
    authz_final_handoff_execution_capsule_authz_final_authz_final_authz_export_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_operator_review: bool = False,
    authz_final_review_expected_execution_capsule_authz_final_authz_final_authz_handoff_hash_override: (
        str | None
    ) = None,
    authz_final_review_execution_capsule_authz_final_authz_final_authz_handoff_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_operator_decision: bool = False,
    authz_final_decision_expected_execution_capsule_authz_final_authz_final_authz_operator_review_hash_override: (
        str | None
    ) = None,
    authz_final_decision_execution_capsule_authz_final_authz_final_authz_operator_review_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_release_attestation: bool = False,
    authz_final_final_attestation_expected_execution_capsule_authz_final_authz_final_authz_operator_decision_hash_override: (
        str | None
    ) = None,
    authz_final_final_attestation_execution_capsule_authz_final_authz_final_authz_operator_decision_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_release_seal: bool = False,
    authz_final_final_seal_expected_execution_capsule_authz_final_authz_final_authz_release_attestation_hash_override: (
        str | None
    ) = None,
    authz_final_final_seal_execution_capsule_authz_final_authz_final_authz_release_attestation_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_final_authorization: bool = False,
    authz_final_final_authz_expected_execution_capsule_authz_final_authz_final_authz_release_seal_hash_override: (
        str | None
    ) = None,
    authz_final_final_authz_execution_capsule_authz_final_authz_final_authz_release_seal_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_final_authorization_export: bool = False,
    authz_final_final_authz_export_expected_execution_capsule_authz_final_authz_final_authz_final_authz_hash_override: (
        str | None
    ) = None,
    authz_final_final_authz_export_execution_capsule_authz_final_authz_final_authz_final_authz_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet: bool = False,
    authz_final_final_authz_handoff_expected_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash_override: (
        str | None
    ) = None,
    authz_final_final_authz_handoff_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review: bool = False,
    authz_final_final_authz_review_expected_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash_override: (
        str | None
    ) = None,
    authz_final_final_authz_review_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision: bool = False,
    authz_final_final_authz_decision_expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash_override: (
        str | None
    ) = None,
    authz_final_final_authz_decision_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation: bool = False,
    authz_final_final_authz_attestation_expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash_override: (
        str | None
    ) = None,
    authz_final_final_authz_attestation_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal: bool = False,
    authz_final_final_authz_seal_expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash_override: (
        str | None
    ) = None,
    authz_final_final_authz_seal_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization: bool = False,
    authz_final_final_authz_final_expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash_override: (
        str | None
    ) = None,
    authz_final_final_authz_final_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export: bool = False,
    authz_final_final_authz_final_export_expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash_override: (
        str | None
    ) = None,
    authz_final_final_authz_final_export_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash_override: (
        str | None
    ) = None,
    include_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_handoff_packet: bool = False,
    authz_final_final_authz_final_handoff_expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash_override: (
        str | None
    ) = None,
    authz_final_final_authz_final_handoff_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash_override: (
        str | None
    ) = None,
) -> dict:
    payload = {
        "run_id": run_id,
        "prompt_contract_hash": prompt_contract_hash or _prompt_contract_hash(),
        "runtime_mode": "live_admission_precheck",
        "response_summary": "API05 sanitized provider envelope precheck summary",
        "policy": {
            "request_timeout_seconds": 30,
            "max_cost_units": 1,
            "max_live_api_calls": 1,
            "max_output_tokens": 512,
            "retry_count": 0,
        },
        "live_open_controls": {field_name: True for field_name in LIVE_OPEN_REQUIRED_CONTROLS},
        "approval": {
            "approved_by": "local-user",
            "approved_at": "2026-06-01T00:00:00Z",
            "run_id": run_id,
            "provider_name": "solar-pro-3",
            "model_name": "solar-pro-3",
            "mode": "live",
            "env_key_name": "UPSTAGE_API_KEY",
            "max_live_api_calls": 1,
            "max_live_llm_calls": 1,
            "expires_at": "2099-01-01T00:00:00Z",
            "audit_log_id": f"audit-{run_id}",
            "signature_id": f"sig-{run_id}",
            "signed_contract_hash": stable_contract_hash(
                {
                    "run_id": run_id,
                    "purpose": "api provider envelope precheck",
                }
            ),
            "nonce": f"nonce-{run_id}",
        },
        "raw_prompt": "API05_RAW_PROMPT_SENTINEL",
        "provider_payload": {"body": "API05_PROVIDER_PAYLOAD_SENTINEL"},
        "provider_body": "API05_PROVIDER_BODY_SENTINEL",
    }
    if include_operator_approval:
        policy_summary = provider_precheck_operator_policy_summary(payload)
        payload["operator_approval"] = {
            "operator_ref": "local-operator",
            "approved_at": "2026-06-01T00:00:00Z",
            "decision": "approved",
            "approved_policy_summary_hash": (
                approved_policy_summary_hash or policy_summary["policy_summary_hash"]
            ),
            "authorization_material": "API06_OPERATOR_AUTH_SENTINEL",
        }
    if include_manual_test_proposal:
        payload["manual_test_proposal"] = {
            "proposal_id": f"proposal-{run_id}",
            "run_id": run_id,
            "prompt_contract_hash": payload["prompt_contract_hash"],
            "provider_name": "solar-pro-3",
            "model_name": "solar-pro-3",
            "request_timeout_seconds": 30,
            "max_cost_units": 1,
            "max_live_api_calls": 1,
            "max_output_unit_budget": 512,
            "rollback_plan_id": f"rollback-{run_id}",
            "abort_criteria": [
                "API08_ABORT_CRITERIA_SENTINEL",
                "stop on timeout, quota, or unexpected provider error",
            ],
        }
        if include_manual_test_operator_approval:
            proposal_summary = provider_manual_test_proposal_summary(payload)
            payload["manual_test_operator_approval"] = {
                "operator_ref": "local-operator",
                "approved_at": "2026-06-01T00:05:00Z",
                "decision": "approved",
                "approved_proposal_hash": proposal_summary["proposal_hash"],
                "authorization_material": "API08_MANUAL_TEST_AUTH_SENTINEL",
            }
    if manual_test_executor_enable:
        payload["manual_test_executor_enable"] = True
    if include_one_shot_live_permission:
        proposal_summary = provider_manual_test_proposal_summary(payload)
        planned_call_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_EXECUTOR_VERSION,
                "run_id": run_id,
                "prompt_contract_hash": payload["prompt_contract_hash"],
                "provider_name": "solar-pro-3",
                "model_name": "solar-pro-3",
                "proposal_hash": proposal_summary["proposal_hash"],
                "executor_enable_requested": bool(manual_test_executor_enable),
            }
        )
        payload["one_shot_live_permission"] = {
            "run_id": run_id,
            "proposal_hash": proposal_summary["proposal_hash"],
            "planned_call_hash": planned_call_hash,
            "request_timeout_seconds": 30,
            "max_cost_units": 1,
            "max_live_api_calls": 1,
            "max_output_unit_budget": 512,
            "rollback_plan_id": f"rollback-{run_id}",
            "abort_criteria_hash": proposal_summary["proposal_fields"]["abort_criteria_hash"],
            "abort_criteria_count": 2,
            "expires_at": "2099-01-01T00:00:00Z",
            "authorization_material": "API10_PERMISSION_AUTH_SENTINEL",
            "provider_payload": "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_readiness_decision:
        preflight_summary = provider_manual_test_preflight_summary(payload)
        payload["manual_test_readiness_decision"] = {
            "preflight_audit_hash": (
                readiness_preflight_hash_override
                or preflight_summary["preflight_audit_hash"]
            ),
            "decision": readiness_decision,
            "operator_ref": "local-operator",
            "decided_at": "2026-06-01T00:10:00Z",
            "decision_reason_code": "manual-provider-test-candidate-reviewed",
            "authorization_material": "API12_READINESS_AUTH_SENTINEL",
            "provider_payload": "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_operator_opt_in:
        handoff_summary = provider_manual_test_handoff_packet_summary(payload)
        payload["manual_test_operator_opt_in"] = {
            "handoff_packet_hash": (
                operator_opt_in_handoff_hash_override
                or handoff_summary["handoff_packet_hash"]
            ),
            "decision": "opt_in",
            "operator_ref": "local-operator",
            "opted_in_at": "2026-06-01T00:15:00Z",
            "authorization_material": "API16_OPT_IN_AUTH_SENTINEL",
            "provider_payload": "API16_OPT_IN_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_sealed_pre_execution_packet:
        operator_opt_in_summary = provider_manual_test_operator_opt_in_summary(payload)
        payload["expected_operator_opt_in_hash"] = (
            sealed_operator_opt_in_hash_override
            or operator_opt_in_summary["operator_opt_in_hash"]
        )
        payload["manual_test_sealed_pre_execution_packet"] = {
            "authorization_material": "API17_SEALED_AUTH_SENTINEL",
            "provider_payload": "API17_SEALED_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_arming_record:
        sealed_summary = provider_manual_test_sealed_pre_execution_packet_summary(payload)
        abort_policy_hash = stable_contract_hash(
            {
                "abort_policy": "manual-provider-test-stop-policy",
                "run_id": run_id,
            }
        )
        payload["expected_sealed_packet_hash"] = (
            arming_expected_sealed_hash_override
            or sealed_summary["sealed_packet_hash"]
        )
        payload["manual_test_live_execution_arming"] = {
            "sealed_packet_hash": (
                arming_record_sealed_hash_override
                or sealed_summary["sealed_packet_hash"]
            ),
            "operator_ref": "local-operator",
            "armed_at": "2026-06-01T00:20:00Z",
            "expires_at": "2026-06-01T00:25:00Z",
            "rollback_abort_hash": sealed_summary["rollback_abort_hash"],
            "abort_policy_hash": abort_policy_hash,
            "authorization_material": "API18_ARMING_AUTH_SENTINEL",
            "provider_payload": "API18_ARMING_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_release_proposal:
        arming_summary = provider_manual_test_arming_record_summary(payload)
        payload["expected_arming_record_hash"] = (
            release_expected_arming_hash_override
            or arming_summary["arming_record_hash"]
        )
        payload["manual_test_execution_release_proposal"] = {
            "arming_record_hash": (
                release_proposal_arming_hash_override
                or arming_summary["arming_record_hash"]
            ),
            "operator_ref": "local-operator",
            "proposed_at": "2026-06-01T00:30:00Z",
            "release_window_start": "2026-06-01T00:35:00Z",
            "release_window_end": "2026-06-01T00:40:00Z",
            "rollback_abort_hash": arming_summary["rollback_abort_hash"],
            "authorization_material": "API19_RELEASE_AUTH_SENTINEL",
            "provider_payload": "API19_RELEASE_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_final_release_packet:
        release_summary = provider_manual_test_release_proposal_summary(payload)
        payload["expected_release_proposal_hash"] = (
            final_expected_release_hash_override
            or release_summary["release_proposal_hash"]
        )
        payload["manual_test_final_release_packet"] = {
            "release_proposal_hash": (
                final_packet_release_hash_override
                or release_summary["release_proposal_hash"]
            ),
            "authorization_material": "API20_FINAL_RELEASE_AUTH_SENTINEL",
            "provider_payload": "API20_FINAL_RELEASE_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_switch:
        final_summary = provider_manual_test_final_release_packet_summary(payload)
        payload["expected_final_release_packet_hash"] = (
            execution_switch_expected_final_hash_override
            or final_summary["final_release_packet_hash"]
        )
        payload["manual_test_execution_switch"] = {
            "final_release_packet_hash": (
                execution_switch_final_hash_override
                or final_summary["final_release_packet_hash"]
            ),
            "authorization_material": "API21_SWITCH_AUTH_SENTINEL",
            "provider_payload": "API21_SWITCH_PROVIDER_PAYLOAD_SENTINEL",
        }
        if execution_switch_enable:
            payload["manual_test_execution_switch"]["enable_requested"] = True
    if include_executor_preflight:
        switch_summary = provider_manual_test_execution_switch_summary(payload)
        payload["expected_execution_switch_hash"] = (
            executor_preflight_expected_switch_hash_override
            or switch_summary["execution_switch_hash"]
        )
        payload["manual_test_executor_preflight"] = {
            "execution_switch_hash": (
                executor_preflight_switch_hash_override
                or switch_summary["execution_switch_hash"]
            ),
            "authorization_material": "API22_PREFLIGHT_AUTH_SENTINEL",
            "provider_payload": "API22_PREFLIGHT_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_executor_dispatch_record:
        preflight_summary = provider_manual_test_executor_preflight_summary(payload)
        payload["expected_executor_preflight_hash"] = (
            executor_dispatch_expected_preflight_hash_override
            or preflight_summary["executor_preflight_hash"]
        )
        payload["manual_test_executor_dispatch_record"] = {
            "executor_preflight_hash": (
                executor_dispatch_preflight_hash_override
                or preflight_summary["executor_preflight_hash"]
            ),
            "dispatch_requested": True,
            "authorization_material": "API23_DISPATCH_AUTH_SENTINEL",
            "provider_payload": "API23_DISPATCH_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_invocation_receipt:
        dispatch_summary = provider_manual_test_executor_dispatch_record_summary(
            payload
        )
        payload["expected_dispatch_record_hash"] = (
            invocation_receipt_expected_dispatch_hash_override
            or dispatch_summary["dispatch_record_hash"]
        )
        payload["manual_test_executor_invocation_receipt"] = {
            "dispatch_record_hash": (
                invocation_receipt_dispatch_hash_override
                or dispatch_summary["dispatch_record_hash"]
            ),
            "receipt_requested": True,
            "authorization_material": "API24_RECEIPT_AUTH_SENTINEL",
            "provider_payload": "API24_RECEIPT_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_post_invocation_audit:
        receipt_summary = provider_manual_test_invocation_receipt_summary(payload)
        payload["expected_invocation_receipt_hash"] = (
            post_invocation_expected_receipt_hash_override
            or receipt_summary["invocation_receipt_hash"]
        )
        payload["manual_test_post_invocation_audit"] = {
            "invocation_receipt_hash": (
                post_invocation_receipt_hash_override
                or receipt_summary["invocation_receipt_hash"]
            ),
            "audit_requested": True,
            "authorization_material": "API25_AUDIT_AUTH_SENTINEL",
            "provider_payload": "API25_AUDIT_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_completion_summary:
        audit_summary = provider_manual_test_post_invocation_audit_summary(payload)
        payload["expected_post_invocation_audit_hash"] = (
            completion_expected_audit_hash_override
            or audit_summary["post_invocation_audit_hash"]
        )
        payload["manual_test_completion_summary"] = {
            "post_invocation_audit_hash": (
                completion_audit_hash_override
                or audit_summary["post_invocation_audit_hash"]
            ),
            "summary_requested": True,
            "authorization_material": "API26_COMPLETION_AUTH_SENTINEL",
            "provider_payload": "API26_COMPLETION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_closeout_record:
        completion_summary = provider_manual_test_completion_summary(payload)
        payload["expected_completion_summary_hash"] = (
            closeout_expected_summary_hash_override
            or completion_summary["completion_summary_hash"]
        )
        payload["manual_test_closeout_record"] = {
            "completion_summary_hash": (
                closeout_summary_hash_override
                or completion_summary["completion_summary_hash"]
            ),
            "closeout_requested": True,
            "authorization_material": "API27_CLOSEOUT_AUTH_SENTINEL",
            "provider_payload": "API27_CLOSEOUT_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_operator_handback:
        closeout_summary = provider_manual_test_closeout_record_summary(payload)
        payload["expected_closeout_record_hash"] = (
            handback_expected_closeout_hash_override
            or closeout_summary["closeout_record_hash"]
        )
        payload["manual_test_operator_handback"] = {
            "closeout_record_hash": (
                handback_closeout_hash_override
                or closeout_summary["closeout_record_hash"]
            ),
            "handback_requested": True,
            "operator_review": {
                "review_decision": "acknowledged",
                "review_reason_code": "local-no-call-handback-reviewed",
                "reviewed_at": "2026-06-01T00:50:00Z",
                "operator_ref": "API28_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API28_HANDBACK_AUTH_SENTINEL",
            "provider_payload": "API28_HANDBACK_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_operator_decision_packet:
        handback_summary = provider_manual_test_operator_handback_summary(payload)
        payload["expected_operator_handback_hash"] = (
            decision_expected_handback_hash_override
            or handback_summary["operator_handback_hash"]
        )
        payload["manual_test_operator_decision_packet"] = {
            "operator_handback_hash": (
                decision_packet_handback_hash_override
                or handback_summary["operator_handback_hash"]
            ),
            "packet_requested": True,
            "operator_decision": {
                "decision": "acknowledged",
                "decision_reason_code": "local-no-call-decision-reviewed",
                "decided_at": "2026-06-01T00:55:00Z",
                "operator_ref": "API29_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API29_DECISION_AUTH_SENTINEL",
            "provider_payload": "API29_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_operator_release_attestation:
        decision_packet_summary = provider_manual_test_operator_decision_packet_summary(
            payload
        )
        payload["expected_operator_decision_packet_hash"] = (
            attestation_expected_decision_packet_hash_override
            or decision_packet_summary["operator_decision_packet_hash"]
        )
        payload["manual_test_operator_release_attestation"] = {
            "operator_decision_packet_hash": (
                attestation_decision_packet_hash_override
                or decision_packet_summary["operator_decision_packet_hash"]
            ),
            "attestation_requested": True,
            "operator_attestation": {
                "attestation": "release_acknowledged",
                "attestation_reason_code": "local-no-call-release-attested",
                "attested_at": "2026-06-01T01:00:00Z",
                "operator_ref": "API30_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API30_ATTESTATION_AUTH_SENTINEL",
            "provider_payload": "API30_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_release_authorization_seal:
        release_attestation_summary = (
            provider_manual_test_operator_release_attestation_summary(payload)
        )
        payload["expected_operator_release_attestation_hash"] = (
            seal_expected_release_attestation_hash_override
            or release_attestation_summary["operator_release_attestation_hash"]
        )
        payload["manual_test_release_authorization_seal"] = {
            "operator_release_attestation_hash": (
                seal_release_attestation_hash_override
                or release_attestation_summary["operator_release_attestation_hash"]
            ),
            "seal_requested": True,
            "seal_material": {
                "seal_decision": "sealed",
                "seal_reason_code": "local-no-call-release-sealed",
                "sealed_at": "2026-06-01T01:05:00Z",
                "operator_ref": "API31_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API31_SEAL_AUTH_SENTINEL",
            "provider_payload": "API31_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_authorization_capsule:
        seal_summary = provider_manual_test_release_authorization_seal_summary(
            payload
        )
        payload["expected_release_seal_hash"] = (
            capsule_expected_release_seal_hash_override
            or seal_summary["release_seal_hash"]
        )
        payload["manual_test_execution_authorization_capsule"] = {
            "release_seal_hash": (
                capsule_release_seal_hash_override
                or seal_summary["release_seal_hash"]
            ),
            "capsule_requested": True,
            "final_authorization": {
                "decision": "sealed",
                "reason_code": "local-no-call-execution-capsule-sealed",
                "authorized_at": "2026-06-01T01:10:00Z",
                "operator_ref": "API32_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API32_CAPSULE_AUTH_SENTINEL",
            "provider_payload": "API32_CAPSULE_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_export:
        capsule_summary = provider_manual_test_execution_authorization_capsule_summary(
            payload
        )
        payload["expected_execution_capsule_hash"] = (
            export_expected_execution_capsule_hash_override
            or capsule_summary["execution_capsule_hash"]
        )
        payload["manual_test_execution_capsule_export"] = {
            "execution_capsule_hash": (
                export_execution_capsule_hash_override
                or capsule_summary["execution_capsule_hash"]
            ),
            "export_requested": True,
            "export_metadata": {
                "export_kind": "read_model_projection",
                "export_reason_code": "local-no-call-capsule-exported",
                "exported_at": "2026-06-01T01:15:00Z",
                "operator_ref": "API33_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API33_EXPORT_AUTH_SENTINEL",
            "provider_payload": "API33_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_handoff_packet:
        export_summary = provider_manual_test_execution_capsule_export_summary(payload)
        payload["expected_execution_capsule_export_hash"] = (
            handoff_expected_execution_capsule_export_hash_override
            or export_summary["execution_capsule_export_hash"]
        )
        payload["manual_test_execution_capsule_handoff_packet"] = {
            "execution_capsule_export_hash": (
                handoff_execution_capsule_export_hash_override
                or export_summary["execution_capsule_export_hash"]
            ),
            "handoff_requested": True,
            "handoff_material": "API34_HANDOFF_MATERIAL_SENTINEL",
            "provider_payload": "API34_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_operator_review:
        handoff_summary = provider_manual_test_execution_capsule_handoff_packet_summary(
            payload
        )
        payload["expected_execution_capsule_handoff_packet_hash"] = (
            review_expected_execution_capsule_handoff_hash_override
            or handoff_summary["execution_capsule_handoff_packet_hash"]
        )
        payload["manual_test_execution_capsule_operator_review"] = {
            "execution_capsule_handoff_packet_hash": (
                review_execution_capsule_handoff_hash_override
                or handoff_summary["execution_capsule_handoff_packet_hash"]
            ),
            "review_requested": True,
            "operator_review": {
                "review_decision": "reviewed",
                "review_reason_code": "local-no-call-capsule-operator-reviewed",
                "reviewed_at": "2026-06-01T01:25:00Z",
                "operator_ref": "API35_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API35_REVIEW_AUTH_SENTINEL",
            "provider_payload": "API35_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_operator_decision:
        review_summary = provider_manual_test_execution_capsule_operator_review_summary(
            payload
        )
        payload["expected_execution_capsule_operator_review_hash"] = (
            decision_expected_execution_capsule_operator_review_hash_override
            or review_summary["execution_capsule_operator_review_hash"]
        )
        payload["manual_test_execution_capsule_operator_decision"] = {
            "execution_capsule_operator_review_hash": (
                decision_execution_capsule_operator_review_hash_override
                or review_summary["execution_capsule_operator_review_hash"]
            ),
            "decision_requested": True,
            "operator_decision": {
                "decision": "reviewed",
                "decision_reason_code": "local-no-call-capsule-operator-decided",
                "decided_at": "2026-06-01T01:30:00Z",
                "operator_ref": "API36_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API36_DECISION_AUTH_SENTINEL",
            "provider_payload": "API36_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_release_attestation:
        decision_summary = (
            provider_manual_test_execution_capsule_operator_decision_summary(payload)
        )
        payload["expected_execution_capsule_operator_decision_hash"] = (
            release_attestation_expected_execution_capsule_operator_decision_hash_override
            or decision_summary["execution_capsule_operator_decision_hash"]
        )
        payload["manual_test_execution_capsule_release_attestation"] = {
            "execution_capsule_operator_decision_hash": (
                release_attestation_execution_capsule_operator_decision_hash_override
                or decision_summary["execution_capsule_operator_decision_hash"]
            ),
            "attestation_requested": True,
            "release_attestation": {
                "attestation": "release_attested",
                "attestation_reason_code": (
                    "local-no-call-capsule-release-attested"
                ),
                "attested_at": "2026-06-01T01:35:00Z",
                "operator_ref": "API37_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API37_ATTESTATION_AUTH_SENTINEL",
            "provider_payload": "API37_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_release_seal:
        attestation_summary = (
            provider_manual_test_execution_capsule_release_attestation_summary(
                payload
            )
        )
        payload["expected_execution_capsule_release_attestation_hash"] = (
            release_seal_expected_execution_capsule_release_attestation_hash_override
            or attestation_summary["execution_capsule_release_attestation_hash"]
        )
        payload["manual_test_execution_capsule_release_seal"] = {
            "execution_capsule_release_attestation_hash": (
                release_seal_execution_capsule_release_attestation_hash_override
                or attestation_summary["execution_capsule_release_attestation_hash"]
            ),
            "seal_requested": True,
            "seal_material": {
                "seal_decision": "sealed",
                "seal_reason_code": "local-no-call-capsule-release-sealed",
                "sealed_at": "2026-06-01T01:40:00Z",
                "operator_ref": "API38_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API38_SEAL_AUTH_SENTINEL",
            "provider_payload": "API38_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_final_authorization:
        release_seal_summary = (
            provider_manual_test_execution_capsule_release_seal_summary(payload)
        )
        payload["expected_execution_capsule_release_seal_hash"] = (
            final_authorization_expected_execution_capsule_release_seal_hash_override
            or release_seal_summary["execution_capsule_release_seal_hash"]
        )
        payload["manual_test_execution_capsule_final_authorization"] = {
            "execution_capsule_release_seal_hash": (
                final_authorization_execution_capsule_release_seal_hash_override
                or release_seal_summary["execution_capsule_release_seal_hash"]
            ),
            "authorization_requested": True,
            "final_authorization": {
                "authorization_decision": "authorized",
                "authorization_reason_code": (
                    "local-no-call-capsule-final-authorized"
                ),
                "authorized_at": "2026-06-01T01:45:00Z",
                "operator_ref": "API39_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API39_FINAL_AUTH_SENTINEL",
            "provider_payload": "API39_FINAL_AUTH_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_export:
        final_authz_summary = (
            provider_manual_test_execution_capsule_final_authorization_summary(
                payload
            )
        )
        payload["expected_execution_capsule_final_authz_hash"] = (
            authz_export_expected_execution_capsule_final_authz_hash_override
            or final_authz_summary["execution_capsule_final_authz_hash"]
        )
        payload["manual_test_execution_capsule_authz_export"] = {
            "execution_capsule_final_authz_hash": (
                authz_export_execution_capsule_final_authz_hash_override
                or final_authz_summary["execution_capsule_final_authz_hash"]
            ),
            "export_requested": True,
            "export_metadata": {
                "export_kind": "authz_read_model",
                "export_reason_code": "local-no-call-capsule-authz-exported",
                "exported_at": "2026-06-01T01:50:00Z",
                "operator_ref": "API40_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API40_EXPORT_AUTH_SENTINEL",
            "provider_payload": "API40_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_handoff_packet:
        authz_export_summary = provider_manual_test_execution_capsule_authz_export_summary(
            payload
        )
        payload["expected_execution_capsule_authz_export_hash"] = (
            authz_handoff_expected_execution_capsule_authz_export_hash_override
            or authz_export_summary["execution_capsule_authz_export_hash"]
        )
        payload["manual_test_execution_capsule_authz_handoff_packet"] = {
            "execution_capsule_authz_export_hash": (
                authz_handoff_execution_capsule_authz_export_hash_override
                or authz_export_summary["execution_capsule_authz_export_hash"]
            ),
            "handoff_requested": True,
            "handoff_material": "API41_HANDOFF_MATERIAL_SENTINEL",
            "authorization_material": "API41_HANDOFF_AUTH_SENTINEL",
            "provider_payload": "API41_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_operator_review:
        authz_handoff_summary = (
            provider_manual_test_execution_capsule_authz_handoff_packet_summary(
                payload
            )
        )
        payload["expected_execution_capsule_authz_handoff_packet_hash"] = (
            authz_review_expected_execution_capsule_authz_handoff_hash_override
            or authz_handoff_summary[
                "execution_capsule_authz_handoff_packet_hash"
            ]
        )
        payload["manual_test_execution_capsule_authz_operator_review"] = {
            "execution_capsule_authz_handoff_packet_hash": (
                authz_review_execution_capsule_authz_handoff_hash_override
                or authz_handoff_summary[
                    "execution_capsule_authz_handoff_packet_hash"
                ]
            ),
            "review_requested": True,
            "operator_review": {
                "review_decision": "reviewed",
                "review_reason_code": "local-no-call-capsule-authz-reviewed",
                "reviewed_at": "2026-06-01T01:55:00Z",
                "operator_ref": "API42_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API42_REVIEW_AUTH_SENTINEL",
            "provider_payload": "API42_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_operator_decision:
        authz_review_summary = (
            provider_manual_test_execution_capsule_authz_operator_review_summary(
                payload
            )
        )
        payload["expected_execution_capsule_authz_operator_review_hash"] = (
            authz_decision_expected_execution_capsule_authz_operator_review_hash_override
            or authz_review_summary["execution_capsule_authz_operator_review_hash"]
        )
        payload["manual_test_execution_capsule_authz_operator_decision"] = {
            "execution_capsule_authz_operator_review_hash": (
                authz_decision_execution_capsule_authz_operator_review_hash_override
                or authz_review_summary["execution_capsule_authz_operator_review_hash"]
            ),
            "decision_requested": True,
            "operator_decision": {
                "decision": "reviewed",
                "decision_reason_code": "local-no-call-capsule-authz-decided",
                "decided_at": "2026-06-01T02:00:00Z",
                "operator_ref": "API43_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API43_DECISION_AUTH_SENTINEL",
            "provider_payload": "API43_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_release_attestation:
        authz_decision_summary = (
            provider_manual_test_execution_capsule_authz_operator_decision_summary(
                payload
            )
        )
        payload["expected_execution_capsule_authz_operator_decision_hash"] = (
            authz_attestation_expected_execution_capsule_authz_operator_decision_hash_override
            or authz_decision_summary[
                "execution_capsule_authz_operator_decision_hash"
            ]
        )
        payload["manual_test_execution_capsule_authz_release_attestation"] = {
            "execution_capsule_authz_operator_decision_hash": (
                authz_attestation_execution_capsule_authz_operator_decision_hash_override
                or authz_decision_summary[
                    "execution_capsule_authz_operator_decision_hash"
                ]
            ),
            "attestation_requested": True,
            "release_attestation": {
                "attestation": "release_attested",
                "attestation_reason_code": (
                    "local-no-call-capsule-authz-release-attested"
                ),
                "attested_at": "2026-06-01T02:05:00Z",
                "operator_ref": "API44_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API44_ATTESTATION_AUTH_SENTINEL",
            "provider_payload": "API44_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_release_seal:
        authz_attestation_summary = (
            provider_manual_test_execution_capsule_authz_release_attestation_summary(
                payload
            )
        )
        payload["expected_execution_capsule_authz_release_attestation_hash"] = (
            authz_release_seal_expected_execution_capsule_authz_release_attestation_hash_override
            or authz_attestation_summary[
                "execution_capsule_authz_release_attestation_hash"
            ]
        )
        payload["manual_test_execution_capsule_authz_release_seal"] = {
            "execution_capsule_authz_release_attestation_hash": (
                authz_release_seal_execution_capsule_authz_release_attestation_hash_override
                or authz_attestation_summary[
                    "execution_capsule_authz_release_attestation_hash"
                ]
            ),
            "seal_requested": True,
            "seal_material": {
                "seal_decision": "sealed",
                "seal_reason_code": "local-no-call-capsule-authz-release-sealed",
                "sealed_at": "2026-06-01T02:10:00Z",
                "operator_ref": "API45_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API45_SEAL_AUTH_SENTINEL",
            "provider_payload": "API45_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authorization:
        authz_release_seal_summary = (
            provider_manual_test_execution_capsule_authz_release_seal_summary(
                payload
            )
        )
        payload["expected_execution_capsule_authz_release_seal_hash"] = (
            authz_final_authorization_expected_execution_capsule_authz_release_seal_hash_override
            or authz_release_seal_summary[
                "execution_capsule_authz_release_seal_hash"
            ]
        )
        payload["manual_test_execution_capsule_authz_final_authorization"] = {
            "execution_capsule_authz_release_seal_hash": (
                authz_final_authorization_execution_capsule_authz_release_seal_hash_override
                or authz_release_seal_summary[
                    "execution_capsule_authz_release_seal_hash"
                ]
            ),
            "authorization_requested": True,
            "final_authorization": {
                "authorization_decision": "authorized",
                "authorization_reason_code": (
                    "local-no-call-capsule-authz-final-authorized"
                ),
                "authorized_at": "2026-06-01T02:15:00Z",
                "operator_ref": "API46_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API46_FINAL_AUTH_SENTINEL",
            "provider_payload": "API46_FINAL_AUTH_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_export:
        authz_final_summary = (
            provider_manual_test_execution_capsule_authz_final_authorization_summary(
                payload
            )
        )
        payload["expected_execution_capsule_authz_final_authz_hash"] = (
            authz_final_export_expected_execution_capsule_authz_final_authz_hash_override
            or authz_final_summary["execution_capsule_authz_final_authz_hash"]
        )
        payload["manual_test_execution_capsule_authz_final_authz_export"] = {
            "execution_capsule_authz_final_authz_hash": (
                authz_final_export_execution_capsule_authz_final_authz_hash_override
                or authz_final_summary["execution_capsule_authz_final_authz_hash"]
            ),
            "export_requested": True,
            "export_metadata": {
                "export_kind": "authz_final_read_model",
                "export_reason_code": (
                    "local-no-call-capsule-authz-final-exported"
                ),
                "exported_at": "2026-06-01T02:20:00Z",
                "operator_ref": "API47_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API47_EXPORT_AUTH_SENTINEL",
            "provider_payload": "API47_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_handoff_packet:
        authz_final_export_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_export_summary(
                payload
            )
        )
        payload["expected_execution_capsule_authz_final_authz_export_hash"] = (
            authz_final_handoff_expected_execution_capsule_authz_final_authz_export_hash_override
            or authz_final_export_summary[
                "execution_capsule_authz_final_authz_export_hash"
            ]
        )
        payload["manual_test_execution_capsule_authz_final_authz_handoff_packet"] = {
            "execution_capsule_authz_final_authz_export_hash": (
                authz_final_handoff_execution_capsule_authz_final_authz_export_hash_override
                or authz_final_export_summary[
                    "execution_capsule_authz_final_authz_export_hash"
                ]
            ),
            "handoff_requested": True,
            "authorization_material": "API48_HANDOFF_AUTH_SENTINEL",
            "provider_payload": "API48_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_operator_review:
        authz_final_handoff_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_handoff_packet_summary(
                payload
            )
        )
        payload["expected_execution_capsule_authz_final_authz_handoff_packet_hash"] = (
            authz_final_review_expected_execution_capsule_authz_final_authz_handoff_hash_override
            or authz_final_handoff_summary[
                "execution_capsule_authz_final_authz_handoff_packet_hash"
            ]
        )
        payload["manual_test_execution_capsule_authz_final_authz_operator_review"] = {
            "execution_capsule_authz_final_authz_handoff_packet_hash": (
                authz_final_review_execution_capsule_authz_final_authz_handoff_hash_override
                or authz_final_handoff_summary[
                    "execution_capsule_authz_final_authz_handoff_packet_hash"
                ]
            ),
            "review_requested": True,
            "operator_review": {
                "review_decision": "reviewed",
                "review_reason_code": (
                    "local-no-call-capsule-authz-final-reviewed"
                ),
                "reviewed_at": "2026-06-01T02:25:00Z",
                "operator_ref": "API49_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API49_REVIEW_AUTH_SENTINEL",
            "provider_payload": "API49_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_operator_decision:
        authz_final_review_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_operator_review_summary(
                payload
            )
        )
        payload["expected_execution_capsule_authz_final_authz_operator_review_hash"] = (
            authz_final_decision_expected_execution_capsule_authz_final_authz_operator_review_hash_override
            or authz_final_review_summary[
                "execution_capsule_authz_final_authz_operator_review_hash"
            ]
        )
        payload["manual_test_execution_capsule_authz_final_authz_operator_decision"] = {
            "execution_capsule_authz_final_authz_operator_review_hash": (
                authz_final_decision_execution_capsule_authz_final_authz_operator_review_hash_override
                or authz_final_review_summary[
                    "execution_capsule_authz_final_authz_operator_review_hash"
                ]
            ),
            "decision_requested": True,
            "operator_decision": {
                "decision": "reviewed",
                "decision_reason_code": (
                    "local-no-call-capsule-authz-final-decided"
                ),
                "decided_at": "2026-06-01T02:30:00Z",
                "operator_ref": "API50_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API50_DECISION_AUTH_SENTINEL",
            "provider_payload": "API50_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_release_attestation:
        authz_final_decision_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_operator_decision_summary(
                payload
            )
        )
        payload["expected_execution_capsule_authz_final_authz_operator_decision_hash"] = (
            authz_final_attestation_expected_execution_capsule_authz_final_authz_operator_decision_hash_override
            or authz_final_decision_summary[
                "execution_capsule_authz_final_authz_operator_decision_hash"
            ]
        )
        payload["manual_test_execution_capsule_authz_final_authz_release_attestation"] = {
            "execution_capsule_authz_final_authz_operator_decision_hash": (
                authz_final_attestation_execution_capsule_authz_final_authz_operator_decision_hash_override
                or authz_final_decision_summary[
                    "execution_capsule_authz_final_authz_operator_decision_hash"
                ]
            ),
            "attestation_requested": True,
            "release_attestation": {
                "attestation": "attested",
                "attestation_reason_code": (
                    "local-no-call-capsule-authz-final-release-attested"
                ),
                "attested_at": "2026-06-01T02:35:00Z",
                "operator_ref": "API51_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API51_ATTESTATION_AUTH_SENTINEL",
            "provider_payload": "API51_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_release_seal:
        authz_final_attestation_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_release_attestation_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_release_attestation_hash"
        ] = (
            authz_final_seal_expected_execution_capsule_authz_final_authz_release_attestation_hash_override
            or authz_final_attestation_summary[
                "execution_capsule_authz_final_authz_release_attestation_hash"
            ]
        )
        payload["manual_test_execution_capsule_authz_final_authz_release_seal"] = {
            "execution_capsule_authz_final_authz_release_attestation_hash": (
                authz_final_seal_execution_capsule_authz_final_authz_release_attestation_hash_override
                or authz_final_attestation_summary[
                    "execution_capsule_authz_final_authz_release_attestation_hash"
                ]
            ),
            "seal_requested": True,
            "seal_material": {
                "seal_decision": "sealed",
                "seal_reason_code": (
                    "local-no-call-capsule-authz-final-release-sealed"
                ),
                "sealed_at": "2026-06-01T02:40:00Z",
                "operator_ref": "API52_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API52_SEAL_AUTH_SENTINEL",
            "provider_payload": "API52_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization:
        authz_final_seal_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_release_seal_summary(
                payload
            )
        )
        payload["expected_execution_capsule_authz_final_authz_release_seal_hash"] = (
            authz_final_final_expected_execution_capsule_authz_final_authz_release_seal_hash_override
            or authz_final_seal_summary[
                "execution_capsule_authz_final_authz_release_seal_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization"
        ] = {
            "execution_capsule_authz_final_authz_release_seal_hash": (
                authz_final_final_execution_capsule_authz_final_authz_release_seal_hash_override
                or authz_final_seal_summary[
                    "execution_capsule_authz_final_authz_release_seal_hash"
                ]
            ),
            "authorization_requested": True,
            "final_authorization": {
                "authorization_decision": "authorized",
                "authorization_reason_code": (
                    "local-no-call-capsule-authz-final-final-authorized"
                ),
                "authorized_at": "2026-06-01T02:45:00Z",
                "operator_ref": "API53_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API53_FINAL_AUTH_SENTINEL",
            "provider_payload": "API53_FINAL_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_export:
        authz_final_final_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_hash"
        ] = (
            authz_final_export_expected_execution_capsule_authz_final_authz_final_authz_hash_override
            or authz_final_final_summary[
                "execution_capsule_authz_final_authz_final_authz_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_export"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_hash": (
                authz_final_export_execution_capsule_authz_final_authz_final_authz_hash_override
                or authz_final_final_summary[
                    "execution_capsule_authz_final_authz_final_authz_hash"
                ]
            ),
            "export_requested": True,
            "export_metadata": {
                "export_kind": "authz_final_final_read_model",
                "export_reason_code": (
                    "local-no-call-capsule-authz-final-final-exported"
                ),
                "exported_at": "2026-06-01T02:50:00Z",
                "operator_ref": "API54_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API54_EXPORT_AUTH_SENTINEL",
            "provider_payload": "API54_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_handoff_packet:
        authz_final_export_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_export_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_export_hash"
        ] = (
            authz_final_handoff_expected_execution_capsule_authz_final_authz_final_authz_export_hash_override
            or authz_final_export_summary[
                "execution_capsule_authz_final_authz_final_authz_export_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_export_hash": (
                authz_final_handoff_execution_capsule_authz_final_authz_final_authz_export_hash_override
                or authz_final_export_summary[
                    "execution_capsule_authz_final_authz_final_authz_export_hash"
                ]
            ),
            "handoff_requested": True,
            "handoff_material": "API55_HANDOFF_MATERIAL_SENTINEL",
            "authorization_material": "API55_HANDOFF_AUTH_SENTINEL",
            "provider_payload": "API55_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_operator_review:
        authz_final_handoff_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
        ] = (
            authz_final_review_expected_execution_capsule_authz_final_authz_final_authz_handoff_hash_override
            or authz_final_handoff_summary[
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash": (
                authz_final_review_execution_capsule_authz_final_authz_final_authz_handoff_hash_override
                or authz_final_handoff_summary[
                    "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
                ]
            ),
            "review_requested": True,
            "operator_review": {
                "review_decision": "reviewed",
                "review_reason_code": (
                    "local-no-call-capsule-authz-final-final-reviewed"
                ),
                "reviewed_at": "2026-06-01T02:55:00Z",
                "operator_ref": "API56_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API56_REVIEW_AUTH_SENTINEL",
            "provider_payload": "API56_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_operator_decision:
        authz_final_review_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_operator_review_hash"
        ] = (
            authz_final_decision_expected_execution_capsule_authz_final_authz_final_authz_operator_review_hash_override
            or authz_final_review_summary[
                "execution_capsule_authz_final_authz_final_authz_operator_review_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_operator_review_hash": (
                authz_final_decision_execution_capsule_authz_final_authz_final_authz_operator_review_hash_override
                or authz_final_review_summary[
                    "execution_capsule_authz_final_authz_final_authz_operator_review_hash"
                ]
            ),
            "decision_requested": True,
            "operator_decision": {
                "decision": "reviewed",
                "decision_reason_code": (
                    "local-no-call-capsule-authz-final-final-decided"
                ),
                "decided_at": "2026-06-01T03:00:00Z",
                "operator_ref": "API57_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API57_DECISION_AUTH_SENTINEL",
            "provider_payload": "API57_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_release_attestation:
        authz_final_decision_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
        ] = (
            authz_final_final_attestation_expected_execution_capsule_authz_final_authz_final_authz_operator_decision_hash_override
            or authz_final_decision_summary[
                "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_release_attestation"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_operator_decision_hash": (
                authz_final_final_attestation_execution_capsule_authz_final_authz_final_authz_operator_decision_hash_override
                or authz_final_decision_summary[
                    "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
                ]
            ),
            "attestation_requested": True,
            "release_attestation": {
                "attestation": "attested",
                "attestation_reason_code": (
                    "local-no-call-capsule-authz-final-final-release-attested"
                ),
                "attested_at": "2026-06-01T03:05:00Z",
                "operator_ref": "API58_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API58_ATTESTATION_AUTH_SENTINEL",
            "provider_payload": "API58_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_release_seal:
        authz_final_attestation_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_attestation_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
        ] = (
            authz_final_final_seal_expected_execution_capsule_authz_final_authz_final_authz_release_attestation_hash_override
            or authz_final_attestation_summary[
                "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_release_attestation_hash": (
                authz_final_final_seal_execution_capsule_authz_final_authz_final_authz_release_attestation_hash_override
                or authz_final_attestation_summary[
                    "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
                ]
            ),
            "seal_requested": True,
            "seal_material": {
                "seal_decision": "sealed",
                "seal_reason_code": "local-no-call-capsule-authz-final-final-release-sealed",
                "sealed_at": "2026-06-01T03:10:00Z",
                "operator_ref": "API59_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API59_SEAL_AUTH_SENTINEL",
            "provider_payload": "API59_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_final_authorization:
        authz_final_seal_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_release_seal_hash"
        ] = (
            authz_final_final_authz_expected_execution_capsule_authz_final_authz_final_authz_release_seal_hash_override
            or authz_final_seal_summary[
                "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_release_seal_hash": (
                authz_final_final_authz_execution_capsule_authz_final_authz_final_authz_release_seal_hash_override
                or authz_final_seal_summary[
                    "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
                ]
            ),
            "authorization_requested": True,
            "final_authorization": {
                "authorization_decision": "authorized_disabled",
                "authorization_reason_code": (
                    "local-no-call-capsule-authz-final-final-final-authorized"
                ),
                "authorized_at": "2026-06-01T03:15:00Z",
                "operator_ref": "API60_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API60_FINAL_AUTHZ_AUTH_SENTINEL",
            "provider_payload": "API60_FINAL_AUTHZ_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_final_authorization_export:
        authz_final_final_authz_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_final_authz_hash"
        ] = (
            authz_final_final_authz_export_expected_execution_capsule_authz_final_authz_final_authz_final_authz_hash_override
            or authz_final_final_authz_summary[
                "execution_capsule_authz_final_authz_final_authz_final_authz_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_export"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_final_authz_hash": (
                authz_final_final_authz_export_execution_capsule_authz_final_authz_final_authz_final_authz_hash_override
                or authz_final_final_authz_summary[
                    "execution_capsule_authz_final_authz_final_authz_final_authz_hash"
                ]
            ),
            "export_requested": True,
            "export_metadata": {
                "export_kind": "final_authorization_read_model",
                "export_reason_code": (
                    "local-no-call-capsule-authz-final-final-final-exported"
                ),
                "exported_at": "2026-06-01T03:20:00Z",
                "operator_ref": "API61_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API61_EXPORT_AUTH_SENTINEL",
            "provider_payload": "API61_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet:
        authz_final_final_authz_export_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_export_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ] = (
            authz_final_final_authz_handoff_expected_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash_override
            or authz_final_final_authz_export_summary[
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash": (
                authz_final_final_authz_handoff_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash_override
                or authz_final_final_authz_export_summary[
                    "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
                ]
            ),
            "handoff_requested": True,
            "handoff_material": "API62_HANDOFF_MATERIAL_SENTINEL",
            "authorization_material": "API62_HANDOFF_AUTH_SENTINEL",
            "provider_payload": "API62_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review:
        authz_final_final_authz_handoff_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ] = (
            authz_final_final_authz_review_expected_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash_override
            or authz_final_final_authz_handoff_summary[
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash": (
                authz_final_final_authz_review_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash_override
                or authz_final_final_authz_handoff_summary[
                    "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
                ]
            ),
            "review_requested": True,
            "operator_review": {
                "review_decision": "reviewed",
                "review_reason_code": (
                    "local-no-call-capsule-authz-final-final-final-reviewed"
                ),
                "reviewed_at": "2026-06-01T03:25:00Z",
                "operator_ref": "API63_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API63_REVIEW_AUTH_SENTINEL",
            "provider_payload": "API63_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision:
        authz_final_final_authz_operator_review_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ] = (
            authz_final_final_authz_decision_expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash_override
            or authz_final_final_authz_operator_review_summary[
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash": (
                authz_final_final_authz_decision_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash_override
                or authz_final_final_authz_operator_review_summary[
                    "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
                ]
            ),
            "decision_requested": True,
            "operator_decision": {
                "decision": "reviewed",
                "decision_reason_code": (
                    "local-no-call-capsule-authz-final-final-final-decided"
                ),
                "decided_at": "2026-06-01T03:30:00Z",
                "operator_ref": "API64_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API64_DECISION_AUTH_SENTINEL",
            "provider_payload": "API64_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation:
        authz_final_final_authz_operator_decision_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ] = (
            authz_final_final_authz_attestation_expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash_override
            or authz_final_final_authz_operator_decision_summary[
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash": (
                authz_final_final_authz_attestation_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash_override
                or authz_final_final_authz_operator_decision_summary[
                    "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
                ]
            ),
            "attestation_requested": True,
            "release_attestation": {
                "attestation": "attested",
                "attestation_reason_code": (
                    "local-no-call-capsule-authz-final-final-final-attested"
                ),
                "attested_at": "2026-06-01T03:35:00Z",
                "operator_ref": "API65_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API65_ATTESTATION_AUTH_SENTINEL",
            "provider_payload": "API65_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal:
        authz_final_final_authz_release_attestation_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ] = (
            authz_final_final_authz_seal_expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash_override
            or authz_final_final_authz_release_attestation_summary[
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash": (
                authz_final_final_authz_seal_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash_override
                or authz_final_final_authz_release_attestation_summary[
                    "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
                ]
            ),
            "seal_requested": True,
            "seal_material": {
                "seal_decision": "sealed",
                "seal_reason_code": (
                    "local-no-call-capsule-authz-final-final-final-sealed"
                ),
                "sealed_at": "2026-06-01T03:40:00Z",
                "operator_ref": "API66_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API66_SEAL_AUTH_SENTINEL",
            "provider_payload": "API66_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization:
        authz_final_final_authz_release_seal_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
        ] = (
            authz_final_final_authz_final_expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash_override
            or authz_final_final_authz_release_seal_summary[
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash": (
                authz_final_final_authz_final_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash_override
                or authz_final_final_authz_release_seal_summary[
                    "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
                ]
            ),
            "authorization_requested": True,
            "final_authorization": {
                "authorization_decision": "authorized_disabled",
                "authorization_reason_code": (
                    "local-no-call-capsule-authz-final-final-final-final-authorized"
                ),
                "authorized_at": "2026-06-01T03:45:00Z",
                "operator_ref": "API67_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API67_AUTH_SENTINEL",
            "provider_payload": "API67_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export:
        authz_final_final_authz_final_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
        ] = (
            authz_final_final_authz_final_export_expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash_override
            or authz_final_final_authz_final_summary[
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash": (
                authz_final_final_authz_final_export_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash_override
                or authz_final_final_authz_final_summary[
                    "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
                ]
            ),
            "export_requested": True,
            "export_metadata": {
                "export_kind": "final_authorization_read_model",
                "export_reason_code": (
                    "local-no-call-capsule-authz-final-final-final-final-exported"
                ),
                "exported_at": "2026-06-01T03:50:00Z",
                "operator_ref": "API68_OPERATOR_REF_SENTINEL",
            },
            "authorization_material": "API68_EXPORT_AUTH_SENTINEL",
            "provider_payload": "API68_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_handoff_packet:
        authz_final_final_authz_final_export_summary = (
            provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export_summary(
                payload
            )
        )
        payload[
            "expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ] = (
            authz_final_final_authz_final_handoff_expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash_override
            or authz_final_final_authz_final_export_summary[
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
            ]
        )
        payload[
            "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_handoff_packet"
        ] = {
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash": (
                authz_final_final_authz_final_handoff_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash_override
                or authz_final_final_authz_final_export_summary[
                    "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
                ]
            ),
            "handoff_requested": True,
            "authorization_material": "API69_HANDOFF_AUTH_SENTINEL",
            "provider_payload": "API69_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        }
    return payload


def _live_admission_payload() -> dict:
    run_id = "run-api-live"
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {
                "toc": ["Agentic Workbench API"],
                "rationale": "Need API wiring for fake live admission.",
                "blueprint": [
                    {"title": "API Gate", "guideline": "persist approval before replay"},
                    {"title": "Fake Runtime", "guideline": "keep target calls at zero"},
                ],
            }
        }
    )
    spec = planning_to_build_spec(blueprint)
    prd_package = planning_to_prd_package(blueprint, build_spec=spec)
    brief = implementation_brief_from_prd_package(prd_package, spec)
    spec_approval = create_spec_approval(
        brief,
        approval_id="approval-api-live-brief",
        approved=True,
    )
    state = build_spec_to_daacs_initial_state(
        spec,
        run_id=run_id,
        implementation_brief=brief,
        approval=spec_approval,
        require_approval=True,
    )
    dry_run = default_runner_provider_registry().run(
        RunnerRequest(
            run_id=run_id,
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=spec_approval,
        )
    )
    assert dry_run.plan is not None
    approval = ApprovalRecord(
        approved_by="local-user",
        approved_at="2026-05-31T00:00:00Z",
        run_id=run_id,
        mode="live",
        allowed_operations=["fake_runtime"],
        max_provider_calls=0,
        max_subprocess_calls=0,
        max_package_installs=0,
        max_server_starts=0,
        max_files_written=0,
        workspace_root=f"runs/{run_id}",
        expires_at="2099-01-01T00:00:00Z",
        rollback_plan_id="rollback-api-live",
        audit_log_id="audit-api-live",
    )
    policy = RunnerPolicy(workspace_root=f"runs/{run_id}")
    request = RunnerRequest(
        run_id=run_id,
        mode="live",
        state=state,
        approval=approval,
        plan=dry_run.plan,
        policy=policy,
    )
    sign_approval_for_tests(
        approval,
        scope=live_replay_scope_for_request(request),
        signature_id="sig-api-live-admission",
        nonce="nonce-api-live-admission",
    )
    return {
        "run_id": run_id,
        "approval_lifecycle": "durable",
        "state": state,
        "plan": dry_run.plan.to_dict(),
        "policy": asdict(policy),
        "approval": asdict(approval),
    }


def _persist_evidence_chain(root, run_id: str = "run-api-provider") -> None:
    store = SQLiteRunnerReportAuditStore(root=root)
    plan_artifact_id = f"artifact-api-plan-{run_id}"
    report_artifact_id = f"artifact-api-report-{run_id}"
    audit_artifact_id = f"artifact-api-audit-{run_id}"
    artifacts = [
        ArtifactRecord(
            artifact_id=plan_artifact_id,
            run_id=run_id,
            kind="api_evidence_fixture",
            name="plan artifact",
            path=None,
            content_hash="f" * 64,
            payload_field_count=0,
            summary="api evidence plan projection",
            created_at="2026-05-31T00:00:00+00:00",
        ),
        ArtifactRecord(
            artifact_id=report_artifact_id,
            run_id=run_id,
            kind="api_evidence_fixture",
            name="report artifact",
            path=None,
            content_hash="f" * 64,
            payload_field_count=0,
            summary="api evidence report projection",
            created_at="2026-05-31T00:00:00+00:00",
        ),
        ArtifactRecord(
            artifact_id=audit_artifact_id,
            run_id=run_id,
            kind="api_evidence_fixture",
            name="audit artifact",
            path=None,
            content_hash="f" * 64,
            payload_field_count=0,
            summary="api evidence audit projection",
            created_at="2026-05-31T00:00:00+00:00",
        ),
    ]
    plan = RunnerPlan(
        run_id=run_id,
        mode="dry_run",
        implementation_brief_hash="a" * 64,
        build_spec_hash="b" * 64,
        planned_actions=[
            {
                "id": "backend-action",
                "role": "backend",
                "summary": "plan backend projection",
                "raw_request_body": "API03_RAW_PLANNED_BODY",
                "provider_payload": {"body": "API03_PROVIDER_BODY"},
                "runtime_payload": "API03_RUNTIME_BODY",
                "file_body": "API03_FILE_BODY",
            }
        ],
        artifact_manifest=[{"kind": "backend", "path": f"runs/{run_id}/backend"}],
        required_approvals=[{"approval_type": "live_runner", "signature_id": "API03_SIGNATURE"}],
        side_effects={"provider_calls": 0, "subprocess_calls": 0, "filesystem_writes": 0},
        created_at="2026-05-31T00:00:01+00:00",
    )
    plan_record = runner_plan_record_from_plan(plan, source_artifact_id=plan_artifact_id)
    report = VerificationReport(
        run_id=run_id,
        passed=False,
        checks=[{"name": "dry_run", "passed": True, "details": "API03_RAW_LOG"}],
        errors=["token=api03-secret"],
        generated_files=["backend/main.py"],
        metrics={"boundary_mode": "dry_run", "provider_calls": 0, "raw_log": "API03_METRIC_RAW_LOG"},
        created_at="2026-05-31T00:00:02+00:00",
    )
    report_record = verification_report_record_from_report(
        report,
        source_artifact_id=report_artifact_id,
        runner_plan_hash=plan_record.plan_hash,
    )
    audit_record = audit_event_record_from_event(
        {
            "run_id": run_id,
            "event": "api_evidence",
            "source": "api_test",
            "stage": "read_model",
            "level": "info",
            "message": "API03_AUDIT_RAW_MESSAGE",
            "payload": {
                "provider_payload": "API03_AUDIT_PROVIDER_PAYLOAD",
                "runtime_payload": "API03_AUDIT_RUNTIME_PAYLOAD",
                "signature_id": "API03_AUDIT_SIGNATURE",
                "nonce": "API03_AUDIT_NONCE",
                "safe_count": 1,
            },
            "created_at": "2026-05-31T00:00:03+00:00",
        },
        source_artifact_id=audit_artifact_id,
        linked_plan_hash=plan_record.plan_hash,
        linked_report_hash=report_record.report_hash,
    )
    store.save_records_atomically(
        artifacts=artifacts,
        runner_plans=[plan_record],
        verification_reports=[report_record],
        audit_events=[audit_record],
    )


def test_create_run_returns_public_projection_with_fixture_boundary_markers():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build a finance app with API_KEY=secret-value and API_RAW_PROMPT_SENTINEL",
            "target_user": "finance-owner@example.com",
            "product_type": "approval workflow",
            "constraints": ["never expose API_CONSTRAINT_SENTINEL"],
            "success_criteria": ["dry-run plan visible"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]

    assert data["projection_version"] == "workflow-session-public-v1"
    assert data["runtime_mode"] == "fixture"
    assert data["approval_lifecycle"] == "synthetic"
    assert data["approval_mode"] == "fixture"
    assert data["fixture_mode"] is True
    assert data["durable_user_approval"] is False
    assert data["run"]["prompt_contract_hash"]
    assert "idea" not in data["run"]
    assert data["execution_boundary"]["live_provider_call_count"] == 0
    assert data["execution_boundary"]["live_source_runtime_call_count"] == 0
    assert data["data_contract"]["workflow_session_to_dict_returned"] is False
    assert data["canonical_persistence"]["status"] == "skipped"
    assert data["canonical_persistence"]["repository_boundary"]["run_artifact_backend"] == "unconfigured"
    assert data["canonical_persistence"]["execution_boundary"]["local_run_artifact_repository_write_count"] == 0
    assert data["evidence_persistence"]["status"] == "skipped"
    assert data["evidence_persistence"]["repository_boundary"]["runner_report_audit_backend"] == "unconfigured"
    assert data["evidence_persistence"]["execution_boundary"]["local_evidence_repository_write_count"] == 0
    assert payload["events"]
    assert "raw_prompt" not in serialized
    assert "API_RAW_PROMPT_SENTINEL" not in serialized
    assert "API_CONSTRAINT_SENTINEL" not in serialized
    assert "finance-owner@example.com" not in serialized
    assert "API_KEY=secret-value" not in serialized
    assert "provider_payload" not in serialized
    assert "approval_authorization_material" not in serialized


def test_runs_fixture_path_persists_sanitized_evidence_when_sqlite_repo_configured(tmp_path):
    evidence_root = tmp_path / "evidence"
    client = TestClient(create_app(evidence_repository_config=EvidenceRepositoryConfig(root=evidence_root)))

    response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build fixture evidence path with API_KEY=secret and API04_RAW_PROMPT_SENTINEL",
            "target_user": "api04-owner@example.com",
            "product_type": "fixture evidence persistence",
            "constraints": ["never expose API04_CONSTRAINT_SENTINEL"],
            "success_criteria": ["persist sanitized evidence"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    run_id = data["run"]["run_id"]
    persistence = data["evidence_persistence"]

    assert persistence["projection_version"] == "fixture-evidence-persistence-public-v1"
    assert persistence["status"] == "persisted"
    assert persistence["fixture_mode"] is True
    assert persistence["durable_user_approval"] is False
    assert persistence["repository_boundary"]["runner_report_audit_backend"] == "sqlite"
    assert persistence["repository_boundary"]["root_path_returned"] is False
    assert persistence["counts"]["artifact_count"] == data["artifact_count"]
    assert persistence["counts"]["runner_plan_count"] == 1
    assert persistence["counts"]["verification_report_count"] == 1
    assert persistence["counts"]["audit_event_count"] == len(payload["events"]) + 1
    assert persistence["execution_boundary"]["local_evidence_repository_write_count"] == 1
    assert persistence["execution_boundary"]["provider_calls"] == 0
    assert persistence["execution_boundary"]["target_runtime_calls"] == 0
    assert (evidence_root / "agentic_workbench.sqlite3").exists()

    evidence_response = client.get(f"/api/v1/evidence/runs/{run_id}")
    assert evidence_response.status_code == 200
    evidence_payload = evidence_response.json()
    evidence_serialized = _serialized(evidence_payload)
    evidence = evidence_payload["data"]

    assert evidence["status"] == "passed"
    assert evidence["counts"]["runner_plan_count"] == 1
    assert evidence["counts"]["verification_report_count"] == 1
    assert evidence["counts"]["audit_event_count"] == len(payload["events"]) + 1
    assert evidence["counts"]["approval_subject_snapshot_count"] == 0
    assert evidence["counts"]["approval_count"] == 0
    assert evidence["counts"]["replay_nonce_count"] == 0
    assert evidence["runner_plans"][0]["run_id"] == run_id
    assert evidence["runner_plans"][0]["mode"] == "dry_run"
    assert evidence["runner_plans"][0]["planned_action_count"] == 3
    assert evidence["runner_plans"][0]["action_role_counts"]["backend"] == 1
    assert evidence["runner_plans"][0]["action_role_counts"]["frontend"] == 1
    assert evidence["runner_plans"][0]["action_role_counts"]["verifier"] == 1
    assert evidence["verification_reports"][0]["mode"] == "dry_run"
    assert evidence["verification_reports"][0]["generated_file_count"] == 0
    assert evidence["verification_reports"][0]["runner_plan_hash"] == persistence["hashes"]["runner_plan_hash"]
    assert evidence["execution_boundary"]["provider_calls"] == 0
    assert evidence["execution_boundary"]["target_runtime_calls"] == 0
    assert evidence["execution_boundary"]["solar_provider_calls"] == 0

    combined = _serialized({"run_response": payload, "evidence_response": evidence_payload})
    for forbidden in (
        "raw_prompt",
        "API04_RAW_PROMPT_SENTINEL",
        "API04_CONSTRAINT_SENTINEL",
        "api04-owner@example.com",
        "API_KEY=secret",
        "provider_payload",
        "runtime_payload",
        "file_body",
        str(tmp_path),
    ):
        assert forbidden not in serialized
        assert forbidden not in evidence_serialized
        assert forbidden not in combined


def test_runs_fixture_evidence_persistence_blocks_corrupted_sqlite_store_without_raw_echo(tmp_path):
    corrupt_root = tmp_path / "corrupt-evidence"
    corrupt_root.mkdir()
    (corrupt_root / "agentic_workbench.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(create_app(evidence_repository_config=EvidenceRepositoryConfig(root=corrupt_root)))

    response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build fixture evidence path with API04_CORRUPT_RAW_SENTINEL",
            "target_user": "api04-corrupt-owner@example.com",
            "product_type": "fixture evidence persistence",
            "constraints": ["never expose corrupt store path"],
            "success_criteria": ["block unsafe persistence"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    persistence = data["evidence_persistence"]
    checks = {check["name"]: check["passed"] for check in persistence["checks"]}

    assert data["runtime_mode"] == "fixture"
    assert persistence["status"] == "blocked"
    assert persistence["repository_boundary"]["runner_report_audit_backend"] == "sqlite"
    assert checks["fixture_projection_persisted"] is False
    assert persistence["counts"]["runner_plan_count"] == 0
    assert persistence["execution_boundary"]["provider_calls"] == 0
    assert persistence["execution_boundary"]["target_runtime_calls"] == 0
    assert persistence["execution_boundary"]["local_evidence_repository_write_count"] == 0
    assert "API04_CORRUPT_RAW_SENTINEL" not in serialized
    assert "api04-corrupt-owner@example.com" not in serialized
    assert str(corrupt_root) not in serialized
    assert "not a sqlite database" not in serialized


def test_runs_fixture_canonical_persistence_blocks_corrupted_sqlite_store_without_raw_echo(tmp_path):
    corrupt_root = tmp_path / "corrupt-canonical"
    corrupt_root.mkdir()
    (corrupt_root / "agentic_workbench_runs.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(create_app(run_repository_config=RunArtifactRepositoryConfig(root=corrupt_root)))

    response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build canonical run path with API08_CORRUPT_RAW_SENTINEL",
            "target_user": "api08-corrupt-owner@example.com",
            "product_type": "canonical run persistence",
            "constraints": ["never expose API08_CORRUPT_CONSTRAINT"],
            "success_criteria": ["block unsafe canonical store"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    persistence = data["canonical_persistence"]
    checks = {check["name"]: check["passed"] for check in persistence["checks"]}

    assert data["runtime_mode"] == "fixture"
    assert persistence["status"] == "blocked"
    assert persistence["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert persistence["repository_boundary"]["runner_report_audit_backend"] == "not_queried"
    assert persistence["repository_boundary"]["approval_replay_backend"] == "not_queried"
    assert checks["canonical_run_session_persisted"] is False
    assert persistence["counts"]["run_session_count"] == 0
    assert persistence["counts"]["artifact_count"] == 0
    assert persistence["execution_boundary"]["provider_calls"] == 0
    assert persistence["execution_boundary"]["target_runtime_calls"] == 0
    assert persistence["execution_boundary"]["local_run_artifact_repository_write_count"] == 0
    assert "API08_CORRUPT_RAW_SENTINEL" not in serialized
    assert "API08_CORRUPT_CONSTRAINT" not in serialized
    assert "api08-corrupt-owner@example.com" not in serialized
    assert str(corrupt_root) not in serialized
    assert "not a sqlite database" not in serialized


def test_run_and_artifact_read_apis_return_sanitized_repository_rows_without_cross_run_leakage(tmp_path):
    evidence_root = tmp_path / "evidence"
    run_root = tmp_path / "canonical-runs"
    admission_root = tmp_path / "admission"
    client = TestClient(
        create_app(
            evidence_repository_config=EvidenceRepositoryConfig(root=evidence_root),
            run_repository_config=RunArtifactRepositoryConfig(root=run_root),
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=admission_root,
            ),
        )
    )

    first_response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build first fixture read model with API05_FIRST_RAW_PROMPT",
            "target_user": "api05-first-owner@example.com",
            "product_type": "run artifact read model",
            "constraints": ["never expose API05_FIRST_CONSTRAINT"],
            "success_criteria": ["read sanitized artifacts"],
        },
    )
    second_response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build second fixture read model with API05_SECOND_RAW_PROMPT",
            "target_user": "api05-second-owner@example.com",
            "product_type": "run artifact read model",
            "constraints": ["never expose API05_SECOND_CONSTRAINT"],
            "success_criteria": ["cross-run isolation"],
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_data = first_response.json()["data"]
    second_data = second_response.json()["data"]
    first_run_id = first_data["run"]["run_id"]
    second_run_id = second_data["run"]["run_id"]

    assert first_data["canonical_persistence"]["status"] == "persisted"
    assert first_data["canonical_persistence"]["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert first_data["canonical_persistence"]["repository_boundary"]["runner_report_audit_backend"] == "not_queried"
    assert first_data["canonical_persistence"]["repository_boundary"]["approval_replay_backend"] == "not_queried"
    assert first_data["canonical_persistence"]["counts"]["run_session_count"] == 1
    assert first_data["canonical_persistence"]["counts"]["artifact_count"] == first_data["artifact_count"]
    assert first_data["canonical_persistence"]["execution_boundary"]["provider_calls"] == 0
    assert first_data["canonical_persistence"]["execution_boundary"]["target_runtime_calls"] == 0
    assert (run_root / "agentic_workbench_runs.sqlite3").exists()
    assert (evidence_root / "agentic_workbench.sqlite3").exists()
    assert not (admission_root / "approval_replay.sqlite3").exists()

    run_response = client.get(f"/api/v1/runs/{first_run_id}")
    artifacts_response = client.get(f"/api/v1/runs/{first_run_id}/artifacts")

    assert run_response.status_code == 200
    assert artifacts_response.status_code == 200
    run_payload = run_response.json()
    artifacts_payload = artifacts_response.json()
    run_data = run_payload["data"]
    artifacts_data = artifacts_payload["data"]
    run_checks = {check["name"]: check["passed"] for check in run_data["checks"]}
    artifact_checks = {check["name"]: check["passed"] for check in artifacts_data["checks"]}

    assert run_data["projection_version"] == "canonical-run-composed-read-model-public-v1"
    assert artifacts_data["projection_version"] == "canonical-artifact-read-model-public-v1"
    assert run_data["status"] == "passed"
    assert artifacts_data["status"] == "passed"
    assert run_checks["run_artifact_repository_available"] is True
    assert run_checks["evidence_summary_not_raw_rows"] is True
    assert artifact_checks["run_artifact_repository_available"] is True
    assert artifact_checks["evidence_repository_not_queried"] is True
    assert artifact_checks["approval_replay_repository_not_queried"] is True
    assert run_data["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert run_data["repository_boundary"]["canonical_run_artifact_backend"] == "sqlite"
    assert run_data["repository_boundary"]["runner_report_audit_backend"] == "sqlite"
    assert run_data["repository_boundary"]["approval_replay_backend"] == "sqlite"
    assert run_data["repository_boundary"]["evidence_db_queried"] is True
    assert run_data["repository_boundary"]["approval_replay_db_queried"] is True
    assert artifacts_data["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert artifacts_data["repository_boundary"]["approval_replay_backend"] == "not_queried"
    assert run_data["run"]["run_id"] == first_run_id
    assert run_data["run"]["prompt_contract_hash"]
    assert run_data["run"]["stage"] == "complete"
    assert run_data["run"]["status"] == "complete"
    assert run_data["run"]["idea_summary"]
    assert run_data["counts"]["artifact_count"] == first_data["artifact_count"]
    assert artifacts_data["counts"]["artifact_count"] == first_data["artifact_count"]
    assert run_data["counts"]["run_session_count"] == 1
    assert run_data["counts"]["runner_plan_count"] == 1
    assert run_data["counts"]["verification_report_count"] == 1
    assert run_data["counts"]["audit_event_count"] == len(first_response.json()["events"]) + 1
    assert run_data["counts"]["approval_subject_snapshot_count"] == 0
    assert run_data["counts"]["approval_count"] == 0
    assert run_data["counts"]["replay_nonce_count"] == 0
    assert run_data["evidence_summary"]["status"] == "available"
    assert run_data["evidence_summary"]["counts"]["runner_plan_count"] == 1
    assert run_data["evidence_summary"]["counts"]["verification_report_count"] == 1
    assert run_data["evidence_summary"]["counts"]["source_artifact_count"] == first_data["artifact_count"]
    assert run_data["evidence_summary"]["linkage"]["run_id_matched"] is True
    assert run_data["evidence_summary"]["linkage"]["artifact_linkage_checked"] is True
    assert {artifact["run_id"] for artifact in artifacts_data["artifacts"]} == {first_run_id}
    assert {artifact["run_id"] for artifact in run_data["artifacts"]} == {first_run_id}
    assert run_data["execution_boundary"]["provider_calls"] == 0
    assert run_data["execution_boundary"]["target_runtime_calls"] == 0
    assert run_data["execution_boundary"]["solar_provider_calls"] == 0

    combined = _serialized({"run": run_payload, "artifacts": artifacts_payload})
    for forbidden in (
        second_run_id,
        "raw_prompt",
        "API05_FIRST_RAW_PROMPT",
        "API05_SECOND_RAW_PROMPT",
        "API05_FIRST_CONSTRAINT",
        "API05_SECOND_CONSTRAINT",
        "api05-first-owner@example.com",
        "api05-second-owner@example.com",
        "provider_payload",
        "runtime_payload",
        "file_body",
        "signature_id",
        "signed_contract_hash",
        str(tmp_path),
    ):
        assert forbidden not in combined


def test_composed_run_read_model_keeps_canonical_lookup_when_evidence_unconfigured(tmp_path):
    run_root = tmp_path / "canonical-runs"
    client = TestClient(create_app(run_repository_config=RunArtifactRepositoryConfig(root=run_root)))

    create_response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build canonical-only run with API06_MISSING_EVIDENCE_RAW_PROMPT",
            "target_user": "api06-missing-evidence-owner@example.com",
            "product_type": "composed read model",
            "constraints": ["never expose API06_MISSING_EVIDENCE_CONSTRAINT"],
            "success_criteria": ["read canonical state without evidence"],
        },
    )

    assert create_response.status_code == 200
    run_id = create_response.json()["data"]["run"]["run_id"]

    read_response = client.get(f"/api/v1/runs/{run_id}")

    assert read_response.status_code == 200
    payload = read_response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "passed"
    assert data["projection_version"] == "canonical-run-composed-read-model-public-v1"
    assert checks["run_artifact_repository_available"] is True
    assert checks["evidence_summary_not_raw_rows"] is True
    assert data["repository_boundary"]["runner_report_audit_backend"] == "unconfigured"
    assert data["repository_boundary"]["approval_replay_backend"] == "not_queried_or_unconfigured"
    assert data["repository_boundary"]["evidence_db_queried"] is False
    assert data["repository_boundary"]["approval_replay_db_queried"] is False
    assert data["evidence_summary"]["status"] == "unconfigured"
    assert data["evidence_summary"]["counts"]["runner_plan_count"] == 0
    assert data["evidence_summary"]["counts"]["approval_count"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert "API06_MISSING_EVIDENCE_RAW_PROMPT" not in serialized
    assert "API06_MISSING_EVIDENCE_CONSTRAINT" not in serialized
    assert "api06-missing-evidence-owner@example.com" not in serialized
    assert str(tmp_path) not in serialized


def test_composed_run_read_model_blocks_only_evidence_section_when_evidence_store_corrupted(tmp_path):
    run_root = tmp_path / "canonical-runs"
    corrupt_evidence_root = tmp_path / "corrupt-evidence"
    corrupt_evidence_root.mkdir()
    (corrupt_evidence_root / "agentic_workbench.sqlite3").write_text(
        "not a sqlite database",
        encoding="utf-8",
    )
    client = TestClient(
        create_app(
            run_repository_config=RunArtifactRepositoryConfig(root=run_root),
            evidence_repository_config=EvidenceRepositoryConfig(root=corrupt_evidence_root),
        )
    )

    create_response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build canonical run with API06_CORRUPT_EVIDENCE_RAW_PROMPT",
            "target_user": "api06-corrupt-evidence-owner@example.com",
            "product_type": "composed read model",
            "constraints": ["never expose API06_CORRUPT_EVIDENCE_CONSTRAINT"],
            "success_criteria": ["block only evidence summary"],
        },
    )

    assert create_response.status_code == 200
    run_id = create_response.json()["data"]["run"]["run_id"]

    read_response = client.get(f"/api/v1/runs/{run_id}")

    assert read_response.status_code == 200
    payload = read_response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["evidence_summary"]["checks"]}

    assert data["status"] == "passed"
    assert data["run"]["run_id"] == run_id
    assert data["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert data["repository_boundary"]["runner_report_audit_backend"] == "sqlite"
    assert data["repository_boundary"]["evidence_db_queried"] is True
    assert data["repository_boundary"]["approval_replay_db_queried"] is False
    assert data["evidence_summary"]["status"] == "blocked"
    assert checks["runner_report_audit_repository_available"] is False
    assert data["evidence_summary"]["counts"]["runner_plan_count"] == 0
    assert data["counts"]["run_session_count"] == 1
    assert data["counts"]["runner_plan_count"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert "API06_CORRUPT_EVIDENCE_RAW_PROMPT" not in serialized
    assert "API06_CORRUPT_EVIDENCE_CONSTRAINT" not in serialized
    assert "api06-corrupt-evidence-owner@example.com" not in serialized
    assert str(corrupt_evidence_root) not in serialized
    assert "not a sqlite database" not in serialized


def test_run_and_artifact_read_apis_block_corrupted_store_without_raw_path(tmp_path):
    corrupt_root = tmp_path / "corrupt-canonical"
    corrupt_root.mkdir()
    (corrupt_root / "agentic_workbench_runs.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(create_app(run_repository_config=RunArtifactRepositoryConfig(root=corrupt_root)))

    run_response = client.get("/api/v1/runs/run-api-provider")
    artifacts_response = client.get("/api/v1/runs/run-api-provider/artifacts")

    assert run_response.status_code == 200
    assert artifacts_response.status_code == 200
    run_payload = run_response.json()
    artifacts_payload = artifacts_response.json()
    combined = _serialized({"run": run_payload, "artifacts": artifacts_payload})
    run_data = run_payload["data"]
    artifacts_data = artifacts_payload["data"]
    run_checks = {check["name"]: check["passed"] for check in run_data["checks"]}
    artifact_checks = {check["name"]: check["passed"] for check in artifacts_data["checks"]}

    assert run_data["status"] == "blocked"
    assert artifacts_data["status"] == "blocked"
    assert run_checks["run_artifact_repository_available"] is False
    assert artifact_checks["run_artifact_repository_available"] is False
    assert run_data["counts"]["artifact_count"] == 0
    assert artifacts_data["counts"]["artifact_count"] == 0
    assert run_data["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert run_data["repository_boundary"]["runner_report_audit_backend"] == "unconfigured"
    assert run_data["repository_boundary"]["approval_replay_backend"] == "not_queried_or_unconfigured"
    assert run_data["execution_boundary"]["provider_calls"] == 0
    assert artifacts_data["execution_boundary"]["target_runtime_calls"] == 0
    assert str(corrupt_root) not in combined
    assert "not a sqlite database" not in combined


def test_evidence_read_model_api_returns_sqlite_rows_without_raw_bodies_or_auth_material(tmp_path):
    evidence_root = tmp_path / "evidence"
    admission_root = tmp_path / "admission"
    _persist_evidence_chain(evidence_root)
    _persist_evidence_chain(evidence_root, run_id="run-api-other")
    client = TestClient(
        create_app(
            evidence_repository_config=EvidenceRepositoryConfig(root=evidence_root),
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=admission_root,
            ),
        )
    )
    admission_response = client.post(
        "/api/v1/admissions/provider/fake",
        json=_provider_admission_payload(),
    )
    other_admission_response = client.post(
        "/api/v1/admissions/provider/fake",
        json=_provider_admission_payload(
            run_id="run-api-other",
            signature_id="sig-api-provider-other",
            nonce="nonce-api-provider-other",
        ),
    )

    response = client.get("/api/v1/evidence/runs/run-api-provider")

    assert admission_response.status_code == 200
    assert other_admission_response.status_code == 200
    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]

    assert data["projection_version"] == "evidence-read-model-public-v1"
    assert data["status"] == "passed"
    assert data["repository_boundary"]["runner_report_audit_backend"] == "sqlite"
    assert data["repository_boundary"]["approval_replay_backend"] == "sqlite"
    assert data["repository_boundary"]["root_path_returned"] is False
    assert data["counts"]["runner_plan_count"] == 1
    assert data["counts"]["verification_report_count"] == 1
    assert data["counts"]["audit_event_count"] == 1
    assert data["counts"]["approval_subject_snapshot_count"] == 1
    assert data["counts"]["approval_count"] == 1
    assert data["counts"]["replay_nonce_count"] == 1
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert "run-api-other" not in serialized

    for forbidden in (
        "API03_RAW_PLANNED_BODY",
        "API03_PROVIDER_BODY",
        "API03_RUNTIME_BODY",
        "API03_FILE_BODY",
        "API03_RAW_LOG",
        "API03_METRIC_RAW_LOG",
        "API03_AUDIT_RAW_MESSAGE",
        "API03_AUDIT_PROVIDER_PAYLOAD",
        "API03_AUDIT_RUNTIME_PAYLOAD",
        "API03_AUDIT_SIGNATURE",
        "API03_AUDIT_NONCE",
        "api03-secret",
        "sig-api-provider-admission",
        "nonce-api-provider-admission",
        "sig-api-provider-other",
        "nonce-api-provider-other",
        _provider_admission_payload()["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_evidence_read_model_api_blocks_corrupted_evidence_store_without_raw_path(tmp_path):
    corrupt_root = tmp_path / "corrupt-evidence"
    corrupt_root.mkdir()
    (corrupt_root / "agentic_workbench.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(create_app(evidence_repository_config=EvidenceRepositoryConfig(root=corrupt_root)))

    response = client.get("/api/v1/evidence/runs/run-api-provider")

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert checks["runner_report_audit_repository_available"] is False
    assert data["counts"]["runner_plan_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert str(corrupt_root) not in serialized
    assert "not a sqlite database" not in serialized


def test_evidence_read_model_api_blocks_corrupted_approval_store_without_runtime_calls(tmp_path):
    evidence_root = tmp_path / "evidence"
    approval_root = tmp_path / "approval"
    approval_root.mkdir()
    _persist_evidence_chain(evidence_root)
    (approval_root / "approval_replay.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(
        create_app(
            evidence_repository_config=EvidenceRepositoryConfig(root=evidence_root),
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=approval_root,
            ),
        )
    )

    response = client.get("/api/v1/evidence/runs/run-api-provider")

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert checks["runner_report_audit_repository_available"] is True
    assert checks["approval_replay_repository_available"] is False
    assert data["counts"]["runner_plan_count"] == 1
    assert data["counts"]["approval_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert str(approval_root) not in serialized
    assert "not a sqlite database" not in serialized


def test_provider_fake_admission_api_uses_canonical_persistence_without_raw_auth_material():
    client = TestClient(create_app())
    request_payload = _provider_admission_payload()

    response = client.post("/api/v1/admissions/provider/fake", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]

    assert data["projection_version"] == "approval-admission-public-v1"
    assert data["admission_kind"] == "provider"
    assert data["runtime_mode"] == "fake"
    assert data["approval_lifecycle"] == "durable"
    assert data["fixture_mode"] is False
    assert data["synthetic_approval"] is False
    assert data["approval_persistence"]["service_used"] is True
    assert data["approval_persistence"]["approval_row_present"] is True
    assert data["approval_persistence"]["hash_match"] is True
    assert data["execution_boundary"]["fake_provider_invocations"] == 1
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["live_llm_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert request_payload["approval"]["nonce"] not in serialized
    assert request_payload["approval"]["signature_id"] not in serialized
    assert request_payload["approval"]["signed_contract_hash"] not in serialized
    assert "nonce" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_provider_fake_admission_api_uses_sqlite_repository_and_blocks_reused_nonce_across_requests(tmp_path):
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=tmp_path,
            )
        )
    )
    request_payload = _provider_admission_payload()

    first = client.post("/api/v1/admissions/provider/fake", json=request_payload)
    second = client.post("/api/v1/admissions/provider/fake", json=request_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    first_data = first.json()["data"]
    second_payload = second.json()
    second_data = second_payload["data"]
    serialized = _serialized(second_payload)
    checks = {check["name"]: check["passed"] for check in second_data["checks"]}

    assert first_data["status"] == "passed"
    assert first_data["repository_boundary"]["backend"] == "sqlite"
    assert first_data["repository_boundary"]["persists_across_requests"] is True
    assert first_data["execution_boundary"]["fake_provider_invocations"] == 1
    assert second_data["status"] == "blocked"
    assert second_data["repository_boundary"]["backend"] == "sqlite"
    assert second_data["repository_boundary"]["persists_across_requests"] is True
    assert checks["provider_approval_replay_fresh"] is False
    assert second_data["execution_boundary"]["fake_provider_invocations"] == 0
    assert second_data["execution_boundary"]["provider_calls"] == 0
    assert second_data["execution_boundary"]["live_api_calls"] == 0
    assert second_data["execution_boundary"]["live_llm_calls"] == 0
    assert second_data["execution_boundary"]["solar_provider_calls"] == 0
    assert (tmp_path / "approval_replay.sqlite3").exists()
    assert request_payload["approval"]["nonce"] not in serialized
    assert request_payload["approval"]["signature_id"] not in serialized
    assert request_payload["approval"]["signed_contract_hash"] not in serialized
    assert "nonce" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_live_fake_admission_api_uses_canonical_persistence_without_target_runtime_calls():
    client = TestClient(create_app())
    request_payload = _live_admission_payload()

    response = client.post("/api/v1/admissions/live/fake", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]

    assert data["projection_version"] == "approval-admission-public-v1"
    assert data["admission_kind"] == "live_runner"
    assert data["runtime_mode"] == "fake"
    assert data["approval_lifecycle"] == "durable"
    assert data["fixture_mode"] is False
    assert data["synthetic_approval"] is False
    assert data["approval_persistence"]["service_used"] is True
    assert data["approval_persistence"]["approval_row_present"] is True
    assert data["approval_persistence"]["hash_match"] is True
    assert data["execution_boundary"]["fake_live_runtime_invocations"] == 1
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert request_payload["approval"]["nonce"] not in serialized
    assert request_payload["approval"]["signature_id"] not in serialized
    assert request_payload["approval"]["signed_contract_hash"] not in serialized
    assert "nonce" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_live_fake_admission_api_uses_sqlite_repository_and_blocks_reused_nonce_across_requests(tmp_path):
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=tmp_path,
            )
        )
    )
    request_payload = _live_admission_payload()

    first = client.post("/api/v1/admissions/live/fake", json=request_payload)
    second = client.post("/api/v1/admissions/live/fake", json=request_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    first_data = first.json()["data"]
    second_payload = second.json()
    second_data = second_payload["data"]
    serialized = _serialized(second_payload)
    checks = {check["name"]: check["passed"] for check in second_data["checks"]}

    assert first_data["status"] == "passed"
    assert first_data["repository_boundary"]["backend"] == "sqlite"
    assert first_data["repository_boundary"]["persists_across_requests"] is True
    assert first_data["execution_boundary"]["fake_live_runtime_invocations"] == 1
    assert second_data["status"] == "blocked"
    assert second_data["repository_boundary"]["backend"] == "sqlite"
    assert second_data["repository_boundary"]["persists_across_requests"] is True
    assert checks["live_approval_replay_fresh"] is False
    assert second_data["execution_boundary"]["fake_live_runtime_invocations"] == 0
    assert second_data["execution_boundary"]["target_runtime_calls"] == 0
    assert second_data["execution_boundary"]["provider_calls"] == 0
    assert second_data["execution_boundary"]["solar_provider_calls"] == 0
    assert (tmp_path / "approval_replay.sqlite3").exists()
    assert request_payload["approval"]["nonce"] not in serialized
    assert request_payload["approval"]["signature_id"] not in serialized
    assert request_payload["approval"]["signed_contract_hash"] not in serialized
    assert "nonce" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_provider_fake_admission_api_blocks_corrupted_sqlite_store_before_fake_invocation(tmp_path):
    (tmp_path / "approval_replay.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=tmp_path,
            )
        )
    )
    request_payload = _provider_admission_payload()

    response = client.post("/api/v1/admissions/provider/fake", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert data["repository_boundary"]["backend"] == "sqlite"
    assert data["repository_boundary"]["persists_across_requests"] is True
    assert checks["provider_repository_available"] is False
    assert data["approval_persistence"]["approval_row_present"] is False
    assert data["execution_boundary"]["fake_provider_invocations"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert request_payload["approval"]["nonce"] not in serialized
    assert request_payload["approval"]["signature_id"] not in serialized
    assert request_payload["approval"]["signed_contract_hash"] not in serialized
    assert "nonce" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_live_fake_admission_api_blocks_corrupted_sqlite_store_before_fake_runtime(tmp_path):
    (tmp_path / "approval_replay.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=tmp_path,
            )
        )
    )
    request_payload = _live_admission_payload()

    response = client.post("/api/v1/admissions/live/fake", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert data["repository_boundary"]["backend"] == "sqlite"
    assert data["repository_boundary"]["persists_across_requests"] is True
    assert checks["live_runner_repository_available"] is False
    assert data["approval_persistence"]["approval_row_present"] is False
    assert data["execution_boundary"]["fake_live_runtime_invocations"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert request_payload["approval"]["nonce"] not in serialized
    assert request_payload["approval"]["signature_id"] not in serialized
    assert request_payload["approval"]["signed_contract_hash"] not in serialized
    assert "nonce" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_provider_fake_admission_api_blocks_unavailable_sqlite_store_before_fake_invocation(tmp_path):
    unavailable_root = tmp_path / "not-a-directory"
    unavailable_root.write_text("file blocks sqlite directory", encoding="utf-8")
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=unavailable_root,
            )
        )
    )
    request_payload = _provider_admission_payload()

    response = client.post("/api/v1/admissions/provider/fake", json=request_payload)

    assert response.status_code == 200
    data = response.json()["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert data["repository_boundary"]["backend"] == "sqlite"
    assert checks["provider_repository_available"] is False
    assert data["execution_boundary"]["fake_provider_invocations"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0


def test_runs_fixture_path_does_not_touch_sqlite_admission_store(tmp_path):
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=tmp_path,
            )
        )
    )

    response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build fixture-only planning flow with API_KEY=secret-value",
            "target_user": "fixture-owner@example.com",
            "product_type": "fixture admission boundary",
            "constraints": ["do not touch durable admission store"],
            "success_criteria": ["public projection only"],
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]

    assert data["runtime_mode"] == "fixture"
    assert data["approval_lifecycle"] == "synthetic"
    assert data["fixture_mode"] is True
    assert data["durable_user_approval"] is False
    assert not (tmp_path / "approval_replay.sqlite3").exists()


def test_provider_envelope_precheck_api_persists_hash_read_model_without_external_calls(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload()

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    admission = data["provider_envelope_admission"]
    read_model = data["provider_envelope_read_model"]
    operator_policy = data["operator_policy_summary"]
    operator_approval = data["operator_approval_envelope"]
    dry_admission = data["live_provider_dry_admission"]
    manual_proposal = data["manual_provider_test_proposal"]
    manual_executor = data["manual_provider_test_executor"]
    one_shot_permission = data["one_shot_live_permission"]
    preflight_audit = data["manual_provider_test_preflight_audit"]
    readiness_decision = data["manual_provider_test_readiness_decision"]
    review_packet = data["manual_provider_test_review_packet"]
    checklist_by_id = {item["id"]: item for item in dry_admission["checklist"]}

    assert data["projection_version"] == "provider-envelope-admission-api-public-v1"
    assert data["runtime_mode"] == "live_admission_precheck"
    assert data["fixture_mode"] is False
    assert data["status"] == "blocked"
    assert admission["status"] == "admitted"
    assert admission["adapter_reached"] is True
    assert admission["request_contract_hash"]
    assert admission["response_contract_hash"]
    assert admission["counts"]["provider_envelope_count"] == 1
    assert read_model["status"] == "available"
    assert read_model["counts"]["provider_envelope_count"] == 1
    assert operator_policy["projection_version"] == "provider-precheck-operator-policy-summary-v1"
    assert operator_policy["policy"]["request_timeout_seconds"] == 30
    assert operator_policy["policy"]["max_cost_units"] == 1
    assert operator_policy["policy"]["max_live_api_calls"] == 1
    assert operator_policy["policy"]["max_output_unit_budget"] == 512
    assert operator_policy["readiness"]["required_control_count"] == len(LIVE_OPEN_REQUIRED_CONTROLS)
    assert operator_policy["readiness"]["missing_control_count"] == 0
    assert operator_policy["readiness"]["allowed_to_execute"] is False
    assert operator_policy["approval_target"]["input_text_included"] is False
    assert operator_policy["approval_target"]["provider_body_included"] is False
    assert operator_policy["approval_target"]["auth_material_included"] is False
    assert operator_approval["projection_version"] == "provider-precheck-operator-approval-envelope-v1"
    assert operator_approval["status"] == "approved"
    assert operator_approval["decision"] == "approved"
    assert operator_approval["operator_ref"] == "local-operator"
    assert operator_approval["policy_summary_hash"] == operator_policy["policy_summary_hash"]
    assert operator_approval["envelope_hash"]
    assert operator_approval["auth_material_returned"] is False
    assert dry_admission["projection_version"] == "live-provider-dry-admission-checklist-v1"
    assert dry_admission["status"] == "dry_admission_only"
    assert dry_admission["live_ready"] is False
    assert dry_admission["allowed_to_execute"] is False
    assert dry_admission["operator_approval"]["status"] == "approved"
    assert dry_admission["operator_approval"]["policy_summary_hash_match"] is True
    assert dry_admission["policy_summary"]["eligible_for_later_live_open"] is True
    assert dry_admission["policy_summary"]["execution_permission_closed"] is True
    assert checklist_by_id["rollback_plan_documented"]["status"] == "manual_required"
    assert checklist_by_id["manual_operator_final_review"]["status"] == "manual_required"
    assert checklist_by_id["execution_permission_closed"]["status"] == "closed"
    assert dry_admission["manual_required_count"] == 2
    assert dry_admission["execution_boundary"]["api_calls"] == 0
    assert dry_admission["execution_boundary"]["network_calls"] == 0
    assert dry_admission["execution_boundary"]["solar_provider_calls"] == 0
    assert dry_admission["execution_boundary"]["target_runtime_calls"] == 0
    assert manual_proposal["projection_version"] == "manual-provider-test-proposal-gate-v1"
    assert manual_proposal["status"] == "blocked"
    assert manual_proposal["proposal_present"] is False
    assert manual_proposal["operator_approval_present"] is False
    assert manual_proposal["live_ready"] is False
    assert manual_proposal["allowed_to_execute"] is False
    assert manual_proposal["disabled_by_default"] is True
    assert manual_proposal["execution_boundary"]["api_calls"] == 0
    assert manual_proposal["execution_boundary"]["network_calls"] == 0
    assert manual_proposal["execution_boundary"]["solar_provider_calls"] == 0
    assert set(manual_executor) == {"status", "reason", "planned_call_hash"}
    assert manual_executor["status"] == "blocked"
    assert manual_executor["reason"] == "manual_provider_test_proposal_required"
    assert manual_executor["planned_call_hash"] == ""
    assert set(one_shot_permission) == {
        "status",
        "reason",
        "permission_contract_hash",
        "expires_at",
        "permission_field_count",
    }
    assert one_shot_permission["status"] == "blocked"
    assert one_shot_permission["reason"] == "one_shot_permission_required"
    assert one_shot_permission["permission_contract_hash"] == ""
    assert one_shot_permission["permission_field_count"] == 0
    assert set(preflight_audit) == {
        "status",
        "reason",
        "preflight_audit_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "no_call_counter_count",
        "no_call_counter_mismatch_count",
    }
    assert preflight_audit["status"] == "blocked"
    assert preflight_audit["reason"] == "proposal_component_missing_or_blocked"
    assert preflight_audit["preflight_audit_hash"] == ""
    assert preflight_audit["component_count"] == 5
    assert preflight_audit["mismatch_count"] >= 1
    assert preflight_audit["no_call_counter_mismatch_count"] == 0
    assert set(readiness_decision) == {
        "status",
        "reason",
        "readiness_decision_hash",
        "decision_count",
        "approve_decision_count",
        "reject_decision_count",
        "defer_decision_count",
        "mismatch_count",
        "execution_permission_count",
    }
    assert readiness_decision["status"] == "blocked"
    assert readiness_decision["reason"] == "readiness_decision_required"
    assert readiness_decision["readiness_decision_hash"] == ""
    assert readiness_decision["decision_count"] == 0
    assert readiness_decision["execution_permission_count"] == 0
    assert set(review_packet) == {
        "status",
        "reason",
        "review_packet_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "execution_permission_count",
    }
    assert review_packet["status"] == "blocked"
    assert review_packet["reason"] == "preflight_component_missing_or_mismatched"
    assert review_packet["review_packet_hash"] == ""
    assert review_packet["component_count"] == 3
    assert review_packet["passed_component_count"] == 1
    assert review_packet["mismatch_count"] >= 1
    assert review_packet["component_hash_count"] == 1
    assert review_packet["execution_permission_count"] == 0
    assert data["repository_boundary"]["provider_envelope_backend"] == "sqlite"
    assert data["repository_boundary"]["root_path_returned"] is False
    assert data["execution_boundary"]["adapter_invocation_count"] == 1
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["live_llm_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_api_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0
    assert (tmp_path / "provider-envelopes.sqlite3").exists()

    read_response = client.get("/api/v1/admissions/provider/envelopes/run-api-envelope")
    assert read_response.status_code == 200
    read_payload = read_response.json()
    read_data = read_payload["data"]
    read_serialized = _serialized(read_payload)

    assert read_data["status"] == "available"
    assert read_data["provider_envelope_admission"]["counts"]["provider_envelope_count"] == 1
    assert admission["request_contract_hash"] in read_serialized
    assert admission["response_contract_hash"] in read_serialized

    for forbidden in (
        "API05_RAW_PROMPT_SENTINEL",
        "API05_PROVIDER_PAYLOAD_SENTINEL",
        "API05_PROVIDER_BODY_SENTINEL",
        "API06_OPERATOR_AUTH_SENTINEL",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "raw_prompt",
        "provider_payload",
        "authorization_material",
        "approved_policy_summary_hash",
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized
        assert forbidden not in read_serialized


def test_provider_envelope_precheck_api_blocks_missing_operator_approval_before_store(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-no-operator",
        include_operator_approval=False,
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}
    operator_policy = data["operator_policy_summary"]
    operator_approval = data["operator_approval_envelope"]
    dry_admission = data["live_provider_dry_admission"]

    assert data["status"] == "blocked"
    assert checks["operator_approval_envelope_present"] is False
    assert operator_policy["policy_summary_hash"]
    assert operator_policy["readiness"]["required_control_count"] == len(LIVE_OPEN_REQUIRED_CONTROLS)
    assert operator_approval["status"] == "missing"
    assert operator_approval["decision"] == "missing"
    assert operator_approval["auth_material_returned"] is False
    assert dry_admission["status"] == "dry_admission_only"
    assert dry_admission["live_ready"] is False
    assert dry_admission["allowed_to_execute"] is False
    assert dry_admission["operator_approval"]["status"] == "missing"
    assert dry_admission["operator_approval"]["policy_summary_hash_match"] is False
    assert dry_admission["blocked_check_count"] >= 1
    assert dry_admission["manual_required_count"] == 2
    assert data["provider_envelope_admission"]["adapter_reached"] is False
    assert data["provider_envelope_admission"]["counts"]["provider_envelope_count"] == 0
    assert data["execution_boundary"]["adapter_invocation_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert not (tmp_path / "provider-envelopes.sqlite3").exists()
    assert "API05_RAW_PROMPT_SENTINEL" not in serialized
    assert "API05_PROVIDER_PAYLOAD_SENTINEL" not in serialized
    assert "authorization_material" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "nonce" not in serialized


def test_provider_envelope_precheck_api_accepts_manual_test_proposal_but_keeps_execution_disabled(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-manual-proposal",
        include_manual_test_proposal=True,
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    manual_proposal = data["manual_provider_test_proposal"]
    manual_executor = data["manual_provider_test_executor"]
    checks = {check["name"]: check["passed"] for check in manual_proposal["checks"]}

    assert manual_proposal["status"] == "approved_disabled"
    assert manual_proposal["proposal_present"] is True
    assert manual_proposal["operator_approval_present"] is True
    assert manual_proposal["proposal_hash"]
    assert manual_proposal["proposal_fields"]["run_id_match"] is True
    assert manual_proposal["proposal_fields"]["prompt_contract_hash_match"] is True
    assert manual_proposal["proposal_fields"]["policy_limits_match"] is True
    assert manual_proposal["proposal_fields"]["rollback_plan_present"] is True
    assert manual_proposal["proposal_fields"]["abort_criteria_count"] == 2
    assert manual_proposal["proposal_fields"]["abort_criteria_hash"]
    assert manual_proposal["operator_approval"]["status"] == "approved"
    assert manual_proposal["operator_approval"]["proposal_hash_match"] is True
    assert manual_proposal["operator_approval"]["auth_material_returned"] is False
    assert manual_proposal["live_ready"] is False
    assert manual_proposal["allowed_to_execute"] is False
    assert manual_proposal["disabled_by_default"] is True
    assert checks["manual_test_proposal_present"] is True
    assert checks["manual_test_operator_approval_proposal_hash_match"] is True
    assert checks["manual_test_execution_disabled_by_default"] is True
    assert manual_proposal["execution_boundary"]["sdk_imports"] == 0
    assert manual_proposal["execution_boundary"]["env_value_reads"] == 0
    assert manual_proposal["execution_boundary"]["api_calls"] == 0
    assert manual_proposal["execution_boundary"]["network_calls"] == 0
    assert manual_proposal["execution_boundary"]["solar_provider_calls"] == 0
    assert manual_proposal["execution_boundary"]["target_runtime_calls"] == 0
    assert set(manual_executor) == {"status", "reason", "planned_call_hash"}
    assert manual_executor["status"] == "blocked"
    assert manual_executor["reason"] == "executor_enable_required"
    assert manual_executor["planned_call_hash"]
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "authorization_material",
        "raw_prompt",
        "provider_payload",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_manual_executor_even_when_enable_requested(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-manual-executor",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    manual_proposal = data["manual_provider_test_proposal"]
    manual_executor = data["manual_provider_test_executor"]

    assert manual_proposal["status"] == "approved_disabled"
    assert set(manual_executor) == {"status", "reason", "planned_call_hash"}
    assert manual_executor["status"] == "blocked"
    assert manual_executor["reason"] == "executor_disabled_by_default"
    assert manual_executor["planned_call_hash"]
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["live_llm_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "authorization_material",
        "raw_prompt",
        "provider_payload",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_one_shot_permission_when_executor_blocked(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-one-shot-permission",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    manual_executor = data["manual_provider_test_executor"]
    one_shot_permission = data["one_shot_live_permission"]
    preflight_audit = data["manual_provider_test_preflight_audit"]

    assert manual_executor["status"] == "blocked"
    assert manual_executor["reason"] == "executor_disabled_by_default"
    assert one_shot_permission["status"] == "blocked"
    assert one_shot_permission["reason"] == "executor_blocked"
    assert set(one_shot_permission) == {
        "status",
        "reason",
        "permission_contract_hash",
        "expires_at",
        "permission_field_count",
    }
    assert one_shot_permission["permission_contract_hash"]
    assert one_shot_permission["expires_at"] == "2099-01-01T00:00:00Z"
    assert one_shot_permission["permission_field_count"] == 11
    assert set(preflight_audit) == {
        "status",
        "reason",
        "preflight_audit_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "no_call_counter_count",
        "no_call_counter_mismatch_count",
    }
    assert preflight_audit["status"] == "blocked"
    assert preflight_audit["reason"] == "preflight_execution_closed"
    assert preflight_audit["preflight_audit_hash"]
    assert preflight_audit["component_count"] == 5
    assert preflight_audit["passed_component_count"] == 5
    assert preflight_audit["mismatch_count"] == 0
    assert preflight_audit["no_call_counter_count"] >= 10
    assert preflight_audit["no_call_counter_mismatch_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_marks_preflight_mismatch_without_raw_echo(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-preflight-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
    )
    request_payload["one_shot_live_permission"]["planned_call_hash"] = "mismatched-call-hash"

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    one_shot_permission = data["one_shot_live_permission"]
    preflight_audit = data["manual_provider_test_preflight_audit"]

    assert one_shot_permission["status"] == "blocked"
    assert one_shot_permission["reason"] == "one_shot_permission_contract_mismatch"
    assert one_shot_permission["permission_contract_hash"] == ""
    assert preflight_audit["status"] == "blocked"
    assert preflight_audit["reason"] == "permission_component_missing_or_mismatch"
    assert preflight_audit["preflight_audit_hash"] == ""
    assert preflight_audit["component_count"] == 5
    assert preflight_audit["mismatch_count"] >= 1
    assert preflight_audit["no_call_counter_mismatch_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_records_readiness_decision_without_execution(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-readiness-decision",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    readiness_decision = data["manual_provider_test_readiness_decision"]

    assert readiness_decision["status"] == "blocked"
    assert readiness_decision["reason"] == "readiness_execution_closed"
    assert set(readiness_decision) == {
        "status",
        "reason",
        "readiness_decision_hash",
        "decision_count",
        "approve_decision_count",
        "reject_decision_count",
        "defer_decision_count",
        "mismatch_count",
        "execution_permission_count",
    }
    assert readiness_decision["readiness_decision_hash"]
    assert readiness_decision["decision_count"] == 1
    assert readiness_decision["approve_decision_count"] == 1
    assert readiness_decision["reject_decision_count"] == 0
    assert readiness_decision["defer_decision_count"] == 0
    assert readiness_decision["mismatch_count"] == 0
    assert readiness_decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_review_packet_without_execution(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-review-packet",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
    )
    request_payload["manual_test_review_packet"] = {
        "authorization_material": "API13_REVIEW_AUTH_SENTINEL",
        "provider_payload": "API13_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "provider_body": "API13_REVIEW_PROVIDER_BODY_SENTINEL",
    }

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review_packet = data["manual_provider_test_review_packet"]
    review_packet_export = data["manual_provider_test_review_packet_export"]
    review_packet_export_read_model = data[
        "manual_provider_test_review_packet_export_read_model"
    ]

    assert review_packet["status"] == "blocked"
    assert review_packet["reason"] == "review_packet_execution_closed"
    assert set(review_packet) == {
        "status",
        "reason",
        "review_packet_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "execution_permission_count",
    }
    assert review_packet["review_packet_hash"]
    assert review_packet["component_count"] == 3
    assert review_packet["passed_component_count"] == 3
    assert review_packet["mismatch_count"] == 0
    assert review_packet["component_hash_count"] == 3
    assert review_packet["execution_permission_count"] == 0
    assert set(review_packet_export) == {
        "status",
        "reason",
        "review_packet_hash",
        "review_packet_export_hash",
        "export_count",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "execution_permission_count",
    }
    assert review_packet_export["status"] == "blocked"
    assert review_packet_export["reason"] == "review_packet_execution_closed"
    assert review_packet_export["review_packet_hash"] == review_packet["review_packet_hash"]
    assert review_packet_export["review_packet_export_hash"]
    assert review_packet_export["export_count"] == 1
    assert review_packet_export["component_count"] == 3
    assert review_packet_export["passed_component_count"] == 3
    assert review_packet_export["mismatch_count"] == 0
    assert review_packet_export["component_hash_count"] == 3
    assert review_packet_export["execution_permission_count"] == 0
    assert review_packet_export_read_model["status"] == "available"
    assert review_packet_export_read_model["counts"]["review_packet_export_count"] == 1
    assert (
        review_packet_export_read_model["counts"]["execution_permission_count"]
        == 0
    )
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "API13_REVIEW_AUTH_SENTINEL",
        "API13_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API13_REVIEW_PROVIDER_BODY_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_reads_review_packet_export_model_without_execution(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-review-packet-read-model",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
    )
    expected_packet = provider_manual_test_review_packet_summary(request_payload)
    request_payload["expected_review_packet_hash"] = expected_packet["review_packet_hash"]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )
    read_response = client.get(
        "/api/v1/admissions/provider/envelopes/run-api-envelope-review-packet-read-model"
    )

    assert response.status_code == 200
    assert read_response.status_code == 200
    payload = response.json()
    read_payload = read_response.json()
    serialized = _serialized({"post": payload, "read": read_payload})
    data = payload["data"]
    read_data = read_payload["data"]
    review_packet = data["manual_provider_test_review_packet"]
    post_export = data["manual_provider_test_review_packet_export"]
    read_export = read_data["manual_provider_test_review_packet_export"]
    read_model = read_data["manual_provider_test_review_packet_export_read_model"]

    assert review_packet["review_packet_hash"] == expected_packet["review_packet_hash"]
    assert post_export["review_packet_hash"] == review_packet["review_packet_hash"]
    assert read_export["status"] == "blocked"
    assert read_export["reason"] == "review_packet_execution_closed"
    assert read_export["review_packet_hash"] == review_packet["review_packet_hash"]
    assert read_export["review_packet_export_hash"] == post_export["review_packet_export_hash"]
    assert read_export["export_count"] == 1
    assert read_export["component_count"] == 3
    assert read_export["mismatch_count"] == 0
    assert read_export["execution_permission_count"] == 0
    assert read_model["status"] == "available"
    assert read_model["counts"]["review_packet_export_count"] == 1
    assert read_model["counts"]["review_packet_hash_count"] == 1
    assert read_model["counts"]["execution_permission_count"] == 0
    assert read_model["repository_boundary"]["raw_row_returned"] is False
    assert read_model["repository_boundary"]["root_path_returned"] is False
    assert read_data["execution_boundary"]["provider_calls"] == 0
    assert read_data["execution_boundary"]["network_calls"] == 0
    assert read_data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_handoff_packet_without_execution(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-handoff-packet",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
    )
    expected_packet = provider_manual_test_review_packet_summary(request_payload)
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    request_payload["expected_review_packet_hash"] = expected_packet["review_packet_hash"]
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )
    read_response = client.get(
        "/api/v1/admissions/provider/envelopes/run-api-envelope-handoff-packet"
    )

    assert response.status_code == 200
    assert read_response.status_code == 200
    payload = response.json()
    read_payload = read_response.json()
    serialized = _serialized({"post": payload, "read": read_payload})
    data = payload["data"]
    handoff = data["manual_provider_test_handoff_packet"]
    read_handoff = read_payload["data"]["manual_provider_test_handoff_packet"]

    assert set(handoff) == {
        "status",
        "reason",
        "handoff_packet_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "export_count",
        "execution_permission_count",
    }
    assert handoff["status"] == "blocked"
    assert handoff["reason"] == "handoff_packet_execution_closed"
    assert handoff["handoff_packet_hash"] == expected_handoff["handoff_packet_hash"]
    assert handoff["component_count"] == 5
    assert handoff["passed_component_count"] == 5
    assert handoff["mismatch_count"] == 0
    assert handoff["component_hash_count"] == 5
    assert handoff["export_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert read_handoff["status"] == "blocked"
    assert read_handoff["reason"] == "policy_summary_missing_or_mismatched"
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_readiness_decision_hash_mismatch(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-readiness-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        readiness_preflight_hash_override="mismatched-preflight-hash",
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    readiness_decision = data["manual_provider_test_readiness_decision"]

    assert readiness_decision["status"] == "blocked"
    assert readiness_decision["reason"] == "preflight_hash_mismatch"
    assert readiness_decision["readiness_decision_hash"] == ""
    assert readiness_decision["decision_count"] == 1
    assert readiness_decision["approve_decision_count"] == 1
    assert readiness_decision["mismatch_count"] >= 1
    assert readiness_decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_review_packet_when_readiness_mismatched(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-review-packet-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        readiness_preflight_hash_override="mismatched-preflight-hash",
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review_packet = data["manual_provider_test_review_packet"]

    assert review_packet["status"] == "blocked"
    assert review_packet["reason"] == "readiness_decision_missing_or_mismatched"
    assert review_packet["review_packet_hash"] == ""
    assert review_packet["component_count"] == 3
    assert review_packet["passed_component_count"] == 2
    assert review_packet["mismatch_count"] == 1
    assert review_packet["component_hash_count"] == 2
    assert review_packet["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_review_packet_export_hash_mismatch(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-review-export-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
    )
    request_payload["expected_review_packet_hash"] = "f" * 64

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}
    review_packet = data["manual_provider_test_review_packet"]
    review_packet_export = data["manual_provider_test_review_packet_export"]

    assert review_packet["status"] == "blocked"
    assert review_packet["reason"] == "review_packet_execution_closed"
    assert review_packet["review_packet_hash"]
    assert review_packet_export["status"] == "blocked"
    assert review_packet_export["reason"] == "review_packet_hash_mismatch"
    assert review_packet_export["review_packet_hash"] == ""
    assert review_packet_export["review_packet_export_hash"] == ""
    assert review_packet_export["export_count"] == 0
    assert review_packet_export["execution_permission_count"] == 0
    assert checks["manual_provider_test_review_packet_hash_match"] is False
    assert data["provider_envelope_admission"]["adapter_reached"] is False
    assert data["execution_boundary"]["adapter_invocation_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0
    assert not (tmp_path / "provider-envelopes.sqlite3").exists()

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_handoff_export_hash_mismatch(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-handoff-export-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
    )
    expected_packet = provider_manual_test_review_packet_summary(request_payload)
    request_payload["expected_review_packet_hash"] = expected_packet["review_packet_hash"]
    request_payload["expected_review_packet_export_hash"] = "f" * 64

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}
    review_packet = data["manual_provider_test_review_packet"]
    review_packet_export = data["manual_provider_test_review_packet_export"]
    handoff = data["manual_provider_test_handoff_packet"]

    assert review_packet["status"] == "blocked"
    assert review_packet["reason"] == "review_packet_execution_closed"
    assert review_packet["review_packet_hash"] == expected_packet["review_packet_hash"]
    assert review_packet_export["status"] == "blocked"
    assert review_packet_export["reason"] == "review_packet_export_hash_mismatch"
    assert review_packet_export["review_packet_export_hash"] == ""
    assert handoff["status"] == "blocked"
    assert handoff["reason"] == "review_packet_export_hash_mismatch"
    assert handoff["handoff_packet_hash"] == ""
    assert handoff["execution_permission_count"] == 0
    assert checks["manual_provider_test_review_packet_export_hash_match"] is False
    assert data["provider_envelope_admission"]["adapter_reached"] is False
    assert data["execution_boundary"]["adapter_invocation_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0
    assert not (tmp_path / "provider-envelopes.sqlite3").exists()

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_handoff_packet_hash_mismatch(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-handoff-packet-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
    )
    expected_packet = provider_manual_test_review_packet_summary(request_payload)
    request_payload["expected_review_packet_hash"] = expected_packet["review_packet_hash"]
    request_payload["expected_handoff_packet_hash"] = "f" * 64

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}
    review_packet_export = data["manual_provider_test_review_packet_export"]
    handoff = data["manual_provider_test_handoff_packet"]

    assert review_packet_export["status"] == "blocked"
    assert review_packet_export["reason"] == "review_packet_execution_closed"
    assert review_packet_export["review_packet_export_hash"]
    assert handoff["status"] == "blocked"
    assert handoff["reason"] == "handoff_packet_hash_mismatch"
    assert handoff["handoff_packet_hash"] == ""
    assert handoff["execution_permission_count"] == 0
    assert checks["manual_provider_test_handoff_packet_hash_match"] is False
    assert data["provider_envelope_admission"]["adapter_reached"] is False
    assert data["execution_boundary"]["adapter_invocation_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0
    assert not (tmp_path / "provider-envelopes.sqlite3").exists()

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_missing_operator_opt_in_without_execution(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-opt-in-missing",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    opt_in = data["manual_provider_test_operator_opt_in"]

    assert set(opt_in) == {
        "status",
        "reason",
        "operator_opt_in_hash",
        "handoff_packet_hash",
        "checklist_item_count",
        "passed_check_count",
        "mismatch_count",
        "execution_permission_count",
    }
    assert opt_in["status"] == "blocked"
    assert opt_in["reason"] == "operator_opt_in_required"
    assert opt_in["operator_opt_in_hash"] == ""
    assert opt_in["handoff_packet_hash"] == expected_handoff["handoff_packet_hash"]
    assert opt_in["checklist_item_count"] == 5
    assert opt_in["passed_check_count"] == 1
    assert opt_in["mismatch_count"] == 4
    assert opt_in["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API16_OPT_IN_AUTH_SENTINEL",
        "API16_OPT_IN_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_accepts_operator_opt_in_but_keeps_execution_disabled(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-opt-in-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_opt_in = provider_manual_test_operator_opt_in_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    opt_in = data["manual_provider_test_operator_opt_in"]

    assert opt_in["status"] == "blocked"
    assert opt_in["reason"] == "operator_opt_in_execution_closed"
    assert opt_in["operator_opt_in_hash"] == expected_opt_in["operator_opt_in_hash"]
    assert opt_in["handoff_packet_hash"] == expected_handoff["handoff_packet_hash"]
    assert opt_in["checklist_item_count"] == 5
    assert opt_in["passed_check_count"] == 5
    assert opt_in["mismatch_count"] == 0
    assert opt_in["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API16_OPT_IN_AUTH_SENTINEL",
        "API16_OPT_IN_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_operator_opt_in_handoff_mismatch(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-opt-in-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        operator_opt_in_handoff_hash_override="f" * 64,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    opt_in = data["manual_provider_test_operator_opt_in"]

    assert opt_in["status"] == "blocked"
    assert opt_in["reason"] == "handoff_packet_hash_mismatch"
    assert opt_in["operator_opt_in_hash"] == ""
    assert opt_in["handoff_packet_hash"] == expected_handoff["handoff_packet_hash"]
    assert opt_in["checklist_item_count"] == 5
    assert opt_in["mismatch_count"] == 1
    assert opt_in["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API16_OPT_IN_AUTH_SENTINEL",
        "API16_OPT_IN_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_sealed_packet_without_expected_operator_opt_in_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-sealed-missing-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_opt_in = provider_manual_test_operator_opt_in_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    sealed = data["manual_provider_test_sealed_pre_execution_packet"]

    assert set(sealed) == {
        "status",
        "reason",
        "sealed_packet_hash",
        "handoff_packet_hash",
        "operator_opt_in_hash",
        "cost_timeout_quota_hash",
        "rollback_abort_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "execution_permission_count",
    }
    assert sealed["status"] == "blocked"
    assert sealed["reason"] == "expected_operator_opt_in_hash_required"
    assert sealed["sealed_packet_hash"] == ""
    assert sealed["handoff_packet_hash"] == expected_handoff["handoff_packet_hash"]
    assert sealed["operator_opt_in_hash"] == expected_opt_in["operator_opt_in_hash"]
    assert sealed["cost_timeout_quota_hash"]
    assert sealed["rollback_abort_hash"]
    assert sealed["component_count"] == 6
    assert sealed["passed_component_count"] == 5
    assert sealed["mismatch_count"] == 1
    assert sealed["component_hash_count"] == 4
    assert sealed["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API17_SEALED_AUTH_SENTINEL",
        "API17_SEALED_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_sealed_packet_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-sealed-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_opt_in = provider_manual_test_operator_opt_in_summary(request_payload)
    expected_sealed = provider_manual_test_sealed_pre_execution_packet_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    sealed = data["manual_provider_test_sealed_pre_execution_packet"]

    assert sealed["status"] == "blocked"
    assert sealed["reason"] == "sealed_pre_execution_packet_execution_closed"
    assert sealed["sealed_packet_hash"] == expected_sealed["sealed_packet_hash"]
    assert sealed["handoff_packet_hash"] == expected_handoff["handoff_packet_hash"]
    assert sealed["operator_opt_in_hash"] == expected_opt_in["operator_opt_in_hash"]
    assert sealed["cost_timeout_quota_hash"] == expected_sealed["cost_timeout_quota_hash"]
    assert sealed["rollback_abort_hash"] == expected_sealed["rollback_abort_hash"]
    assert sealed["component_count"] == 6
    assert sealed["passed_component_count"] == 6
    assert sealed["mismatch_count"] == 0
    assert sealed["component_hash_count"] == 4
    assert sealed["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API17_SEALED_AUTH_SENTINEL",
        "API17_SEALED_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_sealed_packet_operator_hash_mismatch(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-sealed-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        sealed_operator_opt_in_hash_override="f" * 64,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_opt_in = provider_manual_test_operator_opt_in_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    sealed = data["manual_provider_test_sealed_pre_execution_packet"]

    assert sealed["status"] == "blocked"
    assert sealed["reason"] == "operator_opt_in_hash_mismatch"
    assert sealed["sealed_packet_hash"] == ""
    assert sealed["handoff_packet_hash"] == expected_handoff["handoff_packet_hash"]
    assert sealed["operator_opt_in_hash"] == expected_opt_in["operator_opt_in_hash"]
    assert sealed["component_count"] == 6
    assert sealed["passed_component_count"] == 5
    assert sealed["mismatch_count"] == 1
    assert sealed["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API17_SEALED_AUTH_SENTINEL",
        "API17_SEALED_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_arming_record_without_expected_sealed_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-arming-missing-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_sealed = provider_manual_test_sealed_pre_execution_packet_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    arming = data["manual_provider_test_arming_record"]

    assert set(arming) == {
        "status",
        "reason",
        "arming_record_hash",
        "sealed_packet_hash",
        "operator_hash",
        "expiry_hash",
        "rollback_abort_hash",
        "abort_policy_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "execution_permission_count",
    }
    assert arming["status"] == "blocked"
    assert arming["reason"] == "expected_sealed_packet_hash_required"
    assert arming["arming_record_hash"] == ""
    assert arming["sealed_packet_hash"] == expected_sealed["sealed_packet_hash"]
    assert arming["operator_hash"] == ""
    assert arming["expiry_hash"] == ""
    assert arming["rollback_abort_hash"] == ""
    assert arming["abort_policy_hash"] == ""
    assert arming["component_count"] == 8
    assert arming["passed_component_count"] == 1
    assert arming["mismatch_count"] == 7
    assert arming["component_hash_count"] == 1
    assert arming["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API18_ARMING_AUTH_SENTINEL",
        "API18_ARMING_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_arming_record_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-arming-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_sealed = provider_manual_test_sealed_pre_execution_packet_summary(
        request_payload
    )
    expected_arming = provider_manual_test_arming_record_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    arming = data["manual_provider_test_arming_record"]

    assert arming["status"] == "blocked"
    assert arming["reason"] == "arming_record_execution_closed"
    assert arming["arming_record_hash"] == expected_arming["arming_record_hash"]
    assert arming["sealed_packet_hash"] == expected_sealed["sealed_packet_hash"]
    assert arming["operator_hash"] == expected_arming["operator_hash"]
    assert arming["expiry_hash"] == expected_arming["expiry_hash"]
    assert arming["rollback_abort_hash"] == expected_sealed["rollback_abort_hash"]
    assert arming["abort_policy_hash"] == request_payload[
        "manual_test_live_execution_arming"
    ]["abort_policy_hash"]
    assert arming["component_count"] == 8
    assert arming["passed_component_count"] == 8
    assert arming["mismatch_count"] == 0
    assert arming["component_hash_count"] == 5
    assert arming["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API18_ARMING_AUTH_SENTINEL",
        "API18_ARMING_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_arming_record_sealed_hash_mismatch(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-arming-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        arming_record_sealed_hash_override="f" * 64,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_sealed = provider_manual_test_sealed_pre_execution_packet_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    arming = data["manual_provider_test_arming_record"]

    assert arming["status"] == "blocked"
    assert arming["reason"] == "arming_record_sealed_hash_mismatch"
    assert arming["arming_record_hash"] == ""
    assert arming["sealed_packet_hash"] == expected_sealed["sealed_packet_hash"]
    assert arming["operator_hash"]
    assert arming["expiry_hash"]
    assert arming["rollback_abort_hash"] == expected_sealed["rollback_abort_hash"]
    assert arming["abort_policy_hash"] == request_payload[
        "manual_test_live_execution_arming"
    ]["abort_policy_hash"]
    assert arming["component_count"] == 8
    assert arming["passed_component_count"] == 7
    assert arming["mismatch_count"] == 1
    assert arming["component_hash_count"] == 5
    assert arming["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API18_ARMING_AUTH_SENTINEL",
        "API18_ARMING_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_release_proposal_without_expected_arming_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-release-missing-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_arming = provider_manual_test_arming_record_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    release = data["manual_provider_test_release_proposal"]

    assert set(release) == {
        "status",
        "reason",
        "release_proposal_hash",
        "arming_record_hash",
        "operator_hash",
        "release_window_hash",
        "rollback_abort_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "execution_permission_count",
    }
    assert release["status"] == "blocked"
    assert release["reason"] == "expected_arming_record_hash_required"
    assert release["release_proposal_hash"] == ""
    assert release["arming_record_hash"] == expected_arming["arming_record_hash"]
    assert release["operator_hash"] == ""
    assert release["release_window_hash"] == ""
    assert release["rollback_abort_hash"] == ""
    assert release["component_count"] == 7
    assert release["passed_component_count"] == 1
    assert release["mismatch_count"] == 6
    assert release["component_hash_count"] == 1
    assert release["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API19_RELEASE_AUTH_SENTINEL",
        "API19_RELEASE_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_release_proposal_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-release-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_arming = provider_manual_test_arming_record_summary(request_payload)
    expected_release = provider_manual_test_release_proposal_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    release = data["manual_provider_test_release_proposal"]

    assert release["status"] == "blocked"
    assert release["reason"] == "release_proposal_execution_closed"
    assert release["release_proposal_hash"] == expected_release["release_proposal_hash"]
    assert release["arming_record_hash"] == expected_arming["arming_record_hash"]
    assert release["operator_hash"] == expected_release["operator_hash"]
    assert release["release_window_hash"] == expected_release["release_window_hash"]
    assert release["rollback_abort_hash"] == expected_arming["rollback_abort_hash"]
    assert release["component_count"] == 7
    assert release["passed_component_count"] == 7
    assert release["mismatch_count"] == 0
    assert release["component_hash_count"] == 4
    assert release["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API19_RELEASE_AUTH_SENTINEL",
        "API19_RELEASE_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_release_proposal_arming_hash_mismatch(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-release-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        release_proposal_arming_hash_override="f" * 64,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_arming = provider_manual_test_arming_record_summary(request_payload)
    expected_release = provider_manual_test_release_proposal_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    release = data["manual_provider_test_release_proposal"]

    assert release["status"] == "blocked"
    assert release["reason"] == "release_proposal_arming_hash_mismatch"
    assert release["release_proposal_hash"] == ""
    assert release["arming_record_hash"] == expected_arming["arming_record_hash"]
    assert release["operator_hash"] == expected_release["operator_hash"]
    assert release["release_window_hash"] == expected_release["release_window_hash"]
    assert release["rollback_abort_hash"] == expected_arming["rollback_abort_hash"]
    assert release["component_count"] == 7
    assert release["passed_component_count"] == 6
    assert release["mismatch_count"] == 1
    assert release["component_hash_count"] == 4
    assert release["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API19_RELEASE_AUTH_SENTINEL",
        "API19_RELEASE_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_final_release_packet_without_expected_release_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-final-release-missing-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_release = provider_manual_test_release_proposal_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    final_packet = data["manual_provider_test_final_release_packet"]

    assert set(final_packet) == {
        "status",
        "reason",
        "final_release_packet_hash",
        "release_proposal_hash",
        "arming_record_hash",
        "operator_hash",
        "release_window_hash",
        "rollback_abort_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "execution_permission_count",
    }
    assert final_packet["status"] == "blocked"
    assert final_packet["reason"] == "expected_release_proposal_hash_required"
    assert final_packet["final_release_packet_hash"] == ""
    assert final_packet["release_proposal_hash"] == expected_release[
        "release_proposal_hash"
    ]
    assert final_packet["arming_record_hash"] == expected_release["arming_record_hash"]
    assert final_packet["operator_hash"] == expected_release["operator_hash"]
    assert final_packet["release_window_hash"] == expected_release["release_window_hash"]
    assert final_packet["rollback_abort_hash"] == expected_release["rollback_abort_hash"]
    assert final_packet["component_count"] == 8
    assert final_packet["passed_component_count"] == 5
    assert final_packet["mismatch_count"] == 3
    assert final_packet["component_hash_count"] == 5
    assert final_packet["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API20_FINAL_RELEASE_AUTH_SENTINEL",
        "API20_FINAL_RELEASE_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_final_release_packet_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-final-release-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_release = provider_manual_test_release_proposal_summary(request_payload)
    expected_final = provider_manual_test_final_release_packet_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    final_packet = data["manual_provider_test_final_release_packet"]

    assert final_packet["status"] == "blocked"
    assert final_packet["reason"] == "final_release_packet_execution_closed"
    assert final_packet["final_release_packet_hash"] == expected_final[
        "final_release_packet_hash"
    ]
    assert final_packet["release_proposal_hash"] == expected_release[
        "release_proposal_hash"
    ]
    assert final_packet["arming_record_hash"] == expected_release["arming_record_hash"]
    assert final_packet["operator_hash"] == expected_release["operator_hash"]
    assert final_packet["release_window_hash"] == expected_release["release_window_hash"]
    assert final_packet["rollback_abort_hash"] == expected_release["rollback_abort_hash"]
    assert final_packet["component_count"] == 8
    assert final_packet["passed_component_count"] == 8
    assert final_packet["mismatch_count"] == 0
    assert final_packet["component_hash_count"] == 5
    assert final_packet["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API20_FINAL_RELEASE_AUTH_SENTINEL",
        "API20_FINAL_RELEASE_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_final_release_packet_proposal_hash_mismatch(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-final-release-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        final_packet_release_hash_override="f" * 64,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_release = provider_manual_test_release_proposal_summary(request_payload)
    expected_final = provider_manual_test_final_release_packet_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    final_packet = data["manual_provider_test_final_release_packet"]

    assert final_packet["status"] == "blocked"
    assert final_packet["reason"] == "final_release_packet_proposal_hash_mismatch"
    assert final_packet["final_release_packet_hash"] == ""
    assert final_packet["release_proposal_hash"] == expected_release[
        "release_proposal_hash"
    ]
    assert final_packet["arming_record_hash"] == expected_final["arming_record_hash"]
    assert final_packet["operator_hash"] == expected_final["operator_hash"]
    assert final_packet["release_window_hash"] == expected_final[
        "release_window_hash"
    ]
    assert final_packet["rollback_abort_hash"] == expected_final["rollback_abort_hash"]
    assert final_packet["component_count"] == 8
    assert final_packet["passed_component_count"] == 7
    assert final_packet["mismatch_count"] == 1
    assert final_packet["component_hash_count"] == 5
    assert final_packet["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API20_FINAL_RELEASE_AUTH_SENTINEL",
        "API20_FINAL_RELEASE_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_switch_without_expected_final_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-switch-missing-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final = provider_manual_test_final_release_packet_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    switch = data["manual_provider_test_execution_switch"]

    assert set(switch) == {
        "status",
        "reason",
        "execution_switch_hash",
        "final_release_packet_hash",
        "switch_enable_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "enable_request_count",
        "execution_permission_count",
    }
    assert switch["status"] == "blocked"
    assert switch["reason"] == "expected_final_release_packet_hash_required"
    assert switch["execution_switch_hash"] == ""
    assert switch["final_release_packet_hash"] == expected_final[
        "final_release_packet_hash"
    ]
    assert switch["switch_enable_hash"] == ""
    assert switch["component_count"] == 5
    assert switch["passed_component_count"] == 1
    assert switch["mismatch_count"] == 4
    assert switch["component_hash_count"] == 1
    assert switch["enable_request_count"] == 0
    assert switch["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API21_SWITCH_AUTH_SENTINEL",
        "API21_SWITCH_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "enable_requested",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_switch_without_enable_flag(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-switch-missing-enable",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final = provider_manual_test_final_release_packet_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    switch = data["manual_provider_test_execution_switch"]

    assert switch["status"] == "blocked"
    assert switch["reason"] == "execution_switch_enable_required"
    assert switch["execution_switch_hash"] == ""
    assert switch["final_release_packet_hash"] == expected_final[
        "final_release_packet_hash"
    ]
    assert switch["switch_enable_hash"] == ""
    assert switch["component_count"] == 5
    assert switch["passed_component_count"] == 4
    assert switch["mismatch_count"] == 1
    assert switch["component_hash_count"] == 1
    assert switch["enable_request_count"] == 0
    assert switch["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API21_SWITCH_AUTH_SENTINEL",
        "API21_SWITCH_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "enable_requested",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_switch_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-switch-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final = provider_manual_test_final_release_packet_summary(request_payload)
    expected_switch = provider_manual_test_execution_switch_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    switch = data["manual_provider_test_execution_switch"]

    assert switch["status"] == "blocked"
    assert switch["reason"] == "execution_switch_disabled_by_default"
    assert switch["execution_switch_hash"] == expected_switch["execution_switch_hash"]
    assert switch["final_release_packet_hash"] == expected_final[
        "final_release_packet_hash"
    ]
    assert switch["switch_enable_hash"] == expected_switch["switch_enable_hash"]
    assert switch["component_count"] == 5
    assert switch["passed_component_count"] == 5
    assert switch["mismatch_count"] == 0
    assert switch["component_hash_count"] == 2
    assert switch["enable_request_count"] == 1
    assert switch["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API21_SWITCH_AUTH_SENTINEL",
        "API21_SWITCH_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "enable_requested",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_executor_preflight_without_expected_switch_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-preflight-missing-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_switch = provider_manual_test_execution_switch_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    preflight = data["manual_provider_test_executor_preflight"]

    assert set(preflight) == {
        "status",
        "reason",
        "executor_preflight_hash",
        "execution_switch_hash",
        "final_release_packet_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "execution_permission_count",
    }
    assert preflight["status"] == "blocked"
    assert preflight["reason"] == "expected_execution_switch_hash_required"
    assert preflight["executor_preflight_hash"] == ""
    assert preflight["execution_switch_hash"] == expected_switch["execution_switch_hash"]
    assert preflight["final_release_packet_hash"] == expected_switch[
        "final_release_packet_hash"
    ]
    assert preflight["no_call_counters_hash"]
    assert preflight["component_count"] == 5
    assert preflight["passed_component_count"] == 2
    assert preflight["mismatch_count"] == 3
    assert preflight["component_hash_count"] == 3
    assert preflight["no_call_counter_count"] == 13
    assert preflight["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API22_PREFLIGHT_AUTH_SENTINEL",
        "API22_PREFLIGHT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_executor_preflight",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_executor_preflight_without_preflight_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-preflight-missing-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_switch = provider_manual_test_execution_switch_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_switch_hash"] = expected_switch[
        "execution_switch_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    preflight = data["manual_provider_test_executor_preflight"]

    assert preflight["status"] == "blocked"
    assert preflight["reason"] == "executor_preflight_required"
    assert preflight["executor_preflight_hash"] == ""
    assert preflight["execution_switch_hash"] == expected_switch["execution_switch_hash"]
    assert preflight["final_release_packet_hash"] == expected_switch[
        "final_release_packet_hash"
    ]
    assert preflight["no_call_counters_hash"]
    assert preflight["component_count"] == 5
    assert preflight["passed_component_count"] == 3
    assert preflight["mismatch_count"] == 2
    assert preflight["component_hash_count"] == 3
    assert preflight["no_call_counter_count"] == 13
    assert preflight["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API22_PREFLIGHT_AUTH_SENTINEL",
        "API22_PREFLIGHT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_executor_preflight",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_executor_preflight_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-preflight-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_switch = provider_manual_test_execution_switch_summary(request_payload)
    expected_preflight = provider_manual_test_executor_preflight_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    preflight = data["manual_provider_test_executor_preflight"]

    assert preflight["status"] == "blocked"
    assert preflight["reason"] == "executor_preflight_execution_closed"
    assert preflight["executor_preflight_hash"] == expected_preflight[
        "executor_preflight_hash"
    ]
    assert preflight["execution_switch_hash"] == expected_switch["execution_switch_hash"]
    assert preflight["final_release_packet_hash"] == expected_switch[
        "final_release_packet_hash"
    ]
    assert preflight["no_call_counters_hash"] == expected_preflight[
        "no_call_counters_hash"
    ]
    assert preflight["component_count"] == 5
    assert preflight["passed_component_count"] == 5
    assert preflight["mismatch_count"] == 0
    assert preflight["component_hash_count"] == 3
    assert preflight["no_call_counter_count"] == 13
    assert preflight["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API22_PREFLIGHT_AUTH_SENTINEL",
        "API22_PREFLIGHT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_executor_preflight",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_dispatch_record_without_expected_preflight_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-dispatch-missing-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_preflight = provider_manual_test_executor_preflight_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    dispatch = data["manual_provider_test_executor_dispatch_record"]

    assert set(dispatch) == {
        "status",
        "reason",
        "dispatch_record_hash",
        "executor_preflight_hash",
        "planned_dispatch_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "dispatch_request_count",
        "execution_permission_count",
    }
    assert dispatch["status"] == "blocked"
    assert dispatch["reason"] == "expected_executor_preflight_hash_required"
    assert dispatch["dispatch_record_hash"] == ""
    assert dispatch["executor_preflight_hash"] == expected_preflight[
        "executor_preflight_hash"
    ]
    assert dispatch["planned_dispatch_hash"] == ""
    assert dispatch["no_call_counters_hash"]
    assert dispatch["component_count"] == 6
    assert dispatch["passed_component_count"] == 2
    assert dispatch["mismatch_count"] == 4
    assert dispatch["component_hash_count"] == 2
    assert dispatch["no_call_counter_count"] == 13
    assert dispatch["dispatch_request_count"] == 0
    assert dispatch["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API23_DISPATCH_AUTH_SENTINEL",
        "API23_DISPATCH_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_executor_dispatch_record",
        "dispatch_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_dispatch_record_without_record_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-dispatch-missing-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_preflight = provider_manual_test_executor_preflight_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_executor_preflight_hash"] = expected_preflight[
        "executor_preflight_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    dispatch = data["manual_provider_test_executor_dispatch_record"]

    assert dispatch["status"] == "blocked"
    assert dispatch["reason"] == "executor_dispatch_record_required"
    assert dispatch["dispatch_record_hash"] == ""
    assert dispatch["executor_preflight_hash"] == expected_preflight[
        "executor_preflight_hash"
    ]
    assert dispatch["planned_dispatch_hash"] == ""
    assert dispatch["no_call_counters_hash"]
    assert dispatch["component_count"] == 6
    assert dispatch["passed_component_count"] == 3
    assert dispatch["mismatch_count"] == 3
    assert dispatch["component_hash_count"] == 2
    assert dispatch["no_call_counter_count"] == 13
    assert dispatch["dispatch_request_count"] == 0
    assert dispatch["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API23_DISPATCH_AUTH_SENTINEL",
        "API23_DISPATCH_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_executor_dispatch_record",
        "dispatch_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_dispatch_record_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-dispatch-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_preflight = provider_manual_test_executor_preflight_summary(
        request_payload
    )
    expected_dispatch = provider_manual_test_executor_dispatch_record_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    dispatch = data["manual_provider_test_executor_dispatch_record"]

    assert dispatch["status"] == "blocked"
    assert dispatch["reason"] == "executor_dispatch_record_execution_closed"
    assert dispatch["dispatch_record_hash"] == expected_dispatch[
        "dispatch_record_hash"
    ]
    assert dispatch["executor_preflight_hash"] == expected_preflight[
        "executor_preflight_hash"
    ]
    assert dispatch["planned_dispatch_hash"] == expected_dispatch[
        "planned_dispatch_hash"
    ]
    assert dispatch["no_call_counters_hash"] == expected_dispatch[
        "no_call_counters_hash"
    ]
    assert dispatch["component_count"] == 6
    assert dispatch["passed_component_count"] == 6
    assert dispatch["mismatch_count"] == 0
    assert dispatch["component_hash_count"] == 3
    assert dispatch["no_call_counter_count"] == 13
    assert dispatch["dispatch_request_count"] == 1
    assert dispatch["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API23_DISPATCH_AUTH_SENTINEL",
        "API23_DISPATCH_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_executor_dispatch_record",
        "dispatch_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_invocation_receipt_without_expected_dispatch_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-receipt-missing-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_dispatch = provider_manual_test_executor_dispatch_record_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    receipt = data["manual_provider_test_invocation_receipt"]

    assert set(receipt) == {
        "status",
        "reason",
        "invocation_receipt_hash",
        "dispatch_record_hash",
        "result_placeholder_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "receipt_request_count",
        "execution_permission_count",
    }
    assert receipt["status"] == "blocked"
    assert receipt["reason"] == "expected_dispatch_record_hash_required"
    assert receipt["invocation_receipt_hash"] == ""
    assert receipt["dispatch_record_hash"] == expected_dispatch[
        "dispatch_record_hash"
    ]
    assert receipt["result_placeholder_hash"] == ""
    assert receipt["no_call_counters_hash"]
    assert receipt["component_count"] == 6
    assert receipt["passed_component_count"] == 2
    assert receipt["mismatch_count"] == 4
    assert receipt["component_hash_count"] == 2
    assert receipt["no_call_counter_count"] == 13
    assert receipt["receipt_request_count"] == 0
    assert receipt["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API24_RECEIPT_AUTH_SENTINEL",
        "API24_RECEIPT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_executor_invocation_receipt",
        "receipt_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_invocation_receipt_without_receipt_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-receipt-missing-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_dispatch = provider_manual_test_executor_dispatch_record_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_dispatch_record_hash"] = expected_dispatch[
        "dispatch_record_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    receipt = data["manual_provider_test_invocation_receipt"]

    assert receipt["status"] == "blocked"
    assert receipt["reason"] == "invocation_receipt_required"
    assert receipt["invocation_receipt_hash"] == ""
    assert receipt["dispatch_record_hash"] == expected_dispatch[
        "dispatch_record_hash"
    ]
    assert receipt["result_placeholder_hash"] == ""
    assert receipt["no_call_counters_hash"]
    assert receipt["component_count"] == 6
    assert receipt["passed_component_count"] == 3
    assert receipt["mismatch_count"] == 3
    assert receipt["component_hash_count"] == 2
    assert receipt["no_call_counter_count"] == 13
    assert receipt["receipt_request_count"] == 0
    assert receipt["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API24_RECEIPT_AUTH_SENTINEL",
        "API24_RECEIPT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_executor_invocation_receipt",
        "receipt_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_invocation_receipt_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-receipt-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_dispatch = provider_manual_test_executor_dispatch_record_summary(
        request_payload
    )
    expected_receipt = provider_manual_test_invocation_receipt_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    receipt = data["manual_provider_test_invocation_receipt"]

    assert receipt["status"] == "blocked"
    assert receipt["reason"] == "invocation_receipt_execution_closed"
    assert receipt["invocation_receipt_hash"] == expected_receipt[
        "invocation_receipt_hash"
    ]
    assert receipt["dispatch_record_hash"] == expected_dispatch[
        "dispatch_record_hash"
    ]
    assert receipt["result_placeholder_hash"] == expected_receipt[
        "result_placeholder_hash"
    ]
    assert receipt["no_call_counters_hash"] == expected_receipt[
        "no_call_counters_hash"
    ]
    assert receipt["component_count"] == 6
    assert receipt["passed_component_count"] == 6
    assert receipt["mismatch_count"] == 0
    assert receipt["component_hash_count"] == 3
    assert receipt["no_call_counter_count"] == 13
    assert receipt["receipt_request_count"] == 1
    assert receipt["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API24_RECEIPT_AUTH_SENTINEL",
        "API24_RECEIPT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_executor_invocation_receipt",
        "receipt_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_post_invocation_audit_without_expected_receipt_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-audit-missing-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_receipt = provider_manual_test_invocation_receipt_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    audit = data["manual_provider_test_post_invocation_audit"]

    assert set(audit) == {
        "status",
        "reason",
        "post_invocation_audit_hash",
        "invocation_receipt_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "audit_request_count",
        "execution_permission_count",
    }
    assert audit["status"] == "blocked"
    assert audit["reason"] == "expected_invocation_receipt_hash_required"
    assert audit["post_invocation_audit_hash"] == ""
    assert audit["invocation_receipt_hash"] == expected_receipt[
        "invocation_receipt_hash"
    ]
    assert audit["claim_boundary_hash"]
    assert audit["no_call_counters_hash"]
    assert audit["component_count"] == 7
    assert audit["passed_component_count"] == 3
    assert audit["mismatch_count"] == 4
    assert audit["component_hash_count"] == 3
    assert audit["no_call_counter_count"] == 13
    assert audit["claim_boundary_check_count"] == 3
    assert audit["audit_request_count"] == 0
    assert audit["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API25_AUDIT_AUTH_SENTINEL",
        "API25_AUDIT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_post_invocation_audit",
        "audit_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_post_invocation_audit_without_audit_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-audit-missing-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_receipt = provider_manual_test_invocation_receipt_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_invocation_receipt_hash"] = expected_receipt[
        "invocation_receipt_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    audit = data["manual_provider_test_post_invocation_audit"]

    assert audit["status"] == "blocked"
    assert audit["reason"] == "post_invocation_audit_required"
    assert audit["post_invocation_audit_hash"] == ""
    assert audit["invocation_receipt_hash"] == expected_receipt[
        "invocation_receipt_hash"
    ]
    assert audit["claim_boundary_hash"]
    assert audit["no_call_counters_hash"]
    assert audit["component_count"] == 7
    assert audit["passed_component_count"] == 4
    assert audit["mismatch_count"] == 3
    assert audit["component_hash_count"] == 3
    assert audit["no_call_counter_count"] == 13
    assert audit["claim_boundary_check_count"] == 3
    assert audit["audit_request_count"] == 0
    assert audit["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API25_AUDIT_AUTH_SENTINEL",
        "API25_AUDIT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_post_invocation_audit",
        "audit_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_post_invocation_audit_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-audit-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_receipt = provider_manual_test_invocation_receipt_summary(request_payload)
    expected_audit = provider_manual_test_post_invocation_audit_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    audit = data["manual_provider_test_post_invocation_audit"]

    assert audit["status"] == "blocked"
    assert audit["reason"] == "post_invocation_audit_execution_closed"
    assert audit["post_invocation_audit_hash"] == expected_audit[
        "post_invocation_audit_hash"
    ]
    assert audit["invocation_receipt_hash"] == expected_receipt[
        "invocation_receipt_hash"
    ]
    assert audit["claim_boundary_hash"] == expected_audit["claim_boundary_hash"]
    assert audit["no_call_counters_hash"] == expected_audit[
        "no_call_counters_hash"
    ]
    assert audit["component_count"] == 7
    assert audit["passed_component_count"] == 7
    assert audit["mismatch_count"] == 0
    assert audit["component_hash_count"] == 3
    assert audit["no_call_counter_count"] == 13
    assert audit["claim_boundary_check_count"] == 3
    assert audit["audit_request_count"] == 1
    assert audit["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API25_AUDIT_AUTH_SENTINEL",
        "API25_AUDIT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_post_invocation_audit",
        "audit_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_completion_summary_without_expected_audit_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-completion-missing-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_audit = provider_manual_test_post_invocation_audit_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    summary = data["manual_provider_test_completion_summary"]

    assert set(summary) == {
        "status",
        "reason",
        "completion_summary_hash",
        "post_invocation_audit_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "summary_request_count",
        "execution_permission_count",
    }
    assert summary["status"] == "blocked"
    assert summary["reason"] == "expected_post_invocation_audit_hash_required"
    assert summary["completion_summary_hash"] == ""
    assert summary["post_invocation_audit_hash"] == expected_audit[
        "post_invocation_audit_hash"
    ]
    assert summary["claim_boundary_hash"]
    assert summary["no_call_counters_hash"]
    assert summary["component_count"] == 7
    assert summary["passed_component_count"] == 3
    assert summary["mismatch_count"] == 4
    assert summary["component_hash_count"] == 3
    assert summary["no_call_counter_count"] == 13
    assert summary["claim_boundary_check_count"] == 3
    assert summary["summary_request_count"] == 0
    assert summary["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API26_COMPLETION_AUTH_SENTINEL",
        "API26_COMPLETION_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_completion_summary",
        "summary_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_completion_summary_without_summary_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-completion-missing-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_audit = provider_manual_test_post_invocation_audit_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_post_invocation_audit_hash"] = expected_audit[
        "post_invocation_audit_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    summary = data["manual_provider_test_completion_summary"]

    assert summary["status"] == "blocked"
    assert summary["reason"] == "completion_summary_required"
    assert summary["completion_summary_hash"] == ""
    assert summary["post_invocation_audit_hash"] == expected_audit[
        "post_invocation_audit_hash"
    ]
    assert summary["claim_boundary_hash"]
    assert summary["no_call_counters_hash"]
    assert summary["component_count"] == 7
    assert summary["passed_component_count"] == 4
    assert summary["mismatch_count"] == 3
    assert summary["component_hash_count"] == 3
    assert summary["no_call_counter_count"] == 13
    assert summary["claim_boundary_check_count"] == 3
    assert summary["summary_request_count"] == 0
    assert summary["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API26_COMPLETION_AUTH_SENTINEL",
        "API26_COMPLETION_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_completion_summary",
        "summary_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_completion_summary_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-completion-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_audit = provider_manual_test_post_invocation_audit_summary(
        request_payload
    )
    expected_summary = provider_manual_test_completion_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    summary = data["manual_provider_test_completion_summary"]

    assert summary["status"] == "blocked"
    assert summary["reason"] == "completion_summary_execution_closed"
    assert summary["completion_summary_hash"] == expected_summary[
        "completion_summary_hash"
    ]
    assert summary["post_invocation_audit_hash"] == expected_audit[
        "post_invocation_audit_hash"
    ]
    assert summary["claim_boundary_hash"] == expected_summary[
        "claim_boundary_hash"
    ]
    assert summary["no_call_counters_hash"] == expected_summary[
        "no_call_counters_hash"
    ]
    assert summary["component_count"] == 7
    assert summary["passed_component_count"] == 7
    assert summary["mismatch_count"] == 0
    assert summary["component_hash_count"] == 3
    assert summary["no_call_counter_count"] == 13
    assert summary["claim_boundary_check_count"] == 3
    assert summary["summary_request_count"] == 1
    assert summary["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API26_COMPLETION_AUTH_SENTINEL",
        "API26_COMPLETION_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_completion_summary",
        "summary_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_closeout_record_without_expected_summary_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-closeout-missing-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_summary = provider_manual_test_completion_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    closeout = data["manual_provider_test_closeout_record"]

    assert set(closeout) == {
        "status",
        "reason",
        "closeout_record_hash",
        "completion_summary_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "closeout_request_count",
        "execution_permission_count",
    }
    assert closeout["status"] == "blocked"
    assert closeout["reason"] == "expected_completion_summary_hash_required"
    assert closeout["closeout_record_hash"] == ""
    assert closeout["completion_summary_hash"] == expected_summary[
        "completion_summary_hash"
    ]
    assert closeout["claim_boundary_hash"]
    assert closeout["no_call_counters_hash"]
    assert closeout["component_count"] == 7
    assert closeout["passed_component_count"] == 3
    assert closeout["mismatch_count"] == 4
    assert closeout["component_hash_count"] == 3
    assert closeout["no_call_counter_count"] == 13
    assert closeout["claim_boundary_check_count"] == 3
    assert closeout["closeout_request_count"] == 0
    assert closeout["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API27_CLOSEOUT_AUTH_SENTINEL",
        "API27_CLOSEOUT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_closeout_record",
        "closeout_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_closeout_record_without_record_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-closeout-missing-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_summary = provider_manual_test_completion_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_completion_summary_hash"] = expected_summary[
        "completion_summary_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    closeout = data["manual_provider_test_closeout_record"]

    assert closeout["status"] == "blocked"
    assert closeout["reason"] == "closeout_record_required"
    assert closeout["closeout_record_hash"] == ""
    assert closeout["completion_summary_hash"] == expected_summary[
        "completion_summary_hash"
    ]
    assert closeout["claim_boundary_hash"]
    assert closeout["no_call_counters_hash"]
    assert closeout["component_count"] == 7
    assert closeout["passed_component_count"] == 4
    assert closeout["mismatch_count"] == 3
    assert closeout["component_hash_count"] == 3
    assert closeout["no_call_counter_count"] == 13
    assert closeout["claim_boundary_check_count"] == 3
    assert closeout["closeout_request_count"] == 0
    assert closeout["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API27_CLOSEOUT_AUTH_SENTINEL",
        "API27_CLOSEOUT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_closeout_record",
        "closeout_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_closeout_record_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-closeout-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_summary = provider_manual_test_completion_summary(request_payload)
    expected_closeout = provider_manual_test_closeout_record_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    closeout = data["manual_provider_test_closeout_record"]

    assert closeout["status"] == "blocked"
    assert closeout["reason"] == "closeout_record_execution_closed"
    assert closeout["closeout_record_hash"] == expected_closeout[
        "closeout_record_hash"
    ]
    assert closeout["completion_summary_hash"] == expected_summary[
        "completion_summary_hash"
    ]
    assert closeout["claim_boundary_hash"] == expected_closeout[
        "claim_boundary_hash"
    ]
    assert closeout["no_call_counters_hash"] == expected_closeout[
        "no_call_counters_hash"
    ]
    assert closeout["component_count"] == 7
    assert closeout["passed_component_count"] == 7
    assert closeout["mismatch_count"] == 0
    assert closeout["component_hash_count"] == 3
    assert closeout["no_call_counter_count"] == 13
    assert closeout["claim_boundary_check_count"] == 3
    assert closeout["closeout_request_count"] == 1
    assert closeout["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API27_CLOSEOUT_AUTH_SENTINEL",
        "API27_CLOSEOUT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_closeout_record",
        "closeout_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_operator_handback_without_expected_closeout_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-handback-no-expected-closeout",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_closeout = provider_manual_test_closeout_record_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handback = data["manual_provider_test_operator_handback"]

    assert set(handback) == {
        "status",
        "reason",
        "operator_handback_hash",
        "closeout_record_hash",
        "operator_review_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "operator_review_count",
        "handback_request_count",
        "execution_permission_count",
    }
    assert handback["status"] == "blocked"
    assert handback["reason"] == "expected_closeout_record_hash_required"
    assert handback["operator_handback_hash"] == ""
    assert handback["closeout_record_hash"] == expected_closeout[
        "closeout_record_hash"
    ]
    assert handback["operator_review_hash"] == ""
    assert handback["claim_boundary_hash"]
    assert handback["no_call_counters_hash"]
    assert handback["component_count"] == 8
    assert handback["passed_component_count"] == 3
    assert handback["mismatch_count"] == 5
    assert handback["component_hash_count"] == 3
    assert handback["no_call_counter_count"] == 13
    assert handback["claim_boundary_check_count"] == 3
    assert handback["operator_review_count"] == 0
    assert handback["handback_request_count"] == 0
    assert handback["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API28_HANDBACK_AUTH_SENTINEL",
        "API28_HANDBACK_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_operator_handback",
        "handback_requested",
        "API28_OPERATOR_REF_SENTINEL",
        "local-no-call-handback-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_operator_handback_without_handback_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-handback-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_closeout = provider_manual_test_closeout_record_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_closeout_record_hash"] = expected_closeout[
        "closeout_record_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handback = data["manual_provider_test_operator_handback"]

    assert handback["status"] == "blocked"
    assert handback["reason"] == "operator_handback_required"
    assert handback["operator_handback_hash"] == ""
    assert handback["closeout_record_hash"] == expected_closeout[
        "closeout_record_hash"
    ]
    assert handback["operator_review_hash"] == ""
    assert handback["claim_boundary_hash"]
    assert handback["no_call_counters_hash"]
    assert handback["component_count"] == 8
    assert handback["passed_component_count"] == 4
    assert handback["mismatch_count"] == 4
    assert handback["component_hash_count"] == 3
    assert handback["no_call_counter_count"] == 13
    assert handback["claim_boundary_check_count"] == 3
    assert handback["operator_review_count"] == 0
    assert handback["handback_request_count"] == 0
    assert handback["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API28_HANDBACK_AUTH_SENTINEL",
        "API28_HANDBACK_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_operator_handback",
        "handback_requested",
        "API28_OPERATOR_REF_SENTINEL",
        "local-no-call-handback-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_operator_handback_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-handback-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_closeout = provider_manual_test_closeout_record_summary(request_payload)
    expected_handback = provider_manual_test_operator_handback_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handback = data["manual_provider_test_operator_handback"]

    assert handback["status"] == "blocked"
    assert handback["reason"] == "operator_handback_execution_closed"
    assert handback["operator_handback_hash"] == expected_handback[
        "operator_handback_hash"
    ]
    assert handback["closeout_record_hash"] == expected_closeout[
        "closeout_record_hash"
    ]
    assert handback["operator_review_hash"] == expected_handback[
        "operator_review_hash"
    ]
    assert handback["operator_review_hash"]
    assert handback["claim_boundary_hash"] == expected_handback[
        "claim_boundary_hash"
    ]
    assert handback["no_call_counters_hash"] == expected_handback[
        "no_call_counters_hash"
    ]
    assert handback["component_count"] == 8
    assert handback["passed_component_count"] == 8
    assert handback["mismatch_count"] == 0
    assert handback["component_hash_count"] == 4
    assert handback["no_call_counter_count"] == 13
    assert handback["claim_boundary_check_count"] == 3
    assert handback["operator_review_count"] == 1
    assert handback["handback_request_count"] == 1
    assert handback["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API28_HANDBACK_AUTH_SENTINEL",
        "API28_HANDBACK_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_operator_handback",
        "handback_requested",
        "API28_OPERATOR_REF_SENTINEL",
        "local-no-call-handback-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_operator_decision_packet_without_expected_handback_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-decision-no-expected-handback",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_handback = provider_manual_test_operator_handback_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision_packet = data["manual_provider_test_operator_decision_packet"]

    assert set(decision_packet) == {
        "status",
        "reason",
        "operator_decision_packet_hash",
        "operator_handback_hash",
        "operator_decision_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "operator_decision_count",
        "decision_packet_request_count",
        "execution_permission_count",
    }
    assert decision_packet["status"] == "blocked"
    assert decision_packet["reason"] == "expected_operator_handback_hash_required"
    assert decision_packet["operator_decision_packet_hash"] == ""
    assert decision_packet["operator_handback_hash"] == expected_handback[
        "operator_handback_hash"
    ]
    assert decision_packet["operator_decision_hash"] == ""
    assert decision_packet["claim_boundary_hash"]
    assert decision_packet["no_call_counters_hash"]
    assert decision_packet["component_count"] == 8
    assert decision_packet["passed_component_count"] == 3
    assert decision_packet["mismatch_count"] == 5
    assert decision_packet["component_hash_count"] == 3
    assert decision_packet["no_call_counter_count"] == 13
    assert decision_packet["claim_boundary_check_count"] == 3
    assert decision_packet["operator_decision_count"] == 0
    assert decision_packet["decision_packet_request_count"] == 0
    assert decision_packet["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API29_DECISION_AUTH_SENTINEL",
        "API29_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_operator_decision_packet",
        "packet_requested",
        "API29_OPERATOR_REF_SENTINEL",
        "local-no-call-decision-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_operator_decision_packet_without_packet_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-decision-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_handback = provider_manual_test_operator_handback_summary(request_payload)
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_operator_handback_hash"] = expected_handback[
        "operator_handback_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision_packet = data["manual_provider_test_operator_decision_packet"]

    assert decision_packet["status"] == "blocked"
    assert decision_packet["reason"] == "operator_decision_packet_required"
    assert decision_packet["operator_decision_packet_hash"] == ""
    assert decision_packet["operator_handback_hash"] == expected_handback[
        "operator_handback_hash"
    ]
    assert decision_packet["operator_decision_hash"] == ""
    assert decision_packet["claim_boundary_hash"]
    assert decision_packet["no_call_counters_hash"]
    assert decision_packet["component_count"] == 8
    assert decision_packet["passed_component_count"] == 4
    assert decision_packet["mismatch_count"] == 4
    assert decision_packet["component_hash_count"] == 3
    assert decision_packet["no_call_counter_count"] == 13
    assert decision_packet["claim_boundary_check_count"] == 3
    assert decision_packet["operator_decision_count"] == 0
    assert decision_packet["decision_packet_request_count"] == 0
    assert decision_packet["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API29_DECISION_AUTH_SENTINEL",
        "API29_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_operator_decision_packet",
        "packet_requested",
        "API29_OPERATOR_REF_SENTINEL",
        "local-no-call-decision-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_operator_decision_packet_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-decision-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_handback = provider_manual_test_operator_handback_summary(request_payload)
    expected_decision_packet = provider_manual_test_operator_decision_packet_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision_packet = data["manual_provider_test_operator_decision_packet"]

    assert decision_packet["status"] == "blocked"
    assert decision_packet["reason"] == "operator_decision_packet_execution_closed"
    assert decision_packet["operator_decision_packet_hash"] == (
        expected_decision_packet["operator_decision_packet_hash"]
    )
    assert decision_packet["operator_handback_hash"] == expected_handback[
        "operator_handback_hash"
    ]
    assert decision_packet["operator_decision_hash"] == expected_decision_packet[
        "operator_decision_hash"
    ]
    assert decision_packet["operator_decision_hash"]
    assert decision_packet["claim_boundary_hash"] == expected_decision_packet[
        "claim_boundary_hash"
    ]
    assert decision_packet["no_call_counters_hash"] == expected_decision_packet[
        "no_call_counters_hash"
    ]
    assert decision_packet["component_count"] == 8
    assert decision_packet["passed_component_count"] == 8
    assert decision_packet["mismatch_count"] == 0
    assert decision_packet["component_hash_count"] == 4
    assert decision_packet["no_call_counter_count"] == 13
    assert decision_packet["claim_boundary_check_count"] == 3
    assert decision_packet["operator_decision_count"] == 1
    assert decision_packet["decision_packet_request_count"] == 1
    assert decision_packet["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API29_DECISION_AUTH_SENTINEL",
        "API29_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_operator_decision_packet",
        "packet_requested",
        "API29_OPERATOR_REF_SENTINEL",
        "local-no-call-decision-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_operator_release_attestation_without_expected_decision_packet_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-attestation-no-expected-decision",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_decision_packet = provider_manual_test_operator_decision_packet_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data["manual_provider_test_operator_release_attestation"]

    assert set(attestation) == {
        "status",
        "reason",
        "operator_release_attestation_hash",
        "operator_decision_packet_hash",
        "operator_attestation_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "operator_attestation_count",
        "attestation_request_count",
        "execution_permission_count",
    }
    assert attestation["status"] == "blocked"
    assert (
        attestation["reason"]
        == "expected_operator_decision_packet_hash_required"
    )
    assert attestation["operator_release_attestation_hash"] == ""
    assert attestation["operator_decision_packet_hash"] == expected_decision_packet[
        "operator_decision_packet_hash"
    ]
    assert attestation["operator_attestation_hash"] == ""
    assert attestation["claim_boundary_hash"]
    assert attestation["no_call_counters_hash"]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 3
    assert attestation["mismatch_count"] == 5
    assert attestation["component_hash_count"] == 3
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["operator_attestation_count"] == 0
    assert attestation["attestation_request_count"] == 0
    assert attestation["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API30_ATTESTATION_AUTH_SENTINEL",
        "API30_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_operator_release_attestation",
        "attestation_requested",
        "API30_OPERATOR_REF_SENTINEL",
        "local-no-call-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_operator_release_attestation_without_attestation_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-attestation-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_decision_packet = provider_manual_test_operator_decision_packet_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_operator_decision_packet_hash"] = (
        expected_decision_packet["operator_decision_packet_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data["manual_provider_test_operator_release_attestation"]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == "operator_release_attestation_required"
    assert attestation["operator_release_attestation_hash"] == ""
    assert attestation["operator_decision_packet_hash"] == expected_decision_packet[
        "operator_decision_packet_hash"
    ]
    assert attestation["operator_attestation_hash"] == ""
    assert attestation["claim_boundary_hash"]
    assert attestation["no_call_counters_hash"]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 4
    assert attestation["mismatch_count"] == 4
    assert attestation["component_hash_count"] == 3
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["operator_attestation_count"] == 0
    assert attestation["attestation_request_count"] == 0
    assert attestation["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API30_ATTESTATION_AUTH_SENTINEL",
        "API30_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_operator_release_attestation",
        "attestation_requested",
        "API30_OPERATOR_REF_SENTINEL",
        "local-no-call-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_operator_release_attestation_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-attestation-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_decision_packet = provider_manual_test_operator_decision_packet_summary(
        request_payload
    )
    expected_attestation = provider_manual_test_operator_release_attestation_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data["manual_provider_test_operator_release_attestation"]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == "operator_release_attestation_execution_closed"
    assert attestation["operator_release_attestation_hash"] == (
        expected_attestation["operator_release_attestation_hash"]
    )
    assert attestation["operator_decision_packet_hash"] == (
        expected_decision_packet["operator_decision_packet_hash"]
    )
    assert attestation["operator_attestation_hash"] == expected_attestation[
        "operator_attestation_hash"
    ]
    assert attestation["operator_attestation_hash"]
    assert attestation["claim_boundary_hash"] == expected_attestation[
        "claim_boundary_hash"
    ]
    assert attestation["no_call_counters_hash"] == expected_attestation[
        "no_call_counters_hash"
    ]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 8
    assert attestation["mismatch_count"] == 0
    assert attestation["component_hash_count"] == 4
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["operator_attestation_count"] == 1
    assert attestation["attestation_request_count"] == 1
    assert attestation["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API30_ATTESTATION_AUTH_SENTINEL",
        "API30_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_operator_release_attestation",
        "attestation_requested",
        "API30_OPERATOR_REF_SENTINEL",
        "local-no-call-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_release_authorization_seal_without_expected_attestation_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-seal-no-expected-attestation",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_attestation = provider_manual_test_operator_release_attestation_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data["manual_provider_test_release_seal"]

    assert set(seal) == {
        "status",
        "reason",
        "release_seal_hash",
        "operator_release_attestation_hash",
        "seal_material_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "seal_material_count",
        "seal_request_count",
        "execution_permission_count",
    }
    assert seal["status"] == "blocked"
    assert (
        seal["reason"]
        == "expected_operator_release_attestation_hash_required"
    )
    assert seal["release_seal_hash"] == ""
    assert seal["operator_release_attestation_hash"] == expected_attestation[
        "operator_release_attestation_hash"
    ]
    assert seal["seal_material_hash"] == ""
    assert seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 3
    assert seal["mismatch_count"] == 5
    assert seal["component_hash_count"] == 3
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 0
    assert seal["seal_request_count"] == 0
    assert seal["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API31_SEAL_AUTH_SENTINEL",
        "API31_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_release_authorization_seal",
        "seal_requested",
        "API31_OPERATOR_REF_SENTINEL",
        "local-no-call-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_release_authorization_seal_without_seal_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-seal-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_attestation = provider_manual_test_operator_release_attestation_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_operator_release_attestation_hash"] = (
        expected_attestation["operator_release_attestation_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data["manual_provider_test_release_seal"]

    assert seal["status"] == "blocked"
    assert seal["reason"] == "release_authorization_seal_required"
    assert seal["release_seal_hash"] == ""
    assert seal["operator_release_attestation_hash"] == expected_attestation[
        "operator_release_attestation_hash"
    ]
    assert seal["seal_material_hash"] == ""
    assert seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 4
    assert seal["mismatch_count"] == 4
    assert seal["component_hash_count"] == 3
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 0
    assert seal["seal_request_count"] == 0
    assert seal["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API31_SEAL_AUTH_SENTINEL",
        "API31_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_release_authorization_seal",
        "seal_requested",
        "API31_OPERATOR_REF_SENTINEL",
        "local-no-call-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_release_authorization_seal_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-seal-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_attestation = provider_manual_test_operator_release_attestation_summary(
        request_payload
    )
    expected_seal = provider_manual_test_release_authorization_seal_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data["manual_provider_test_release_seal"]

    assert seal["status"] == "blocked"
    assert seal["reason"] == "release_authorization_seal_execution_closed"
    assert seal["release_seal_hash"] == (
        expected_seal["release_seal_hash"]
    )
    assert seal["operator_release_attestation_hash"] == (
        expected_attestation["operator_release_attestation_hash"]
    )
    assert seal["seal_material_hash"] == expected_seal["seal_material_hash"]
    assert seal["seal_material_hash"]
    assert seal["claim_boundary_hash"] == expected_seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"] == expected_seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 8
    assert seal["mismatch_count"] == 0
    assert seal["component_hash_count"] == 4
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 1
    assert seal["seal_request_count"] == 1
    assert seal["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API31_SEAL_AUTH_SENTINEL",
        "API31_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_release_authorization_seal",
        "seal_requested",
        "API31_OPERATOR_REF_SENTINEL",
        "local-no-call-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_without_expected_release_seal_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-no-expected-seal",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_seal = provider_manual_test_release_authorization_seal_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    capsule = data["manual_provider_test_execution_capsule"]

    assert set(capsule) == {
        "status",
        "reason",
        "execution_capsule_hash",
        "release_seal_hash",
        "final_authz_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "final_authz_count",
        "capsule_request_count",
        "execution_permission_count",
    }
    assert capsule["status"] == "blocked"
    assert capsule["reason"] == "expected_release_seal_hash_required"
    assert capsule["execution_capsule_hash"] == ""
    assert capsule["release_seal_hash"] == expected_seal["release_seal_hash"]
    assert capsule["final_authz_hash"] == ""
    assert capsule["claim_boundary_hash"]
    assert capsule["no_call_counters_hash"]
    assert capsule["component_count"] == 8
    assert capsule["passed_component_count"] == 3
    assert capsule["mismatch_count"] == 5
    assert capsule["component_hash_count"] == 3
    assert capsule["no_call_counter_count"] == 13
    assert capsule["claim_boundary_check_count"] == 3
    assert capsule["final_authz_count"] == 0
    assert capsule["capsule_request_count"] == 0
    assert capsule["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API32_CAPSULE_AUTH_SENTINEL",
        "API32_CAPSULE_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_authorization_capsule",
        "capsule_requested",
        "final_authorization",
        "API32_OPERATOR_REF_SENTINEL",
        "local-no-call-execution-capsule-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_without_capsule_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_seal = provider_manual_test_release_authorization_seal_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_release_seal_hash"] = expected_seal[
        "release_seal_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    capsule = data["manual_provider_test_execution_capsule"]

    assert capsule["status"] == "blocked"
    assert capsule["reason"] == "execution_authorization_capsule_required"
    assert capsule["execution_capsule_hash"] == ""
    assert capsule["release_seal_hash"] == expected_seal["release_seal_hash"]
    assert capsule["final_authz_hash"] == ""
    assert capsule["claim_boundary_hash"]
    assert capsule["no_call_counters_hash"]
    assert capsule["component_count"] == 8
    assert capsule["passed_component_count"] == 4
    assert capsule["mismatch_count"] == 4
    assert capsule["component_hash_count"] == 3
    assert capsule["no_call_counter_count"] == 13
    assert capsule["claim_boundary_check_count"] == 3
    assert capsule["final_authz_count"] == 0
    assert capsule["capsule_request_count"] == 0
    assert capsule["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API32_CAPSULE_AUTH_SENTINEL",
        "API32_CAPSULE_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_authorization_capsule",
        "capsule_requested",
        "final_authorization",
        "API32_OPERATOR_REF_SENTINEL",
        "local-no-call-execution-capsule-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_seal = provider_manual_test_release_authorization_seal_summary(
        request_payload
    )
    expected_capsule = provider_manual_test_execution_authorization_capsule_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    capsule = data["manual_provider_test_execution_capsule"]

    assert capsule["status"] == "blocked"
    assert capsule["reason"] == "execution_authorization_capsule_execution_closed"
    assert capsule["execution_capsule_hash"] == (
        expected_capsule["execution_capsule_hash"]
    )
    assert capsule["release_seal_hash"] == expected_seal["release_seal_hash"]
    assert capsule["final_authz_hash"] == expected_capsule["final_authz_hash"]
    assert capsule["final_authz_hash"]
    assert capsule["claim_boundary_hash"] == expected_capsule["claim_boundary_hash"]
    assert capsule["no_call_counters_hash"] == expected_capsule[
        "no_call_counters_hash"
    ]
    assert capsule["component_count"] == 8
    assert capsule["passed_component_count"] == 8
    assert capsule["mismatch_count"] == 0
    assert capsule["component_hash_count"] == 4
    assert capsule["no_call_counter_count"] == 13
    assert capsule["claim_boundary_check_count"] == 3
    assert capsule["final_authz_count"] == 1
    assert capsule["capsule_request_count"] == 1
    assert capsule["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API32_CAPSULE_AUTH_SENTINEL",
        "API32_CAPSULE_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_authorization_capsule",
        "capsule_requested",
        "final_authorization",
        "API32_OPERATOR_REF_SENTINEL",
        "local-no-call-execution-capsule-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_export_without_expected_capsule_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-export-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_capsule = provider_manual_test_execution_authorization_capsule_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data["manual_provider_test_execution_capsule_export"]
    read_model = data["manual_provider_test_execution_capsule_export_read_model"]

    assert set(export) == {
        "status",
        "reason",
        "execution_capsule_export_hash",
        "execution_capsule_hash",
        "export_metadata_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "export_count",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "export_metadata_count",
        "execution_permission_count",
    }
    assert export["status"] == "blocked"
    assert export["reason"] == "expected_execution_capsule_hash_required"
    assert export["execution_capsule_export_hash"] == ""
    assert export["execution_capsule_hash"] == expected_capsule[
        "execution_capsule_hash"
    ]
    assert export["export_metadata_hash"] == ""
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["export_count"] == 0
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 3
    assert export["mismatch_count"] == 5
    assert export["component_hash_count"] == 3
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 0
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "blocked"
    assert read_model["reason"] == "execution_capsule_export_not_available"
    assert read_model["counts"]["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API33_EXPORT_AUTH_SENTINEL",
        "API33_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_export",
        "export_requested",
        "API33_OPERATOR_REF_SENTINEL",
        "local-no-call-capsule-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_export_without_export_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-export-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_capsule = provider_manual_test_execution_authorization_capsule_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_hash"] = expected_capsule[
        "execution_capsule_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data["manual_provider_test_execution_capsule_export"]
    read_model = data["manual_provider_test_execution_capsule_export_read_model"]

    assert export["status"] == "blocked"
    assert export["reason"] == "execution_capsule_export_required"
    assert export["execution_capsule_export_hash"] == ""
    assert export["execution_capsule_hash"] == expected_capsule[
        "execution_capsule_hash"
    ]
    assert export["export_metadata_hash"] == ""
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["export_count"] == 0
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 4
    assert export["mismatch_count"] == 4
    assert export["component_hash_count"] == 3
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 0
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "blocked"
    assert read_model["reason"] == "execution_capsule_export_not_available"
    assert read_model["counts"]["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API33_EXPORT_AUTH_SENTINEL",
        "API33_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_export",
        "export_requested",
        "API33_OPERATOR_REF_SENTINEL",
        "local-no-call-capsule-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_export_read_model_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-export-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_capsule = provider_manual_test_execution_authorization_capsule_summary(
        request_payload
    )
    expected_export = provider_manual_test_execution_capsule_export_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data["manual_provider_test_execution_capsule_export"]
    read_model = data["manual_provider_test_execution_capsule_export_read_model"]

    assert export["status"] == "blocked"
    assert export["reason"] == "execution_capsule_export_execution_closed"
    assert export["execution_capsule_export_hash"] == (
        expected_export["execution_capsule_export_hash"]
    )
    assert export["execution_capsule_hash"] == expected_capsule[
        "execution_capsule_hash"
    ]
    assert export["export_metadata_hash"] == expected_export[
        "export_metadata_hash"
    ]
    assert export["export_metadata_hash"]
    assert export["claim_boundary_hash"] == expected_export["claim_boundary_hash"]
    assert export["no_call_counters_hash"] == expected_export[
        "no_call_counters_hash"
    ]
    assert export["export_count"] == 1
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 8
    assert export["mismatch_count"] == 0
    assert export["component_hash_count"] == 4
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 1
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "available"
    assert (
        read_model["reason"]
        == "execution_capsule_export_read_model_available"
    )
    assert read_model["latest_execution_capsule_export_hash"] == (
        export["execution_capsule_export_hash"]
    )
    assert read_model["counts"]["execution_capsule_export_count"] == 1
    assert read_model["counts"]["component_count"] == 8
    assert read_model["counts"]["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API33_EXPORT_AUTH_SENTINEL",
        "API33_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_export",
        "export_requested",
        "API33_OPERATOR_REF_SENTINEL",
        "local-no-call-capsule-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_handoff_without_expected_export_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-handoff-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_export = provider_manual_test_execution_capsule_export_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_export_hash", None)

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    packet = data["manual_provider_test_execution_capsule_handoff_packet"]

    assert set(packet) == {
        "status",
        "reason",
        "execution_capsule_handoff_packet_hash",
        "execution_capsule_export_hash",
        "execution_capsule_export_read_model_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "packet_count",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "export_read_model_count",
        "handoff_request_count",
        "execution_permission_count",
    }
    assert packet["status"] == "blocked"
    assert packet["reason"] == "expected_execution_capsule_export_hash_required"
    assert packet["execution_capsule_handoff_packet_hash"] == ""
    assert packet["execution_capsule_export_hash"] == expected_export[
        "execution_capsule_export_hash"
    ]
    assert packet["execution_capsule_export_read_model_hash"] == expected_export[
        "execution_capsule_export_hash"
    ]
    assert packet["claim_boundary_hash"]
    assert packet["no_call_counters_hash"]
    assert packet["packet_count"] == 0
    assert packet["component_count"] == 8
    assert packet["passed_component_count"] == 7
    assert packet["mismatch_count"] == 1
    assert packet["component_hash_count"] == 4
    assert packet["no_call_counter_count"] == 13
    assert packet["claim_boundary_check_count"] == 3
    assert packet["export_read_model_count"] == 1
    assert packet["handoff_request_count"] == 1
    assert packet["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API34_HANDOFF_MATERIAL_SENTINEL",
        "API34_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_handoff_without_packet_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-handoff-no-packet",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_export = provider_manual_test_execution_capsule_export_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_export_hash"] = expected_export[
        "execution_capsule_export_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    packet = data["manual_provider_test_execution_capsule_handoff_packet"]

    assert packet["status"] == "blocked"
    assert packet["reason"] == "execution_capsule_handoff_packet_required"
    assert packet["execution_capsule_handoff_packet_hash"] == ""
    assert packet["execution_capsule_export_hash"] == expected_export[
        "execution_capsule_export_hash"
    ]
    assert packet["execution_capsule_export_read_model_hash"] == expected_export[
        "execution_capsule_export_hash"
    ]
    assert packet["claim_boundary_hash"]
    assert packet["no_call_counters_hash"]
    assert packet["packet_count"] == 0
    assert packet["component_count"] == 8
    assert packet["passed_component_count"] == 5
    assert packet["mismatch_count"] == 3
    assert packet["component_hash_count"] == 4
    assert packet["no_call_counter_count"] == 13
    assert packet["claim_boundary_check_count"] == 3
    assert packet["export_read_model_count"] == 1
    assert packet["handoff_request_count"] == 0
    assert packet["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API34_HANDOFF_MATERIAL_SENTINEL",
        "API34_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_handoff_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-handoff-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_packet = provider_manual_test_execution_capsule_handoff_packet_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    packet = data["manual_provider_test_execution_capsule_handoff_packet"]

    assert packet["status"] == "blocked"
    assert packet["reason"] == "execution_capsule_handoff_packet_execution_closed"
    assert packet["execution_capsule_handoff_packet_hash"] == expected_packet[
        "execution_capsule_handoff_packet_hash"
    ]
    assert packet["execution_capsule_export_hash"] == expected_packet[
        "execution_capsule_export_hash"
    ]
    assert packet["execution_capsule_export_read_model_hash"] == expected_packet[
        "execution_capsule_export_read_model_hash"
    ]
    assert packet["claim_boundary_hash"] == expected_packet["claim_boundary_hash"]
    assert packet["no_call_counters_hash"] == expected_packet[
        "no_call_counters_hash"
    ]
    assert packet["packet_count"] == 1
    assert packet["component_count"] == 8
    assert packet["passed_component_count"] == 8
    assert packet["mismatch_count"] == 0
    assert packet["component_hash_count"] == 4
    assert packet["no_call_counter_count"] == 13
    assert packet["claim_boundary_check_count"] == 3
    assert packet["export_read_model_count"] == 1
    assert packet["handoff_request_count"] == 1
    assert packet["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API34_HANDOFF_MATERIAL_SENTINEL",
        "API34_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_operator_review_without_expected_handoff_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-review-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_capsule_handoff = (
        provider_manual_test_execution_capsule_handoff_packet_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_handoff_packet_hash", None)

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data["manual_provider_test_execution_capsule_operator_review"]

    assert set(review) == {
        "status",
        "reason",
        "execution_capsule_operator_review_hash",
        "execution_capsule_handoff_packet_hash",
        "operator_review_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "operator_review_count",
        "review_request_count",
        "execution_permission_count",
    }
    assert review["status"] == "blocked"
    assert (
        review["reason"]
        == "expected_execution_capsule_handoff_packet_hash_required"
    )
    assert review["execution_capsule_operator_review_hash"] == ""
    assert review["execution_capsule_handoff_packet_hash"] == (
        expected_capsule_handoff["execution_capsule_handoff_packet_hash"]
    )
    assert review["operator_review_hash"]
    assert review["claim_boundary_hash"]
    assert review["no_call_counters_hash"]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 7
    assert review["mismatch_count"] == 1
    assert review["component_hash_count"] == 4
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 1
    assert review["review_request_count"] == 1
    assert review["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API35_REVIEW_AUTH_SENTINEL",
        "API35_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API35_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_operator_review",
        "review_requested",
        "local-no-call-capsule-operator-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_operator_review_without_review_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-review-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_capsule_handoff = (
        provider_manual_test_execution_capsule_handoff_packet_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_handoff_packet_hash"] = (
        expected_capsule_handoff["execution_capsule_handoff_packet_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data["manual_provider_test_execution_capsule_operator_review"]

    assert review["status"] == "blocked"
    assert review["reason"] == "execution_capsule_operator_review_required"
    assert review["execution_capsule_operator_review_hash"] == ""
    assert review["execution_capsule_handoff_packet_hash"] == (
        expected_capsule_handoff["execution_capsule_handoff_packet_hash"]
    )
    assert review["operator_review_hash"] == ""
    assert review["claim_boundary_hash"]
    assert review["no_call_counters_hash"]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 4
    assert review["mismatch_count"] == 4
    assert review["component_hash_count"] == 3
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 0
    assert review["review_request_count"] == 0
    assert review["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API35_REVIEW_AUTH_SENTINEL",
        "API35_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API35_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_operator_review",
        "review_requested",
        "local-no-call-capsule-operator-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_operator_review_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-review-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_review = provider_manual_test_execution_capsule_operator_review_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data["manual_provider_test_execution_capsule_operator_review"]

    assert review["status"] == "blocked"
    assert review["reason"] == "execution_capsule_operator_review_execution_closed"
    assert review["execution_capsule_operator_review_hash"] == expected_review[
        "execution_capsule_operator_review_hash"
    ]
    assert review["execution_capsule_handoff_packet_hash"] == expected_review[
        "execution_capsule_handoff_packet_hash"
    ]
    assert review["operator_review_hash"] == expected_review["operator_review_hash"]
    assert review["operator_review_hash"]
    assert review["claim_boundary_hash"] == expected_review["claim_boundary_hash"]
    assert review["no_call_counters_hash"] == expected_review[
        "no_call_counters_hash"
    ]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 8
    assert review["mismatch_count"] == 0
    assert review["component_hash_count"] == 4
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 1
    assert review["review_request_count"] == 1
    assert review["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API35_REVIEW_AUTH_SENTINEL",
        "API35_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API35_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_operator_review",
        "review_requested",
        "local-no-call-capsule-operator-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_operator_decision_without_expected_review_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-decision-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_review = provider_manual_test_execution_capsule_operator_review_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_operator_review_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data["manual_provider_test_execution_capsule_operator_decision"]

    assert set(decision) == {
        "status",
        "reason",
        "execution_capsule_operator_decision_hash",
        "execution_capsule_operator_review_hash",
        "operator_decision_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "operator_decision_count",
        "decision_request_count",
        "execution_permission_count",
    }
    assert decision["status"] == "blocked"
    assert (
        decision["reason"]
        == "expected_execution_capsule_operator_review_hash_required"
    )
    assert decision["execution_capsule_operator_decision_hash"] == ""
    assert decision["execution_capsule_operator_review_hash"] == expected_review[
        "execution_capsule_operator_review_hash"
    ]
    assert decision["operator_decision_hash"]
    assert decision["claim_boundary_hash"]
    assert decision["no_call_counters_hash"]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 7
    assert decision["mismatch_count"] == 1
    assert decision["component_hash_count"] == 4
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 1
    assert decision["decision_request_count"] == 1
    assert decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API36_DECISION_AUTH_SENTINEL",
        "API36_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API36_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_operator_decision",
        "decision_requested",
        "local-no-call-capsule-operator-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_operator_decision_without_decision_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-decision-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_review = provider_manual_test_execution_capsule_operator_review_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_operator_review_hash"] = (
        expected_review["execution_capsule_operator_review_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data["manual_provider_test_execution_capsule_operator_decision"]

    assert decision["status"] == "blocked"
    assert decision["reason"] == "execution_capsule_operator_decision_required"
    assert decision["execution_capsule_operator_decision_hash"] == ""
    assert decision["execution_capsule_operator_review_hash"] == expected_review[
        "execution_capsule_operator_review_hash"
    ]
    assert decision["operator_decision_hash"] == ""
    assert decision["claim_boundary_hash"]
    assert decision["no_call_counters_hash"]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 4
    assert decision["mismatch_count"] == 4
    assert decision["component_hash_count"] == 3
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 0
    assert decision["decision_request_count"] == 0
    assert decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API36_DECISION_AUTH_SENTINEL",
        "API36_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API36_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_operator_decision",
        "decision_requested",
        "local-no-call-capsule-operator-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_operator_decision_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-decision-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_decision = provider_manual_test_execution_capsule_operator_decision_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data["manual_provider_test_execution_capsule_operator_decision"]

    assert decision["status"] == "blocked"
    assert decision["reason"] == "execution_capsule_operator_decision_execution_closed"
    assert decision["execution_capsule_operator_decision_hash"] == expected_decision[
        "execution_capsule_operator_decision_hash"
    ]
    assert decision["execution_capsule_operator_review_hash"] == expected_decision[
        "execution_capsule_operator_review_hash"
    ]
    assert decision["operator_decision_hash"] == expected_decision[
        "operator_decision_hash"
    ]
    assert decision["operator_decision_hash"]
    assert decision["claim_boundary_hash"] == expected_decision["claim_boundary_hash"]
    assert decision["no_call_counters_hash"] == expected_decision[
        "no_call_counters_hash"
    ]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 8
    assert decision["mismatch_count"] == 0
    assert decision["component_hash_count"] == 4
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 1
    assert decision["decision_request_count"] == 1
    assert decision["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API36_DECISION_AUTH_SENTINEL",
        "API36_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API36_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_operator_decision",
        "decision_requested",
        "local-no-call-capsule-operator-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_release_attestation_without_expected_decision_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-attestation-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_decision = provider_manual_test_execution_capsule_operator_decision_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_operator_decision_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data["manual_provider_test_execution_capsule_release_attestation"]

    assert set(attestation) == {
        "status",
        "reason",
        "execution_capsule_release_attestation_hash",
        "execution_capsule_operator_decision_hash",
        "release_attestation_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "release_attestation_count",
        "attestation_request_count",
        "execution_permission_count",
    }
    assert attestation["status"] == "blocked"
    assert (
        attestation["reason"]
        == "expected_execution_capsule_operator_decision_hash_required"
    )
    assert attestation["execution_capsule_release_attestation_hash"] == ""
    assert attestation["execution_capsule_operator_decision_hash"] == (
        expected_decision["execution_capsule_operator_decision_hash"]
    )
    assert attestation["release_attestation_hash"]
    assert attestation["claim_boundary_hash"]
    assert attestation["no_call_counters_hash"]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 7
    assert attestation["mismatch_count"] == 1
    assert attestation["component_hash_count"] == 4
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 1
    assert attestation["attestation_request_count"] == 1
    assert attestation["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API37_ATTESTATION_AUTH_SENTINEL",
        "API37_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API37_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_release_attestation_without_attestation_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-attestation-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_decision = provider_manual_test_execution_capsule_operator_decision_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_operator_decision_hash"] = (
        expected_decision["execution_capsule_operator_decision_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data["manual_provider_test_execution_capsule_release_attestation"]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == "execution_capsule_release_attestation_required"
    assert attestation["execution_capsule_release_attestation_hash"] == ""
    assert attestation["execution_capsule_operator_decision_hash"] == (
        expected_decision["execution_capsule_operator_decision_hash"]
    )
    assert attestation["release_attestation_hash"] == ""
    assert attestation["claim_boundary_hash"]
    assert attestation["no_call_counters_hash"]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 4
    assert attestation["mismatch_count"] == 4
    assert attestation["component_hash_count"] == 3
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 0
    assert attestation["attestation_request_count"] == 0
    assert attestation["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API37_ATTESTATION_AUTH_SENTINEL",
        "API37_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API37_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_release_attestation_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-attestation-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_attestation = (
        provider_manual_test_execution_capsule_release_attestation_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data["manual_provider_test_execution_capsule_release_attestation"]

    assert attestation["status"] == "blocked"
    assert (
        attestation["reason"]
        == "execution_capsule_release_attestation_execution_closed"
    )
    assert attestation["execution_capsule_release_attestation_hash"] == (
        expected_attestation["execution_capsule_release_attestation_hash"]
    )
    assert attestation["execution_capsule_operator_decision_hash"] == (
        expected_attestation["execution_capsule_operator_decision_hash"]
    )
    assert attestation["release_attestation_hash"] == expected_attestation[
        "release_attestation_hash"
    ]
    assert attestation["release_attestation_hash"]
    assert attestation["claim_boundary_hash"] == expected_attestation[
        "claim_boundary_hash"
    ]
    assert attestation["no_call_counters_hash"] == expected_attestation[
        "no_call_counters_hash"
    ]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 8
    assert attestation["mismatch_count"] == 0
    assert attestation["component_hash_count"] == 4
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 1
    assert attestation["attestation_request_count"] == 1
    assert attestation["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API37_ATTESTATION_AUTH_SENTINEL",
        "API37_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API37_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_release_seal_without_expected_attestation_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-release-seal-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_attestation = (
        provider_manual_test_execution_capsule_release_attestation_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_release_attestation_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data["manual_provider_test_execution_capsule_release_seal"]

    assert set(seal) == {
        "status",
        "reason",
        "execution_capsule_release_seal_hash",
        "execution_capsule_release_attestation_hash",
        "seal_material_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "seal_material_count",
        "seal_request_count",
        "execution_permission_count",
    }
    assert seal["status"] == "blocked"
    assert (
        seal["reason"]
        == "expected_execution_capsule_release_attestation_hash_required"
    )
    assert seal["execution_capsule_release_seal_hash"] == ""
    assert seal["execution_capsule_release_attestation_hash"] == (
        expected_attestation["execution_capsule_release_attestation_hash"]
    )
    assert seal["seal_material_hash"]
    assert seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 7
    assert seal["mismatch_count"] == 1
    assert seal["component_hash_count"] == 4
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 1
    assert seal["seal_request_count"] == 1
    assert seal["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API38_SEAL_AUTH_SENTINEL",
        "API38_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API38_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_release_seal",
        "seal_requested",
        "local-no-call-capsule-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_release_seal_without_seal_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-release-seal-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_attestation = (
        provider_manual_test_execution_capsule_release_attestation_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_release_attestation_hash"] = (
        expected_attestation["execution_capsule_release_attestation_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data["manual_provider_test_execution_capsule_release_seal"]

    assert seal["status"] == "blocked"
    assert seal["reason"] == "execution_capsule_release_seal_required"
    assert seal["execution_capsule_release_seal_hash"] == ""
    assert seal["execution_capsule_release_attestation_hash"] == (
        expected_attestation["execution_capsule_release_attestation_hash"]
    )
    assert seal["seal_material_hash"] == ""
    assert seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 4
    assert seal["mismatch_count"] == 4
    assert seal["component_hash_count"] == 3
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 0
    assert seal["seal_request_count"] == 0
    assert seal["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API38_SEAL_AUTH_SENTINEL",
        "API38_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API38_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_release_seal",
        "seal_requested",
        "local-no-call-capsule-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_release_seal_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-release-seal-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_seal = provider_manual_test_execution_capsule_release_seal_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data["manual_provider_test_execution_capsule_release_seal"]

    assert seal["status"] == "blocked"
    assert seal["reason"] == "execution_capsule_release_seal_execution_closed"
    assert seal["execution_capsule_release_seal_hash"] == expected_seal[
        "execution_capsule_release_seal_hash"
    ]
    assert seal["execution_capsule_release_attestation_hash"] == expected_seal[
        "execution_capsule_release_attestation_hash"
    ]
    assert seal["seal_material_hash"] == expected_seal["seal_material_hash"]
    assert seal["seal_material_hash"]
    assert seal["claim_boundary_hash"] == expected_seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"] == expected_seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 8
    assert seal["mismatch_count"] == 0
    assert seal["component_hash_count"] == 4
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 1
    assert seal["seal_request_count"] == 1
    assert seal["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API38_SEAL_AUTH_SENTINEL",
        "API38_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API38_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_release_seal",
        "seal_requested",
        "local-no-call-capsule-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_final_authorization_without_expected_release_seal_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-final-authorization-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_release_seal = (
        provider_manual_test_execution_capsule_release_seal_summary(request_payload)
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_release_seal_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    authorization = data["manual_provider_test_execution_capsule_final_authz"]

    assert set(authorization) == {
        "status",
        "reason",
        "execution_capsule_final_authz_hash",
        "execution_capsule_release_seal_hash",
        "final_authz_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "final_authz_count",
        "authz_request_count",
        "execution_permission_count",
    }
    assert authorization["status"] == "blocked"
    assert (
        authorization["reason"]
        == "expected_execution_capsule_release_seal_hash_required"
    )
    assert authorization["execution_capsule_final_authz_hash"] == ""
    assert authorization["execution_capsule_release_seal_hash"] == (
        expected_release_seal["execution_capsule_release_seal_hash"]
    )
    assert authorization["final_authz_hash"]
    assert authorization["claim_boundary_hash"]
    assert authorization["no_call_counters_hash"]
    assert authorization["component_count"] == 8
    assert authorization["passed_component_count"] == 7
    assert authorization["mismatch_count"] == 1
    assert authorization["component_hash_count"] == 4
    assert authorization["no_call_counter_count"] == 13
    assert authorization["claim_boundary_check_count"] == 3
    assert authorization["final_authz_count"] == 1
    assert authorization["authz_request_count"] == 1
    assert authorization["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API39_FINAL_AUTH_SENTINEL",
        "API39_FINAL_AUTH_PROVIDER_PAYLOAD_SENTINEL",
        "API39_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_final_authorization_without_authorization_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-final-authorization-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_release_seal = (
        provider_manual_test_execution_capsule_release_seal_summary(request_payload)
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_release_seal_hash"] = (
        expected_release_seal["execution_capsule_release_seal_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    authorization = data["manual_provider_test_execution_capsule_final_authz"]

    assert authorization["status"] == "blocked"
    assert authorization["reason"] == "execution_capsule_final_authz_required"
    assert authorization["execution_capsule_final_authz_hash"] == ""
    assert authorization["execution_capsule_release_seal_hash"] == (
        expected_release_seal["execution_capsule_release_seal_hash"]
    )
    assert authorization["final_authz_hash"] == ""
    assert authorization["claim_boundary_hash"]
    assert authorization["no_call_counters_hash"]
    assert authorization["component_count"] == 8
    assert authorization["passed_component_count"] == 4
    assert authorization["mismatch_count"] == 4
    assert authorization["component_hash_count"] == 3
    assert authorization["no_call_counter_count"] == 13
    assert authorization["claim_boundary_check_count"] == 3
    assert authorization["final_authz_count"] == 0
    assert authorization["authz_request_count"] == 0
    assert authorization["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API39_FINAL_AUTH_SENTINEL",
        "API39_FINAL_AUTH_PROVIDER_PAYLOAD_SENTINEL",
        "API39_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_final_authorization_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-final-authorization-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authorization = (
        provider_manual_test_execution_capsule_final_authorization_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    authorization = data["manual_provider_test_execution_capsule_final_authz"]

    assert authorization["status"] == "blocked"
    assert (
        authorization["reason"]
        == "execution_capsule_final_authz_execution_closed"
    )
    assert authorization["execution_capsule_final_authz_hash"] == (
        expected_authorization["execution_capsule_final_authz_hash"]
    )
    assert authorization["execution_capsule_release_seal_hash"] == (
        expected_authorization["execution_capsule_release_seal_hash"]
    )
    assert authorization["final_authz_hash"] == (
        expected_authorization["final_authz_hash"]
    )
    assert authorization["final_authz_hash"]
    assert authorization["claim_boundary_hash"] == (
        expected_authorization["claim_boundary_hash"]
    )
    assert authorization["no_call_counters_hash"] == (
        expected_authorization["no_call_counters_hash"]
    )
    assert authorization["component_count"] == 8
    assert authorization["passed_component_count"] == 8
    assert authorization["mismatch_count"] == 0
    assert authorization["component_hash_count"] == 4
    assert authorization["no_call_counter_count"] == 13
    assert authorization["claim_boundary_check_count"] == 3
    assert authorization["final_authz_count"] == 1
    assert authorization["authz_request_count"] == 1
    assert authorization["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API39_FINAL_AUTH_SENTINEL",
        "API39_FINAL_AUTH_PROVIDER_PAYLOAD_SENTINEL",
        "API39_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_export_without_expected_final_authz_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-export-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final_authz = (
        provider_manual_test_execution_capsule_final_authorization_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_final_authz_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data["manual_provider_test_execution_capsule_authz_export"]
    read_model = data["manual_provider_test_execution_capsule_authz_export_read_model"]

    assert set(export) == {
        "status",
        "reason",
        "execution_capsule_authz_export_hash",
        "execution_capsule_final_authz_hash",
        "export_metadata_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "export_count",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "export_metadata_count",
        "execution_permission_count",
    }
    assert export["status"] == "blocked"
    assert export["reason"] == "expected_execution_capsule_final_authz_hash_required"
    assert export["execution_capsule_authz_export_hash"] == ""
    assert export["execution_capsule_final_authz_hash"] == (
        expected_final_authz["execution_capsule_final_authz_hash"]
    )
    assert export["export_metadata_hash"]
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["export_count"] == 0
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 7
    assert export["mismatch_count"] == 1
    assert export["component_hash_count"] == 4
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 1
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "blocked"
    assert read_model["reason"] == "execution_capsule_authz_export_not_available"
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API40_EXPORT_AUTH_SENTINEL",
        "API40_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API40_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_export",
        "export_requested",
        "local-no-call-capsule-authz-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_export_without_export_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-export-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final_authz = (
        provider_manual_test_execution_capsule_final_authorization_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_final_authz_hash"] = (
        expected_final_authz["execution_capsule_final_authz_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data["manual_provider_test_execution_capsule_authz_export"]
    read_model = data["manual_provider_test_execution_capsule_authz_export_read_model"]

    assert export["status"] == "blocked"
    assert export["reason"] == "execution_capsule_authz_export_required"
    assert export["execution_capsule_authz_export_hash"] == ""
    assert export["execution_capsule_final_authz_hash"] == (
        expected_final_authz["execution_capsule_final_authz_hash"]
    )
    assert export["export_metadata_hash"] == ""
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["export_count"] == 0
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 4
    assert export["mismatch_count"] == 4
    assert export["component_hash_count"] == 3
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 0
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "blocked"
    assert read_model["reason"] == "execution_capsule_authz_export_not_available"
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API40_EXPORT_AUTH_SENTINEL",
        "API40_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API40_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_export",
        "export_requested",
        "local-no-call-capsule-authz-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_export_read_model_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-export-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_export = provider_manual_test_execution_capsule_authz_export_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data["manual_provider_test_execution_capsule_authz_export"]
    read_model = data["manual_provider_test_execution_capsule_authz_export_read_model"]

    assert export["status"] == "blocked"
    assert export["reason"] == "execution_capsule_authz_export_execution_closed"
    assert export["execution_capsule_authz_export_hash"] == (
        expected_export["execution_capsule_authz_export_hash"]
    )
    assert export["execution_capsule_final_authz_hash"] == (
        expected_export["execution_capsule_final_authz_hash"]
    )
    assert export["export_metadata_hash"] == expected_export["export_metadata_hash"]
    assert export["export_metadata_hash"]
    assert export["claim_boundary_hash"] == expected_export["claim_boundary_hash"]
    assert export["no_call_counters_hash"] == expected_export["no_call_counters_hash"]
    assert export["export_count"] == 1
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 8
    assert export["mismatch_count"] == 0
    assert export["component_hash_count"] == 4
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 1
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "available"
    assert read_model["reason"] == "execution_capsule_authz_export_read_model_available"
    assert read_model["latest_execution_capsule_authz_export_hash"] == (
        expected_export["execution_capsule_authz_export_hash"]
    )
    assert read_model["counts"]["execution_capsule_authz_export_count"] == 1
    assert read_model["counts"]["component_count"] == 8
    assert read_model["counts"]["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API40_EXPORT_AUTH_SENTINEL",
        "API40_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API40_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_export",
        "export_requested",
        "local-no-call-capsule-authz-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_handoff_without_expected_export_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-handoff-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_export = provider_manual_test_execution_capsule_authz_export_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_authz_export_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data["manual_provider_test_execution_capsule_authz_handoff_packet"]

    assert set(handoff) == {
        "status",
        "reason",
        "execution_capsule_authz_handoff_packet_hash",
        "execution_capsule_authz_export_hash",
        "execution_capsule_authz_export_read_model_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "packet_count",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "export_read_model_count",
        "handoff_request_count",
        "execution_permission_count",
    }
    assert handoff["status"] == "blocked"
    assert (
        handoff["reason"]
        == "expected_execution_capsule_authz_export_hash_required"
    )
    assert handoff["execution_capsule_authz_handoff_packet_hash"] == ""
    assert handoff["execution_capsule_authz_export_hash"] == (
        expected_export["execution_capsule_authz_export_hash"]
    )
    assert handoff["execution_capsule_authz_export_read_model_hash"] == (
        expected_export["execution_capsule_authz_export_hash"]
    )
    assert handoff["claim_boundary_hash"]
    assert handoff["no_call_counters_hash"]
    assert handoff["packet_count"] == 0
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 7
    assert handoff["mismatch_count"] == 1
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API41_HANDOFF_AUTH_SENTINEL",
        "API41_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "API41_HANDOFF_MATERIAL_SENTINEL",
        "manual_test_execution_capsule_authz_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_handoff_without_packet_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-handoff-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_export = provider_manual_test_execution_capsule_authz_export_summary(
        request_payload
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_authz_export_hash"] = (
        expected_export["execution_capsule_authz_export_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data["manual_provider_test_execution_capsule_authz_handoff_packet"]

    assert handoff["status"] == "blocked"
    assert handoff["reason"] == "execution_capsule_authz_handoff_packet_required"
    assert handoff["execution_capsule_authz_handoff_packet_hash"] == ""
    assert handoff["execution_capsule_authz_export_hash"] == (
        expected_export["execution_capsule_authz_export_hash"]
    )
    assert handoff["execution_capsule_authz_export_read_model_hash"] == (
        expected_export["execution_capsule_authz_export_hash"]
    )
    assert handoff["claim_boundary_hash"]
    assert handoff["no_call_counters_hash"]
    assert handoff["packet_count"] == 0
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 5
    assert handoff["mismatch_count"] == 3
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 0
    assert handoff["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API41_HANDOFF_AUTH_SENTINEL",
        "API41_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "API41_HANDOFF_MATERIAL_SENTINEL",
        "manual_test_execution_capsule_authz_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_handoff_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-handoff-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_handoff = (
        provider_manual_test_execution_capsule_authz_handoff_packet_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data["manual_provider_test_execution_capsule_authz_handoff_packet"]

    assert handoff["status"] == "blocked"
    assert handoff["reason"] == "execution_capsule_authz_handoff_packet_execution_closed"
    assert handoff["execution_capsule_authz_handoff_packet_hash"] == (
        expected_authz_handoff["execution_capsule_authz_handoff_packet_hash"]
    )
    assert handoff["execution_capsule_authz_export_hash"] == (
        expected_authz_handoff["execution_capsule_authz_export_hash"]
    )
    assert handoff["execution_capsule_authz_export_read_model_hash"] == (
        expected_authz_handoff["execution_capsule_authz_export_read_model_hash"]
    )
    assert handoff["claim_boundary_hash"] == (
        expected_authz_handoff["claim_boundary_hash"]
    )
    assert handoff["no_call_counters_hash"] == (
        expected_authz_handoff["no_call_counters_hash"]
    )
    assert handoff["packet_count"] == 1
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 8
    assert handoff["mismatch_count"] == 0
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API41_HANDOFF_AUTH_SENTINEL",
        "API41_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "API41_HANDOFF_MATERIAL_SENTINEL",
        "manual_test_execution_capsule_authz_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_review_without_expected_handoff_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-review-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_handoff = (
        provider_manual_test_execution_capsule_authz_handoff_packet_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_authz_handoff_packet_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data["manual_provider_test_execution_capsule_authz_operator_review"]

    assert set(review) == {
        "status",
        "reason",
        "execution_capsule_authz_operator_review_hash",
        "execution_capsule_authz_handoff_packet_hash",
        "operator_review_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "operator_review_count",
        "review_request_count",
        "execution_permission_count",
    }
    assert review["status"] == "blocked"
    assert (
        review["reason"]
        == "expected_execution_capsule_authz_handoff_packet_hash_required"
    )
    assert review["execution_capsule_authz_operator_review_hash"] == ""
    assert review["execution_capsule_authz_handoff_packet_hash"] == (
        expected_authz_handoff["execution_capsule_authz_handoff_packet_hash"]
    )
    assert review["operator_review_hash"]
    assert review["claim_boundary_hash"]
    assert review["no_call_counters_hash"]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 7
    assert review["mismatch_count"] == 1
    assert review["component_hash_count"] == 4
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 1
    assert review["review_request_count"] == 1
    assert review["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API42_REVIEW_AUTH_SENTINEL",
        "API42_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API42_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_operator_review",
        "review_requested",
        "local-no-call-capsule-authz-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_review_without_review_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-review-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_handoff = (
        provider_manual_test_execution_capsule_authz_handoff_packet_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_authz_handoff_packet_hash"] = (
        expected_authz_handoff["execution_capsule_authz_handoff_packet_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data["manual_provider_test_execution_capsule_authz_operator_review"]

    assert review["status"] == "blocked"
    assert review["reason"] == "execution_capsule_authz_operator_review_required"
    assert review["execution_capsule_authz_operator_review_hash"] == ""
    assert review["execution_capsule_authz_handoff_packet_hash"] == (
        expected_authz_handoff["execution_capsule_authz_handoff_packet_hash"]
    )
    assert review["operator_review_hash"] == ""
    assert review["claim_boundary_hash"]
    assert review["no_call_counters_hash"]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 4
    assert review["mismatch_count"] == 4
    assert review["component_hash_count"] == 3
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 0
    assert review["review_request_count"] == 0
    assert review["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API42_REVIEW_AUTH_SENTINEL",
        "API42_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API42_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_operator_review",
        "review_requested",
        "local-no-call-capsule-authz-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_review_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-review-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_review = (
        provider_manual_test_execution_capsule_authz_operator_review_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data["manual_provider_test_execution_capsule_authz_operator_review"]

    assert review["status"] == "blocked"
    assert review["reason"] == "execution_capsule_authz_operator_review_execution_closed"
    assert review["execution_capsule_authz_operator_review_hash"] == (
        expected_authz_review["execution_capsule_authz_operator_review_hash"]
    )
    assert review["execution_capsule_authz_handoff_packet_hash"] == (
        expected_authz_review["execution_capsule_authz_handoff_packet_hash"]
    )
    assert review["operator_review_hash"] == expected_authz_review["operator_review_hash"]
    assert review["claim_boundary_hash"] == expected_authz_review["claim_boundary_hash"]
    assert review["no_call_counters_hash"] == (
        expected_authz_review["no_call_counters_hash"]
    )
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 8
    assert review["mismatch_count"] == 0
    assert review["component_hash_count"] == 4
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 1
    assert review["review_request_count"] == 1
    assert review["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API42_REVIEW_AUTH_SENTINEL",
        "API42_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API42_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_operator_review",
        "review_requested",
        "local-no-call-capsule-authz-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_decision_without_expected_review_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-decision-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_review = (
        provider_manual_test_execution_capsule_authz_operator_review_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_authz_operator_review_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data["manual_provider_test_execution_capsule_authz_operator_decision"]

    assert set(decision) == {
        "status",
        "reason",
        "execution_capsule_authz_operator_decision_hash",
        "execution_capsule_authz_operator_review_hash",
        "operator_decision_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "operator_decision_count",
        "decision_request_count",
        "execution_permission_count",
    }
    assert decision["status"] == "blocked"
    assert (
        decision["reason"]
        == "expected_execution_capsule_authz_operator_review_hash_required"
    )
    assert decision["execution_capsule_authz_operator_decision_hash"] == ""
    assert decision["execution_capsule_authz_operator_review_hash"] == (
        expected_authz_review["execution_capsule_authz_operator_review_hash"]
    )
    assert decision["operator_decision_hash"]
    assert decision["claim_boundary_hash"]
    assert decision["no_call_counters_hash"]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 7
    assert decision["mismatch_count"] == 1
    assert decision["component_hash_count"] == 4
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 1
    assert decision["decision_request_count"] == 1
    assert decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API43_DECISION_AUTH_SENTINEL",
        "API43_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API43_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_operator_decision",
        "decision_requested",
        "local-no-call-capsule-authz-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_decision_without_decision_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-decision-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_review = (
        provider_manual_test_execution_capsule_authz_operator_review_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_authz_operator_review_hash"] = (
        expected_authz_review["execution_capsule_authz_operator_review_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data["manual_provider_test_execution_capsule_authz_operator_decision"]

    assert decision["status"] == "blocked"
    assert decision["reason"] == "execution_capsule_authz_operator_decision_required"
    assert decision["execution_capsule_authz_operator_decision_hash"] == ""
    assert decision["execution_capsule_authz_operator_review_hash"] == (
        expected_authz_review["execution_capsule_authz_operator_review_hash"]
    )
    assert decision["operator_decision_hash"] == ""
    assert decision["claim_boundary_hash"]
    assert decision["no_call_counters_hash"]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 4
    assert decision["mismatch_count"] == 4
    assert decision["component_hash_count"] == 3
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 0
    assert decision["decision_request_count"] == 0
    assert decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API43_DECISION_AUTH_SENTINEL",
        "API43_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API43_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_operator_decision",
        "decision_requested",
        "local-no-call-capsule-authz-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_decision_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-decision-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_decision = (
        provider_manual_test_execution_capsule_authz_operator_decision_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data["manual_provider_test_execution_capsule_authz_operator_decision"]

    assert decision["status"] == "blocked"
    assert decision["reason"] == "execution_capsule_authz_operator_decision_execution_closed"
    assert decision["execution_capsule_authz_operator_decision_hash"] == (
        expected_authz_decision["execution_capsule_authz_operator_decision_hash"]
    )
    assert decision["execution_capsule_authz_operator_review_hash"] == (
        expected_authz_decision["execution_capsule_authz_operator_review_hash"]
    )
    assert decision["operator_decision_hash"] == (
        expected_authz_decision["operator_decision_hash"]
    )
    assert decision["claim_boundary_hash"] == (
        expected_authz_decision["claim_boundary_hash"]
    )
    assert decision["no_call_counters_hash"] == (
        expected_authz_decision["no_call_counters_hash"]
    )
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 8
    assert decision["mismatch_count"] == 0
    assert decision["component_hash_count"] == 4
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 1
    assert decision["decision_request_count"] == 1
    assert decision["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API43_DECISION_AUTH_SENTINEL",
        "API43_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API43_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_operator_decision",
        "decision_requested",
        "local-no-call-capsule-authz-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_release_attestation_without_expected_decision_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-attestation-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_decision = (
        provider_manual_test_execution_capsule_authz_operator_decision_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_authz_operator_decision_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data[
        "manual_provider_test_execution_capsule_authz_release_attestation"
    ]

    assert set(attestation) == {
        "status",
        "reason",
        "execution_capsule_authz_release_attestation_hash",
        "execution_capsule_authz_operator_decision_hash",
        "release_attestation_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "release_attestation_count",
        "attestation_request_count",
        "execution_permission_count",
    }
    assert attestation["status"] == "blocked"
    assert (
        attestation["reason"]
        == "expected_execution_capsule_authz_operator_decision_hash_required"
    )
    assert attestation["execution_capsule_authz_release_attestation_hash"] == ""
    assert attestation["execution_capsule_authz_operator_decision_hash"] == (
        expected_authz_decision["execution_capsule_authz_operator_decision_hash"]
    )
    assert attestation["release_attestation_hash"]
    assert attestation["claim_boundary_hash"]
    assert attestation["no_call_counters_hash"]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 7
    assert attestation["mismatch_count"] == 1
    assert attestation["component_hash_count"] == 4
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 1
    assert attestation["attestation_request_count"] == 1
    assert attestation["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API44_ATTESTATION_AUTH_SENTINEL",
        "API44_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API44_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-authz-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_release_attestation_without_attestation_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-attestation-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_decision = (
        provider_manual_test_execution_capsule_authz_operator_decision_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_authz_operator_decision_hash"] = (
        expected_authz_decision["execution_capsule_authz_operator_decision_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data[
        "manual_provider_test_execution_capsule_authz_release_attestation"
    ]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == "execution_capsule_authz_release_attestation_required"
    assert attestation["execution_capsule_authz_release_attestation_hash"] == ""
    assert attestation["execution_capsule_authz_operator_decision_hash"] == (
        expected_authz_decision["execution_capsule_authz_operator_decision_hash"]
    )
    assert attestation["release_attestation_hash"] == ""
    assert attestation["claim_boundary_hash"]
    assert attestation["no_call_counters_hash"]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 4
    assert attestation["mismatch_count"] == 4
    assert attestation["component_hash_count"] == 3
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 0
    assert attestation["attestation_request_count"] == 0
    assert attestation["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API44_ATTESTATION_AUTH_SENTINEL",
        "API44_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API44_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-authz-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_release_attestation_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-attestation-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_attestation = (
        provider_manual_test_execution_capsule_authz_release_attestation_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data[
        "manual_provider_test_execution_capsule_authz_release_attestation"
    ]

    assert attestation["status"] == "blocked"
    assert (
        attestation["reason"]
        == "execution_capsule_authz_release_attestation_execution_closed"
    )
    assert attestation["execution_capsule_authz_release_attestation_hash"] == (
        expected_authz_attestation[
            "execution_capsule_authz_release_attestation_hash"
        ]
    )
    assert attestation["execution_capsule_authz_operator_decision_hash"] == (
        expected_authz_attestation[
            "execution_capsule_authz_operator_decision_hash"
        ]
    )
    assert attestation["release_attestation_hash"] == (
        expected_authz_attestation["release_attestation_hash"]
    )
    assert attestation["claim_boundary_hash"] == (
        expected_authz_attestation["claim_boundary_hash"]
    )
    assert attestation["no_call_counters_hash"] == (
        expected_authz_attestation["no_call_counters_hash"]
    )
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 8
    assert attestation["mismatch_count"] == 0
    assert attestation["component_hash_count"] == 4
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 1
    assert attestation["attestation_request_count"] == 1
    assert attestation["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API44_ATTESTATION_AUTH_SENTINEL",
        "API44_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API44_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-authz-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_release_seal_without_expected_attestation_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-seal-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_attestation = (
        provider_manual_test_execution_capsule_authz_release_attestation_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_authz_release_attestation_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data["manual_provider_test_execution_capsule_authz_release_seal"]

    assert set(seal) == {
        "status",
        "reason",
        "execution_capsule_authz_release_seal_hash",
        "execution_capsule_authz_release_attestation_hash",
        "seal_material_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "seal_material_count",
        "seal_request_count",
        "execution_permission_count",
    }
    assert seal["status"] == "blocked"
    assert (
        seal["reason"]
        == "expected_execution_capsule_authz_release_attestation_hash_required"
    )
    assert seal["execution_capsule_authz_release_seal_hash"] == ""
    assert seal["execution_capsule_authz_release_attestation_hash"] == (
        expected_authz_attestation[
            "execution_capsule_authz_release_attestation_hash"
        ]
    )
    assert seal["seal_material_hash"]
    assert seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 7
    assert seal["mismatch_count"] == 1
    assert seal["component_hash_count"] == 4
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 1
    assert seal["seal_request_count"] == 1
    assert seal["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API45_SEAL_AUTH_SENTINEL",
        "API45_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API45_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_release_seal",
        "seal_requested",
        "local-no-call-capsule-authz-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_release_seal_without_seal_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-seal-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_attestation = (
        provider_manual_test_execution_capsule_authz_release_attestation_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_authz_release_attestation_hash"] = (
        expected_authz_attestation[
            "execution_capsule_authz_release_attestation_hash"
        ]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data["manual_provider_test_execution_capsule_authz_release_seal"]

    assert seal["status"] == "blocked"
    assert seal["reason"] == "execution_capsule_authz_release_seal_required"
    assert seal["execution_capsule_authz_release_seal_hash"] == ""
    assert seal["execution_capsule_authz_release_attestation_hash"] == (
        expected_authz_attestation[
            "execution_capsule_authz_release_attestation_hash"
        ]
    )
    assert seal["seal_material_hash"] == ""
    assert seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 4
    assert seal["mismatch_count"] == 4
    assert seal["component_hash_count"] == 3
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 0
    assert seal["seal_request_count"] == 0
    assert seal["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API45_SEAL_AUTH_SENTINEL",
        "API45_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API45_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_release_seal",
        "seal_requested",
        "local-no-call-capsule-authz-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_release_seal_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-seal-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_seal = (
        provider_manual_test_execution_capsule_authz_release_seal_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data["manual_provider_test_execution_capsule_authz_release_seal"]

    assert seal["status"] == "blocked"
    assert seal["reason"] == "execution_capsule_authz_release_seal_execution_closed"
    assert seal["execution_capsule_authz_release_seal_hash"] == (
        expected_authz_seal["execution_capsule_authz_release_seal_hash"]
    )
    assert seal["execution_capsule_authz_release_attestation_hash"] == (
        expected_authz_seal["execution_capsule_authz_release_attestation_hash"]
    )
    assert seal["seal_material_hash"] == expected_authz_seal["seal_material_hash"]
    assert seal["claim_boundary_hash"] == expected_authz_seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"] == (
        expected_authz_seal["no_call_counters_hash"]
    )
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 8
    assert seal["mismatch_count"] == 0
    assert seal["component_hash_count"] == 4
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 1
    assert seal["seal_request_count"] == 1
    assert seal["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API45_SEAL_AUTH_SENTINEL",
        "API45_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API45_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_release_seal",
        "seal_requested",
        "local-no-call-capsule-authz-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_without_expected_seal_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_seal = (
        provider_manual_test_execution_capsule_authz_release_seal_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_authz_release_seal_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    final_authz = data["manual_provider_test_execution_capsule_authz_final_authz"]

    assert set(final_authz) == {
        "status",
        "reason",
        "execution_capsule_authz_final_authz_hash",
        "execution_capsule_authz_release_seal_hash",
        "final_authz_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "final_authz_count",
        "authz_request_count",
        "execution_permission_count",
    }
    assert final_authz["status"] == "blocked"
    assert (
        final_authz["reason"]
        == "expected_execution_capsule_authz_release_seal_hash_required"
    )
    assert final_authz["execution_capsule_authz_final_authz_hash"] == ""
    assert final_authz["execution_capsule_authz_release_seal_hash"] == (
        expected_authz_seal["execution_capsule_authz_release_seal_hash"]
    )
    assert final_authz["final_authz_hash"]
    assert final_authz["claim_boundary_hash"]
    assert final_authz["no_call_counters_hash"]
    assert final_authz["component_count"] == 8
    assert final_authz["passed_component_count"] == 7
    assert final_authz["mismatch_count"] == 1
    assert final_authz["component_hash_count"] == 4
    assert final_authz["no_call_counter_count"] == 13
    assert final_authz["claim_boundary_check_count"] == 3
    assert final_authz["final_authz_count"] == 1
    assert final_authz["authz_request_count"] == 1
    assert final_authz["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API46_FINAL_AUTH_SENTINEL",
        "API46_FINAL_AUTH_PROVIDER_PAYLOAD_SENTINEL",
        "API46_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-authz-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_without_authorization_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_seal = (
        provider_manual_test_execution_capsule_authz_release_seal_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_authz_release_seal_hash"] = (
        expected_authz_seal["execution_capsule_authz_release_seal_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    final_authz = data["manual_provider_test_execution_capsule_authz_final_authz"]

    assert final_authz["status"] == "blocked"
    assert final_authz["reason"] == "execution_capsule_authz_final_authz_required"
    assert final_authz["execution_capsule_authz_final_authz_hash"] == ""
    assert final_authz["execution_capsule_authz_release_seal_hash"] == (
        expected_authz_seal["execution_capsule_authz_release_seal_hash"]
    )
    assert final_authz["final_authz_hash"] == ""
    assert final_authz["claim_boundary_hash"]
    assert final_authz["no_call_counters_hash"]
    assert final_authz["component_count"] == 8
    assert final_authz["passed_component_count"] == 4
    assert final_authz["mismatch_count"] == 4
    assert final_authz["component_hash_count"] == 3
    assert final_authz["no_call_counter_count"] == 13
    assert final_authz["claim_boundary_check_count"] == 3
    assert final_authz["final_authz_count"] == 0
    assert final_authz["authz_request_count"] == 0
    assert final_authz["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API46_FINAL_AUTH_SENTINEL",
        "API46_FINAL_AUTH_PROVIDER_PAYLOAD_SENTINEL",
        "API46_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-authz-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_final = (
        provider_manual_test_execution_capsule_authz_final_authorization_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    final_authz = data["manual_provider_test_execution_capsule_authz_final_authz"]

    assert final_authz["status"] == "blocked"
    assert final_authz["reason"] == "execution_capsule_authz_final_authz_execution_closed"
    assert final_authz["execution_capsule_authz_final_authz_hash"] == (
        expected_authz_final["execution_capsule_authz_final_authz_hash"]
    )
    assert final_authz["execution_capsule_authz_release_seal_hash"] == (
        expected_authz_final["execution_capsule_authz_release_seal_hash"]
    )
    assert final_authz["final_authz_hash"] == expected_authz_final["final_authz_hash"]
    assert final_authz["claim_boundary_hash"] == (
        expected_authz_final["claim_boundary_hash"]
    )
    assert final_authz["no_call_counters_hash"] == (
        expected_authz_final["no_call_counters_hash"]
    )
    assert final_authz["component_count"] == 8
    assert final_authz["passed_component_count"] == 8
    assert final_authz["mismatch_count"] == 0
    assert final_authz["component_hash_count"] == 4
    assert final_authz["no_call_counter_count"] == 13
    assert final_authz["claim_boundary_check_count"] == 3
    assert final_authz["final_authz_count"] == 1
    assert final_authz["authz_request_count"] == 1
    assert final_authz["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API46_FINAL_AUTH_SENTINEL",
        "API46_FINAL_AUTH_PROVIDER_PAYLOAD_SENTINEL",
        "API46_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-authz-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_export_without_expected_final_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-export-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_final = (
        provider_manual_test_execution_capsule_authz_final_authorization_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_authz_final_authz_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data["manual_provider_test_execution_capsule_authz_final_authz_export"]
    read_model = data[
        "manual_provider_test_execution_capsule_authz_final_authz_export_read_model"
    ]

    assert set(export) == {
        "status",
        "reason",
        "execution_capsule_authz_final_authz_export_hash",
        "execution_capsule_authz_final_authz_hash",
        "export_metadata_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "export_count",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "export_metadata_count",
        "export_request_count",
        "execution_permission_count",
    }
    assert export["status"] == "blocked"
    assert (
        export["reason"]
        == "expected_execution_capsule_authz_final_authz_hash_required"
    )
    assert export["execution_capsule_authz_final_authz_export_hash"] == ""
    assert export["execution_capsule_authz_final_authz_hash"] == (
        expected_authz_final["execution_capsule_authz_final_authz_hash"]
    )
    assert export["export_metadata_hash"]
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["export_count"] == 0
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 7
    assert export["mismatch_count"] == 1
    assert export["component_hash_count"] == 4
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 1
    assert export["export_request_count"] == 1
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "blocked"
    assert (
        read_model["reason"]
        == "execution_capsule_authz_final_authz_export_not_available"
    )
    assert (
        read_model["latest_execution_capsule_authz_final_authz_export_hash"] == ""
    )
    assert read_model["counts"][
        "execution_capsule_authz_final_authz_export_count"
    ] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API47_EXPORT_AUTH_SENTINEL",
        "API47_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API47_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_export",
        "export_requested",
        "local-no-call-capsule-authz-final-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_export_without_export_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-export-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_authz_final = (
        provider_manual_test_execution_capsule_authz_final_authorization_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_authz_final_authz_hash"] = (
        expected_authz_final["execution_capsule_authz_final_authz_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data["manual_provider_test_execution_capsule_authz_final_authz_export"]
    read_model = data[
        "manual_provider_test_execution_capsule_authz_final_authz_export_read_model"
    ]

    assert export["status"] == "blocked"
    assert export["reason"] == "execution_capsule_authz_final_authz_export_required"
    assert export["execution_capsule_authz_final_authz_export_hash"] == ""
    assert export["execution_capsule_authz_final_authz_hash"] == (
        expected_authz_final["execution_capsule_authz_final_authz_hash"]
    )
    assert export["export_metadata_hash"] == ""
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["export_count"] == 0
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 4
    assert export["mismatch_count"] == 4
    assert export["component_hash_count"] == 3
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 0
    assert export["export_request_count"] == 0
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "blocked"
    assert (
        read_model["reason"]
        == "execution_capsule_authz_final_authz_export_not_available"
    )
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_export",
        "export_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_export_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-export-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_export = (
        provider_manual_test_execution_capsule_authz_final_authz_export_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data["manual_provider_test_execution_capsule_authz_final_authz_export"]
    read_model = data[
        "manual_provider_test_execution_capsule_authz_final_authz_export_read_model"
    ]

    assert export["status"] == "blocked"
    assert export["reason"] == (
        "execution_capsule_authz_final_authz_export_execution_closed"
    )
    assert export["execution_capsule_authz_final_authz_export_hash"] == (
        expected_export["execution_capsule_authz_final_authz_export_hash"]
    )
    assert export["execution_capsule_authz_final_authz_hash"] == (
        expected_export["execution_capsule_authz_final_authz_hash"]
    )
    assert export["export_metadata_hash"] == expected_export["export_metadata_hash"]
    assert export["claim_boundary_hash"] == expected_export["claim_boundary_hash"]
    assert export["no_call_counters_hash"] == (
        expected_export["no_call_counters_hash"]
    )
    assert export["export_count"] == 1
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 8
    assert export["mismatch_count"] == 0
    assert export["component_hash_count"] == 4
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 1
    assert export["export_request_count"] == 1
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "available"
    assert read_model["reason"] == (
        "execution_capsule_authz_final_authz_export_read_model_available"
    )
    assert read_model[
        "latest_execution_capsule_authz_final_authz_export_hash"
    ] == expected_export["execution_capsule_authz_final_authz_export_hash"]
    assert read_model["counts"][
        "execution_capsule_authz_final_authz_export_count"
    ] == 1
    assert read_model["counts"]["component_count"] == 8
    assert read_model["counts"]["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API47_EXPORT_AUTH_SENTINEL",
        "API47_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API47_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_export",
        "export_requested",
        "local-no-call-capsule-authz-final-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_handoff_without_expected_export_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-handoff-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
        include_execution_capsule_authz_final_authz_handoff_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_export = (
        provider_manual_test_execution_capsule_authz_final_authz_export_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop("expected_execution_capsule_authz_final_authz_export_hash")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data[
        "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet"
    ]

    assert set(handoff) == {
        "status",
        "reason",
        "execution_capsule_authz_final_authz_handoff_packet_hash",
        "execution_capsule_authz_final_authz_export_hash",
        "execution_capsule_authz_final_authz_export_read_model_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "packet_count",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "export_read_model_count",
        "handoff_request_count",
        "execution_permission_count",
    }
    assert handoff["status"] == "blocked"
    assert handoff["reason"] == (
        "expected_execution_capsule_authz_final_authz_export_hash_required"
    )
    assert handoff["execution_capsule_authz_final_authz_handoff_packet_hash"] == ""
    assert handoff["execution_capsule_authz_final_authz_export_hash"] == (
        expected_export["execution_capsule_authz_final_authz_export_hash"]
    )
    assert handoff["execution_capsule_authz_final_authz_export_read_model_hash"] == (
        expected_export["execution_capsule_authz_final_authz_export_hash"]
    )
    assert handoff["claim_boundary_hash"]
    assert handoff["no_call_counters_hash"]
    assert handoff["packet_count"] == 0
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 7
    assert handoff["mismatch_count"] == 1
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API48_HANDOFF_AUTH_SENTINEL",
        "API48_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_handoff_without_packet_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-handoff-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_export = (
        provider_manual_test_execution_capsule_authz_final_authz_export_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_authz_final_authz_export_hash"] = (
        expected_export["execution_capsule_authz_final_authz_export_hash"]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data[
        "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet"
    ]

    assert handoff["status"] == "blocked"
    assert (
        handoff["reason"]
        == "execution_capsule_authz_final_authz_handoff_packet_required"
    )
    assert handoff["execution_capsule_authz_final_authz_handoff_packet_hash"] == ""
    assert handoff["execution_capsule_authz_final_authz_export_hash"] == (
        expected_export["execution_capsule_authz_final_authz_export_hash"]
    )
    assert handoff["execution_capsule_authz_final_authz_export_read_model_hash"] == (
        expected_export["execution_capsule_authz_final_authz_export_hash"]
    )
    assert handoff["claim_boundary_hash"]
    assert handoff["no_call_counters_hash"]
    assert handoff["packet_count"] == 0
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 5
    assert handoff["mismatch_count"] == 3
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 0
    assert handoff["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_handoff_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-handoff-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
        include_execution_capsule_authz_final_authz_handoff_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final_handoff = (
        provider_manual_test_execution_capsule_authz_final_authz_handoff_packet_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data[
        "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet"
    ]

    assert handoff["status"] == "blocked"
    assert handoff["reason"] == (
        "execution_capsule_authz_final_authz_handoff_packet_execution_closed"
    )
    assert handoff["execution_capsule_authz_final_authz_handoff_packet_hash"] == (
        expected_final_handoff[
            "execution_capsule_authz_final_authz_handoff_packet_hash"
        ]
    )
    assert handoff["execution_capsule_authz_final_authz_export_hash"] == (
        expected_final_handoff["execution_capsule_authz_final_authz_export_hash"]
    )
    assert handoff["execution_capsule_authz_final_authz_export_read_model_hash"] == (
        expected_final_handoff[
            "execution_capsule_authz_final_authz_export_read_model_hash"
        ]
    )
    assert handoff["claim_boundary_hash"] == expected_final_handoff[
        "claim_boundary_hash"
    ]
    assert handoff["no_call_counters_hash"] == expected_final_handoff[
        "no_call_counters_hash"
    ]
    assert handoff["packet_count"] == 1
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 8
    assert handoff["mismatch_count"] == 0
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API48_HANDOFF_AUTH_SENTINEL",
        "API48_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_review_without_expected_handoff_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-review-no-expected",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
        include_execution_capsule_authz_final_authz_handoff_packet=True,
        include_execution_capsule_authz_final_authz_operator_review=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final_handoff = (
        provider_manual_test_execution_capsule_authz_final_authz_handoff_packet_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_handoff_packet_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data[
        "manual_provider_test_execution_capsule_authz_final_authz_operator_review"
    ]

    assert set(review) == {
        "status",
        "reason",
        "execution_capsule_authz_final_authz_operator_review_hash",
        "execution_capsule_authz_final_authz_handoff_packet_hash",
        "operator_review_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "operator_review_count",
        "review_request_count",
        "execution_permission_count",
    }
    assert review["status"] == "blocked"
    assert review["reason"] == (
        "expected_execution_capsule_authz_final_authz_handoff_packet_hash_required"
    )
    assert review["execution_capsule_authz_final_authz_operator_review_hash"] == ""
    assert review["execution_capsule_authz_final_authz_handoff_packet_hash"] == (
        expected_final_handoff[
            "execution_capsule_authz_final_authz_handoff_packet_hash"
        ]
    )
    assert review["operator_review_hash"]
    assert review["claim_boundary_hash"]
    assert review["no_call_counters_hash"]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 7
    assert review["mismatch_count"] == 1
    assert review["component_hash_count"] == 4
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 1
    assert review["review_request_count"] == 1
    assert review["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API49_REVIEW_AUTH_SENTINEL",
        "API49_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API49_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_operator_review",
        "review_requested",
        "local-no-call-capsule-authz-final-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_review_without_review_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-review-no-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
        include_execution_capsule_authz_final_authz_handoff_packet=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final_handoff = (
        provider_manual_test_execution_capsule_authz_final_authz_handoff_packet_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_authz_final_authz_handoff_packet_hash"] = (
        expected_final_handoff[
            "execution_capsule_authz_final_authz_handoff_packet_hash"
        ]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data[
        "manual_provider_test_execution_capsule_authz_final_authz_operator_review"
    ]

    assert review["status"] == "blocked"
    assert review["reason"] == (
        "execution_capsule_authz_final_authz_operator_review_required"
    )
    assert review["execution_capsule_authz_final_authz_operator_review_hash"] == ""
    assert review["execution_capsule_authz_final_authz_handoff_packet_hash"] == (
        expected_final_handoff[
            "execution_capsule_authz_final_authz_handoff_packet_hash"
        ]
    )
    assert review["operator_review_hash"] == ""
    assert review["claim_boundary_hash"]
    assert review["no_call_counters_hash"]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 4
    assert review["mismatch_count"] == 4
    assert review["component_hash_count"] == 3
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 0
    assert review["review_request_count"] == 0
    assert review["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API49_REVIEW_AUTH_SENTINEL",
        "API49_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API49_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_operator_review",
        "review_requested",
        "local-no-call-capsule-authz-final-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_review_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-capsule-authz-final-review-present",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
        include_execution_capsule_authz_final_authz_handoff_packet=True,
        include_execution_capsule_authz_final_authz_operator_review=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final_review = (
        provider_manual_test_execution_capsule_authz_final_authz_operator_review_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data[
        "manual_provider_test_execution_capsule_authz_final_authz_operator_review"
    ]

    assert review["status"] == "blocked"
    assert review["reason"] == (
        "execution_capsule_authz_final_authz_operator_review_execution_closed"
    )
    assert review["execution_capsule_authz_final_authz_operator_review_hash"] == (
        expected_final_review[
            "execution_capsule_authz_final_authz_operator_review_hash"
        ]
    )
    assert review["execution_capsule_authz_final_authz_handoff_packet_hash"] == (
        expected_final_review[
            "execution_capsule_authz_final_authz_handoff_packet_hash"
        ]
    )
    assert review["operator_review_hash"] == expected_final_review[
        "operator_review_hash"
    ]
    assert review["claim_boundary_hash"] == expected_final_review[
        "claim_boundary_hash"
    ]
    assert review["no_call_counters_hash"] == expected_final_review[
        "no_call_counters_hash"
    ]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 8
    assert review["mismatch_count"] == 0
    assert review["component_hash_count"] == 4
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 1
    assert review["review_request_count"] == 1
    assert review["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API49_REVIEW_AUTH_SENTINEL",
        "API49_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API49_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_operator_review",
        "review_requested",
        "local-no-call-capsule-authz-final-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_decision_without_expected_review_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api50-decision-missing-expected-review",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
        include_execution_capsule_authz_final_authz_handoff_packet=True,
        include_execution_capsule_authz_final_authz_operator_review=True,
        include_execution_capsule_authz_final_authz_operator_decision=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final_review = (
        provider_manual_test_execution_capsule_authz_final_authz_operator_review_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_operator_review_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    decision = payload["data"][
        "manual_provider_test_execution_capsule_authz_final_authz_operator_decision"
    ]

    assert decision["status"] == "blocked"
    assert decision["reason"] == (
        "expected_execution_capsule_authz_final_authz_operator_review_hash_required"
    )
    assert decision[
        "execution_capsule_authz_final_authz_operator_decision_hash"
    ] == ""
    assert decision[
        "execution_capsule_authz_final_authz_operator_review_hash"
    ] == expected_final_review[
        "execution_capsule_authz_final_authz_operator_review_hash"
    ]
    assert decision["operator_decision_hash"]
    assert decision["passed_component_count"] == 7
    assert decision["mismatch_count"] == 1
    assert decision["component_hash_count"] == 4
    assert decision["execution_permission_count"] == 0
    assert payload["data"]["execution_boundary"]["provider_calls"] == 0
    assert payload["data"]["execution_boundary"]["network_calls"] == 0
    assert payload["data"]["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API50_DECISION_AUTH_SENTINEL",
        "API50_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API50_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_operator_decision",
        "decision_requested",
        "local-no-call-capsule-authz-final-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_decision_without_decision_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api50-decision-missing-payload",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
        include_execution_capsule_authz_final_authz_handoff_packet=True,
        include_execution_capsule_authz_final_authz_operator_review=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final_review = (
        provider_manual_test_execution_capsule_authz_final_authz_operator_review_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    request_payload["expected_execution_capsule_authz_final_authz_operator_review_hash"] = (
        expected_final_review[
            "execution_capsule_authz_final_authz_operator_review_hash"
        ]
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    decision = payload["data"][
        "manual_provider_test_execution_capsule_authz_final_authz_operator_decision"
    ]

    assert decision["status"] == "blocked"
    assert decision["reason"] == (
        "execution_capsule_authz_final_authz_operator_decision_required"
    )
    assert decision[
        "execution_capsule_authz_final_authz_operator_decision_hash"
    ] == ""
    assert decision[
        "execution_capsule_authz_final_authz_operator_review_hash"
    ] == expected_final_review[
        "execution_capsule_authz_final_authz_operator_review_hash"
    ]
    assert decision["operator_decision_hash"] == ""
    assert decision["passed_component_count"] == 4
    assert decision["mismatch_count"] == 4
    assert decision["component_hash_count"] == 3
    assert decision["operator_decision_count"] == 0
    assert decision["decision_request_count"] == 0
    assert decision["execution_permission_count"] == 0
    assert payload["data"]["execution_boundary"]["provider_calls"] == 0
    assert payload["data"]["execution_boundary"]["network_calls"] == 0
    assert payload["data"]["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_operator_decision",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_decision_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api50-decision-complete",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
        include_execution_capsule_authz_final_authz_handoff_packet=True,
        include_execution_capsule_authz_final_authz_operator_review=True,
        include_execution_capsule_authz_final_authz_operator_decision=True,
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(request_payload)
    expected_final_decision = (
        provider_manual_test_execution_capsule_authz_final_authz_operator_decision_summary(
            request_payload
        )
    )
    request_payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data[
        "manual_provider_test_execution_capsule_authz_final_authz_operator_decision"
    ]

    assert decision["status"] == "blocked"
    assert decision["reason"] == (
        "execution_capsule_authz_final_authz_operator_decision_execution_closed"
    )
    assert decision[
        "execution_capsule_authz_final_authz_operator_decision_hash"
    ] == expected_final_decision[
        "execution_capsule_authz_final_authz_operator_decision_hash"
    ]
    assert decision[
        "execution_capsule_authz_final_authz_operator_review_hash"
    ] == expected_final_decision[
        "execution_capsule_authz_final_authz_operator_review_hash"
    ]
    assert decision["operator_decision_hash"] == expected_final_decision[
        "operator_decision_hash"
    ]
    assert decision["claim_boundary_hash"] == expected_final_decision[
        "claim_boundary_hash"
    ]
    assert decision["no_call_counters_hash"] == expected_final_decision[
        "no_call_counters_hash"
    ]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 8
    assert decision["mismatch_count"] == 0
    assert decision["component_hash_count"] == 4
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 1
    assert decision["decision_request_count"] == 1
    assert decision["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API50_DECISION_AUTH_SENTINEL",
        "API50_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API50_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_operator_decision",
        "decision_requested",
        "local-no-call-capsule-authz-final-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def _final_authz_decision_precheck_payload(
    run_id: str,
    *,
    include_release_attestation: bool = False,
    include_release_seal: bool = False,
    include_final_authorization: bool = False,
    include_final_authorization_export: bool = False,
    include_final_authorization_handoff: bool = False,
    include_final_authorization_operator_review: bool = False,
    include_final_authorization_operator_decision: bool = False,
    include_final_authorization_release_attestation: bool = False,
    include_final_authorization_release_seal: bool = False,
    include_final_authorization_final_authorization: bool = False,
    include_final_authorization_final_authorization_export: bool = False,
    include_final_authorization_final_authorization_handoff: bool = False,
    include_final_authorization_final_authorization_operator_review: bool = False,
    include_final_authorization_final_authorization_operator_decision: bool = False,
    include_final_authorization_final_authorization_release_attestation: bool = False,
    include_final_authorization_final_authorization_release_seal: bool = False,
    include_final_authorization_final_authorization_final_authorization: bool = False,
    include_final_authorization_final_authorization_final_authorization_export: bool = False,
    include_final_authorization_final_authorization_final_authorization_handoff: bool = False,
) -> dict:
    payload = _provider_envelope_precheck_payload(
        run_id=run_id,
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        include_operator_opt_in=True,
        include_sealed_pre_execution_packet=True,
        include_arming_record=True,
        include_release_proposal=True,
        include_final_release_packet=True,
        include_execution_switch=True,
        execution_switch_enable=True,
        include_executor_preflight=True,
        include_executor_dispatch_record=True,
        include_invocation_receipt=True,
        include_post_invocation_audit=True,
        include_completion_summary=True,
        include_closeout_record=True,
        include_operator_handback=True,
        include_operator_decision_packet=True,
        include_operator_release_attestation=True,
        include_release_authorization_seal=True,
        include_execution_authorization_capsule=True,
        include_execution_capsule_export=True,
        include_execution_capsule_handoff_packet=True,
        include_execution_capsule_operator_review=True,
        include_execution_capsule_operator_decision=True,
        include_execution_capsule_release_attestation=True,
        include_execution_capsule_release_seal=True,
        include_execution_capsule_final_authorization=True,
        include_execution_capsule_authz_export=True,
        include_execution_capsule_authz_handoff_packet=True,
        include_execution_capsule_authz_operator_review=True,
        include_execution_capsule_authz_operator_decision=True,
        include_execution_capsule_authz_release_attestation=True,
        include_execution_capsule_authz_release_seal=True,
        include_execution_capsule_authz_final_authorization=True,
        include_execution_capsule_authz_final_authz_export=True,
        include_execution_capsule_authz_final_authz_handoff_packet=True,
        include_execution_capsule_authz_final_authz_operator_review=True,
        include_execution_capsule_authz_final_authz_operator_decision=True,
        include_execution_capsule_authz_final_authz_release_attestation=(
            include_release_attestation
            or include_release_seal
            or include_final_authorization
            or include_final_authorization_export
            or include_final_authorization_handoff
            or include_final_authorization_operator_review
            or include_final_authorization_operator_decision
            or include_final_authorization_release_attestation
            or include_final_authorization_release_seal
            or include_final_authorization_final_authorization
            or include_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_release_seal=(
            include_release_seal
            or include_final_authorization
            or include_final_authorization_export
            or include_final_authorization_handoff
            or include_final_authorization_operator_review
            or include_final_authorization_operator_decision
            or include_final_authorization_release_attestation
            or include_final_authorization_release_seal
            or include_final_authorization_final_authorization
            or include_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization=(
            include_final_authorization
            or include_final_authorization_export
            or include_final_authorization_handoff
            or include_final_authorization_operator_review
            or include_final_authorization_operator_decision
            or include_final_authorization_release_attestation
            or include_final_authorization_release_seal
            or include_final_authorization_final_authorization
            or include_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_export=(
            include_final_authorization_export
            or include_final_authorization_handoff
            or include_final_authorization_operator_review
            or include_final_authorization_operator_decision
            or include_final_authorization_release_attestation
            or include_final_authorization_release_seal
            or include_final_authorization_final_authorization
            or include_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_handoff_packet=(
            include_final_authorization_handoff
            or include_final_authorization_operator_review
            or include_final_authorization_operator_decision
            or include_final_authorization_release_attestation
            or include_final_authorization_release_seal
            or include_final_authorization_final_authorization
            or include_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_operator_review=(
            include_final_authorization_operator_review
            or include_final_authorization_operator_decision
            or include_final_authorization_release_attestation
            or include_final_authorization_release_seal
            or include_final_authorization_final_authorization
            or include_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_operator_decision=(
            include_final_authorization_operator_decision
            or include_final_authorization_release_attestation
            or include_final_authorization_release_seal
            or include_final_authorization_final_authorization
            or include_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_release_attestation=(
            include_final_authorization_release_attestation
            or include_final_authorization_release_seal
            or include_final_authorization_final_authorization
            or include_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_release_seal=(
            include_final_authorization_release_seal
            or include_final_authorization_final_authorization
            or include_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_final_authorization=(
            include_final_authorization_final_authorization
            or include_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_final_authorization_export=(
            include_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet=(
            include_final_authorization_final_authorization_handoff
            or include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review=(
            include_final_authorization_final_authorization_operator_review
            or include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision=(
            include_final_authorization_final_authorization_operator_decision
            or include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation=(
            include_final_authorization_final_authorization_release_attestation
            or include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal=(
            include_final_authorization_final_authorization_release_seal
            or include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization=(
            include_final_authorization_final_authorization_final_authorization
            or include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export=(
            include_final_authorization_final_authorization_final_authorization_export
            or include_final_authorization_final_authorization_final_authorization_handoff
        ),
        include_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_handoff_packet=(
            include_final_authorization_final_authorization_final_authorization_handoff
        ),
    )
    expected_handoff = provider_manual_test_handoff_packet_summary(payload)
    payload["expected_handoff_packet_hash"] = expected_handoff[
        "handoff_packet_hash"
    ]
    return payload


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_release_attestation_without_expected_decision_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api51-attestation-missing-expected-decision",
        include_release_attestation=True,
    )
    expected_final_decision = (
        provider_manual_test_execution_capsule_authz_final_authz_operator_decision_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_operator_decision_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    attestation = payload["data"][
        "manual_provider_test_execution_capsule_authz_final_authz_release_attestation"
    ]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == (
        "expected_execution_capsule_authz_final_authz_operator_decision_hash_required"
    )
    assert attestation[
        "execution_capsule_authz_final_authz_release_attestation_hash"
    ] == ""
    assert attestation[
        "execution_capsule_authz_final_authz_operator_decision_hash"
    ] == expected_final_decision[
        "execution_capsule_authz_final_authz_operator_decision_hash"
    ]
    assert attestation["release_attestation_hash"]
    assert attestation["passed_component_count"] == 7
    assert attestation["mismatch_count"] == 1
    assert attestation["component_hash_count"] == 4
    assert attestation["execution_permission_count"] == 0
    assert payload["data"]["execution_boundary"]["provider_calls"] == 0
    assert payload["data"]["execution_boundary"]["network_calls"] == 0
    assert payload["data"]["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API51_ATTESTATION_AUTH_SENTINEL",
        "API51_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API51_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-authz-final-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_release_attestation_without_attestation_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api51-attestation-missing-payload"
    )
    expected_final_decision = (
        provider_manual_test_execution_capsule_authz_final_authz_operator_decision_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_operator_decision_hash"
    ] = expected_final_decision[
        "execution_capsule_authz_final_authz_operator_decision_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    attestation = payload["data"][
        "manual_provider_test_execution_capsule_authz_final_authz_release_attestation"
    ]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == (
        "execution_capsule_authz_final_authz_release_attestation_required"
    )
    assert attestation[
        "execution_capsule_authz_final_authz_release_attestation_hash"
    ] == ""
    assert attestation[
        "execution_capsule_authz_final_authz_operator_decision_hash"
    ] == expected_final_decision[
        "execution_capsule_authz_final_authz_operator_decision_hash"
    ]
    assert attestation["release_attestation_hash"] == ""
    assert attestation["passed_component_count"] == 4
    assert attestation["mismatch_count"] == 4
    assert attestation["component_hash_count"] == 3
    assert attestation["release_attestation_count"] == 0
    assert attestation["attestation_request_count"] == 0
    assert attestation["execution_permission_count"] == 0
    assert payload["data"]["execution_boundary"]["provider_calls"] == 0
    assert payload["data"]["execution_boundary"]["network_calls"] == 0
    assert payload["data"]["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_release_attestation",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_release_attestation_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api51-attestation-complete",
        include_release_attestation=True,
    )
    expected_attestation = (
        provider_manual_test_execution_capsule_authz_final_authz_release_attestation_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data[
        "manual_provider_test_execution_capsule_authz_final_authz_release_attestation"
    ]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == (
        "execution_capsule_authz_final_authz_release_attestation_execution_closed"
    )
    assert attestation[
        "execution_capsule_authz_final_authz_release_attestation_hash"
    ] == expected_attestation[
        "execution_capsule_authz_final_authz_release_attestation_hash"
    ]
    assert attestation[
        "execution_capsule_authz_final_authz_operator_decision_hash"
    ] == expected_attestation[
        "execution_capsule_authz_final_authz_operator_decision_hash"
    ]
    assert attestation["release_attestation_hash"] == expected_attestation[
        "release_attestation_hash"
    ]
    assert attestation["claim_boundary_hash"] == expected_attestation[
        "claim_boundary_hash"
    ]
    assert attestation["no_call_counters_hash"] == expected_attestation[
        "no_call_counters_hash"
    ]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 8
    assert attestation["mismatch_count"] == 0
    assert attestation["component_hash_count"] == 4
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 1
    assert attestation["attestation_request_count"] == 1
    assert attestation["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API51_ATTESTATION_AUTH_SENTINEL",
        "API51_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API51_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-authz-final-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_release_seal_without_expected_attestation_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api52-seal-missing-expected-attestation",
        include_release_seal=True,
    )
    expected_attestation = (
        provider_manual_test_execution_capsule_authz_final_authz_release_attestation_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_release_attestation_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    seal = payload["data"][
        "manual_provider_test_execution_capsule_authz_final_authz_release_seal"
    ]

    assert seal["status"] == "blocked"
    assert seal["reason"] == (
        "expected_execution_capsule_authz_final_authz_release_attestation_hash_required"
    )
    assert seal["execution_capsule_authz_final_authz_release_seal_hash"] == ""
    assert seal[
        "execution_capsule_authz_final_authz_release_attestation_hash"
    ] == expected_attestation[
        "execution_capsule_authz_final_authz_release_attestation_hash"
    ]
    assert seal["seal_material_hash"]
    assert seal["passed_component_count"] == 7
    assert seal["mismatch_count"] == 1
    assert seal["component_hash_count"] == 4
    assert seal["execution_permission_count"] == 0
    assert payload["data"]["execution_boundary"]["provider_calls"] == 0
    assert payload["data"]["execution_boundary"]["network_calls"] == 0
    assert payload["data"]["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API52_SEAL_AUTH_SENTINEL",
        "API52_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API52_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_release_seal",
        "seal_requested",
        "local-no-call-capsule-authz-final-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_release_seal_without_seal_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api52-seal-missing-payload",
        include_release_attestation=True,
    )
    expected_attestation = (
        provider_manual_test_execution_capsule_authz_final_authz_release_attestation_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_release_attestation_hash"
    ] = expected_attestation[
        "execution_capsule_authz_final_authz_release_attestation_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    seal = payload["data"][
        "manual_provider_test_execution_capsule_authz_final_authz_release_seal"
    ]

    assert seal["status"] == "blocked"
    assert seal["reason"] == "execution_capsule_authz_final_authz_release_seal_required"
    assert seal["execution_capsule_authz_final_authz_release_seal_hash"] == ""
    assert seal[
        "execution_capsule_authz_final_authz_release_attestation_hash"
    ] == expected_attestation[
        "execution_capsule_authz_final_authz_release_attestation_hash"
    ]
    assert seal["seal_material_hash"] == ""
    assert seal["passed_component_count"] == 4
    assert seal["mismatch_count"] == 4
    assert seal["component_hash_count"] == 3
    assert seal["seal_material_count"] == 0
    assert seal["seal_request_count"] == 0
    assert seal["execution_permission_count"] == 0
    assert payload["data"]["execution_boundary"]["provider_calls"] == 0
    assert payload["data"]["execution_boundary"]["network_calls"] == 0
    assert payload["data"]["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_release_seal",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_release_seal_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api52-seal-complete",
        include_release_seal=True,
    )
    expected_seal = (
        provider_manual_test_execution_capsule_authz_final_authz_release_seal_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data[
        "manual_provider_test_execution_capsule_authz_final_authz_release_seal"
    ]

    assert seal["status"] == "blocked"
    assert seal["reason"] == (
        "execution_capsule_authz_final_authz_release_seal_execution_closed"
    )
    assert seal["execution_capsule_authz_final_authz_release_seal_hash"] == (
        expected_seal["execution_capsule_authz_final_authz_release_seal_hash"]
    )
    assert seal[
        "execution_capsule_authz_final_authz_release_attestation_hash"
    ] == expected_seal[
        "execution_capsule_authz_final_authz_release_attestation_hash"
    ]
    assert seal["seal_material_hash"] == expected_seal["seal_material_hash"]
    assert seal["claim_boundary_hash"] == expected_seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"] == expected_seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 8
    assert seal["mismatch_count"] == 0
    assert seal["component_hash_count"] == 4
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 1
    assert seal["seal_request_count"] == 1
    assert seal["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API52_SEAL_AUTH_SENTINEL",
        "API52_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API52_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_release_seal",
        "seal_requested",
        "local-no-call-capsule-authz-final-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_without_expected_seal_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api53-final-missing-expected-seal",
        include_final_authorization=True,
    )
    expected_seal = (
        provider_manual_test_execution_capsule_authz_final_authz_release_seal_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_release_seal_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    authorization = payload["data"][
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz"
    ]

    assert authorization["status"] == "blocked"
    assert authorization["reason"] == (
        "expected_execution_capsule_authz_final_authz_release_seal_hash_required"
    )
    assert authorization["execution_capsule_authz_final_authz_final_authz_hash"] == ""
    assert authorization[
        "execution_capsule_authz_final_authz_release_seal_hash"
    ] == expected_seal["execution_capsule_authz_final_authz_release_seal_hash"]
    assert authorization["final_authz_hash"]
    assert authorization["passed_component_count"] == 7
    assert authorization["mismatch_count"] == 1
    assert authorization["component_hash_count"] == 4
    assert authorization["execution_permission_count"] == 0
    assert payload["data"]["execution_boundary"]["provider_calls"] == 0
    assert payload["data"]["execution_boundary"]["network_calls"] == 0
    assert payload["data"]["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API53_FINAL_AUTH_SENTINEL",
        "API53_FINAL_PROVIDER_PAYLOAD_SENTINEL",
        "API53_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-authz-final-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_without_authorization_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api53-final-missing-payload",
        include_release_seal=True,
    )
    expected_seal = (
        provider_manual_test_execution_capsule_authz_final_authz_release_seal_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_release_seal_hash"
    ] = expected_seal["execution_capsule_authz_final_authz_release_seal_hash"]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    authorization = payload["data"][
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz"
    ]

    assert authorization["status"] == "blocked"
    assert authorization["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_required"
    )
    assert authorization["execution_capsule_authz_final_authz_final_authz_hash"] == ""
    assert authorization[
        "execution_capsule_authz_final_authz_release_seal_hash"
    ] == expected_seal["execution_capsule_authz_final_authz_release_seal_hash"]
    assert authorization["final_authz_hash"] == ""
    assert authorization["passed_component_count"] == 4
    assert authorization["mismatch_count"] == 4
    assert authorization["component_hash_count"] == 3
    assert authorization["final_authz_count"] == 0
    assert authorization["authz_request_count"] == 0
    assert authorization["execution_permission_count"] == 0
    assert payload["data"]["execution_boundary"]["provider_calls"] == 0
    assert payload["data"]["execution_boundary"]["network_calls"] == 0
    assert payload["data"]["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api53-final-complete",
        include_final_authorization=True,
    )
    expected_authorization = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    authorization = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz"
    ]

    assert authorization["status"] == "blocked"
    assert authorization["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_execution_closed"
    )
    assert authorization["execution_capsule_authz_final_authz_final_authz_hash"] == (
        expected_authorization[
            "execution_capsule_authz_final_authz_final_authz_hash"
        ]
    )
    assert authorization[
        "execution_capsule_authz_final_authz_release_seal_hash"
    ] == expected_authorization[
        "execution_capsule_authz_final_authz_release_seal_hash"
    ]
    assert authorization["final_authz_hash"] == expected_authorization[
        "final_authz_hash"
    ]
    assert authorization["claim_boundary_hash"] == expected_authorization[
        "claim_boundary_hash"
    ]
    assert authorization["no_call_counters_hash"] == expected_authorization[
        "no_call_counters_hash"
    ]
    assert authorization["component_count"] == 8
    assert authorization["passed_component_count"] == 8
    assert authorization["mismatch_count"] == 0
    assert authorization["component_hash_count"] == 4
    assert authorization["no_call_counter_count"] == 13
    assert authorization["claim_boundary_check_count"] == 3
    assert authorization["final_authz_count"] == 1
    assert authorization["authz_request_count"] == 1
    assert authorization["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API53_FINAL_AUTH_SENTINEL",
        "API53_FINAL_PROVIDER_PAYLOAD_SENTINEL",
        "API53_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-authz-final-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_export_without_expected_final_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api54-export-missing-expected-final",
        include_final_authorization_export=True,
    )
    expected_authorization = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export"
    ]
    read_model = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export_read_model"
    ]

    assert set(export) == {
        "status",
        "reason",
        "execution_capsule_authz_final_authz_final_authz_export_hash",
        "execution_capsule_authz_final_authz_final_authz_hash",
        "export_metadata_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "export_count",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "export_metadata_count",
        "export_request_count",
        "execution_permission_count",
    }
    assert export["status"] == "blocked"
    assert export["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_hash_required"
    )
    assert export["execution_capsule_authz_final_authz_final_authz_export_hash"] == ""
    assert export["execution_capsule_authz_final_authz_final_authz_hash"] == (
        expected_authorization[
            "execution_capsule_authz_final_authz_final_authz_hash"
        ]
    )
    assert export["export_metadata_hash"]
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["export_count"] == 0
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 7
    assert export["mismatch_count"] == 1
    assert export["component_hash_count"] == 4
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 1
    assert export["export_request_count"] == 1
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "blocked"
    assert read_model["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_export_not_available"
    )
    assert (
        read_model[
            "latest_execution_capsule_authz_final_authz_final_authz_export_hash"
        ]
        == ""
    )
    assert read_model["counts"][
        "execution_capsule_authz_final_authz_final_authz_export_count"
    ] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API54_EXPORT_AUTH_SENTINEL",
        "API54_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API54_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_export",
        "export_requested",
        "local-no-call-capsule-authz-final-final-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_export_without_export_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api54-export-missing-payload",
        include_final_authorization=True,
    )
    expected_authorization = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_hash"
    ] = expected_authorization[
        "execution_capsule_authz_final_authz_final_authz_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export"
    ]
    read_model = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export_read_model"
    ]

    assert export["status"] == "blocked"
    assert export["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_export_required"
    )
    assert export["execution_capsule_authz_final_authz_final_authz_export_hash"] == ""
    assert export["execution_capsule_authz_final_authz_final_authz_hash"] == (
        expected_authorization[
            "execution_capsule_authz_final_authz_final_authz_hash"
        ]
    )
    assert export["export_metadata_hash"] == ""
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["export_count"] == 0
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 4
    assert export["mismatch_count"] == 4
    assert export["component_hash_count"] == 3
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 0
    assert export["export_request_count"] == 0
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "blocked"
    assert read_model["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_export_not_available"
    )
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_export",
        "export_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_export_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api54-export-complete",
        include_final_authorization_export=True,
    )
    expected_export = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_export_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export"
    ]
    read_model = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export_read_model"
    ]

    assert export["status"] == "blocked"
    assert export["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_export_execution_closed"
    )
    assert export["execution_capsule_authz_final_authz_final_authz_export_hash"] == (
        expected_export[
            "execution_capsule_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert export["execution_capsule_authz_final_authz_final_authz_hash"] == (
        expected_export["execution_capsule_authz_final_authz_final_authz_hash"]
    )
    assert export["export_metadata_hash"] == expected_export["export_metadata_hash"]
    assert export["claim_boundary_hash"] == expected_export["claim_boundary_hash"]
    assert export["no_call_counters_hash"] == expected_export[
        "no_call_counters_hash"
    ]
    assert export["export_count"] == 1
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 8
    assert export["mismatch_count"] == 0
    assert export["component_hash_count"] == 4
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 1
    assert export["export_request_count"] == 1
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "available"
    assert read_model["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_export_read_model_available"
    )
    assert read_model[
        "latest_execution_capsule_authz_final_authz_final_authz_export_hash"
    ] == expected_export[
        "execution_capsule_authz_final_authz_final_authz_export_hash"
    ]
    assert read_model["counts"][
        "execution_capsule_authz_final_authz_final_authz_export_count"
    ] == 1
    assert read_model["counts"]["component_count"] == 8
    assert read_model["counts"]["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API54_EXPORT_AUTH_SENTINEL",
        "API54_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API54_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_export",
        "export_requested",
        "local-no-call-capsule-authz-final-final-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_handoff_without_expected_export_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api55-handoff-missing-expected-export",
        include_final_authorization_handoff=True,
    )
    expected_export = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_export_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_export_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet"
    ]

    assert set(handoff) == {
        "status",
        "reason",
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash",
        "execution_capsule_authz_final_authz_final_authz_export_hash",
        "execution_capsule_authz_final_authz_final_authz_export_read_model_hash",
        "claim_boundary_hash",
        "no_call_counters_hash",
        "packet_count",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "no_call_counter_count",
        "claim_boundary_check_count",
        "export_read_model_count",
        "handoff_request_count",
        "execution_permission_count",
    }
    assert handoff["status"] == "blocked"
    assert handoff["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_export_hash_required"
    )
    assert (
        handoff["execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"]
        == ""
    )
    assert handoff["execution_capsule_authz_final_authz_final_authz_export_hash"] == (
        expected_export[
            "execution_capsule_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_export_read_model_hash"
        ]
        == expected_export[
            "execution_capsule_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert handoff["claim_boundary_hash"]
    assert handoff["no_call_counters_hash"]
    assert handoff["packet_count"] == 0
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 7
    assert handoff["mismatch_count"] == 1
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API54_EXPORT_AUTH_SENTINEL",
        "API54_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API54_OPERATOR_REF_SENTINEL",
        "API55_HANDOFF_MATERIAL_SENTINEL",
        "API55_HANDOFF_AUTH_SENTINEL",
        "API55_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_handoff_without_packet_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api55-handoff-missing-payload",
        include_final_authorization_export=True,
    )
    expected_export = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_export_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_export_hash"
    ] = expected_export[
        "execution_capsule_authz_final_authz_final_authz_export_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet"
    ]

    assert handoff["status"] == "blocked"
    assert handoff["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_required"
    )
    assert (
        handoff["execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"]
        == ""
    )
    assert handoff["execution_capsule_authz_final_authz_final_authz_export_hash"] == (
        expected_export[
            "execution_capsule_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_export_read_model_hash"
        ]
        == expected_export[
            "execution_capsule_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert handoff["claim_boundary_hash"]
    assert handoff["no_call_counters_hash"]
    assert handoff["packet_count"] == 0
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 5
    assert handoff["mismatch_count"] == 3
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 0
    assert handoff["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_handoff_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api55-handoff-complete",
        include_final_authorization_handoff=True,
    )
    expected_handoff = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet"
    ]

    assert handoff["status"] == "blocked"
    assert handoff["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_execution_closed"
    )
    assert handoff[
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    ] == expected_handoff[
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    ]
    assert handoff["execution_capsule_authz_final_authz_final_authz_export_hash"] == (
        expected_handoff["execution_capsule_authz_final_authz_final_authz_export_hash"]
    )
    assert handoff[
        "execution_capsule_authz_final_authz_final_authz_export_read_model_hash"
    ] == expected_handoff[
        "execution_capsule_authz_final_authz_final_authz_export_read_model_hash"
    ]
    assert handoff["claim_boundary_hash"] == expected_handoff["claim_boundary_hash"]
    assert handoff["no_call_counters_hash"] == expected_handoff[
        "no_call_counters_hash"
    ]
    assert handoff["packet_count"] == 1
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 8
    assert handoff["mismatch_count"] == 0
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API55_HANDOFF_MATERIAL_SENTINEL",
        "API55_HANDOFF_AUTH_SENTINEL",
        "API55_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_review_without_expected_handoff_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api56-review-missing-expected-handoff",
        include_final_authorization_operator_review=True,
    )
    expected_handoff = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review"
    ]

    assert review["status"] == "blocked"
    assert review["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_handoff_packet_hash_required"
    )
    assert review["execution_capsule_authz_final_authz_final_authz_operator_review_hash"] == ""
    assert review[
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    ] == expected_handoff[
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    ]
    assert review["operator_review_hash"]
    assert review["claim_boundary_hash"]
    assert review["no_call_counters_hash"]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 7
    assert review["mismatch_count"] == 1
    assert review["component_hash_count"] == 4
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 1
    assert review["review_request_count"] == 1
    assert review["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API56_REVIEW_AUTH_SENTINEL",
        "API56_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API56_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review",
        "review_requested",
        "local-no-call-capsule-authz-final-final-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_review_without_operator_review_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api56-review-missing-payload",
        include_final_authorization_handoff=True,
    )
    expected_handoff = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    ] = expected_handoff[
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review"
    ]

    assert review["status"] == "blocked"
    assert review["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_operator_review_required"
    )
    assert review["execution_capsule_authz_final_authz_final_authz_operator_review_hash"] == ""
    assert review[
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    ] == expected_handoff[
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    ]
    assert review["operator_review_hash"] == ""
    assert review["claim_boundary_hash"]
    assert review["no_call_counters_hash"]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 4
    assert review["mismatch_count"] == 4
    assert review["component_hash_count"] == 3
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 0
    assert review["review_request_count"] == 0
    assert review["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_operator_review_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api56-review-complete",
        include_final_authorization_operator_review=True,
    )
    expected_review = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review"
    ]

    assert review["status"] == "blocked"
    assert review["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_operator_review_execution_closed"
    )
    assert review[
        "execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    ] == expected_review[
        "execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    ]
    assert review[
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    ] == expected_review[
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    ]
    assert review["operator_review_hash"] == expected_review["operator_review_hash"]
    assert review["claim_boundary_hash"] == expected_review["claim_boundary_hash"]
    assert review["no_call_counters_hash"] == expected_review[
        "no_call_counters_hash"
    ]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 8
    assert review["mismatch_count"] == 0
    assert review["component_hash_count"] == 4
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 1
    assert review["review_request_count"] == 1
    assert review["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API56_REVIEW_AUTH_SENTINEL",
        "API56_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API56_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review",
        "review_requested",
        "local-no-call-capsule-authz-final-final-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_decision_without_expected_review_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api57-decision-missing-expected-review",
        include_final_authorization_operator_decision=True,
    )
    expected_review = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision"
    ]

    assert decision["status"] == "blocked"
    assert decision["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_operator_review_hash_required"
    )
    assert decision[
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ] == ""
    assert decision[
        "execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    ] == expected_review[
        "execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    ]
    assert decision["operator_decision_hash"]
    assert decision["claim_boundary_hash"]
    assert decision["no_call_counters_hash"]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 7
    assert decision["mismatch_count"] == 1
    assert decision["component_hash_count"] == 4
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 1
    assert decision["decision_request_count"] == 1
    assert decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API57_DECISION_AUTH_SENTINEL",
        "API57_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API57_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision",
        "decision_requested",
        "local-no-call-capsule-authz-final-final-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_decision_without_decision_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api57-decision-missing-payload",
        include_final_authorization_operator_review=True,
    )
    expected_review = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    ] = expected_review[
        "execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision"
    ]

    assert decision["status"] == "blocked"
    assert decision["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_operator_decision_required"
    )
    assert decision[
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ] == ""
    assert decision[
        "execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    ] == expected_review[
        "execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    ]
    assert decision["operator_decision_hash"] == ""
    assert decision["claim_boundary_hash"]
    assert decision["no_call_counters_hash"]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 4
    assert decision["mismatch_count"] == 4
    assert decision["component_hash_count"] == 3
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 0
    assert decision["decision_request_count"] == 0
    assert decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_operator_decision_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api57-decision-complete",
        include_final_authorization_operator_decision=True,
    )
    expected_decision = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision"
    ]

    assert decision["status"] == "blocked"
    assert decision["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_operator_decision_execution_closed"
    )
    assert decision[
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ] == expected_decision[
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ]
    assert decision[
        "execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    ] == expected_decision[
        "execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    ]
    assert decision["operator_decision_hash"] == expected_decision[
        "operator_decision_hash"
    ]
    assert decision["claim_boundary_hash"] == expected_decision[
        "claim_boundary_hash"
    ]
    assert decision["no_call_counters_hash"] == expected_decision[
        "no_call_counters_hash"
    ]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 8
    assert decision["mismatch_count"] == 0
    assert decision["component_hash_count"] == 4
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 1
    assert decision["decision_request_count"] == 1
    assert decision["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API57_DECISION_AUTH_SENTINEL",
        "API57_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API57_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision",
        "decision_requested",
        "local-no-call-capsule-authz-final-final-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_attestation_without_expected_decision_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api58-attestation-missing-expected-decision",
        include_final_authorization_release_attestation=True,
    )
    expected_decision = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation"
    ]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_operator_decision_hash_required"
    )
    assert attestation[
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ] == ""
    assert attestation[
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ] == expected_decision[
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ]
    assert attestation["release_attestation_hash"]
    assert attestation["claim_boundary_hash"]
    assert attestation["no_call_counters_hash"]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 7
    assert attestation["mismatch_count"] == 1
    assert attestation["component_hash_count"] == 4
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 1
    assert attestation["attestation_request_count"] == 1
    assert attestation["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API58_ATTESTATION_AUTH_SENTINEL",
        "API58_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API58_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-authz-final-final-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_attestation_without_attestation_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api58-attestation-missing-payload",
        include_final_authorization_operator_decision=True,
    )
    expected_decision = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ] = expected_decision[
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation"
    ]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_release_attestation_required"
    )
    assert attestation[
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ] == ""
    assert attestation[
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ] == expected_decision[
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ]
    assert attestation["release_attestation_hash"] == ""
    assert attestation["claim_boundary_hash"]
    assert attestation["no_call_counters_hash"]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 4
    assert attestation["mismatch_count"] == 4
    assert attestation["component_hash_count"] == 3
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 0
    assert attestation["attestation_request_count"] == 0
    assert attestation["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_release_attestation",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_release_attestation_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api58-attestation-complete",
        include_final_authorization_release_attestation=True,
    )
    expected_attestation = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_attestation_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation"
    ]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_release_attestation_execution_closed"
    )
    assert attestation[
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ] == expected_attestation[
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ]
    assert attestation[
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ] == expected_attestation[
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ]
    assert attestation["release_attestation_hash"] == expected_attestation[
        "release_attestation_hash"
    ]
    assert attestation["claim_boundary_hash"] == expected_attestation[
        "claim_boundary_hash"
    ]
    assert attestation["no_call_counters_hash"] == expected_attestation[
        "no_call_counters_hash"
    ]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 8
    assert attestation["mismatch_count"] == 0
    assert attestation["component_hash_count"] == 4
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 1
    assert attestation["attestation_request_count"] == 1
    assert attestation["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API58_ATTESTATION_AUTH_SENTINEL",
        "API58_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API58_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-authz-final-final-release-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_seal_without_expected_attestation_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api59-seal-missing-expected-attestation",
        include_final_authorization_release_seal=True,
    )
    expected_attestation = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_attestation_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal"
    ]

    assert seal["status"] == "blocked"
    assert seal["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_release_attestation_hash_required"
    )
    assert seal[
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ] == ""
    assert seal[
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ] == expected_attestation[
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ]
    assert seal["seal_material_hash"]
    assert seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 7
    assert seal["mismatch_count"] == 1
    assert seal["component_hash_count"] == 4
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 1
    assert seal["seal_request_count"] == 1
    assert seal["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API59_SEAL_AUTH_SENTINEL",
        "API59_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API59_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal",
        "seal_requested",
        "local-no-call-capsule-authz-final-final-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_seal_without_seal_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api59-seal-missing-payload",
        include_final_authorization_release_attestation=True,
    )
    expected_attestation = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_attestation_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ] = expected_attestation[
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal"
    ]

    assert seal["status"] == "blocked"
    assert seal["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_release_seal_required"
    )
    assert seal[
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ] == ""
    assert seal[
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ] == expected_attestation[
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ]
    assert seal["seal_material_hash"] == ""
    assert seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 4
    assert seal["mismatch_count"] == 4
    assert seal["component_hash_count"] == 3
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 0
    assert seal["seal_request_count"] == 0
    assert seal["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_release_seal_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api59-seal-complete",
        include_final_authorization_release_seal=True,
    )
    expected_seal = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal"
    ]

    assert seal["status"] == "blocked"
    assert seal["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_release_seal_execution_closed"
    )
    assert seal[
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ] == expected_seal[
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ]
    assert seal[
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ] == expected_seal[
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ]
    assert seal["seal_material_hash"] == expected_seal["seal_material_hash"]
    assert seal["claim_boundary_hash"] == expected_seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"] == expected_seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 8
    assert seal["mismatch_count"] == 0
    assert seal["component_hash_count"] == 4
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 1
    assert seal["seal_request_count"] == 1
    assert seal["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API59_SEAL_AUTH_SENTINEL",
        "API59_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API59_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal",
        "seal_requested",
        "local-no-call-capsule-authz-final-final-release-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_without_expected_seal_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api60-final-authz-missing-expected-seal",
        include_final_authorization_final_authorization=True,
    )
    expected_seal = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    authorization = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz"
    ]

    assert authorization["status"] == "blocked"
    assert authorization["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_release_seal_hash_required"
    )
    assert authorization[
        "execution_capsule_authz_final_authz_final_authz_final_authz_hash"
    ] == ""
    assert authorization[
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ] == expected_seal[
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ]
    assert authorization["final_authz_hash"]
    assert authorization["claim_boundary_hash"]
    assert authorization["no_call_counters_hash"]
    assert authorization["component_count"] == 8
    assert authorization["passed_component_count"] == 7
    assert authorization["mismatch_count"] == 1
    assert authorization["component_hash_count"] == 4
    assert authorization["no_call_counter_count"] == 13
    assert authorization["claim_boundary_check_count"] == 3
    assert authorization["final_authz_count"] == 1
    assert authorization["authz_request_count"] == 1
    assert authorization["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API60_FINAL_AUTHZ_AUTH_SENTINEL",
        "API60_FINAL_AUTHZ_PROVIDER_PAYLOAD_SENTINEL",
        "API60_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-authz-final-final-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_without_authorization_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api60-final-authz-missing-payload",
        include_final_authorization_release_seal=True,
    )
    expected_seal = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ] = expected_seal[
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    authorization = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz"
    ]

    assert authorization["status"] == "blocked"
    assert authorization["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_required"
    )
    assert authorization[
        "execution_capsule_authz_final_authz_final_authz_final_authz_hash"
    ] == ""
    assert authorization[
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ] == expected_seal[
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ]
    assert authorization["final_authz_hash"] == ""
    assert authorization["claim_boundary_hash"]
    assert authorization["no_call_counters_hash"]
    assert authorization["component_count"] == 8
    assert authorization["passed_component_count"] == 4
    assert authorization["mismatch_count"] == 4
    assert authorization["component_hash_count"] == 3
    assert authorization["no_call_counter_count"] == 13
    assert authorization["claim_boundary_check_count"] == 3
    assert authorization["final_authz_count"] == 0
    assert authorization["authz_request_count"] == 0
    assert authorization["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization",
        "authorization_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_final_authz_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api60-final-authz-complete",
        include_final_authorization_final_authorization=True,
    )
    expected_authorization = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    authorization = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz"
    ]

    assert authorization["status"] == "blocked"
    assert authorization["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_execution_closed"
    )
    assert authorization[
        "execution_capsule_authz_final_authz_final_authz_final_authz_hash"
    ] == expected_authorization[
        "execution_capsule_authz_final_authz_final_authz_final_authz_hash"
    ]
    assert authorization[
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ] == expected_authorization[
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ]
    assert authorization["final_authz_hash"] == expected_authorization["final_authz_hash"]
    assert authorization["claim_boundary_hash"] == expected_authorization[
        "claim_boundary_hash"
    ]
    assert authorization["no_call_counters_hash"] == expected_authorization[
        "no_call_counters_hash"
    ]
    assert authorization["component_count"] == 8
    assert authorization["passed_component_count"] == 8
    assert authorization["mismatch_count"] == 0
    assert authorization["component_hash_count"] == 4
    assert authorization["no_call_counter_count"] == 13
    assert authorization["claim_boundary_check_count"] == 3
    assert authorization["final_authz_count"] == 1
    assert authorization["authz_request_count"] == 1
    assert authorization["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API60_FINAL_AUTHZ_AUTH_SENTINEL",
        "API60_FINAL_AUTHZ_PROVIDER_PAYLOAD_SENTINEL",
        "API60_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-authz-final-final-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_export_without_expected_final_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api61-final-authz-export-missing-expected",
        include_final_authorization_final_authorization_export=True,
    )
    expected_authorization = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export"
    ]
    read_model = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model"
    ]

    assert export["status"] == "blocked"
    assert export["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_hash_required"
    )
    assert (
        export["execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"]
        == ""
    )
    assert (
        export["execution_capsule_authz_final_authz_final_authz_final_authz_hash"]
        == expected_authorization[
            "execution_capsule_authz_final_authz_final_authz_final_authz_hash"
        ]
    )
    assert export["export_metadata_hash"]
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 7
    assert export["mismatch_count"] == 1
    assert export["component_hash_count"] == 4
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 1
    assert export["export_request_count"] == 1
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "blocked"
    assert read_model["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_export_not_available"
    )
    assert (
        read_model[
            "latest_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
        == ""
    )
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API61_EXPORT_AUTH_SENTINEL",
        "API61_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API61_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_export",
        "export_requested",
        "local-no-call-capsule-authz-final-final-final-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_export_without_export_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api61-final-authz-export-missing-payload",
        include_final_authorization_final_authorization=True,
    )
    expected_authorization = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_hash"
    ] = expected_authorization[
        "execution_capsule_authz_final_authz_final_authz_final_authz_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export"
    ]
    read_model = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model"
    ]

    assert export["status"] == "blocked"
    assert export["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_export_required"
    )
    assert (
        export["execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"]
        == ""
    )
    assert (
        export["execution_capsule_authz_final_authz_final_authz_final_authz_hash"]
        == expected_authorization[
            "execution_capsule_authz_final_authz_final_authz_final_authz_hash"
        ]
    )
    assert export["export_metadata_hash"] == ""
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 4
    assert export["mismatch_count"] == 4
    assert export["component_hash_count"] == 3
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 0
    assert export["export_request_count"] == 0
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "blocked"
    assert read_model["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_export_not_available"
    )
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_export",
        "export_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_final_authz_export_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api61-final-authz-export-complete",
        include_final_authorization_final_authorization_export=True,
    )
    expected_export = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_export_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export"
    ]
    read_model = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model"
    ]

    assert export["status"] == "blocked"
    assert export["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_export_execution_closed"
    )
    assert (
        export["execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"]
        == expected_export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert (
        export["execution_capsule_authz_final_authz_final_authz_final_authz_hash"]
        == expected_export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_hash"
        ]
    )
    assert export["export_metadata_hash"] == expected_export["export_metadata_hash"]
    assert export["claim_boundary_hash"] == expected_export["claim_boundary_hash"]
    assert export["no_call_counters_hash"] == expected_export[
        "no_call_counters_hash"
    ]
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 8
    assert export["mismatch_count"] == 0
    assert export["component_hash_count"] == 4
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 1
    assert export["export_request_count"] == 1
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "available"
    assert read_model["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_available"
    )
    assert (
        read_model[
            "latest_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
        == export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert (
        read_model["counts"][
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_count"
        ]
        == 1
    )
    assert read_model["counts"]["component_count"] == 8
    assert read_model["counts"]["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API61_EXPORT_AUTH_SENTINEL",
        "API61_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API61_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_export",
        "export_requested",
        "local-no-call-capsule-authz-final-final-final-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_without_expected_export_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api62-final-authz-handoff-missing-expected",
        include_final_authorization_final_authorization_handoff=True,
    )
    expected_export = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_export_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet"
    ]

    assert handoff["status"] == "blocked"
    assert handoff["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash_required"
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ]
        == ""
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
        == expected_export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_hash"
        ]
        == expected_export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert handoff["claim_boundary_hash"]
    assert handoff["no_call_counters_hash"]
    assert handoff["packet_count"] == 0
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 7
    assert handoff["mismatch_count"] == 1
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API62_HANDOFF_AUTH_SENTINEL",
        "API62_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "API62_HANDOFF_MATERIAL_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet",
        "handoff_requested",
        "handoff_material",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_without_packet_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api62-final-authz-handoff-missing-payload",
        include_final_authorization_final_authorization_export=True,
    )
    expected_export = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_export_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
    ] = expected_export[
        "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet"
    ]

    assert handoff["status"] == "blocked"
    assert handoff["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_required"
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ]
        == ""
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
        == expected_export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_hash"
        ]
        == expected_export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert handoff["claim_boundary_hash"]
    assert handoff["no_call_counters_hash"]
    assert handoff["packet_count"] == 0
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 5
    assert handoff["mismatch_count"] == 3
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 0
    assert handoff["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet",
        "handoff_requested",
        "handoff_material",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api62-final-authz-handoff-complete",
        include_final_authorization_final_authorization_handoff=True,
    )
    expected_handoff = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    handoff = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet"
    ]

    assert handoff["status"] == "blocked"
    assert handoff["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_execution_closed"
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ]
        == expected_handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ]
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
        == expected_handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_hash"
        ]
        == expected_handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_hash"
        ]
    )
    assert handoff["claim_boundary_hash"] == expected_handoff["claim_boundary_hash"]
    assert handoff["no_call_counters_hash"] == expected_handoff[
        "no_call_counters_hash"
    ]
    assert handoff["packet_count"] == 1
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 8
    assert handoff["mismatch_count"] == 0
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API62_HANDOFF_AUTH_SENTINEL",
        "API62_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "API62_HANDOFF_MATERIAL_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet",
        "handoff_requested",
        "handoff_material",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_review_without_expected_handoff_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api63-review-missing-expected-handoff",
        include_final_authorization_final_authorization_operator_review=True,
    )
    expected_handoff = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review"
    ]

    assert review["status"] == "blocked"
    assert review["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash_required"
    )
    assert (
        review[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ]
        == ""
    )
    assert (
        review[
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ]
        == expected_handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ]
    )
    assert review["operator_review_hash"]
    assert review["claim_boundary_hash"]
    assert review["no_call_counters_hash"]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 7
    assert review["mismatch_count"] == 1
    assert review["component_hash_count"] == 4
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 1
    assert review["review_request_count"] == 1
    assert review["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API63_REVIEW_AUTH_SENTINEL",
        "API63_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API63_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review",
        "review_requested",
        "local-no-call-capsule-authz-final-final-final-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_review_without_operator_review_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api63-review-missing-payload",
        include_final_authorization_final_authorization_handoff=True,
    )
    expected_handoff = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
    ] = expected_handoff[
        "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review"
    ]

    assert review["status"] == "blocked"
    assert review["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_required"
    )
    assert (
        review[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ]
        == ""
    )
    assert (
        review[
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ]
        == expected_handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ]
    )
    assert review["operator_review_hash"] == ""
    assert review["claim_boundary_hash"]
    assert review["no_call_counters_hash"]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 4
    assert review["mismatch_count"] == 4
    assert review["component_hash_count"] == 3
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 0
    assert review["review_request_count"] == 0
    assert review["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api63-review-complete",
        include_final_authorization_final_authorization_operator_review=True,
    )
    expected_review = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review"
    ]

    assert review["status"] == "blocked"
    assert review["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_execution_closed"
    )
    assert (
        review[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ]
        == expected_review[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ]
    )
    assert (
        review[
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ]
        == expected_review[
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ]
    )
    assert review["operator_review_hash"] == expected_review["operator_review_hash"]
    assert review["claim_boundary_hash"] == expected_review["claim_boundary_hash"]
    assert review["no_call_counters_hash"] == expected_review[
        "no_call_counters_hash"
    ]
    assert review["component_count"] == 8
    assert review["passed_component_count"] == 8
    assert review["mismatch_count"] == 0
    assert review["component_hash_count"] == 4
    assert review["no_call_counter_count"] == 13
    assert review["claim_boundary_check_count"] == 3
    assert review["operator_review_count"] == 1
    assert review["review_request_count"] == 1
    assert review["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API63_REVIEW_AUTH_SENTINEL",
        "API63_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API63_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review",
        "review_requested",
        "local-no-call-capsule-authz-final-final-final-reviewed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_decision_without_expected_review_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api64-decision-missing-expected-review",
        include_final_authorization_final_authorization_operator_decision=True,
    )
    expected_review = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision"
    ]

    assert decision["status"] == "blocked"
    assert decision["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash_required"
    )
    assert (
        decision[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ]
        == ""
    )
    assert (
        decision[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ]
        == expected_review[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ]
    )
    assert decision["operator_decision_hash"]
    assert decision["claim_boundary_hash"]
    assert decision["no_call_counters_hash"]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 7
    assert decision["mismatch_count"] == 1
    assert decision["component_hash_count"] == 4
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 1
    assert decision["decision_request_count"] == 1
    assert decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API64_DECISION_AUTH_SENTINEL",
        "API64_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API64_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision",
        "decision_requested",
        "local-no-call-capsule-authz-final-final-final-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_decision_without_operator_decision_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api64-decision-missing-payload",
        include_final_authorization_final_authorization_operator_review=True,
    )
    expected_review = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
    ] = expected_review[
        "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision"
    ]

    assert decision["status"] == "blocked"
    assert decision["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_required"
    )
    assert (
        decision[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ]
        == ""
    )
    assert (
        decision[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ]
        == expected_review[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ]
    )
    assert decision["operator_decision_hash"] == ""
    assert decision["claim_boundary_hash"]
    assert decision["no_call_counters_hash"]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 4
    assert decision["mismatch_count"] == 4
    assert decision["component_hash_count"] == 3
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 0
    assert decision["decision_request_count"] == 0
    assert decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api64-decision-complete",
        include_final_authorization_final_authorization_operator_decision=True,
    )
    expected_decision = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    decision = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision"
    ]

    assert decision["status"] == "blocked"
    assert decision["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_execution_closed"
    )
    assert (
        decision[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ]
        == expected_decision[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ]
    )
    assert (
        decision[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ]
        == expected_decision[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ]
    )
    assert decision["operator_decision_hash"] == expected_decision[
        "operator_decision_hash"
    ]
    assert decision["claim_boundary_hash"] == expected_decision["claim_boundary_hash"]
    assert decision["no_call_counters_hash"] == expected_decision[
        "no_call_counters_hash"
    ]
    assert decision["component_count"] == 8
    assert decision["passed_component_count"] == 8
    assert decision["mismatch_count"] == 0
    assert decision["component_hash_count"] == 4
    assert decision["no_call_counter_count"] == 13
    assert decision["claim_boundary_check_count"] == 3
    assert decision["operator_decision_count"] == 1
    assert decision["decision_request_count"] == 1
    assert decision["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API64_DECISION_AUTH_SENTINEL",
        "API64_DECISION_PROVIDER_PAYLOAD_SENTINEL",
        "API64_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision",
        "decision_requested",
        "local-no-call-capsule-authz-final-final-final-decided",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_attestation_without_expected_decision_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api65-attestation-missing-expected-decision",
        include_final_authorization_final_authorization_release_attestation=True,
    )
    expected_decision = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation"
    ]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash_required"
    )
    assert (
        attestation[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ]
        == ""
    )
    assert (
        attestation[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ]
        == expected_decision[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ]
    )
    assert attestation["release_attestation_hash"]
    assert attestation["claim_boundary_hash"]
    assert attestation["no_call_counters_hash"]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 7
    assert attestation["mismatch_count"] == 1
    assert attestation["component_hash_count"] == 4
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 1
    assert attestation["attestation_request_count"] == 1
    assert attestation["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API65_ATTESTATION_AUTH_SENTINEL",
        "API65_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API65_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-authz-final-final-final-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_attestation_without_attestation_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api65-attestation-missing-payload",
        include_final_authorization_final_authorization_operator_decision=True,
    )
    expected_decision = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
    ] = expected_decision[
        "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation"
    ]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_required"
    )
    assert (
        attestation[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ]
        == ""
    )
    assert (
        attestation[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ]
        == expected_decision[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ]
    )
    assert attestation["release_attestation_hash"] == ""
    assert attestation["claim_boundary_hash"]
    assert attestation["no_call_counters_hash"]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 4
    assert attestation["mismatch_count"] == 4
    assert attestation["component_hash_count"] == 3
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 0
    assert attestation["attestation_request_count"] == 0
    assert attestation["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api65-attestation-complete",
        include_final_authorization_final_authorization_release_attestation=True,
    )
    expected_attestation = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    attestation = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation"
    ]

    assert attestation["status"] == "blocked"
    assert attestation["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_execution_closed"
    )
    assert (
        attestation[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ]
        == expected_attestation[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ]
    )
    assert (
        attestation[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ]
        == expected_attestation[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ]
    )
    assert attestation["release_attestation_hash"] == expected_attestation[
        "release_attestation_hash"
    ]
    assert attestation["claim_boundary_hash"] == expected_attestation[
        "claim_boundary_hash"
    ]
    assert attestation["no_call_counters_hash"] == expected_attestation[
        "no_call_counters_hash"
    ]
    assert attestation["component_count"] == 8
    assert attestation["passed_component_count"] == 8
    assert attestation["mismatch_count"] == 0
    assert attestation["component_hash_count"] == 4
    assert attestation["no_call_counter_count"] == 13
    assert attestation["claim_boundary_check_count"] == 3
    assert attestation["release_attestation_count"] == 1
    assert attestation["attestation_request_count"] == 1
    assert attestation["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API65_ATTESTATION_AUTH_SENTINEL",
        "API65_ATTESTATION_PROVIDER_PAYLOAD_SENTINEL",
        "API65_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation",
        "attestation_requested",
        "local-no-call-capsule-authz-final-final-final-attested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_seal_without_expected_attestation_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api66-seal-missing-expected-attestation",
        include_final_authorization_final_authorization_release_seal=True,
    )
    expected_attestation = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal"
    ]

    assert seal["status"] == "blocked"
    assert seal["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash_required"
    )
    assert seal[
        "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
    ] == ""
    assert (
        seal[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ]
        == expected_attestation[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ]
    )
    assert seal["seal_material_hash"]
    assert seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 7
    assert seal["mismatch_count"] == 1
    assert seal["component_hash_count"] == 4
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 1
    assert seal["seal_request_count"] == 1
    assert seal["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API66_SEAL_AUTH_SENTINEL",
        "API66_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API66_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal",
        "seal_requested",
        "local-no-call-capsule-authz-final-final-final-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_seal_without_seal_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api66-seal-missing-payload",
        include_final_authorization_final_authorization_release_attestation=True,
    )
    expected_attestation = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
    ] = expected_attestation[
        "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal"
    ]

    assert seal["status"] == "blocked"
    assert seal["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_required"
    )
    assert seal[
        "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
    ] == ""
    assert (
        seal[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ]
        == expected_attestation[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ]
    )
    assert seal["seal_material_hash"] == ""
    assert seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 4
    assert seal["mismatch_count"] == 4
    assert seal["component_hash_count"] == 3
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 0
    assert seal["seal_request_count"] == 0
    assert seal["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal",
        "seal_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api66-seal-complete",
        include_final_authorization_final_authorization_release_seal=True,
    )
    expected_seal = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    seal = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal"
    ]

    assert seal["status"] == "blocked"
    assert seal["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_execution_closed"
    )
    assert (
        seal[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
        ]
        == expected_seal[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
        ]
    )
    assert (
        seal[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ]
        == expected_seal[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ]
    )
    assert seal["seal_material_hash"] == expected_seal["seal_material_hash"]
    assert seal["claim_boundary_hash"] == expected_seal["claim_boundary_hash"]
    assert seal["no_call_counters_hash"] == expected_seal["no_call_counters_hash"]
    assert seal["component_count"] == 8
    assert seal["passed_component_count"] == 8
    assert seal["mismatch_count"] == 0
    assert seal["component_hash_count"] == 4
    assert seal["no_call_counter_count"] == 13
    assert seal["claim_boundary_check_count"] == 3
    assert seal["seal_material_count"] == 1
    assert seal["seal_request_count"] == 1
    assert seal["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API66_SEAL_AUTH_SENTINEL",
        "API66_SEAL_PROVIDER_PAYLOAD_SENTINEL",
        "API66_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal",
        "seal_requested",
        "local-no-call-capsule-authz-final-final-final-sealed",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_without_expected_release_seal_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api67-final-authz-missing-expected-seal",
        include_final_authorization_final_authorization_final_authorization=True,
    )
    expected_seal = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    final_authz = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz"
    ]

    assert final_authz["status"] == "blocked"
    assert final_authz["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash_required"
    )
    assert final_authz[
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
    ] == ""
    assert (
        final_authz[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
        ]
        == expected_seal[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
        ]
    )
    assert final_authz["final_authz_hash"]
    assert final_authz["claim_boundary_hash"]
    assert final_authz["no_call_counters_hash"]
    assert final_authz["component_count"] == 8
    assert final_authz["passed_component_count"] == 7
    assert final_authz["mismatch_count"] == 1
    assert final_authz["component_hash_count"] == 4
    assert final_authz["no_call_counter_count"] == 13
    assert final_authz["claim_boundary_check_count"] == 3
    assert final_authz["final_authz_count"] == 1
    assert final_authz["authz_request_count"] == 1
    assert final_authz["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API67_AUTH_SENTINEL",
        "API67_PROVIDER_PAYLOAD_SENTINEL",
        "API67_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-authz-final-final-final-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_without_final_authorization_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api67-final-authz-missing-payload",
        include_final_authorization_final_authorization_release_seal=True,
    )
    expected_seal = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
    ] = expected_seal[
        "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    final_authz = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz"
    ]

    assert final_authz["status"] == "blocked"
    assert final_authz["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_required"
    )
    assert final_authz[
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
    ] == ""
    assert (
        final_authz[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
        ]
        == expected_seal[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
        ]
    )
    assert final_authz["final_authz_hash"] == ""
    assert final_authz["claim_boundary_hash"]
    assert final_authz["no_call_counters_hash"]
    assert final_authz["component_count"] == 8
    assert final_authz["passed_component_count"] == 4
    assert final_authz["mismatch_count"] == 4
    assert final_authz["component_hash_count"] == 3
    assert final_authz["no_call_counter_count"] == 13
    assert final_authz["claim_boundary_check_count"] == 3
    assert final_authz["final_authz_count"] == 0
    assert final_authz["authz_request_count"] == 0
    assert final_authz["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization",
        "authorization_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api67-final-authz-complete",
        include_final_authorization_final_authorization_final_authorization=True,
    )
    expected_final_authz = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    final_authz = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz"
    ]

    assert final_authz["status"] == "blocked"
    assert final_authz["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_execution_closed"
    )
    assert (
        final_authz[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
        ]
        == expected_final_authz[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
        ]
    )
    assert (
        final_authz[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
        ]
        == expected_final_authz[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
        ]
    )
    assert final_authz["final_authz_hash"] == expected_final_authz["final_authz_hash"]
    assert final_authz["claim_boundary_hash"] == expected_final_authz["claim_boundary_hash"]
    assert final_authz["no_call_counters_hash"] == expected_final_authz[
        "no_call_counters_hash"
    ]
    assert final_authz["component_count"] == 8
    assert final_authz["passed_component_count"] == 8
    assert final_authz["mismatch_count"] == 0
    assert final_authz["component_hash_count"] == 4
    assert final_authz["no_call_counter_count"] == 13
    assert final_authz["claim_boundary_check_count"] == 3
    assert final_authz["final_authz_count"] == 1
    assert final_authz["authz_request_count"] == 1
    assert final_authz["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API67_AUTH_SENTINEL",
        "API67_PROVIDER_PAYLOAD_SENTINEL",
        "API67_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization",
        "authorization_requested",
        "local-no-call-capsule-authz-final-final-final-final-authorized",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_without_expected_final_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api68-export-missing-expected-final",
        include_final_authorization_final_authorization_final_authorization_export=True,
    )
    expected_final_authz = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export"
    ]

    assert export["status"] == "blocked"
    assert export["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash_required"
    )
    assert (
        export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ]
        == ""
    )
    assert (
        export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
        ]
        == expected_final_authz[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
        ]
    )
    assert export["export_metadata_hash"]
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 7
    assert export["mismatch_count"] == 1
    assert export["component_hash_count"] == 4
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_count"] == 0
    assert export["export_metadata_count"] == 1
    assert export["export_request_count"] == 1
    assert export["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API68_EXPORT_AUTH_SENTINEL",
        "API68_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API68_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export",
        "export_requested",
        "local-no-call-capsule-authz-final-final-final-final-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_without_export_payload(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api68-export-missing-payload",
        include_final_authorization_final_authorization_final_authorization=True,
    )
    expected_final_authz = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_summary(
            request_payload
        )
    )
    request_payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
    ] = expected_final_authz[
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
    ]

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export"
    ]

    assert export["status"] == "blocked"
    assert export["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_required"
    )
    assert (
        export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ]
        == ""
    )
    assert (
        export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
        ]
        == expected_final_authz[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
        ]
    )
    assert export["export_metadata_hash"] == ""
    assert export["claim_boundary_hash"]
    assert export["no_call_counters_hash"]
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 4
    assert export["mismatch_count"] == 4
    assert export["component_hash_count"] == 3
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_count"] == 0
    assert export["export_metadata_count"] == 0
    assert export["export_request_count"] == 0
    assert export["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export",
        "export_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api68-export-complete",
        include_final_authorization_final_authorization_final_authorization_export=True,
    )
    expected_export = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export_summary(
            request_payload
        )
    )
    expected_read_model = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export_read_model_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export"
    ]
    read_model = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model"
    ]

    assert export["status"] == "blocked"
    assert export["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_execution_closed"
    )
    assert (
        export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ]
        == expected_export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert (
        export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
        ]
        == expected_export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
        ]
    )
    assert export["export_metadata_hash"] == expected_export["export_metadata_hash"]
    assert export["claim_boundary_hash"] == expected_export["claim_boundary_hash"]
    assert export["no_call_counters_hash"] == expected_export["no_call_counters_hash"]
    assert export["export_count"] == 1
    assert export["component_count"] == 8
    assert export["passed_component_count"] == 8
    assert export["mismatch_count"] == 0
    assert export["component_hash_count"] == 4
    assert export["no_call_counter_count"] == 13
    assert export["claim_boundary_check_count"] == 3
    assert export["export_metadata_count"] == 1
    assert export["export_request_count"] == 1
    assert export["execution_permission_count"] == 0
    assert read_model["status"] == "available"
    assert read_model["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model_available"
    )
    assert read_model == expected_read_model
    assert (
        read_model[
            "latest_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ]
        == export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert (
        read_model["counts"][
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_count"
        ]
        == 1
    )
    assert read_model["counts"]["component_count"] == 8
    assert read_model["counts"]["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API68_EXPORT_AUTH_SENTINEL",
        "API68_EXPORT_PROVIDER_PAYLOAD_SENTINEL",
        "API68_OPERATOR_REF_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export",
        "export_requested",
        "local-no-call-capsule-authz-final-final-final-final-exported",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_without_expected_export_hash(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api69-handoff-missing-expected-export",
        include_final_authorization_final_authorization_final_authorization_handoff=True,
    )
    expected_export = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export_summary(
            request_payload
        )
    )
    request_payload.pop(
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    handoff = payload["data"][
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_packet"
    ]

    assert handoff["status"] == "blocked"
    assert handoff["reason"] == (
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash_required"
    )
    assert handoff[
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
    ] == ""
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ]
        == expected_export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert handoff["packet_count"] == 0
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 7
    assert handoff["mismatch_count"] == 1
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert payload["data"]["execution_boundary"]["provider_calls"] == 0
    assert payload["data"]["execution_boundary"]["network_calls"] == 0
    assert payload["data"]["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API69_HANDOFF_AUTH_SENTINEL",
        "API69_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_on_export_hash_mismatch(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api69-handoff-hash-mismatch",
        include_final_authorization_final_authorization_final_authorization_handoff=True,
    )
    request_payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_handoff_packet"
    ][
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
    ] = "wrong-export-hash"

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    handoff = payload["data"][
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_packet"
    ]

    assert handoff["status"] == "blocked"
    assert handoff["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_packet_hash_mismatch"
    )
    assert handoff[
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
    ] == ""
    assert handoff["packet_count"] == 0
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 7
    assert handoff["mismatch_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert payload["data"]["execution_boundary"]["provider_calls"] == 0
    assert payload["data"]["execution_boundary"]["network_calls"] == 0
    assert payload["data"]["execution_boundary"]["solar_live_api_calls"] == 0


def test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_but_keeps_execution_disabled(
    tmp_path,
):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _final_authz_decision_precheck_payload(
        "run-api69-handoff-complete",
        include_final_authorization_final_authorization_final_authorization_handoff=True,
    )
    expected_handoff = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_handoff_packet_summary(
            request_payload
        )
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    export = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export"
    ]
    read_model = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model"
    ]
    handoff = data[
        "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_packet"
    ]

    assert handoff["status"] == "blocked"
    assert handoff["reason"] == (
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_packet_execution_closed"
    )
    assert handoff == expected_handoff
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ]
        == export[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert (
        handoff[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model_hash"
        ]
        == read_model[
            "latest_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    assert handoff["claim_boundary_hash"]
    assert handoff["no_call_counters_hash"]
    assert handoff["packet_count"] == 1
    assert handoff["component_count"] == 8
    assert handoff["passed_component_count"] == 8
    assert handoff["mismatch_count"] == 0
    assert handoff["component_hash_count"] == 4
    assert handoff["no_call_counter_count"] == 13
    assert handoff["claim_boundary_check_count"] == 3
    assert handoff["export_read_model_count"] == 1
    assert handoff["handoff_request_count"] == 1
    assert handoff["execution_permission_count"] == 0
    assert data["provider_envelope_admission"]["adapter_reached"] is True
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API69_HANDOFF_AUTH_SENTINEL",
        "API69_HANDOFF_PROVIDER_PAYLOAD_SENTINEL",
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_handoff_packet",
        "handoff_requested",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_represents_reject_and_defer_decisions(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )

    for decision, expected_reason, count_field in (
        ("reject", "readiness_rejected", "reject_decision_count"),
        ("defer", "readiness_deferred", "defer_decision_count"),
    ):
        request_payload = _provider_envelope_precheck_payload(
            run_id=f"run-api-envelope-readiness-{decision}",
            include_manual_test_proposal=True,
            manual_test_executor_enable=True,
            include_one_shot_live_permission=True,
            include_readiness_decision=True,
            readiness_decision=decision,
        )
        response = client.post(
            "/api/v1/admissions/provider/envelope/precheck",
            json=request_payload,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        readiness_decision = data["manual_provider_test_readiness_decision"]

        assert readiness_decision["status"] == "blocked"
        assert readiness_decision["reason"] == expected_reason
        assert readiness_decision["readiness_decision_hash"]
        assert readiness_decision["decision_count"] == 1
        assert readiness_decision[count_field] == 1
        assert readiness_decision["mismatch_count"] == 0
        assert readiness_decision["execution_permission_count"] == 0
        assert data["execution_boundary"]["provider_calls"] == 0
        assert data["execution_boundary"]["network_calls"] == 0
        assert data["execution_boundary"]["solar_live_api_calls"] == 0


def test_provider_envelope_precheck_api_blocks_missing_store_before_adapter():
    client = TestClient(create_app())
    request_payload = _provider_envelope_precheck_payload(run_id="run-api-envelope-missing")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert data["provider_envelope_admission"]["status"] == "blocked"
    assert data["provider_envelope_admission"]["adapter_reached"] is False
    assert data["repository_boundary"]["provider_envelope_backend"] == "unconfigured"
    assert checks["provider_envelope_repository_configured"] is False
    assert data["execution_boundary"]["adapter_invocation_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert request_payload["approval"]["nonce"] not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_provider_envelope_precheck_api_blocks_corrupted_store_without_raw_echo(tmp_path):
    (tmp_path / "provider-envelopes.sqlite3").write_text(
        "not a sqlite database",
        encoding="utf-8",
    )
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(run_id="run-api-envelope-corrupt")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert checks["provider_envelope_repository_available"] is False
    assert data["provider_envelope_admission"]["adapter_reached"] is False
    assert data["execution_boundary"]["adapter_invocation_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert "not a sqlite database" not in serialized
    assert str(tmp_path) not in serialized
    assert request_payload["approval"]["nonce"] not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_runs_fixture_path_does_not_touch_provider_envelope_store(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )

    response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build fixture path without provider envelope store writes",
            "target_user": "fixture-envelope-owner@example.com",
            "product_type": "fixture provider envelope boundary",
            "constraints": ["keep provider envelope path separate"],
            "success_criteria": ["provider envelope db is not created"],
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]

    assert data["runtime_mode"] == "fixture"
    assert data["fixture_mode"] is True
    assert data["durable_user_approval"] is False
    assert not (tmp_path / "provider-envelopes.sqlite3").exists()


def test_fake_admission_api_rejects_fixture_or_synthetic_approval_path_without_raw_echo():
    client = TestClient(create_app())
    payload = _provider_admission_payload()
    payload["approval_lifecycle"] = "synthetic"
    payload["fixture_mode"] = True

    response = client.post("/api/v1/admissions/provider/fake", json=payload)
    serialized = _serialized(response.json())

    assert response.status_code == 409
    assert "durable" in serialized or "fixture approval path" in serialized
    assert payload["approval"]["nonce"] not in serialized
    assert payload["approval"]["signature_id"] not in serialized
    assert payload["approval"]["signed_contract_hash"] not in serialized

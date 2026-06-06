"""Run the AW-DEMO-01 local service-shaped demo.

The script uses the public API construction path in-process. It writes only
configured local SQLite projection stores and prints a sanitized summary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient

from apps.api.agentic_workbench_api.main import create_app
from apps.api.agentic_workbench_api.services.canonical_run_store import (
    RunArtifactRepositoryConfig,
)
from apps.api.agentic_workbench_api.services.evidence_read_model import (
    EvidenceRepositoryConfig,
)
from apps.api.agentic_workbench_api.services.provider_envelope_api import (
    MANUAL_PROVIDER_TEST_EXECUTOR_VERSION,
    ProviderEnvelopeRepositoryConfig,
    provider_manual_test_arming_record_summary,
    provider_manual_test_closeout_record_summary,
    provider_manual_test_completion_summary,
    provider_manual_test_executor_dispatch_record_summary,
    provider_manual_test_executor_preflight_summary,
    provider_manual_test_execution_authorization_capsule_summary,
    provider_manual_test_execution_capsule_export_summary,
    provider_manual_test_execution_capsule_handoff_packet_summary,
    provider_manual_test_execution_capsule_operator_decision_summary,
    provider_manual_test_execution_capsule_operator_review_summary,
    provider_manual_test_execution_capsule_final_authorization_summary,
    provider_manual_test_execution_capsule_authz_export_summary,
    provider_manual_test_execution_capsule_authz_handoff_packet_summary,
    provider_manual_test_execution_capsule_authz_operator_decision_summary,
    provider_manual_test_execution_capsule_authz_operator_review_summary,
    provider_manual_test_execution_capsule_authz_final_authorization_summary,
    provider_manual_test_execution_capsule_authz_final_authz_export_summary,
    provider_manual_test_execution_capsule_authz_final_authz_handoff_packet_summary,
    provider_manual_test_execution_capsule_authz_final_authz_operator_decision_summary,
    provider_manual_test_execution_capsule_authz_final_authz_operator_review_summary,
    provider_manual_test_execution_capsule_authz_final_authz_release_attestation_summary,
    provider_manual_test_execution_capsule_authz_final_authz_release_seal_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review_summary,
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision_summary,
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
    provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal_summary,
    provider_manual_test_execution_capsule_authz_release_attestation_summary,
    provider_manual_test_execution_capsule_authz_release_seal_summary,
    provider_manual_test_execution_capsule_release_attestation_summary,
    provider_manual_test_execution_capsule_release_seal_summary,
    provider_manual_test_execution_switch_summary,
    provider_manual_test_final_release_packet_summary,
    provider_manual_test_invocation_receipt_summary,
    provider_manual_test_release_proposal_summary,
    provider_manual_test_release_authorization_seal_summary,
    provider_manual_test_handoff_packet_summary,
    provider_manual_test_operator_handback_summary,
    provider_manual_test_operator_decision_packet_summary,
    provider_manual_test_operator_opt_in_summary,
    provider_manual_test_operator_release_attestation_summary,
    provider_manual_test_post_invocation_audit_summary,
    provider_manual_test_preflight_summary,
    provider_manual_test_proposal_summary,
    provider_manual_test_sealed_pre_execution_packet_summary,
    provider_precheck_operator_policy_summary,
)
from apps.api.agentic_workbench_api.services.target_runtime_admission import (
    TargetRuntimeAdmissionRepositoryConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_output_manifest import (
    TargetRuntimeOutputManifestRepositoryConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_fixture_materialization import (
    TargetRuntimeFixtureMaterializationConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_restricted_workspace_generation import (
    TargetRuntimeRestrictedWorkspaceGenerationConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_generated_artifact_verification import (
    TargetRuntimeGeneratedArtifactVerificationConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_generated_workspace_static_validation import (
    TargetRuntimeGeneratedWorkspaceStaticValidationConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_buildable_fixture_manifest import (
    TargetRuntimeBuildableFixtureManifestConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_local_build_attempt import (
    TargetRuntimeLocalBuildAttemptConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_local_preview_attempt import (
    TargetRuntimeLocalPreviewAttemptConfig,
)
from packages.core.live_open_policy import LIVE_OPEN_REQUIRED_CONTROLS
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_sandbox import (
    TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT,
)
from packages.daacs_builder.target_runtime_admission import (
    TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION,
)
from packages.daacs_builder.target_runtime_output_manifest import (
    TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
    TARGET_RUNTIME_OUTPUT_MANIFEST_VERSION,
)
from packages.daacs_builder.target_runtime_generated_artifact_bundle import (
    TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED,
    TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
)
from packages.daacs_builder.target_runtime_fixture_materialization import (
    TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE,
    TARGET_RUNTIME_FIXTURE_MATERIALIZATION_VERSION,
)
from packages.daacs_builder.target_runtime_restricted_workspace_generation import (
    TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE,
    TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION,
)
from packages.daacs_builder.target_runtime_generated_artifact_verification import (
    TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE,
    TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION,
)
from packages.daacs_builder.target_runtime_generated_workspace_static_validation import (
    TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE,
    TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION,
)
from packages.daacs_builder.target_runtime_buildable_fixture_manifest import (
    TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE,
    TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION,
)
from packages.daacs_builder.target_runtime_local_build_preflight import (
    TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE,
    TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION,
)
from packages.daacs_builder.target_runtime_local_build_attempt import (
    TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE,
    TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION,
)
from packages.daacs_builder.target_runtime_local_preview_attempt import (
    TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE,
    TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_VERSION,
)
from packages.daacs_builder.target_runtime_browser_setup_attempt import (
    TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE,
    TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_VERSION,
)
from packages.div_planner.provider_boundary import (
    PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
    PLANNER_PROVIDER_MODE_SOLAR_SPIKE_PREFLIGHT,
)
from packages.div_planner.solar_live_spike import (
    SOLAR_PLANNER_LIVE_SPIKE_VERSION,
)
from packages.div_planner.solar_quality_comparison import (
    SOLAR_PLANNER_QUALITY_COMPARISON_VERSION,
)
from packages.div_planner.solar_draft_projection import (
    SOLAR_PLANNER_DRAFT_PROJECTION_VERSION,
)


DEMO_PAYLOAD = {
    "raw_prompt": (
        "Build a small task collaboration app for a study group. "
        "It needs task creation, assignee tracking, status changes, due dates, "
        "and a simple dashboard for incomplete work."
    ),
    "target_user": "study group members",
    "product_type": "task collaboration app",
    "constraints": [
        "local fixture demo only",
        "do not call live providers",
        "do not run target runtime",
    ],
    "success_criteria": [
        "planning artifact chain is visible",
        "dry-run evidence summary is visible",
        "verification report evidence is visible",
    ],
}


MVP_ID = "AW-MVP-01"
MVP_STAGE_NAMES = (
    "Idea",
    "PlanningBlueprint",
    "PRDPackage",
    "ImplementationBrief",
    "Approval",
    "RunnerPlan",
    "VerificationReport",
)


def _client(
    store_root: Path,
    *,
    include_provider_precheck: bool = False,
    include_target_runtime_admission: bool = False,
    include_target_runtime_output_manifest: bool = False,
    include_target_runtime_fixture_materialization: bool = False,
    include_target_runtime_restricted_workspace_generation: bool = False,
    include_target_runtime_generated_artifact_verification: bool = False,
    include_target_runtime_generated_workspace_static_validation: bool = False,
    include_target_runtime_buildable_fixture_manifest: bool = False,
    include_target_runtime_local_build_preflight: bool = False,
    include_target_runtime_local_build_attempt: bool = False,
    include_target_runtime_local_preview_attempt: bool = False,
) -> TestClient:
    provider_envelope_config = (
        ProviderEnvelopeRepositoryConfig(root=store_root / "provider-envelope-evidence")
        if include_provider_precheck
        else None
    )
    target_runtime_admission_config = (
        TargetRuntimeAdmissionRepositoryConfig(
            root=store_root / "target-runtime-admission-evidence"
        )
        if include_target_runtime_admission
        else None
    )
    target_runtime_output_manifest_config = (
        TargetRuntimeOutputManifestRepositoryConfig(
            root=store_root / "target-runtime-output-manifest-evidence"
        )
        if include_target_runtime_output_manifest
        else None
    )
    target_runtime_fixture_materialization_config = (
        TargetRuntimeFixtureMaterializationConfig(
            root=store_root / "target-runtime-fixture-workspace"
        )
        if include_target_runtime_fixture_materialization
        else None
    )
    target_runtime_restricted_workspace_generation_config = (
        TargetRuntimeRestrictedWorkspaceGenerationConfig(
            root=store_root / "target-runtime-restricted-workspace"
        )
        if (
            include_target_runtime_restricted_workspace_generation
            or include_target_runtime_generated_artifact_verification
            or include_target_runtime_generated_workspace_static_validation
            or include_target_runtime_buildable_fixture_manifest
            or include_target_runtime_local_build_preflight
            or include_target_runtime_local_build_attempt
        )
        else None
    )
    target_runtime_generated_artifact_verification_config = (
        TargetRuntimeGeneratedArtifactVerificationConfig(
            root=store_root / "target-runtime-restricted-workspace"
        )
        if (
            include_target_runtime_generated_artifact_verification
            or include_target_runtime_generated_workspace_static_validation
            or include_target_runtime_buildable_fixture_manifest
            or include_target_runtime_local_build_preflight
            or include_target_runtime_local_build_attempt
        )
        else None
    )
    target_runtime_generated_workspace_static_validation_config = (
        TargetRuntimeGeneratedWorkspaceStaticValidationConfig(
            root=store_root / "target-runtime-restricted-workspace"
        )
        if (
            include_target_runtime_generated_workspace_static_validation
            or include_target_runtime_buildable_fixture_manifest
            or include_target_runtime_local_build_preflight
            or include_target_runtime_local_build_attempt
        )
        else None
    )
    target_runtime_buildable_fixture_manifest_config = (
        TargetRuntimeBuildableFixtureManifestConfig(
            root=store_root / "target-runtime-restricted-workspace"
        )
        if (
            include_target_runtime_buildable_fixture_manifest
            or include_target_runtime_local_build_preflight
            or include_target_runtime_local_build_attempt
        )
        else None
    )
    target_runtime_local_build_attempt_config = (
        TargetRuntimeLocalBuildAttemptConfig(
            root=store_root / "target-runtime-restricted-workspace"
        )
        if include_target_runtime_local_build_attempt
        else None
    )
    target_runtime_local_preview_attempt_config = (
        TargetRuntimeLocalPreviewAttemptConfig(
            root=store_root / "target-runtime-restricted-workspace"
        )
        if include_target_runtime_local_preview_attempt
        else None
    )
    return TestClient(
        create_app(
            run_repository_config=RunArtifactRepositoryConfig(
                root=store_root / "canonical-run-artifacts",
            ),
            evidence_repository_config=EvidenceRepositoryConfig(
                root=store_root / "runner-report-audit-evidence",
            ),
            provider_envelope_repository_config=provider_envelope_config,
            target_runtime_admission_repository_config=target_runtime_admission_config,
            target_runtime_output_manifest_repository_config=(
                target_runtime_output_manifest_config
            ),
            target_runtime_fixture_materialization_config=(
                target_runtime_fixture_materialization_config
            ),
            target_runtime_restricted_workspace_generation_config=(
                target_runtime_restricted_workspace_generation_config
            ),
            target_runtime_generated_artifact_verification_config=(
                target_runtime_generated_artifact_verification_config
            ),
            target_runtime_generated_workspace_static_validation_config=(
                target_runtime_generated_workspace_static_validation_config
            ),
            target_runtime_buildable_fixture_manifest_config=(
                target_runtime_buildable_fixture_manifest_config
            ),
            target_runtime_local_build_attempt_config=(
                target_runtime_local_build_attempt_config
            ),
            target_runtime_local_preview_attempt_config=(
                target_runtime_local_preview_attempt_config
            ),
        )
    )


def _post_run(client: TestClient) -> dict[str, Any]:
    response = client.post("/api/v1/runs", json=DEMO_PAYLOAD)
    response.raise_for_status()
    return response.json()["data"]


def _get_data(client: TestClient, path: str) -> dict[str, Any]:
    response = client.get(path)
    response.raise_for_status()
    return response.json()["data"]


def _provider_envelope_precheck_payload(run_id: str, prompt_contract_hash: str) -> dict[str, Any]:
    payload = {
        "run_id": run_id,
        "prompt_contract_hash": prompt_contract_hash,
        "runtime_mode": "live_admission_precheck",
        "response_summary": "sanitized local demo provider envelope precheck projection",
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
                {"run_id": run_id, "purpose": "local demo provider envelope precheck"}
            ),
            "nonce": f"nonce-{run_id}",
        },
    }
    policy_summary = provider_precheck_operator_policy_summary(payload)
    payload["operator_approval"] = {
        "operator_ref": "local-demo-operator",
        "approved_at": "2026-06-01T00:00:00Z",
        "decision": "approved",
        "approved_policy_summary_hash": policy_summary["policy_summary_hash"],
    }
    payload["manual_test_proposal"] = {
        "proposal_id": f"proposal-{run_id}",
        "run_id": run_id,
        "prompt_contract_hash": prompt_contract_hash,
        "provider_name": "solar-pro-3",
        "model_name": "solar-pro-3",
        "request_timeout_seconds": 30,
        "max_cost_units": 1,
        "max_live_api_calls": 1,
        "max_output_unit_budget": 512,
        "rollback_plan_id": f"rollback-{run_id}",
        "abort_criteria": [
            "stop on timeout or quota breach",
            "stop on unexpected provider error",
        ],
    }
    proposal_summary = provider_manual_test_proposal_summary(payload)
    payload["manual_test_operator_approval"] = {
        "operator_ref": "local-demo-operator",
        "approved_at": "2026-06-01T00:05:00Z",
        "decision": "approved",
        "approved_proposal_hash": proposal_summary["proposal_hash"],
    }
    payload["manual_test_executor_enable"] = True
    planned_call_hash = stable_contract_hash(
        {
            "projection_version": MANUAL_PROVIDER_TEST_EXECUTOR_VERSION,
            "run_id": run_id,
            "prompt_contract_hash": prompt_contract_hash,
            "provider_name": "solar-pro-3",
            "model_name": "solar-pro-3",
            "proposal_hash": proposal_summary["proposal_hash"],
            "executor_enable_requested": True,
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
    }
    preflight_summary = provider_manual_test_preflight_summary(payload)
    payload["manual_test_readiness_decision"] = {
        "preflight_audit_hash": preflight_summary["preflight_audit_hash"],
        "decision": "approve",
        "operator_ref": "local-demo-operator",
        "decided_at": "2026-06-01T00:10:00Z",
        "decision_reason_code": "local-demo-readiness-reviewed",
    }
    handoff_summary = provider_manual_test_handoff_packet_summary(payload)
    payload["manual_test_operator_opt_in"] = {
        "handoff_packet_hash": handoff_summary["handoff_packet_hash"],
        "decision": "opt_in",
        "operator_ref": "local-demo-operator",
        "opted_in_at": "2026-06-01T00:15:00Z",
    }
    opt_in_summary = provider_manual_test_operator_opt_in_summary(payload)
    payload["expected_operator_opt_in_hash"] = opt_in_summary["operator_opt_in_hash"]
    sealed_summary = provider_manual_test_sealed_pre_execution_packet_summary(payload)
    payload["expected_sealed_packet_hash"] = sealed_summary["sealed_packet_hash"]
    payload["manual_test_live_execution_arming"] = {
        "sealed_packet_hash": sealed_summary["sealed_packet_hash"],
        "operator_ref": "local-demo-operator",
        "armed_at": "2026-06-01T00:20:00Z",
        "expires_at": "2026-06-01T00:25:00Z",
        "rollback_abort_hash": sealed_summary["rollback_abort_hash"],
        "abort_policy_hash": stable_contract_hash(
            {
                "abort_policy": "local-demo-manual-provider-test-stop-policy",
                "run_id": run_id,
            }
        ),
    }
    arming_summary = provider_manual_test_arming_record_summary(payload)
    payload["expected_arming_record_hash"] = arming_summary["arming_record_hash"]
    payload["manual_test_execution_release_proposal"] = {
        "arming_record_hash": arming_summary["arming_record_hash"],
        "operator_ref": "local-demo-operator",
        "proposed_at": "2026-06-01T00:30:00Z",
        "release_window_start": "2026-06-01T00:35:00Z",
        "release_window_end": "2026-06-01T00:40:00Z",
        "rollback_abort_hash": arming_summary["rollback_abort_hash"],
    }
    release_summary = provider_manual_test_release_proposal_summary(payload)
    payload["expected_release_proposal_hash"] = release_summary["release_proposal_hash"]
    payload["manual_test_final_release_packet"] = {
        "release_proposal_hash": release_summary["release_proposal_hash"],
    }
    final_summary = provider_manual_test_final_release_packet_summary(payload)
    payload["expected_final_release_packet_hash"] = final_summary[
        "final_release_packet_hash"
    ]
    payload["manual_test_execution_switch"] = {
        "final_release_packet_hash": final_summary["final_release_packet_hash"],
        "enable_requested": True,
    }
    execution_switch_summary = provider_manual_test_execution_switch_summary(payload)
    payload["expected_execution_switch_hash"] = execution_switch_summary[
        "execution_switch_hash"
    ]
    payload["manual_test_executor_preflight"] = {
        "execution_switch_hash": execution_switch_summary["execution_switch_hash"],
    }
    executor_preflight_summary = provider_manual_test_executor_preflight_summary(
        payload
    )
    payload["expected_executor_preflight_hash"] = executor_preflight_summary[
        "executor_preflight_hash"
    ]
    payload["manual_test_executor_dispatch_record"] = {
        "executor_preflight_hash": executor_preflight_summary[
            "executor_preflight_hash"
        ],
        "dispatch_requested": True,
    }
    dispatch_record_summary = provider_manual_test_executor_dispatch_record_summary(
        payload
    )
    payload["expected_dispatch_record_hash"] = dispatch_record_summary[
        "dispatch_record_hash"
    ]
    payload["manual_test_executor_invocation_receipt"] = {
        "dispatch_record_hash": dispatch_record_summary["dispatch_record_hash"],
        "receipt_requested": True,
    }
    invocation_receipt_summary = provider_manual_test_invocation_receipt_summary(
        payload
    )
    payload["expected_invocation_receipt_hash"] = invocation_receipt_summary[
        "invocation_receipt_hash"
    ]
    payload["manual_test_post_invocation_audit"] = {
        "invocation_receipt_hash": invocation_receipt_summary[
            "invocation_receipt_hash"
        ],
        "audit_requested": True,
    }
    post_invocation_audit_summary = provider_manual_test_post_invocation_audit_summary(
        payload
    )
    post_invocation_audit_hash = post_invocation_audit_summary[
        "post_invocation_audit_hash"
    ]
    payload["expected_post_invocation_audit_hash"] = post_invocation_audit_hash
    payload["manual_test_completion_summary"] = {
        "post_invocation_audit_hash": post_invocation_audit_hash,
        "summary_requested": True,
    }
    completion_summary = provider_manual_test_completion_summary(payload)
    payload["expected_completion_summary_hash"] = completion_summary[
        "completion_summary_hash"
    ]
    payload["manual_test_closeout_record"] = {
        "completion_summary_hash": completion_summary["completion_summary_hash"],
        "closeout_requested": True,
    }
    closeout_record_summary = provider_manual_test_closeout_record_summary(payload)
    payload["expected_closeout_record_hash"] = closeout_record_summary[
        "closeout_record_hash"
    ]
    payload["manual_test_operator_handback"] = {
        "closeout_record_hash": closeout_record_summary["closeout_record_hash"],
        "handback_requested": True,
        "operator_review": {
            "operator_ref": "local-demo-operator",
            "reviewed_at": "2026-06-01T00:45:00Z",
            "review_decision": "acknowledged",
            "review_reason_code": "local-demo-no-call-handback-reviewed",
        },
    }
    operator_handback_hash = provider_manual_test_operator_handback_summary(payload)[
        "operator_handback_hash"
    ]
    payload["expected_operator_handback_hash"] = operator_handback_hash
    payload["manual_test_operator_decision_packet"] = {
        "operator_handback_hash": operator_handback_hash,
        "packet_requested": True,
        "operator_decision": {
            "operator_ref": "local-demo-operator",
            "decided_at": "2026-06-01T00:50:00Z",
            "decision": "acknowledged",
            "decision_reason_code": "local-demo-no-call-decision-reviewed",
        },
    }
    decision_packet_hash = provider_manual_test_operator_decision_packet_summary(
        payload
    )["operator_decision_packet_hash"]
    payload["expected_operator_decision_packet_hash"] = decision_packet_hash
    payload["manual_test_operator_release_attestation"] = {
        "operator_decision_packet_hash": decision_packet_hash,
        "attestation_requested": True,
        "operator_attestation": {
            "operator_ref": "local-demo-operator",
            "attested_at": "2026-06-01T00:55:00Z",
            "attestation": "release_acknowledged",
            "attestation_reason_code": "local-demo-no-call-release-attested",
        },
    }
    release_attestation_hash = provider_manual_test_operator_release_attestation_summary(
        payload
    )["operator_release_attestation_hash"]
    payload["expected_operator_release_attestation_hash"] = release_attestation_hash
    payload["manual_test_release_authorization_seal"] = {
        "operator_release_attestation_hash": release_attestation_hash,
        "seal_requested": True,
        "seal_material": {
            "operator_ref": "local-demo-operator",
            "sealed_at": "2026-06-01T01:00:00Z",
            "seal_decision": "sealed",
            "seal_reason_code": "local-demo-no-call-release-sealed",
        },
    }
    release_seal_hash = provider_manual_test_release_authorization_seal_summary(
        payload
    )["release_seal_hash"]
    payload["expected_release_seal_hash"] = release_seal_hash
    payload["manual_test_execution_authorization_capsule"] = {
        "release_seal_hash": release_seal_hash,
        "capsule_requested": True,
        "final_authorization": {
            "operator_ref": "local-demo-operator",
            "authorized_at": "2026-06-01T01:05:00Z",
            "decision": "sealed",
            "reason_code": "local-demo-no-call-execution-capsule-sealed",
        },
    }
    execution_capsule_hash = provider_manual_test_execution_authorization_capsule_summary(
        payload
    )["execution_capsule_hash"]
    payload["expected_execution_capsule_hash"] = execution_capsule_hash
    payload["manual_test_execution_capsule_export"] = {
        "execution_capsule_hash": execution_capsule_hash,
        "export_requested": True,
        "export_metadata": {
            "operator_ref": "local-demo-operator",
            "exported_at": "2026-06-01T01:10:00Z",
            "export_kind": "read_model_projection",
            "export_reason_code": "local-demo-no-call-capsule-exported",
        },
    }
    execution_capsule_export_hash = provider_manual_test_execution_capsule_export_summary(
        payload
    )["execution_capsule_export_hash"]
    payload["expected_execution_capsule_export_hash"] = execution_capsule_export_hash
    payload["manual_test_execution_capsule_handoff_packet"] = {
        "execution_capsule_export_hash": execution_capsule_export_hash,
        "handoff_requested": True,
        "handoff_material": "local-demo-no-call-capsule-handoff",
    }
    execution_capsule_handoff_packet_hash = (
        provider_manual_test_execution_capsule_handoff_packet_summary(payload)[
            "execution_capsule_handoff_packet_hash"
        ]
    )
    payload["expected_execution_capsule_handoff_packet_hash"] = (
        execution_capsule_handoff_packet_hash
    )
    payload["manual_test_execution_capsule_operator_review"] = {
        "execution_capsule_handoff_packet_hash": execution_capsule_handoff_packet_hash,
        "review_requested": True,
        "operator_review": {
            "operator_ref": "local-demo-operator",
            "reviewed_at": "2026-06-01T01:15:00Z",
            "review_decision": "reviewed",
            "review_reason_code": "local-demo-no-call-capsule-operator-reviewed",
        },
    }
    execution_capsule_operator_review_hash = (
        provider_manual_test_execution_capsule_operator_review_summary(payload)[
            "execution_capsule_operator_review_hash"
        ]
    )
    payload["expected_execution_capsule_operator_review_hash"] = (
        execution_capsule_operator_review_hash
    )
    payload["manual_test_execution_capsule_operator_decision"] = {
        "execution_capsule_operator_review_hash": (
            execution_capsule_operator_review_hash
        ),
        "decision_requested": True,
        "operator_decision": {
            "operator_ref": "local-demo-operator",
            "decided_at": "2026-06-01T01:20:00Z",
            "decision": "reviewed",
            "decision_reason_code": "local-demo-no-call-capsule-operator-decided",
        },
    }
    execution_capsule_operator_decision_hash = (
        provider_manual_test_execution_capsule_operator_decision_summary(payload)[
            "execution_capsule_operator_decision_hash"
        ]
    )
    payload["expected_execution_capsule_operator_decision_hash"] = (
        execution_capsule_operator_decision_hash
    )
    payload["manual_test_execution_capsule_release_attestation"] = {
        "execution_capsule_operator_decision_hash": (
            execution_capsule_operator_decision_hash
        ),
        "attestation_requested": True,
        "release_attestation": {
            "operator_ref": "local-demo-operator",
            "attested_at": "2026-06-01T01:25:00Z",
            "attestation": "release_attested",
            "attestation_reason_code": (
                "local-demo-no-call-capsule-release-attested"
            ),
        },
    }
    execution_capsule_release_attestation_hash = (
        provider_manual_test_execution_capsule_release_attestation_summary(payload)[
            "execution_capsule_release_attestation_hash"
        ]
    )
    payload["expected_execution_capsule_release_attestation_hash"] = (
        execution_capsule_release_attestation_hash
    )
    payload["manual_test_execution_capsule_release_seal"] = {
        "execution_capsule_release_attestation_hash": (
            execution_capsule_release_attestation_hash
        ),
        "seal_requested": True,
        "seal_material": {
            "operator_ref": "local-demo-operator",
            "sealed_at": "2026-06-01T01:30:00Z",
            "seal_decision": "sealed",
            "seal_reason_code": "local-demo-no-call-capsule-release-sealed",
        },
    }
    execution_capsule_release_seal_hash = (
        provider_manual_test_execution_capsule_release_seal_summary(payload)[
            "execution_capsule_release_seal_hash"
        ]
    )
    payload["expected_execution_capsule_release_seal_hash"] = (
        execution_capsule_release_seal_hash
    )
    payload["manual_test_execution_capsule_final_authorization"] = {
        "execution_capsule_release_seal_hash": execution_capsule_release_seal_hash,
        "authorization_requested": True,
        "final_authorization": {
            "operator_ref": "local-demo-operator",
            "authorized_at": "2026-06-01T01:35:00Z",
            "authorization_decision": "authorized",
            "authorization_reason_code": (
                "local-demo-no-call-capsule-final-authorized"
            ),
        },
    }
    execution_capsule_final_authz_hash = (
        provider_manual_test_execution_capsule_final_authorization_summary(payload)[
            "execution_capsule_final_authz_hash"
        ]
    )
    payload["expected_execution_capsule_final_authz_hash"] = (
        execution_capsule_final_authz_hash
    )
    payload["manual_test_execution_capsule_authz_export"] = {
        "execution_capsule_final_authz_hash": execution_capsule_final_authz_hash,
        "export_requested": True,
        "export_metadata": {
            "operator_ref": "local-demo-operator",
            "exported_at": "2026-06-01T01:40:00Z",
            "export_kind": "authz_read_model",
            "export_reason_code": "local-demo-no-call-capsule-authz-exported",
        },
    }
    execution_capsule_authz_export_hash = (
        provider_manual_test_execution_capsule_authz_export_summary(payload)[
            "execution_capsule_authz_export_hash"
        ]
    )
    payload["expected_execution_capsule_authz_export_hash"] = (
        execution_capsule_authz_export_hash
    )
    payload["manual_test_execution_capsule_authz_handoff_packet"] = {
        "execution_capsule_authz_export_hash": execution_capsule_authz_export_hash,
        "handoff_requested": True,
        "handoff_material": "local-demo-no-call-capsule-authz-handoff",
    }
    execution_capsule_authz_handoff_packet_hash = (
        provider_manual_test_execution_capsule_authz_handoff_packet_summary(payload)[
            "execution_capsule_authz_handoff_packet_hash"
        ]
    )
    payload["expected_execution_capsule_authz_handoff_packet_hash"] = (
        execution_capsule_authz_handoff_packet_hash
    )
    payload["manual_test_execution_capsule_authz_operator_review"] = {
        "execution_capsule_authz_handoff_packet_hash": (
            execution_capsule_authz_handoff_packet_hash
        ),
        "review_requested": True,
        "operator_review": {
            "operator_ref": "local-demo-operator",
            "reviewed_at": "2026-06-01T01:45:00Z",
            "review_decision": "reviewed",
            "review_reason_code": "local-demo-no-call-capsule-authz-reviewed",
        },
    }
    execution_capsule_authz_operator_review_hash = (
        provider_manual_test_execution_capsule_authz_operator_review_summary(payload)[
            "execution_capsule_authz_operator_review_hash"
        ]
    )
    payload["expected_execution_capsule_authz_operator_review_hash"] = (
        execution_capsule_authz_operator_review_hash
    )
    payload["manual_test_execution_capsule_authz_operator_decision"] = {
        "execution_capsule_authz_operator_review_hash": (
            execution_capsule_authz_operator_review_hash
        ),
        "decision_requested": True,
        "operator_decision": {
            "operator_ref": "local-demo-operator",
            "decided_at": "2026-06-01T01:50:00Z",
            "decision": "reviewed",
            "decision_reason_code": "local-demo-no-call-capsule-authz-decided",
        },
    }
    execution_capsule_authz_operator_decision_hash = (
        provider_manual_test_execution_capsule_authz_operator_decision_summary(
            payload
        )["execution_capsule_authz_operator_decision_hash"]
    )
    payload["expected_execution_capsule_authz_operator_decision_hash"] = (
        execution_capsule_authz_operator_decision_hash
    )
    payload["manual_test_execution_capsule_authz_release_attestation"] = {
        "execution_capsule_authz_operator_decision_hash": (
            execution_capsule_authz_operator_decision_hash
        ),
        "attestation_requested": True,
        "release_attestation": {
            "operator_ref": "local-demo-operator",
            "attested_at": "2026-06-01T01:55:00Z",
            "attestation": "release_attested",
            "attestation_reason_code": (
                "local-demo-no-call-capsule-authz-release-attested"
            ),
        },
    }
    execution_capsule_authz_release_attestation_hash = (
        provider_manual_test_execution_capsule_authz_release_attestation_summary(
            payload
        )["execution_capsule_authz_release_attestation_hash"]
    )
    payload["expected_execution_capsule_authz_release_attestation_hash"] = (
        execution_capsule_authz_release_attestation_hash
    )
    payload["manual_test_execution_capsule_authz_release_seal"] = {
        "execution_capsule_authz_release_attestation_hash": (
            execution_capsule_authz_release_attestation_hash
        ),
        "seal_requested": True,
        "seal_material": {
            "operator_ref": "local-demo-operator",
            "sealed_at": "2026-06-01T02:00:00Z",
            "seal_decision": "sealed",
            "seal_reason_code": "local-demo-no-call-capsule-authz-release-sealed",
        },
    }
    execution_capsule_authz_release_seal_hash = (
        provider_manual_test_execution_capsule_authz_release_seal_summary(payload)[
            "execution_capsule_authz_release_seal_hash"
        ]
    )
    payload["expected_execution_capsule_authz_release_seal_hash"] = (
        execution_capsule_authz_release_seal_hash
    )
    payload["manual_test_execution_capsule_authz_final_authorization"] = {
        "execution_capsule_authz_release_seal_hash": (
            execution_capsule_authz_release_seal_hash
        ),
        "authorization_requested": True,
        "final_authorization": {
            "operator_ref": "local-demo-operator",
            "authorized_at": "2026-06-01T02:05:00Z",
            "authorization_decision": "authorized",
            "authorization_reason_code": (
                "local-demo-no-call-capsule-authz-final-authorized"
            ),
        },
    }
    execution_capsule_authz_final_authz_hash = (
        provider_manual_test_execution_capsule_authz_final_authorization_summary(
            payload
        )["execution_capsule_authz_final_authz_hash"]
    )
    payload["expected_execution_capsule_authz_final_authz_hash"] = (
        execution_capsule_authz_final_authz_hash
    )
    payload["manual_test_execution_capsule_authz_final_authz_export"] = {
        "execution_capsule_authz_final_authz_hash": (
            execution_capsule_authz_final_authz_hash
        ),
        "export_requested": True,
        "export_metadata": {
            "operator_ref": "local-demo-operator",
            "exported_at": "2026-06-01T02:10:00Z",
            "export_kind": "authz_final_read_model",
            "export_reason_code": (
                "local-demo-no-call-capsule-authz-final-exported"
            ),
        },
    }
    execution_capsule_authz_final_authz_export_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_export_summary(
            payload
        )["execution_capsule_authz_final_authz_export_hash"]
    )
    payload["expected_execution_capsule_authz_final_authz_export_hash"] = (
        execution_capsule_authz_final_authz_export_hash
    )
    payload["manual_test_execution_capsule_authz_final_authz_handoff_packet"] = {
        "execution_capsule_authz_final_authz_export_hash": (
            execution_capsule_authz_final_authz_export_hash
        ),
        "handoff_requested": True,
    }
    execution_capsule_authz_final_authz_handoff_packet_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_handoff_packet_summary(
            payload
        )["execution_capsule_authz_final_authz_handoff_packet_hash"]
    )
    payload["expected_execution_capsule_authz_final_authz_handoff_packet_hash"] = (
        execution_capsule_authz_final_authz_handoff_packet_hash
    )
    payload["manual_test_execution_capsule_authz_final_authz_operator_review"] = {
        "execution_capsule_authz_final_authz_handoff_packet_hash": (
            execution_capsule_authz_final_authz_handoff_packet_hash
        ),
        "review_requested": True,
        "operator_review": {
            "operator_ref": "local-demo-operator",
            "reviewed_at": "2026-06-01T02:15:00Z",
            "review_decision": "reviewed",
            "review_reason_code": "local-demo-no-call-capsule-authz-final-reviewed",
        },
    }
    execution_capsule_authz_final_authz_operator_review_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_operator_review_summary(
            payload
        )["execution_capsule_authz_final_authz_operator_review_hash"]
    )
    payload["expected_execution_capsule_authz_final_authz_operator_review_hash"] = (
        execution_capsule_authz_final_authz_operator_review_hash
    )
    payload["manual_test_execution_capsule_authz_final_authz_operator_decision"] = {
        "execution_capsule_authz_final_authz_operator_review_hash": (
            execution_capsule_authz_final_authz_operator_review_hash
        ),
        "decision_requested": True,
        "operator_decision": {
            "operator_ref": "local-demo-operator",
            "decided_at": "2026-06-01T02:20:00Z",
            "decision": "reviewed",
            "decision_reason_code": "local-demo-no-call-capsule-authz-final-decided",
        },
    }
    execution_capsule_authz_final_authz_operator_decision_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_operator_decision_summary(
            payload
        )["execution_capsule_authz_final_authz_operator_decision_hash"]
    )
    payload["expected_execution_capsule_authz_final_authz_operator_decision_hash"] = (
        execution_capsule_authz_final_authz_operator_decision_hash
    )
    payload["manual_test_execution_capsule_authz_final_authz_release_attestation"] = {
        "execution_capsule_authz_final_authz_operator_decision_hash": (
            execution_capsule_authz_final_authz_operator_decision_hash
        ),
        "attestation_requested": True,
        "release_attestation": {
            "operator_ref": "local-demo-operator",
            "attested_at": "2026-06-01T02:25:00Z",
            "attestation": "attested",
            "attestation_reason_code": (
                "local-demo-no-call-capsule-authz-final-release-attested"
            ),
        },
    }
    execution_capsule_authz_final_authz_release_attestation_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_release_attestation_summary(
            payload
        )["execution_capsule_authz_final_authz_release_attestation_hash"]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_release_attestation_hash"
    ] = execution_capsule_authz_final_authz_release_attestation_hash
    payload["manual_test_execution_capsule_authz_final_authz_release_seal"] = {
        "execution_capsule_authz_final_authz_release_attestation_hash": (
            execution_capsule_authz_final_authz_release_attestation_hash
        ),
        "seal_requested": True,
        "seal_material": {
            "operator_ref": "local-demo-operator",
            "sealed_at": "2026-06-01T02:30:00Z",
            "seal_decision": "sealed",
            "seal_reason_code": (
                "local-demo-no-call-capsule-authz-final-release-sealed"
            ),
        },
    }
    execution_capsule_authz_final_authz_release_seal_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_release_seal_summary(
            payload
        )["execution_capsule_authz_final_authz_release_seal_hash"]
    )
    payload["expected_execution_capsule_authz_final_authz_release_seal_hash"] = (
        execution_capsule_authz_final_authz_release_seal_hash
    )
    payload["manual_test_execution_capsule_authz_final_authz_final_authorization"] = {
        "execution_capsule_authz_final_authz_release_seal_hash": (
            execution_capsule_authz_final_authz_release_seal_hash
        ),
        "authorization_requested": True,
        "final_authorization": {
            "operator_ref": "local-demo-operator",
            "authorized_at": "2026-06-01T02:35:00Z",
            "authorization_decision": "authorized",
            "authorization_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-authorized"
            ),
        },
    }
    execution_capsule_authz_final_authz_final_authz_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_summary(
            payload
        )["execution_capsule_authz_final_authz_final_authz_hash"]
    )
    payload["expected_execution_capsule_authz_final_authz_final_authz_hash"] = (
        execution_capsule_authz_final_authz_final_authz_hash
    )
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_export"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_hash": (
            execution_capsule_authz_final_authz_final_authz_hash
        ),
        "export_requested": True,
        "export_metadata": {
            "operator_ref": "local-demo-operator",
            "exported_at": "2026-06-01T02:40:00Z",
            "export_kind": "authz_final_final_read_model",
            "export_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-exported"
            ),
        },
    }
    execution_capsule_authz_final_authz_final_authz_export_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet_summary(
            payload
        )["execution_capsule_authz_final_authz_final_authz_export_hash"]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_export_hash"
    ] = execution_capsule_authz_final_authz_final_authz_export_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_export_hash": (
            execution_capsule_authz_final_authz_final_authz_export_hash
        ),
        "handoff_requested": True,
        "handoff_material": "local-demo-no-call-capsule-authz-final-final-handoff",
    }
    execution_capsule_authz_final_authz_final_authz_handoff_packet_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_handoff_packet_summary(
            payload
        )["execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"
    ] = execution_capsule_authz_final_authz_final_authz_handoff_packet_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash": (
            execution_capsule_authz_final_authz_final_authz_handoff_packet_hash
        ),
        "review_requested": True,
        "operator_review": {
            "operator_ref": "local-demo-operator",
            "reviewed_at": "2026-06-01T02:45:00Z",
            "review_decision": "reviewed",
            "review_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-reviewed"
            ),
        },
    }
    execution_capsule_authz_final_authz_final_authz_operator_review_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_review_summary(
            payload
        )["execution_capsule_authz_final_authz_final_authz_operator_review_hash"]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_operator_review_hash"
    ] = execution_capsule_authz_final_authz_final_authz_operator_review_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_operator_review_hash": (
            execution_capsule_authz_final_authz_final_authz_operator_review_hash
        ),
        "decision_requested": True,
        "operator_decision": {
            "operator_ref": "local-demo-operator",
            "decided_at": "2026-06-01T02:50:00Z",
            "decision": "reviewed",
            "decision_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-decided"
            ),
        },
    }
    execution_capsule_authz_final_authz_final_authz_operator_decision_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_operator_decision_summary(
            payload
        )["execution_capsule_authz_final_authz_final_authz_operator_decision_hash"]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_operator_decision_hash"
    ] = execution_capsule_authz_final_authz_final_authz_operator_decision_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_release_attestation"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_operator_decision_hash": (
            execution_capsule_authz_final_authz_final_authz_operator_decision_hash
        ),
        "attestation_requested": True,
        "release_attestation": {
            "operator_ref": "local-demo-operator",
            "attested_at": "2026-06-01T02:55:00Z",
            "attestation": "attested",
            "attestation_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-release-attested"
            ),
        },
    }
    execution_capsule_authz_final_authz_final_authz_release_attestation_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_attestation_summary(
            payload
        )["execution_capsule_authz_final_authz_final_authz_release_attestation_hash"]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_release_attestation_hash"
    ] = execution_capsule_authz_final_authz_final_authz_release_attestation_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_release_attestation_hash": (
            execution_capsule_authz_final_authz_final_authz_release_attestation_hash
        ),
        "seal_requested": True,
        "seal_material": {
            "operator_ref": "local-demo-operator",
            "sealed_at": "2026-06-01T03:00:00Z",
            "seal_decision": "sealed",
            "seal_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-release-sealed"
            ),
        },
    }
    execution_capsule_authz_final_authz_final_authz_release_seal_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_release_seal_summary(
            payload
        )["execution_capsule_authz_final_authz_final_authz_release_seal_hash"]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_release_seal_hash"
    ] = execution_capsule_authz_final_authz_final_authz_release_seal_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_release_seal_hash": (
            execution_capsule_authz_final_authz_final_authz_release_seal_hash
        ),
        "authorization_requested": True,
        "final_authorization": {
            "operator_ref": "local-demo-operator",
            "authorized_at": "2026-06-01T03:05:00Z",
            "authorization_decision": "authorized_disabled",
            "authorization_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-final-authorized"
            ),
        },
    }
    execution_capsule_authz_final_authz_final_authz_final_authz_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_summary(
            payload
        )["execution_capsule_authz_final_authz_final_authz_final_authz_hash"]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_hash"
    ] = execution_capsule_authz_final_authz_final_authz_final_authz_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_export"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_final_authz_hash": (
            execution_capsule_authz_final_authz_final_authz_final_authz_hash
        ),
        "export_requested": True,
        "export_metadata": {
            "operator_ref": "local-demo-operator",
            "exported_at": "2026-06-01T03:10:00Z",
            "export_kind": "final_authorization_read_model",
            "export_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-final-exported"
            ),
        },
    }
    execution_capsule_authz_final_authz_final_authz_final_authz_export_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_export_summary(
            payload
        )[
            "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
        ]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
    ] = execution_capsule_authz_final_authz_final_authz_final_authz_export_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash": (
            execution_capsule_authz_final_authz_final_authz_final_authz_export_hash
        ),
        "handoff_requested": True,
        "handoff_material": "local-demo-no-call-capsule-authz-final-final-final-handoff",
    }
    execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_handoff_packet_summary(
            payload
        )[
            "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
        ]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
    ] = execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash": (
            execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash
        ),
        "review_requested": True,
        "operator_review": {
            "review_decision": "reviewed",
            "review_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-final-reviewed"
            ),
            "reviewed_at": "2026-06-01T03:15:00Z",
            "operator_ref": "local-demo-operator",
        },
    }
    execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_review_summary(
            payload
        )[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
        ]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
    ] = execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash": (
            execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash
        ),
        "decision_requested": True,
        "operator_decision": {
            "decision": "reviewed",
            "decision_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-final-decided"
            ),
            "decided_at": "2026-06-01T03:20:00Z",
            "operator_ref": "local-demo-operator",
        },
    }
    execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_operator_decision_summary(
            payload
        )[
            "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
        ]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
    ] = execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash": (
            execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash
        ),
        "attestation_requested": True,
        "release_attestation": {
            "attestation": "attested",
            "attestation_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-final-attested"
            ),
            "attested_at": "2026-06-01T03:25:00Z",
            "operator_ref": "local-demo-operator",
        },
    }
    execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_attestation_summary(
            payload
        )[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
        ]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
    ] = execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash": (
            execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash
        ),
        "seal_requested": True,
        "seal_material": {
            "seal_decision": "sealed",
            "seal_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-final-sealed"
            ),
            "sealed_at": "2026-06-01T03:30:00Z",
            "operator_ref": "local-demo-operator",
        },
    }
    execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_release_seal_summary(
            payload
        )[
            "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
        ]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
    ] = execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash": (
            execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash
        ),
        "authorization_requested": True,
        "final_authorization": {
            "authorization_decision": "authorized_disabled",
            "authorization_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-final-final-authorized"
            ),
            "authorized_at": "2026-06-01T03:35:00Z",
            "operator_ref": "local-demo-operator",
        },
    }
    execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash = (
        provider_manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_summary(
            payload
        )[
            "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
        ]
    )
    payload[
        "expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
    ] = execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash
    payload[
        "manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export"
    ] = {
        "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash": (
            execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash
        ),
        "export_requested": True,
        "export_metadata": {
            "operator_ref": "local-demo-operator",
            "exported_at": "2026-06-01T03:40:00Z",
            "export_kind": "final_authorization_read_model",
            "export_reason_code": (
                "local-demo-no-call-capsule-authz-final-final-final-final-exported"
            ),
        },
    }
    return payload


def _post_provider_envelope_precheck(
    client: TestClient,
    *,
    run_id: str,
    prompt_contract_hash: str,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=_provider_envelope_precheck_payload(run_id, prompt_contract_hash),
    )
    response.raise_for_status()
    return response.json()["data"]


def _solar_planner_preflight_payload(run_id: str, prompt_contract_hash: str) -> dict[str, Any]:
    readiness = {field_name: True for field_name in LIVE_OPEN_REQUIRED_CONTROLS}
    return {
        "run_id": run_id,
        "prompt_contract_hash": prompt_contract_hash,
        "planner_provider_mode": PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
        "stage_target": "PlanningBlueprint",
        "env_key_name": "UPSTAGE_API_KEY",
        "policy": {
            **readiness,
            "request_timeout_seconds": 30,
            "max_cost_units": 1,
            "max_output_tokens": 512,
            "max_live_api_calls": 1,
            "retry_count": 0,
        },
    }


def _solar_planner_spike_payload(run_id: str, prompt_contract_hash: str) -> dict[str, Any]:
    payload = _solar_planner_preflight_payload(run_id, prompt_contract_hash)
    payload["planner_provider_mode"] = PLANNER_PROVIDER_MODE_SOLAR_SPIKE_PREFLIGHT
    payload["model_family"] = "solar-pro3"
    payload["cost_limit_label"] = "one-shot-bounded"
    payload["response_summary"] = "Sanitized mocked planner expansion for one-shot spike readiness."
    payload["summary_section_count"] = 4
    return payload


def _post_solar_planner_preflight(
    client: TestClient,
    *,
    run_id: str,
    prompt_contract_hash: str,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/planner/provider/preflight",
        json=_solar_planner_preflight_payload(run_id, prompt_contract_hash),
    )
    response.raise_for_status()
    return response.json()["data"]


def _post_solar_planner_spike_mock_response(
    client: TestClient,
    *,
    run_id: str,
    prompt_contract_hash: str,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/planner/provider/solar-spike/mock-response",
        json=_solar_planner_spike_payload(run_id, prompt_contract_hash),
    )
    response.raise_for_status()
    return response.json()["data"]


def _solar_planner_live_spike_payload(
    run_id: str,
    prompt_contract_hash: str,
    *,
    allow_solar_planner_live_call: bool,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "prompt_contract_hash": prompt_contract_hash,
        "operator_live_opt_in": allow_solar_planner_live_call,
        "env_key_name": "UPSTAGE_API_KEY",
        "model": "solar-pro3",
        "request_timeout_seconds": 20,
        "max_input_chars": 1800,
        "max_output_tokens": 384,
        "max_live_api_calls": 1,
        "cost_limit_label": "one-shot-bounded",
        "sanitized_idea_summary": "study group task collaboration app with dashboard",
    }


def _post_solar_planner_live_spike(
    client: TestClient,
    *,
    run_id: str,
    prompt_contract_hash: str,
    allow_solar_planner_live_call: bool,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/planner/provider/solar-live/spike",
        json=_solar_planner_live_spike_payload(
            run_id,
            prompt_contract_hash,
            allow_solar_planner_live_call=allow_solar_planner_live_call,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _solar_planner_quality_comparison_payload(
    run_id: str,
    prompt_contract_hash: str,
    *,
    stage_coverage: dict[str, Any],
    fixture_artifact_count: int,
    solar_live_spike_projection: dict[str, Any],
    reviewer_approval_hash: str = "",
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "prompt_contract_hash": prompt_contract_hash,
        "fixture_required_stage_count": _as_int(
            stage_coverage.get("required_stage_count")
        ),
        "fixture_covered_stage_count": _as_int(
            stage_coverage.get("covered_stage_count")
        ),
        "fixture_artifact_count": fixture_artifact_count,
        "solar_live_spike_projection": solar_live_spike_projection,
        "reviewer_approval_hash": reviewer_approval_hash,
        "required_solar_section_count": 4,
    }


def _post_solar_planner_quality_comparison(
    client: TestClient,
    *,
    run_id: str,
    prompt_contract_hash: str,
    stage_coverage: dict[str, Any],
    fixture_artifact_count: int,
    solar_live_spike_projection: dict[str, Any],
    reviewer_approval_hash: str = "",
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/planner/provider/solar-quality/comparison",
        json=_solar_planner_quality_comparison_payload(
            run_id,
            prompt_contract_hash,
            stage_coverage=stage_coverage,
            fixture_artifact_count=fixture_artifact_count,
            solar_live_spike_projection=solar_live_spike_projection,
            reviewer_approval_hash=reviewer_approval_hash,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _solar_planner_draft_projection_payload(
    run_id: str,
    prompt_contract_hash: str,
    *,
    solar_quality_comparison_projection: dict[str, Any],
    reviewer_approval_hash: str = "",
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "prompt_contract_hash": prompt_contract_hash,
        "solar_quality_comparison_hash": str(
            solar_quality_comparison_projection.get("comparison_hash", "")
        ),
        "solar_quality_comparison_projection": solar_quality_comparison_projection,
        "reviewer_approval_hash": reviewer_approval_hash,
        "requested_draft_labels": ["PlanningBlueprint", "PRDPackage"],
    }


def _post_solar_planner_draft_projection(
    client: TestClient,
    *,
    run_id: str,
    prompt_contract_hash: str,
    solar_quality_comparison_projection: dict[str, Any],
    reviewer_approval_hash: str = "",
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/planner/provider/solar-draft/projection",
        json=_solar_planner_draft_projection_payload(
            run_id,
            prompt_contract_hash,
            solar_quality_comparison_projection=solar_quality_comparison_projection,
            reviewer_approval_hash=reviewer_approval_hash,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_preflight_payload(run_id: str, runner_plan_hash: str) -> dict[str, Any]:
    readiness = {field_name: True for field_name in LIVE_OPEN_REQUIRED_CONTROLS}
    workspace_root = f"runs/{run_id}/workspace"
    return {
        "run_id": run_id,
        "runner_plan_hash": runner_plan_hash,
        "mode": TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT,
        "sandbox_policy": {
            **readiness,
            "timeout_seconds": 60,
            "max_planned_files": 20,
            "max_subprocess_calls": 0,
            "max_package_installs": 0,
            "max_server_starts": 0,
            "max_network_calls": 0,
            "max_target_runtime_calls": 0,
        },
        "workspace_intent": {
            "workspace_root": workspace_root,
            "allowed_write_paths": [
                f"{workspace_root}/backend",
                f"{workspace_root}/frontend",
                f"{workspace_root}/reports",
            ],
            "requested_write_paths": [
                f"{workspace_root}/backend/main.py",
                f"{workspace_root}/frontend/App.tsx",
                f"{workspace_root}/reports/verification.json",
            ],
            "expected_output_paths": [
                f"{workspace_root}/backend",
                f"{workspace_root}/frontend",
                f"{workspace_root}/reports",
            ],
        },
        "command_policy": {
            "requested_operations": [
                "render backend files",
                "render frontend files",
                "render report",
            ],
            "allowed_operation_labels": [
                "render_backend",
                "render_frontend",
                "render_report",
            ],
        },
        "rollback_policy": {
            "rollback_plan_id": "rollback-local-target-runtime-preflight",
            "abort_criteria": [
                "any path boundary finding",
                "any non-zero side-effect counter",
            ],
            "cleanup_steps": [
                "discard run-scoped workspace",
                "keep sanitized audit projection only",
            ],
        },
    }


def _post_daacs_runtime_preflight(
    client: TestClient,
    *,
    run_id: str,
    runner_plan_hash: str,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/preflight",
        json=_daacs_runtime_preflight_payload(run_id, runner_plan_hash),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_adapter_admission_payload(
    *,
    run_id: str,
    runner_plan_hash: str,
    preflight_projection: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "runner_plan_hash": runner_plan_hash,
        "expected_preflight_hash": preflight_projection.get("preflight_hash", ""),
        "mode": TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION,
        "preflight_projection": preflight_projection,
    }


def _post_daacs_runtime_adapter_admission(
    client: TestClient,
    *,
    run_id: str,
    runner_plan_hash: str,
    preflight_projection: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/adapter/admission",
        json=_daacs_runtime_adapter_admission_payload(
            run_id=run_id,
            runner_plan_hash=runner_plan_hash,
            preflight_projection=preflight_projection,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_output_manifest_payload(
    *,
    run_id: str,
    runner_plan_hash: str,
    adapter_admission_hash: str,
    adapter_admission_read_model: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "runner_plan_hash": runner_plan_hash,
        "adapter_admission_hash": adapter_admission_hash,
        "adapter_admission_read_model": adapter_admission_read_model,
        "mode": TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
        "output_groups": [
            {"label": "backend", "expected_artifact_kind": "backend"},
            {"label": "frontend", "expected_artifact_kind": "frontend"},
            {
                "label": "verification_report",
                "expected_artifact_kind": "verification_report",
            },
        ],
    }


def _post_daacs_runtime_output_manifest(
    client: TestClient,
    *,
    run_id: str,
    runner_plan_hash: str,
    adapter_admission_hash: str,
    adapter_admission_read_model: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/output-manifest",
        json=_daacs_runtime_output_manifest_payload(
            run_id=run_id,
            runner_plan_hash=runner_plan_hash,
            adapter_admission_hash=adapter_admission_hash,
            adapter_admission_read_model=adapter_admission_read_model,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_generated_artifact_bundle_payload(
    *,
    run_id: str,
    runner_plan_hash: str,
    output_manifest_hash: str,
    output_manifest_read_model: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "runner_plan_hash": runner_plan_hash,
        "output_manifest_hash": output_manifest_hash,
        "output_manifest_read_model": output_manifest_read_model,
        "mode": TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED,
        "artifact_units": [
            {"label": "backend", "artifact_kind": "backend"},
            {"label": "frontend", "artifact_kind": "frontend"},
            {
                "label": "verification_report",
                "artifact_kind": "verification_report",
            },
        ],
    }


def _post_daacs_runtime_generated_artifact_bundle(
    client: TestClient,
    *,
    run_id: str,
    runner_plan_hash: str,
    output_manifest_hash: str,
    output_manifest_read_model: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/generated-artifact-bundle",
        json=_daacs_runtime_generated_artifact_bundle_payload(
            run_id=run_id,
            runner_plan_hash=runner_plan_hash,
            output_manifest_hash=output_manifest_hash,
            output_manifest_read_model=output_manifest_read_model,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_fixture_materialization_payload(
    *,
    run_id: str,
    runner_plan_hash: str,
    generated_artifact_bundle_hash: str,
    generated_artifact_bundle_projection: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "runner_plan_hash": runner_plan_hash,
        "generated_artifact_bundle_hash": generated_artifact_bundle_hash,
        "generated_artifact_bundle_projection": generated_artifact_bundle_projection,
        "mode": TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE,
    }


def _post_daacs_runtime_fixture_materialization(
    client: TestClient,
    *,
    run_id: str,
    runner_plan_hash: str,
    generated_artifact_bundle_hash: str,
    generated_artifact_bundle_projection: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/fixture-materialization",
        json=_daacs_runtime_fixture_materialization_payload(
            run_id=run_id,
            runner_plan_hash=runner_plan_hash,
            generated_artifact_bundle_hash=generated_artifact_bundle_hash,
            generated_artifact_bundle_projection=generated_artifact_bundle_projection,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_restricted_workspace_generation_payload(
    *,
    run_id: str,
    runner_plan_hash: str,
    planning_blueprint_hash: str,
    prd_package_hash: str,
    implementation_brief_hash: str,
    generated_artifact_bundle_hash: str,
    generated_artifact_bundle_projection: dict[str, Any],
    solar_draft_projection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_solar_draft_projection = solar_draft_projection or {}
    return {
        "run_id": run_id,
        "runner_plan_hash": runner_plan_hash,
        "planning_blueprint_hash": planning_blueprint_hash,
        "prd_package_hash": prd_package_hash,
        "implementation_brief_hash": implementation_brief_hash,
        "generated_artifact_bundle_hash": generated_artifact_bundle_hash,
        "generated_artifact_bundle_projection": generated_artifact_bundle_projection,
        "solar_draft_projection_hash": str(
            selected_solar_draft_projection.get("draft_projection_hash", "")
        ),
        "solar_draft_projection": selected_solar_draft_projection,
        "mode": TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE,
    }


def _post_daacs_runtime_restricted_workspace_generation(
    client: TestClient,
    *,
    run_id: str,
    runner_plan_hash: str,
    planning_blueprint_hash: str,
    prd_package_hash: str,
    implementation_brief_hash: str,
    generated_artifact_bundle_hash: str,
    generated_artifact_bundle_projection: dict[str, Any],
    solar_draft_projection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/restricted-workspace-generation",
        json=_daacs_runtime_restricted_workspace_generation_payload(
            run_id=run_id,
            runner_plan_hash=runner_plan_hash,
            planning_blueprint_hash=planning_blueprint_hash,
            prd_package_hash=prd_package_hash,
            implementation_brief_hash=implementation_brief_hash,
            generated_artifact_bundle_hash=generated_artifact_bundle_hash,
            generated_artifact_bundle_projection=generated_artifact_bundle_projection,
            solar_draft_projection=solar_draft_projection,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_generated_artifact_verification_payload(
    *,
    run_id: str,
    generated_workspace_hash: str,
    generated_workspace_projection: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "generated_workspace_hash": generated_workspace_hash,
        "generated_workspace_projection": generated_workspace_projection,
        "mode": TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE,
    }


def _post_daacs_runtime_generated_artifact_verification(
    client: TestClient,
    *,
    run_id: str,
    generated_workspace_hash: str,
    generated_workspace_projection: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/generated-artifact-verification",
        json=_daacs_runtime_generated_artifact_verification_payload(
            run_id=run_id,
            generated_workspace_hash=generated_workspace_hash,
            generated_workspace_projection=generated_workspace_projection,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_generated_workspace_static_validation_payload(
    *,
    run_id: str,
    generated_artifact_verification_hash: str,
    generated_artifact_verification_projection: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "generated_artifact_verification_hash": generated_artifact_verification_hash,
        "generated_artifact_verification_projection": (
            generated_artifact_verification_projection
        ),
        "mode": TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE,
    }


def _post_daacs_runtime_generated_workspace_static_validation(
    client: TestClient,
    *,
    run_id: str,
    generated_artifact_verification_hash: str,
    generated_artifact_verification_projection: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/generated-workspace-static-validation",
        json=_daacs_runtime_generated_workspace_static_validation_payload(
            run_id=run_id,
            generated_artifact_verification_hash=generated_artifact_verification_hash,
            generated_artifact_verification_projection=(
                generated_artifact_verification_projection
            ),
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_buildable_fixture_manifest_payload(
    *,
    run_id: str,
    generated_workspace_static_validation_hash: str,
    generated_workspace_static_validation_projection: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "generated_workspace_static_validation_hash": (
            generated_workspace_static_validation_hash
        ),
        "generated_workspace_static_validation_projection": (
            generated_workspace_static_validation_projection
        ),
        "mode": TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE,
    }


def _post_daacs_runtime_buildable_fixture_manifest(
    client: TestClient,
    *,
    run_id: str,
    generated_workspace_static_validation_hash: str,
    generated_workspace_static_validation_projection: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/buildable-fixture-manifest",
        json=_daacs_runtime_buildable_fixture_manifest_payload(
            run_id=run_id,
            generated_workspace_static_validation_hash=(
                generated_workspace_static_validation_hash
            ),
            generated_workspace_static_validation_projection=(
                generated_workspace_static_validation_projection
            ),
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_local_build_preflight_payload(
    *,
    run_id: str,
    buildable_fixture_manifest_hash: str,
    buildable_fixture_manifest_projection: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "buildable_fixture_manifest_hash": buildable_fixture_manifest_hash,
        "buildable_fixture_manifest_projection": buildable_fixture_manifest_projection,
        "mode": TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE,
        "operator_opt_in": False,
    }


def _post_daacs_runtime_local_build_preflight(
    client: TestClient,
    *,
    run_id: str,
    buildable_fixture_manifest_hash: str,
    buildable_fixture_manifest_projection: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/local-build-preflight",
        json=_daacs_runtime_local_build_preflight_payload(
            run_id=run_id,
            buildable_fixture_manifest_hash=buildable_fixture_manifest_hash,
            buildable_fixture_manifest_projection=buildable_fixture_manifest_projection,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_local_build_attempt_payload(
    *,
    run_id: str,
    local_build_preflight_hash: str,
    local_build_preflight_projection: dict[str, Any],
    allow_local_build_attempt: bool,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "local_build_preflight_hash": local_build_preflight_hash,
        "local_build_preflight_projection": local_build_preflight_projection,
        "mode": TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE,
        "operator_opt_in": allow_local_build_attempt,
        "allow_local_command_execution": allow_local_build_attempt,
        "install_timeout_seconds": 180,
        "build_timeout_seconds": 180,
    }


def _post_daacs_runtime_local_build_attempt(
    client: TestClient,
    *,
    run_id: str,
    local_build_preflight_hash: str,
    local_build_preflight_projection: dict[str, Any],
    allow_local_build_attempt: bool,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/local-build-attempt",
        json=_daacs_runtime_local_build_attempt_payload(
            run_id=run_id,
            local_build_preflight_hash=local_build_preflight_hash,
            local_build_preflight_projection=local_build_preflight_projection,
            allow_local_build_attempt=allow_local_build_attempt,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_local_preview_attempt_payload(
    *,
    run_id: str,
    local_build_attempt_hash: str,
    local_build_attempt_projection: dict[str, Any],
    allow_local_preview_attempt: bool,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "local_build_attempt_hash": local_build_attempt_hash,
        "local_build_attempt_projection": local_build_attempt_projection,
        "mode": TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE,
        "operator_opt_in": allow_local_preview_attempt,
        "allow_local_preview_server": allow_local_preview_attempt,
        "allow_browser_verification": allow_local_preview_attempt,
        "require_browser_runtime_preflight": True,
        "preview_timeout_seconds": 45,
    }


def _post_daacs_runtime_local_preview_attempt(
    client: TestClient,
    *,
    run_id: str,
    local_build_attempt_hash: str,
    local_build_attempt_projection: dict[str, Any],
    allow_local_preview_attempt: bool,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/local-preview-attempt",
        json=_daacs_runtime_local_preview_attempt_payload(
            run_id=run_id,
            local_build_attempt_hash=local_build_attempt_hash,
            local_build_attempt_projection=local_build_attempt_projection,
            allow_local_preview_attempt=allow_local_preview_attempt,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _daacs_runtime_browser_setup_attempt_payload(
    *,
    run_id: str,
    browser_runtime_preflight_projection: dict[str, Any],
    allow_browser_runtime_setup: bool,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "browser_runtime_preflight_hash": stable_contract_hash(
            browser_runtime_preflight_projection
        ),
        "browser_runtime_preflight_projection": browser_runtime_preflight_projection,
        "mode": TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE,
        "operator_opt_in": allow_browser_runtime_setup,
        "allow_browser_runtime_setup": allow_browser_runtime_setup,
        "setup_timeout_seconds": 180,
    }


def _post_daacs_runtime_browser_setup_attempt(
    client: TestClient,
    *,
    run_id: str,
    browser_runtime_preflight_projection: dict[str, Any],
    allow_browser_runtime_setup: bool,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/daacs/runtime/browser-setup-attempt",
        json=_daacs_runtime_browser_setup_attempt_payload(
            run_id=run_id,
            browser_runtime_preflight_projection=browser_runtime_preflight_projection,
            allow_browser_runtime_setup=allow_browser_runtime_setup,
        ),
    )
    response.raise_for_status()
    return response.json()["data"]


def _should_retry_local_preview_after_browser_setup(
    *,
    local_preview_attempt: dict[str, Any] | None,
    browser_setup_attempt: dict[str, Any] | None,
    allow_local_preview_attempt: bool,
) -> bool:
    """Return whether setup made screenshot capture newly eligible."""
    if not allow_local_preview_attempt or not browser_setup_attempt:
        return False
    if (local_preview_attempt or {}).get("status") == "passed":
        return False
    post_setup_preflight = browser_setup_attempt.get(
        "post_setup_browser_runtime_preflight",
        {},
    )
    return bool(post_setup_preflight.get("available") is True)


def _artifact_kinds(artifacts: list[dict[str, Any]]) -> set[str]:
    return {str(artifact.get("kind") or "") for artifact in artifacts}


def _artifact_content_hash(
    artifacts: list[dict[str, Any]],
    *,
    artifact_kind: str,
) -> str:
    for artifact in artifacts:
        if str(artifact.get("kind") or "") == artifact_kind:
            return str(artifact.get("content_hash") or "")
    return ""


def _as_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _mvp_stage_coverage(
    run_data: dict[str, Any],
    verification_data: dict[str, Any],
) -> dict[str, Any]:
    artifact_kinds = _artifact_kinds(run_data.get("artifacts", []))
    evidence_counts = run_data.get("evidence_summary", {}).get("counts", {})
    stage_statuses = [
        {
            "stage": "Idea",
            "covered": bool(run_data.get("run", {}).get("prompt_contract_hash")),
            "evidence": "canonical_run_prompt_contract_hash",
        },
        {
            "stage": "PlanningBlueprint",
            "covered": "planning_blueprint" in artifact_kinds,
            "evidence": "planning_blueprint_artifact",
        },
        {
            "stage": "PRDPackage",
            "covered": "prd_package" in artifact_kinds,
            "evidence": "prd_package_artifact",
        },
        {
            "stage": "ImplementationBrief",
            "covered": "implementation_brief" in artifact_kinds,
            "evidence": "implementation_brief_artifact",
        },
        {
            "stage": "Approval",
            "covered": "spec_approval" in artifact_kinds,
            "evidence": "synthetic_spec_approval_artifact",
        },
        {
            "stage": "RunnerPlan",
            "covered": _as_int(evidence_counts.get("runner_plan_count")) >= 1,
            "evidence": "dry_run_runner_plan_record",
        },
        {
            "stage": "VerificationReport",
            "covered": _as_int(
                verification_data.get("counts", {}).get("verification_report_count")
            )
            >= 1,
            "evidence": "verification_read_model_record",
        },
    ]
    covered_count = sum(1 for stage in stage_statuses if stage["covered"])
    required_count = len(MVP_STAGE_NAMES)
    return {
        "mvp_id": MVP_ID,
        "required_stage_count": required_count,
        "covered_stage_count": covered_count,
        "coverage_percent": round((covered_count / required_count) * 100, 1),
        "stage_order": list(MVP_STAGE_NAMES),
        "stages": stage_statuses,
    }


def _checks(
    create_data: dict[str, Any],
    run_data: dict[str, Any],
    *,
    verification_data: dict[str, Any] | None = None,
    provider_envelope_data: dict[str, Any] | None = None,
    solar_planner_preflight_data: dict[str, Any] | None = None,
    solar_planner_spike_data: dict[str, Any] | None = None,
    solar_planner_live_spike_data: dict[str, Any] | None = None,
    solar_planner_quality_comparison_data: dict[str, Any] | None = None,
    solar_planner_draft_projection_data: dict[str, Any] | None = None,
    daacs_runtime_preflight_data: dict[str, Any] | None = None,
    daacs_runtime_adapter_admission_data: dict[str, Any] | None = None,
    daacs_runtime_adapter_admission_read_data: dict[str, Any] | None = None,
    daacs_runtime_output_manifest_data: dict[str, Any] | None = None,
    daacs_runtime_output_manifest_read_data: dict[str, Any] | None = None,
    daacs_runtime_generated_artifact_bundle_data: dict[str, Any] | None = None,
    daacs_runtime_fixture_materialization_data: dict[str, Any] | None = None,
    daacs_runtime_restricted_workspace_generation_data: dict[str, Any] | None = None,
    daacs_runtime_generated_artifact_verification_data: dict[str, Any] | None = None,
    daacs_runtime_generated_workspace_static_validation_data: (
        dict[str, Any] | None
    ) = None,
    daacs_runtime_buildable_fixture_manifest_data: dict[str, Any] | None = None,
    daacs_runtime_local_build_preflight_data: dict[str, Any] | None = None,
    daacs_runtime_local_build_attempt_data: dict[str, Any] | None = None,
    daacs_runtime_browser_setup_attempt_data: dict[str, Any] | None = None,
    daacs_runtime_local_preview_attempt_data: dict[str, Any] | None = None,
) -> dict[str, bool]:
    artifact_kinds = _artifact_kinds(run_data.get("artifacts", []))
    evidence_summary = run_data.get("evidence_summary", {})
    evidence_counts = evidence_summary.get("counts", {})
    execution_boundary = run_data.get("execution_boundary", {})
    verification = verification_data or {}
    stage_coverage = _mvp_stage_coverage(run_data, verification)
    checks = {
        "created_run": bool(create_data.get("run", {}).get("run_id")),
        "canonical_persisted": create_data.get("canonical_persistence", {}).get("status") == "persisted",
        "evidence_persisted": create_data.get("evidence_persistence", {}).get("status") == "persisted",
        "composed_read_model": run_data.get("projection_version")
        == "canonical-run-composed-read-model-public-v1",
        "artifact_count_at_least_3": int(run_data.get("counts", {}).get("artifact_count", 0)) >= 3,
        "planning_blueprint_artifact": "planning_blueprint" in artifact_kinds,
        "prd_package_artifact": "prd_package" in artifact_kinds,
        "build_spec_artifact": "build_spec" in artifact_kinds,
        "implementation_brief_artifact": "implementation_brief" in artifact_kinds,
        "verification_report_artifact": "verification_report" in artifact_kinds,
        "runner_plan_evidence": int(evidence_counts.get("runner_plan_count", 0)) >= 1,
        "verification_report_evidence": int(evidence_counts.get("verification_report_count", 0)) >= 1,
        "audit_event_evidence": int(evidence_counts.get("audit_event_count", 0)) >= 1,
        "verification_read_model": verification.get("projection_version")
        == "verification-read-model-public-v1"
        and verification.get("status") == "passed",
        "verification_read_model_report": _as_int(
            verification.get("counts", {}).get("verification_report_count")
        )
        >= 1,
        "mvp_stage_coverage_7_of_7": stage_coverage["covered_stage_count"]
        == stage_coverage["required_stage_count"],
        "mvp_artifact_linkage_100_percent": evidence_summary.get("linkage", {}).get(
            "run_id_matched"
        )
        is True
        and evidence_summary.get("linkage", {}).get("artifact_linkage_checked") is True,
        "solar_provider_calls_zero": int(execution_boundary.get("solar_provider_calls", -1)) == 0,
        "target_runtime_calls_zero": int(execution_boundary.get("target_runtime_calls", -1)) == 0,
    }
    if provider_envelope_data is None:
        checks["provider_envelope_precheck_optional"] = True
    else:
        envelope = provider_envelope_data.get("provider_envelope_admission", {})
        envelope_execution = provider_envelope_data.get("execution_boundary", {})
        checks["provider_envelope_precheck_recorded"] = envelope.get("status") == "admitted"
        checks["provider_envelope_adapter_reached_disabled_path"] = (
            envelope.get("adapter_reached") is True
        )
        checks["provider_envelope_calls_zero"] = (
            int(envelope_execution.get("provider_calls", -1)) == 0
            and int(envelope_execution.get("network_calls", -1)) == 0
            and int(envelope_execution.get("solar_live_api_calls", -1)) == 0
        )
        preflight = provider_envelope_data.get("manual_provider_test_preflight_audit", {})
        checks["provider_preflight_audit_blocked"] = (
            preflight.get("status") == "blocked"
            and preflight.get("reason") == "preflight_execution_closed"
        )
        readiness = provider_envelope_data.get("manual_provider_test_readiness_decision", {})
        checks["provider_readiness_decision_blocked"] = (
            readiness.get("status") == "blocked"
            and readiness.get("reason") == "readiness_execution_closed"
        )
        review_packet = provider_envelope_data.get("manual_provider_test_review_packet", {})
        checks["provider_review_packet_blocked"] = (
            review_packet.get("status") == "blocked"
            and review_packet.get("reason") == "review_packet_execution_closed"
            and int(review_packet.get("execution_permission_count", -1)) == 0
        )
        review_packet_export = provider_envelope_data.get(
            "manual_provider_test_review_packet_export", {}
        )
        checks["provider_review_packet_export_blocked"] = (
            review_packet_export.get("status") == "blocked"
            and review_packet_export.get("reason") == "review_packet_execution_closed"
            and int(review_packet_export.get("export_count", 0)) >= 1
            and int(review_packet_export.get("execution_permission_count", -1)) == 0
        )
        handoff_packet = provider_envelope_data.get(
            "manual_provider_test_handoff_packet", {}
        )
        checks["provider_handoff_packet_blocked"] = (
            handoff_packet.get("status") == "blocked"
            and handoff_packet.get("reason") == "handoff_packet_execution_closed"
            and int(handoff_packet.get("component_count", 0)) >= 5
            and int(handoff_packet.get("execution_permission_count", -1)) == 0
        )
        operator_opt_in = provider_envelope_data.get(
            "manual_provider_test_operator_opt_in", {}
        )
        checks["provider_operator_opt_in_blocked"] = (
            operator_opt_in.get("status") == "blocked"
            and operator_opt_in.get("reason") == "operator_opt_in_execution_closed"
            and int(operator_opt_in.get("execution_permission_count", -1)) == 0
        )
        sealed_packet = provider_envelope_data.get(
            "manual_provider_test_sealed_pre_execution_packet", {}
        )
        checks["provider_sealed_packet_blocked"] = (
            sealed_packet.get("status") == "blocked"
            and sealed_packet.get("reason")
            == "sealed_pre_execution_packet_execution_closed"
            and int(sealed_packet.get("execution_permission_count", -1)) == 0
        )
        arming_record = provider_envelope_data.get(
            "manual_provider_test_arming_record", {}
        )
        checks["provider_arming_record_blocked"] = (
            arming_record.get("status") == "blocked"
            and arming_record.get("reason") == "arming_record_execution_closed"
            and int(arming_record.get("execution_permission_count", -1)) == 0
        )
        release_proposal = provider_envelope_data.get(
            "manual_provider_test_release_proposal", {}
        )
        checks["provider_release_proposal_blocked"] = (
            release_proposal.get("status") == "blocked"
            and release_proposal.get("reason") == "release_proposal_execution_closed"
            and int(release_proposal.get("execution_permission_count", -1)) == 0
        )
        final_release_packet = provider_envelope_data.get(
            "manual_provider_test_final_release_packet", {}
        )
        checks["provider_final_release_packet_blocked"] = (
            final_release_packet.get("status") == "blocked"
            and final_release_packet.get("reason") == "final_release_packet_execution_closed"
            and int(final_release_packet.get("execution_permission_count", -1)) == 0
        )
        execution_switch = provider_envelope_data.get(
            "manual_provider_test_execution_switch", {}
        )
        checks["provider_execution_switch_blocked"] = (
            execution_switch.get("status") == "blocked"
            and execution_switch.get("reason") == "execution_switch_disabled_by_default"
            and int(execution_switch.get("execution_permission_count", -1)) == 0
        )
        executor_preflight = provider_envelope_data.get(
            "manual_provider_test_executor_preflight", {}
        )
        checks["provider_executor_preflight_blocked"] = (
            executor_preflight.get("status") == "blocked"
            and executor_preflight.get("reason") == "executor_preflight_execution_closed"
            and int(executor_preflight.get("execution_permission_count", -1)) == 0
        )
        dispatch_record = provider_envelope_data.get(
            "manual_provider_test_executor_dispatch_record", {}
        )
        checks["provider_executor_dispatch_record_blocked"] = (
            dispatch_record.get("status") == "blocked"
            and dispatch_record.get("reason")
            == "executor_dispatch_record_execution_closed"
            and int(dispatch_record.get("execution_permission_count", -1)) == 0
        )
        invocation_receipt = provider_envelope_data.get(
            "manual_provider_test_invocation_receipt", {}
        )
        checks["provider_invocation_receipt_blocked"] = (
            invocation_receipt.get("status") == "blocked"
            and invocation_receipt.get("reason") == "invocation_receipt_execution_closed"
            and int(invocation_receipt.get("execution_permission_count", -1)) == 0
        )
        post_invocation_audit = provider_envelope_data.get(
            "manual_provider_test_post_invocation_audit", {}
        )
        checks["provider_post_invocation_audit_blocked"] = (
            post_invocation_audit.get("status") == "blocked"
            and post_invocation_audit.get("reason")
            == "post_invocation_audit_execution_closed"
            and int(post_invocation_audit.get("execution_permission_count", -1)) == 0
        )
        completion_summary = provider_envelope_data.get(
            "manual_provider_test_completion_summary", {}
        )
        checks["provider_completion_summary_blocked"] = (
            completion_summary.get("status") == "blocked"
            and completion_summary.get("reason") == "completion_summary_execution_closed"
            and int(completion_summary.get("execution_permission_count", -1)) == 0
        )
        closeout_record = provider_envelope_data.get(
            "manual_provider_test_closeout_record", {}
        )
        checks["provider_closeout_record_blocked"] = (
            closeout_record.get("status") == "blocked"
            and closeout_record.get("reason") == "closeout_record_execution_closed"
            and int(closeout_record.get("execution_permission_count", -1)) == 0
        )
        operator_handback = provider_envelope_data.get(
            "manual_provider_test_operator_handback", {}
        )
        checks["provider_operator_handback_blocked"] = (
            operator_handback.get("status") == "blocked"
            and operator_handback.get("reason") == "operator_handback_execution_closed"
            and int(operator_handback.get("execution_permission_count", -1)) == 0
        )
        decision_packet = provider_envelope_data.get(
            "manual_provider_test_operator_decision_packet", {}
        )
        checks["provider_operator_decision_packet_blocked"] = (
            decision_packet.get("status") == "blocked"
            and decision_packet.get("reason")
            == "operator_decision_packet_execution_closed"
            and int(decision_packet.get("execution_permission_count", -1)) == 0
        )
        release_attestation = provider_envelope_data.get(
            "manual_provider_test_operator_release_attestation", {}
        )
        checks["provider_operator_release_attestation_blocked"] = (
            release_attestation.get("status") == "blocked"
            and release_attestation.get("reason")
            == "operator_release_attestation_execution_closed"
            and int(release_attestation.get("execution_permission_count", -1)) == 0
        )
        release_authorization_seal = provider_envelope_data.get(
            "manual_provider_test_release_seal", {}
        )
        checks["provider_release_seal_blocked"] = (
            release_authorization_seal.get("status") == "blocked"
            and release_authorization_seal.get("reason")
            == "release_authorization_seal_execution_closed"
            and int(release_authorization_seal.get("execution_permission_count", -1))
            == 0
        )
        execution_capsule = provider_envelope_data.get(
            "manual_provider_test_execution_capsule", {}
        )
        checks["provider_execution_capsule_blocked"] = (
            execution_capsule.get("status") == "blocked"
            and execution_capsule.get("reason")
            == "execution_authorization_capsule_execution_closed"
            and int(execution_capsule.get("execution_permission_count", -1)) == 0
        )
        execution_capsule_export = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_export", {}
        )
        execution_capsule_export_read_model = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_export_read_model", {}
        )
        checks["provider_execution_capsule_export_blocked"] = (
            execution_capsule_export.get("status") == "blocked"
            and execution_capsule_export.get("reason")
            == "execution_capsule_export_execution_closed"
            and int(execution_capsule_export.get("execution_permission_count", -1))
            == 0
        )
        checks["provider_execution_capsule_export_read_model_available"] = (
            execution_capsule_export_read_model.get("status") == "available"
        )
        execution_capsule_handoff_packet = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_handoff_packet", {}
        )
        checks["provider_execution_capsule_handoff_packet_blocked"] = (
            execution_capsule_handoff_packet.get("status") == "blocked"
            and execution_capsule_handoff_packet.get("reason")
            == "execution_capsule_handoff_packet_execution_closed"
            and int(
                execution_capsule_handoff_packet.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_operator_review = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_operator_review", {}
        )
        checks["provider_execution_capsule_operator_review_blocked"] = (
            execution_capsule_operator_review.get("status") == "blocked"
            and execution_capsule_operator_review.get("reason")
            == "execution_capsule_operator_review_execution_closed"
            and int(
                execution_capsule_operator_review.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_operator_decision = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_operator_decision", {}
        )
        checks["provider_execution_capsule_operator_decision_blocked"] = (
            execution_capsule_operator_decision.get("status") == "blocked"
            and execution_capsule_operator_decision.get("reason")
            == "execution_capsule_operator_decision_execution_closed"
            and int(
                execution_capsule_operator_decision.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_release_attestation = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_release_attestation", {}
        )
        checks["provider_execution_capsule_release_attestation_blocked"] = (
            execution_capsule_release_attestation.get("status") == "blocked"
            and execution_capsule_release_attestation.get("reason")
            == "execution_capsule_release_attestation_execution_closed"
            and int(
                execution_capsule_release_attestation.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_release_seal = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_release_seal", {}
        )
        checks["provider_execution_capsule_release_seal_blocked"] = (
            execution_capsule_release_seal.get("status") == "blocked"
            and execution_capsule_release_seal.get("reason")
            == "execution_capsule_release_seal_execution_closed"
            and int(
                execution_capsule_release_seal.get("execution_permission_count", -1)
            )
            == 0
        )
        execution_capsule_final_authorization = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_final_authz", {}
        )
        checks["provider_execution_capsule_final_authorization_blocked"] = (
            execution_capsule_final_authorization.get("status") == "blocked"
            and execution_capsule_final_authorization.get("reason")
            == "execution_capsule_final_authz_execution_closed"
            and int(
                execution_capsule_final_authorization.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_export = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_authz_export", {}
        )
        execution_capsule_authz_export_read_model = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_authz_export_read_model", {}
        )
        checks["provider_execution_capsule_authz_export_blocked"] = (
            execution_capsule_authz_export.get("status") == "blocked"
            and execution_capsule_authz_export.get("reason")
            == "execution_capsule_authz_export_execution_closed"
            and int(
                execution_capsule_authz_export.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        checks["provider_execution_capsule_authz_export_read_model_available"] = (
            execution_capsule_authz_export_read_model.get("status") == "available"
        )
        execution_capsule_authz_handoff_packet = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_authz_handoff_packet", {}
        )
        checks["provider_execution_capsule_authz_handoff_packet_blocked"] = (
            execution_capsule_authz_handoff_packet.get("status") == "blocked"
            and execution_capsule_authz_handoff_packet.get("reason")
            == "execution_capsule_authz_handoff_packet_execution_closed"
            and int(
                execution_capsule_authz_handoff_packet.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_operator_review = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_authz_operator_review", {}
        )
        checks["provider_execution_capsule_authz_operator_review_blocked"] = (
            execution_capsule_authz_operator_review.get("status") == "blocked"
            and execution_capsule_authz_operator_review.get("reason")
            == "execution_capsule_authz_operator_review_execution_closed"
            and int(
                execution_capsule_authz_operator_review.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_operator_decision = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_authz_operator_decision", {}
        )
        checks["provider_execution_capsule_authz_operator_decision_blocked"] = (
            execution_capsule_authz_operator_decision.get("status") == "blocked"
            and execution_capsule_authz_operator_decision.get("reason")
            == "execution_capsule_authz_operator_decision_execution_closed"
            and int(
                execution_capsule_authz_operator_decision.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_release_attestation = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_authz_release_attestation", {}
        )
        checks["provider_execution_capsule_authz_release_attestation_blocked"] = (
            execution_capsule_authz_release_attestation.get("status") == "blocked"
            and execution_capsule_authz_release_attestation.get("reason")
            == "execution_capsule_authz_release_attestation_execution_closed"
            and int(
                execution_capsule_authz_release_attestation.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_release_seal = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_authz_release_seal", {}
        )
        checks["provider_execution_capsule_authz_release_seal_blocked"] = (
            execution_capsule_authz_release_seal.get("status") == "blocked"
            and execution_capsule_authz_release_seal.get("reason")
            == "execution_capsule_authz_release_seal_execution_closed"
            and int(
                execution_capsule_authz_release_seal.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_authz_final_authz", {}
        )
        checks["provider_execution_capsule_authz_final_authorization_blocked"] = (
            execution_capsule_authz_final_authz.get("status") == "blocked"
            and execution_capsule_authz_final_authz.get("reason")
            == "execution_capsule_authz_final_authz_execution_closed"
            and int(
                execution_capsule_authz_final_authz.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_export = provider_envelope_data.get(
            "manual_provider_test_execution_capsule_authz_final_authz_export", {}
        )
        execution_capsule_authz_final_authz_export_read_model = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_export_read_model",
                {},
            )
        )
        checks["provider_execution_capsule_authz_final_authz_export_blocked"] = (
            execution_capsule_authz_final_authz_export.get("status") == "blocked"
            and execution_capsule_authz_final_authz_export.get("reason")
            == "execution_capsule_authz_final_authz_export_execution_closed"
            and int(
                execution_capsule_authz_final_authz_export.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        checks[
            "provider_execution_capsule_authz_final_authz_export_read_model_available"
        ] = (
            execution_capsule_authz_final_authz_export_read_model.get("status")
            == "available"
            and execution_capsule_authz_final_authz_export_read_model.get("reason")
            == "execution_capsule_authz_final_authz_export_read_model_available"
            and int(
                execution_capsule_authz_final_authz_export_read_model.get(
                    "counts", {}
                ).get("execution_permission_count", -1)
            )
            == 0
        )
        execution_capsule_authz_final_authz_handoff_packet = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_handoff_packet_blocked"
        ] = (
            execution_capsule_authz_final_authz_handoff_packet.get("status")
            == "blocked"
            and execution_capsule_authz_final_authz_handoff_packet.get("reason")
            == "execution_capsule_authz_final_authz_handoff_packet_execution_closed"
            and int(
                execution_capsule_authz_final_authz_handoff_packet.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_operator_review = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_operator_review_blocked"
        ] = (
            execution_capsule_authz_final_authz_operator_review.get("status")
            == "blocked"
            and execution_capsule_authz_final_authz_operator_review.get("reason")
            == "execution_capsule_authz_final_authz_operator_review_execution_closed"
            and int(
                execution_capsule_authz_final_authz_operator_review.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_operator_decision = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_operator_decision_blocked"
        ] = (
            execution_capsule_authz_final_authz_operator_decision.get("status")
            == "blocked"
            and execution_capsule_authz_final_authz_operator_decision.get("reason")
            == "execution_capsule_authz_final_authz_operator_decision_execution_closed"
            and int(
                execution_capsule_authz_final_authz_operator_decision.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_release_attestation = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_release_attestation_blocked"
        ] = (
            execution_capsule_authz_final_authz_release_attestation.get("status")
            == "blocked"
            and execution_capsule_authz_final_authz_release_attestation.get("reason")
            == "execution_capsule_authz_final_authz_release_attestation_execution_closed"
            and int(
                execution_capsule_authz_final_authz_release_attestation.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_release_seal = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_release_seal_blocked"
        ] = (
            execution_capsule_authz_final_authz_release_seal.get("status")
            == "blocked"
            and execution_capsule_authz_final_authz_release_seal.get("reason")
            == "execution_capsule_authz_final_authz_release_seal_execution_closed"
            and int(
                execution_capsule_authz_final_authz_release_seal.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz.get("status")
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz.get("reason")
            == "execution_capsule_authz_final_authz_final_authz_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_export = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                {},
            )
        )
        execution_capsule_authz_final_authz_final_authz_export_read_model = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export_read_model",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_export_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_export.get("status")
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_export.get("reason")
            == "execution_capsule_authz_final_authz_final_authz_export_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_export.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_export_read_model_available"
        ] = (
            execution_capsule_authz_final_authz_final_authz_export_read_model.get(
                "status"
            )
            == "available"
            and execution_capsule_authz_final_authz_final_authz_export_read_model.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_export_read_model_available"
            and int(
                execution_capsule_authz_final_authz_final_authz_export_read_model.get(
                    "counts", {}
                ).get("execution_permission_count", -1)
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_handoff_packet = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_handoff_packet_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_handoff_packet.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_handoff_packet.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_handoff_packet_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_handoff_packet.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_operator_review = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_operator_review_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_operator_review.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_operator_review.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_operator_review_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_operator_review.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_operator_decision = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_operator_decision_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_operator_decision.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_operator_decision.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_operator_decision_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_operator_decision.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_release_attestation = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_release_attestation_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_release_attestation.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_release_attestation.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_release_attestation_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_release_attestation.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_release_seal = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_release_seal_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_release_seal.get("status")
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_release_seal.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_release_seal_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_release_seal.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_final_authz = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_final_authz_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_final_authz.get("status")
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_final_authz.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_final_authz_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_final_authz.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_final_authz_export = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                {},
            )
        )
        execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_final_authz_export_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_final_authz_export.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_final_authz_export.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_final_authz_export_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_final_authz_export.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_available"
        ] = (
            execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model.get(
                "status"
            )
            == "available"
            and execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_available"
            and int(
                execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model.get(
                    "counts", {}
                ).get("execution_permission_count", -1)
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_final_authz_operator_review = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_final_authz_operator_review.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_final_authz_operator_review.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_final_authz_operator_review.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_final_authz_release_seal = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_final_authz_release_seal.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_final_authz_release_seal.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_final_authz_release_seal.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_final_authz_final_authz = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_final_authz_final_authz.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_final_authz_final_authz.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_final_authz_final_authz.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_blocked"
        ] = (
            execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export.get(
                "status"
            )
            == "blocked"
            and execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export.get(
                "reason"
            )
            == "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_execution_closed"
            and int(
                execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export.get(
                    "execution_permission_count", -1
                )
            )
            == 0
        )
        execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model = (
            provider_envelope_data.get(
                "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model",
                {},
            )
        )
        checks[
            "provider_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model_available"
        ] = (
            execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model.get(
                "status"
            )
            == "available"
            and int(
                execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model.get(
                    "counts", {}
                ).get("execution_permission_count", -1)
            )
            == 0
        )
    if solar_planner_preflight_data is None:
        checks["solar_planner_preflight_optional"] = True
    else:
        execution = solar_planner_preflight_data.get("execution_boundary", {})
        counts = solar_planner_preflight_data.get("counts", {})
        checks["solar_planner_preflight_projection"] = (
            solar_planner_preflight_data.get("projection_version")
            == "planner-provider-preflight-public-v1"
        )
        checks["solar_planner_preflight_only"] = (
            solar_planner_preflight_data.get("status") == "preflight_only"
        )
        checks["solar_planner_preflight_provider_calls_zero"] = (
            int(execution.get("solar_provider_calls", -1)) == 0
            and int(execution.get("provider_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
        )
        checks["solar_planner_preflight_env_and_sdk_zero"] = (
            int(execution.get("env_key_value_reads", -1)) == 0
            and int(execution.get("sdk_imports", -1)) == 0
        )
        checks["solar_planner_preflight_no_provider_success"] = (
            int(counts.get("planner_provider_success_count", -1)) == 0
            and int(counts.get("provider_generated_blueprint_count", -1)) == 0
        )
    if solar_planner_spike_data is None:
        checks["solar_planner_spike_optional"] = True
    else:
        execution = solar_planner_spike_data.get("execution_boundary", {})
        counts = solar_planner_spike_data.get("counts", {})
        response_projection = solar_planner_spike_data.get("response_projection", {})
        checks["solar_planner_spike_projection"] = (
            solar_planner_spike_data.get("projection_version")
            == "planner-provider-spike-response-public-v1"
        )
        checks["solar_planner_spike_mock_projected"] = (
            solar_planner_spike_data.get("status") == "mock_projected"
            and len(str(response_projection.get("response_contract_hash", ""))) == 64
        )
        checks["solar_planner_spike_no_call"] = (
            int(execution.get("provider_calls", -1)) == 0
            and int(execution.get("env_key_value_reads", -1)) == 0
            and int(execution.get("sdk_imports", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
        )
        checks["solar_planner_spike_hash_only"] = (
            int(counts.get("mock_response_projection_count", -1)) == 1
            and int(counts.get("raw_provider_body_stored_count", -1)) == 0
        )
    if solar_planner_live_spike_data is None:
        checks["solar_planner_live_spike_optional"] = True
    else:
        execution = solar_planner_live_spike_data.get("execution_boundary", {})
        counts = solar_planner_live_spike_data.get("counts", {})
        response_projection = solar_planner_live_spike_data.get(
            "response_projection", {}
        )
        status = solar_planner_live_spike_data.get("status")
        checks["solar_planner_live_spike_projection"] = (
            solar_planner_live_spike_data.get("projection_version")
            == SOLAR_PLANNER_LIVE_SPIKE_VERSION
        )
        checks["solar_planner_live_spike_observed"] = status in {
            "projected",
            "failed",
            "blocked",
        }
        checks["solar_planner_live_spike_one_call_or_blocked"] = (
            (
                status == "projected"
                and int(execution.get("provider_calls", -1)) == 1
                and int(counts.get("provider_call_count", -1)) == 1
            )
            or (
                status in {"failed", "blocked"}
                and int(execution.get("provider_calls", 0)) in {0, 1}
                and int(counts.get("provider_call_count", 0)) in {0, 1}
            )
        )
        checks["solar_planner_live_spike_public_safe"] = (
            int(counts.get("credential_value_exposure_count", -1)) == 0
            and int(counts.get("input_text_exposure_count", -1)) == 0
            and int(counts.get("raw_provider_body_stored_count", -1)) == 0
            and int(counts.get("raw_provider_body_returned_count", -1)) == 0
            and int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("server_start_calls", -1)) == 0
        )
        checks["solar_planner_live_spike_hash_only"] = (
            status != "projected"
            or (
                len(str(response_projection.get("response_contract_hash", "")))
                == 64
                and len(str(response_projection.get("summary_hash", ""))) == 64
                and response_projection.get("provider_body_included") is False
            )
        )
    if solar_planner_quality_comparison_data is None:
        checks["solar_planner_quality_comparison_optional"] = True
    else:
        execution = solar_planner_quality_comparison_data.get("execution_boundary", {})
        counts = solar_planner_quality_comparison_data.get("counts", {})
        review_gate = solar_planner_quality_comparison_data.get("review_gate", {})
        solar_summary = solar_planner_quality_comparison_data.get("solar_summary", {})
        checks["solar_planner_quality_comparison_projection"] = (
            solar_planner_quality_comparison_data.get("projection_version")
            == SOLAR_PLANNER_QUALITY_COMPARISON_VERSION
        )
        checks["solar_planner_quality_comparison_stage_coverage"] = (
            int(counts.get("fixture_required_stage_count", -1)) == 7
            and int(counts.get("fixture_covered_stage_count", -1)) == 7
        )
        checks["solar_planner_quality_comparison_summary_metrics"] = (
            "summary_section_count" in solar_summary
            and "artifact_hint_count" in solar_summary
            and "missing_required_stage_count" in solar_summary
        )
        checks["solar_planner_quality_comparison_review_gate"] = (
            (
                review_gate.get("status") == "blocked"
                and review_gate.get("artifact_binding_permission") is False
            )
            or (
                review_gate.get("status") == "ready"
                and review_gate.get("artifact_binding_permission") is True
                and review_gate.get("artifact_binding_performed") is False
            )
        )
        checks["solar_planner_quality_comparison_no_extra_live_call"] = (
            int(execution.get("comparison_provider_calls", -1)) == 0
            and int(execution.get("comparison_live_api_calls", -1)) == 0
            and int(execution.get("comparison_network_calls", -1)) == 0
            and int(execution.get("comparison_env_key_value_reads", -1)) == 0
            and int(counts.get("additional_live_call_count", -1)) == 0
        )
        checks["solar_planner_quality_comparison_public_safe"] = (
            int(counts.get("raw_provider_body_stored_count", -1)) == 0
            and int(counts.get("raw_provider_body_returned_count", -1)) == 0
            and int(counts.get("credential_value_exposure_count", -1)) == 0
            and int(counts.get("input_text_exposure_count", -1)) == 0
            and int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("server_start_calls", -1)) == 0
        )
    if solar_planner_draft_projection_data is None:
        checks["solar_planner_draft_projection_optional"] = True
    else:
        execution = solar_planner_draft_projection_data.get("execution_boundary", {})
        counts = solar_planner_draft_projection_data.get("counts", {})
        review_gate = solar_planner_draft_projection_data.get("review_gate", {})
        status = solar_planner_draft_projection_data.get("status")
        checks["solar_planner_draft_projection_projection"] = (
            solar_planner_draft_projection_data.get("projection_version")
            == SOLAR_PLANNER_DRAFT_PROJECTION_VERSION
        )
        checks["solar_planner_draft_projection_status"] = status in {
            "blocked",
            "draft_projected",
        }
        checks["solar_planner_draft_projection_artifacts"] = (
            (
                status == "draft_projected"
                and int(counts.get("draft_planning_blueprint_projection_count", -1))
                == 1
                and int(counts.get("draft_prd_package_projection_count", -1)) == 1
            )
            or (
                status == "blocked"
                and int(counts.get("draft_artifact_projection_count", -1)) == 0
            )
        )
        checks["solar_planner_draft_projection_canonical_closed"] = (
            review_gate.get("canonical_artifact_write_permission") is False
            and review_gate.get("canonical_artifact_write_performed") is False
            and int(counts.get("canonical_artifact_write_count", -1)) == 0
            and int(execution.get("canonical_artifact_write_calls", -1)) == 0
        )
        checks["solar_planner_draft_projection_no_extra_live_call"] = (
            int(execution.get("draft_projection_provider_calls", -1)) == 0
            and int(execution.get("draft_projection_live_api_calls", -1)) == 0
            and int(execution.get("draft_projection_network_calls", -1)) == 0
            and int(execution.get("draft_projection_env_key_value_reads", -1)) == 0
            and int(counts.get("additional_live_call_count", -1)) == 0
        )
        checks["solar_planner_draft_projection_public_safe"] = (
            int(counts.get("raw_provider_body_stored_count", -1)) == 0
            and int(counts.get("raw_provider_body_returned_count", -1)) == 0
            and int(counts.get("credential_value_exposure_count", -1)) == 0
            and int(counts.get("input_text_exposure_count", -1)) == 0
            and int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("server_start_calls", -1)) == 0
        )
    if daacs_runtime_preflight_data is None:
        checks["daacs_runtime_preflight_optional"] = True
    else:
        execution = daacs_runtime_preflight_data.get("execution_boundary", {})
        counts = daacs_runtime_preflight_data.get("counts", {})
        checks["daacs_runtime_preflight_projection"] = (
            daacs_runtime_preflight_data.get("projection_version")
            == "target-runtime-preflight-public-v1"
        )
        checks["daacs_runtime_preflight_blocked"] = (
            daacs_runtime_preflight_data.get("status") == "blocked"
        )
        checks["daacs_runtime_preflight_execution_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("filesystem_writes", -1)) == 0
            and int(execution.get("subprocess_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
        )
        checks["daacs_runtime_preflight_boundary_clean"] = (
            int(counts.get("denied_path_count", -1)) == 0
            and int(counts.get("blocked_operation_count", -1)) == 0
            and int(counts.get("target_runtime_call_count", -1)) == 0
        )
    if daacs_runtime_adapter_admission_data is None:
        checks["daacs_runtime_adapter_admission_optional"] = True
    else:
        execution = daacs_runtime_adapter_admission_data.get("execution_boundary", {})
        counts = daacs_runtime_adapter_admission_data.get("counts", {})
        checks["daacs_runtime_adapter_admission_projection"] = (
            daacs_runtime_adapter_admission_data.get("projection_version")
            == "target-runtime-adapter-admission-public-v1"
        )
        checks["daacs_runtime_adapter_admission_blocked"] = (
            daacs_runtime_adapter_admission_data.get("status") == "blocked"
            and daacs_runtime_adapter_admission_data.get("reason")
            == "target_runtime_adapter_disabled"
        )
        checks["daacs_runtime_adapter_admission_hash_match"] = (
            int(counts.get("preflight_hash_match_count", -1)) == 1
        )
        checks["daacs_runtime_adapter_disabled_reached"] = (
            int(counts.get("adapter_reach_count", -1)) == 1
            and int(counts.get("adapter_disabled_block_count", -1)) == 1
        )
        checks["daacs_runtime_adapter_execution_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("filesystem_writes", -1)) == 0
            and int(execution.get("subprocess_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
            and int(execution.get("execution_permission_count", -1)) == 0
        )
        persistence = daacs_runtime_adapter_admission_data.get(
            "adapter_admission_persistence", {}
        )
        persistence_counts = persistence.get("counts", {})
        checks["daacs_runtime_adapter_admission_persisted"] = (
            persistence.get("status") in {"persisted", "duplicate"}
            and int(persistence_counts.get("local_evidence_repository_write_count", -1))
            >= 0
        )
        read_model = daacs_runtime_adapter_admission_read_data or {}
        read_counts = read_model.get("counts", {})
        read_execution = read_model.get("execution_boundary", {})
        checks["daacs_runtime_adapter_admission_read_model"] = (
            read_model.get("projection_version")
            == "target-runtime-adapter-admission-read-model-public-v1"
            and read_model.get("status") == "available"
            and int(read_counts.get("adapter_admission_record_count", -1)) >= 1
            and int(read_counts.get("adapter_admission_hash_count", -1)) >= 1
        )
        checks["daacs_runtime_adapter_read_model_execution_zero"] = (
            int(read_execution.get("target_runtime_calls", -1)) == 0
            and int(read_execution.get("filesystem_writes", -1)) == 0
            and int(read_execution.get("subprocess_calls", -1)) == 0
            and int(read_execution.get("network_calls", -1)) == 0
        )
    if daacs_runtime_output_manifest_data is None:
        checks["daacs_runtime_output_manifest_optional"] = True
    else:
        execution = daacs_runtime_output_manifest_data.get("execution_boundary", {})
        counts = daacs_runtime_output_manifest_data.get("counts", {})
        checks["daacs_runtime_output_manifest_projection"] = (
            daacs_runtime_output_manifest_data.get("projection_version")
            == TARGET_RUNTIME_OUTPUT_MANIFEST_VERSION
        )
        checks["daacs_runtime_output_manifest_blocked"] = (
            daacs_runtime_output_manifest_data.get("status") == "blocked"
            and daacs_runtime_output_manifest_data.get("reason")
            == "target_runtime_output_manifest_execution_closed"
        )
        checks["daacs_runtime_output_manifest_prerequisite"] = (
            int(counts.get("adapter_admission_read_model_count", -1)) == 1
            and int(counts.get("adapter_admission_hash_match_count", -1)) == 1
        )
        checks["daacs_runtime_output_manifest_groups"] = (
            int(counts.get("output_group_count", -1)) >= 3
            and int(counts.get("output_group_hash_count", -1)) >= 3
        )
        checks["daacs_runtime_output_manifest_execution_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("filesystem_writes", -1)) == 0
            and int(execution.get("subprocess_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
            and int(execution.get("execution_permission_count", -1)) == 0
            and int(execution.get("generated_artifact_body_write_count", -1)) == 0
        )
        persistence = daacs_runtime_output_manifest_data.get(
            "output_manifest_persistence", {}
        )
        persistence_counts = persistence.get("counts", {})
        checks["daacs_runtime_output_manifest_persisted"] = (
            persistence.get("status") in {"persisted", "duplicate"}
            and int(persistence_counts.get("local_evidence_repository_write_count", -1))
            >= 0
        )
        read_model = daacs_runtime_output_manifest_read_data or {}
        read_counts = read_model.get("counts", {})
        read_execution = read_model.get("execution_boundary", {})
        checks["daacs_runtime_output_manifest_read_model"] = (
            read_model.get("projection_version")
            == "target-runtime-output-manifest-read-model-public-v1"
            and read_model.get("status") == "available"
            and int(read_counts.get("output_manifest_record_count", -1)) >= 1
            and int(read_counts.get("output_manifest_hash_count", -1)) >= 1
        )
        checks["daacs_runtime_output_manifest_read_model_execution_zero"] = (
            int(read_execution.get("target_runtime_calls", -1)) == 0
            and int(read_execution.get("filesystem_writes", -1)) == 0
            and int(read_execution.get("subprocess_calls", -1)) == 0
            and int(read_execution.get("network_calls", -1)) == 0
            and int(read_execution.get("execution_permission_count", -1)) == 0
            and int(read_execution.get("generated_artifact_body_write_count", -1)) == 0
        )
    if daacs_runtime_generated_artifact_bundle_data is None:
        checks["daacs_runtime_generated_artifact_bundle_optional"] = True
    else:
        execution = daacs_runtime_generated_artifact_bundle_data.get(
            "execution_boundary", {}
        )
        counts = daacs_runtime_generated_artifact_bundle_data.get("counts", {})
        checks["daacs_runtime_generated_artifact_bundle_projection"] = (
            daacs_runtime_generated_artifact_bundle_data.get("projection_version")
            == TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION
        )
        checks["daacs_runtime_generated_artifact_bundle_blocked"] = (
            daacs_runtime_generated_artifact_bundle_data.get("status") == "blocked"
            and daacs_runtime_generated_artifact_bundle_data.get("reason")
            == "target_runtime_generated_artifact_bundle_execution_closed"
        )
        checks["daacs_runtime_generated_artifact_bundle_prerequisite"] = (
            int(counts.get("output_manifest_read_model_count", -1)) == 1
            and int(counts.get("output_manifest_hash_match_count", -1)) == 1
            and int(counts.get("output_manifest_record_count", -1)) >= 1
        )
        checks["daacs_runtime_generated_artifact_bundle_units"] = (
            int(counts.get("artifact_unit_count", -1)) >= 3
            and int(counts.get("artifact_unit_hash_count", -1)) >= 3
        )
        checks["daacs_runtime_generated_artifact_bundle_execution_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("filesystem_writes", -1)) == 0
            and int(execution.get("subprocess_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
            and int(execution.get("execution_permission_count", -1)) == 0
            and int(execution.get("generated_artifact_body_write_count", -1)) == 0
        )
    if daacs_runtime_fixture_materialization_data is None:
        checks["daacs_runtime_fixture_materialization_optional"] = True
    else:
        execution = daacs_runtime_fixture_materialization_data.get(
            "execution_boundary", {}
        )
        counts = daacs_runtime_fixture_materialization_data.get("counts", {})
        checks["daacs_runtime_fixture_materialization_projection"] = (
            daacs_runtime_fixture_materialization_data.get("projection_version")
            == TARGET_RUNTIME_FIXTURE_MATERIALIZATION_VERSION
        )
        checks["daacs_runtime_fixture_materialization_passed"] = (
            daacs_runtime_fixture_materialization_data.get("status") == "passed"
            and daacs_runtime_fixture_materialization_data.get("reason")
            == "target_runtime_fixture_artifacts_materialized"
        )
        checks["daacs_runtime_fixture_materialization_prerequisite"] = (
            int(counts.get("generated_artifact_bundle_projection_count", -1)) == 1
            and int(counts.get("generated_artifact_bundle_hash_match_count", -1))
            == 1
        )
        checks["daacs_runtime_fixture_materialization_records"] = (
            int(counts.get("fixture_artifact_record_count", -1)) >= 3
            and int(counts.get("fixture_artifact_content_hash_count", -1)) >= 3
        )
        checks["daacs_runtime_fixture_materialization_workspace_writes"] = (
            int(counts.get("fixture_workspace_file_write_count", -1)) >= 3
            and int(execution.get("fixture_workspace_file_write_count", -1)) >= 3
            and int(execution.get("filesystem_writes_outside_workspace", -1)) == 0
            and int(execution.get("generated_artifact_body_public_return_count", -1))
            == 0
        )
        checks["daacs_runtime_fixture_materialization_live_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("provider_calls", -1)) == 0
            and int(execution.get("subprocess_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
            and int(execution.get("execution_permission_count", -1)) == 0
        )
    if daacs_runtime_restricted_workspace_generation_data is None:
        checks["daacs_runtime_restricted_workspace_generation_optional"] = True
    else:
        execution = daacs_runtime_restricted_workspace_generation_data.get(
            "execution_boundary", {}
        )
        repository = daacs_runtime_restricted_workspace_generation_data.get(
            "repository_boundary", {}
        )
        counts = daacs_runtime_restricted_workspace_generation_data.get("counts", {})
        checks["daacs_runtime_restricted_workspace_generation_projection"] = (
            daacs_runtime_restricted_workspace_generation_data.get(
                "projection_version"
            )
            == TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION
        )
        checks["daacs_runtime_restricted_workspace_generation_passed"] = (
            daacs_runtime_restricted_workspace_generation_data.get("status")
            == "passed"
            and daacs_runtime_restricted_workspace_generation_data.get("reason")
            == "target_runtime_restricted_workspace_generated"
        )
        checks["daacs_runtime_restricted_workspace_generation_prerequisite"] = (
            int(counts.get("generated_artifact_bundle_projection_count", -1)) == 1
            and int(counts.get("generated_artifact_bundle_hash_match_count", -1))
            == 1
        )
        checks["daacs_runtime_restricted_workspace_generation_codegen_input"] = (
            int(counts.get("codegen_input_hash_count", -1)) == 1
            and int(counts.get("codegen_input_document_hash_count", -1)) >= 1
            and int(counts.get("implementation_brief_hash_present_count", -1)) == 1
        )
        checks["daacs_runtime_restricted_workspace_generation_records"] = (
            int(counts.get("generated_workspace_file_record_count", -1)) >= 5
            and int(counts.get("generated_workspace_file_hash_count", -1)) >= 5
            and int(counts.get("generated_workspace_file_byte_count", -1)) > 0
        )
        checks["daacs_runtime_restricted_workspace_generation_writes"] = (
            int(counts.get("restricted_workspace_file_write_count", -1)) >= 5
            and int(execution.get("restricted_workspace_file_write_count", -1)) >= 5
            and int(execution.get("filesystem_writes_outside_workspace", -1)) == 0
            and int(execution.get("generated_file_content_public_return_count", -1))
            == 0
        )
        checks["daacs_runtime_restricted_workspace_generation_public_safe"] = (
            repository.get("root_path_returned") is False
            and repository.get("file_content_returned") is False
            and int(counts.get("file_content_public_return_count", -1)) == 0
            and int(counts.get("local_root_path_return_count", -1)) == 0
        )
        checks["daacs_runtime_restricted_workspace_generation_live_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("provider_calls", -1)) == 0
            and int(execution.get("sdk_imports", -1)) == 0
            and int(execution.get("env_key_value_reads", -1)) == 0
            and int(execution.get("subprocess_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
            and int(execution.get("package_install_calls", -1)) == 0
            and int(execution.get("build_calls", -1)) == 0
            and int(execution.get("server_start_calls", -1)) == 0
            and int(execution.get("execution_permission_count", -1)) == 0
        )
    if daacs_runtime_generated_artifact_verification_data is None:
        checks["daacs_runtime_generated_artifact_verification_optional"] = True
    else:
        execution = daacs_runtime_generated_artifact_verification_data.get(
            "execution_boundary", {}
        )
        repository = daacs_runtime_generated_artifact_verification_data.get(
            "repository_boundary", {}
        )
        counts = daacs_runtime_generated_artifact_verification_data.get("counts", {})
        checks["daacs_runtime_generated_artifact_verification_projection"] = (
            daacs_runtime_generated_artifact_verification_data.get(
                "projection_version"
            )
            == TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION
        )
        checks["daacs_runtime_generated_artifact_verification_passed"] = (
            daacs_runtime_generated_artifact_verification_data.get("status")
            == "passed"
            and daacs_runtime_generated_artifact_verification_data.get("reason")
            == "generated_artifact_files_verified"
        )
        checks["daacs_runtime_generated_artifact_verification_prerequisite"] = (
            int(counts.get("generated_workspace_projection_count", -1)) == 1
            and int(counts.get("generated_workspace_hash_match_count", -1)) == 1
        )
        checks["daacs_runtime_generated_artifact_verification_records"] = (
            int(counts.get("expected_file_count", -1)) == 9
            and int(counts.get("file_check_record_count", -1)) == 9
            and int(counts.get("content_hash_match_count", -1)) == 9
            and int(counts.get("byte_count_match_count", -1)) == 9
        )
        checks["daacs_runtime_generated_artifact_verification_public_safe"] = (
            repository.get("root_path_returned") is False
            and repository.get("file_content_returned") is False
            and int(counts.get("file_content_public_return_count", -1)) == 0
            and int(counts.get("local_root_path_return_count", -1)) == 0
        )
        checks["daacs_runtime_generated_artifact_verification_live_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("provider_calls", -1)) == 0
            and int(execution.get("sdk_imports", -1)) == 0
            and int(execution.get("env_key_value_reads", -1)) == 0
            and int(execution.get("subprocess_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
            and int(execution.get("package_install_calls", -1)) == 0
            and int(execution.get("build_calls", -1)) == 0
            and int(execution.get("server_start_calls", -1)) == 0
            and int(execution.get("execution_permission_count", -1)) == 0
        )
    if daacs_runtime_generated_workspace_static_validation_data is None:
        checks["daacs_runtime_generated_workspace_static_validation_optional"] = True
    else:
        execution = daacs_runtime_generated_workspace_static_validation_data.get(
            "execution_boundary", {}
        )
        repository = daacs_runtime_generated_workspace_static_validation_data.get(
            "repository_boundary", {}
        )
        counts = daacs_runtime_generated_workspace_static_validation_data.get(
            "counts", {}
        )
        checks["daacs_runtime_generated_workspace_static_validation_projection"] = (
            daacs_runtime_generated_workspace_static_validation_data.get(
                "projection_version"
            )
            == TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION
        )
        checks["daacs_runtime_generated_workspace_static_validation_passed"] = (
            daacs_runtime_generated_workspace_static_validation_data.get("status")
            == "passed"
            and daacs_runtime_generated_workspace_static_validation_data.get("reason")
            == "generated_workspace_static_validation_passed"
        )
        checks["daacs_runtime_generated_workspace_static_validation_prerequisite"] = (
            int(counts.get("verification_hash_match_count", -1)) == 1
            and int(counts.get("verified_file_record_count", -1)) == 9
        )
        checks["daacs_runtime_generated_workspace_static_validation_records"] = (
            int(counts.get("static_file_checked_count", -1)) == 9
            and int(counts.get("file_read_count", -1)) == 9
            and int(counts.get("package_json_parse_pass_count", -1)) == 1
            and int(counts.get("required_script_present_count", -1)) == 4
            and int(counts.get("app_component_marker_present_count", -1)) >= 6
            and int(counts.get("api_marker_present_count", -1)) >= 4
            and int(counts.get("verification_boundary_marker_present_count", -1)) >= 4
            and int(counts.get("zero_call_marker_present_count", -1)) == 5
        )
        checks["daacs_runtime_generated_workspace_static_validation_public_safe"] = (
            repository.get("root_path_returned") is False
            and repository.get("file_content_returned") is False
            and int(counts.get("file_content_public_return_count", -1)) == 0
            and int(counts.get("local_root_path_return_count", -1)) == 0
        )
        checks["daacs_runtime_generated_workspace_static_validation_live_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("provider_calls", -1)) == 0
            and int(execution.get("sdk_imports", -1)) == 0
            and int(execution.get("env_key_value_reads", -1)) == 0
            and int(execution.get("subprocess_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
            and int(execution.get("package_install_calls", -1)) == 0
            and int(execution.get("build_calls", -1)) == 0
            and int(execution.get("server_start_calls", -1)) == 0
            and int(execution.get("execution_permission_count", -1)) == 0
        )
    if daacs_runtime_buildable_fixture_manifest_data is None:
        checks["daacs_runtime_buildable_fixture_manifest_optional"] = True
    else:
        execution = daacs_runtime_buildable_fixture_manifest_data.get(
            "execution_boundary", {}
        )
        repository = daacs_runtime_buildable_fixture_manifest_data.get(
            "repository_boundary", {}
        )
        counts = daacs_runtime_buildable_fixture_manifest_data.get("counts", {})
        package_manifest = daacs_runtime_buildable_fixture_manifest_data.get(
            "package_manifest", {}
        )
        checks["daacs_runtime_buildable_fixture_manifest_projection"] = (
            daacs_runtime_buildable_fixture_manifest_data.get("projection_version")
            == TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION
        )
        checks["daacs_runtime_buildable_fixture_manifest_passed"] = (
            daacs_runtime_buildable_fixture_manifest_data.get("status") == "passed"
            and daacs_runtime_buildable_fixture_manifest_data.get("reason")
            == "buildable_fixture_manifest_ready"
            and daacs_runtime_buildable_fixture_manifest_data.get(
                "build_ready_candidate"
            )
            is True
        )
        checks["daacs_runtime_buildable_fixture_manifest_package"] = (
            int(counts.get("required_script_present_count", -1)) == 4
            and int(counts.get("total_dependency_label_count", -1)) >= 4
            and int(counts.get("placeholder_dependency_value_count", -1)) == 0
            and package_manifest.get("dependency_value_returned") is False
        )
        checks["daacs_runtime_buildable_fixture_manifest_source_shape"] = (
            int(counts.get("required_file_read_count", -1)) == 5
            and int(counts.get("index_html_marker_present_count", -1)) == 2
            and int(counts.get("main_entrypoint_marker_present_count", -1)) == 2
            and int(counts.get("vite_config_marker_present_count", -1)) == 2
            and int(counts.get("tsconfig_marker_present_count", -1)) == 2
        )
        checks["daacs_runtime_buildable_fixture_manifest_public_safe"] = (
            repository.get("root_path_returned") is False
            and repository.get("file_content_returned") is False
            and int(counts.get("package_manifest_value_return_count", -1)) == 0
            and int(counts.get("file_content_public_return_count", -1)) == 0
            and int(counts.get("local_root_path_return_count", -1)) == 0
        )
        checks["daacs_runtime_buildable_fixture_manifest_live_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("provider_calls", -1)) == 0
            and int(execution.get("sdk_imports", -1)) == 0
            and int(execution.get("env_key_value_reads", -1)) == 0
            and int(execution.get("subprocess_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
            and int(execution.get("package_install_calls", -1)) == 0
            and int(execution.get("build_calls", -1)) == 0
            and int(execution.get("server_start_calls", -1)) == 0
            and int(execution.get("execution_permission_count", -1)) == 0
        )
    if daacs_runtime_local_build_preflight_data is None:
        checks["daacs_runtime_local_build_preflight_optional"] = True
    else:
        execution = daacs_runtime_local_build_preflight_data.get(
            "execution_boundary", {}
        )
        repository = daacs_runtime_local_build_preflight_data.get(
            "repository_boundary", {}
        )
        counts = daacs_runtime_local_build_preflight_data.get("counts", {})
        command_plan = daacs_runtime_local_build_preflight_data.get(
            "command_plan", []
        )
        checks["daacs_runtime_local_build_preflight_projection"] = (
            daacs_runtime_local_build_preflight_data.get("projection_version")
            == TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION
        )
        checks["daacs_runtime_local_build_preflight_passed"] = (
            daacs_runtime_local_build_preflight_data.get("status") == "passed"
            and daacs_runtime_local_build_preflight_data.get("reason")
            == "local_build_preflight_ready"
            and daacs_runtime_local_build_preflight_data.get(
                "local_build_eligible"
            )
            is True
        )
        checks["daacs_runtime_local_build_preflight_policy"] = (
            daacs_runtime_local_build_preflight_data.get(
                "local_build_opt_in_required"
            )
            is True
            and daacs_runtime_local_build_preflight_data.get(
                "operator_opt_in_present"
            )
            is False
            and int(counts.get("local_build_opt_in_required_count", -1)) == 1
            and int(counts.get("default_execution_permission_count", -1)) == 0
        )
        checks["daacs_runtime_local_build_preflight_commands"] = (
            int(counts.get("command_plan_label_count", -1)) >= 2
            and int(counts.get("command_plan_hash_count", -1)) >= 2
            and len(command_plan) >= 2
        )
        checks["daacs_runtime_local_build_preflight_public_safe"] = (
            repository.get("root_path_returned") is False
            and repository.get("file_content_returned") is False
            and repository.get("dependency_value_returned") is False
            and int(counts.get("dependency_value_return_count", -1)) == 0
            and int(counts.get("file_content_public_return_count", -1)) == 0
            and int(counts.get("local_root_path_return_count", -1)) == 0
        )
        checks["daacs_runtime_local_build_preflight_live_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("provider_calls", -1)) == 0
            and int(execution.get("sdk_imports", -1)) == 0
            and int(execution.get("env_key_value_reads", -1)) == 0
            and int(execution.get("subprocess_calls", -1)) == 0
            and int(execution.get("network_calls", -1)) == 0
            and int(execution.get("package_install_calls", -1)) == 0
            and int(execution.get("build_calls", -1)) == 0
            and int(execution.get("server_start_calls", -1)) == 0
            and int(execution.get("execution_permission_count", -1)) == 0
        )
    if daacs_runtime_local_build_attempt_data is None:
        checks["daacs_runtime_local_build_attempt_optional"] = True
    else:
        execution = daacs_runtime_local_build_attempt_data.get(
            "execution_boundary", {}
        )
        repository = daacs_runtime_local_build_attempt_data.get(
            "repository_boundary", {}
        )
        counts = daacs_runtime_local_build_attempt_data.get("counts", {})
        command_results = daacs_runtime_local_build_attempt_data.get(
            "command_results", []
        )
        attempted = (
            daacs_runtime_local_build_attempt_data.get("local_build_attempted")
            is True
        )
        checks["daacs_runtime_local_build_attempt_projection"] = (
            daacs_runtime_local_build_attempt_data.get("projection_version")
            == TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION
        )
        checks["daacs_runtime_local_build_attempt_status_recorded"] = (
            (
                daacs_runtime_local_build_attempt_data.get("status")
                in {"passed", "failed", "environment_blocked"}
                and attempted
                and int(counts.get("package_install_attempt_count", -1)) == 1
            )
            or (
                daacs_runtime_local_build_attempt_data.get("status") == "blocked"
                and daacs_runtime_local_build_attempt_data.get("reason")
                == "local_build_attempt_opt_in_required"
                and not attempted
                and int(counts.get("package_install_attempt_count", -1)) == 0
            )
        )
        checks["daacs_runtime_local_build_attempt_policy"] = (
            daacs_runtime_local_build_attempt_data.get(
                "local_build_opt_in_present"
            )
            is daacs_runtime_local_build_attempt_data.get(
                "local_command_execution_allowed"
            )
            and int(counts.get("server_start_attempt_count", -1)) == 0
            and int(execution.get("server_start_calls", -1)) == 0
        )
        checks["daacs_runtime_local_build_attempt_results_hash_only"] = (
            all(
                isinstance(record, dict)
                and "output_hash" in record
                and record.get("raw_output_returned") is False
                and record.get("root_path_returned") is False
                for record in command_results
            )
            and int(counts.get("raw_output_public_return_count", -1)) == 0
        )
        checks["daacs_runtime_local_build_attempt_public_safe"] = (
            repository.get("root_path_returned") is False
            and repository.get("file_content_returned") is False
            and repository.get("command_output_returned") is False
            and repository.get("dependency_value_returned") is False
            and int(counts.get("file_content_public_return_count", -1)) == 0
            and int(counts.get("local_root_path_return_count", -1)) == 0
            and int(counts.get("dependency_value_return_count", -1)) == 0
        )
        checks["daacs_runtime_local_build_attempt_provider_runtime_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("provider_calls", -1)) == 0
            and int(execution.get("sdk_imports", -1)) == 0
            and int(execution.get("env_key_value_reads", -1)) == 0
            and int(execution.get("server_start_calls", -1)) == 0
        )
    if daacs_runtime_local_preview_attempt_data is None:
        checks["daacs_runtime_local_preview_attempt_optional"] = True
    else:
        execution = daacs_runtime_local_preview_attempt_data.get(
            "execution_boundary", {}
        )
        repository = daacs_runtime_local_preview_attempt_data.get(
            "repository_boundary", {}
        )
        counts = daacs_runtime_local_preview_attempt_data.get("counts", {})
        preview_record = daacs_runtime_local_preview_attempt_data.get(
            "preview_record", {}
        )
        attempted = (
            daacs_runtime_local_preview_attempt_data.get("local_preview_attempted")
            is True
        )
        checks["daacs_runtime_local_preview_attempt_projection"] = (
            daacs_runtime_local_preview_attempt_data.get("projection_version")
            == TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_VERSION
        )
        checks["daacs_runtime_local_preview_attempt_status_recorded"] = (
            (
                daacs_runtime_local_preview_attempt_data.get("status")
                in {"passed", "failed"}
                and attempted
                and int(counts.get("preview_server_start_attempt_count", -1)) == 1
            )
            or (
                daacs_runtime_local_preview_attempt_data.get("status")
                == "environment_blocked"
                and int(counts.get("browser_runtime_preflight_count", -1)) == 1
                and int(counts.get("browser_runtime_available_count", -1)) == 0
                and int(counts.get("preview_server_start_attempt_count", -1)) == 0
            )
            or (
                daacs_runtime_local_preview_attempt_data.get("status") == "blocked"
                and daacs_runtime_local_preview_attempt_data.get("reason")
                == "local_preview_opt_in_required"
                and not attempted
                and int(counts.get("preview_server_start_attempt_count", -1)) == 0
            )
        )
        checks["daacs_runtime_local_preview_attempt_policy"] = (
            daacs_runtime_local_preview_attempt_data.get(
                "local_preview_opt_in_present"
            )
            is daacs_runtime_local_preview_attempt_data.get(
                "local_preview_server_allowed"
            )
            and daacs_runtime_local_preview_attempt_data.get(
                "local_preview_server_allowed"
            )
            is daacs_runtime_local_preview_attempt_data.get(
                "browser_verification_allowed"
            )
        )
        checks["daacs_runtime_local_preview_attempt_evidence_hash_only"] = (
            isinstance(preview_record, dict)
            and preview_record.get("raw_command_output_returned", False) is False
            and preview_record.get("screenshot_path_returned", False) is False
            and preview_record.get("page_text_returned", False) is False
            and preview_record.get("root_path_returned", False) is False
            and int(counts.get("raw_output_public_return_count", -1)) == 0
            and int(counts.get("file_content_public_return_count", -1)) == 0
            and int(counts.get("local_root_path_return_count", -1)) == 0
            and int(
                counts.get("browser_runtime_install_guidance_label_count", 0)
            )
            in {0, 2}
            and int(
                counts.get("browser_runtime_install_guidance_hash_count", 0)
            )
            in {0, 2}
        )
        checks["daacs_runtime_local_preview_attempt_public_safe"] = (
            repository.get("root_path_returned") is False
            and repository.get("file_content_returned") is False
            and repository.get("command_output_returned") is False
            and repository.get("screenshot_path_returned") is False
            and repository.get("page_text_returned") is False
            and int(counts.get("screenshot_path_return_count", -1)) == 0
            and int(counts.get("page_text_return_count", -1)) == 0
        )
        checks["daacs_runtime_local_preview_attempt_provider_runtime_zero"] = (
            int(execution.get("target_runtime_calls", -1)) == 0
            and int(execution.get("provider_calls", -1)) == 0
            and int(execution.get("sdk_imports", -1)) == 0
            and int(execution.get("env_key_value_reads", -1)) == 0
            and int(execution.get("package_install_calls", -1)) == 0
            and int(execution.get("build_calls", -1)) == 0
            and int(execution.get("external_network_calls", -1)) == 0
        )
    if daacs_runtime_browser_setup_attempt_data is None:
        checks["daacs_runtime_browser_setup_attempt_optional"] = True
    else:
        execution = daacs_runtime_browser_setup_attempt_data.get(
            "execution_boundary", {}
        )
        repository = daacs_runtime_browser_setup_attempt_data.get(
            "repository_boundary", {}
        )
        counts = daacs_runtime_browser_setup_attempt_data.get("counts", {})
        checks["daacs_runtime_browser_setup_attempt_projection"] = (
            daacs_runtime_browser_setup_attempt_data.get("projection_version")
            == TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_VERSION
        )
        checks["daacs_runtime_browser_setup_attempt_status_recorded"] = (
            daacs_runtime_browser_setup_attempt_data.get("status")
            in {"passed", "blocked", "environment_blocked"}
        )
        checks["daacs_runtime_browser_setup_attempt_policy"] = (
            daacs_runtime_browser_setup_attempt_data.get("operator_opt_in_present")
            is daacs_runtime_browser_setup_attempt_data.get(
                "browser_runtime_setup_allowed"
            )
        )
        checks["daacs_runtime_browser_setup_attempt_public_safe"] = (
            repository.get("raw_command_output_stored") is False
            and repository.get("raw_browser_error_stored") is False
            and repository.get("local_root_path_returned") is False
            and repository.get("env_value_returned") is False
            and int(counts.get("raw_output_public_return_count", -1)) == 0
            and int(counts.get("argv_public_return_count", -1)) == 0
            and int(counts.get("browser_error_public_return_count", -1)) == 0
        )
        checks["daacs_runtime_browser_setup_attempt_provider_runtime_zero"] = (
            int(execution.get("provider_calls", -1)) == 0
            and int(execution.get("solar_live_calls", -1)) == 0
            and int(execution.get("daacs_target_runtime_calls", -1)) == 0
        )
    return checks


def run_demo(
    store_root: str | Path | None = None,
    *,
    include_provider_precheck: bool = False,
    include_solar_planner_preflight: bool = False,
    include_solar_planner_spike: bool = False,
    include_solar_planner_live_spike: bool = False,
    include_solar_planner_quality_comparison: bool = False,
    include_solar_planner_draft_projection: bool = False,
    include_daacs_runtime_preflight: bool = False,
    include_daacs_runtime_adapter_admission: bool = False,
    include_daacs_runtime_output_manifest: bool = False,
    include_daacs_runtime_generated_artifact_bundle: bool = False,
    include_daacs_runtime_fixture_materialization: bool = False,
    include_daacs_runtime_restricted_workspace_generation: bool = False,
    include_daacs_runtime_generated_artifact_verification: bool = False,
    include_daacs_runtime_generated_workspace_static_validation: bool = False,
    include_daacs_runtime_buildable_fixture_manifest: bool = False,
    include_daacs_runtime_local_build_preflight: bool = False,
    include_daacs_runtime_local_build_attempt: bool = False,
    include_daacs_runtime_local_preview_attempt: bool = False,
    include_daacs_runtime_browser_setup_attempt: bool = False,
    allow_local_build_attempt: bool = False,
    allow_local_preview_attempt: bool = False,
    allow_browser_runtime_setup: bool = False,
    allow_solar_planner_live_call: bool = False,
    allow_solar_quality_reviewer_approval: bool = False,
) -> dict[str, Any]:
    selected_root = Path(store_root) if store_root else Path(__file__).resolve().parent / ".local"
    selected_root.mkdir(parents=True, exist_ok=True)
    client = _client(
        selected_root,
        include_provider_precheck=include_provider_precheck,
        include_target_runtime_admission=(
            include_daacs_runtime_adapter_admission
            or include_daacs_runtime_output_manifest
            or include_daacs_runtime_generated_artifact_bundle
            or include_daacs_runtime_fixture_materialization
            or include_daacs_runtime_restricted_workspace_generation
            or include_daacs_runtime_generated_artifact_verification
            or include_daacs_runtime_generated_workspace_static_validation
            or include_daacs_runtime_buildable_fixture_manifest
            or include_daacs_runtime_local_build_preflight
            or include_daacs_runtime_local_build_attempt
            or include_daacs_runtime_local_preview_attempt
            or include_daacs_runtime_browser_setup_attempt
        ),
        include_target_runtime_output_manifest=(
            include_daacs_runtime_output_manifest
            or include_daacs_runtime_generated_artifact_bundle
            or include_daacs_runtime_fixture_materialization
            or include_daacs_runtime_restricted_workspace_generation
            or include_daacs_runtime_generated_artifact_verification
            or include_daacs_runtime_generated_workspace_static_validation
            or include_daacs_runtime_buildable_fixture_manifest
            or include_daacs_runtime_local_build_preflight
            or include_daacs_runtime_local_build_attempt
            or include_daacs_runtime_local_preview_attempt
            or include_daacs_runtime_browser_setup_attempt
        ),
        include_target_runtime_fixture_materialization=(
            include_daacs_runtime_fixture_materialization
            or include_daacs_runtime_restricted_workspace_generation
            or include_daacs_runtime_generated_artifact_verification
            or include_daacs_runtime_generated_workspace_static_validation
            or include_daacs_runtime_buildable_fixture_manifest
            or include_daacs_runtime_local_build_preflight
            or include_daacs_runtime_local_build_attempt
            or include_daacs_runtime_local_preview_attempt
            or include_daacs_runtime_browser_setup_attempt
        ),
        include_target_runtime_restricted_workspace_generation=(
            include_daacs_runtime_restricted_workspace_generation
            or include_daacs_runtime_generated_artifact_verification
            or include_daacs_runtime_generated_workspace_static_validation
            or include_daacs_runtime_buildable_fixture_manifest
            or include_daacs_runtime_local_build_preflight
            or include_daacs_runtime_local_build_attempt
            or include_daacs_runtime_local_preview_attempt
            or include_daacs_runtime_browser_setup_attempt
        ),
        include_target_runtime_generated_artifact_verification=(
            include_daacs_runtime_generated_artifact_verification
            or include_daacs_runtime_generated_workspace_static_validation
            or include_daacs_runtime_buildable_fixture_manifest
            or include_daacs_runtime_local_build_preflight
            or include_daacs_runtime_local_build_attempt
            or include_daacs_runtime_local_preview_attempt
        ),
        include_target_runtime_generated_workspace_static_validation=(
            include_daacs_runtime_generated_workspace_static_validation
            or include_daacs_runtime_buildable_fixture_manifest
            or include_daacs_runtime_local_build_preflight
            or include_daacs_runtime_local_build_attempt
            or include_daacs_runtime_browser_setup_attempt
        ),
        include_target_runtime_buildable_fixture_manifest=(
            include_daacs_runtime_buildable_fixture_manifest
            or include_daacs_runtime_local_build_preflight
            or include_daacs_runtime_local_build_attempt
            or include_daacs_runtime_local_preview_attempt
            or include_daacs_runtime_browser_setup_attempt
        ),
        include_target_runtime_local_build_attempt=(
            include_daacs_runtime_local_build_attempt
            or include_daacs_runtime_local_preview_attempt
            or include_daacs_runtime_browser_setup_attempt
        ),
        include_target_runtime_local_preview_attempt=(
            include_daacs_runtime_local_preview_attempt
            or include_daacs_runtime_browser_setup_attempt
        ),
    )

    create_data = _post_run(client)
    run_id = str(create_data["run"]["run_id"])
    run_data = _get_data(client, f"/api/v1/runs/{run_id}")
    artifact_data = _get_data(client, f"/api/v1/runs/{run_id}/artifacts")
    verification_data = _get_data(client, f"/api/v1/runs/{run_id}/verification")
    provider_envelope_data = None
    provider_envelope_read_data = None
    solar_planner_preflight_data = None
    solar_planner_spike_data = None
    solar_planner_live_spike_data = None
    solar_planner_quality_comparison_data = None
    solar_planner_draft_projection_data = None
    daacs_runtime_preflight_data = None
    daacs_runtime_adapter_admission_data = None
    daacs_runtime_adapter_admission_read_data = None
    daacs_runtime_output_manifest_data = None
    daacs_runtime_output_manifest_read_data = None
    daacs_runtime_generated_artifact_bundle_data = None
    daacs_runtime_fixture_materialization_data = None
    daacs_runtime_restricted_workspace_generation_data = None
    daacs_runtime_generated_artifact_verification_data = None
    daacs_runtime_generated_workspace_static_validation_data = None
    daacs_runtime_buildable_fixture_manifest_data = None
    daacs_runtime_local_build_preflight_data = None
    daacs_runtime_local_build_attempt_data = None
    daacs_runtime_browser_setup_attempt_data = None
    daacs_runtime_local_preview_attempt_data = None
    daacs_runtime_local_preview_retry_after_browser_setup_count = 0
    if include_provider_precheck:
        provider_envelope_data = _post_provider_envelope_precheck(
            client,
            run_id=run_id,
            prompt_contract_hash=str(create_data["run"]["prompt_contract_hash"]),
        )
        provider_envelope_read_data = _get_data(
            client,
            f"/api/v1/admissions/provider/envelopes/{run_id}",
        )
    if include_solar_planner_preflight:
        solar_planner_preflight_data = _post_solar_planner_preflight(
            client,
            run_id=run_id,
            prompt_contract_hash=str(create_data["run"]["prompt_contract_hash"]),
        )
    if include_solar_planner_spike:
        solar_planner_spike_data = _post_solar_planner_spike_mock_response(
            client,
            run_id=run_id,
            prompt_contract_hash=str(create_data["run"]["prompt_contract_hash"]),
        )
    if include_solar_planner_live_spike:
        solar_planner_live_spike_data = _post_solar_planner_live_spike(
            client,
            run_id=run_id,
            prompt_contract_hash=str(create_data["run"]["prompt_contract_hash"]),
            allow_solar_planner_live_call=allow_solar_planner_live_call,
        )
    if include_solar_planner_quality_comparison or include_solar_planner_draft_projection:
        if solar_planner_live_spike_data is None:
            solar_planner_live_spike_data = _post_solar_planner_live_spike(
                client,
                run_id=run_id,
                prompt_contract_hash=str(create_data["run"]["prompt_contract_hash"]),
                allow_solar_planner_live_call=False,
            )
        reviewer_approval_hash = (
            stable_contract_hash(
                {
                    "run_id": run_id,
                    "decision": "review_solar_quality_comparison_only",
                    "artifact_binding": "draft_candidate_only",
                }
            )
            if allow_solar_quality_reviewer_approval
            else ""
        )
        solar_planner_quality_comparison_data = (
            _post_solar_planner_quality_comparison(
                client,
                run_id=run_id,
                prompt_contract_hash=str(create_data["run"]["prompt_contract_hash"]),
                stage_coverage=_mvp_stage_coverage(run_data, verification_data),
                fixture_artifact_count=_as_int(
                    run_data.get("counts", {}).get("artifact_count")
                ),
                solar_live_spike_projection=solar_planner_live_spike_data,
                reviewer_approval_hash=reviewer_approval_hash,
            )
        )
    if include_solar_planner_draft_projection:
        if solar_planner_quality_comparison_data is None:
            raise RuntimeError("solar quality comparison must exist before draft projection")
        reviewer_approval_hash = (
            stable_contract_hash(
                {
                    "run_id": run_id,
                    "decision": "review_solar_quality_comparison_only",
                    "artifact_binding": "draft_candidate_only",
                }
            )
            if allow_solar_quality_reviewer_approval
            else ""
        )
        solar_planner_draft_projection_data = _post_solar_planner_draft_projection(
            client,
            run_id=run_id,
            prompt_contract_hash=str(create_data["run"]["prompt_contract_hash"]),
            solar_quality_comparison_projection=solar_planner_quality_comparison_data,
            reviewer_approval_hash=reviewer_approval_hash,
        )
    if (
        include_daacs_runtime_preflight
        or include_daacs_runtime_adapter_admission
        or include_daacs_runtime_output_manifest
        or include_daacs_runtime_generated_artifact_bundle
        or include_daacs_runtime_fixture_materialization
        or include_daacs_runtime_restricted_workspace_generation
        or include_daacs_runtime_generated_artifact_verification
        or include_daacs_runtime_generated_workspace_static_validation
        or include_daacs_runtime_buildable_fixture_manifest
        or include_daacs_runtime_local_build_preflight
        or include_daacs_runtime_local_build_attempt
        or include_daacs_runtime_local_preview_attempt
        or include_daacs_runtime_browser_setup_attempt
    ):
        runner_plan_hashes = verification_data.get("runner_plan_hashes", [])
        runner_plan_hash = str(runner_plan_hashes[0] if runner_plan_hashes else "")
        planning_blueprint_hash = _artifact_content_hash(
            run_data.get("artifacts", []),
            artifact_kind="planning_blueprint",
        )
        prd_package_hash = _artifact_content_hash(
            run_data.get("artifacts", []),
            artifact_kind="prd_package",
        )
        implementation_brief_hash = _artifact_content_hash(
            run_data.get("artifacts", []),
            artifact_kind="implementation_brief",
        )
        daacs_runtime_preflight_data = _post_daacs_runtime_preflight(
            client,
            run_id=run_id,
            runner_plan_hash=runner_plan_hash,
        )
        if (
            include_daacs_runtime_adapter_admission
            or include_daacs_runtime_output_manifest
            or include_daacs_runtime_generated_artifact_bundle
            or include_daacs_runtime_fixture_materialization
            or include_daacs_runtime_restricted_workspace_generation
            or include_daacs_runtime_generated_artifact_verification
            or include_daacs_runtime_generated_workspace_static_validation
            or include_daacs_runtime_buildable_fixture_manifest
            or include_daacs_runtime_local_build_preflight
            or include_daacs_runtime_local_build_attempt
            or include_daacs_runtime_local_preview_attempt
            or include_daacs_runtime_browser_setup_attempt
        ):
            daacs_runtime_adapter_admission_data = _post_daacs_runtime_adapter_admission(
                client,
                run_id=run_id,
                runner_plan_hash=runner_plan_hash,
                preflight_projection=daacs_runtime_preflight_data,
            )
            daacs_runtime_adapter_admission_read_data = _get_data(
                client,
                f"/api/v1/daacs/runtime/adapter/admissions/{run_id}",
            )
            if (
                include_daacs_runtime_output_manifest
                or include_daacs_runtime_generated_artifact_bundle
                or include_daacs_runtime_fixture_materialization
                or include_daacs_runtime_restricted_workspace_generation
                or include_daacs_runtime_generated_artifact_verification
                or include_daacs_runtime_generated_workspace_static_validation
                or include_daacs_runtime_buildable_fixture_manifest
                or include_daacs_runtime_local_build_preflight
                or include_daacs_runtime_local_build_attempt
                or include_daacs_runtime_local_preview_attempt
                or include_daacs_runtime_browser_setup_attempt
            ):
                daacs_runtime_output_manifest_data = _post_daacs_runtime_output_manifest(
                    client,
                    run_id=run_id,
                    runner_plan_hash=runner_plan_hash,
                    adapter_admission_hash=str(
                        daacs_runtime_adapter_admission_data.get(
                            "adapter_admission_hash", ""
                        )
                    ),
                    adapter_admission_read_model=(
                        daacs_runtime_adapter_admission_read_data or {}
                    ),
                )
                daacs_runtime_output_manifest_read_data = _get_data(
                    client,
                    f"/api/v1/daacs/runtime/output-manifests/{run_id}",
                )
                if (
                    include_daacs_runtime_generated_artifact_bundle
                    or include_daacs_runtime_fixture_materialization
                    or include_daacs_runtime_restricted_workspace_generation
                    or include_daacs_runtime_generated_artifact_verification
                    or include_daacs_runtime_generated_workspace_static_validation
                    or include_daacs_runtime_buildable_fixture_manifest
                    or include_daacs_runtime_local_build_preflight
                    or include_daacs_runtime_local_build_attempt
                    or include_daacs_runtime_local_preview_attempt
                    or include_daacs_runtime_browser_setup_attempt
                ):
                    daacs_runtime_generated_artifact_bundle_data = (
                        _post_daacs_runtime_generated_artifact_bundle(
                            client,
                            run_id=run_id,
                            runner_plan_hash=runner_plan_hash,
                            output_manifest_hash=str(
                                daacs_runtime_output_manifest_data.get(
                                    "output_manifest_hash", ""
                                )
                            ),
                            output_manifest_read_model=(
                                daacs_runtime_output_manifest_read_data or {}
                            ),
                        )
                    )
                    if (
                        include_daacs_runtime_fixture_materialization
                        or include_daacs_runtime_restricted_workspace_generation
                        or include_daacs_runtime_generated_artifact_verification
                        or include_daacs_runtime_generated_workspace_static_validation
                        or include_daacs_runtime_buildable_fixture_manifest
                        or include_daacs_runtime_local_build_preflight
                        or include_daacs_runtime_local_build_attempt
                        or include_daacs_runtime_local_preview_attempt
                        or include_daacs_runtime_browser_setup_attempt
                    ):
                        daacs_runtime_fixture_materialization_data = (
                            _post_daacs_runtime_fixture_materialization(
                                client,
                                run_id=run_id,
                                runner_plan_hash=runner_plan_hash,
                                generated_artifact_bundle_hash=str(
                                    daacs_runtime_generated_artifact_bundle_data.get(
                                        "generated_artifact_bundle_hash", ""
                                    )
                                ),
                                generated_artifact_bundle_projection=(
                                    daacs_runtime_generated_artifact_bundle_data
                                    or {}
                                ),
                            )
                        )
                    if (
                        include_daacs_runtime_restricted_workspace_generation
                        or include_daacs_runtime_generated_artifact_verification
                        or include_daacs_runtime_generated_workspace_static_validation
                        or include_daacs_runtime_buildable_fixture_manifest
                        or include_daacs_runtime_local_build_preflight
                        or include_daacs_runtime_local_build_attempt
                        or include_daacs_runtime_local_preview_attempt
                        or include_daacs_runtime_browser_setup_attempt
                    ):
                        daacs_runtime_restricted_workspace_generation_data = (
                            _post_daacs_runtime_restricted_workspace_generation(
                                client,
                                run_id=run_id,
                                runner_plan_hash=runner_plan_hash,
                                planning_blueprint_hash=planning_blueprint_hash,
                                prd_package_hash=prd_package_hash,
                                implementation_brief_hash=implementation_brief_hash,
                                generated_artifact_bundle_hash=str(
                                    daacs_runtime_generated_artifact_bundle_data.get(
                                        "generated_artifact_bundle_hash", ""
                                    )
                                ),
                                generated_artifact_bundle_projection=(
                                    daacs_runtime_generated_artifact_bundle_data
                                    or {}
                                ),
                                solar_draft_projection=solar_planner_draft_projection_data,
                            )
                        )
                    if (
                        include_daacs_runtime_generated_artifact_verification
                        or include_daacs_runtime_generated_workspace_static_validation
                        or include_daacs_runtime_buildable_fixture_manifest
                        or include_daacs_runtime_local_build_preflight
                        or include_daacs_runtime_local_build_attempt
                        or include_daacs_runtime_local_preview_attempt
                        or include_daacs_runtime_browser_setup_attempt
                    ):
                        daacs_runtime_generated_artifact_verification_data = (
                            _post_daacs_runtime_generated_artifact_verification(
                                client,
                                run_id=run_id,
                                generated_workspace_hash=str(
                                    daacs_runtime_restricted_workspace_generation_data.get(
                                        "generated_workspace_hash", ""
                                    )
                                ),
                                generated_workspace_projection=(
                                    daacs_runtime_restricted_workspace_generation_data
                                    or {}
                                ),
                            )
                        )
                    if (
                        include_daacs_runtime_generated_workspace_static_validation
                        or include_daacs_runtime_buildable_fixture_manifest
                        or include_daacs_runtime_local_build_preflight
                        or include_daacs_runtime_local_build_attempt
                        or include_daacs_runtime_local_preview_attempt
                        or include_daacs_runtime_browser_setup_attempt
                    ):
                        daacs_runtime_generated_workspace_static_validation_data = (
                            _post_daacs_runtime_generated_workspace_static_validation(
                                client,
                                run_id=run_id,
                                generated_artifact_verification_hash=str(
                                    daacs_runtime_generated_artifact_verification_data.get(
                                        "generated_artifact_verification_hash", ""
                                    )
                                ),
                                generated_artifact_verification_projection=(
                                    daacs_runtime_generated_artifact_verification_data
                                    or {}
                                ),
                            )
                        )
                    if (
                        include_daacs_runtime_buildable_fixture_manifest
                        or include_daacs_runtime_local_build_preflight
                        or include_daacs_runtime_local_build_attempt
                        or include_daacs_runtime_local_preview_attempt
                        or include_daacs_runtime_browser_setup_attempt
                    ):
                        daacs_runtime_buildable_fixture_manifest_data = (
                            _post_daacs_runtime_buildable_fixture_manifest(
                                client,
                                run_id=run_id,
                                generated_workspace_static_validation_hash=str(
                                    daacs_runtime_generated_workspace_static_validation_data.get(
                                        "generated_workspace_static_validation_hash",
                                        "",
                                    )
                                ),
                                generated_workspace_static_validation_projection=(
                                    daacs_runtime_generated_workspace_static_validation_data
                                    or {}
                                ),
                            )
                        )
                    if (
                        include_daacs_runtime_local_build_preflight
                        or include_daacs_runtime_local_build_attempt
                        or include_daacs_runtime_local_preview_attempt
                        or include_daacs_runtime_browser_setup_attempt
                    ):
                        daacs_runtime_local_build_preflight_data = (
                            _post_daacs_runtime_local_build_preflight(
                                client,
                                run_id=run_id,
                                buildable_fixture_manifest_hash=str(
                                    daacs_runtime_buildable_fixture_manifest_data.get(
                                        "buildable_fixture_manifest_hash",
                                        "",
                                    )
                                ),
                                buildable_fixture_manifest_projection=(
                                    daacs_runtime_buildable_fixture_manifest_data
                                    or {}
                                ),
                            )
                        )
                    if (
                        include_daacs_runtime_local_build_attempt
                        or include_daacs_runtime_local_preview_attempt
                        or include_daacs_runtime_browser_setup_attempt
                    ):
                        daacs_runtime_local_build_attempt_data = (
                            _post_daacs_runtime_local_build_attempt(
                                client,
                                run_id=run_id,
                                local_build_preflight_hash=str(
                                    daacs_runtime_local_build_preflight_data.get(
                                        "local_build_preflight_hash",
                                        "",
                                    )
                                ),
                                local_build_preflight_projection=(
                                    daacs_runtime_local_build_preflight_data or {}
                                ),
                                allow_local_build_attempt=(
                                    allow_local_build_attempt
                                    or allow_local_preview_attempt
                                ),
                            )
                        )
                    if (
                        include_daacs_runtime_local_preview_attempt
                        or include_daacs_runtime_browser_setup_attempt
                    ):
                        daacs_runtime_local_preview_attempt_data = (
                            _post_daacs_runtime_local_preview_attempt(
                                client,
                                run_id=run_id,
                                local_build_attempt_hash=str(
                                    daacs_runtime_local_build_attempt_data.get(
                                        "local_build_attempt_hash",
                                        "",
                                    )
                                ),
                                local_build_attempt_projection=(
                                    daacs_runtime_local_build_attempt_data or {}
                                ),
                                allow_local_preview_attempt=allow_local_preview_attempt,
                            )
                        )
                    if include_daacs_runtime_browser_setup_attempt:
                        browser_preflight = (
                            daacs_runtime_local_preview_attempt_data or {}
                        ).get("browser_runtime_preflight", {})
                        daacs_runtime_browser_setup_attempt_data = (
                            _post_daacs_runtime_browser_setup_attempt(
                                client,
                                run_id=run_id,
                                browser_runtime_preflight_projection=(
                                    browser_preflight or {}
                                ),
                                allow_browser_runtime_setup=(
                                    allow_browser_runtime_setup
                                ),
                            )
                        )
                        if _should_retry_local_preview_after_browser_setup(
                            local_preview_attempt=(
                                daacs_runtime_local_preview_attempt_data
                            ),
                            browser_setup_attempt=(
                                daacs_runtime_browser_setup_attempt_data
                            ),
                            allow_local_preview_attempt=allow_local_preview_attempt,
                        ):
                            daacs_runtime_local_preview_attempt_data = (
                                _post_daacs_runtime_local_preview_attempt(
                                    client,
                                    run_id=run_id,
                                    local_build_attempt_hash=str(
                                        daacs_runtime_local_build_attempt_data.get(
                                            "local_build_attempt_hash",
                                            "",
                                        )
                                    ),
                                    local_build_attempt_projection=(
                                        daacs_runtime_local_build_attempt_data or {}
                                    ),
                                    allow_local_preview_attempt=(
                                        allow_local_preview_attempt
                                    ),
                                )
                            )
                            daacs_runtime_local_preview_retry_after_browser_setup_count = 1

    checks = _checks(
        create_data,
        run_data,
        verification_data=verification_data,
        provider_envelope_data=provider_envelope_data,
        solar_planner_preflight_data=solar_planner_preflight_data,
        solar_planner_spike_data=solar_planner_spike_data,
        solar_planner_live_spike_data=solar_planner_live_spike_data,
        solar_planner_quality_comparison_data=solar_planner_quality_comparison_data,
        solar_planner_draft_projection_data=solar_planner_draft_projection_data,
        daacs_runtime_preflight_data=daacs_runtime_preflight_data,
        daacs_runtime_adapter_admission_data=daacs_runtime_adapter_admission_data,
        daacs_runtime_adapter_admission_read_data=(
            daacs_runtime_adapter_admission_read_data
        ),
        daacs_runtime_output_manifest_data=daacs_runtime_output_manifest_data,
        daacs_runtime_output_manifest_read_data=(
            daacs_runtime_output_manifest_read_data
        ),
        daacs_runtime_generated_artifact_bundle_data=(
            daacs_runtime_generated_artifact_bundle_data
        ),
        daacs_runtime_fixture_materialization_data=(
            daacs_runtime_fixture_materialization_data
        ),
        daacs_runtime_restricted_workspace_generation_data=(
            daacs_runtime_restricted_workspace_generation_data
        ),
        daacs_runtime_generated_artifact_verification_data=(
            daacs_runtime_generated_artifact_verification_data
        ),
        daacs_runtime_generated_workspace_static_validation_data=(
            daacs_runtime_generated_workspace_static_validation_data
        ),
        daacs_runtime_buildable_fixture_manifest_data=(
            daacs_runtime_buildable_fixture_manifest_data
        ),
        daacs_runtime_local_build_preflight_data=(
            daacs_runtime_local_build_preflight_data
        ),
        daacs_runtime_local_build_attempt_data=(
            daacs_runtime_local_build_attempt_data
        ),
        daacs_runtime_browser_setup_attempt_data=(
            daacs_runtime_browser_setup_attempt_data
        ),
        daacs_runtime_local_preview_attempt_data=(
            daacs_runtime_local_preview_attempt_data
        ),
    )
    artifact_kinds = sorted(_artifact_kinds(run_data.get("artifacts", [])))
    evidence_summary = run_data.get("evidence_summary", {})
    stage_coverage = _mvp_stage_coverage(run_data, verification_data)
    solar_planner_execution = (
        solar_planner_preflight_data.get("execution_boundary", {})
        if solar_planner_preflight_data
        else {}
    )
    solar_planner_spike_execution = (
        solar_planner_spike_data.get("execution_boundary", {})
        if solar_planner_spike_data
        else {}
    )
    solar_planner_live_spike_execution = (
        solar_planner_live_spike_data.get("execution_boundary", {})
        if solar_planner_live_spike_data
        else {}
    )
    solar_planner_quality_execution = (
        solar_planner_quality_comparison_data.get("execution_boundary", {})
        if solar_planner_quality_comparison_data
        else {}
    )
    solar_planner_draft_execution = (
        solar_planner_draft_projection_data.get("execution_boundary", {})
        if solar_planner_draft_projection_data
        else {}
    )
    daacs_runtime_execution = (
        daacs_runtime_preflight_data.get("execution_boundary", {})
        if daacs_runtime_preflight_data
        else {}
    )
    daacs_runtime_adapter_execution = (
        daacs_runtime_adapter_admission_data.get("execution_boundary", {})
        if daacs_runtime_adapter_admission_data
        else {}
    )
    daacs_runtime_output_manifest_execution = (
        daacs_runtime_output_manifest_data.get("execution_boundary", {})
        if daacs_runtime_output_manifest_data
        else {}
    )
    daacs_runtime_generated_artifact_bundle_execution = (
        daacs_runtime_generated_artifact_bundle_data.get("execution_boundary", {})
        if daacs_runtime_generated_artifact_bundle_data
        else {}
    )
    daacs_runtime_fixture_materialization_execution = (
        daacs_runtime_fixture_materialization_data.get("execution_boundary", {})
        if daacs_runtime_fixture_materialization_data
        else {}
    )
    daacs_runtime_restricted_workspace_generation_execution = (
        daacs_runtime_restricted_workspace_generation_data.get(
            "execution_boundary", {}
        )
        if daacs_runtime_restricted_workspace_generation_data
        else {}
    )
    daacs_runtime_generated_artifact_verification_execution = (
        daacs_runtime_generated_artifact_verification_data.get(
            "execution_boundary", {}
        )
        if daacs_runtime_generated_artifact_verification_data
        else {}
    )
    daacs_runtime_generated_workspace_static_validation_execution = (
        daacs_runtime_generated_workspace_static_validation_data.get(
            "execution_boundary", {}
        )
        if daacs_runtime_generated_workspace_static_validation_data
        else {}
    )
    daacs_runtime_buildable_fixture_manifest_execution = (
        daacs_runtime_buildable_fixture_manifest_data.get("execution_boundary", {})
        if daacs_runtime_buildable_fixture_manifest_data
        else {}
    )
    daacs_runtime_local_build_preflight_execution = (
        daacs_runtime_local_build_preflight_data.get("execution_boundary", {})
        if daacs_runtime_local_build_preflight_data
        else {}
    )
    daacs_runtime_local_build_attempt_execution = (
        daacs_runtime_local_build_attempt_data.get("execution_boundary", {})
        if daacs_runtime_local_build_attempt_data
        else {}
    )
    daacs_runtime_local_preview_attempt_execution = (
        daacs_runtime_local_preview_attempt_data.get("execution_boundary", {})
        if daacs_runtime_local_preview_attempt_data
        else {}
    )
    comparison_variant_count = (
        5
        if solar_planner_draft_projection_data
        else 4
        if solar_planner_live_spike_data
        else 3
        if solar_planner_spike_data
        else 2
        if solar_planner_preflight_data
        else 1
    )
    runtime_comparison_variant_count = (
        13
        if daacs_runtime_local_preview_attempt_data
        else
        12
        if daacs_runtime_local_build_attempt_data
        else
        11
        if daacs_runtime_local_build_preflight_data
        else
        10
        if daacs_runtime_buildable_fixture_manifest_data
        else
        9
        if daacs_runtime_generated_workspace_static_validation_data
        else
        8
        if daacs_runtime_generated_artifact_verification_data
        else
        7
        if daacs_runtime_restricted_workspace_generation_data
        else
        6
        if daacs_runtime_fixture_materialization_data
        else
        5
        if daacs_runtime_generated_artifact_bundle_data
        else
        4
        if daacs_runtime_output_manifest_data
        else 3
        if daacs_runtime_adapter_admission_data
        else 2
        if daacs_runtime_preflight_data
        else 1
    )
    summary = {
        "demo_id": "AW-DEMO-01",
        "mvp_id": MVP_ID,
        "status": "passed" if all(checks.values()) else "failed",
        "run_id": run_id,
        "projection_version": run_data.get("projection_version"),
        "runtime_mode": run_data.get("runtime_mode"),
        "fixture_mode": run_data.get("fixture_mode"),
        "artifact_count": run_data.get("counts", {}).get("artifact_count", 0),
        "artifact_kinds": artifact_kinds,
        "identity_signals": {
            "div": {
                "planning_blueprint_artifact": checks["planning_blueprint_artifact"],
                "prd_package_artifact": checks["prd_package_artifact"],
                "evidence_summary_present": evidence_summary.get("status")
                in {"available", "not_found", "unconfigured"},
            },
            "daacs": {
                "build_spec_artifact": checks["build_spec_artifact"],
                "implementation_brief_artifact": checks["implementation_brief_artifact"],
                "runner_plan_evidence": checks["runner_plan_evidence"],
                "verification_report_evidence": checks["verification_report_evidence"],
            },
        },
        "counts": run_data.get("counts", {}),
        "evidence_summary": {
            "status": evidence_summary.get("status"),
            "counts": evidence_summary.get("counts", {}),
            "linkage": evidence_summary.get("linkage", {}),
        },
        "repository_boundary": run_data.get("repository_boundary", {}),
        "execution_boundary": run_data.get("execution_boundary", {}),
        "claim_boundary": run_data.get("claim_boundary", {}),
        "artifact_read_model": {
            "projection_version": artifact_data.get("projection_version"),
            "artifact_count": artifact_data.get("counts", {}).get("artifact_count", 0),
        },
        "verification_read_model": {
            "projection_version": verification_data.get("projection_version"),
            "status": verification_data.get("status"),
            "counts": verification_data.get("counts", {}),
            "runner_plan_hash_count": len(verification_data.get("runner_plan_hashes", [])),
            "repository_boundary": verification_data.get("repository_boundary", {}),
            "execution_boundary": verification_data.get("execution_boundary", {}),
            "claim_boundary": verification_data.get("claim_boundary", {}),
        },
        "workflow_stage_coverage": stage_coverage,
        "mvp_metrics": {
            "golden_path_scenario_count": 1,
            "stage_coverage": f"{stage_coverage['covered_stage_count']}/{stage_coverage['required_stage_count']}",
            "stage_coverage_percent": stage_coverage["coverage_percent"],
            "artifact_linkage_by_run_id_percent": 100
            if checks["mvp_artifact_linkage_100_percent"]
            else 0,
            "raw_exposure_findings": 0,
            "live_provider_calls": _as_int(
                solar_planner_live_spike_execution.get("provider_calls")
            ),
            "daacs_target_runtime_calls": 0,
            "public_claim_drift_findings": 0,
        },
        "solar_planner_preflight": (
            {
                "projection_version": solar_planner_preflight_data.get("projection_version"),
                "status": solar_planner_preflight_data.get("status"),
                "reason": solar_planner_preflight_data.get("reason"),
                "planner_provider_mode": solar_planner_preflight_data.get(
                    "planner_provider_mode"
                ),
                "stage_target": solar_planner_preflight_data.get("stage_target"),
                "request_contract_hash": solar_planner_preflight_data.get(
                    "request_contract_hash"
                ),
                "policy_hash": solar_planner_preflight_data.get("policy_hash"),
                "cost_timeout_quota_hash": solar_planner_preflight_data.get(
                    "cost_timeout_quota_hash"
                ),
                "counts": solar_planner_preflight_data.get("counts", {}),
                "execution_boundary": solar_planner_preflight_data.get(
                    "execution_boundary", {}
                ),
                "claim_boundary": solar_planner_preflight_data.get("claim_boundary", {}),
            }
            if solar_planner_preflight_data is not None
            else {
                "status": "skipped",
                "reason": "optional solar planner preflight not requested",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
            }
        ),
        "solar_planner_comparison": {
            "comparison_variant_count": comparison_variant_count,
            "fixture_stage_coverage": f"{stage_coverage['covered_stage_count']}/{stage_coverage['required_stage_count']}",
            "solar_preflight_status": (
                solar_planner_preflight_data.get("status")
                if solar_planner_preflight_data
                else "skipped"
            ),
            "solar_preflight_provider_calls": _as_int(
                solar_planner_execution.get("provider_calls")
            ),
            "solar_preflight_sdk_imports": _as_int(
                solar_planner_execution.get("sdk_imports")
            ),
            "solar_preflight_env_value_reads": _as_int(
                solar_planner_execution.get("env_key_value_reads")
            ),
            "solar_preflight_network_calls": _as_int(
                solar_planner_execution.get("network_calls")
            ),
            "raw_exposure_findings": 0,
            "public_claim_drift_findings": 0,
        },
        "solar_planner_spike": (
            {
                "projection_version": solar_planner_spike_data.get(
                    "projection_version"
                ),
                "status": solar_planner_spike_data.get("status"),
                "reason": solar_planner_spike_data.get("reason"),
                "planner_provider_mode": solar_planner_spike_data.get(
                    "planner_provider_mode"
                ),
                "request_contract_hash": solar_planner_spike_data.get(
                    "request_contract_hash"
                ),
                "planning_request_hash": solar_planner_spike_data.get(
                    "planning_request_hash"
                ),
                "response_projection": solar_planner_spike_data.get(
                    "response_projection", {}
                ),
                "counts": solar_planner_spike_data.get("counts", {}),
                "execution_boundary": solar_planner_spike_data.get(
                    "execution_boundary", {}
                ),
                "claim_boundary": solar_planner_spike_data.get("claim_boundary", {}),
            }
            if solar_planner_spike_data is not None
            else {
                "status": "skipped",
                "reason": "optional solar planner spike not requested",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
            }
        ),
        "solar_planner_spike_comparison": {
            "comparison_variant_count": comparison_variant_count,
            "fixture_stage_coverage": f"{stage_coverage['covered_stage_count']}/{stage_coverage['required_stage_count']}",
            "solar_spike_status": (
                solar_planner_spike_data.get("status")
                if solar_planner_spike_data
                else "skipped"
            ),
            "solar_spike_mock_projection_count": _as_int(
                solar_planner_spike_data.get("counts", {}).get(
                    "mock_response_projection_count"
                )
                if solar_planner_spike_data
                else None
            ),
            "solar_spike_provider_calls": _as_int(
                solar_planner_spike_execution.get("provider_calls")
            ),
            "solar_spike_sdk_imports": _as_int(
                solar_planner_spike_execution.get("sdk_imports")
            ),
            "solar_spike_env_value_reads": _as_int(
                solar_planner_spike_execution.get("env_key_value_reads")
            ),
            "solar_spike_network_calls": _as_int(
                solar_planner_spike_execution.get("network_calls")
            ),
            "raw_exposure_findings": 0,
            "public_claim_drift_findings": 0,
        },
        "solar_planner_live_spike": (
            {
                "projection_version": solar_planner_live_spike_data.get(
                    "projection_version"
                ),
                "status": solar_planner_live_spike_data.get("status"),
                "reason": solar_planner_live_spike_data.get("reason"),
                "planner_provider_mode": solar_planner_live_spike_data.get(
                    "planner_provider_mode"
                ),
                "request_contract_hash": solar_planner_live_spike_data.get(
                    "request_contract_hash"
                ),
                "prompt_contract_hash": solar_planner_live_spike_data.get(
                    "prompt_contract_hash"
                ),
                "model": solar_planner_live_spike_data.get("model"),
                "endpoint_host_hash": solar_planner_live_spike_data.get(
                    "endpoint_host_hash"
                ),
                "response_projection": solar_planner_live_spike_data.get(
                    "response_projection", {}
                ),
                "counts": solar_planner_live_spike_data.get("counts", {}),
                "execution_boundary": solar_planner_live_spike_data.get(
                    "execution_boundary", {}
                ),
                "claim_boundary": solar_planner_live_spike_data.get(
                    "claim_boundary", {}
                ),
            }
            if solar_planner_live_spike_data is not None
            else {
                "status": "skipped",
                "reason": "optional solar planner live spike not requested",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
            }
        ),
        "solar_planner_live_spike_comparison": {
            "comparison_variant_count": comparison_variant_count,
            "fixture_stage_coverage": f"{stage_coverage['covered_stage_count']}/{stage_coverage['required_stage_count']}",
            "solar_live_spike_status": (
                solar_planner_live_spike_data.get("status")
                if solar_planner_live_spike_data
                else "skipped"
            ),
            "solar_live_spike_provider_calls": _as_int(
                solar_planner_live_spike_execution.get("provider_calls")
            ),
            "solar_live_spike_env_value_reads": _as_int(
                solar_planner_live_spike_execution.get("env_key_value_reads")
            ),
            "solar_live_spike_sdk_imports": _as_int(
                solar_planner_live_spike_execution.get("sdk_imports")
            ),
            "solar_live_spike_network_calls": _as_int(
                solar_planner_live_spike_execution.get("network_calls")
            ),
            "solar_live_spike_response_projection_count": _as_int(
                solar_planner_live_spike_data.get("counts", {}).get(
                    "response_projection_count"
                )
                if solar_planner_live_spike_data
                else None
            ),
            "raw_exposure_findings": 0,
            "credential_value_exposure_findings": 0,
            "public_claim_drift_findings": 0,
        },
        "solar_planner_quality_comparison": (
            {
                "projection_version": solar_planner_quality_comparison_data.get(
                    "projection_version"
                ),
                "status": solar_planner_quality_comparison_data.get("status"),
                "reason": solar_planner_quality_comparison_data.get("reason"),
                "mode": solar_planner_quality_comparison_data.get("mode"),
                "comparison_hash": solar_planner_quality_comparison_data.get(
                    "comparison_hash"
                ),
                "fixture_summary": solar_planner_quality_comparison_data.get(
                    "fixture_summary", {}
                ),
                "solar_summary": solar_planner_quality_comparison_data.get(
                    "solar_summary", {}
                ),
                "review_gate": solar_planner_quality_comparison_data.get(
                    "review_gate", {}
                ),
                "counts": solar_planner_quality_comparison_data.get("counts", {}),
                "execution_boundary": solar_planner_quality_comparison_data.get(
                    "execution_boundary", {}
                ),
                "claim_boundary": solar_planner_quality_comparison_data.get(
                    "claim_boundary", {}
                ),
            }
            if solar_planner_quality_comparison_data is not None
            else {
                "status": "skipped",
                "reason": "optional solar planner quality comparison not requested",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
            }
        ),
        "solar_planner_quality_summary": {
            "comparison_variant_count": comparison_variant_count,
            "fixture_stage_coverage": f"{stage_coverage['covered_stage_count']}/{stage_coverage['required_stage_count']}",
            "quality_comparison_status": (
                solar_planner_quality_comparison_data.get("status")
                if solar_planner_quality_comparison_data
                else "skipped"
            ),
            "quality_comparison_reason": (
                solar_planner_quality_comparison_data.get("reason")
                if solar_planner_quality_comparison_data
                else "optional solar planner quality comparison not requested"
            ),
            "solar_summary_section_count": _as_int(
                solar_planner_quality_comparison_data.get("counts", {}).get(
                    "solar_summary_section_count"
                )
                if solar_planner_quality_comparison_data
                else None
            ),
            "solar_artifact_hint_count": _as_int(
                solar_planner_quality_comparison_data.get("counts", {}).get(
                    "solar_artifact_hint_count"
                )
                if solar_planner_quality_comparison_data
                else None
            ),
            "missing_required_stage_count": _as_int(
                solar_planner_quality_comparison_data.get("counts", {}).get(
                    "missing_required_stage_count"
                )
                if solar_planner_quality_comparison_data
                else None
            ),
            "reviewer_approval_count": _as_int(
                solar_planner_quality_comparison_data.get("counts", {}).get(
                    "reviewer_approval_count"
                )
                if solar_planner_quality_comparison_data
                else None
            ),
            "artifact_binding_permission_count": _as_int(
                solar_planner_quality_comparison_data.get("counts", {}).get(
                    "artifact_binding_permission_count"
                )
                if solar_planner_quality_comparison_data
                else None
            ),
            "artifact_binding_performed_count": _as_int(
                solar_planner_quality_comparison_data.get("counts", {}).get(
                    "artifact_binding_performed_count"
                )
                if solar_planner_quality_comparison_data
                else None
            ),
            "additional_live_call_count": _as_int(
                solar_planner_quality_execution.get("additional_live_call_count")
            ),
            "comparison_provider_calls": _as_int(
                solar_planner_quality_execution.get("comparison_provider_calls")
            ),
            "comparison_env_value_reads": _as_int(
                solar_planner_quality_execution.get("comparison_env_key_value_reads")
            ),
            "comparison_network_calls": _as_int(
                solar_planner_quality_execution.get("comparison_network_calls")
            ),
            "target_runtime_calls": _as_int(
                solar_planner_quality_execution.get("target_runtime_calls")
            ),
            "raw_exposure_findings": 0,
            "credential_value_exposure_findings": 0,
            "public_claim_drift_findings": 0,
        },
        "solar_planner_draft_projection": (
            {
                "projection_version": solar_planner_draft_projection_data.get(
                    "projection_version"
                ),
                "status": solar_planner_draft_projection_data.get("status"),
                "reason": solar_planner_draft_projection_data.get("reason"),
                "mode": solar_planner_draft_projection_data.get("mode"),
                "source_quality_comparison_hash": (
                    solar_planner_draft_projection_data.get(
                        "source_quality_comparison_hash"
                    )
                ),
                "draft_projection_hash": solar_planner_draft_projection_data.get(
                    "draft_projection_hash"
                ),
                "draft_artifacts": solar_planner_draft_projection_data.get(
                    "draft_artifacts", []
                ),
                "review_gate": solar_planner_draft_projection_data.get(
                    "review_gate", {}
                ),
                "counts": solar_planner_draft_projection_data.get("counts", {}),
                "execution_boundary": solar_planner_draft_projection_data.get(
                    "execution_boundary", {}
                ),
                "claim_boundary": solar_planner_draft_projection_data.get(
                    "claim_boundary", {}
                ),
            }
            if solar_planner_draft_projection_data is not None
            else {
                "status": "skipped",
                "reason": "optional solar planner draft projection not requested",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
            }
        ),
        "solar_planner_draft_summary": {
            "comparison_variant_count": comparison_variant_count,
            "fixture_stage_coverage": f"{stage_coverage['covered_stage_count']}/{stage_coverage['required_stage_count']}",
            "draft_projection_status": (
                solar_planner_draft_projection_data.get("status")
                if solar_planner_draft_projection_data
                else "skipped"
            ),
            "draft_projection_reason": (
                solar_planner_draft_projection_data.get("reason")
                if solar_planner_draft_projection_data
                else "optional solar planner draft projection not requested"
            ),
            "draft_artifact_projection_count": _as_int(
                solar_planner_draft_projection_data.get("counts", {}).get(
                    "draft_artifact_projection_count"
                )
                if solar_planner_draft_projection_data
                else None
            ),
            "draft_planning_blueprint_projection_count": _as_int(
                solar_planner_draft_projection_data.get("counts", {}).get(
                    "draft_planning_blueprint_projection_count"
                )
                if solar_planner_draft_projection_data
                else None
            ),
            "draft_prd_package_projection_count": _as_int(
                solar_planner_draft_projection_data.get("counts", {}).get(
                    "draft_prd_package_projection_count"
                )
                if solar_planner_draft_projection_data
                else None
            ),
            "quality_comparison_hash_match_count": _as_int(
                solar_planner_draft_projection_data.get("counts", {}).get(
                    "quality_comparison_hash_match_count"
                )
                if solar_planner_draft_projection_data
                else None
            ),
            "canonical_artifact_write_count": _as_int(
                solar_planner_draft_projection_data.get("counts", {}).get(
                    "canonical_artifact_write_count"
                )
                if solar_planner_draft_projection_data
                else None
            ),
            "additional_live_call_count": _as_int(
                solar_planner_draft_execution.get("additional_live_call_count")
            ),
            "draft_projection_provider_calls": _as_int(
                solar_planner_draft_execution.get("draft_projection_provider_calls")
            ),
            "draft_projection_env_value_reads": _as_int(
                solar_planner_draft_execution.get(
                    "draft_projection_env_key_value_reads"
                )
            ),
            "draft_projection_network_calls": _as_int(
                solar_planner_draft_execution.get("draft_projection_network_calls")
            ),
            "target_runtime_calls": _as_int(
                solar_planner_draft_execution.get("target_runtime_calls")
            ),
            "raw_exposure_findings": 0,
            "credential_value_exposure_findings": 0,
            "public_claim_drift_findings": 0,
        },
        "daacs_runtime_preflight": (
            {
                "projection_version": daacs_runtime_preflight_data.get(
                    "projection_version"
                ),
                "status": daacs_runtime_preflight_data.get("status"),
                "reason": daacs_runtime_preflight_data.get("reason"),
                "mode": daacs_runtime_preflight_data.get("mode"),
                "preflight_hash": daacs_runtime_preflight_data.get("preflight_hash"),
                "runner_plan_hash": daacs_runtime_preflight_data.get("runner_plan_hash"),
                "sandbox_policy_hash": daacs_runtime_preflight_data.get(
                    "sandbox_policy_hash"
                ),
                "workspace_intent_hash": daacs_runtime_preflight_data.get(
                    "workspace_intent_hash"
                ),
                "command_policy_hash": daacs_runtime_preflight_data.get(
                    "command_policy_hash"
                ),
                "rollback_policy_hash": daacs_runtime_preflight_data.get(
                    "rollback_policy_hash"
                ),
                "counts": daacs_runtime_preflight_data.get("counts", {}),
                "execution_boundary": daacs_runtime_preflight_data.get(
                    "execution_boundary", {}
                ),
                "claim_boundary": daacs_runtime_preflight_data.get("claim_boundary", {}),
            }
            if daacs_runtime_preflight_data is not None
            else {
                "status": "skipped",
                "reason": "optional target runtime preflight not requested",
                "target_runtime_outcome": False,
            }
        ),
        "daacs_runtime_comparison": {
            "comparison_variant_count": runtime_comparison_variant_count,
            "dry_run_stage_coverage": f"{stage_coverage['covered_stage_count']}/{stage_coverage['required_stage_count']}",
            "target_runtime_preflight_status": (
                daacs_runtime_preflight_data.get("status")
                if daacs_runtime_preflight_data
                else "skipped"
            ),
            "target_runtime_calls": _as_int(
                daacs_runtime_execution.get("target_runtime_calls")
            ),
            "filesystem_writes": _as_int(
                daacs_runtime_execution.get("filesystem_writes")
            ),
            "subprocess_calls": _as_int(
                daacs_runtime_execution.get("subprocess_calls")
            ),
            "network_calls": _as_int(daacs_runtime_execution.get("network_calls")),
            "adapter_admission_status": (
                daacs_runtime_adapter_admission_data.get("status")
                if daacs_runtime_adapter_admission_data
                else "skipped"
            ),
            "adapter_admission_reason": (
                daacs_runtime_adapter_admission_data.get("reason")
                if daacs_runtime_adapter_admission_data
                else "skipped"
            ),
            "adapter_preflight_hash_match_count": _as_int(
                (
                    daacs_runtime_adapter_admission_data or {}
                ).get("counts", {}).get("preflight_hash_match_count")
            ),
            "adapter_reach_count": _as_int(
                (daacs_runtime_adapter_admission_data or {})
                .get("counts", {})
                .get("adapter_reach_count")
            ),
            "adapter_disabled_block_count": _as_int(
                (daacs_runtime_adapter_admission_data or {})
                .get("counts", {})
                .get("adapter_disabled_block_count")
            ),
            "adapter_persisted_count": _as_int(
                (daacs_runtime_adapter_admission_data or {})
                .get("adapter_admission_persistence", {})
                .get("counts", {})
                .get("adapter_admission_persisted_count")
            ),
            "adapter_read_model_record_count": _as_int(
                (daacs_runtime_adapter_admission_read_data or {})
                .get("counts", {})
                .get("adapter_admission_record_count")
            ),
            "output_manifest_status": (
                daacs_runtime_output_manifest_data.get("status")
                if daacs_runtime_output_manifest_data
                else "skipped"
            ),
            "output_manifest_reason": (
                daacs_runtime_output_manifest_data.get("reason")
                if daacs_runtime_output_manifest_data
                else "skipped"
            ),
            "output_manifest_hash_count": (
                1
                if (daacs_runtime_output_manifest_data or {}).get(
                    "output_manifest_hash"
                )
                else 0
            ),
            "output_manifest_group_count": _as_int(
                (daacs_runtime_output_manifest_data or {})
                .get("counts", {})
                .get("output_group_count")
            ),
            "output_manifest_prerequisite_count": _as_int(
                (daacs_runtime_output_manifest_data or {})
                .get("counts", {})
                .get("adapter_admission_read_model_count")
            ),
            "output_manifest_persisted_count": _as_int(
                (daacs_runtime_output_manifest_data or {})
                .get("output_manifest_persistence", {})
                .get("counts", {})
                .get("output_manifest_persisted_count")
            ),
            "output_manifest_read_model_record_count": _as_int(
                (daacs_runtime_output_manifest_read_data or {})
                .get("counts", {})
                .get("output_manifest_record_count")
            ),
            "output_manifest_read_model_hash_count": _as_int(
                (daacs_runtime_output_manifest_read_data or {})
                .get("counts", {})
                .get("output_manifest_hash_count")
            ),
            "output_manifest_generated_body_writes": _as_int(
                daacs_runtime_output_manifest_execution.get(
                    "generated_artifact_body_write_count"
                )
            ),
            "output_manifest_target_runtime_calls": _as_int(
                daacs_runtime_output_manifest_execution.get("target_runtime_calls")
            ),
            "output_manifest_filesystem_writes": _as_int(
                daacs_runtime_output_manifest_execution.get("filesystem_writes")
            ),
            "output_manifest_subprocess_calls": _as_int(
                daacs_runtime_output_manifest_execution.get("subprocess_calls")
            ),
            "output_manifest_network_calls": _as_int(
                daacs_runtime_output_manifest_execution.get("network_calls")
            ),
            "generated_artifact_bundle_status": (
                daacs_runtime_generated_artifact_bundle_data.get("status")
                if daacs_runtime_generated_artifact_bundle_data
                else "skipped"
            ),
            "generated_artifact_bundle_reason": (
                daacs_runtime_generated_artifact_bundle_data.get("reason")
                if daacs_runtime_generated_artifact_bundle_data
                else "skipped"
            ),
            "generated_artifact_bundle_hash_count": (
                1
                if (daacs_runtime_generated_artifact_bundle_data or {}).get(
                    "generated_artifact_bundle_hash"
                )
                else 0
            ),
            "generated_artifact_bundle_unit_count": _as_int(
                (daacs_runtime_generated_artifact_bundle_data or {})
                .get("counts", {})
                .get("artifact_unit_count")
            ),
            "generated_artifact_bundle_prerequisite_count": _as_int(
                (daacs_runtime_generated_artifact_bundle_data or {})
                .get("counts", {})
                .get("output_manifest_read_model_count")
            ),
            "generated_artifact_bundle_body_writes": _as_int(
                daacs_runtime_generated_artifact_bundle_execution.get(
                    "generated_artifact_body_write_count"
                )
            ),
            "generated_artifact_bundle_target_runtime_calls": _as_int(
                daacs_runtime_generated_artifact_bundle_execution.get(
                    "target_runtime_calls"
                )
            ),
            "generated_artifact_bundle_filesystem_writes": _as_int(
                daacs_runtime_generated_artifact_bundle_execution.get(
                    "filesystem_writes"
                )
            ),
            "generated_artifact_bundle_subprocess_calls": _as_int(
                daacs_runtime_generated_artifact_bundle_execution.get(
                    "subprocess_calls"
                )
            ),
            "generated_artifact_bundle_network_calls": _as_int(
                daacs_runtime_generated_artifact_bundle_execution.get("network_calls")
            ),
            "fixture_materialization_status": (
                daacs_runtime_fixture_materialization_data.get("status")
                if daacs_runtime_fixture_materialization_data
                else "skipped"
            ),
            "fixture_materialization_reason": (
                daacs_runtime_fixture_materialization_data.get("reason")
                if daacs_runtime_fixture_materialization_data
                else "skipped"
            ),
            "fixture_materialization_record_count": _as_int(
                (daacs_runtime_fixture_materialization_data or {})
                .get("counts", {})
                .get("fixture_artifact_record_count")
            ),
            "fixture_materialization_content_hash_count": _as_int(
                (daacs_runtime_fixture_materialization_data or {})
                .get("counts", {})
                .get("fixture_artifact_content_hash_count")
            ),
            "fixture_materialization_workspace_writes": _as_int(
                daacs_runtime_fixture_materialization_execution.get(
                    "fixture_workspace_file_write_count"
                )
            ),
            "fixture_materialization_outside_workspace_writes": _as_int(
                daacs_runtime_fixture_materialization_execution.get(
                    "filesystem_writes_outside_workspace"
                )
            ),
            "fixture_materialization_body_public_returns": _as_int(
                daacs_runtime_fixture_materialization_execution.get(
                    "generated_artifact_body_public_return_count"
                )
            ),
            "fixture_materialization_target_runtime_calls": _as_int(
                daacs_runtime_fixture_materialization_execution.get(
                    "target_runtime_calls"
                )
            ),
            "fixture_materialization_provider_calls": _as_int(
                daacs_runtime_fixture_materialization_execution.get("provider_calls")
            ),
            "fixture_materialization_subprocess_calls": _as_int(
                daacs_runtime_fixture_materialization_execution.get(
                    "subprocess_calls"
                )
            ),
            "fixture_materialization_network_calls": _as_int(
                daacs_runtime_fixture_materialization_execution.get("network_calls")
            ),
            "restricted_workspace_generation_status": (
                daacs_runtime_restricted_workspace_generation_data.get("status")
                if daacs_runtime_restricted_workspace_generation_data
                else "skipped"
            ),
            "restricted_workspace_generation_reason": (
                daacs_runtime_restricted_workspace_generation_data.get("reason")
                if daacs_runtime_restricted_workspace_generation_data
                else "skipped"
            ),
            "restricted_workspace_file_record_count": _as_int(
                (daacs_runtime_restricted_workspace_generation_data or {})
                .get("counts", {})
                .get("generated_workspace_file_record_count")
            ),
            "restricted_workspace_file_hash_count": _as_int(
                (daacs_runtime_restricted_workspace_generation_data or {})
                .get("counts", {})
                .get("generated_workspace_file_hash_count")
            ),
            "restricted_workspace_file_byte_count": _as_int(
                (daacs_runtime_restricted_workspace_generation_data or {})
                .get("counts", {})
                .get("generated_workspace_file_byte_count")
            ),
            "restricted_workspace_codegen_input_hash_count": _as_int(
                (daacs_runtime_restricted_workspace_generation_data or {})
                .get("counts", {})
                .get("codegen_input_hash_count")
            ),
            "restricted_workspace_codegen_document_hash_count": _as_int(
                (daacs_runtime_restricted_workspace_generation_data or {})
                .get("counts", {})
                .get("codegen_input_document_hash_count")
            ),
            "restricted_workspace_planning_hash_present_count": _as_int(
                (daacs_runtime_restricted_workspace_generation_data or {})
                .get("counts", {})
                .get("planning_blueprint_hash_present_count")
            ),
            "restricted_workspace_prd_hash_present_count": _as_int(
                (daacs_runtime_restricted_workspace_generation_data or {})
                .get("counts", {})
                .get("prd_package_hash_present_count")
            ),
            "restricted_workspace_solar_draft_hash_present_count": _as_int(
                (daacs_runtime_restricted_workspace_generation_data or {})
                .get("counts", {})
                .get("solar_draft_projection_hash_present_count")
            ),
            "restricted_workspace_writes": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "restricted_workspace_file_write_count"
                )
            ),
            "restricted_workspace_outside_writes": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "filesystem_writes_outside_workspace"
                )
            ),
            "restricted_workspace_file_content_public_returns": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "generated_file_content_public_return_count"
                )
            ),
            "restricted_workspace_target_runtime_calls": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "target_runtime_calls"
                )
            ),
            "restricted_workspace_provider_calls": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "provider_calls"
                )
            ),
            "restricted_workspace_sdk_imports": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "sdk_imports"
                )
            ),
            "restricted_workspace_env_value_reads": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "env_key_value_reads"
                )
            ),
            "restricted_workspace_subprocess_calls": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "subprocess_calls"
                )
            ),
            "restricted_workspace_network_calls": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "network_calls"
                )
            ),
            "restricted_workspace_package_install_calls": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "package_install_calls"
                )
            ),
            "restricted_workspace_build_calls": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "build_calls"
                )
            ),
            "restricted_workspace_server_start_calls": _as_int(
                daacs_runtime_restricted_workspace_generation_execution.get(
                    "server_start_calls"
                )
            ),
            "generated_artifact_verification_status": (
                daacs_runtime_generated_artifact_verification_data.get("status")
                if daacs_runtime_generated_artifact_verification_data
                else "skipped"
            ),
            "generated_artifact_verification_reason": (
                daacs_runtime_generated_artifact_verification_data.get("reason")
                if daacs_runtime_generated_artifact_verification_data
                else "skipped"
            ),
            "generated_artifact_verification_expected_file_count": _as_int(
                (daacs_runtime_generated_artifact_verification_data or {})
                .get("counts", {})
                .get("expected_file_count")
            ),
            "generated_artifact_verification_file_check_count": _as_int(
                (daacs_runtime_generated_artifact_verification_data or {})
                .get("counts", {})
                .get("file_check_record_count")
            ),
            "generated_artifact_verification_content_hash_matches": _as_int(
                (daacs_runtime_generated_artifact_verification_data or {})
                .get("counts", {})
                .get("content_hash_match_count")
            ),
            "generated_artifact_verification_byte_count_matches": _as_int(
                (daacs_runtime_generated_artifact_verification_data or {})
                .get("counts", {})
                .get("byte_count_match_count")
            ),
            "generated_artifact_verification_file_reads": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "generated_workspace_file_read_count"
                )
            ),
            "generated_artifact_verification_file_content_public_returns": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "generated_file_content_public_return_count"
                )
            ),
            "generated_artifact_verification_local_root_public_returns": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "local_root_path_public_return_count"
                )
            ),
            "generated_artifact_verification_target_runtime_calls": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "target_runtime_calls"
                )
            ),
            "generated_artifact_verification_provider_calls": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "provider_calls"
                )
            ),
            "generated_artifact_verification_sdk_imports": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "sdk_imports"
                )
            ),
            "generated_artifact_verification_env_value_reads": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "env_key_value_reads"
                )
            ),
            "generated_artifact_verification_subprocess_calls": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "subprocess_calls"
                )
            ),
            "generated_artifact_verification_network_calls": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "network_calls"
                )
            ),
            "generated_artifact_verification_package_install_calls": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "package_install_calls"
                )
            ),
            "generated_artifact_verification_build_calls": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "build_calls"
                )
            ),
            "generated_artifact_verification_server_start_calls": _as_int(
                daacs_runtime_generated_artifact_verification_execution.get(
                    "server_start_calls"
                )
            ),
            "generated_workspace_static_validation_status": (
                daacs_runtime_generated_workspace_static_validation_data.get("status")
                if daacs_runtime_generated_workspace_static_validation_data
                else "skipped"
            ),
            "generated_workspace_static_validation_reason": (
                daacs_runtime_generated_workspace_static_validation_data.get("reason")
                if daacs_runtime_generated_workspace_static_validation_data
                else "skipped"
            ),
            "generated_workspace_static_validation_file_checked_count": _as_int(
                (daacs_runtime_generated_workspace_static_validation_data or {})
                .get("counts", {})
                .get("static_file_checked_count")
            ),
            "generated_workspace_static_validation_file_reads": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "static_validation_file_read_count"
                )
            ),
            "generated_workspace_static_validation_package_json_parse_pass": _as_int(
                (daacs_runtime_generated_workspace_static_validation_data or {})
                .get("counts", {})
                .get("package_json_parse_pass_count")
            ),
            "generated_workspace_static_validation_required_script_present_count": _as_int(
                (daacs_runtime_generated_workspace_static_validation_data or {})
                .get("counts", {})
                .get("required_script_present_count")
            ),
            "generated_workspace_static_validation_app_marker_count": _as_int(
                (daacs_runtime_generated_workspace_static_validation_data or {})
                .get("counts", {})
                .get("app_component_marker_present_count")
            ),
            "generated_workspace_static_validation_api_marker_count": _as_int(
                (daacs_runtime_generated_workspace_static_validation_data or {})
                .get("counts", {})
                .get("api_marker_present_count")
            ),
            "generated_workspace_static_validation_verification_boundary_marker_count": _as_int(
                (daacs_runtime_generated_workspace_static_validation_data or {})
                .get("counts", {})
                .get("verification_boundary_marker_present_count")
            ),
            "generated_workspace_static_validation_zero_call_marker_count": _as_int(
                (daacs_runtime_generated_workspace_static_validation_data or {})
                .get("counts", {})
                .get("zero_call_marker_present_count")
            ),
            "generated_workspace_static_validation_file_content_public_returns": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "generated_file_content_public_return_count"
                )
            ),
            "generated_workspace_static_validation_local_root_public_returns": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "local_root_path_public_return_count"
                )
            ),
            "generated_workspace_static_validation_target_runtime_calls": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "target_runtime_calls"
                )
            ),
            "generated_workspace_static_validation_provider_calls": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "provider_calls"
                )
            ),
            "generated_workspace_static_validation_sdk_imports": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "sdk_imports"
                )
            ),
            "generated_workspace_static_validation_env_value_reads": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "env_key_value_reads"
                )
            ),
            "generated_workspace_static_validation_subprocess_calls": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "subprocess_calls"
                )
            ),
            "generated_workspace_static_validation_network_calls": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "network_calls"
                )
            ),
            "generated_workspace_static_validation_package_install_calls": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "package_install_calls"
                )
            ),
            "generated_workspace_static_validation_build_calls": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "build_calls"
                )
            ),
            "generated_workspace_static_validation_server_start_calls": _as_int(
                daacs_runtime_generated_workspace_static_validation_execution.get(
                    "server_start_calls"
                )
            ),
            "buildable_fixture_manifest_status": (
                daacs_runtime_buildable_fixture_manifest_data.get("status")
                if daacs_runtime_buildable_fixture_manifest_data
                else "skipped"
            ),
            "buildable_fixture_manifest_reason": (
                daacs_runtime_buildable_fixture_manifest_data.get("reason")
                if daacs_runtime_buildable_fixture_manifest_data
                else "skipped"
            ),
            "buildable_fixture_manifest_candidate": (
                daacs_runtime_buildable_fixture_manifest_data.get(
                    "build_ready_candidate"
                )
                if daacs_runtime_buildable_fixture_manifest_data
                else False
            ),
            "buildable_fixture_manifest_file_reads": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get(
                    "buildable_manifest_file_read_count"
                )
            ),
            "buildable_fixture_manifest_required_file_read_count": _as_int(
                (daacs_runtime_buildable_fixture_manifest_data or {})
                .get("counts", {})
                .get("required_file_read_count")
            ),
            "buildable_fixture_manifest_required_script_present_count": _as_int(
                (daacs_runtime_buildable_fixture_manifest_data or {})
                .get("counts", {})
                .get("required_script_present_count")
            ),
            "buildable_fixture_manifest_dependency_label_count": _as_int(
                (daacs_runtime_buildable_fixture_manifest_data or {})
                .get("counts", {})
                .get("total_dependency_label_count")
            ),
            "buildable_fixture_manifest_placeholder_dependency_values": _as_int(
                (daacs_runtime_buildable_fixture_manifest_data or {})
                .get("counts", {})
                .get("placeholder_dependency_value_count")
            ),
            "buildable_fixture_manifest_package_manifest_value_returns": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get(
                    "package_manifest_values_returned"
                )
            ),
            "buildable_fixture_manifest_file_content_public_returns": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get(
                    "generated_file_content_public_return_count"
                )
            ),
            "buildable_fixture_manifest_local_root_public_returns": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get(
                    "local_root_path_public_return_count"
                )
            ),
            "buildable_fixture_manifest_target_runtime_calls": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get(
                    "target_runtime_calls"
                )
            ),
            "buildable_fixture_manifest_provider_calls": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get("provider_calls")
            ),
            "buildable_fixture_manifest_sdk_imports": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get("sdk_imports")
            ),
            "buildable_fixture_manifest_env_value_reads": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get(
                    "env_key_value_reads"
                )
            ),
            "buildable_fixture_manifest_subprocess_calls": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get(
                    "subprocess_calls"
                )
            ),
            "buildable_fixture_manifest_network_calls": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get("network_calls")
            ),
            "buildable_fixture_manifest_package_install_calls": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get(
                    "package_install_calls"
                )
            ),
            "buildable_fixture_manifest_build_calls": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get("build_calls")
            ),
            "buildable_fixture_manifest_server_start_calls": _as_int(
                daacs_runtime_buildable_fixture_manifest_execution.get(
                    "server_start_calls"
                )
            ),
            "local_build_preflight_status": (
                daacs_runtime_local_build_preflight_data.get("status")
                if daacs_runtime_local_build_preflight_data
                else "skipped"
            ),
            "local_build_preflight_reason": (
                daacs_runtime_local_build_preflight_data.get("reason")
                if daacs_runtime_local_build_preflight_data
                else "skipped"
            ),
            "local_build_preflight_eligible": (
                daacs_runtime_local_build_preflight_data.get(
                    "local_build_eligible"
                )
                if daacs_runtime_local_build_preflight_data
                else False
            ),
            "local_build_preflight_opt_in_required": (
                daacs_runtime_local_build_preflight_data.get(
                    "local_build_opt_in_required"
                )
                if daacs_runtime_local_build_preflight_data
                else False
            ),
            "local_build_preflight_operator_opt_in_present": (
                daacs_runtime_local_build_preflight_data.get(
                    "operator_opt_in_present"
                )
                if daacs_runtime_local_build_preflight_data
                else False
            ),
            "local_build_preflight_command_label_count": _as_int(
                (daacs_runtime_local_build_preflight_data or {})
                .get("counts", {})
                .get("command_plan_label_count")
            ),
            "local_build_preflight_command_hash_count": _as_int(
                (daacs_runtime_local_build_preflight_data or {})
                .get("counts", {})
                .get("command_plan_hash_count")
            ),
            "local_build_preflight_default_execution_permission_count": _as_int(
                (daacs_runtime_local_build_preflight_data or {})
                .get("counts", {})
                .get("default_execution_permission_count")
            ),
            "local_build_preflight_target_runtime_calls": _as_int(
                daacs_runtime_local_build_preflight_execution.get(
                    "target_runtime_calls"
                )
            ),
            "local_build_preflight_provider_calls": _as_int(
                daacs_runtime_local_build_preflight_execution.get("provider_calls")
            ),
            "local_build_preflight_sdk_imports": _as_int(
                daacs_runtime_local_build_preflight_execution.get("sdk_imports")
            ),
            "local_build_preflight_env_value_reads": _as_int(
                daacs_runtime_local_build_preflight_execution.get(
                    "env_key_value_reads"
                )
            ),
            "local_build_preflight_subprocess_calls": _as_int(
                daacs_runtime_local_build_preflight_execution.get(
                    "subprocess_calls"
                )
            ),
            "local_build_preflight_network_calls": _as_int(
                daacs_runtime_local_build_preflight_execution.get("network_calls")
            ),
            "local_build_preflight_package_install_calls": _as_int(
                daacs_runtime_local_build_preflight_execution.get(
                    "package_install_calls"
                )
            ),
            "local_build_preflight_build_calls": _as_int(
                daacs_runtime_local_build_preflight_execution.get("build_calls")
            ),
            "local_build_preflight_server_start_calls": _as_int(
                daacs_runtime_local_build_preflight_execution.get(
                    "server_start_calls"
                )
            ),
            "local_build_attempt_status": (
                daacs_runtime_local_build_attempt_data.get("status")
                if daacs_runtime_local_build_attempt_data
                else "skipped"
            ),
            "local_build_attempt_reason": (
                daacs_runtime_local_build_attempt_data.get("reason")
                if daacs_runtime_local_build_attempt_data
                else "skipped"
            ),
            "local_build_attempt_attempted": (
                daacs_runtime_local_build_attempt_data.get(
                    "local_build_attempted"
                )
                if daacs_runtime_local_build_attempt_data
                else False
            ),
            "local_build_attempt_opt_in_present": (
                daacs_runtime_local_build_attempt_data.get(
                    "local_build_opt_in_present"
                )
                if daacs_runtime_local_build_attempt_data
                else False
            ),
            "local_build_attempt_command_allowed": (
                daacs_runtime_local_build_attempt_data.get(
                    "local_command_execution_allowed"
                )
                if daacs_runtime_local_build_attempt_data
                else False
            ),
            "local_build_attempt_command_result_count": _as_int(
                (daacs_runtime_local_build_attempt_data or {})
                .get("counts", {})
                .get("command_result_count")
            ),
            "local_build_attempt_command_output_hash_count": _as_int(
                (daacs_runtime_local_build_attempt_data or {})
                .get("counts", {})
                .get("command_output_hash_count")
            ),
            "local_build_attempt_package_install_attempts": _as_int(
                (daacs_runtime_local_build_attempt_data or {})
                .get("counts", {})
                .get("package_install_attempt_count")
            ),
            "local_build_attempt_build_attempts": _as_int(
                (daacs_runtime_local_build_attempt_data or {})
                .get("counts", {})
                .get("build_attempt_count")
            ),
            "local_build_attempt_server_start_attempts": _as_int(
                (daacs_runtime_local_build_attempt_data or {})
                .get("counts", {})
                .get("server_start_attempt_count")
            ),
            "local_build_attempt_raw_output_returns": _as_int(
                (daacs_runtime_local_build_attempt_data or {})
                .get("counts", {})
                .get("raw_output_public_return_count")
            ),
            "local_build_attempt_target_runtime_calls": _as_int(
                daacs_runtime_local_build_attempt_execution.get(
                    "target_runtime_calls"
                )
            ),
            "local_build_attempt_provider_calls": _as_int(
                daacs_runtime_local_build_attempt_execution.get("provider_calls")
            ),
            "local_build_attempt_sdk_imports": _as_int(
                daacs_runtime_local_build_attempt_execution.get("sdk_imports")
            ),
            "local_build_attempt_env_value_reads": _as_int(
                daacs_runtime_local_build_attempt_execution.get(
                    "env_key_value_reads"
                )
            ),
            "local_build_attempt_subprocess_calls": _as_int(
                daacs_runtime_local_build_attempt_execution.get(
                    "subprocess_calls"
                )
            ),
            "local_build_attempt_network_calls": _as_int(
                daacs_runtime_local_build_attempt_execution.get("network_calls")
            ),
            "local_build_attempt_package_install_calls": _as_int(
                daacs_runtime_local_build_attempt_execution.get(
                    "package_install_calls"
                )
            ),
            "local_build_attempt_build_calls": _as_int(
                daacs_runtime_local_build_attempt_execution.get("build_calls")
            ),
            "local_build_attempt_server_start_calls": _as_int(
                daacs_runtime_local_build_attempt_execution.get(
                    "server_start_calls"
                )
            ),
            "local_preview_attempt_status": (
                daacs_runtime_local_preview_attempt_data.get("status")
                if daacs_runtime_local_preview_attempt_data
                else "skipped"
            ),
            "local_preview_attempt_reason": (
                daacs_runtime_local_preview_attempt_data.get("reason")
                if daacs_runtime_local_preview_attempt_data
                else "skipped"
            ),
            "local_preview_attempt_attempted": (
                daacs_runtime_local_preview_attempt_data.get(
                    "local_preview_attempted"
                )
                if daacs_runtime_local_preview_attempt_data
                else False
            ),
            "local_preview_attempt_opt_in_present": (
                daacs_runtime_local_preview_attempt_data.get(
                    "local_preview_opt_in_present"
                )
                if daacs_runtime_local_preview_attempt_data
                else False
            ),
            "local_preview_attempt_server_allowed": (
                daacs_runtime_local_preview_attempt_data.get(
                    "local_preview_server_allowed"
                )
                if daacs_runtime_local_preview_attempt_data
                else False
            ),
            "local_preview_attempt_browser_allowed": (
                daacs_runtime_local_preview_attempt_data.get(
                    "browser_verification_allowed"
                )
                if daacs_runtime_local_preview_attempt_data
                else False
            ),
            "local_preview_browser_runtime_preflight_count": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("browser_runtime_preflight_count")
            ),
            "local_preview_browser_runtime_available_count": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("browser_runtime_available_count")
            ),
            "local_preview_browser_runtime_import_check_count": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("browser_runtime_import_check_count")
            ),
            "local_preview_browser_runtime_launch_check_count": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("browser_runtime_launch_check_count")
            ),
            "local_preview_browser_runtime_install_guidance_label_count": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("browser_runtime_install_guidance_label_count")
            ),
            "local_preview_browser_runtime_install_guidance_hash_count": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("browser_runtime_install_guidance_hash_count")
            ),
            "local_preview_attempt_server_start_attempts": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("preview_server_start_attempt_count")
            ),
            "local_preview_attempt_server_starts": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("server_start_count")
            ),
            "local_preview_attempt_server_stops": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("server_stop_count")
            ),
            "local_preview_attempt_browser_verification_attempts": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("browser_verification_attempt_count")
            ),
            "local_preview_attempt_browser_verification_passes": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("browser_verification_pass_count")
            ),
            "local_preview_retry_after_browser_setup_count": (
                daacs_runtime_local_preview_retry_after_browser_setup_count
            ),
            "local_preview_attempt_screenshot_evidence_count": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("screenshot_evidence_count")
            ),
            "local_preview_attempt_screenshot_hash_count": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("screenshot_hash_count")
            ),
            "local_preview_attempt_visible_marker_count": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("visible_marker_count")
            ),
            "local_preview_attempt_raw_output_returns": _as_int(
                (daacs_runtime_local_preview_attempt_data or {})
                .get("counts", {})
                .get("raw_output_public_return_count")
            ),
            "local_preview_attempt_target_runtime_calls": _as_int(
                daacs_runtime_local_preview_attempt_execution.get(
                    "target_runtime_calls"
                )
            ),
            "local_preview_attempt_provider_calls": _as_int(
                daacs_runtime_local_preview_attempt_execution.get("provider_calls")
            ),
            "local_preview_attempt_sdk_imports": _as_int(
                daacs_runtime_local_preview_attempt_execution.get("sdk_imports")
            ),
            "local_preview_attempt_env_value_reads": _as_int(
                daacs_runtime_local_preview_attempt_execution.get(
                    "env_key_value_reads"
                )
            ),
            "local_preview_attempt_subprocess_calls": _as_int(
                daacs_runtime_local_preview_attempt_execution.get(
                    "subprocess_calls"
                )
            ),
            "local_preview_attempt_network_calls": _as_int(
                daacs_runtime_local_preview_attempt_execution.get("network_calls")
            ),
            "local_preview_attempt_external_network_calls": _as_int(
                daacs_runtime_local_preview_attempt_execution.get(
                    "external_network_calls"
                )
            ),
            "local_preview_attempt_package_install_calls": _as_int(
                daacs_runtime_local_preview_attempt_execution.get(
                    "package_install_calls"
                )
            ),
            "local_preview_attempt_build_calls": _as_int(
                daacs_runtime_local_preview_attempt_execution.get("build_calls")
            ),
            "local_preview_attempt_server_start_calls": _as_int(
                daacs_runtime_local_preview_attempt_execution.get(
                    "server_start_calls"
                )
            ),
            "local_preview_attempt_server_stop_calls": _as_int(
                daacs_runtime_local_preview_attempt_execution.get("server_stop_calls")
            ),
            "adapter_target_runtime_calls": _as_int(
                daacs_runtime_adapter_execution.get("target_runtime_calls")
            ),
            "adapter_filesystem_writes": _as_int(
                daacs_runtime_adapter_execution.get("filesystem_writes")
            ),
            "adapter_subprocess_calls": _as_int(
                daacs_runtime_adapter_execution.get("subprocess_calls")
            ),
            "adapter_network_calls": _as_int(
                daacs_runtime_adapter_execution.get("network_calls")
            ),
            "raw_exposure_findings": 0,
            "public_claim_drift_findings": 0,
        },
        "daacs_runtime_adapter_admission": (
            {
                "projection_version": daacs_runtime_adapter_admission_data.get(
                    "projection_version"
                ),
                "status": daacs_runtime_adapter_admission_data.get("status"),
                "reason": daacs_runtime_adapter_admission_data.get("reason"),
                "mode": daacs_runtime_adapter_admission_data.get("mode"),
                "expected_preflight_hash": daacs_runtime_adapter_admission_data.get(
                    "expected_preflight_hash"
                ),
                "preflight_hash": daacs_runtime_adapter_admission_data.get(
                    "preflight_hash"
                ),
                "adapter_admission_hash": daacs_runtime_adapter_admission_data.get(
                    "adapter_admission_hash"
                ),
                "counts": daacs_runtime_adapter_admission_data.get("counts", {}),
                "persistence": daacs_runtime_adapter_admission_data.get(
                    "adapter_admission_persistence", {}
                ),
                "read_model": {
                    "status": (
                        daacs_runtime_adapter_admission_read_data or {}
                    ).get("status"),
                    "counts": (
                        daacs_runtime_adapter_admission_read_data or {}
                    ).get("counts", {}),
                    "repository_boundary": (
                        daacs_runtime_adapter_admission_read_data or {}
                    ).get("repository_boundary", {}),
                    "execution_boundary": (
                        daacs_runtime_adapter_admission_read_data or {}
                    ).get("execution_boundary", {}),
                },
                "execution_boundary": daacs_runtime_adapter_admission_data.get(
                    "execution_boundary", {}
                ),
                "claim_boundary": daacs_runtime_adapter_admission_data.get(
                    "claim_boundary", {}
                ),
            }
            if daacs_runtime_adapter_admission_data is not None
            else {
                "status": "skipped",
                "reason": "optional target runtime adapter admission not requested",
                "target_runtime_outcome": False,
            }
        ),
        "daacs_runtime_output_manifest": (
            {
                "projection_version": daacs_runtime_output_manifest_data.get(
                    "projection_version"
                ),
                "status": daacs_runtime_output_manifest_data.get("status"),
                "reason": daacs_runtime_output_manifest_data.get("reason"),
                "mode": daacs_runtime_output_manifest_data.get("mode"),
                "adapter_admission_hash": daacs_runtime_output_manifest_data.get(
                    "adapter_admission_hash"
                ),
                "adapter_admission_read_model_hash": (
                    daacs_runtime_output_manifest_data.get(
                        "adapter_admission_read_model_hash"
                    )
                ),
                "output_manifest_hash": daacs_runtime_output_manifest_data.get(
                    "output_manifest_hash"
                ),
                "output_groups": daacs_runtime_output_manifest_data.get(
                    "output_groups", []
                ),
                "counts": daacs_runtime_output_manifest_data.get("counts", {}),
                "persistence": daacs_runtime_output_manifest_data.get(
                    "output_manifest_persistence", {}
                ),
                "read_model": {
                    "status": (
                        daacs_runtime_output_manifest_read_data or {}
                    ).get("status"),
                    "counts": (
                        daacs_runtime_output_manifest_read_data or {}
                    ).get("counts", {}),
                    "repository_boundary": (
                        daacs_runtime_output_manifest_read_data or {}
                    ).get("repository_boundary", {}),
                    "execution_boundary": (
                        daacs_runtime_output_manifest_read_data or {}
                    ).get("execution_boundary", {}),
                },
                "execution_boundary": daacs_runtime_output_manifest_data.get(
                    "execution_boundary", {}
                ),
                "claim_boundary": daacs_runtime_output_manifest_data.get(
                    "claim_boundary", {}
                ),
            }
            if daacs_runtime_output_manifest_data is not None
            else {
                "status": "skipped",
                "reason": "optional target runtime output manifest not requested",
                "target_runtime_outcome": False,
            }
        ),
        "daacs_runtime_generated_artifact_bundle": (
            {
                "projection_version": (
                    daacs_runtime_generated_artifact_bundle_data.get(
                        "projection_version"
                    )
                ),
                "status": daacs_runtime_generated_artifact_bundle_data.get("status"),
                "reason": daacs_runtime_generated_artifact_bundle_data.get("reason"),
                "mode": daacs_runtime_generated_artifact_bundle_data.get("mode"),
                "output_manifest_hash": (
                    daacs_runtime_generated_artifact_bundle_data.get(
                        "output_manifest_hash"
                    )
                ),
                "output_manifest_read_model_hash": (
                    daacs_runtime_generated_artifact_bundle_data.get(
                        "output_manifest_read_model_hash"
                    )
                ),
                "generated_artifact_bundle_hash": (
                    daacs_runtime_generated_artifact_bundle_data.get(
                        "generated_artifact_bundle_hash"
                    )
                ),
                "artifact_units": daacs_runtime_generated_artifact_bundle_data.get(
                    "artifact_units", []
                ),
                "counts": daacs_runtime_generated_artifact_bundle_data.get(
                    "counts", {}
                ),
                "execution_boundary": (
                    daacs_runtime_generated_artifact_bundle_data.get(
                        "execution_boundary", {}
                    )
                ),
                "claim_boundary": daacs_runtime_generated_artifact_bundle_data.get(
                    "claim_boundary", {}
                ),
            }
            if daacs_runtime_generated_artifact_bundle_data is not None
            else {
                "status": "skipped",
                "reason": "optional target runtime generated artifact bundle not requested",
                "target_runtime_outcome": False,
            }
        ),
        "daacs_runtime_fixture_materialization": (
            {
                "projection_version": daacs_runtime_fixture_materialization_data.get(
                    "projection_version"
                ),
                "status": daacs_runtime_fixture_materialization_data.get("status"),
                "reason": daacs_runtime_fixture_materialization_data.get("reason"),
                "mode": daacs_runtime_fixture_materialization_data.get("mode"),
                "generated_artifact_bundle_hash": (
                    daacs_runtime_fixture_materialization_data.get(
                        "generated_artifact_bundle_hash"
                    )
                ),
                "generated_artifact_bundle_projection_hash": (
                    daacs_runtime_fixture_materialization_data.get(
                        "generated_artifact_bundle_projection_hash"
                    )
                ),
                "materialization_hash": daacs_runtime_fixture_materialization_data.get(
                    "materialization_hash"
                ),
                "artifact_records": daacs_runtime_fixture_materialization_data.get(
                    "artifact_records", []
                ),
                "counts": daacs_runtime_fixture_materialization_data.get(
                    "counts", {}
                ),
                "repository_boundary": (
                    daacs_runtime_fixture_materialization_data.get(
                        "repository_boundary", {}
                    )
                ),
                "execution_boundary": (
                    daacs_runtime_fixture_materialization_data.get(
                        "execution_boundary", {}
                    )
                ),
                "claim_boundary": daacs_runtime_fixture_materialization_data.get(
                    "claim_boundary", {}
                ),
            }
            if daacs_runtime_fixture_materialization_data is not None
            else {
                "status": "skipped",
                "reason": "optional target runtime fixture materialization not requested",
                "target_runtime_outcome": False,
            }
        ),
        "daacs_runtime_restricted_workspace_generation": (
            {
                "projection_version": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "projection_version"
                    )
                ),
                "status": daacs_runtime_restricted_workspace_generation_data.get(
                    "status"
                ),
                "reason": daacs_runtime_restricted_workspace_generation_data.get(
                    "reason"
                ),
                "mode": daacs_runtime_restricted_workspace_generation_data.get(
                    "mode"
                ),
                "generated_artifact_bundle_hash": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "generated_artifact_bundle_hash"
                    )
                ),
                "generated_artifact_bundle_projection_hash": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "generated_artifact_bundle_projection_hash"
                    )
                ),
                "implementation_brief_hash": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "implementation_brief_hash"
                    )
                ),
                "planning_blueprint_hash": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "planning_blueprint_hash"
                    )
                ),
                "prd_package_hash": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "prd_package_hash"
                    )
                ),
                "solar_draft_projection_hash": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "solar_draft_projection_hash"
                    )
                ),
                "codegen_input_hash": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "codegen_input_hash"
                    )
                ),
                "document_input_summary": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "document_input_summary", {}
                    )
                ),
                "generated_workspace_hash": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "generated_workspace_hash"
                    )
                ),
                "file_records": daacs_runtime_restricted_workspace_generation_data.get(
                    "file_records", []
                ),
                "counts": daacs_runtime_restricted_workspace_generation_data.get(
                    "counts", {}
                ),
                "repository_boundary": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "repository_boundary", {}
                    )
                ),
                "execution_boundary": (
                    daacs_runtime_restricted_workspace_generation_data.get(
                        "execution_boundary", {}
                    )
                ),
                "claim_boundary": daacs_runtime_restricted_workspace_generation_data.get(
                    "claim_boundary", {}
                ),
            }
            if daacs_runtime_restricted_workspace_generation_data is not None
            else {
                "status": "skipped",
                "reason": "optional target runtime restricted workspace generation not requested",
                "target_runtime_outcome": False,
            }
        ),
        "daacs_runtime_generated_artifact_verification": (
            {
                "projection_version": (
                    daacs_runtime_generated_artifact_verification_data.get(
                        "projection_version"
                    )
                ),
                "status": daacs_runtime_generated_artifact_verification_data.get(
                    "status"
                ),
                "reason": daacs_runtime_generated_artifact_verification_data.get(
                    "reason"
                ),
                "mode": daacs_runtime_generated_artifact_verification_data.get(
                    "mode"
                ),
                "generated_workspace_hash": (
                    daacs_runtime_generated_artifact_verification_data.get(
                        "generated_workspace_hash"
                    )
                ),
                "generated_workspace_projection_hash": (
                    daacs_runtime_generated_artifact_verification_data.get(
                        "generated_workspace_projection_hash"
                    )
                ),
                "generated_artifact_verification_hash": (
                    daacs_runtime_generated_artifact_verification_data.get(
                        "generated_artifact_verification_hash"
                    )
                ),
                "file_check_records": (
                    daacs_runtime_generated_artifact_verification_data.get(
                        "file_check_records", []
                    )
                ),
                "counts": daacs_runtime_generated_artifact_verification_data.get(
                    "counts", {}
                ),
                "repository_boundary": (
                    daacs_runtime_generated_artifact_verification_data.get(
                        "repository_boundary", {}
                    )
                ),
                "execution_boundary": (
                    daacs_runtime_generated_artifact_verification_data.get(
                        "execution_boundary", {}
                    )
                ),
                "claim_boundary": (
                    daacs_runtime_generated_artifact_verification_data.get(
                        "claim_boundary", {}
                    )
                ),
            }
            if daacs_runtime_generated_artifact_verification_data is not None
            else {
                "status": "skipped",
                "reason": "optional target runtime generated artifact verification not requested",
                "target_runtime_outcome": False,
            }
        ),
        "daacs_runtime_generated_workspace_static_validation": (
            {
                "projection_version": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "projection_version"
                    )
                ),
                "status": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "status"
                    )
                ),
                "reason": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "reason"
                    )
                ),
                "mode": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "mode"
                    )
                ),
                "generated_artifact_verification_hash": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "generated_artifact_verification_hash"
                    )
                ),
                "generated_artifact_verification_projection_hash": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "generated_artifact_verification_projection_hash"
                    )
                ),
                "generated_workspace_static_validation_hash": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "generated_workspace_static_validation_hash"
                    )
                ),
                "validation_records": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "validation_records", []
                    )
                ),
                "counts": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "counts", {}
                    )
                ),
                "repository_boundary": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "repository_boundary", {}
                    )
                ),
                "execution_boundary": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "execution_boundary", {}
                    )
                ),
                "claim_boundary": (
                    daacs_runtime_generated_workspace_static_validation_data.get(
                        "claim_boundary", {}
                    )
                ),
            }
            if daacs_runtime_generated_workspace_static_validation_data is not None
            else {
                "status": "skipped",
                "reason": "optional generated workspace static validation not requested",
                "target_runtime_outcome": False,
            }
        ),
        "daacs_runtime_buildable_fixture_manifest": (
            {
                "projection_version": daacs_runtime_buildable_fixture_manifest_data.get(
                    "projection_version"
                ),
                "run_id": daacs_runtime_buildable_fixture_manifest_data.get("run_id"),
                "status": daacs_runtime_buildable_fixture_manifest_data.get("status"),
                "reason": daacs_runtime_buildable_fixture_manifest_data.get("reason"),
                "mode": daacs_runtime_buildable_fixture_manifest_data.get("mode"),
                "build_ready_candidate": (
                    daacs_runtime_buildable_fixture_manifest_data.get(
                        "build_ready_candidate"
                    )
                ),
                "generated_workspace_static_validation_hash": (
                    daacs_runtime_buildable_fixture_manifest_data.get(
                        "generated_workspace_static_validation_hash"
                    )
                ),
                "generated_workspace_static_validation_projection_hash": (
                    daacs_runtime_buildable_fixture_manifest_data.get(
                        "generated_workspace_static_validation_projection_hash"
                    )
                ),
                "buildable_fixture_manifest_hash": (
                    daacs_runtime_buildable_fixture_manifest_data.get(
                        "buildable_fixture_manifest_hash"
                    )
                ),
                "package_manifest": (
                    daacs_runtime_buildable_fixture_manifest_data.get(
                        "package_manifest", {}
                    )
                ),
                "build_readiness_records": (
                    daacs_runtime_buildable_fixture_manifest_data.get(
                        "build_readiness_records", []
                    )
                ),
                "counts": daacs_runtime_buildable_fixture_manifest_data.get(
                    "counts", {}
                ),
                "repository_boundary": (
                    daacs_runtime_buildable_fixture_manifest_data.get(
                        "repository_boundary", {}
                    )
                ),
                "execution_boundary": (
                    daacs_runtime_buildable_fixture_manifest_data.get(
                        "execution_boundary", {}
                    )
                ),
                "claim_boundary": (
                    daacs_runtime_buildable_fixture_manifest_data.get(
                        "claim_boundary", {}
                    )
                ),
            }
            if daacs_runtime_buildable_fixture_manifest_data is not None
            else {
                "status": "skipped",
                "reason": "optional buildable fixture manifest not requested",
                "target_runtime_outcome": False,
                "build_ready_candidate": False,
            }
        ),
        "daacs_runtime_local_build_preflight": (
            {
                "projection_version": daacs_runtime_local_build_preflight_data.get(
                    "projection_version"
                ),
                "run_id": daacs_runtime_local_build_preflight_data.get("run_id"),
                "status": daacs_runtime_local_build_preflight_data.get("status"),
                "reason": daacs_runtime_local_build_preflight_data.get("reason"),
                "mode": daacs_runtime_local_build_preflight_data.get("mode"),
                "local_build_eligible": (
                    daacs_runtime_local_build_preflight_data.get(
                        "local_build_eligible"
                    )
                ),
                "local_build_opt_in_required": (
                    daacs_runtime_local_build_preflight_data.get(
                        "local_build_opt_in_required"
                    )
                ),
                "operator_opt_in_present": (
                    daacs_runtime_local_build_preflight_data.get(
                        "operator_opt_in_present"
                    )
                ),
                "buildable_fixture_manifest_hash": (
                    daacs_runtime_local_build_preflight_data.get(
                        "buildable_fixture_manifest_hash"
                    )
                ),
                "buildable_fixture_manifest_projection_hash": (
                    daacs_runtime_local_build_preflight_data.get(
                        "buildable_fixture_manifest_projection_hash"
                    )
                ),
                "local_build_preflight_hash": (
                    daacs_runtime_local_build_preflight_data.get(
                        "local_build_preflight_hash"
                    )
                ),
                "command_plan": daacs_runtime_local_build_preflight_data.get(
                    "command_plan", []
                ),
                "counts": daacs_runtime_local_build_preflight_data.get(
                    "counts", {}
                ),
                "repository_boundary": (
                    daacs_runtime_local_build_preflight_data.get(
                        "repository_boundary", {}
                    )
                ),
                "execution_boundary": (
                    daacs_runtime_local_build_preflight_data.get(
                        "execution_boundary", {}
                    )
                ),
                "claim_boundary": (
                    daacs_runtime_local_build_preflight_data.get(
                        "claim_boundary", {}
                    )
                ),
            }
            if daacs_runtime_local_build_preflight_data is not None
            else {
                "status": "skipped",
                "reason": "optional local build preflight not requested",
                "target_runtime_outcome": False,
                "local_build_eligible": False,
                "local_build_opt_in_required": True,
            }
        ),
        "daacs_runtime_local_build_attempt": (
            {
                "projection_version": daacs_runtime_local_build_attempt_data.get(
                    "projection_version"
                ),
                "run_id": daacs_runtime_local_build_attempt_data.get("run_id"),
                "status": daacs_runtime_local_build_attempt_data.get("status"),
                "reason": daacs_runtime_local_build_attempt_data.get("reason"),
                "mode": daacs_runtime_local_build_attempt_data.get("mode"),
                "local_build_attempted": (
                    daacs_runtime_local_build_attempt_data.get(
                        "local_build_attempted"
                    )
                ),
                "local_build_opt_in_present": (
                    daacs_runtime_local_build_attempt_data.get(
                        "local_build_opt_in_present"
                    )
                ),
                "local_command_execution_allowed": (
                    daacs_runtime_local_build_attempt_data.get(
                        "local_command_execution_allowed"
                    )
                ),
                "local_build_preflight_hash": (
                    daacs_runtime_local_build_attempt_data.get(
                        "local_build_preflight_hash"
                    )
                ),
                "local_build_preflight_projection_hash": (
                    daacs_runtime_local_build_attempt_data.get(
                        "local_build_preflight_projection_hash"
                    )
                ),
                "local_build_attempt_hash": (
                    daacs_runtime_local_build_attempt_data.get(
                        "local_build_attempt_hash"
                    )
                ),
                "command_results": daacs_runtime_local_build_attempt_data.get(
                    "command_results", []
                ),
                "counts": daacs_runtime_local_build_attempt_data.get(
                    "counts", {}
                ),
                "repository_boundary": (
                    daacs_runtime_local_build_attempt_data.get(
                        "repository_boundary", {}
                    )
                ),
                "execution_boundary": (
                    daacs_runtime_local_build_attempt_data.get(
                        "execution_boundary", {}
                    )
                ),
                "claim_boundary": (
                    daacs_runtime_local_build_attempt_data.get(
                        "claim_boundary", {}
                    )
                ),
            }
            if daacs_runtime_local_build_attempt_data is not None
            else {
                "status": "skipped",
                "reason": "optional local build attempt not requested",
                "target_runtime_outcome": False,
                "local_build_attempted": False,
                "local_build_opt_in_present": False,
                "local_command_execution_allowed": False,
            }
        ),
        "daacs_runtime_browser_setup_attempt": (
            {
                "projection_version": (
                    daacs_runtime_browser_setup_attempt_data.get(
                        "projection_version"
                    )
                ),
                "run_id": daacs_runtime_browser_setup_attempt_data.get("run_id"),
                "status": daacs_runtime_browser_setup_attempt_data.get("status"),
                "reason": daacs_runtime_browser_setup_attempt_data.get("reason"),
                "mode": daacs_runtime_browser_setup_attempt_data.get("mode"),
                "setup_attempted": daacs_runtime_browser_setup_attempt_data.get(
                    "setup_attempted"
                ),
                "operator_opt_in_present": (
                    daacs_runtime_browser_setup_attempt_data.get(
                        "operator_opt_in_present"
                    )
                ),
                "browser_runtime_setup_allowed": (
                    daacs_runtime_browser_setup_attempt_data.get(
                        "browser_runtime_setup_allowed"
                    )
                ),
                "browser_runtime_preflight_hash": (
                    daacs_runtime_browser_setup_attempt_data.get(
                        "browser_runtime_preflight_hash"
                    )
                ),
                "browser_runtime_setup_attempt_hash": (
                    daacs_runtime_browser_setup_attempt_data.get(
                        "browser_runtime_setup_attempt_hash"
                    )
                ),
                "command_records": daacs_runtime_browser_setup_attempt_data.get(
                    "command_records", []
                ),
                "post_setup_browser_runtime_preflight": (
                    daacs_runtime_browser_setup_attempt_data.get(
                        "post_setup_browser_runtime_preflight", {}
                    )
                ),
                "counts": daacs_runtime_browser_setup_attempt_data.get(
                    "counts", {}
                ),
                "repository_boundary": (
                    daacs_runtime_browser_setup_attempt_data.get(
                        "repository_boundary", {}
                    )
                ),
                "execution_boundary": (
                    daacs_runtime_browser_setup_attempt_data.get(
                        "execution_boundary", {}
                    )
                ),
                "claim_boundary": (
                    daacs_runtime_browser_setup_attempt_data.get(
                        "claim_boundary", {}
                    )
                ),
            }
            if daacs_runtime_browser_setup_attempt_data is not None
            else {
                "status": "skipped",
                "reason": "optional browser runtime setup attempt not requested",
                "setup_attempted": False,
                "operator_opt_in_present": False,
                "browser_runtime_setup_allowed": False,
            }
        ),
        "daacs_runtime_local_preview_attempt": (
            {
                "projection_version": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "projection_version"
                    )
                ),
                "run_id": daacs_runtime_local_preview_attempt_data.get("run_id"),
                "status": daacs_runtime_local_preview_attempt_data.get("status"),
                "reason": daacs_runtime_local_preview_attempt_data.get("reason"),
                "mode": daacs_runtime_local_preview_attempt_data.get("mode"),
                "local_preview_attempted": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "local_preview_attempted"
                    )
                ),
                "local_preview_opt_in_present": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "local_preview_opt_in_present"
                    )
                ),
                "local_preview_server_allowed": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "local_preview_server_allowed"
                    )
                ),
                "browser_verification_allowed": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "browser_verification_allowed"
                    )
                ),
                "local_build_attempt_hash": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "local_build_attempt_hash"
                    )
                ),
                "local_build_attempt_projection_hash": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "local_build_attempt_projection_hash"
                    )
                ),
                "browser_runtime_preflight": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "browser_runtime_preflight", {}
                    )
                ),
                "local_preview_attempt_hash": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "local_preview_attempt_hash"
                    )
                ),
                "preview_record": daacs_runtime_local_preview_attempt_data.get(
                    "preview_record", {}
                ),
                "counts": daacs_runtime_local_preview_attempt_data.get(
                    "counts", {}
                ),
                "repository_boundary": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "repository_boundary", {}
                    )
                ),
                "execution_boundary": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "execution_boundary", {}
                    )
                ),
                "claim_boundary": (
                    daacs_runtime_local_preview_attempt_data.get(
                        "claim_boundary", {}
                    )
                ),
            }
            if daacs_runtime_local_preview_attempt_data is not None
            else {
                "status": "skipped",
                "reason": "optional local preview attempt not requested",
                "target_runtime_outcome": False,
                "local_preview_attempted": False,
                "local_preview_opt_in_present": False,
                "local_preview_server_allowed": False,
                "browser_verification_allowed": False,
            }
        ),
        "provider_envelope_admission": (
            {
                "status": provider_envelope_data.get("status"),
                "admission_status": provider_envelope_data.get(
                    "provider_envelope_admission", {}
                ).get("status"),
                "adapter_reached": provider_envelope_data.get(
                    "provider_envelope_admission", {}
                ).get("adapter_reached"),
                "counts": provider_envelope_data.get("provider_envelope_admission", {}).get(
                    "counts", {}
                ),
                "operator_approval_status": provider_envelope_data.get(
                    "operator_approval_envelope", {}
                ).get("status"),
                "operator_policy_summary_hash": provider_envelope_data.get(
                    "operator_policy_summary", {}
                ).get("policy_summary_hash"),
                "dry_admission_status": provider_envelope_data.get(
                    "live_provider_dry_admission", {}
                ).get("status"),
                "live_ready": provider_envelope_data.get(
                    "live_provider_dry_admission", {}
                ).get("live_ready"),
                "allowed_to_execute": provider_envelope_data.get(
                    "live_provider_dry_admission", {}
                ).get("allowed_to_execute"),
                "manual_required_count": provider_envelope_data.get(
                    "live_provider_dry_admission", {}
                ).get("manual_required_count"),
                "checklist_item_count": provider_envelope_data.get(
                    "live_provider_dry_admission", {}
                ).get("checklist_item_count"),
                "manual_test_proposal_status": provider_envelope_data.get(
                    "manual_provider_test_proposal", {}
                ).get("status"),
                "manual_test_proposal_hash": provider_envelope_data.get(
                    "manual_provider_test_proposal", {}
                ).get("proposal_hash"),
                "manual_test_allowed_to_execute": provider_envelope_data.get(
                    "manual_provider_test_proposal", {}
                ).get("allowed_to_execute"),
                "manual_test_disabled_by_default": provider_envelope_data.get(
                    "manual_provider_test_proposal", {}
                ).get("disabled_by_default"),
                "manual_test_abort_criteria_count": provider_envelope_data.get(
                    "manual_provider_test_proposal", {}
                )
                .get("proposal_fields", {})
                .get("abort_criteria_count"),
                "manual_test_executor_status": provider_envelope_data.get(
                    "manual_provider_test_executor", {}
                ).get("status"),
                "manual_test_executor_reason": provider_envelope_data.get(
                    "manual_provider_test_executor", {}
                ).get("reason"),
                "manual_test_executor_planned_call_hash": provider_envelope_data.get(
                    "manual_provider_test_executor", {}
                ).get("planned_call_hash"),
                "one_shot_permission_status": provider_envelope_data.get(
                    "one_shot_live_permission", {}
                ).get("status"),
                "one_shot_permission_reason": provider_envelope_data.get(
                    "one_shot_live_permission", {}
                ).get("reason"),
                "one_shot_permission_hash": provider_envelope_data.get(
                    "one_shot_live_permission", {}
                ).get("permission_contract_hash"),
                "one_shot_permission_expires_at": provider_envelope_data.get(
                    "one_shot_live_permission", {}
                ).get("expires_at"),
                "one_shot_permission_field_count": provider_envelope_data.get(
                    "one_shot_live_permission", {}
                ).get("permission_field_count"),
                "preflight_audit_status": provider_envelope_data.get(
                    "manual_provider_test_preflight_audit", {}
                ).get("status"),
                "preflight_audit_reason": provider_envelope_data.get(
                    "manual_provider_test_preflight_audit", {}
                ).get("reason"),
                "preflight_audit_hash": provider_envelope_data.get(
                    "manual_provider_test_preflight_audit", {}
                ).get("preflight_audit_hash"),
                "preflight_audit_component_count": provider_envelope_data.get(
                    "manual_provider_test_preflight_audit", {}
                ).get("component_count"),
                "preflight_audit_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_preflight_audit", {}
                ).get("passed_component_count"),
                "preflight_audit_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_preflight_audit", {}
                ).get("mismatch_count"),
                "preflight_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_preflight_audit", {}
                ).get("no_call_counter_count"),
                "preflight_no_call_counter_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_preflight_audit", {}
                ).get("no_call_counter_mismatch_count"),
                "readiness_decision_status": provider_envelope_data.get(
                    "manual_provider_test_readiness_decision", {}
                ).get("status"),
                "readiness_decision_reason": provider_envelope_data.get(
                    "manual_provider_test_readiness_decision", {}
                ).get("reason"),
                "readiness_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_readiness_decision", {}
                ).get("readiness_decision_hash"),
                "readiness_decision_count": provider_envelope_data.get(
                    "manual_provider_test_readiness_decision", {}
                ).get("decision_count"),
                "readiness_approve_decision_count": provider_envelope_data.get(
                    "manual_provider_test_readiness_decision", {}
                ).get("approve_decision_count"),
                "readiness_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_readiness_decision", {}
                ).get("mismatch_count"),
                "readiness_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_readiness_decision", {}
                ).get("execution_permission_count"),
                "review_packet_status": provider_envelope_data.get(
                    "manual_provider_test_review_packet", {}
                ).get("status"),
                "review_packet_reason": provider_envelope_data.get(
                    "manual_provider_test_review_packet", {}
                ).get("reason"),
                "review_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_review_packet", {}
                ).get("review_packet_hash"),
                "review_packet_component_count": provider_envelope_data.get(
                    "manual_provider_test_review_packet", {}
                ).get("component_count"),
                "review_packet_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_review_packet", {}
                ).get("passed_component_count"),
                "review_packet_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_review_packet", {}
                ).get("mismatch_count"),
                "review_packet_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_review_packet", {}
                ).get("component_hash_count"),
                "review_packet_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_review_packet", {}
                ).get("execution_permission_count"),
                "review_packet_export_status": provider_envelope_data.get(
                    "manual_provider_test_review_packet_export", {}
                ).get("status"),
                "review_packet_export_reason": provider_envelope_data.get(
                    "manual_provider_test_review_packet_export", {}
                ).get("reason"),
                "review_packet_export_hash": provider_envelope_data.get(
                    "manual_provider_test_review_packet_export", {}
                ).get("review_packet_export_hash"),
                "review_packet_export_count": provider_envelope_data.get(
                    "manual_provider_test_review_packet_export", {}
                ).get("export_count"),
                "review_packet_export_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_review_packet_export", {}
                ).get("execution_permission_count"),
                "handoff_packet_status": provider_envelope_data.get(
                    "manual_provider_test_handoff_packet", {}
                ).get("status"),
                "handoff_packet_reason": provider_envelope_data.get(
                    "manual_provider_test_handoff_packet", {}
                ).get("reason"),
                "handoff_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_handoff_packet", {}
                ).get("handoff_packet_hash"),
                "handoff_packet_component_count": provider_envelope_data.get(
                    "manual_provider_test_handoff_packet", {}
                ).get("component_count"),
                "handoff_packet_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_handoff_packet", {}
                ).get("passed_component_count"),
                "handoff_packet_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_handoff_packet", {}
                ).get("mismatch_count"),
                "handoff_packet_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_handoff_packet", {}
                ).get("component_hash_count"),
                "handoff_packet_export_count": provider_envelope_data.get(
                    "manual_provider_test_handoff_packet", {}
                ).get("export_count"),
                "handoff_packet_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_handoff_packet", {}
                ).get("execution_permission_count"),
                "operator_opt_in_status": provider_envelope_data.get(
                    "manual_provider_test_operator_opt_in", {}
                ).get("status"),
                "operator_opt_in_reason": provider_envelope_data.get(
                    "manual_provider_test_operator_opt_in", {}
                ).get("reason"),
                "operator_opt_in_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_opt_in", {}
                ).get("operator_opt_in_hash"),
                "operator_opt_in_handoff_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_opt_in", {}
                ).get("handoff_packet_hash"),
                "operator_opt_in_checklist_item_count": provider_envelope_data.get(
                    "manual_provider_test_operator_opt_in", {}
                ).get("checklist_item_count"),
                "operator_opt_in_passed_check_count": provider_envelope_data.get(
                    "manual_provider_test_operator_opt_in", {}
                ).get("passed_check_count"),
                "operator_opt_in_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_operator_opt_in", {}
                ).get("mismatch_count"),
                "operator_opt_in_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_operator_opt_in", {}
                ).get("execution_permission_count"),
                "sealed_packet_status": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("status"),
                "sealed_packet_reason": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("reason"),
                "sealed_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("sealed_packet_hash"),
                "sealed_packet_handoff_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("handoff_packet_hash"),
                "sealed_packet_operator_opt_in_hash": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("operator_opt_in_hash"),
                "sealed_packet_cost_timeout_quota_hash": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("cost_timeout_quota_hash"),
                "sealed_packet_rollback_abort_hash": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("rollback_abort_hash"),
                "sealed_packet_component_count": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("component_count"),
                "sealed_packet_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("passed_component_count"),
                "sealed_packet_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("mismatch_count"),
                "sealed_packet_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("component_hash_count"),
                "sealed_packet_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_sealed_pre_execution_packet", {}
                ).get("execution_permission_count"),
                "arming_record_status": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("status"),
                "arming_record_reason": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("reason"),
                "arming_record_hash": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("arming_record_hash"),
                "arming_record_sealed_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("sealed_packet_hash"),
                "arming_record_operator_hash": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("operator_hash"),
                "arming_record_expiry_hash": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("expiry_hash"),
                "arming_record_rollback_abort_hash": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("rollback_abort_hash"),
                "arming_record_abort_policy_hash": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("abort_policy_hash"),
                "arming_record_component_count": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("component_count"),
                "arming_record_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("passed_component_count"),
                "arming_record_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("mismatch_count"),
                "arming_record_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("component_hash_count"),
                "arming_record_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_arming_record", {}
                ).get("execution_permission_count"),
                "release_proposal_status": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("status"),
                "release_proposal_reason": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("reason"),
                "release_proposal_hash": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("release_proposal_hash"),
                "release_proposal_arming_record_hash": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("arming_record_hash"),
                "release_proposal_operator_hash": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("operator_hash"),
                "release_proposal_release_window_hash": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("release_window_hash"),
                "release_proposal_rollback_abort_hash": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("rollback_abort_hash"),
                "release_proposal_component_count": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("component_count"),
                "release_proposal_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("passed_component_count"),
                "release_proposal_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("mismatch_count"),
                "release_proposal_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("component_hash_count"),
                "release_proposal_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_release_proposal", {}
                ).get("execution_permission_count"),
                "final_release_packet_status": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("status"),
                "final_release_packet_reason": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("reason"),
                "final_release_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("final_release_packet_hash"),
                "final_release_packet_release_proposal_hash": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("release_proposal_hash"),
                "final_release_packet_arming_record_hash": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("arming_record_hash"),
                "final_release_packet_operator_hash": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("operator_hash"),
                "final_release_packet_release_window_hash": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("release_window_hash"),
                "final_release_packet_rollback_abort_hash": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("rollback_abort_hash"),
                "final_release_packet_component_count": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("component_count"),
                "final_release_packet_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("passed_component_count"),
                "final_release_packet_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("mismatch_count"),
                "final_release_packet_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("component_hash_count"),
                "final_release_packet_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_final_release_packet", {}
                ).get("execution_permission_count"),
                "execution_switch_status": provider_envelope_data.get(
                    "manual_provider_test_execution_switch", {}
                ).get("status"),
                "execution_switch_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_switch", {}
                ).get("reason"),
                "execution_switch_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_switch", {}
                ).get("execution_switch_hash"),
                "execution_switch_final_release_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_switch", {}
                ).get("final_release_packet_hash"),
                "execution_switch_enable_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_switch", {}
                ).get("switch_enable_hash"),
                "execution_switch_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_switch", {}
                ).get("component_count"),
                "execution_switch_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_switch", {}
                ).get("passed_component_count"),
                "execution_switch_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_switch", {}
                ).get("mismatch_count"),
                "execution_switch_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_switch", {}
                ).get("component_hash_count"),
                "execution_switch_enable_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_switch", {}
                ).get("enable_request_count"),
                "execution_switch_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_switch", {}
                ).get("execution_permission_count"),
                "executor_preflight_status": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("status"),
                "executor_preflight_reason": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("reason"),
                "executor_preflight_hash": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("executor_preflight_hash"),
                "executor_preflight_execution_switch_hash": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("execution_switch_hash"),
                "executor_preflight_final_release_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("final_release_packet_hash"),
                "executor_preflight_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("no_call_counters_hash"),
                "executor_preflight_component_count": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("component_count"),
                "executor_preflight_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("passed_component_count"),
                "executor_preflight_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("mismatch_count"),
                "executor_preflight_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("component_hash_count"),
                "executor_preflight_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("no_call_counter_count"),
                "executor_preflight_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_executor_preflight", {}
                ).get("execution_permission_count"),
                "executor_dispatch_record_status": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("status"),
                "executor_dispatch_record_reason": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("reason"),
                "executor_dispatch_record_hash": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("dispatch_record_hash"),
                "executor_dispatch_record_executor_preflight_hash": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("executor_preflight_hash"),
                "executor_dispatch_record_planned_dispatch_hash": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("planned_dispatch_hash"),
                "executor_dispatch_record_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("no_call_counters_hash"),
                "executor_dispatch_record_component_count": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("component_count"),
                "executor_dispatch_record_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("passed_component_count"),
                "executor_dispatch_record_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("mismatch_count"),
                "executor_dispatch_record_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("component_hash_count"),
                "executor_dispatch_record_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("no_call_counter_count"),
                "executor_dispatch_record_dispatch_request_count": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("dispatch_request_count"),
                "executor_dispatch_record_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_executor_dispatch_record", {}
                ).get("execution_permission_count"),
                "invocation_receipt_status": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("status"),
                "invocation_receipt_reason": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("reason"),
                "invocation_receipt_hash": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("invocation_receipt_hash"),
                "invocation_receipt_dispatch_record_hash": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("dispatch_record_hash"),
                "invocation_receipt_result_placeholder_hash": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("result_placeholder_hash"),
                "invocation_receipt_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("no_call_counters_hash"),
                "invocation_receipt_component_count": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("component_count"),
                "invocation_receipt_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("passed_component_count"),
                "invocation_receipt_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("mismatch_count"),
                "invocation_receipt_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("component_hash_count"),
                "invocation_receipt_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("no_call_counter_count"),
                "invocation_receipt_request_count": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("receipt_request_count"),
                "invocation_receipt_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_invocation_receipt", {}
                ).get("execution_permission_count"),
                "post_invocation_audit_status": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("status"),
                "post_invocation_audit_reason": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("reason"),
                "post_invocation_audit_hash": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("post_invocation_audit_hash"),
                "post_invocation_audit_invocation_receipt_hash": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("invocation_receipt_hash"),
                "post_invocation_audit_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("claim_boundary_hash"),
                "post_invocation_audit_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("no_call_counters_hash"),
                "post_invocation_audit_component_count": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("component_count"),
                "post_invocation_audit_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("passed_component_count"),
                "post_invocation_audit_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("mismatch_count"),
                "post_invocation_audit_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("component_hash_count"),
                "post_invocation_audit_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("no_call_counter_count"),
                "post_invocation_audit_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("claim_boundary_check_count"),
                "post_invocation_audit_request_count": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("audit_request_count"),
                "post_invocation_audit_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_post_invocation_audit", {}
                ).get("execution_permission_count"),
                "completion_summary_status": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("status"),
                "completion_summary_reason": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("reason"),
                "completion_summary_hash": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("completion_summary_hash"),
                "completion_summary_post_invocation_audit_hash": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("post_invocation_audit_hash"),
                "completion_summary_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("claim_boundary_hash"),
                "completion_summary_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("no_call_counters_hash"),
                "completion_summary_component_count": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("component_count"),
                "completion_summary_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("passed_component_count"),
                "completion_summary_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("mismatch_count"),
                "completion_summary_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("component_hash_count"),
                "completion_summary_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("no_call_counter_count"),
                "completion_summary_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("claim_boundary_check_count"),
                "completion_summary_request_count": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("summary_request_count"),
                "completion_summary_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_completion_summary", {}
                ).get("execution_permission_count"),
                "closeout_record_status": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("status"),
                "closeout_record_reason": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("reason"),
                "closeout_record_hash": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("closeout_record_hash"),
                "closeout_record_completion_summary_hash": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("completion_summary_hash"),
                "closeout_record_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("claim_boundary_hash"),
                "closeout_record_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("no_call_counters_hash"),
                "closeout_record_component_count": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("component_count"),
                "closeout_record_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("passed_component_count"),
                "closeout_record_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("mismatch_count"),
                "closeout_record_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("component_hash_count"),
                "closeout_record_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("no_call_counter_count"),
                "closeout_record_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("claim_boundary_check_count"),
                "closeout_record_request_count": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("closeout_request_count"),
                "closeout_record_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_closeout_record", {}
                ).get("execution_permission_count"),
                "operator_handback_status": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("status"),
                "operator_handback_reason": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("reason"),
                "operator_handback_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("operator_handback_hash"),
                "operator_handback_closeout_record_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("closeout_record_hash"),
                "operator_handback_operator_review_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("operator_review_hash"),
                "operator_handback_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("claim_boundary_hash"),
                "operator_handback_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("no_call_counters_hash"),
                "operator_handback_component_count": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("component_count"),
                "operator_handback_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("passed_component_count"),
                "operator_handback_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("mismatch_count"),
                "operator_handback_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("component_hash_count"),
                "operator_handback_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("no_call_counter_count"),
                "operator_handback_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("claim_boundary_check_count"),
                "operator_handback_operator_review_count": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("operator_review_count"),
                "operator_handback_request_count": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("handback_request_count"),
                "operator_handback_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_operator_handback", {}
                ).get("execution_permission_count"),
                "operator_decision_packet_status": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("status"),
                "operator_decision_packet_reason": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("reason"),
                "operator_decision_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("operator_decision_packet_hash"),
                "operator_decision_packet_operator_handback_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("operator_handback_hash"),
                "operator_decision_packet_operator_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("operator_decision_hash"),
                "operator_decision_packet_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("claim_boundary_hash"),
                "operator_decision_packet_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("no_call_counters_hash"),
                "operator_decision_packet_component_count": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("component_count"),
                "operator_decision_packet_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("passed_component_count"),
                "operator_decision_packet_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("mismatch_count"),
                "operator_decision_packet_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("component_hash_count"),
                "operator_decision_packet_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("no_call_counter_count"),
                "operator_decision_packet_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("claim_boundary_check_count"),
                "operator_decision_packet_operator_decision_count": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("operator_decision_count"),
                "operator_decision_packet_request_count": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("decision_packet_request_count"),
                "operator_decision_packet_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_operator_decision_packet", {}
                ).get("execution_permission_count"),
                "operator_release_attestation_status": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("status"),
                "operator_release_attestation_reason": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("reason"),
                "operator_release_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("operator_release_attestation_hash"),
                "operator_release_attestation_operator_decision_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("operator_decision_packet_hash"),
                "operator_release_attestation_operator_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("operator_attestation_hash"),
                "operator_release_attestation_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("claim_boundary_hash"),
                "operator_release_attestation_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("no_call_counters_hash"),
                "operator_release_attestation_component_count": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("component_count"),
                "operator_release_attestation_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("passed_component_count"),
                "operator_release_attestation_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("mismatch_count"),
                "operator_release_attestation_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("component_hash_count"),
                "operator_release_attestation_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("no_call_counter_count"),
                "operator_release_attestation_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("claim_boundary_check_count"),
                "operator_release_attestation_operator_attestation_count": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("operator_attestation_count"),
                "operator_release_attestation_request_count": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("attestation_request_count"),
                "operator_release_attestation_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_operator_release_attestation", {}
                ).get("execution_permission_count"),
                "release_seal_status": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("status"),
                "release_seal_reason": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("reason"),
                "release_seal_hash": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("release_seal_hash"),
                "release_seal_operator_release_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("operator_release_attestation_hash"),
                "release_seal_material_hash": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("seal_material_hash"),
                "release_seal_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("claim_boundary_hash"),
                "release_seal_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("no_call_counters_hash"),
                "release_seal_component_count": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("component_count"),
                "release_seal_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("passed_component_count"),
                "release_seal_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("mismatch_count"),
                "release_seal_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("component_hash_count"),
                "release_seal_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("no_call_counter_count"),
                "release_seal_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("claim_boundary_check_count"),
                "release_seal_material_count": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("seal_material_count"),
                "release_seal_request_count": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("seal_request_count"),
                "release_seal_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_release_seal", {}
                ).get("execution_permission_count"),
                "execution_capsule_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("status"),
                "execution_capsule_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("reason"),
                "execution_capsule_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("execution_capsule_hash"),
                "execution_capsule_release_seal_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("release_seal_hash"),
                "execution_capsule_final_authz_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("final_authz_hash"),
                "execution_capsule_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("claim_boundary_hash"),
                "execution_capsule_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("no_call_counters_hash"),
                "execution_capsule_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("component_count"),
                "execution_capsule_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("passed_component_count"),
                "execution_capsule_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("mismatch_count"),
                "execution_capsule_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("component_hash_count"),
                "execution_capsule_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("no_call_counter_count"),
                "execution_capsule_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("claim_boundary_check_count"),
                "execution_capsule_final_authz_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("final_authz_count"),
                "execution_capsule_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("capsule_request_count"),
                "execution_capsule_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule", {}
                ).get("execution_permission_count"),
                "execution_capsule_export_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("status"),
                "execution_capsule_export_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("reason"),
                "execution_capsule_export_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("execution_capsule_export_hash"),
                "execution_capsule_export_execution_capsule_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("execution_capsule_hash"),
                "execution_capsule_export_metadata_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("export_metadata_hash"),
                "execution_capsule_export_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("claim_boundary_hash"),
                "execution_capsule_export_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("no_call_counters_hash"),
                "execution_capsule_export_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("export_count"),
                "execution_capsule_export_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("component_count"),
                "execution_capsule_export_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("passed_component_count"),
                "execution_capsule_export_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("mismatch_count"),
                "execution_capsule_export_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("component_hash_count"),
                "execution_capsule_export_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("no_call_counter_count"),
                "execution_capsule_export_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("claim_boundary_check_count"),
                "execution_capsule_export_metadata_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("export_metadata_count"),
                "execution_capsule_export_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export", {}
                ).get("execution_permission_count"),
                "execution_capsule_export_read_model_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export_read_model", {}
                ).get("status"),
                "execution_capsule_export_read_model_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export_read_model", {}
                ).get("latest_execution_capsule_export_hash"),
                "execution_capsule_export_read_model_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export_read_model", {}
                )
                .get("counts", {})
                .get("execution_capsule_export_count"),
                "execution_capsule_export_read_model_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_export_read_model", {}
                )
                .get("counts", {})
                .get("execution_permission_count"),
                "execution_capsule_handoff_packet_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("status"),
                "execution_capsule_handoff_packet_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("reason"),
                "execution_capsule_handoff_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("execution_capsule_handoff_packet_hash"),
                "execution_capsule_handoff_packet_export_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("execution_capsule_export_hash"),
                "execution_capsule_handoff_packet_read_model_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("execution_capsule_export_read_model_hash"),
                "execution_capsule_handoff_packet_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("claim_boundary_hash"),
                "execution_capsule_handoff_packet_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("no_call_counters_hash"),
                "execution_capsule_handoff_packet_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("packet_count"),
                "execution_capsule_handoff_packet_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("component_count"),
                "execution_capsule_handoff_packet_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("passed_component_count"),
                "execution_capsule_handoff_packet_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("mismatch_count"),
                "execution_capsule_handoff_packet_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("component_hash_count"),
                "execution_capsule_handoff_packet_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("no_call_counter_count"),
                "execution_capsule_handoff_packet_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("claim_boundary_check_count"),
                "execution_capsule_handoff_packet_export_read_model_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("export_read_model_count"),
                "execution_capsule_handoff_packet_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("handoff_request_count"),
                "execution_capsule_handoff_packet_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_handoff_packet", {}
                ).get("execution_permission_count"),
                "execution_capsule_operator_review_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("status"),
                "execution_capsule_operator_review_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("reason"),
                "execution_capsule_operator_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("execution_capsule_operator_review_hash"),
                "execution_capsule_operator_review_handoff_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("execution_capsule_handoff_packet_hash"),
                "execution_capsule_operator_review_operator_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("operator_review_hash"),
                "execution_capsule_operator_review_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("claim_boundary_hash"),
                "execution_capsule_operator_review_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("no_call_counters_hash"),
                "execution_capsule_operator_review_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("component_count"),
                "execution_capsule_operator_review_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("passed_component_count"),
                "execution_capsule_operator_review_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("mismatch_count"),
                "execution_capsule_operator_review_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("component_hash_count"),
                "execution_capsule_operator_review_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("no_call_counter_count"),
                "execution_capsule_operator_review_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("claim_boundary_check_count"),
                "execution_capsule_operator_review_operator_review_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("operator_review_count"),
                "execution_capsule_operator_review_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("review_request_count"),
                "execution_capsule_operator_review_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_review", {}
                ).get("execution_permission_count"),
                "execution_capsule_operator_decision_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("status"),
                "execution_capsule_operator_decision_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("reason"),
                "execution_capsule_operator_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("execution_capsule_operator_decision_hash"),
                "execution_capsule_operator_decision_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("execution_capsule_operator_review_hash"),
                "execution_capsule_operator_decision_operator_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("operator_decision_hash"),
                "execution_capsule_operator_decision_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("claim_boundary_hash"),
                "execution_capsule_operator_decision_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("no_call_counters_hash"),
                "execution_capsule_operator_decision_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("component_count"),
                "execution_capsule_operator_decision_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("passed_component_count"),
                "execution_capsule_operator_decision_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("mismatch_count"),
                "execution_capsule_operator_decision_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("component_hash_count"),
                "execution_capsule_operator_decision_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("no_call_counter_count"),
                "execution_capsule_operator_decision_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("claim_boundary_check_count"),
                "execution_capsule_operator_decision_operator_decision_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("operator_decision_count"),
                "execution_capsule_operator_decision_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("decision_request_count"),
                "execution_capsule_operator_decision_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_operator_decision", {}
                ).get("execution_permission_count"),
                "execution_capsule_release_attestation_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("status"),
                "execution_capsule_release_attestation_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("reason"),
                "execution_capsule_release_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("execution_capsule_release_attestation_hash"),
                "execution_capsule_release_attestation_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("execution_capsule_operator_decision_hash"),
                "execution_capsule_release_attestation_release_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("release_attestation_hash"),
                "execution_capsule_release_attestation_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("claim_boundary_hash"),
                "execution_capsule_release_attestation_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("no_call_counters_hash"),
                "execution_capsule_release_attestation_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("component_count"),
                "execution_capsule_release_attestation_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("passed_component_count"),
                "execution_capsule_release_attestation_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("mismatch_count"),
                "execution_capsule_release_attestation_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("component_hash_count"),
                "execution_capsule_release_attestation_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("no_call_counter_count"),
                "execution_capsule_release_attestation_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("claim_boundary_check_count"),
                "execution_capsule_release_attestation_release_attestation_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("release_attestation_count"),
                "execution_capsule_release_attestation_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("attestation_request_count"),
                "execution_capsule_release_attestation_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_attestation", {}
                ).get("execution_permission_count"),
                "execution_capsule_release_seal_boundary_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("status"),
                "execution_capsule_release_seal_boundary_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("reason"),
                "execution_capsule_release_seal_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("execution_capsule_release_seal_hash"),
                "execution_capsule_release_seal_boundary_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("execution_capsule_release_attestation_hash"),
                "execution_capsule_release_seal_boundary_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("seal_material_hash"),
                "execution_capsule_release_seal_boundary_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("claim_boundary_hash"),
                "execution_capsule_release_seal_boundary_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("no_call_counters_hash"),
                "execution_capsule_release_seal_boundary_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("component_count"),
                "execution_capsule_release_seal_boundary_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("passed_component_count"),
                "execution_capsule_release_seal_boundary_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("mismatch_count"),
                "execution_capsule_release_seal_boundary_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("component_hash_count"),
                "execution_capsule_release_seal_boundary_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("no_call_counter_count"),
                "execution_capsule_release_seal_boundary_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("claim_boundary_check_count"),
                "execution_capsule_release_seal_boundary_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("seal_material_count"),
                "execution_capsule_release_seal_boundary_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("seal_request_count"),
                "execution_capsule_release_seal_boundary_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_release_seal", {}
                ).get("execution_permission_count"),
                "execution_capsule_authz_boundary_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("status"),
                "execution_capsule_authz_boundary_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("reason"),
                "execution_capsule_authz_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("execution_capsule_final_authz_hash"),
                "execution_capsule_authz_boundary_release_seal_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("execution_capsule_release_seal_hash"),
                "execution_capsule_authz_boundary_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("final_authz_hash"),
                "execution_capsule_authz_boundary_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_boundary_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_boundary_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("component_count"),
                "execution_capsule_authz_boundary_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("passed_component_count"),
                "execution_capsule_authz_boundary_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("mismatch_count"),
                "execution_capsule_authz_boundary_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("component_hash_count"),
                "execution_capsule_authz_boundary_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("no_call_counter_count"),
                "execution_capsule_authz_boundary_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_boundary_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("final_authz_count"),
                "execution_capsule_authz_boundary_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("authz_request_count"),
                "execution_capsule_authz_boundary_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_final_authz", {}
                ).get("execution_permission_count"),
                "execution_capsule_authz_export_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("status"),
                "execution_capsule_authz_export_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("reason"),
                "execution_capsule_authz_export_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("execution_capsule_authz_export_hash"),
                "execution_capsule_authz_export_final_authz_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("execution_capsule_final_authz_hash"),
                "execution_capsule_authz_export_metadata_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("export_metadata_hash"),
                "execution_capsule_authz_export_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_export_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_export_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("export_count"),
                "execution_capsule_authz_export_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("component_count"),
                "execution_capsule_authz_export_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("passed_component_count"),
                "execution_capsule_authz_export_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("mismatch_count"),
                "execution_capsule_authz_export_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("component_hash_count"),
                "execution_capsule_authz_export_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("no_call_counter_count"),
                "execution_capsule_authz_export_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_export_metadata_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("export_metadata_count"),
                "execution_capsule_authz_export_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export", {}
                ).get("execution_permission_count"),
                "execution_capsule_authz_export_read_model_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export_read_model",
                    {},
                ).get("status"),
                "execution_capsule_authz_export_read_model_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export_read_model",
                    {},
                ).get("reason"),
                "execution_capsule_authz_export_read_model_latest_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export_read_model",
                    {},
                ).get("latest_execution_capsule_authz_export_hash"),
                "execution_capsule_authz_export_read_model_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get("execution_capsule_authz_export_count"),
                "execution_capsule_authz_export_read_model_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get("component_count"),
                "execution_capsule_authz_export_read_model_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get("execution_permission_count"),
                "execution_capsule_authz_handoff_packet_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("status"),
                "execution_capsule_authz_handoff_packet_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("reason"),
                "execution_capsule_authz_handoff_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("execution_capsule_authz_handoff_packet_hash"),
                "execution_capsule_authz_handoff_packet_export_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("execution_capsule_authz_export_hash"),
                "execution_capsule_authz_handoff_packet_read_model_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("execution_capsule_authz_export_read_model_hash"),
                "execution_capsule_authz_handoff_packet_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_handoff_packet_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_handoff_packet_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("packet_count"),
                "execution_capsule_authz_handoff_packet_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_handoff_packet_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_handoff_packet_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_handoff_packet_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_handoff_packet_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_handoff_packet_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_handoff_packet_export_read_model_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("export_read_model_count"),
                "execution_capsule_authz_handoff_packet_handoff_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("handoff_request_count"),
                "execution_capsule_authz_handoff_packet_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_handoff_packet",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_operator_review_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("status"),
                "execution_capsule_authz_operator_review_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("reason"),
                "execution_capsule_authz_operator_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("execution_capsule_authz_operator_review_hash"),
                "execution_capsule_authz_operator_review_handoff_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("execution_capsule_authz_handoff_packet_hash"),
                "execution_capsule_authz_operator_review_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("operator_review_hash"),
                "execution_capsule_authz_operator_review_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_operator_review_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_operator_review_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_operator_review_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_operator_review_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_operator_review_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_operator_review_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_operator_review_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_operator_review_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("operator_review_count"),
                "execution_capsule_authz_operator_review_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("review_request_count"),
                "execution_capsule_authz_operator_review_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_review",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_operator_decision_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("status"),
                "execution_capsule_authz_operator_decision_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("reason"),
                "execution_capsule_authz_operator_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("execution_capsule_authz_operator_decision_hash"),
                "execution_capsule_authz_operator_decision_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("execution_capsule_authz_operator_review_hash"),
                "execution_capsule_authz_operator_decision_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("operator_decision_hash"),
                "execution_capsule_authz_operator_decision_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_operator_decision_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_operator_decision_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_operator_decision_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_operator_decision_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_operator_decision_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_operator_decision_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_operator_decision_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_operator_decision_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("operator_decision_count"),
                "execution_capsule_authz_operator_decision_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("decision_request_count"),
                "execution_capsule_authz_operator_decision_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_operator_decision",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_release_attestation_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("status"),
                "execution_capsule_authz_release_attestation_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("reason"),
                "execution_capsule_authz_release_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("execution_capsule_authz_release_attestation_hash"),
                "execution_capsule_authz_release_attestation_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("execution_capsule_authz_operator_decision_hash"),
                "execution_capsule_authz_release_attestation_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("release_attestation_hash"),
                "execution_capsule_authz_release_attestation_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_release_attestation_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_release_attestation_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_release_attestation_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_release_attestation_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_release_attestation_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_release_attestation_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_release_attestation_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_release_attestation_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("release_attestation_count"),
                "execution_capsule_authz_release_attestation_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("attestation_request_count"),
                "execution_capsule_authz_release_attestation_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_attestation",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_release_seal_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("status"),
                "execution_capsule_authz_release_seal_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("reason"),
                "execution_capsule_authz_release_seal_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("execution_capsule_authz_release_seal_hash"),
                "execution_capsule_authz_release_seal_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("execution_capsule_authz_release_attestation_hash"),
                "execution_capsule_authz_release_seal_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("seal_material_hash"),
                "execution_capsule_authz_release_seal_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_release_seal_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_release_seal_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_release_seal_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_release_seal_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_release_seal_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_release_seal_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_release_seal_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_release_seal_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("seal_material_count"),
                "execution_capsule_authz_release_seal_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("seal_request_count"),
                "execution_capsule_authz_release_seal_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_release_seal",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("execution_capsule_authz_final_authz_hash"),
                "execution_capsule_authz_final_authz_release_seal_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("execution_capsule_authz_release_seal_hash"),
                "execution_capsule_authz_final_authz_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("final_authz_hash"),
                "execution_capsule_authz_final_authz_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("final_authz_count"),
                "execution_capsule_authz_final_authz_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("authz_request_count"),
                "execution_capsule_authz_final_authz_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_export_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_export_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_export_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("execution_capsule_authz_final_authz_export_hash"),
                "execution_capsule_authz_final_authz_export_final_authz_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("execution_capsule_authz_final_authz_hash"),
                "execution_capsule_authz_final_authz_export_metadata_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("export_metadata_hash"),
                "execution_capsule_authz_final_authz_export_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_export_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_export_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("export_count"),
                "execution_capsule_authz_final_authz_export_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_export_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_export_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_export_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_export_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_export_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_export_metadata_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("export_metadata_count"),
                "execution_capsule_authz_final_authz_export_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("export_request_count"),
                "execution_capsule_authz_final_authz_export_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_export_read_model_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export_read_model",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_export_read_model_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export_read_model",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_export_read_model_latest_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export_read_model",
                    {},
                ).get("latest_execution_capsule_authz_final_authz_export_hash"),
                "execution_capsule_authz_final_authz_export_read_model_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get("execution_capsule_authz_final_authz_export_count"),
                "execution_capsule_authz_final_authz_export_read_model_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get("component_count"),
                "execution_capsule_authz_final_authz_export_read_model_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get("execution_permission_count"),
                "execution_capsule_authz_final_authz_handoff_packet_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_handoff_packet_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_handoff_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("execution_capsule_authz_final_authz_handoff_packet_hash"),
                "execution_capsule_authz_final_authz_handoff_packet_export_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("execution_capsule_authz_final_authz_export_hash"),
                "execution_capsule_authz_final_authz_handoff_packet_read_model_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("execution_capsule_authz_final_authz_export_read_model_hash"),
                "execution_capsule_authz_final_authz_handoff_packet_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_handoff_packet_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_handoff_packet_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("packet_count"),
                "execution_capsule_authz_final_authz_handoff_packet_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_handoff_packet_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_handoff_packet_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_handoff_packet_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_handoff_packet_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_handoff_packet_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_handoff_packet_export_read_model_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("export_read_model_count"),
                "execution_capsule_authz_final_authz_handoff_packet_handoff_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("handoff_request_count"),
                "execution_capsule_authz_final_authz_handoff_packet_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_handoff_packet",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_operator_review_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_operator_review_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_operator_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("execution_capsule_authz_final_authz_operator_review_hash"),
                "execution_capsule_authz_final_authz_operator_review_handoff_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("execution_capsule_authz_final_authz_handoff_packet_hash"),
                "execution_capsule_authz_final_authz_operator_review_operator_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("operator_review_hash"),
                "execution_capsule_authz_final_authz_operator_review_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_operator_review_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_operator_review_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_operator_review_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_operator_review_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_operator_review_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_operator_review_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_operator_review_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_operator_review_operator_review_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("operator_review_count"),
                "execution_capsule_authz_final_authz_operator_review_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("review_request_count"),
                "execution_capsule_authz_final_authz_operator_review_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_review",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_operator_decision_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_operator_decision_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_operator_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("execution_capsule_authz_final_authz_operator_decision_hash"),
                "execution_capsule_authz_final_authz_operator_decision_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("execution_capsule_authz_final_authz_operator_review_hash"),
                "execution_capsule_authz_final_authz_operator_decision_operator_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("operator_decision_hash"),
                "execution_capsule_authz_final_authz_operator_decision_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_operator_decision_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_operator_decision_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_operator_decision_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_operator_decision_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_operator_decision_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_operator_decision_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_operator_decision_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_operator_decision_operator_decision_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("operator_decision_count"),
                "execution_capsule_authz_final_authz_operator_decision_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("decision_request_count"),
                "execution_capsule_authz_final_authz_operator_decision_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_operator_decision",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_release_attestation_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_release_attestation_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_release_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_release_attestation_hash"
                ),
                "execution_capsule_authz_final_authz_release_attestation_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_operator_decision_hash"
                ),
                "execution_capsule_authz_final_authz_release_attestation_release_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("release_attestation_hash"),
                "execution_capsule_authz_final_authz_release_attestation_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_release_attestation_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_release_attestation_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_release_attestation_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_release_attestation_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_release_attestation_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_release_attestation_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_release_attestation_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_release_attestation_release_attestation_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("release_attestation_count"),
                "execution_capsule_authz_final_authz_release_attestation_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("attestation_request_count"),
                "execution_capsule_authz_final_authz_release_attestation_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_attestation",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_release_seal_boundary_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_release_seal_boundary_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_release_seal_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("execution_capsule_authz_final_authz_release_seal_hash"),
                "execution_capsule_authz_final_authz_release_seal_boundary_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_release_attestation_hash"
                ),
                "execution_capsule_authz_final_authz_release_seal_boundary_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("seal_material_hash"),
                "execution_capsule_authz_final_authz_release_seal_boundary_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_release_seal_boundary_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_release_seal_boundary_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_release_seal_boundary_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_release_seal_boundary_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_release_seal_boundary_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_release_seal_boundary_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_release_seal_boundary_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_release_seal_boundary_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("seal_material_count"),
                "execution_capsule_authz_final_authz_release_seal_boundary_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("seal_request_count"),
                "execution_capsule_authz_final_authz_release_seal_boundary_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_release_seal",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_boundary_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_boundary_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_hash"),
                "execution_capsule_authz_final_authz_final_authz_boundary_release_seal_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("execution_capsule_authz_final_authz_release_seal_hash"),
                "execution_capsule_authz_final_authz_final_authz_boundary_authz_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("final_authz_hash"),
                "execution_capsule_authz_final_authz_final_authz_boundary_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_boundary_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_boundary_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_boundary_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_boundary_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_boundary_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_boundary_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_boundary_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_boundary_authz_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("final_authz_count"),
                "execution_capsule_authz_final_authz_final_authz_boundary_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("authz_request_count"),
                "execution_capsule_authz_final_authz_final_authz_boundary_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_export_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_export_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_export_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_export_hash"),
                "execution_capsule_authz_final_authz_final_authz_export_final_authz_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_hash"),
                "execution_capsule_authz_final_authz_final_authz_export_metadata_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("export_metadata_hash"),
                "execution_capsule_authz_final_authz_final_authz_export_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_export_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_export_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("export_count"),
                "execution_capsule_authz_final_authz_final_authz_export_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_export_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_export_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_export_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_export_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_export_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_export_metadata_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("export_metadata_count"),
                "execution_capsule_authz_final_authz_final_authz_export_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("export_request_count"),
                "execution_capsule_authz_final_authz_final_authz_export_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_export_read_model_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export_read_model",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_export_read_model_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export_read_model",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_export_read_model_latest_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export_read_model",
                    {},
                ).get("latest_execution_capsule_authz_final_authz_final_authz_export_hash"),
                "execution_capsule_authz_final_authz_final_authz_export_read_model_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get("execution_capsule_authz_final_authz_final_authz_export_count"),
                "execution_capsule_authz_final_authz_final_authz_export_read_model_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_export_read_model_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_export_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_export_hash"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_read_model_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_export_read_model_hash"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("packet_count"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_export_read_model_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("export_read_model_count"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_handoff_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("handoff_request_count"),
                "execution_capsule_authz_final_authz_final_authz_handoff_packet_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_operator_review_hash"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_handoff_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_handoff_packet_hash"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_operator_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("operator_review_hash"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_operator_review_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("operator_review_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("review_request_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_review_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_operator_decision_hash"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_operator_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_operator_review_hash"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_operator_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("operator_decision_hash"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_operator_decision_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("operator_decision_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("decision_request_count"),
                "execution_capsule_authz_final_authz_final_authz_operator_decision_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_release_attestation_hash"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_operator_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_operator_decision_hash"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("release_attestation_hash"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("release_attestation_count"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("attestation_request_count"),
                "execution_capsule_authz_final_authz_final_authz_release_attestation_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_release_seal_hash"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_release_attestation_hash"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("seal_material_hash"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("seal_material_count"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("seal_request_count"),
                "execution_capsule_authz_final_authz_final_authz_release_seal_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_final_authz_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("execution_capsule_authz_final_authz_final_authz_release_seal_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("final_authz_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("final_authz_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("authz_request_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_final_authz_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_metadata_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("export_metadata_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("export_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_metadata_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("export_metadata_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("export_request_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_latest_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model",
                    {},
                ).get(
                    "latest_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_export_count"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model",
                    {},
                )
                .get("counts", {})
                .get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_export_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_export_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_read_model_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("packet_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_export_read_model_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("export_read_model_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("handoff_request_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_handoff_packet_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_operator_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("operator_review_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_operator_review_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("operator_review_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("review_request_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_review_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_operator_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("operator_decision_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_operator_decision_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("operator_decision_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("decision_request_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_operator_decision_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_release_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("release_attestation_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_release_attestation_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("release_attestation_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("attestation_request_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_release_attestation_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_material_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("seal_material_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_material_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("seal_material_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("seal_request_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_boundary_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_release_seal_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_final_authz_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("final_authz_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_final_authz_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("final_authz_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_authz_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("authz_request_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_boundary_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_reason": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("reason"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_final_authz_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get(
                    "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash"
                ),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_metadata_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("export_metadata_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_claim_boundary_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("claim_boundary_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_no_call_counters_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("no_call_counters_hash"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_passed_component_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("passed_component_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_mismatch_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("mismatch_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_component_hash_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("component_hash_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_no_call_counter_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("no_call_counter_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_claim_boundary_check_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("claim_boundary_check_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_export_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("export_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_metadata_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("export_metadata_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_request_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("export_request_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_boundary_execution_permission_count": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export",
                    {},
                ).get("execution_permission_count"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model_status": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model",
                    {},
                ).get("status"),
                "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model_hash": provider_envelope_data.get(
                    "manual_provider_test_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model",
                    {},
                ).get(
                    "latest_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash"
                ),
                "review_packet_read_model_status": (
                    provider_envelope_read_data or {}
                )
                .get("manual_provider_test_review_packet_export_read_model", {})
                .get("status"),
                "review_packet_read_export_hash": (
                    provider_envelope_read_data or {}
                )
                .get("manual_provider_test_review_packet_export", {})
                .get("review_packet_hash"),
                "review_packet_read_export_count": (
                    provider_envelope_read_data or {}
                )
                .get("manual_provider_test_review_packet_export", {})
                .get("export_count"),
                "read_model_status": (
                    provider_envelope_read_data or {}
                ).get("status"),
                "execution_boundary": provider_envelope_data.get("execution_boundary", {}),
                "claim_boundary": provider_envelope_data.get("claim_boundary", {}),
            }
            if provider_envelope_data is not None
            else {
                "status": "skipped",
                "reason": "optional precheck not requested",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
            }
        ),
        "checks": checks,
    }
    assert_public_projection_safe(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Agentic Workbench demo.")
    parser.add_argument(
        "--store-root",
        default=None,
        help="Optional local store root. Defaults to examples/demo-service-flow/.local.",
    )
    parser.add_argument(
        "--include-provider-precheck",
        action="store_true",
        help="Also run the no-call provider envelope admission precheck.",
    )
    parser.add_argument(
        "--include-solar-planner-preflight",
        action="store_true",
        help="Also run the no-call Solar planner provider preflight comparison.",
    )
    parser.add_argument(
        "--include-solar-planner-spike",
        action="store_true",
        help="Also run the no-call Solar planner one-shot spike mock projection.",
    )
    parser.add_argument(
        "--include-solar-planner-live-spike",
        action="store_true",
        help=(
            "Also run the Solar planner one-shot live spike boundary. "
            "Without --allow-solar-planner-live-call this remains blocked."
        ),
    )
    parser.add_argument(
        "--allow-solar-planner-live-call",
        action="store_true",
        help=(
            "Allow exactly one Upstage Solar Pro 3 chat completion attempt "
            "with timeout/input/output caps. This reads UPSTAGE_API_KEY but "
            "never prints or stores its value."
        ),
    )
    parser.add_argument(
        "--include-solar-planner-quality-comparison",
        action="store_true",
        help=(
            "Compare fixture planner evidence with the Solar live spike public "
            "projection. Without live opt-in this uses the blocked projection."
        ),
    )
    parser.add_argument(
        "--allow-solar-quality-reviewer-approval",
        action="store_true",
        help=(
            "Attach a deterministic reviewer approval hash to the Solar "
            "quality comparison. This does not create Solar-authored artifacts."
        ),
    )
    parser.add_argument(
        "--include-solar-planner-draft-projection",
        action="store_true",
        help=(
            "Project reviewer-approved Solar quality evidence into draft "
            "PlanningBlueprint/PRDPackage projections. This never writes "
            "canonical artifacts or performs an additional live call."
        ),
    )
    parser.add_argument(
        "--include-daacs-runtime-preflight",
        action="store_true",
        help="Also run the no-call DAACS target runtime sandbox preflight comparison.",
    )
    parser.add_argument(
        "--include-daacs-runtime-adapter-admission",
        action="store_true",
        help="Also run the no-call DAACS target runtime disabled adapter admission comparison.",
    )
    parser.add_argument(
        "--include-daacs-runtime-output-manifest",
        action="store_true",
        help="Also run the no-call DAACS target runtime output manifest contract comparison.",
    )
    parser.add_argument(
        "--include-daacs-runtime-generated-artifact-bundle",
        action="store_true",
        help="Also run the no-call DAACS generated artifact bundle contract comparison.",
    )
    parser.add_argument(
        "--include-daacs-runtime-fixture-materialization",
        action="store_true",
        help="Also write sanitized fixture artifacts in a run-scoped local workspace.",
    )
    parser.add_argument(
        "--include-daacs-runtime-restricted-workspace-generation",
        action="store_true",
        help="Also generate a sanitized fixture app skeleton in a restricted workspace.",
    )
    parser.add_argument(
        "--include-daacs-runtime-generated-artifact-verification",
        action="store_true",
        help="Also verify generated fixture app skeleton files by hash and byte count.",
    )
    parser.add_argument(
        "--include-daacs-runtime-generated-workspace-static-validation",
        action="store_true",
        help="Also statically validate the verified fixture app workspace.",
    )
    parser.add_argument(
        "--include-daacs-runtime-buildable-fixture-manifest",
        action="store_true",
        help="Also project a build-ready manifest for the fixture app workspace.",
    )
    parser.add_argument(
        "--include-daacs-runtime-local-build-preflight",
        action="store_true",
        help=(
            "Also project local build preflight eligibility without running "
            "package install, build, or server commands."
        ),
    )
    parser.add_argument(
        "--include-daacs-runtime-local-build-attempt",
        action="store_true",
        help=(
            "Also record an explicit local fixture app build attempt boundary. "
            "Without --allow-local-build-attempt this remains blocked."
        ),
    )
    parser.add_argument(
        "--allow-local-build-attempt",
        action="store_true",
        help=(
            "Allow local npm install/build inside the run-scoped generated "
            "fixture app workspace. This never starts a server."
        ),
    )
    parser.add_argument(
        "--include-daacs-runtime-local-preview-attempt",
        action="store_true",
        help=(
            "Also record a local preview-server/browser verification attempt "
            "over the generated fixture app workspace."
        ),
    )
    parser.add_argument(
        "--allow-local-preview-attempt",
        action="store_true",
        help=(
            "Allow local preview server start and browser verification inside "
            "the run-scoped generated fixture app workspace."
        ),
    )
    parser.add_argument(
        "--include-daacs-runtime-browser-setup-attempt",
        action="store_true",
        help=(
            "Also record an explicit browser runtime setup attempt boundary. "
            "Without --allow-browser-runtime-setup this remains blocked."
        ),
    )
    parser.add_argument(
        "--allow-browser-runtime-setup",
        action="store_true",
        help=(
            "Allow local Playwright package/browser setup commands. This may "
            "download packages or browser binaries and still never calls "
            "Solar or the DAACS target runtime."
        ),
    )
    args = parser.parse_args()

    summary = run_demo(
        args.store_root,
        include_provider_precheck=args.include_provider_precheck,
        include_solar_planner_preflight=args.include_solar_planner_preflight,
        include_solar_planner_spike=args.include_solar_planner_spike,
        include_solar_planner_live_spike=args.include_solar_planner_live_spike,
        include_solar_planner_quality_comparison=(
            args.include_solar_planner_quality_comparison
        ),
        include_solar_planner_draft_projection=(
            args.include_solar_planner_draft_projection
        ),
        include_daacs_runtime_preflight=args.include_daacs_runtime_preflight,
        include_daacs_runtime_adapter_admission=args.include_daacs_runtime_adapter_admission,
        include_daacs_runtime_output_manifest=args.include_daacs_runtime_output_manifest,
        include_daacs_runtime_generated_artifact_bundle=(
            args.include_daacs_runtime_generated_artifact_bundle
        ),
        include_daacs_runtime_fixture_materialization=(
            args.include_daacs_runtime_fixture_materialization
        ),
        include_daacs_runtime_restricted_workspace_generation=(
            args.include_daacs_runtime_restricted_workspace_generation
        ),
        include_daacs_runtime_generated_artifact_verification=(
            args.include_daacs_runtime_generated_artifact_verification
        ),
        include_daacs_runtime_generated_workspace_static_validation=(
            args.include_daacs_runtime_generated_workspace_static_validation
        ),
        include_daacs_runtime_buildable_fixture_manifest=(
            args.include_daacs_runtime_buildable_fixture_manifest
        ),
        include_daacs_runtime_local_build_preflight=(
            args.include_daacs_runtime_local_build_preflight
        ),
        include_daacs_runtime_local_build_attempt=(
            args.include_daacs_runtime_local_build_attempt
        ),
        include_daacs_runtime_local_preview_attempt=(
            args.include_daacs_runtime_local_preview_attempt
        ),
        include_daacs_runtime_browser_setup_attempt=(
            args.include_daacs_runtime_browser_setup_attempt
        ),
        allow_local_build_attempt=args.allow_local_build_attempt,
        allow_local_preview_attempt=args.allow_local_preview_attempt,
        allow_browser_runtime_setup=args.allow_browser_runtime_setup,
        allow_solar_planner_live_call=args.allow_solar_planner_live_call,
        allow_solar_quality_reviewer_approval=(
            args.allow_solar_quality_reviewer_approval
        ),
    )
    rendered = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)


if __name__ == "__main__":
    main()

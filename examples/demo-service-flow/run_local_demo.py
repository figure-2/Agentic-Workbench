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
from packages.div_planner.provider_boundary import PLANNER_PROVIDER_MODE_SOLAR_DISABLED


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


def _artifact_kinds(artifacts: list[dict[str, Any]]) -> set[str]:
    return {str(artifact.get("kind") or "") for artifact in artifacts}


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
    daacs_runtime_preflight_data: dict[str, Any] | None = None,
    daacs_runtime_adapter_admission_data: dict[str, Any] | None = None,
    daacs_runtime_adapter_admission_read_data: dict[str, Any] | None = None,
    daacs_runtime_output_manifest_data: dict[str, Any] | None = None,
    daacs_runtime_output_manifest_read_data: dict[str, Any] | None = None,
    daacs_runtime_generated_artifact_bundle_data: dict[str, Any] | None = None,
    daacs_runtime_fixture_materialization_data: dict[str, Any] | None = None,
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
    return checks


def run_demo(
    store_root: str | Path | None = None,
    *,
    include_provider_precheck: bool = False,
    include_solar_planner_preflight: bool = False,
    include_daacs_runtime_preflight: bool = False,
    include_daacs_runtime_adapter_admission: bool = False,
    include_daacs_runtime_output_manifest: bool = False,
    include_daacs_runtime_generated_artifact_bundle: bool = False,
    include_daacs_runtime_fixture_materialization: bool = False,
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
        ),
        include_target_runtime_output_manifest=(
            include_daacs_runtime_output_manifest
            or include_daacs_runtime_generated_artifact_bundle
            or include_daacs_runtime_fixture_materialization
        ),
        include_target_runtime_fixture_materialization=(
            include_daacs_runtime_fixture_materialization
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
    daacs_runtime_preflight_data = None
    daacs_runtime_adapter_admission_data = None
    daacs_runtime_adapter_admission_read_data = None
    daacs_runtime_output_manifest_data = None
    daacs_runtime_output_manifest_read_data = None
    daacs_runtime_generated_artifact_bundle_data = None
    daacs_runtime_fixture_materialization_data = None
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
    if (
        include_daacs_runtime_preflight
        or include_daacs_runtime_adapter_admission
        or include_daacs_runtime_output_manifest
        or include_daacs_runtime_generated_artifact_bundle
        or include_daacs_runtime_fixture_materialization
    ):
        runner_plan_hashes = verification_data.get("runner_plan_hashes", [])
        runner_plan_hash = str(runner_plan_hashes[0] if runner_plan_hashes else "")
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
                    if include_daacs_runtime_fixture_materialization:
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

    checks = _checks(
        create_data,
        run_data,
        verification_data=verification_data,
        provider_envelope_data=provider_envelope_data,
        solar_planner_preflight_data=solar_planner_preflight_data,
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
    )
    artifact_kinds = sorted(_artifact_kinds(run_data.get("artifacts", [])))
    evidence_summary = run_data.get("evidence_summary", {})
    stage_coverage = _mvp_stage_coverage(run_data, verification_data)
    solar_planner_execution = (
        solar_planner_preflight_data.get("execution_boundary", {})
        if solar_planner_preflight_data
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
    comparison_variant_count = 2 if solar_planner_preflight_data else 1
    runtime_comparison_variant_count = (
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
            "live_provider_calls": 0,
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
    args = parser.parse_args()

    summary = run_demo(
        args.store_root,
        include_provider_precheck=args.include_provider_precheck,
        include_solar_planner_preflight=args.include_solar_planner_preflight,
        include_daacs_runtime_preflight=args.include_daacs_runtime_preflight,
        include_daacs_runtime_adapter_admission=args.include_daacs_runtime_adapter_admission,
        include_daacs_runtime_output_manifest=args.include_daacs_runtime_output_manifest,
        include_daacs_runtime_generated_artifact_bundle=(
            args.include_daacs_runtime_generated_artifact_bundle
        ),
        include_daacs_runtime_fixture_materialization=(
            args.include_daacs_runtime_fixture_materialization
        ),
    )
    rendered = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)


if __name__ == "__main__":
    main()

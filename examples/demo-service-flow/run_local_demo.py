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
    ProviderEnvelopeRepositoryConfig,
    provider_precheck_operator_policy_summary,
)
from packages.core.live_open_policy import LIVE_OPEN_REQUIRED_CONTROLS
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash


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


def _client(store_root: Path, *, include_provider_precheck: bool = False) -> TestClient:
    provider_envelope_config = (
        ProviderEnvelopeRepositoryConfig(root=store_root / "provider-envelope-evidence")
        if include_provider_precheck
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


def _artifact_kinds(artifacts: list[dict[str, Any]]) -> set[str]:
    return {str(artifact.get("kind") or "") for artifact in artifacts}


def _checks(
    create_data: dict[str, Any],
    run_data: dict[str, Any],
    *,
    provider_envelope_data: dict[str, Any] | None = None,
) -> dict[str, bool]:
    artifact_kinds = _artifact_kinds(run_data.get("artifacts", []))
    evidence_summary = run_data.get("evidence_summary", {})
    evidence_counts = evidence_summary.get("counts", {})
    execution_boundary = run_data.get("execution_boundary", {})
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
    return checks


def run_demo(
    store_root: str | Path | None = None,
    *,
    include_provider_precheck: bool = False,
) -> dict[str, Any]:
    selected_root = Path(store_root) if store_root else Path(__file__).resolve().parent / ".local"
    selected_root.mkdir(parents=True, exist_ok=True)
    client = _client(selected_root, include_provider_precheck=include_provider_precheck)

    create_data = _post_run(client)
    run_id = str(create_data["run"]["run_id"])
    run_data = _get_data(client, f"/api/v1/runs/{run_id}")
    artifact_data = _get_data(client, f"/api/v1/runs/{run_id}/artifacts")
    provider_envelope_data = None
    provider_envelope_read_data = None
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

    checks = _checks(create_data, run_data, provider_envelope_data=provider_envelope_data)
    artifact_kinds = sorted(_artifact_kinds(run_data.get("artifacts", [])))
    evidence_summary = run_data.get("evidence_summary", {})
    summary = {
        "demo_id": "AW-DEMO-01",
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
    args = parser.parse_args()

    summary = run_demo(args.store_root, include_provider_precheck=args.include_provider_precheck)
    rendered = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)


if __name__ == "__main__":
    main()

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
from packages.core.public_projection import assert_public_projection_safe


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


def _client(store_root: Path) -> TestClient:
    return TestClient(
        create_app(
            run_repository_config=RunArtifactRepositoryConfig(
                root=store_root / "canonical-run-artifacts",
            ),
            evidence_repository_config=EvidenceRepositoryConfig(
                root=store_root / "runner-report-audit-evidence",
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


def _artifact_kinds(artifacts: list[dict[str, Any]]) -> set[str]:
    return {str(artifact.get("kind") or "") for artifact in artifacts}


def _checks(create_data: dict[str, Any], run_data: dict[str, Any]) -> dict[str, bool]:
    artifact_kinds = _artifact_kinds(run_data.get("artifacts", []))
    evidence_summary = run_data.get("evidence_summary", {})
    evidence_counts = evidence_summary.get("counts", {})
    execution_boundary = run_data.get("execution_boundary", {})
    return {
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


def run_demo(store_root: str | Path | None = None) -> dict[str, Any]:
    selected_root = Path(store_root) if store_root else Path(__file__).resolve().parent / ".local"
    selected_root.mkdir(parents=True, exist_ok=True)
    client = _client(selected_root)

    create_data = _post_run(client)
    run_id = str(create_data["run"]["run_id"])
    run_data = _get_data(client, f"/api/v1/runs/{run_id}")
    artifact_data = _get_data(client, f"/api/v1/runs/{run_id}/artifacts")

    checks = _checks(create_data, run_data)
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
    args = parser.parse_args()

    summary = run_demo(args.store_root)
    rendered = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)


if __name__ == "__main__":
    main()

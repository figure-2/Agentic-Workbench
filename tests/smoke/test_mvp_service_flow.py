import importlib.util
import json
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.agentic_workbench_api.main import create_app
from apps.api.agentic_workbench_api.services.evidence_read_model import (
    EvidenceRepositoryConfig,
)


DEMO_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "demo-service-flow"
    / "run_local_demo.py"
)


def _load_demo_module():
    spec = importlib.util.spec_from_file_location("aw_mvp_01_service_flow", DEMO_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_mvp_service_flow_covers_idea_to_verification_without_live_calls(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(tmp_path / "mvp-store")

    stage_coverage = summary["workflow_stage_coverage"]
    verification = summary["verification_read_model"]
    metrics = summary["mvp_metrics"]
    checks = summary["checks"]

    assert summary["mvp_id"] == "AW-MVP-01"
    assert summary["status"] == "passed"
    assert stage_coverage["required_stage_count"] == 7
    assert stage_coverage["covered_stage_count"] == 7
    assert stage_coverage["coverage_percent"] == 100.0
    assert stage_coverage["stage_order"] == [
        "Idea",
        "PlanningBlueprint",
        "PRDPackage",
        "ImplementationBrief",
        "Approval",
        "RunnerPlan",
        "VerificationReport",
    ]
    assert all(stage["covered"] for stage in stage_coverage["stages"])
    assert verification["projection_version"] == "verification-read-model-public-v1"
    assert verification["status"] == "passed"
    assert verification["counts"]["runner_plan_count"] == 1
    assert verification["counts"]["verification_report_count"] == 1
    assert verification["counts"]["failed_report_count"] == 0
    assert verification["counts"]["check_count"] >= 1
    assert verification["runner_plan_hash_count"] == 1
    assert verification["repository_boundary"]["raw_row_returned"] is False
    assert verification["execution_boundary"]["solar_provider_calls"] == 0
    assert verification["execution_boundary"]["target_runtime_calls"] == 0
    assert checks["mvp_stage_coverage_7_of_7"] is True
    assert checks["mvp_artifact_linkage_100_percent"] is True
    assert checks["verification_read_model"] is True
    assert checks["verification_read_model_report"] is True
    assert metrics["golden_path_scenario_count"] == 1
    assert metrics["stage_coverage"] == "7/7"
    assert metrics["stage_coverage_percent"] == 100.0
    assert metrics["artifact_linkage_by_run_id_percent"] == 100
    assert metrics["raw_exposure_findings"] == 0
    assert metrics["live_provider_calls"] == 0
    assert metrics["daacs_target_runtime_calls"] == 0
    assert metrics["public_claim_drift_findings"] == 0

    serialized = _serialized(summary)
    for forbidden in (
        "raw_prompt",
        "raw_log",
        "Build a small task collaboration app",
        "provider_payload",
        "runtime_payload",
        "file_body",
        "signature_id",
        "signed_contract_hash",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_mvp_verification_read_api_blocks_when_evidence_store_is_unavailable(tmp_path):
    bad_root = tmp_path / "not-a-directory"
    bad_root.write_text("occupied", encoding="utf-8")
    app = create_app(evidence_repository_config=EvidenceRepositoryConfig(root=bad_root))
    client = TestClient(app)

    response = client.get("/api/v1/runs/run-closed/verification")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["projection_version"] == "verification-read-model-public-v1"
    assert data["status"] == "blocked"
    assert data["repository_boundary"]["raw_row_returned"] is False
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["claim_boundary"]["local_read_model_only"] is True
    assert data["claim_boundary"]["external_provider_outcome"] is False
    assert str(tmp_path) not in _serialized(data)

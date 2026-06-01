import importlib.util
import json
from pathlib import Path


DEMO_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "demo-service-flow"
    / "run_local_demo.py"
)


def _load_demo_module():
    spec = importlib.util.spec_from_file_location("aw_demo_01_local_service_flow", DEMO_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_local_service_demo_proves_composed_run_flow_without_live_calls(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(tmp_path / "demo-store")

    serialized = _serialized(summary)
    checks = summary["checks"]

    assert summary["demo_id"] == "AW-DEMO-01"
    assert summary["status"] == "passed"
    assert summary["projection_version"] == "canonical-run-composed-read-model-public-v1"
    assert summary["runtime_mode"] == "read_model"
    assert summary["fixture_mode"] is False
    assert summary["artifact_count"] >= 3
    assert checks["created_run"] is True
    assert checks["canonical_persisted"] is True
    assert checks["evidence_persisted"] is True
    assert checks["composed_read_model"] is True
    assert summary["identity_signals"]["div"]["planning_blueprint_artifact"] is True
    assert summary["identity_signals"]["div"]["prd_package_artifact"] is True
    assert summary["identity_signals"]["div"]["evidence_summary_present"] is True
    assert summary["identity_signals"]["daacs"]["build_spec_artifact"] is True
    assert summary["identity_signals"]["daacs"]["implementation_brief_artifact"] is True
    assert summary["identity_signals"]["daacs"]["runner_plan_evidence"] is True
    assert summary["identity_signals"]["daacs"]["verification_report_evidence"] is True
    assert summary["evidence_summary"]["counts"]["runner_plan_count"] == 1
    assert summary["evidence_summary"]["counts"]["verification_report_count"] == 1
    assert summary["evidence_summary"]["counts"]["audit_event_count"] >= 1
    assert summary["repository_boundary"]["canonical_run_artifact_backend"] == "sqlite"
    assert summary["repository_boundary"]["runner_report_audit_backend"] == "sqlite"
    assert summary["repository_boundary"]["evidence_db_queried"] is True
    assert summary["execution_boundary"]["solar_provider_calls"] == 0
    assert summary["execution_boundary"]["target_runtime_calls"] == 0

    for forbidden in (
        "raw_prompt",
        "Build a small task collaboration app",
        "provider_payload",
        "runtime_payload",
        "file_body",
        "signature_id",
        "signed_contract_hash",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_local_service_demo_structural_counts_are_repeatable_with_fresh_stores(tmp_path):
    module = _load_demo_module()

    first = module.run_demo(tmp_path / "first-store")
    second = module.run_demo(tmp_path / "second-store")

    assert first["status"] == "passed"
    assert second["status"] == "passed"
    assert first["artifact_count"] == second["artifact_count"]
    assert first["artifact_kinds"] == second["artifact_kinds"]
    assert first["counts"]["runner_plan_count"] == second["counts"]["runner_plan_count"]
    assert (
        first["counts"]["verification_report_count"]
        == second["counts"]["verification_report_count"]
    )
    assert first["execution_boundary"]["solar_provider_calls"] == 0
    assert second["execution_boundary"]["solar_provider_calls"] == 0


def test_local_service_demo_can_include_provider_envelope_precheck_without_calls(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "demo-store",
        include_provider_precheck=True,
    )

    serialized = _serialized(summary)
    checks = summary["checks"]
    envelope = summary["provider_envelope_admission"]

    assert summary["status"] == "passed"
    assert envelope["status"] == "blocked"
    assert envelope["admission_status"] == "admitted"
    assert envelope["adapter_reached"] is True
    assert envelope["counts"]["provider_envelope_count"] == 1
    assert envelope["operator_approval_status"] == "approved"
    assert envelope["operator_policy_summary_hash"]
    assert envelope["read_model_status"] == "available"
    assert checks["provider_envelope_precheck_recorded"] is True
    assert checks["provider_envelope_adapter_reached_disabled_path"] is True
    assert checks["provider_envelope_calls_zero"] is True
    assert envelope["execution_boundary"]["provider_calls"] == 0
    assert envelope["execution_boundary"]["network_calls"] == 0
    assert envelope["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "raw_prompt",
        "provider_payload",
        "provider_body",
        "signature_id",
        "signed_contract_hash",
        "approved_policy_summary_hash",
        "sig-",
        "nonce-",
        str(tmp_path),
    ):
        assert forbidden not in serialized

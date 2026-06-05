import importlib.util
import json
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.agentic_workbench_api.main import create_app
from packages.core.live_open_policy import LIVE_OPEN_REQUIRED_CONTROLS
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.div_planner.provider_boundary import (
    PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
    PLANNER_PROVIDER_MODE_SOLAR_SPIKE_PREFLIGHT,
)
from packages.div_planner.solar_live_spike import (
    SolarPlannerHTTPResponse,
    SolarPlannerLiveSpikeRequest,
    run_solar_planner_live_spike,
)
from packages.div_planner.solar_quality_comparison import (
    SolarPlannerQualityComparisonRequest,
    compare_solar_planner_quality,
)


DEMO_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "demo-service-flow"
    / "run_local_demo.py"
)


def _load_demo_module():
    spec = importlib.util.spec_from_file_location("aw_solar_01_service_flow", DEMO_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prompt_contract_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "solar planner preflight smoke",
            "prompt": "hash-only",
        }
    )


def _projected_solar_live_spike(run_id: str = "run-solar-quality-api") -> dict:
    def runner(**kwargs):
        return SolarPlannerHTTPResponse(
            status_code=200,
            body=json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "planning_blueprint": "workflow",
                                        "prd_package": "requirements",
                                        "implementation_brief": "build plan",
                                        "acceptance_criteria": "checks",
                                    }
                                )
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )

    return run_solar_planner_live_spike(
        SolarPlannerLiveSpikeRequest(
            run_id=run_id,
            prompt_contract_hash=_prompt_contract_hash(),
            operator_live_opt_in=True,
            request_timeout_seconds=20,
            max_input_chars=1800,
            max_output_tokens=384,
            max_live_api_calls=1,
            cost_limit_label="one-shot-bounded",
        ),
        credential_reader=lambda _: "up_test_key",
        live_runner=runner,
    ).to_dict()


def _reviewer_approval_hash(run_id: str = "run-solar-draft-api") -> str:
    return stable_contract_hash(
        {
            "run_id": run_id,
            "decision": "review_solar_quality_comparison_only",
            "artifact_binding": "draft_candidate_only",
        }
    )


def _review_ready_quality_projection(run_id: str = "run-solar-draft-api") -> dict:
    return compare_solar_planner_quality(
        SolarPlannerQualityComparisonRequest(
            run_id=run_id,
            prompt_contract_hash=_prompt_contract_hash(),
            fixture_required_stage_count=7,
            fixture_covered_stage_count=7,
            fixture_artifact_count=6,
            solar_live_spike_projection=_projected_solar_live_spike(run_id),
            reviewer_approval_hash=_reviewer_approval_hash(run_id),
        )
    ).to_dict()


def _ready_policy() -> dict:
    readiness = {field_name: True for field_name in LIVE_OPEN_REQUIRED_CONTROLS}
    return {
        **readiness,
        "request_timeout_seconds": 30,
        "max_cost_units": 1,
        "max_output_tokens": 512,
        "max_live_api_calls": 1,
        "retry_count": 0,
    }


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_planner_provider_preflight_api_is_no_call_and_public_safe():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/planner/provider/preflight",
        json={
            "run_id": "run-solar-planner-api",
            "prompt_contract_hash": _prompt_contract_hash(),
            "planner_provider_mode": PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
            "stage_target": "PlanningBlueprint",
            "env_key_name": "UPSTAGE_API_KEY",
            "policy": _ready_policy(),
            "raw_prompt": "SOLAR_PLANNER_API_RAW_PROMPT_SENTINEL",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    serialized = _serialized(data)

    assert data["projection_version"] == "planner-provider-preflight-public-v1"
    assert data["status"] == "preflight_only"
    assert data["reason"] == "provider_call_disabled_by_design"
    assert data["planner_provider_mode"] == PLANNER_PROVIDER_MODE_SOLAR_DISABLED
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert data["execution_boundary"]["env_key_value_reads"] == 0
    assert data["execution_boundary"]["sdk_imports"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["counts"]["planner_provider_success_count"] == 0
    assert "SOLAR_PLANNER_API_RAW_PROMPT_SENTINEL" not in serialized
    assert "raw_prompt" not in serialized
    assert_public_projection_safe(data)


def test_local_service_demo_can_compare_fixture_and_disabled_solar_planner(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "solar-planner-store",
        include_solar_planner_preflight=True,
    )
    serialized = _serialized(summary)
    comparison = summary["solar_planner_comparison"]
    preflight = summary["solar_planner_preflight"]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert comparison["comparison_variant_count"] == 2
    assert comparison["fixture_stage_coverage"] == "7/7"
    assert comparison["solar_preflight_status"] == "preflight_only"
    assert comparison["solar_preflight_provider_calls"] == 0
    assert comparison["solar_preflight_sdk_imports"] == 0
    assert comparison["solar_preflight_env_value_reads"] == 0
    assert comparison["solar_preflight_network_calls"] == 0
    assert comparison["raw_exposure_findings"] == 0
    assert comparison["public_claim_drift_findings"] == 0
    assert preflight["status"] == "preflight_only"
    assert preflight["counts"]["planner_provider_success_count"] == 0
    assert preflight["claim_boundary"]["external_provider_outcome"] is False
    assert checks["solar_planner_preflight_projection"] is True
    assert checks["solar_planner_preflight_only"] is True
    assert checks["solar_planner_preflight_provider_calls_zero"] is True
    assert checks["solar_planner_preflight_env_and_sdk_zero"] is True
    assert checks["solar_planner_preflight_no_provider_success"] is True

    for forbidden in (
        "raw_prompt",
        "Build a small task collaboration app",
        "provider_payload",
        "runtime_payload",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(summary)


def test_solar_spike_mock_response_api_is_no_call_and_public_safe():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/planner/provider/solar-spike/mock-response",
        json={
            "run_id": "run-solar-spike-api",
            "prompt_contract_hash": _prompt_contract_hash(),
            "planner_provider_mode": PLANNER_PROVIDER_MODE_SOLAR_SPIKE_PREFLIGHT,
            "stage_target": "PlanningBlueprint",
            "env_key_name": "UPSTAGE_API_KEY",
            "policy": _ready_policy(),
            "response_summary": "Mocked Solar planner expansion.",
            "summary_section_count": 4,
            "raw_response_body": "RAW_SOLAR_SPIKE_RESPONSE_SENTINEL",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    serialized = _serialized(data)

    assert data["projection_version"] == "planner-provider-spike-response-public-v1"
    assert data["status"] == "mock_projected"
    assert data["reason"] == "mock_solar_planner_response_projected"
    assert data["planner_provider_mode"] == PLANNER_PROVIDER_MODE_SOLAR_SPIKE_PREFLIGHT
    assert len(data["planning_request_hash"]) == 64
    assert len(data["response_projection"]["response_contract_hash"]) == 64
    assert data["response_projection"]["summary_section_count"] == 4
    assert data["response_projection"]["provider_body_included"] is False
    assert data["counts"]["mock_response_projection_count"] == 1
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["env_key_value_reads"] == 0
    assert data["execution_boundary"]["sdk_imports"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert "RAW_SOLAR_SPIKE_RESPONSE_SENTINEL" not in serialized
    assert "raw_response_body" not in serialized
    assert_public_projection_safe(data)


def test_solar_live_spike_api_blocks_without_operator_opt_in():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/planner/provider/solar-live/spike",
        json={
            "run_id": "run-solar-live-api",
            "prompt_contract_hash": _prompt_contract_hash(),
            "operator_live_opt_in": False,
            "env_key_name": "UPSTAGE_API_KEY",
            "model": "solar-pro3",
            "request_timeout_seconds": 20,
            "max_input_chars": 1800,
            "max_output_tokens": 384,
            "max_live_api_calls": 1,
            "cost_limit_label": "one-shot-bounded",
            "raw_prompt": "SOLAR_LIVE_API_RAW_PROMPT_SENTINEL",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    serialized = _serialized(data)

    assert data["projection_version"] == "planner-provider-solar-live-spike-public-v1"
    assert data["status"] == "blocked"
    assert data["reason"] == "operator_live_opt_in_missing"
    assert data["counts"]["provider_call_count"] == 0
    assert data["counts"]["env_value_read_count"] == 0
    assert data["counts"]["credential_value_exposure_count"] == 0
    assert data["counts"]["input_text_exposure_count"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert "SOLAR_LIVE_API_RAW_PROMPT_SENTINEL" not in serialized
    assert "raw_prompt" not in serialized
    assert_public_projection_safe(data)


def test_local_service_demo_can_include_solar_spike_mock_projection(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "solar-spike-store",
        include_solar_planner_spike=True,
    )
    serialized = _serialized(summary)
    spike = summary["solar_planner_spike"]
    comparison = summary["solar_planner_spike_comparison"]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert comparison["comparison_variant_count"] == 3
    assert comparison["fixture_stage_coverage"] == "7/7"
    assert comparison["solar_spike_status"] == "mock_projected"
    assert comparison["solar_spike_mock_projection_count"] == 1
    assert comparison["solar_spike_provider_calls"] == 0
    assert comparison["solar_spike_sdk_imports"] == 0
    assert comparison["solar_spike_env_value_reads"] == 0
    assert comparison["solar_spike_network_calls"] == 0
    assert spike["status"] == "mock_projected"
    assert len(spike["planning_request_hash"]) == 64
    assert len(spike["response_projection"]["response_contract_hash"]) == 64
    assert checks["solar_planner_spike_projection"] is True
    assert checks["solar_planner_spike_mock_projected"] is True
    assert checks["solar_planner_spike_no_call"] is True
    assert checks["solar_planner_spike_hash_only"] is True

    for forbidden in (
        "raw_prompt",
        "Build a small task collaboration app",
        "provider_payload",
        "runtime_payload",
        "RAW_SOLAR",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(summary)


def test_local_service_demo_can_include_blocked_solar_live_spike(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "solar-live-spike-store",
        include_solar_planner_live_spike=True,
        allow_solar_planner_live_call=False,
    )
    serialized = _serialized(summary)
    live_spike = summary["solar_planner_live_spike"]
    comparison = summary["solar_planner_live_spike_comparison"]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert live_spike["status"] == "blocked"
    assert live_spike["reason"] == "operator_live_opt_in_missing"
    assert comparison["comparison_variant_count"] == 4
    assert comparison["solar_live_spike_provider_calls"] == 0
    assert comparison["solar_live_spike_env_value_reads"] == 0
    assert comparison["solar_live_spike_network_calls"] == 0
    assert checks["solar_planner_live_spike_projection"] is True
    assert checks["solar_planner_live_spike_observed"] is True
    assert checks["solar_planner_live_spike_one_call_or_blocked"] is True
    assert checks["solar_planner_live_spike_public_safe"] is True

    for forbidden in (
        "raw_prompt",
        "Build a small task collaboration app",
        "provider_payload",
        "runtime_payload",
        "UPSTAGE_API_KEY=",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(summary)


def test_solar_quality_comparison_api_blocks_artifact_binding_without_review():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/planner/provider/solar-quality/comparison",
        json={
            "run_id": "run-solar-quality-api",
            "prompt_contract_hash": _prompt_contract_hash(),
            "fixture_required_stage_count": 7,
            "fixture_covered_stage_count": 7,
            "fixture_artifact_count": 6,
            "solar_live_spike_projection": _projected_solar_live_spike(),
            "raw_provider_body": "SOLAR_QUALITY_RAW_BODY_SENTINEL",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    serialized = _serialized(data)

    assert data["projection_version"] == "solar-planner-quality-comparison-public-v1"
    assert data["status"] == "review_blocked"
    assert data["reason"] == "reviewer_approval_missing"
    assert data["fixture_summary"]["stage_coverage"] == "7/7"
    assert data["solar_summary"]["summary_section_count"] == 4
    assert data["solar_summary"]["missing_required_stage_count"] == 0
    assert data["review_gate"]["status"] == "blocked"
    assert data["review_gate"]["artifact_binding_permission"] is False
    assert data["counts"]["additional_live_call_count"] == 0
    assert data["counts"]["raw_provider_body_returned_count"] == 0
    assert data["execution_boundary"]["comparison_provider_calls"] == 0
    assert data["execution_boundary"]["observed_solar_provider_calls"] == 1
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert "SOLAR_QUALITY_RAW_BODY_SENTINEL" not in serialized
    assert data["solar_summary"]["provider_body_included"] is False
    assert "up_test_key" not in serialized
    assert_public_projection_safe(data)


def test_local_service_demo_can_include_solar_quality_comparison_without_live_call(
    tmp_path,
):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "solar-quality-store",
        include_solar_planner_quality_comparison=True,
    )
    serialized = _serialized(summary)
    quality = summary["solar_planner_quality_comparison"]
    quality_summary = summary["solar_planner_quality_summary"]
    live_spike = summary["solar_planner_live_spike"]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert live_spike["status"] == "blocked"
    assert quality["projection_version"] == "solar-planner-quality-comparison-public-v1"
    assert quality["status"] == "review_blocked"
    assert quality["review_gate"]["artifact_binding_permission"] is False
    assert quality_summary["fixture_stage_coverage"] == "7/7"
    assert quality_summary["additional_live_call_count"] == 0
    assert quality_summary["comparison_provider_calls"] == 0
    assert quality_summary["comparison_env_value_reads"] == 0
    assert quality_summary["comparison_network_calls"] == 0
    assert quality_summary["target_runtime_calls"] == 0
    assert checks["solar_planner_quality_comparison_projection"] is True
    assert checks["solar_planner_quality_comparison_stage_coverage"] is True
    assert checks["solar_planner_quality_comparison_review_gate"] is True
    assert checks["solar_planner_quality_comparison_no_extra_live_call"] is True
    assert checks["solar_planner_quality_comparison_public_safe"] is True

    for forbidden in (
        "raw_prompt",
        "Build a small task collaboration app",
        "provider_payload",
        "runtime_payload",
        "UPSTAGE_API_KEY=",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(summary)


def test_solar_draft_projection_api_projects_reviewer_bound_drafts():
    client = TestClient(create_app())
    quality = _review_ready_quality_projection()

    response = client.post(
        "/api/v1/planner/provider/solar-draft/projection",
        json={
            "run_id": "run-solar-draft-api",
            "prompt_contract_hash": _prompt_contract_hash(),
            "solar_quality_comparison_hash": quality["comparison_hash"],
            "solar_quality_comparison_projection": quality,
            "reviewer_approval_hash": _reviewer_approval_hash(),
            "raw_provider_body": "SOLAR_DRAFT_RAW_BODY_SENTINEL",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    serialized = _serialized(data)

    assert data["projection_version"] == "solar-planner-draft-projection-public-v1"
    assert data["status"] == "draft_projected"
    assert data["counts"]["draft_artifact_projection_count"] == 2
    assert data["counts"]["draft_planning_blueprint_projection_count"] == 1
    assert data["counts"]["draft_prd_package_projection_count"] == 1
    assert data["counts"]["canonical_artifact_write_count"] == 0
    assert data["counts"]["additional_live_call_count"] == 0
    assert data["execution_boundary"]["draft_projection_provider_calls"] == 0
    assert data["execution_boundary"]["draft_projection_env_key_value_reads"] == 0
    assert data["execution_boundary"]["draft_projection_network_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["review_gate"]["canonical_artifact_write_performed"] is False
    assert {artifact["artifact_label"] for artifact in data["draft_artifacts"]} == {
        "PlanningBlueprint",
        "PRDPackage",
    }
    assert "SOLAR_DRAFT_RAW_BODY_SENTINEL" not in serialized
    assert data["counts"]["raw_provider_body_stored_count"] == 0
    assert data["counts"]["raw_provider_body_returned_count"] == 0
    assert "up_test_key" not in serialized
    assert_public_projection_safe(data)


def test_local_service_demo_can_include_blocked_solar_draft_projection_without_live_call(
    tmp_path,
):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "solar-draft-store",
        include_solar_planner_draft_projection=True,
    )
    serialized = _serialized(summary)
    draft = summary["solar_planner_draft_projection"]
    draft_summary = summary["solar_planner_draft_summary"]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert draft["projection_version"] == "solar-planner-draft-projection-public-v1"
    assert draft["status"] == "blocked"
    assert draft_summary["fixture_stage_coverage"] == "7/7"
    assert draft_summary["draft_artifact_projection_count"] == 0
    assert draft_summary["canonical_artifact_write_count"] == 0
    assert draft_summary["additional_live_call_count"] == 0
    assert draft_summary["draft_projection_provider_calls"] == 0
    assert draft_summary["draft_projection_env_value_reads"] == 0
    assert draft_summary["draft_projection_network_calls"] == 0
    assert draft_summary["target_runtime_calls"] == 0
    assert checks["solar_planner_draft_projection_projection"] is True
    assert checks["solar_planner_draft_projection_status"] is True
    assert checks["solar_planner_draft_projection_artifacts"] is True
    assert checks["solar_planner_draft_projection_canonical_closed"] is True
    assert checks["solar_planner_draft_projection_no_extra_live_call"] is True
    assert checks["solar_planner_draft_projection_public_safe"] is True

    for forbidden in (
        "raw_prompt",
        "Build a small task collaboration app",
        "provider_payload",
        "runtime_payload",
        "UPSTAGE_API_KEY=",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(summary)

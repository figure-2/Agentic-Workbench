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

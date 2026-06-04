import importlib.util
import json
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.agentic_workbench_api.main import create_app
from packages.core.live_open_policy import LIVE_OPEN_REQUIRED_CONTROLS
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.div_planner.provider_boundary import PLANNER_PROVIDER_MODE_SOLAR_DISABLED


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

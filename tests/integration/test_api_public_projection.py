import json

from fastapi.testclient import TestClient

from apps.api.agentic_workbench_api.main import create_app


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


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
    assert payload["events"]
    assert "raw_prompt" not in serialized
    assert "API_RAW_PROMPT_SENTINEL" not in serialized
    assert "API_CONSTRAINT_SENTINEL" not in serialized
    assert "finance-owner@example.com" not in serialized
    assert "API_KEY=secret-value" not in serialized
    assert "provider_payload" not in serialized
    assert "approval_authorization_material" not in serialized

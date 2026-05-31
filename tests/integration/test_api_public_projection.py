import json
from dataclasses import asdict

from fastapi.testclient import TestClient

from apps.api.agentic_workbench_api.main import create_app
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.adapters import (
    build_spec_to_daacs_initial_state,
    create_spec_approval,
    implementation_brief_from_prd_package,
    planning_to_build_spec,
)
from packages.daacs_builder.approval_security import sign_approval_for_tests
from packages.daacs_builder.live_runner import live_replay_scope_for_request
from packages.daacs_builder.provider_boundary import (
    ProviderApprovalRecord,
    ProviderRequest,
    provider_replay_scope_for_request,
)
from packages.daacs_builder.runner_provider import (
    ApprovalRecord,
    RunnerPolicy,
    RunnerRequest,
    default_runner_provider_registry,
)
from packages.div_planner.adapters import planning_blueprint_from_div_state, planning_to_prd_package


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _prompt_contract_hash() -> str:
    return stable_contract_hash({"purpose": "api provider admission demo"})


def _provider_admission_payload() -> dict:
    approval = ProviderApprovalRecord(
        approved_by="local-user",
        approved_at="2026-05-31T00:00:00Z",
        run_id="run-api-provider",
        provider_name="solar-pro-3",
        model_name="solar-pro-3",
        mode="fake",
        env_key_name="UPSTAGE_API_KEY",
        max_live_api_calls=0,
        max_live_llm_calls=0,
        expires_at="2099-01-01T00:00:00Z",
        audit_log_id="audit-api-provider",
    )
    request = ProviderRequest(
        run_id="run-api-provider",
        prompt_contract_hash=_prompt_contract_hash(),
        approval=approval,
    )
    sign_approval_for_tests(
        approval,
        scope=provider_replay_scope_for_request(request),
        signature_id="sig-api-provider-admission",
        nonce="nonce-api-provider-admission",
    )
    return {
        "run_id": request.run_id,
        "prompt_contract_hash": request.prompt_contract_hash,
        "approval_lifecycle": "durable",
        "approval": asdict(approval),
    }


def _live_admission_payload() -> dict:
    run_id = "run-api-live"
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {
                "toc": ["Agentic Workbench API"],
                "rationale": "Need API wiring for fake live admission.",
                "blueprint": [
                    {"title": "API Gate", "guideline": "persist approval before replay"},
                    {"title": "Fake Runtime", "guideline": "keep target calls at zero"},
                ],
            }
        }
    )
    spec = planning_to_build_spec(blueprint)
    prd_package = planning_to_prd_package(blueprint, build_spec=spec)
    brief = implementation_brief_from_prd_package(prd_package, spec)
    spec_approval = create_spec_approval(
        brief,
        approval_id="approval-api-live-brief",
        approved=True,
    )
    state = build_spec_to_daacs_initial_state(
        spec,
        run_id=run_id,
        implementation_brief=brief,
        approval=spec_approval,
        require_approval=True,
    )
    dry_run = default_runner_provider_registry().run(
        RunnerRequest(
            run_id=run_id,
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=spec_approval,
        )
    )
    assert dry_run.plan is not None
    approval = ApprovalRecord(
        approved_by="local-user",
        approved_at="2026-05-31T00:00:00Z",
        run_id=run_id,
        mode="live",
        allowed_operations=["fake_runtime"],
        max_provider_calls=0,
        max_subprocess_calls=0,
        max_package_installs=0,
        max_server_starts=0,
        max_files_written=0,
        workspace_root=f"runs/{run_id}",
        expires_at="2099-01-01T00:00:00Z",
        rollback_plan_id="rollback-api-live",
        audit_log_id="audit-api-live",
    )
    policy = RunnerPolicy(workspace_root=f"runs/{run_id}")
    request = RunnerRequest(
        run_id=run_id,
        mode="live",
        state=state,
        approval=approval,
        plan=dry_run.plan,
        policy=policy,
    )
    sign_approval_for_tests(
        approval,
        scope=live_replay_scope_for_request(request),
        signature_id="sig-api-live-admission",
        nonce="nonce-api-live-admission",
    )
    return {
        "run_id": run_id,
        "approval_lifecycle": "durable",
        "state": state,
        "plan": dry_run.plan.to_dict(),
        "policy": asdict(policy),
        "approval": asdict(approval),
    }


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


def test_provider_fake_admission_api_uses_canonical_persistence_without_raw_auth_material():
    client = TestClient(create_app())
    request_payload = _provider_admission_payload()

    response = client.post("/api/v1/admissions/provider/fake", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]

    assert data["projection_version"] == "approval-admission-public-v1"
    assert data["admission_kind"] == "provider"
    assert data["runtime_mode"] == "fake"
    assert data["approval_lifecycle"] == "durable"
    assert data["fixture_mode"] is False
    assert data["synthetic_approval"] is False
    assert data["approval_persistence"]["service_used"] is True
    assert data["approval_persistence"]["approval_row_present"] is True
    assert data["approval_persistence"]["hash_match"] is True
    assert data["execution_boundary"]["fake_provider_invocations"] == 1
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["live_llm_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert request_payload["approval"]["nonce"] not in serialized
    assert request_payload["approval"]["signature_id"] not in serialized
    assert request_payload["approval"]["signed_contract_hash"] not in serialized
    assert "nonce" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_live_fake_admission_api_uses_canonical_persistence_without_target_runtime_calls():
    client = TestClient(create_app())
    request_payload = _live_admission_payload()

    response = client.post("/api/v1/admissions/live/fake", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]

    assert data["projection_version"] == "approval-admission-public-v1"
    assert data["admission_kind"] == "live_runner"
    assert data["runtime_mode"] == "fake"
    assert data["approval_lifecycle"] == "durable"
    assert data["fixture_mode"] is False
    assert data["synthetic_approval"] is False
    assert data["approval_persistence"]["service_used"] is True
    assert data["approval_persistence"]["approval_row_present"] is True
    assert data["approval_persistence"]["hash_match"] is True
    assert data["execution_boundary"]["fake_live_runtime_invocations"] == 1
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert request_payload["approval"]["nonce"] not in serialized
    assert request_payload["approval"]["signature_id"] not in serialized
    assert request_payload["approval"]["signed_contract_hash"] not in serialized
    assert "nonce" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_fake_admission_api_rejects_fixture_or_synthetic_approval_path_without_raw_echo():
    client = TestClient(create_app())
    payload = _provider_admission_payload()
    payload["approval_lifecycle"] = "synthetic"
    payload["fixture_mode"] = True

    response = client.post("/api/v1/admissions/provider/fake", json=payload)
    serialized = _serialized(response.json())

    assert response.status_code == 409
    assert "durable" in serialized or "fixture approval path" in serialized
    assert payload["approval"]["nonce"] not in serialized
    assert payload["approval"]["signature_id"] not in serialized
    assert payload["approval"]["signed_contract_hash"] not in serialized

import json
from dataclasses import asdict

from fastapi.testclient import TestClient

from apps.api.agentic_workbench_api.main import create_app
from apps.api.agentic_workbench_api.services.canonical_run_store import RunArtifactRepositoryConfig
from apps.api.agentic_workbench_api.services.evidence_read_model import EvidenceRepositoryConfig
from apps.api.agentic_workbench_api.services.provider_envelope_api import (
    MANUAL_PROVIDER_TEST_EXECUTOR_VERSION,
    ProviderEnvelopeRepositoryConfig,
    provider_manual_test_preflight_summary,
    provider_manual_test_proposal_summary,
    provider_precheck_operator_policy_summary,
)
from packages.core.approval_replay_factory import ApprovalReplayRepositoryConfig
from packages.core.live_open_policy import LIVE_OPEN_REQUIRED_CONTROLS
from packages.core.repositories import (
    ArtifactRecord,
    audit_event_record_from_event,
    runner_plan_record_from_plan,
    verification_report_record_from_report,
)
from packages.core.schemas import VerificationReport, stable_contract_hash
from packages.core.sqlite_repositories import SQLiteRunnerReportAuditStore
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
    RunnerPlan,
    RunnerPolicy,
    RunnerRequest,
    default_runner_provider_registry,
)
from packages.div_planner.adapters import planning_blueprint_from_div_state, planning_to_prd_package


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _prompt_contract_hash() -> str:
    return stable_contract_hash({"purpose": "api provider admission demo"})


def _provider_admission_payload(
    *,
    run_id: str = "run-api-provider",
    signature_id: str = "sig-api-provider-admission",
    nonce: str = "nonce-api-provider-admission",
) -> dict:
    approval = ProviderApprovalRecord(
        approved_by="local-user",
        approved_at="2026-05-31T00:00:00Z",
        run_id=run_id,
        provider_name="solar-pro-3",
        model_name="solar-pro-3",
        mode="fake",
        env_key_name="UPSTAGE_API_KEY",
        max_live_api_calls=0,
        max_live_llm_calls=0,
        expires_at="2099-01-01T00:00:00Z",
        audit_log_id=f"audit-{run_id}",
    )
    request = ProviderRequest(
        run_id=run_id,
        prompt_contract_hash=_prompt_contract_hash(),
        approval=approval,
    )
    sign_approval_for_tests(
        approval,
        scope=provider_replay_scope_for_request(request),
        signature_id=signature_id,
        nonce=nonce,
    )
    return {
        "run_id": request.run_id,
        "prompt_contract_hash": request.prompt_contract_hash,
        "approval_lifecycle": "durable",
        "approval": asdict(approval),
    }


def _provider_envelope_precheck_payload(
    *,
    run_id: str = "run-api-envelope",
    prompt_contract_hash: str | None = None,
    include_operator_approval: bool = True,
    approved_policy_summary_hash: str | None = None,
    include_manual_test_proposal: bool = False,
    include_manual_test_operator_approval: bool = True,
    manual_test_executor_enable: bool = False,
    include_one_shot_live_permission: bool = False,
    include_readiness_decision: bool = False,
    readiness_decision: str = "approve",
    readiness_preflight_hash_override: str | None = None,
) -> dict:
    payload = {
        "run_id": run_id,
        "prompt_contract_hash": prompt_contract_hash or _prompt_contract_hash(),
        "runtime_mode": "live_admission_precheck",
        "response_summary": "API05 sanitized provider envelope precheck summary",
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
                {
                    "run_id": run_id,
                    "purpose": "api provider envelope precheck",
                }
            ),
            "nonce": f"nonce-{run_id}",
        },
        "raw_prompt": "API05_RAW_PROMPT_SENTINEL",
        "provider_payload": {"body": "API05_PROVIDER_PAYLOAD_SENTINEL"},
        "provider_body": "API05_PROVIDER_BODY_SENTINEL",
    }
    if include_operator_approval:
        policy_summary = provider_precheck_operator_policy_summary(payload)
        payload["operator_approval"] = {
            "operator_ref": "local-operator",
            "approved_at": "2026-06-01T00:00:00Z",
            "decision": "approved",
            "approved_policy_summary_hash": (
                approved_policy_summary_hash or policy_summary["policy_summary_hash"]
            ),
            "authorization_material": "API06_OPERATOR_AUTH_SENTINEL",
        }
    if include_manual_test_proposal:
        payload["manual_test_proposal"] = {
            "proposal_id": f"proposal-{run_id}",
            "run_id": run_id,
            "prompt_contract_hash": payload["prompt_contract_hash"],
            "provider_name": "solar-pro-3",
            "model_name": "solar-pro-3",
            "request_timeout_seconds": 30,
            "max_cost_units": 1,
            "max_live_api_calls": 1,
            "max_output_unit_budget": 512,
            "rollback_plan_id": f"rollback-{run_id}",
            "abort_criteria": [
                "API08_ABORT_CRITERIA_SENTINEL",
                "stop on timeout, quota, or unexpected provider error",
            ],
        }
        if include_manual_test_operator_approval:
            proposal_summary = provider_manual_test_proposal_summary(payload)
            payload["manual_test_operator_approval"] = {
                "operator_ref": "local-operator",
                "approved_at": "2026-06-01T00:05:00Z",
                "decision": "approved",
                "approved_proposal_hash": proposal_summary["proposal_hash"],
                "authorization_material": "API08_MANUAL_TEST_AUTH_SENTINEL",
            }
    if manual_test_executor_enable:
        payload["manual_test_executor_enable"] = True
    if include_one_shot_live_permission:
        proposal_summary = provider_manual_test_proposal_summary(payload)
        planned_call_hash = stable_contract_hash(
            {
                "projection_version": MANUAL_PROVIDER_TEST_EXECUTOR_VERSION,
                "run_id": run_id,
                "prompt_contract_hash": payload["prompt_contract_hash"],
                "provider_name": "solar-pro-3",
                "model_name": "solar-pro-3",
                "proposal_hash": proposal_summary["proposal_hash"],
                "executor_enable_requested": bool(manual_test_executor_enable),
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
            "authorization_material": "API10_PERMISSION_AUTH_SENTINEL",
            "provider_payload": "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        }
    if include_readiness_decision:
        preflight_summary = provider_manual_test_preflight_summary(payload)
        payload["manual_test_readiness_decision"] = {
            "preflight_audit_hash": (
                readiness_preflight_hash_override
                or preflight_summary["preflight_audit_hash"]
            ),
            "decision": readiness_decision,
            "operator_ref": "local-operator",
            "decided_at": "2026-06-01T00:10:00Z",
            "decision_reason_code": "manual-provider-test-candidate-reviewed",
            "authorization_material": "API12_READINESS_AUTH_SENTINEL",
            "provider_payload": "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        }
    return payload


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


def _persist_evidence_chain(root, run_id: str = "run-api-provider") -> None:
    store = SQLiteRunnerReportAuditStore(root=root)
    plan_artifact_id = f"artifact-api-plan-{run_id}"
    report_artifact_id = f"artifact-api-report-{run_id}"
    audit_artifact_id = f"artifact-api-audit-{run_id}"
    artifacts = [
        ArtifactRecord(
            artifact_id=plan_artifact_id,
            run_id=run_id,
            kind="api_evidence_fixture",
            name="plan artifact",
            path=None,
            content_hash="f" * 64,
            payload_field_count=0,
            summary="api evidence plan projection",
            created_at="2026-05-31T00:00:00+00:00",
        ),
        ArtifactRecord(
            artifact_id=report_artifact_id,
            run_id=run_id,
            kind="api_evidence_fixture",
            name="report artifact",
            path=None,
            content_hash="f" * 64,
            payload_field_count=0,
            summary="api evidence report projection",
            created_at="2026-05-31T00:00:00+00:00",
        ),
        ArtifactRecord(
            artifact_id=audit_artifact_id,
            run_id=run_id,
            kind="api_evidence_fixture",
            name="audit artifact",
            path=None,
            content_hash="f" * 64,
            payload_field_count=0,
            summary="api evidence audit projection",
            created_at="2026-05-31T00:00:00+00:00",
        ),
    ]
    plan = RunnerPlan(
        run_id=run_id,
        mode="dry_run",
        implementation_brief_hash="a" * 64,
        build_spec_hash="b" * 64,
        planned_actions=[
            {
                "id": "backend-action",
                "role": "backend",
                "summary": "plan backend projection",
                "raw_request_body": "API03_RAW_PLANNED_BODY",
                "provider_payload": {"body": "API03_PROVIDER_BODY"},
                "runtime_payload": "API03_RUNTIME_BODY",
                "file_body": "API03_FILE_BODY",
            }
        ],
        artifact_manifest=[{"kind": "backend", "path": f"runs/{run_id}/backend"}],
        required_approvals=[{"approval_type": "live_runner", "signature_id": "API03_SIGNATURE"}],
        side_effects={"provider_calls": 0, "subprocess_calls": 0, "filesystem_writes": 0},
        created_at="2026-05-31T00:00:01+00:00",
    )
    plan_record = runner_plan_record_from_plan(plan, source_artifact_id=plan_artifact_id)
    report = VerificationReport(
        run_id=run_id,
        passed=False,
        checks=[{"name": "dry_run", "passed": True, "details": "API03_RAW_LOG"}],
        errors=["token=api03-secret"],
        generated_files=["backend/main.py"],
        metrics={"boundary_mode": "dry_run", "provider_calls": 0, "raw_log": "API03_METRIC_RAW_LOG"},
        created_at="2026-05-31T00:00:02+00:00",
    )
    report_record = verification_report_record_from_report(
        report,
        source_artifact_id=report_artifact_id,
        runner_plan_hash=plan_record.plan_hash,
    )
    audit_record = audit_event_record_from_event(
        {
            "run_id": run_id,
            "event": "api_evidence",
            "source": "api_test",
            "stage": "read_model",
            "level": "info",
            "message": "API03_AUDIT_RAW_MESSAGE",
            "payload": {
                "provider_payload": "API03_AUDIT_PROVIDER_PAYLOAD",
                "runtime_payload": "API03_AUDIT_RUNTIME_PAYLOAD",
                "signature_id": "API03_AUDIT_SIGNATURE",
                "nonce": "API03_AUDIT_NONCE",
                "safe_count": 1,
            },
            "created_at": "2026-05-31T00:00:03+00:00",
        },
        source_artifact_id=audit_artifact_id,
        linked_plan_hash=plan_record.plan_hash,
        linked_report_hash=report_record.report_hash,
    )
    store.save_records_atomically(
        artifacts=artifacts,
        runner_plans=[plan_record],
        verification_reports=[report_record],
        audit_events=[audit_record],
    )


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
    assert data["canonical_persistence"]["status"] == "skipped"
    assert data["canonical_persistence"]["repository_boundary"]["run_artifact_backend"] == "unconfigured"
    assert data["canonical_persistence"]["execution_boundary"]["local_run_artifact_repository_write_count"] == 0
    assert data["evidence_persistence"]["status"] == "skipped"
    assert data["evidence_persistence"]["repository_boundary"]["runner_report_audit_backend"] == "unconfigured"
    assert data["evidence_persistence"]["execution_boundary"]["local_evidence_repository_write_count"] == 0
    assert payload["events"]
    assert "raw_prompt" not in serialized
    assert "API_RAW_PROMPT_SENTINEL" not in serialized
    assert "API_CONSTRAINT_SENTINEL" not in serialized
    assert "finance-owner@example.com" not in serialized
    assert "API_KEY=secret-value" not in serialized
    assert "provider_payload" not in serialized
    assert "approval_authorization_material" not in serialized


def test_runs_fixture_path_persists_sanitized_evidence_when_sqlite_repo_configured(tmp_path):
    evidence_root = tmp_path / "evidence"
    client = TestClient(create_app(evidence_repository_config=EvidenceRepositoryConfig(root=evidence_root)))

    response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build fixture evidence path with API_KEY=secret and API04_RAW_PROMPT_SENTINEL",
            "target_user": "api04-owner@example.com",
            "product_type": "fixture evidence persistence",
            "constraints": ["never expose API04_CONSTRAINT_SENTINEL"],
            "success_criteria": ["persist sanitized evidence"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    run_id = data["run"]["run_id"]
    persistence = data["evidence_persistence"]

    assert persistence["projection_version"] == "fixture-evidence-persistence-public-v1"
    assert persistence["status"] == "persisted"
    assert persistence["fixture_mode"] is True
    assert persistence["durable_user_approval"] is False
    assert persistence["repository_boundary"]["runner_report_audit_backend"] == "sqlite"
    assert persistence["repository_boundary"]["root_path_returned"] is False
    assert persistence["counts"]["artifact_count"] == data["artifact_count"]
    assert persistence["counts"]["runner_plan_count"] == 1
    assert persistence["counts"]["verification_report_count"] == 1
    assert persistence["counts"]["audit_event_count"] == len(payload["events"]) + 1
    assert persistence["execution_boundary"]["local_evidence_repository_write_count"] == 1
    assert persistence["execution_boundary"]["provider_calls"] == 0
    assert persistence["execution_boundary"]["target_runtime_calls"] == 0
    assert (evidence_root / "agentic_workbench.sqlite3").exists()

    evidence_response = client.get(f"/api/v1/evidence/runs/{run_id}")
    assert evidence_response.status_code == 200
    evidence_payload = evidence_response.json()
    evidence_serialized = _serialized(evidence_payload)
    evidence = evidence_payload["data"]

    assert evidence["status"] == "passed"
    assert evidence["counts"]["runner_plan_count"] == 1
    assert evidence["counts"]["verification_report_count"] == 1
    assert evidence["counts"]["audit_event_count"] == len(payload["events"]) + 1
    assert evidence["counts"]["approval_subject_snapshot_count"] == 0
    assert evidence["counts"]["approval_count"] == 0
    assert evidence["counts"]["replay_nonce_count"] == 0
    assert evidence["runner_plans"][0]["run_id"] == run_id
    assert evidence["runner_plans"][0]["mode"] == "dry_run"
    assert evidence["runner_plans"][0]["planned_action_count"] == 3
    assert evidence["runner_plans"][0]["action_role_counts"]["backend"] == 1
    assert evidence["runner_plans"][0]["action_role_counts"]["frontend"] == 1
    assert evidence["runner_plans"][0]["action_role_counts"]["verifier"] == 1
    assert evidence["verification_reports"][0]["mode"] == "dry_run"
    assert evidence["verification_reports"][0]["generated_file_count"] == 0
    assert evidence["verification_reports"][0]["runner_plan_hash"] == persistence["hashes"]["runner_plan_hash"]
    assert evidence["execution_boundary"]["provider_calls"] == 0
    assert evidence["execution_boundary"]["target_runtime_calls"] == 0
    assert evidence["execution_boundary"]["solar_provider_calls"] == 0

    combined = _serialized({"run_response": payload, "evidence_response": evidence_payload})
    for forbidden in (
        "raw_prompt",
        "API04_RAW_PROMPT_SENTINEL",
        "API04_CONSTRAINT_SENTINEL",
        "api04-owner@example.com",
        "API_KEY=secret",
        "provider_payload",
        "runtime_payload",
        "file_body",
        str(tmp_path),
    ):
        assert forbidden not in serialized
        assert forbidden not in evidence_serialized
        assert forbidden not in combined


def test_runs_fixture_evidence_persistence_blocks_corrupted_sqlite_store_without_raw_echo(tmp_path):
    corrupt_root = tmp_path / "corrupt-evidence"
    corrupt_root.mkdir()
    (corrupt_root / "agentic_workbench.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(create_app(evidence_repository_config=EvidenceRepositoryConfig(root=corrupt_root)))

    response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build fixture evidence path with API04_CORRUPT_RAW_SENTINEL",
            "target_user": "api04-corrupt-owner@example.com",
            "product_type": "fixture evidence persistence",
            "constraints": ["never expose corrupt store path"],
            "success_criteria": ["block unsafe persistence"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    persistence = data["evidence_persistence"]
    checks = {check["name"]: check["passed"] for check in persistence["checks"]}

    assert data["runtime_mode"] == "fixture"
    assert persistence["status"] == "blocked"
    assert persistence["repository_boundary"]["runner_report_audit_backend"] == "sqlite"
    assert checks["fixture_projection_persisted"] is False
    assert persistence["counts"]["runner_plan_count"] == 0
    assert persistence["execution_boundary"]["provider_calls"] == 0
    assert persistence["execution_boundary"]["target_runtime_calls"] == 0
    assert persistence["execution_boundary"]["local_evidence_repository_write_count"] == 0
    assert "API04_CORRUPT_RAW_SENTINEL" not in serialized
    assert "api04-corrupt-owner@example.com" not in serialized
    assert str(corrupt_root) not in serialized
    assert "not a sqlite database" not in serialized


def test_runs_fixture_canonical_persistence_blocks_corrupted_sqlite_store_without_raw_echo(tmp_path):
    corrupt_root = tmp_path / "corrupt-canonical"
    corrupt_root.mkdir()
    (corrupt_root / "agentic_workbench_runs.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(create_app(run_repository_config=RunArtifactRepositoryConfig(root=corrupt_root)))

    response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build canonical run path with API08_CORRUPT_RAW_SENTINEL",
            "target_user": "api08-corrupt-owner@example.com",
            "product_type": "canonical run persistence",
            "constraints": ["never expose API08_CORRUPT_CONSTRAINT"],
            "success_criteria": ["block unsafe canonical store"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    persistence = data["canonical_persistence"]
    checks = {check["name"]: check["passed"] for check in persistence["checks"]}

    assert data["runtime_mode"] == "fixture"
    assert persistence["status"] == "blocked"
    assert persistence["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert persistence["repository_boundary"]["runner_report_audit_backend"] == "not_queried"
    assert persistence["repository_boundary"]["approval_replay_backend"] == "not_queried"
    assert checks["canonical_run_session_persisted"] is False
    assert persistence["counts"]["run_session_count"] == 0
    assert persistence["counts"]["artifact_count"] == 0
    assert persistence["execution_boundary"]["provider_calls"] == 0
    assert persistence["execution_boundary"]["target_runtime_calls"] == 0
    assert persistence["execution_boundary"]["local_run_artifact_repository_write_count"] == 0
    assert "API08_CORRUPT_RAW_SENTINEL" not in serialized
    assert "API08_CORRUPT_CONSTRAINT" not in serialized
    assert "api08-corrupt-owner@example.com" not in serialized
    assert str(corrupt_root) not in serialized
    assert "not a sqlite database" not in serialized


def test_run_and_artifact_read_apis_return_sanitized_repository_rows_without_cross_run_leakage(tmp_path):
    evidence_root = tmp_path / "evidence"
    run_root = tmp_path / "canonical-runs"
    admission_root = tmp_path / "admission"
    client = TestClient(
        create_app(
            evidence_repository_config=EvidenceRepositoryConfig(root=evidence_root),
            run_repository_config=RunArtifactRepositoryConfig(root=run_root),
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=admission_root,
            ),
        )
    )

    first_response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build first fixture read model with API05_FIRST_RAW_PROMPT",
            "target_user": "api05-first-owner@example.com",
            "product_type": "run artifact read model",
            "constraints": ["never expose API05_FIRST_CONSTRAINT"],
            "success_criteria": ["read sanitized artifacts"],
        },
    )
    second_response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build second fixture read model with API05_SECOND_RAW_PROMPT",
            "target_user": "api05-second-owner@example.com",
            "product_type": "run artifact read model",
            "constraints": ["never expose API05_SECOND_CONSTRAINT"],
            "success_criteria": ["cross-run isolation"],
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_data = first_response.json()["data"]
    second_data = second_response.json()["data"]
    first_run_id = first_data["run"]["run_id"]
    second_run_id = second_data["run"]["run_id"]

    assert first_data["canonical_persistence"]["status"] == "persisted"
    assert first_data["canonical_persistence"]["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert first_data["canonical_persistence"]["repository_boundary"]["runner_report_audit_backend"] == "not_queried"
    assert first_data["canonical_persistence"]["repository_boundary"]["approval_replay_backend"] == "not_queried"
    assert first_data["canonical_persistence"]["counts"]["run_session_count"] == 1
    assert first_data["canonical_persistence"]["counts"]["artifact_count"] == first_data["artifact_count"]
    assert first_data["canonical_persistence"]["execution_boundary"]["provider_calls"] == 0
    assert first_data["canonical_persistence"]["execution_boundary"]["target_runtime_calls"] == 0
    assert (run_root / "agentic_workbench_runs.sqlite3").exists()
    assert (evidence_root / "agentic_workbench.sqlite3").exists()
    assert not (admission_root / "approval_replay.sqlite3").exists()

    run_response = client.get(f"/api/v1/runs/{first_run_id}")
    artifacts_response = client.get(f"/api/v1/runs/{first_run_id}/artifacts")

    assert run_response.status_code == 200
    assert artifacts_response.status_code == 200
    run_payload = run_response.json()
    artifacts_payload = artifacts_response.json()
    run_data = run_payload["data"]
    artifacts_data = artifacts_payload["data"]
    run_checks = {check["name"]: check["passed"] for check in run_data["checks"]}
    artifact_checks = {check["name"]: check["passed"] for check in artifacts_data["checks"]}

    assert run_data["projection_version"] == "canonical-run-composed-read-model-public-v1"
    assert artifacts_data["projection_version"] == "canonical-artifact-read-model-public-v1"
    assert run_data["status"] == "passed"
    assert artifacts_data["status"] == "passed"
    assert run_checks["run_artifact_repository_available"] is True
    assert run_checks["evidence_summary_not_raw_rows"] is True
    assert artifact_checks["run_artifact_repository_available"] is True
    assert artifact_checks["evidence_repository_not_queried"] is True
    assert artifact_checks["approval_replay_repository_not_queried"] is True
    assert run_data["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert run_data["repository_boundary"]["canonical_run_artifact_backend"] == "sqlite"
    assert run_data["repository_boundary"]["runner_report_audit_backend"] == "sqlite"
    assert run_data["repository_boundary"]["approval_replay_backend"] == "sqlite"
    assert run_data["repository_boundary"]["evidence_db_queried"] is True
    assert run_data["repository_boundary"]["approval_replay_db_queried"] is True
    assert artifacts_data["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert artifacts_data["repository_boundary"]["approval_replay_backend"] == "not_queried"
    assert run_data["run"]["run_id"] == first_run_id
    assert run_data["run"]["prompt_contract_hash"]
    assert run_data["run"]["stage"] == "complete"
    assert run_data["run"]["status"] == "complete"
    assert run_data["run"]["idea_summary"]
    assert run_data["counts"]["artifact_count"] == first_data["artifact_count"]
    assert artifacts_data["counts"]["artifact_count"] == first_data["artifact_count"]
    assert run_data["counts"]["run_session_count"] == 1
    assert run_data["counts"]["runner_plan_count"] == 1
    assert run_data["counts"]["verification_report_count"] == 1
    assert run_data["counts"]["audit_event_count"] == len(first_response.json()["events"]) + 1
    assert run_data["counts"]["approval_subject_snapshot_count"] == 0
    assert run_data["counts"]["approval_count"] == 0
    assert run_data["counts"]["replay_nonce_count"] == 0
    assert run_data["evidence_summary"]["status"] == "available"
    assert run_data["evidence_summary"]["counts"]["runner_plan_count"] == 1
    assert run_data["evidence_summary"]["counts"]["verification_report_count"] == 1
    assert run_data["evidence_summary"]["counts"]["source_artifact_count"] == first_data["artifact_count"]
    assert run_data["evidence_summary"]["linkage"]["run_id_matched"] is True
    assert run_data["evidence_summary"]["linkage"]["artifact_linkage_checked"] is True
    assert {artifact["run_id"] for artifact in artifacts_data["artifacts"]} == {first_run_id}
    assert {artifact["run_id"] for artifact in run_data["artifacts"]} == {first_run_id}
    assert run_data["execution_boundary"]["provider_calls"] == 0
    assert run_data["execution_boundary"]["target_runtime_calls"] == 0
    assert run_data["execution_boundary"]["solar_provider_calls"] == 0

    combined = _serialized({"run": run_payload, "artifacts": artifacts_payload})
    for forbidden in (
        second_run_id,
        "raw_prompt",
        "API05_FIRST_RAW_PROMPT",
        "API05_SECOND_RAW_PROMPT",
        "API05_FIRST_CONSTRAINT",
        "API05_SECOND_CONSTRAINT",
        "api05-first-owner@example.com",
        "api05-second-owner@example.com",
        "provider_payload",
        "runtime_payload",
        "file_body",
        "signature_id",
        "signed_contract_hash",
        str(tmp_path),
    ):
        assert forbidden not in combined


def test_composed_run_read_model_keeps_canonical_lookup_when_evidence_unconfigured(tmp_path):
    run_root = tmp_path / "canonical-runs"
    client = TestClient(create_app(run_repository_config=RunArtifactRepositoryConfig(root=run_root)))

    create_response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build canonical-only run with API06_MISSING_EVIDENCE_RAW_PROMPT",
            "target_user": "api06-missing-evidence-owner@example.com",
            "product_type": "composed read model",
            "constraints": ["never expose API06_MISSING_EVIDENCE_CONSTRAINT"],
            "success_criteria": ["read canonical state without evidence"],
        },
    )

    assert create_response.status_code == 200
    run_id = create_response.json()["data"]["run"]["run_id"]

    read_response = client.get(f"/api/v1/runs/{run_id}")

    assert read_response.status_code == 200
    payload = read_response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "passed"
    assert data["projection_version"] == "canonical-run-composed-read-model-public-v1"
    assert checks["run_artifact_repository_available"] is True
    assert checks["evidence_summary_not_raw_rows"] is True
    assert data["repository_boundary"]["runner_report_audit_backend"] == "unconfigured"
    assert data["repository_boundary"]["approval_replay_backend"] == "not_queried_or_unconfigured"
    assert data["repository_boundary"]["evidence_db_queried"] is False
    assert data["repository_boundary"]["approval_replay_db_queried"] is False
    assert data["evidence_summary"]["status"] == "unconfigured"
    assert data["evidence_summary"]["counts"]["runner_plan_count"] == 0
    assert data["evidence_summary"]["counts"]["approval_count"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert "API06_MISSING_EVIDENCE_RAW_PROMPT" not in serialized
    assert "API06_MISSING_EVIDENCE_CONSTRAINT" not in serialized
    assert "api06-missing-evidence-owner@example.com" not in serialized
    assert str(tmp_path) not in serialized


def test_composed_run_read_model_blocks_only_evidence_section_when_evidence_store_corrupted(tmp_path):
    run_root = tmp_path / "canonical-runs"
    corrupt_evidence_root = tmp_path / "corrupt-evidence"
    corrupt_evidence_root.mkdir()
    (corrupt_evidence_root / "agentic_workbench.sqlite3").write_text(
        "not a sqlite database",
        encoding="utf-8",
    )
    client = TestClient(
        create_app(
            run_repository_config=RunArtifactRepositoryConfig(root=run_root),
            evidence_repository_config=EvidenceRepositoryConfig(root=corrupt_evidence_root),
        )
    )

    create_response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build canonical run with API06_CORRUPT_EVIDENCE_RAW_PROMPT",
            "target_user": "api06-corrupt-evidence-owner@example.com",
            "product_type": "composed read model",
            "constraints": ["never expose API06_CORRUPT_EVIDENCE_CONSTRAINT"],
            "success_criteria": ["block only evidence summary"],
        },
    )

    assert create_response.status_code == 200
    run_id = create_response.json()["data"]["run"]["run_id"]

    read_response = client.get(f"/api/v1/runs/{run_id}")

    assert read_response.status_code == 200
    payload = read_response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["evidence_summary"]["checks"]}

    assert data["status"] == "passed"
    assert data["run"]["run_id"] == run_id
    assert data["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert data["repository_boundary"]["runner_report_audit_backend"] == "sqlite"
    assert data["repository_boundary"]["evidence_db_queried"] is True
    assert data["repository_boundary"]["approval_replay_db_queried"] is False
    assert data["evidence_summary"]["status"] == "blocked"
    assert checks["runner_report_audit_repository_available"] is False
    assert data["evidence_summary"]["counts"]["runner_plan_count"] == 0
    assert data["counts"]["run_session_count"] == 1
    assert data["counts"]["runner_plan_count"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert "API06_CORRUPT_EVIDENCE_RAW_PROMPT" not in serialized
    assert "API06_CORRUPT_EVIDENCE_CONSTRAINT" not in serialized
    assert "api06-corrupt-evidence-owner@example.com" not in serialized
    assert str(corrupt_evidence_root) not in serialized
    assert "not a sqlite database" not in serialized


def test_run_and_artifact_read_apis_block_corrupted_store_without_raw_path(tmp_path):
    corrupt_root = tmp_path / "corrupt-canonical"
    corrupt_root.mkdir()
    (corrupt_root / "agentic_workbench_runs.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(create_app(run_repository_config=RunArtifactRepositoryConfig(root=corrupt_root)))

    run_response = client.get("/api/v1/runs/run-api-provider")
    artifacts_response = client.get("/api/v1/runs/run-api-provider/artifacts")

    assert run_response.status_code == 200
    assert artifacts_response.status_code == 200
    run_payload = run_response.json()
    artifacts_payload = artifacts_response.json()
    combined = _serialized({"run": run_payload, "artifacts": artifacts_payload})
    run_data = run_payload["data"]
    artifacts_data = artifacts_payload["data"]
    run_checks = {check["name"]: check["passed"] for check in run_data["checks"]}
    artifact_checks = {check["name"]: check["passed"] for check in artifacts_data["checks"]}

    assert run_data["status"] == "blocked"
    assert artifacts_data["status"] == "blocked"
    assert run_checks["run_artifact_repository_available"] is False
    assert artifact_checks["run_artifact_repository_available"] is False
    assert run_data["counts"]["artifact_count"] == 0
    assert artifacts_data["counts"]["artifact_count"] == 0
    assert run_data["repository_boundary"]["run_artifact_backend"] == "sqlite"
    assert run_data["repository_boundary"]["runner_report_audit_backend"] == "unconfigured"
    assert run_data["repository_boundary"]["approval_replay_backend"] == "not_queried_or_unconfigured"
    assert run_data["execution_boundary"]["provider_calls"] == 0
    assert artifacts_data["execution_boundary"]["target_runtime_calls"] == 0
    assert str(corrupt_root) not in combined
    assert "not a sqlite database" not in combined


def test_evidence_read_model_api_returns_sqlite_rows_without_raw_bodies_or_auth_material(tmp_path):
    evidence_root = tmp_path / "evidence"
    admission_root = tmp_path / "admission"
    _persist_evidence_chain(evidence_root)
    _persist_evidence_chain(evidence_root, run_id="run-api-other")
    client = TestClient(
        create_app(
            evidence_repository_config=EvidenceRepositoryConfig(root=evidence_root),
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=admission_root,
            ),
        )
    )
    admission_response = client.post(
        "/api/v1/admissions/provider/fake",
        json=_provider_admission_payload(),
    )
    other_admission_response = client.post(
        "/api/v1/admissions/provider/fake",
        json=_provider_admission_payload(
            run_id="run-api-other",
            signature_id="sig-api-provider-other",
            nonce="nonce-api-provider-other",
        ),
    )

    response = client.get("/api/v1/evidence/runs/run-api-provider")

    assert admission_response.status_code == 200
    assert other_admission_response.status_code == 200
    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]

    assert data["projection_version"] == "evidence-read-model-public-v1"
    assert data["status"] == "passed"
    assert data["repository_boundary"]["runner_report_audit_backend"] == "sqlite"
    assert data["repository_boundary"]["approval_replay_backend"] == "sqlite"
    assert data["repository_boundary"]["root_path_returned"] is False
    assert data["counts"]["runner_plan_count"] == 1
    assert data["counts"]["verification_report_count"] == 1
    assert data["counts"]["audit_event_count"] == 1
    assert data["counts"]["approval_subject_snapshot_count"] == 1
    assert data["counts"]["approval_count"] == 1
    assert data["counts"]["replay_nonce_count"] == 1
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert "run-api-other" not in serialized

    for forbidden in (
        "API03_RAW_PLANNED_BODY",
        "API03_PROVIDER_BODY",
        "API03_RUNTIME_BODY",
        "API03_FILE_BODY",
        "API03_RAW_LOG",
        "API03_METRIC_RAW_LOG",
        "API03_AUDIT_RAW_MESSAGE",
        "API03_AUDIT_PROVIDER_PAYLOAD",
        "API03_AUDIT_RUNTIME_PAYLOAD",
        "API03_AUDIT_SIGNATURE",
        "API03_AUDIT_NONCE",
        "api03-secret",
        "sig-api-provider-admission",
        "nonce-api-provider-admission",
        "sig-api-provider-other",
        "nonce-api-provider-other",
        _provider_admission_payload()["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_evidence_read_model_api_blocks_corrupted_evidence_store_without_raw_path(tmp_path):
    corrupt_root = tmp_path / "corrupt-evidence"
    corrupt_root.mkdir()
    (corrupt_root / "agentic_workbench.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(create_app(evidence_repository_config=EvidenceRepositoryConfig(root=corrupt_root)))

    response = client.get("/api/v1/evidence/runs/run-api-provider")

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert checks["runner_report_audit_repository_available"] is False
    assert data["counts"]["runner_plan_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert str(corrupt_root) not in serialized
    assert "not a sqlite database" not in serialized


def test_evidence_read_model_api_blocks_corrupted_approval_store_without_runtime_calls(tmp_path):
    evidence_root = tmp_path / "evidence"
    approval_root = tmp_path / "approval"
    approval_root.mkdir()
    _persist_evidence_chain(evidence_root)
    (approval_root / "approval_replay.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(
        create_app(
            evidence_repository_config=EvidenceRepositoryConfig(root=evidence_root),
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=approval_root,
            ),
        )
    )

    response = client.get("/api/v1/evidence/runs/run-api-provider")

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert checks["runner_report_audit_repository_available"] is True
    assert checks["approval_replay_repository_available"] is False
    assert data["counts"]["runner_plan_count"] == 1
    assert data["counts"]["approval_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert str(approval_root) not in serialized
    assert "not a sqlite database" not in serialized


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


def test_provider_fake_admission_api_uses_sqlite_repository_and_blocks_reused_nonce_across_requests(tmp_path):
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=tmp_path,
            )
        )
    )
    request_payload = _provider_admission_payload()

    first = client.post("/api/v1/admissions/provider/fake", json=request_payload)
    second = client.post("/api/v1/admissions/provider/fake", json=request_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    first_data = first.json()["data"]
    second_payload = second.json()
    second_data = second_payload["data"]
    serialized = _serialized(second_payload)
    checks = {check["name"]: check["passed"] for check in second_data["checks"]}

    assert first_data["status"] == "passed"
    assert first_data["repository_boundary"]["backend"] == "sqlite"
    assert first_data["repository_boundary"]["persists_across_requests"] is True
    assert first_data["execution_boundary"]["fake_provider_invocations"] == 1
    assert second_data["status"] == "blocked"
    assert second_data["repository_boundary"]["backend"] == "sqlite"
    assert second_data["repository_boundary"]["persists_across_requests"] is True
    assert checks["provider_approval_replay_fresh"] is False
    assert second_data["execution_boundary"]["fake_provider_invocations"] == 0
    assert second_data["execution_boundary"]["provider_calls"] == 0
    assert second_data["execution_boundary"]["live_api_calls"] == 0
    assert second_data["execution_boundary"]["live_llm_calls"] == 0
    assert second_data["execution_boundary"]["solar_provider_calls"] == 0
    assert (tmp_path / "approval_replay.sqlite3").exists()
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


def test_live_fake_admission_api_uses_sqlite_repository_and_blocks_reused_nonce_across_requests(tmp_path):
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=tmp_path,
            )
        )
    )
    request_payload = _live_admission_payload()

    first = client.post("/api/v1/admissions/live/fake", json=request_payload)
    second = client.post("/api/v1/admissions/live/fake", json=request_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    first_data = first.json()["data"]
    second_payload = second.json()
    second_data = second_payload["data"]
    serialized = _serialized(second_payload)
    checks = {check["name"]: check["passed"] for check in second_data["checks"]}

    assert first_data["status"] == "passed"
    assert first_data["repository_boundary"]["backend"] == "sqlite"
    assert first_data["repository_boundary"]["persists_across_requests"] is True
    assert first_data["execution_boundary"]["fake_live_runtime_invocations"] == 1
    assert second_data["status"] == "blocked"
    assert second_data["repository_boundary"]["backend"] == "sqlite"
    assert second_data["repository_boundary"]["persists_across_requests"] is True
    assert checks["live_approval_replay_fresh"] is False
    assert second_data["execution_boundary"]["fake_live_runtime_invocations"] == 0
    assert second_data["execution_boundary"]["target_runtime_calls"] == 0
    assert second_data["execution_boundary"]["provider_calls"] == 0
    assert second_data["execution_boundary"]["solar_provider_calls"] == 0
    assert (tmp_path / "approval_replay.sqlite3").exists()
    assert request_payload["approval"]["nonce"] not in serialized
    assert request_payload["approval"]["signature_id"] not in serialized
    assert request_payload["approval"]["signed_contract_hash"] not in serialized
    assert "nonce" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_provider_fake_admission_api_blocks_corrupted_sqlite_store_before_fake_invocation(tmp_path):
    (tmp_path / "approval_replay.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=tmp_path,
            )
        )
    )
    request_payload = _provider_admission_payload()

    response = client.post("/api/v1/admissions/provider/fake", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert data["repository_boundary"]["backend"] == "sqlite"
    assert data["repository_boundary"]["persists_across_requests"] is True
    assert checks["provider_repository_available"] is False
    assert data["approval_persistence"]["approval_row_present"] is False
    assert data["execution_boundary"]["fake_provider_invocations"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert request_payload["approval"]["nonce"] not in serialized
    assert request_payload["approval"]["signature_id"] not in serialized
    assert request_payload["approval"]["signed_contract_hash"] not in serialized
    assert "nonce" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_live_fake_admission_api_blocks_corrupted_sqlite_store_before_fake_runtime(tmp_path):
    (tmp_path / "approval_replay.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=tmp_path,
            )
        )
    )
    request_payload = _live_admission_payload()

    response = client.post("/api/v1/admissions/live/fake", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert data["repository_boundary"]["backend"] == "sqlite"
    assert data["repository_boundary"]["persists_across_requests"] is True
    assert checks["live_runner_repository_available"] is False
    assert data["approval_persistence"]["approval_row_present"] is False
    assert data["execution_boundary"]["fake_live_runtime_invocations"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0
    assert request_payload["approval"]["nonce"] not in serialized
    assert request_payload["approval"]["signature_id"] not in serialized
    assert request_payload["approval"]["signed_contract_hash"] not in serialized
    assert "nonce" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_provider_fake_admission_api_blocks_unavailable_sqlite_store_before_fake_invocation(tmp_path):
    unavailable_root = tmp_path / "not-a-directory"
    unavailable_root.write_text("file blocks sqlite directory", encoding="utf-8")
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=unavailable_root,
            )
        )
    )
    request_payload = _provider_admission_payload()

    response = client.post("/api/v1/admissions/provider/fake", json=request_payload)

    assert response.status_code == 200
    data = response.json()["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert data["repository_boundary"]["backend"] == "sqlite"
    assert checks["provider_repository_available"] is False
    assert data["execution_boundary"]["fake_provider_invocations"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["solar_provider_calls"] == 0


def test_runs_fixture_path_does_not_touch_sqlite_admission_store(tmp_path):
    client = TestClient(
        create_app(
            admission_repository_config=ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=tmp_path,
            )
        )
    )

    response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build fixture-only planning flow with API_KEY=secret-value",
            "target_user": "fixture-owner@example.com",
            "product_type": "fixture admission boundary",
            "constraints": ["do not touch durable admission store"],
            "success_criteria": ["public projection only"],
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]

    assert data["runtime_mode"] == "fixture"
    assert data["approval_lifecycle"] == "synthetic"
    assert data["fixture_mode"] is True
    assert data["durable_user_approval"] is False
    assert not (tmp_path / "approval_replay.sqlite3").exists()


def test_provider_envelope_precheck_api_persists_hash_read_model_without_external_calls(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload()

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    admission = data["provider_envelope_admission"]
    read_model = data["provider_envelope_read_model"]
    operator_policy = data["operator_policy_summary"]
    operator_approval = data["operator_approval_envelope"]
    dry_admission = data["live_provider_dry_admission"]
    manual_proposal = data["manual_provider_test_proposal"]
    manual_executor = data["manual_provider_test_executor"]
    one_shot_permission = data["one_shot_live_permission"]
    preflight_audit = data["manual_provider_test_preflight_audit"]
    readiness_decision = data["manual_provider_test_readiness_decision"]
    review_packet = data["manual_provider_test_review_packet"]
    checklist_by_id = {item["id"]: item for item in dry_admission["checklist"]}

    assert data["projection_version"] == "provider-envelope-admission-api-public-v1"
    assert data["runtime_mode"] == "live_admission_precheck"
    assert data["fixture_mode"] is False
    assert data["status"] == "blocked"
    assert admission["status"] == "admitted"
    assert admission["adapter_reached"] is True
    assert admission["request_contract_hash"]
    assert admission["response_contract_hash"]
    assert admission["counts"]["provider_envelope_count"] == 1
    assert read_model["status"] == "available"
    assert read_model["counts"]["provider_envelope_count"] == 1
    assert operator_policy["projection_version"] == "provider-precheck-operator-policy-summary-v1"
    assert operator_policy["policy"]["request_timeout_seconds"] == 30
    assert operator_policy["policy"]["max_cost_units"] == 1
    assert operator_policy["policy"]["max_live_api_calls"] == 1
    assert operator_policy["policy"]["max_output_unit_budget"] == 512
    assert operator_policy["readiness"]["required_control_count"] == len(LIVE_OPEN_REQUIRED_CONTROLS)
    assert operator_policy["readiness"]["missing_control_count"] == 0
    assert operator_policy["readiness"]["allowed_to_execute"] is False
    assert operator_policy["approval_target"]["input_text_included"] is False
    assert operator_policy["approval_target"]["provider_body_included"] is False
    assert operator_policy["approval_target"]["auth_material_included"] is False
    assert operator_approval["projection_version"] == "provider-precheck-operator-approval-envelope-v1"
    assert operator_approval["status"] == "approved"
    assert operator_approval["decision"] == "approved"
    assert operator_approval["operator_ref"] == "local-operator"
    assert operator_approval["policy_summary_hash"] == operator_policy["policy_summary_hash"]
    assert operator_approval["envelope_hash"]
    assert operator_approval["auth_material_returned"] is False
    assert dry_admission["projection_version"] == "live-provider-dry-admission-checklist-v1"
    assert dry_admission["status"] == "dry_admission_only"
    assert dry_admission["live_ready"] is False
    assert dry_admission["allowed_to_execute"] is False
    assert dry_admission["operator_approval"]["status"] == "approved"
    assert dry_admission["operator_approval"]["policy_summary_hash_match"] is True
    assert dry_admission["policy_summary"]["eligible_for_later_live_open"] is True
    assert dry_admission["policy_summary"]["execution_permission_closed"] is True
    assert checklist_by_id["rollback_plan_documented"]["status"] == "manual_required"
    assert checklist_by_id["manual_operator_final_review"]["status"] == "manual_required"
    assert checklist_by_id["execution_permission_closed"]["status"] == "closed"
    assert dry_admission["manual_required_count"] == 2
    assert dry_admission["execution_boundary"]["api_calls"] == 0
    assert dry_admission["execution_boundary"]["network_calls"] == 0
    assert dry_admission["execution_boundary"]["solar_provider_calls"] == 0
    assert dry_admission["execution_boundary"]["target_runtime_calls"] == 0
    assert manual_proposal["projection_version"] == "manual-provider-test-proposal-gate-v1"
    assert manual_proposal["status"] == "blocked"
    assert manual_proposal["proposal_present"] is False
    assert manual_proposal["operator_approval_present"] is False
    assert manual_proposal["live_ready"] is False
    assert manual_proposal["allowed_to_execute"] is False
    assert manual_proposal["disabled_by_default"] is True
    assert manual_proposal["execution_boundary"]["api_calls"] == 0
    assert manual_proposal["execution_boundary"]["network_calls"] == 0
    assert manual_proposal["execution_boundary"]["solar_provider_calls"] == 0
    assert set(manual_executor) == {"status", "reason", "planned_call_hash"}
    assert manual_executor["status"] == "blocked"
    assert manual_executor["reason"] == "manual_provider_test_proposal_required"
    assert manual_executor["planned_call_hash"] == ""
    assert set(one_shot_permission) == {
        "status",
        "reason",
        "permission_contract_hash",
        "expires_at",
        "permission_field_count",
    }
    assert one_shot_permission["status"] == "blocked"
    assert one_shot_permission["reason"] == "one_shot_permission_required"
    assert one_shot_permission["permission_contract_hash"] == ""
    assert one_shot_permission["permission_field_count"] == 0
    assert set(preflight_audit) == {
        "status",
        "reason",
        "preflight_audit_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "no_call_counter_count",
        "no_call_counter_mismatch_count",
    }
    assert preflight_audit["status"] == "blocked"
    assert preflight_audit["reason"] == "proposal_component_missing_or_blocked"
    assert preflight_audit["preflight_audit_hash"] == ""
    assert preflight_audit["component_count"] == 5
    assert preflight_audit["mismatch_count"] >= 1
    assert preflight_audit["no_call_counter_mismatch_count"] == 0
    assert set(readiness_decision) == {
        "status",
        "reason",
        "readiness_decision_hash",
        "decision_count",
        "approve_decision_count",
        "reject_decision_count",
        "defer_decision_count",
        "mismatch_count",
        "execution_permission_count",
    }
    assert readiness_decision["status"] == "blocked"
    assert readiness_decision["reason"] == "readiness_decision_required"
    assert readiness_decision["readiness_decision_hash"] == ""
    assert readiness_decision["decision_count"] == 0
    assert readiness_decision["execution_permission_count"] == 0
    assert set(review_packet) == {
        "status",
        "reason",
        "review_packet_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "execution_permission_count",
    }
    assert review_packet["status"] == "blocked"
    assert review_packet["reason"] == "preflight_component_missing_or_mismatched"
    assert review_packet["review_packet_hash"] == ""
    assert review_packet["component_count"] == 3
    assert review_packet["passed_component_count"] == 1
    assert review_packet["mismatch_count"] >= 1
    assert review_packet["component_hash_count"] == 1
    assert review_packet["execution_permission_count"] == 0
    assert data["repository_boundary"]["provider_envelope_backend"] == "sqlite"
    assert data["repository_boundary"]["root_path_returned"] is False
    assert data["execution_boundary"]["adapter_invocation_count"] == 1
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["live_llm_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_api_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0
    assert (tmp_path / "provider-envelopes.sqlite3").exists()

    read_response = client.get("/api/v1/admissions/provider/envelopes/run-api-envelope")
    assert read_response.status_code == 200
    read_payload = read_response.json()
    read_data = read_payload["data"]
    read_serialized = _serialized(read_payload)

    assert read_data["status"] == "available"
    assert read_data["provider_envelope_admission"]["counts"]["provider_envelope_count"] == 1
    assert admission["request_contract_hash"] in read_serialized
    assert admission["response_contract_hash"] in read_serialized

    for forbidden in (
        "API05_RAW_PROMPT_SENTINEL",
        "API05_PROVIDER_PAYLOAD_SENTINEL",
        "API05_PROVIDER_BODY_SENTINEL",
        "API06_OPERATOR_AUTH_SENTINEL",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "raw_prompt",
        "provider_payload",
        "authorization_material",
        "approved_policy_summary_hash",
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized
        assert forbidden not in read_serialized


def test_provider_envelope_precheck_api_blocks_missing_operator_approval_before_store(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-no-operator",
        include_operator_approval=False,
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}
    operator_policy = data["operator_policy_summary"]
    operator_approval = data["operator_approval_envelope"]
    dry_admission = data["live_provider_dry_admission"]

    assert data["status"] == "blocked"
    assert checks["operator_approval_envelope_present"] is False
    assert operator_policy["policy_summary_hash"]
    assert operator_policy["readiness"]["required_control_count"] == len(LIVE_OPEN_REQUIRED_CONTROLS)
    assert operator_approval["status"] == "missing"
    assert operator_approval["decision"] == "missing"
    assert operator_approval["auth_material_returned"] is False
    assert dry_admission["status"] == "dry_admission_only"
    assert dry_admission["live_ready"] is False
    assert dry_admission["allowed_to_execute"] is False
    assert dry_admission["operator_approval"]["status"] == "missing"
    assert dry_admission["operator_approval"]["policy_summary_hash_match"] is False
    assert dry_admission["blocked_check_count"] >= 1
    assert dry_admission["manual_required_count"] == 2
    assert data["provider_envelope_admission"]["adapter_reached"] is False
    assert data["provider_envelope_admission"]["counts"]["provider_envelope_count"] == 0
    assert data["execution_boundary"]["adapter_invocation_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert not (tmp_path / "provider-envelopes.sqlite3").exists()
    assert "API05_RAW_PROMPT_SENTINEL" not in serialized
    assert "API05_PROVIDER_PAYLOAD_SENTINEL" not in serialized
    assert "authorization_material" not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "nonce" not in serialized


def test_provider_envelope_precheck_api_accepts_manual_test_proposal_but_keeps_execution_disabled(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-manual-proposal",
        include_manual_test_proposal=True,
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    manual_proposal = data["manual_provider_test_proposal"]
    manual_executor = data["manual_provider_test_executor"]
    checks = {check["name"]: check["passed"] for check in manual_proposal["checks"]}

    assert manual_proposal["status"] == "approved_disabled"
    assert manual_proposal["proposal_present"] is True
    assert manual_proposal["operator_approval_present"] is True
    assert manual_proposal["proposal_hash"]
    assert manual_proposal["proposal_fields"]["run_id_match"] is True
    assert manual_proposal["proposal_fields"]["prompt_contract_hash_match"] is True
    assert manual_proposal["proposal_fields"]["policy_limits_match"] is True
    assert manual_proposal["proposal_fields"]["rollback_plan_present"] is True
    assert manual_proposal["proposal_fields"]["abort_criteria_count"] == 2
    assert manual_proposal["proposal_fields"]["abort_criteria_hash"]
    assert manual_proposal["operator_approval"]["status"] == "approved"
    assert manual_proposal["operator_approval"]["proposal_hash_match"] is True
    assert manual_proposal["operator_approval"]["auth_material_returned"] is False
    assert manual_proposal["live_ready"] is False
    assert manual_proposal["allowed_to_execute"] is False
    assert manual_proposal["disabled_by_default"] is True
    assert checks["manual_test_proposal_present"] is True
    assert checks["manual_test_operator_approval_proposal_hash_match"] is True
    assert checks["manual_test_execution_disabled_by_default"] is True
    assert manual_proposal["execution_boundary"]["sdk_imports"] == 0
    assert manual_proposal["execution_boundary"]["env_value_reads"] == 0
    assert manual_proposal["execution_boundary"]["api_calls"] == 0
    assert manual_proposal["execution_boundary"]["network_calls"] == 0
    assert manual_proposal["execution_boundary"]["solar_provider_calls"] == 0
    assert manual_proposal["execution_boundary"]["target_runtime_calls"] == 0
    assert set(manual_executor) == {"status", "reason", "planned_call_hash"}
    assert manual_executor["status"] == "blocked"
    assert manual_executor["reason"] == "executor_enable_required"
    assert manual_executor["planned_call_hash"]
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "authorization_material",
        "raw_prompt",
        "provider_payload",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_manual_executor_even_when_enable_requested(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-manual-executor",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    manual_proposal = data["manual_provider_test_proposal"]
    manual_executor = data["manual_provider_test_executor"]

    assert manual_proposal["status"] == "approved_disabled"
    assert set(manual_executor) == {"status", "reason", "planned_call_hash"}
    assert manual_executor["status"] == "blocked"
    assert manual_executor["reason"] == "executor_disabled_by_default"
    assert manual_executor["planned_call_hash"]
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["live_llm_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "authorization_material",
        "raw_prompt",
        "provider_payload",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_one_shot_permission_when_executor_blocked(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-one-shot-permission",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    manual_executor = data["manual_provider_test_executor"]
    one_shot_permission = data["one_shot_live_permission"]
    preflight_audit = data["manual_provider_test_preflight_audit"]

    assert manual_executor["status"] == "blocked"
    assert manual_executor["reason"] == "executor_disabled_by_default"
    assert one_shot_permission["status"] == "blocked"
    assert one_shot_permission["reason"] == "executor_blocked"
    assert set(one_shot_permission) == {
        "status",
        "reason",
        "permission_contract_hash",
        "expires_at",
        "permission_field_count",
    }
    assert one_shot_permission["permission_contract_hash"]
    assert one_shot_permission["expires_at"] == "2099-01-01T00:00:00Z"
    assert one_shot_permission["permission_field_count"] == 11
    assert set(preflight_audit) == {
        "status",
        "reason",
        "preflight_audit_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "no_call_counter_count",
        "no_call_counter_mismatch_count",
    }
    assert preflight_audit["status"] == "blocked"
    assert preflight_audit["reason"] == "preflight_execution_closed"
    assert preflight_audit["preflight_audit_hash"]
    assert preflight_audit["component_count"] == 5
    assert preflight_audit["passed_component_count"] == 5
    assert preflight_audit["mismatch_count"] == 0
    assert preflight_audit["no_call_counter_count"] >= 10
    assert preflight_audit["no_call_counter_mismatch_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_marks_preflight_mismatch_without_raw_echo(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-preflight-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
    )
    request_payload["one_shot_live_permission"]["planned_call_hash"] = "mismatched-call-hash"

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    one_shot_permission = data["one_shot_live_permission"]
    preflight_audit = data["manual_provider_test_preflight_audit"]

    assert one_shot_permission["status"] == "blocked"
    assert one_shot_permission["reason"] == "one_shot_permission_contract_mismatch"
    assert one_shot_permission["permission_contract_hash"] == ""
    assert preflight_audit["status"] == "blocked"
    assert preflight_audit["reason"] == "permission_component_missing_or_mismatch"
    assert preflight_audit["preflight_audit_hash"] == ""
    assert preflight_audit["component_count"] == 5
    assert preflight_audit["mismatch_count"] >= 1
    assert preflight_audit["no_call_counter_mismatch_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_records_readiness_decision_without_execution(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-readiness-decision",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    readiness_decision = data["manual_provider_test_readiness_decision"]

    assert readiness_decision["status"] == "blocked"
    assert readiness_decision["reason"] == "readiness_execution_closed"
    assert set(readiness_decision) == {
        "status",
        "reason",
        "readiness_decision_hash",
        "decision_count",
        "approve_decision_count",
        "reject_decision_count",
        "defer_decision_count",
        "mismatch_count",
        "execution_permission_count",
    }
    assert readiness_decision["readiness_decision_hash"]
    assert readiness_decision["decision_count"] == 1
    assert readiness_decision["approve_decision_count"] == 1
    assert readiness_decision["reject_decision_count"] == 0
    assert readiness_decision["defer_decision_count"] == 0
    assert readiness_decision["mismatch_count"] == 0
    assert readiness_decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_builds_review_packet_without_execution(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-review-packet",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
    )
    request_payload["manual_test_review_packet"] = {
        "authorization_material": "API13_REVIEW_AUTH_SENTINEL",
        "provider_payload": "API13_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "provider_body": "API13_REVIEW_PROVIDER_BODY_SENTINEL",
    }

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review_packet = data["manual_provider_test_review_packet"]

    assert review_packet["status"] == "blocked"
    assert review_packet["reason"] == "review_packet_execution_closed"
    assert set(review_packet) == {
        "status",
        "reason",
        "review_packet_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "execution_permission_count",
    }
    assert review_packet["review_packet_hash"]
    assert review_packet["component_count"] == 3
    assert review_packet["passed_component_count"] == 3
    assert review_packet["mismatch_count"] == 0
    assert review_packet["component_hash_count"] == 3
    assert review_packet["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "API13_REVIEW_AUTH_SENTINEL",
        "API13_REVIEW_PROVIDER_PAYLOAD_SENTINEL",
        "API13_REVIEW_PROVIDER_BODY_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_readiness_decision_hash_mismatch(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-readiness-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        readiness_preflight_hash_override="mismatched-preflight-hash",
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    readiness_decision = data["manual_provider_test_readiness_decision"]

    assert readiness_decision["status"] == "blocked"
    assert readiness_decision["reason"] == "preflight_hash_mismatch"
    assert readiness_decision["readiness_decision_hash"] == ""
    assert readiness_decision["decision_count"] == 1
    assert readiness_decision["approve_decision_count"] == 1
    assert readiness_decision["mismatch_count"] >= 1
    assert readiness_decision["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_blocks_review_packet_when_readiness_mismatched(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(
        run_id="run-api-envelope-review-packet-mismatch",
        include_manual_test_proposal=True,
        manual_test_executor_enable=True,
        include_one_shot_live_permission=True,
        include_readiness_decision=True,
        readiness_preflight_hash_override="mismatched-preflight-hash",
    )

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    review_packet = data["manual_provider_test_review_packet"]

    assert review_packet["status"] == "blocked"
    assert review_packet["reason"] == "readiness_decision_missing_or_mismatched"
    assert review_packet["review_packet_hash"] == ""
    assert review_packet["component_count"] == 3
    assert review_packet["passed_component_count"] == 2
    assert review_packet["mismatch_count"] == 1
    assert review_packet["component_hash_count"] == 2
    assert review_packet["execution_permission_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_envelope_env_value_reads"] == 0
    assert data["execution_boundary"]["solar_live_api_calls"] == 0

    for forbidden in (
        "API08_ABORT_CRITERIA_SENTINEL",
        "API08_MANUAL_TEST_AUTH_SENTINEL",
        "API10_PERMISSION_AUTH_SENTINEL",
        "API10_PERMISSION_PROVIDER_PAYLOAD_SENTINEL",
        "API12_READINESS_AUTH_SENTINEL",
        "API12_READINESS_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material",
        "provider_payload",
        "raw_prompt",
        request_payload["approval"]["nonce"],
        request_payload["approval"]["signature_id"],
        request_payload["approval"]["signed_contract_hash"],
        "signature_id",
        "signed_contract_hash",
        "nonce",
        str(tmp_path),
    ):
        assert forbidden not in serialized


def test_provider_envelope_precheck_api_represents_reject_and_defer_decisions(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )

    for decision, expected_reason, count_field in (
        ("reject", "readiness_rejected", "reject_decision_count"),
        ("defer", "readiness_deferred", "defer_decision_count"),
    ):
        request_payload = _provider_envelope_precheck_payload(
            run_id=f"run-api-envelope-readiness-{decision}",
            include_manual_test_proposal=True,
            manual_test_executor_enable=True,
            include_one_shot_live_permission=True,
            include_readiness_decision=True,
            readiness_decision=decision,
        )
        response = client.post(
            "/api/v1/admissions/provider/envelope/precheck",
            json=request_payload,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        readiness_decision = data["manual_provider_test_readiness_decision"]

        assert readiness_decision["status"] == "blocked"
        assert readiness_decision["reason"] == expected_reason
        assert readiness_decision["readiness_decision_hash"]
        assert readiness_decision["decision_count"] == 1
        assert readiness_decision[count_field] == 1
        assert readiness_decision["mismatch_count"] == 0
        assert readiness_decision["execution_permission_count"] == 0
        assert data["execution_boundary"]["provider_calls"] == 0
        assert data["execution_boundary"]["network_calls"] == 0
        assert data["execution_boundary"]["solar_live_api_calls"] == 0


def test_provider_envelope_precheck_api_blocks_missing_store_before_adapter():
    client = TestClient(create_app())
    request_payload = _provider_envelope_precheck_payload(run_id="run-api-envelope-missing")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert data["provider_envelope_admission"]["status"] == "blocked"
    assert data["provider_envelope_admission"]["adapter_reached"] is False
    assert data["repository_boundary"]["provider_envelope_backend"] == "unconfigured"
    assert checks["provider_envelope_repository_configured"] is False
    assert data["execution_boundary"]["adapter_invocation_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert request_payload["approval"]["nonce"] not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_provider_envelope_precheck_api_blocks_corrupted_store_without_raw_echo(tmp_path):
    (tmp_path / "provider-envelopes.sqlite3").write_text(
        "not a sqlite database",
        encoding="utf-8",
    )
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )
    request_payload = _provider_envelope_precheck_payload(run_id="run-api-envelope-corrupt")

    response = client.post(
        "/api/v1/admissions/provider/envelope/precheck",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = _serialized(payload)
    data = payload["data"]
    checks = {check["name"]: check["passed"] for check in data["checks"]}

    assert data["status"] == "blocked"
    assert checks["provider_envelope_repository_available"] is False
    assert data["provider_envelope_admission"]["adapter_reached"] is False
    assert data["execution_boundary"]["adapter_invocation_count"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["live_api_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert "not a sqlite database" not in serialized
    assert str(tmp_path) not in serialized
    assert request_payload["approval"]["nonce"] not in serialized
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized


def test_runs_fixture_path_does_not_touch_provider_envelope_store(tmp_path):
    client = TestClient(
        create_app(
            provider_envelope_repository_config=ProviderEnvelopeRepositoryConfig(root=tmp_path)
        )
    )

    response = client.post(
        "/api/v1/runs",
        json={
            "raw_prompt": "Build fixture path without provider envelope store writes",
            "target_user": "fixture-envelope-owner@example.com",
            "product_type": "fixture provider envelope boundary",
            "constraints": ["keep provider envelope path separate"],
            "success_criteria": ["provider envelope db is not created"],
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]

    assert data["runtime_mode"] == "fixture"
    assert data["fixture_mode"] is True
    assert data["durable_user_approval"] is False
    assert not (tmp_path / "provider-envelopes.sqlite3").exists()


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

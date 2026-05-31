import json

import pytest

from packages.core.claims import find_forbidden_claims
from packages.core.events import WorkflowEvent
from packages.core.exposure import find_forbidden_public_keys
from packages.core.repositories import (
    ArtifactRecord,
    InMemoryAuditEventRepository,
    InMemoryRunnerPlanRepository,
    InMemoryVerificationReportRepository,
    validate_runner_report_audit_linkage,
)
from packages.core.schemas import VerificationReport, WorkflowStage
from packages.daacs_builder.runner_provider import RunnerPlan


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _artifact_record(artifact_id: str, run_id: str = "run-persist-03") -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id=artifact_id,
        run_id=run_id,
        kind="persist_03_fixture",
        name=artifact_id,
        path=None,
        content_hash="f" * 64,
        payload_field_count=0,
        summary="artifact projection fixture",
        created_at="2026-05-31T00:00:00+00:00",
    )


def _runner_plan(run_id: str = "run-persist-03") -> RunnerPlan:
    return RunnerPlan(
        run_id=run_id,
        mode="dry_run",
        implementation_brief_hash="a" * 64,
        build_spec_hash="b" * 64,
        planned_actions=[
            {
                "id": "backend-action",
                "role": "backend",
                "summary": "plan backend contract",
                "raw_request_body": "PERSIST03_RAW_REQUEST_BODY",
                "provider_payload": {"body": "PERSIST03_PROVIDER_PAYLOAD"},
                "runtime_payload": "PERSIST03_RUNTIME_PAYLOAD",
                "command": "npm install && PERSIST03_COMMAND",
                "file_body": "PERSIST03_FILE_BODY",
            },
            {"id": "frontend-action", "role": "frontend", "summary": "plan frontend contract"},
            {"id": "verifier-action", "role": "verifier", "summary": "plan verifier contract"},
        ],
        artifact_manifest=[
            {"kind": "backend_source", "path": f"runs/{run_id}/backend", "file_body": "PERSIST03_MANIFEST_BODY"}
        ],
        required_approvals=[
            {
                "approval_type": "live_runner",
                "reason": "real DAACS execution should never persist as a repository string",
                "signature_id": "PERSIST03_SIGNATURE",
            }
        ],
        side_effects={"provider_calls": 0, "subprocess_calls": 0, "filesystem_writes": 0},
        created_at="2026-05-31T00:00:00+00:00",
    )


def _verification_report(run_id: str = "run-persist-03") -> VerificationReport:
    return VerificationReport(
        run_id=run_id,
        passed=False,
        checks=[
            {"name": "dry_run", "passed": True},
            {
                "name": "runtime_check",
                "passed": False,
                "details": "PERSIST03_RAW_LOG and real DAACS execution text",
                "file_body": "PERSIST03_CHECK_FILE_BODY",
            },
        ],
        errors=[
            "PERSIST03_STDERR raw stack trace at C:/Users/example/secret.py",
            "token=secret-value",
        ],
        generated_files=["backend/main.py", "frontend/src/App.jsx"],
        metrics={
            "boundary_mode": "dry_run",
            "provider_calls": 0,
            "raw_log": "PERSIST03_METRIC_RAW_LOG",
            "real_daacs_execution_count": 99,
        },
        created_at="2026-05-31T00:00:01+00:00",
    )


def _audit_event(run_id: str = "run-persist-03") -> dict:
    return {
        "run_id": run_id,
        "event": "provider_payload",
        "source": "provider_boundary",
        "stage": "build",
        "level": "info",
        "message": "PERSIST03_AUDIT_RAW_MESSAGE with live provider success wording",
        "payload": {
            "status": "blocked",
            "provider_payload": {"body": "PERSIST03_PROVIDER_BODY"},
            "runtime_payload": "PERSIST03_RUNTIME_BODY",
            "request_payload": "PERSIST03_REQUEST_BODY",
            "response_payload": "PERSIST03_RESPONSE_BODY",
            "stdout": "PERSIST03_STDOUT",
            "stderr": "PERSIST03_STDERR",
            "command": "python -m http.server",
            "tool_output": "PERSIST03_TOOL_OUTPUT",
            "approval_hash": "c" * 64,
            "plan_hash": "d" * 64,
            "signature_id": "PERSIST03_SIGNATURE",
            "nonce": "PERSIST03_NONCE",
        },
        "created_at": "2026-05-31T00:00:02+00:00",
    }


def test_runner_plan_repository_stores_hash_counts_not_raw_planned_payload():
    record = InMemoryRunnerPlanRepository().save(_runner_plan(), source_artifact_id="artifact-plan")
    stored = record.to_dict()
    serialized = _serialized(stored)

    assert stored["plan_id"].startswith("plan-")
    assert stored["plan_hash"] == _runner_plan().to_dict()["plan_hash"]
    assert stored["planned_action_count"] == 3
    assert stored["action_role_counts"] == {"backend": 1, "frontend": 1, "verifier": 1}
    assert stored["artifact_manifest_count"] == 1
    assert stored["required_approval_count"] == 1
    assert stored["side_effects_zero"] is True
    assert stored["visible_field_counts"]["forbidden_public_key_count"] > 0
    assert '"planned_actions"' not in serialized
    assert '"required_approvals"' not in serialized
    assert '"artifact_manifest"' not in serialized
    assert "PERSIST03_RAW_REQUEST_BODY" not in serialized
    assert "PERSIST03_PROVIDER_PAYLOAD" not in serialized
    assert "PERSIST03_RUNTIME_PAYLOAD" not in serialized
    assert "real DAACS execution" not in serialized
    assert find_forbidden_public_keys(stored) == []
    assert find_forbidden_claims(serialized) == []


def test_runner_plan_repository_sanitizes_untrusted_mode_and_source_reference():
    record = InMemoryRunnerPlanRepository().save(
        {
            "run_id": "run-persist-03",
            "mode": "live provider success",
            "implementation_brief_hash": "a" * 64,
            "build_spec_hash": "b" * 64,
            "planned_actions": [{"role": "backend"}],
            "artifact_manifest": [],
            "required_approvals": [],
            "side_effects": {"provider_calls": 0},
        },
        source_artifact_id="C:/Users/example/secret-body.txt",
    )
    stored = record.to_dict()
    serialized = _serialized(stored)

    assert stored["mode"] == "unknown"
    assert stored["source_artifact_id"] == ""
    assert "live provider success" not in serialized
    assert "secret-body" not in serialized
    assert find_forbidden_claims(serialized) == []


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("plan_hash", "live provider success"),
        ("implementation_brief_hash", "real DAACS execution"),
        ("build_spec_hash", "C:/Users/example/raw-body.txt"),
    ],
)
def test_runner_plan_repository_rejects_invalid_contract_hash_fields(field_name, field_value):
    payload = {
        "run_id": "run-persist-03",
        "mode": "dry_run",
        "plan_hash": "c" * 64,
        "implementation_brief_hash": "a" * 64,
        "build_spec_hash": "b" * 64,
        "planned_actions": [{"role": "backend"}],
        "artifact_manifest": [],
        "required_approvals": [],
        "side_effects": {"provider_calls": 0},
    }
    payload[field_name] = field_value

    with pytest.raises(ValueError, match=field_name):
        InMemoryRunnerPlanRepository().save(payload)


def test_verification_report_repository_stores_hashes_counts_not_raw_logs_or_file_body():
    plan_record = InMemoryRunnerPlanRepository().save(_runner_plan(), source_artifact_id="artifact-plan")
    record = InMemoryVerificationReportRepository().save(
        _verification_report(),
        source_artifact_id="artifact-report",
        runner_plan_hash=plan_record.plan_hash,
    )
    stored = record.to_dict()
    serialized = _serialized(stored)

    assert stored["mode"] == "dry_run"
    assert stored["passed"] is False
    assert stored["check_count"] == 2
    assert stored["failed_check_count"] == 1
    assert stored["error_count"] == 2
    assert stored["generated_file_count"] == 2
    assert stored["metric_count"] == 3
    assert "PERSIST03_RAW_LOG" not in serialized
    assert "PERSIST03_STDERR" not in serialized
    assert "secret-value" not in serialized
    assert "real_daacs_execution_count" not in serialized
    assert "real DAACS execution" not in serialized
    assert "backend/main.py" not in serialized
    assert find_forbidden_public_keys(stored) == []
    assert find_forbidden_claims(serialized) == []


def test_verification_report_repository_rejects_invalid_plan_hash_reference():
    with pytest.raises(ValueError, match="runner_plan_hash"):
        InMemoryVerificationReportRepository().save(
            _verification_report(),
            runner_plan_hash="not-a-contract-hash",
        )


def test_audit_event_repository_stores_metadata_not_provider_or_runtime_payload():
    record = InMemoryAuditEventRepository().save(
        _audit_event(),
        source_artifact_id="artifact-audit",
        linked_plan_hash="d" * 64,
        linked_report_hash="e" * 64,
    )
    stored = record.to_dict()
    serialized = _serialized(stored)

    assert stored["event_type"] == "audit_event"
    assert stored["source"] == "provider_boundary"
    assert stored["stage"] == "build"
    assert stored["linked_plan_hash"] == "d" * 64
    assert stored["linked_report_hash"] == "e" * 64
    assert stored["payload_field_count"] == 3
    assert stored["visible_field_counts"]["forbidden_public_key_count"] > 0
    assert "PERSIST03_PROVIDER_BODY" not in serialized
    assert "PERSIST03_RUNTIME_BODY" not in serialized
    assert "PERSIST03_STDOUT" not in serialized
    assert "PERSIST03_SIGNATURE" not in serialized
    assert "PERSIST03_NONCE" not in serialized
    assert "live provider success" not in serialized
    assert find_forbidden_public_keys(stored) == []
    assert find_forbidden_claims(serialized) == []


def test_audit_event_repository_rejects_invalid_link_hash_reference():
    with pytest.raises(ValueError, match="linked_plan_hash"):
        InMemoryAuditEventRepository().save(
            _audit_event(),
            linked_plan_hash="not-a-contract-hash",
        )


def test_workflow_event_audit_projection_drops_payload_and_message_bodies():
    event = WorkflowEvent(
        run_id="run-persist-03",
        stage=WorkflowStage.BUILD,
        source="dry_run_runner",
        message="PERSIST03_WORKFLOW_EVENT_RAW_MESSAGE",
        payload={
            "provider_payload": "PERSIST03_PROVIDER_PAYLOAD",
            "runtime_payload": "PERSIST03_RUNTIME_PAYLOAD",
            "safe_count": 1,
        },
    )

    stored = InMemoryAuditEventRepository().save(event).to_dict()
    serialized = _serialized(stored)

    assert stored["event_type"] == "audit_event"
    assert stored["source"] == "dry_run_runner"
    assert stored["payload_field_count"] == 1
    assert "PERSIST03_WORKFLOW_EVENT_RAW_MESSAGE" not in serialized
    assert "PERSIST03_PROVIDER_PAYLOAD" not in serialized
    assert "PERSIST03_RUNTIME_PAYLOAD" not in serialized


def test_runner_report_audit_linkage_rejects_cross_run_rows():
    plan_record = InMemoryRunnerPlanRepository().save(_runner_plan("run-linkage"), source_artifact_id="artifact-plan")
    report_record = InMemoryVerificationReportRepository().save(
        _verification_report("run-other"),
        source_artifact_id="artifact-report",
        runner_plan_hash=plan_record.plan_hash,
    )

    with pytest.raises(ValueError, match="verification report run_id"):
        validate_runner_report_audit_linkage(
            run_id="run-linkage",
            runner_plans=[plan_record],
            verification_reports=[report_record],
            audit_events=[],
        )


def test_runner_report_audit_linkage_covers_artifact_report_run_id_chain():
    plan_record = InMemoryRunnerPlanRepository().save(_runner_plan(), source_artifact_id="artifact-plan")
    report_record = InMemoryVerificationReportRepository().save(
        _verification_report(),
        source_artifact_id="artifact-report",
        runner_plan_hash=plan_record.plan_hash,
    )
    audit_record = InMemoryAuditEventRepository().save(
        _audit_event(),
        source_artifact_id="artifact-audit",
        linked_plan_hash=plan_record.plan_hash,
        linked_report_hash=report_record.report_hash,
    )

    linkage = validate_runner_report_audit_linkage(
        run_id="run-persist-03",
        runner_plans=[plan_record],
        verification_reports=[report_record],
        audit_events=[audit_record],
        artifacts=[
            _artifact_record("artifact-plan"),
            _artifact_record("artifact-report"),
            _artifact_record("artifact-audit"),
        ],
    )

    assert linkage == {
        "run_id_linked": 1,
        "runner_plan_count": 1,
        "verification_report_count": 1,
        "audit_event_count": 1,
        "source_artifact_reference_count": 3,
        "artifact_linkage_count": 3,
    }


def test_runner_report_audit_linkage_rejects_missing_artifact_reference():
    plan_record = InMemoryRunnerPlanRepository().save(_runner_plan(), source_artifact_id="artifact-plan")
    report_record = InMemoryVerificationReportRepository().save(
        _verification_report(),
        source_artifact_id="artifact-report",
        runner_plan_hash=plan_record.plan_hash,
    )

    with pytest.raises(ValueError, match="source_artifact_id"):
        validate_runner_report_audit_linkage(
            run_id="run-persist-03",
            runner_plans=[plan_record],
            verification_reports=[report_record],
            audit_events=[],
            artifacts=[_artifact_record("artifact-plan")],
        )


def test_runner_report_audit_linkage_rejects_unknown_runner_plan_hash():
    report_record = InMemoryVerificationReportRepository().save(
        _verification_report(),
        source_artifact_id="artifact-report",
        runner_plan_hash="d" * 64,
    )

    with pytest.raises(ValueError, match="runner_plan_hash"):
        validate_runner_report_audit_linkage(
            run_id="run-persist-03",
            runner_plans=[],
            verification_reports=[report_record],
            audit_events=[],
        )


def test_runner_report_audit_linkage_rejects_unknown_report_hash():
    plan_record = InMemoryRunnerPlanRepository().save(_runner_plan(), source_artifact_id="artifact-plan")
    audit_record = InMemoryAuditEventRepository().save(
        _audit_event(),
        linked_plan_hash=plan_record.plan_hash,
        linked_report_hash="e" * 64,
    )

    with pytest.raises(ValueError, match="linked_report_hash"):
        validate_runner_report_audit_linkage(
            run_id="run-persist-03",
            runner_plans=[plan_record],
            verification_reports=[],
            audit_events=[audit_record],
        )


def test_runner_report_audit_linkage_rejects_unknown_audit_plan_hash():
    audit_record = InMemoryAuditEventRepository().save(
        _audit_event(),
        linked_plan_hash="d" * 64,
    )

    with pytest.raises(ValueError, match="linked_plan_hash"):
        validate_runner_report_audit_linkage(
            run_id="run-persist-03",
            runner_plans=[],
            verification_reports=[],
            audit_events=[audit_record],
        )

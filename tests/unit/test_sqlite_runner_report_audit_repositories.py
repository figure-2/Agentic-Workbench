import json
import sqlite3

import pytest

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys
from packages.core.repositories import (
    ArtifactRecord,
    audit_event_record_from_event,
    runner_plan_record_from_plan,
    validate_runner_report_audit_linkage,
    verification_report_record_from_report,
)
from packages.core.schemas import VerificationReport
from packages.core.sqlite_repositories import (
    EXPECTED_COLUMNS,
    SQLiteRepositoryUnavailableError,
    SQLiteRunnerReportAuditStore,
)
from packages.daacs_builder.runner_provider import RunnerPlan


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def _artifact_record(artifact_id: str, run_id: str = "run-persist-04") -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id=artifact_id,
        run_id=run_id,
        kind="persist_04_fixture",
        name=artifact_id,
        path=None,
        content_hash="f" * 64,
        payload_field_count=0,
        summary="sqlite artifact projection fixture",
        created_at="2026-05-31T00:00:00+00:00",
    )


def _runner_plan(run_id: str = "run-persist-04") -> RunnerPlan:
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
                "raw_request_body": "PERSIST04_RAW_REQUEST_BODY",
                "provider_payload": {"body": "PERSIST04_PROVIDER_PAYLOAD"},
                "runtime_payload": "PERSIST04_RUNTIME_PAYLOAD",
                "command": "npm install && PERSIST04_COMMAND",
                "file_body": "PERSIST04_FILE_BODY",
            },
            {"id": "frontend-action", "role": "frontend", "summary": "plan frontend contract"},
        ],
        artifact_manifest=[
            {"kind": "backend_source", "path": f"runs/{run_id}/backend", "file_body": "PERSIST04_MANIFEST_BODY"}
        ],
        required_approvals=[
            {
                "approval_type": "live_runner",
                "reason": "real DAACS execution should never persist in sqlite",
                "signature_id": "PERSIST04_SIGNATURE",
            }
        ],
        side_effects={"provider_calls": 0, "subprocess_calls": 0, "filesystem_writes": 0},
        created_at="2026-05-31T00:00:00+00:00",
    )


def _verification_report(run_id: str = "run-persist-04") -> VerificationReport:
    return VerificationReport(
        run_id=run_id,
        passed=False,
        checks=[
            {"name": "dry_run", "passed": True},
            {
                "name": "runtime_check",
                "passed": False,
                "details": "PERSIST04_RAW_LOG and real DAACS execution text",
                "file_body": "PERSIST04_CHECK_FILE_BODY",
            },
        ],
        errors=[
            "PERSIST04_STDERR raw stack trace at C:/Users/example/secret.py",
            "token=secret-value",
        ],
        generated_files=["backend/main.py", "frontend/src/App.jsx"],
        metrics={
            "boundary_mode": "dry_run",
            "provider_calls": 0,
            "raw_log": "PERSIST04_METRIC_RAW_LOG",
            "real_daacs_execution_count": 99,
        },
        created_at="2026-05-31T00:00:01+00:00",
    )


def _audit_event(run_id: str = "run-persist-04") -> dict:
    return {
        "run_id": run_id,
        "event": "provider_payload",
        "source": "provider_boundary",
        "stage": "build",
        "level": "info",
        "message": "PERSIST04_AUDIT_RAW_MESSAGE with live provider success wording",
        "payload": {
            "status": "blocked",
            "provider_payload": {"body": "PERSIST04_PROVIDER_BODY"},
            "runtime_payload": "PERSIST04_RUNTIME_BODY",
            "stdout": "PERSIST04_STDOUT",
            "stderr": "PERSIST04_STDERR",
            "command": "python -m http.server",
            "tool_output": "PERSIST04_TOOL_OUTPUT",
            "approval_hash": "c" * 64,
            "plan_hash": "d" * 64,
            "signature_id": "PERSIST04_SIGNATURE",
            "nonce": "PERSIST04_NONCE",
        },
        "created_at": "2026-05-31T00:00:02+00:00",
    }


def _sqlite_rows(path):
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = {}
        for table in ("artifacts", "runner_plans", "verification_reports", "audit_events"):
            rows[table] = [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]
        return rows


def _persist_full_chain(store: SQLiteRunnerReportAuditStore):
    artifacts = [
        _artifact_record("artifact-plan"),
        _artifact_record("artifact-report"),
        _artifact_record("artifact-audit"),
    ]
    plan_record = runner_plan_record_from_plan(_runner_plan(), source_artifact_id="artifact-plan")
    report_record = verification_report_record_from_report(
        _verification_report(),
        source_artifact_id="artifact-report",
        runner_plan_hash=plan_record.plan_hash,
    )
    audit_record = audit_event_record_from_event(
        _audit_event(),
        source_artifact_id="artifact-audit",
        linked_plan_hash=plan_record.plan_hash,
        linked_report_hash=report_record.report_hash,
    )
    store.save_records_atomically(
        artifacts=artifacts,
        runner_plans=[plan_record],
        verification_reports=[report_record],
        audit_events=[audit_record],
    )
    return artifacts, plan_record, report_record, audit_record


def test_sqlite_schema_migration_is_idempotent_and_round_trips_projection_rows(tmp_path):
    store = SQLiteRunnerReportAuditStore(root=tmp_path)
    same_store = SQLiteRunnerReportAuditStore(root=tmp_path)
    artifacts, plan_record, report_record, audit_record = _persist_full_chain(same_store)

    assert same_store.runner_plans().get(plan_record.plan_hash).to_dict() == plan_record.to_dict()
    assert same_store.verification_reports().get(report_record.report_hash).to_dict() == report_record.to_dict()
    assert [record.to_dict() for record in same_store.audit_events().list_for_run("run-persist-04")] == [
        audit_record.to_dict()
    ]
    assert validate_runner_report_audit_linkage(
        run_id="run-persist-04",
        runner_plans=same_store.runner_plans().list_for_run("run-persist-04"),
        verification_reports=same_store.verification_reports().list_for_run("run-persist-04"),
        audit_events=same_store.audit_events().list_for_run("run-persist-04"),
        artifacts=artifacts,
    )["artifact_linkage_count"] == 3


def test_sqlite_rows_do_not_store_raw_planned_log_file_provider_or_runtime_body(tmp_path):
    store = SQLiteRunnerReportAuditStore(root=tmp_path)
    _persist_full_chain(store)
    rows = _sqlite_rows(store.path)
    serialized = _serialized(rows)

    for sentinel in (
        "PERSIST04_RAW_REQUEST_BODY",
        "PERSIST04_PROVIDER_PAYLOAD",
        "PERSIST04_RUNTIME_PAYLOAD",
        "PERSIST04_COMMAND",
        "PERSIST04_FILE_BODY",
        "PERSIST04_RAW_LOG",
        "PERSIST04_STDERR",
        "PERSIST04_PROVIDER_BODY",
        "PERSIST04_RUNTIME_BODY",
        "PERSIST04_STDOUT",
        "PERSIST04_SIGNATURE",
        "PERSIST04_NONCE",
        "secret-value",
        "real DAACS execution",
        "live provider success",
    ):
        assert sentinel not in serialized
    assert find_forbidden_public_keys(rows) == []
    assert find_forbidden_claims(serialized) == []


def test_sqlite_unique_constraints_block_duplicate_plan_report_and_audit_rows(tmp_path):
    store = SQLiteRunnerReportAuditStore(root=tmp_path)
    _artifacts, plan_record, report_record, audit_record = _persist_full_chain(store)

    with pytest.raises(ValueError, match="runner plan"):
        store.runner_plans().save(_runner_plan(), source_artifact_id="artifact-plan")
    with pytest.raises(ValueError, match="verification report"):
        store.verification_reports().save(
            _verification_report(),
            source_artifact_id="artifact-report",
            runner_plan_hash=plan_record.plan_hash,
        )
    with pytest.raises(ValueError, match="audit event"):
        store.audit_events().save(
            _audit_event(),
            source_artifact_id="artifact-audit",
            linked_plan_hash=plan_record.plan_hash,
            linked_report_hash=report_record.report_hash,
        )
    assert store.audit_events().list_for_run(audit_record.run_id)[0].audit_event_id == audit_record.audit_event_id


def test_sqlite_linkage_constraints_block_missing_artifact_plan_and_report(tmp_path):
    store = SQLiteRunnerReportAuditStore(root=tmp_path)
    plan_record = runner_plan_record_from_plan(_runner_plan(), source_artifact_id="missing-artifact")

    with pytest.raises(ValueError, match="source_artifact_id"):
        store.save_records_atomically(runner_plans=[plan_record])

    store.save_artifact_record(_artifact_record("artifact-report"))
    report_record = verification_report_record_from_report(
        _verification_report(),
        source_artifact_id="artifact-report",
        runner_plan_hash="d" * 64,
    )
    with pytest.raises(ValueError, match="runner_plan_hash"):
        store.save_records_atomically(verification_reports=[report_record])

    store.save_artifact_record(_artifact_record("artifact-audit"))
    audit_record = audit_event_record_from_event(
        _audit_event(),
        source_artifact_id="artifact-audit",
        linked_plan_hash="d" * 64,
        linked_report_hash="e" * 64,
    )
    with pytest.raises(ValueError, match="runner_plan_hash"):
        store.save_records_atomically(audit_events=[audit_record])


def test_sqlite_linkage_constraints_block_audit_report_plan_chain_mismatch(tmp_path):
    store = SQLiteRunnerReportAuditStore(root=tmp_path)
    artifacts = [
        _artifact_record("artifact-plan-a"),
        _artifact_record("artifact-plan-b"),
        _artifact_record("artifact-report"),
        _artifact_record("artifact-audit"),
    ]
    plan_a = runner_plan_record_from_plan(_runner_plan(), source_artifact_id="artifact-plan-a")
    plan_b = runner_plan_record_from_plan(
        {
            "run_id": "run-persist-04",
            "mode": "dry_run",
            "plan_hash": "d" * 64,
            "implementation_brief_hash": "a" * 64,
            "build_spec_hash": "b" * 64,
            "planned_actions": [{"role": "frontend"}],
            "artifact_manifest": [],
            "required_approvals": [],
            "side_effects": {"provider_calls": 0},
        },
        source_artifact_id="artifact-plan-b",
    )
    report = verification_report_record_from_report(
        _verification_report(),
        source_artifact_id="artifact-report",
        runner_plan_hash=plan_a.plan_hash,
    )
    audit = audit_event_record_from_event(
        _audit_event(),
        source_artifact_id="artifact-audit",
        linked_plan_hash=plan_b.plan_hash,
        linked_report_hash=report.report_hash,
    )

    with pytest.raises(ValueError, match="plan/report chain"):
        store.save_records_atomically(
            artifacts=artifacts,
            runner_plans=[plan_a, plan_b],
            verification_reports=[report],
            audit_events=[audit],
        )
    assert store.runner_plans().list_for_run("run-persist-04") == []


def test_sqlite_transaction_rollback_leaves_no_partial_rows(tmp_path):
    store = SQLiteRunnerReportAuditStore(root=tmp_path)
    artifact = _artifact_record("artifact-plan")
    plan_record = runner_plan_record_from_plan(_runner_plan(), source_artifact_id="artifact-plan")

    with pytest.raises(ValueError, match="runner plan"):
        store.save_records_atomically(
            artifacts=[artifact],
            runner_plans=[plan_record, plan_record],
        )

    assert store.list_artifacts_for_run("run-persist-04") == []
    assert store.runner_plans().list_for_run("run-persist-04") == []


def test_sqlite_transaction_rollback_when_report_linkage_fails_after_plan_insert(tmp_path):
    store = SQLiteRunnerReportAuditStore(root=tmp_path)
    plan_record = runner_plan_record_from_plan(_runner_plan(), source_artifact_id="artifact-plan")
    report_record = verification_report_record_from_report(
        _verification_report(),
        source_artifact_id="artifact-report",
        runner_plan_hash="d" * 64,
    )

    with pytest.raises(ValueError, match="runner_plan_hash"):
        store.save_records_atomically(
            artifacts=[_artifact_record("artifact-plan"), _artifact_record("artifact-report")],
            runner_plans=[plan_record],
            verification_reports=[report_record],
        )

    assert store.list_artifacts_for_run("run-persist-04") == []
    assert store.runner_plans().list_for_run("run-persist-04") == []
    assert store.verification_reports().list_for_run("run-persist-04") == []


def test_sqlite_corrupted_and_unavailable_database_are_blocked(tmp_path):
    corrupt_root = tmp_path / "corrupt"
    corrupt_root.mkdir()
    (corrupt_root / "agentic_workbench.sqlite3").write_text("not a sqlite database", encoding="utf-8")

    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteRunnerReportAuditStore(root=corrupt_root)

    unavailable_root = tmp_path / "not-a-directory"
    unavailable_root.write_text("file blocks directory creation", encoding="utf-8")
    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteRunnerReportAuditStore(root=unavailable_root)


def test_sqlite_partial_schema_is_blocked_instead_of_auto_migrated(tmp_path):
    db_path = tmp_path / "agentic_workbench.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
        connection.execute("INSERT INTO schema_migrations(version, applied_at) VALUES (1, '2026-05-31T00:00:00+00:00')")

    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteRunnerReportAuditStore(root=tmp_path)


def test_sqlite_wrong_column_schema_is_blocked_even_when_table_names_exist(tmp_path):
    db_path = tmp_path / "agentic_workbench.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
            INSERT INTO schema_migrations(version, applied_at) VALUES (1, '2026-05-31T00:00:00+00:00');
            CREATE TABLE artifacts(artifact_id TEXT PRIMARY KEY);
            CREATE TABLE runner_plans(plan_hash TEXT UNIQUE);
            CREATE TABLE verification_reports(report_hash TEXT UNIQUE);
            CREATE TABLE audit_events(audit_event_id TEXT PRIMARY KEY);
            CREATE INDEX idx_runner_plans_run_created ON runner_plans(plan_hash);
            CREATE INDEX idx_reports_run_mode_created ON verification_reports(report_hash);
            CREATE INDEX idx_reports_passed_created ON verification_reports(report_hash);
            CREATE INDEX idx_audit_run_created ON audit_events(audit_event_id);
            CREATE INDEX idx_audit_stage_created ON audit_events(audit_event_id);
            """
        )

    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteRunnerReportAuditStore(root=tmp_path)


def test_sqlite_missing_primary_key_schema_is_blocked_even_when_columns_exist(tmp_path):
    db_path = tmp_path / "agentic_workbench.sqlite3"
    with sqlite3.connect(db_path) as connection:
        for table, columns in EXPECTED_COLUMNS.items():
            definitions = []
            for column in sorted(columns):
                column_type = "INTEGER" if column == "version" else "TEXT"
                definitions.append(f"{column} {column_type}")
            connection.execute(f"CREATE TABLE {table}({', '.join(definitions)})")
        connection.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (1, '2026-05-31T00:00:00+00:00')"
        )
        connection.execute("CREATE UNIQUE INDEX uq_runner_plan_hash ON runner_plans(plan_hash)")
        connection.execute("CREATE UNIQUE INDEX uq_report_hash ON verification_reports(report_hash)")
        connection.execute("CREATE INDEX idx_runner_plans_run_created ON runner_plans(run_id, created_at)")
        connection.execute("CREATE INDEX idx_reports_run_mode_created ON verification_reports(run_id, mode, created_at)")
        connection.execute("CREATE INDEX idx_reports_passed_created ON verification_reports(passed, created_at)")
        connection.execute("CREATE INDEX idx_audit_run_created ON audit_events(run_id, created_at)")
        connection.execute("CREATE INDEX idx_audit_stage_created ON audit_events(stage, created_at)")

    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteRunnerReportAuditStore(root=tmp_path)


def test_sqlite_unsafe_run_id_is_blocked(tmp_path):
    store = SQLiteRunnerReportAuditStore(root=tmp_path)
    unsafe_plan = runner_plan_record_from_plan(
        {
            "run_id": "..\\escape",
            "mode": "dry_run",
            "plan_hash": "c" * 64,
            "implementation_brief_hash": "a" * 64,
            "build_spec_hash": "b" * 64,
            "planned_actions": [{"role": "backend"}],
            "artifact_manifest": [],
            "required_approvals": [],
            "side_effects": {"provider_calls": 0},
        },
        source_artifact_id="",
    )

    with pytest.raises(ValueError, match="run_id"):
        store.save_records_atomically(runner_plans=[unsafe_plan])


@pytest.mark.parametrize("run_id", ["run..child", "run:child"])
def test_sqlite_runner_boundary_unsafe_run_id_variants_are_blocked(tmp_path, run_id):
    store = SQLiteRunnerReportAuditStore(root=tmp_path)
    unsafe_plan = runner_plan_record_from_plan(
        {
            "run_id": run_id,
            "mode": "dry_run",
            "plan_hash": "c" * 64,
            "implementation_brief_hash": "a" * 64,
            "build_spec_hash": "b" * 64,
            "planned_actions": [{"role": "backend"}],
            "artifact_manifest": [],
            "required_approvals": [],
            "side_effects": {"provider_calls": 0},
        },
        source_artifact_id="",
    )

    with pytest.raises(ValueError, match="run_id"):
        store.save_records_atomically(runner_plans=[unsafe_plan])


def test_sqlite_cross_run_artifact_plan_report_and_audit_links_are_blocked(tmp_path):
    store = SQLiteRunnerReportAuditStore(root=tmp_path)
    store.save_artifact_record(_artifact_record("artifact-plan-other", run_id="run-other"))
    plan_cross_artifact = runner_plan_record_from_plan(
        _runner_plan(),
        source_artifact_id="artifact-plan-other",
    )
    with pytest.raises(ValueError, match="source_artifact_id"):
        store.save_records_atomically(runner_plans=[plan_cross_artifact])

    store.save_records_atomically(
        artifacts=[_artifact_record("artifact-plan")],
        runner_plans=[runner_plan_record_from_plan(_runner_plan(), source_artifact_id="artifact-plan")],
    )
    plan_record = store.runner_plans().list_for_run("run-persist-04")[0]
    report_cross_plan = verification_report_record_from_report(
        _verification_report("run-other"),
        runner_plan_hash=plan_record.plan_hash,
    )
    with pytest.raises(ValueError, match="runner_plan_hash"):
        store.save_records_atomically(verification_reports=[report_cross_plan])

    store.save_records_atomically(
        artifacts=[_artifact_record("artifact-report")],
        verification_reports=[
            verification_report_record_from_report(
                _verification_report(),
                source_artifact_id="artifact-report",
                runner_plan_hash=plan_record.plan_hash,
            )
        ],
    )
    report_record = store.verification_reports().list_for_run("run-persist-04")[0]
    audit_cross_report = audit_event_record_from_event(
        _audit_event("run-other"),
        linked_plan_hash=plan_record.plan_hash,
        linked_report_hash=report_record.report_hash,
    )
    with pytest.raises(ValueError, match="runner_plan_hash"):
        store.save_records_atomically(audit_events=[audit_cross_report])


def test_sqlite_relative_path_traversal_is_blocked(tmp_path):
    with pytest.raises(ValueError):
        SQLiteRunnerReportAuditStore(root=tmp_path, relative_path="../escape.sqlite3")

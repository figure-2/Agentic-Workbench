"""SQLite adapters for sanitized runner, report, and audit projections."""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import re
import sqlite3
from typing import Iterator, Sequence

from .claims import find_forbidden_claims
from .exposure import find_forbidden_public_keys, sanitize_public_payload
from .pathing import resolve_within_root
from .repositories import (
    ArtifactRecord,
    AuditEventRecord,
    RunnerPlanRecord,
    VerificationReportRecord,
    audit_event_record_from_event,
    runner_plan_record_from_plan,
    verification_report_record_from_report,
)
from .schemas import VerificationReport, utc_now


SCHEMA_VERSION = 1
EXPECTED_TABLES = {
    "schema_migrations",
    "artifacts",
    "runner_plans",
    "verification_reports",
    "audit_events",
}
EXPECTED_INDEXES = {
    "idx_runner_plans_run_created",
    "idx_reports_run_mode_created",
    "idx_reports_passed_created",
    "idx_audit_run_created",
    "idx_audit_stage_created",
}
SAFE_DB_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,120}$")
EXPECTED_COLUMNS = {
    "schema_migrations": {"version", "applied_at"},
    "artifacts": {
        "artifact_id",
        "run_id",
        "kind",
        "name",
        "path",
        "content_hash",
        "payload_field_count",
        "summary",
        "created_at",
    },
    "runner_plans": {
        "plan_id",
        "run_id",
        "mode",
        "plan_hash",
        "implementation_brief_hash",
        "build_spec_hash",
        "source_artifact_id",
        "planned_action_count",
        "action_role_counts",
        "artifact_manifest_count",
        "required_approval_count",
        "side_effect_count",
        "side_effects_zero",
        "payload_hash",
        "payload_field_count",
        "visible_field_counts",
        "summary",
        "created_at",
    },
    "verification_reports": {
        "report_id",
        "run_id",
        "mode",
        "source_artifact_id",
        "runner_plan_hash",
        "report_hash",
        "passed",
        "check_count",
        "failed_check_count",
        "error_count",
        "generated_file_count",
        "metric_count",
        "metric_keys",
        "checks_hash",
        "errors_hash",
        "metrics_hash",
        "generated_files_hash",
        "visible_field_counts",
        "summary",
        "created_at",
    },
    "audit_events": {
        "audit_event_id",
        "run_id",
        "event_type",
        "source",
        "stage",
        "level",
        "source_artifact_id",
        "linked_plan_hash",
        "linked_report_hash",
        "message_hash",
        "payload_hash",
        "payload_field_count",
        "visible_field_counts",
        "summary",
        "created_at",
    },
}


class SQLiteRepositoryUnavailableError(RuntimeError):
    """Raised when the SQLite repository cannot be trusted or opened."""


def _json_dumps(value: object) -> str:
    sanitized = sanitize_public_payload(value)
    return json.dumps(sanitized, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _json_loads_dict(value: str) -> dict[str, int]:
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise SQLiteRepositoryUnavailableError("sqlite repository row is unavailable")
    return {str(key): int(item) for key, item in payload.items()}


def _json_loads_str_tuple(value: str) -> tuple[str, ...]:
    payload = json.loads(value)
    if not isinstance(payload, list):
        raise SQLiteRepositoryUnavailableError("sqlite repository row is unavailable")
    return tuple(str(item) for item in payload)


def _assert_public_row_safe(value: object, *, label: str) -> None:
    row = sanitize_public_payload(value)
    if find_forbidden_public_keys(row):
        raise ValueError(f"{label} contains forbidden public keys")
    serialized = _json_dumps(row)
    if find_forbidden_claims(serialized):
        raise ValueError(f"{label} contains forbidden claim language")


def _assert_safe_db_identifier(value: str, *, label: str, allow_empty: bool = False) -> None:
    if allow_empty and not value:
        return
    if not SAFE_DB_ID_PATTERN.fullmatch(value):
        raise ValueError(f"{label} is not a safe database identifier")


def _nullable(value: str) -> str | None:
    return value or None


def _not_null(value: str | None) -> str:
    return value or ""


class SQLiteRunnerReportAuditStore:
    """SQLite schema and transaction boundary for sanitized persistence rows."""

    def __init__(
        self,
        *,
        root: str | Path,
        relative_path: str | Path = "agentic_workbench.sqlite3",
    ) -> None:
        self.root = Path(root)
        self.path = resolve_within_root(self.root, relative_path)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise SQLiteRepositoryUnavailableError("sqlite repository is unavailable") from exc
        self._ensure_schema()

    def runner_plans(self) -> "SQLiteRunnerPlanRepository":
        return SQLiteRunnerPlanRepository(self)

    def verification_reports(self) -> "SQLiteVerificationReportRepository":
        return SQLiteVerificationReportRepository(self)

    def audit_events(self) -> "SQLiteAuditEventRepository":
        return SQLiteAuditEventRepository(self)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        try:
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            check = connection.execute("PRAGMA quick_check").fetchone()
            if not check or str(check[0]).lower() != "ok":
                raise SQLiteRepositoryUnavailableError("sqlite repository is unavailable")
            yield connection
        except SQLiteRepositoryUnavailableError:
            raise
        except (OSError, sqlite3.DatabaseError) as exc:
            raise SQLiteRepositoryUnavailableError("sqlite repository is unavailable") from exc
        finally:
            try:
                connection.close()
            except UnboundLocalError:
                pass

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connect() as connection:
            try:
                connection.execute("BEGIN")
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def _ensure_schema(self) -> None:
        try:
            with self._connect() as connection:
                tables = self._existing_tables(connection)
                if "schema_migrations" in tables:
                    self._validate_existing_schema(connection)
                    return
                if tables:
                    raise SQLiteRepositoryUnavailableError("sqlite repository schema is unavailable")
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS artifacts (
                        artifact_id TEXT PRIMARY KEY,
                        run_id TEXT NOT NULL,
                        kind TEXT NOT NULL,
                        name TEXT NOT NULL,
                        path TEXT,
                        content_hash TEXT NOT NULL,
                        payload_field_count INTEGER NOT NULL,
                        summary TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS runner_plans (
                        plan_id TEXT PRIMARY KEY,
                        run_id TEXT NOT NULL,
                        mode TEXT NOT NULL,
                        plan_hash TEXT NOT NULL UNIQUE,
                        implementation_brief_hash TEXT NOT NULL,
                        build_spec_hash TEXT NOT NULL,
                        source_artifact_id TEXT REFERENCES artifacts(artifact_id),
                        planned_action_count INTEGER NOT NULL,
                        action_role_counts TEXT NOT NULL,
                        artifact_manifest_count INTEGER NOT NULL,
                        required_approval_count INTEGER NOT NULL,
                        side_effect_count INTEGER NOT NULL,
                        side_effects_zero INTEGER NOT NULL CHECK (side_effects_zero IN (0, 1)),
                        payload_hash TEXT NOT NULL,
                        payload_field_count INTEGER NOT NULL,
                        visible_field_counts TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS verification_reports (
                        report_id TEXT PRIMARY KEY,
                        run_id TEXT NOT NULL,
                        mode TEXT NOT NULL,
                        source_artifact_id TEXT REFERENCES artifacts(artifact_id),
                        runner_plan_hash TEXT REFERENCES runner_plans(plan_hash),
                        report_hash TEXT NOT NULL UNIQUE,
                        passed INTEGER NOT NULL CHECK (passed IN (0, 1)),
                        check_count INTEGER NOT NULL,
                        failed_check_count INTEGER NOT NULL,
                        error_count INTEGER NOT NULL,
                        generated_file_count INTEGER NOT NULL,
                        metric_count INTEGER NOT NULL,
                        metric_keys TEXT NOT NULL,
                        checks_hash TEXT NOT NULL,
                        errors_hash TEXT NOT NULL,
                        metrics_hash TEXT NOT NULL,
                        generated_files_hash TEXT NOT NULL,
                        visible_field_counts TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS audit_events (
                        audit_event_id TEXT PRIMARY KEY,
                        run_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        source TEXT NOT NULL,
                        stage TEXT NOT NULL,
                        level TEXT NOT NULL,
                        source_artifact_id TEXT REFERENCES artifacts(artifact_id),
                        linked_plan_hash TEXT REFERENCES runner_plans(plan_hash),
                        linked_report_hash TEXT REFERENCES verification_reports(report_hash),
                        message_hash TEXT NOT NULL,
                        payload_hash TEXT NOT NULL,
                        payload_field_count INTEGER NOT NULL,
                        visible_field_counts TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );

                    CREATE INDEX IF NOT EXISTS idx_runner_plans_run_created
                        ON runner_plans(run_id, created_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_reports_run_mode_created
                        ON verification_reports(run_id, mode, created_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_reports_passed_created
                        ON verification_reports(passed, created_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_audit_run_created
                        ON audit_events(run_id, created_at);
                    CREATE INDEX IF NOT EXISTS idx_audit_stage_created
                        ON audit_events(stage, created_at);
                    """
                )
                connection.execute(
                    "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (SCHEMA_VERSION, utc_now()),
                )
                self._validate_existing_schema(connection)
                connection.commit()
        except SQLiteRepositoryUnavailableError:
            raise
        except sqlite3.DatabaseError as exc:
            raise SQLiteRepositoryUnavailableError("sqlite repository is unavailable") from exc

    def _existing_tables(self, connection: sqlite3.Connection) -> set[str]:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        return {str(row[0]) for row in rows}

    def _existing_indexes(self, connection: sqlite3.Connection) -> set[str]:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        return {str(row[0]) for row in rows}

    def _validate_existing_schema(self, connection: sqlite3.Connection) -> None:
        tables = self._existing_tables(connection)
        indexes = self._existing_indexes(connection)
        if not EXPECTED_TABLES.issubset(tables):
            raise SQLiteRepositoryUnavailableError("sqlite repository schema is unavailable")
        if not EXPECTED_INDEXES.issubset(indexes):
            raise SQLiteRepositoryUnavailableError("sqlite repository schema is unavailable")
        for table, expected_columns in EXPECTED_COLUMNS.items():
            columns = {
                str(row["name"])
                for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
            }
            if columns != expected_columns:
                raise SQLiteRepositoryUnavailableError("sqlite repository schema is unavailable")
        for table, primary_key in (
            ("schema_migrations", "version"),
            ("artifacts", "artifact_id"),
            ("runner_plans", "plan_id"),
            ("verification_reports", "report_id"),
            ("audit_events", "audit_event_id"),
        ):
            if not self._has_primary_key_on(connection, table, primary_key):
                raise SQLiteRepositoryUnavailableError("sqlite repository schema is unavailable")
        if not self._has_unique_index_on(connection, "runner_plans", ["plan_hash"]):
            raise SQLiteRepositoryUnavailableError("sqlite repository schema is unavailable")
        if not self._has_unique_index_on(connection, "verification_reports", ["report_hash"]):
            raise SQLiteRepositoryUnavailableError("sqlite repository schema is unavailable")
        row = connection.execute(
            "SELECT version FROM schema_migrations WHERE version = ?",
            (SCHEMA_VERSION,),
        ).fetchone()
        if row is None:
            raise SQLiteRepositoryUnavailableError("sqlite repository schema is unavailable")

    def _has_primary_key_on(self, connection: sqlite3.Connection, table: str, column: str) -> bool:
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
        return any(str(row["name"]) == column and int(row["pk"]) == 1 for row in rows)

    def _has_unique_index_on(
        self,
        connection: sqlite3.Connection,
        table: str,
        expected_columns: list[str],
    ) -> bool:
        indexes = connection.execute(f"PRAGMA index_list({table})").fetchall()
        for index in indexes:
            if int(index["unique"]) != 1:
                continue
            columns = [
                str(row["name"])
                for row in connection.execute(f"PRAGMA index_info({index['name']})").fetchall()
            ]
            if columns == expected_columns:
                return True
        return False

    def _assert_artifact_link(self, connection: sqlite3.Connection, artifact_id: str, run_id: str) -> None:
        if not artifact_id:
            return
        row = connection.execute(
            "SELECT run_id FROM artifacts WHERE artifact_id = ?",
            (artifact_id,),
        ).fetchone()
        if row is None or str(row["run_id"]) != run_id:
            raise ValueError("source_artifact_id does not match run_id")

    def _assert_plan_link(self, connection: sqlite3.Connection, plan_hash: str, run_id: str) -> None:
        if not plan_hash:
            return
        row = connection.execute(
            "SELECT run_id FROM runner_plans WHERE plan_hash = ?",
            (plan_hash,),
        ).fetchone()
        if row is None or str(row["run_id"]) != run_id:
            raise ValueError("runner_plan_hash does not match run_id")

    def _assert_report_link(
        self,
        connection: sqlite3.Connection,
        report_hash: str,
        run_id: str,
        linked_plan_hash: str,
    ) -> None:
        if not report_hash:
            return
        row = connection.execute(
            "SELECT run_id, runner_plan_hash FROM verification_reports WHERE report_hash = ?",
            (report_hash,),
        ).fetchone()
        if row is None or str(row["run_id"]) != run_id:
            raise ValueError("linked_report_hash does not match run_id")
        report_plan_hash = str(row["runner_plan_hash"] or "")
        if linked_plan_hash and report_plan_hash and linked_plan_hash != report_plan_hash:
            raise ValueError("audit event linked plan/report chain does not match")

    def save_artifact_record(self, record: ArtifactRecord) -> ArtifactRecord:
        _assert_public_row_safe(record.to_dict(), label="artifact record")
        with self.transaction() as connection:
            self._insert_artifact(connection, record)
        return record

    def list_artifacts_for_run(self, run_id: str) -> list[ArtifactRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM artifacts WHERE run_id = ? ORDER BY created_at",
                (run_id,),
            ).fetchall()
        return [self._artifact_from_row(row) for row in rows]

    def save_records_atomically(
        self,
        *,
        artifacts: Sequence[ArtifactRecord] = (),
        runner_plans: Sequence[RunnerPlanRecord] = (),
        verification_reports: Sequence[VerificationReportRecord] = (),
        audit_events: Sequence[AuditEventRecord] = (),
    ) -> None:
        with self.transaction() as connection:
            for record in artifacts:
                self._insert_artifact(connection, record)
            for record in runner_plans:
                self._insert_runner_plan(connection, record)
            for record in verification_reports:
                self._insert_verification_report(connection, record)
            for record in audit_events:
                self._insert_audit_event(connection, record)

    def _insert_artifact(self, connection: sqlite3.Connection, record: ArtifactRecord) -> None:
        _assert_public_row_safe(record.to_dict(), label="artifact record")
        _assert_safe_db_identifier(record.artifact_id, label="artifact_id")
        _assert_safe_db_identifier(record.run_id, label="run_id")
        try:
            connection.execute(
                """
                INSERT INTO artifacts(
                    artifact_id, run_id, kind, name, path, content_hash,
                    payload_field_count, summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.artifact_id,
                    record.run_id,
                    record.kind,
                    record.name,
                    _nullable(record.path or ""),
                    record.content_hash,
                    record.payload_field_count,
                    record.summary,
                    record.created_at,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("artifact repository constraint failed") from exc

    def _insert_runner_plan(self, connection: sqlite3.Connection, record: RunnerPlanRecord) -> None:
        _assert_public_row_safe(record.to_dict(), label="runner plan record")
        _assert_safe_db_identifier(record.plan_id, label="plan_id")
        _assert_safe_db_identifier(record.run_id, label="run_id")
        _assert_safe_db_identifier(record.source_artifact_id, label="source_artifact_id", allow_empty=True)
        self._assert_artifact_link(connection, record.source_artifact_id, record.run_id)
        try:
            connection.execute(
                """
                INSERT INTO runner_plans(
                    plan_id, run_id, mode, plan_hash, implementation_brief_hash,
                    build_spec_hash, source_artifact_id, planned_action_count,
                    action_role_counts, artifact_manifest_count, required_approval_count,
                    side_effect_count, side_effects_zero, payload_hash, payload_field_count,
                    visible_field_counts, summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.plan_id,
                    record.run_id,
                    record.mode,
                    record.plan_hash,
                    record.implementation_brief_hash,
                    record.build_spec_hash,
                    _nullable(record.source_artifact_id),
                    record.planned_action_count,
                    _json_dumps(record.action_role_counts),
                    record.artifact_manifest_count,
                    record.required_approval_count,
                    record.side_effect_count,
                    int(record.side_effects_zero),
                    record.payload_hash,
                    record.payload_field_count,
                    _json_dumps(record.visible_field_counts),
                    record.summary,
                    record.created_at,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("runner plan repository constraint failed") from exc

    def _insert_verification_report(
        self,
        connection: sqlite3.Connection,
        record: VerificationReportRecord,
    ) -> None:
        _assert_public_row_safe(record.to_dict(), label="verification report record")
        _assert_safe_db_identifier(record.report_id, label="report_id")
        _assert_safe_db_identifier(record.run_id, label="run_id")
        _assert_safe_db_identifier(record.source_artifact_id, label="source_artifact_id", allow_empty=True)
        self._assert_artifact_link(connection, record.source_artifact_id, record.run_id)
        self._assert_plan_link(connection, record.runner_plan_hash, record.run_id)
        try:
            connection.execute(
                """
                INSERT INTO verification_reports(
                    report_id, run_id, mode, source_artifact_id, runner_plan_hash,
                    report_hash, passed, check_count, failed_check_count, error_count,
                    generated_file_count, metric_count, metric_keys, checks_hash,
                    errors_hash, metrics_hash, generated_files_hash, visible_field_counts,
                    summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.report_id,
                    record.run_id,
                    record.mode,
                    _nullable(record.source_artifact_id),
                    _nullable(record.runner_plan_hash),
                    record.report_hash,
                    int(record.passed),
                    record.check_count,
                    record.failed_check_count,
                    record.error_count,
                    record.generated_file_count,
                    record.metric_count,
                    _json_dumps(list(record.metric_keys)),
                    record.checks_hash,
                    record.errors_hash,
                    record.metrics_hash,
                    record.generated_files_hash,
                    _json_dumps(record.visible_field_counts),
                    record.summary,
                    record.created_at,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("verification report repository constraint failed") from exc

    def _insert_audit_event(self, connection: sqlite3.Connection, record: AuditEventRecord) -> None:
        _assert_public_row_safe(record.to_dict(), label="audit event record")
        _assert_safe_db_identifier(record.audit_event_id, label="audit_event_id")
        _assert_safe_db_identifier(record.run_id, label="run_id")
        _assert_safe_db_identifier(record.source_artifact_id, label="source_artifact_id", allow_empty=True)
        self._assert_artifact_link(connection, record.source_artifact_id, record.run_id)
        self._assert_plan_link(connection, record.linked_plan_hash, record.run_id)
        self._assert_report_link(connection, record.linked_report_hash, record.run_id, record.linked_plan_hash)
        if record.linked_plan_hash and record.linked_report_hash:
            row = connection.execute(
                "SELECT runner_plan_hash FROM verification_reports WHERE report_hash = ?",
                (record.linked_report_hash,),
            ).fetchone()
            if row is not None and str(row["runner_plan_hash"] or "") != record.linked_plan_hash:
                raise ValueError("audit event linked plan/report chain does not match")
        try:
            connection.execute(
                """
                INSERT INTO audit_events(
                    audit_event_id, run_id, event_type, source, stage, level,
                    source_artifact_id, linked_plan_hash, linked_report_hash,
                    message_hash, payload_hash, payload_field_count, visible_field_counts,
                    summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.audit_event_id,
                    record.run_id,
                    record.event_type,
                    record.source,
                    record.stage,
                    record.level,
                    _nullable(record.source_artifact_id),
                    _nullable(record.linked_plan_hash),
                    _nullable(record.linked_report_hash),
                    record.message_hash,
                    record.payload_hash,
                    record.payload_field_count,
                    _json_dumps(record.visible_field_counts),
                    record.summary,
                    record.created_at,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("audit event repository constraint failed") from exc

    def _artifact_from_row(self, row: sqlite3.Row) -> ArtifactRecord:
        return ArtifactRecord(
            artifact_id=str(row["artifact_id"]),
            run_id=str(row["run_id"]),
            kind=str(row["kind"]),
            name=str(row["name"]),
            path=_not_null(row["path"]),
            content_hash=str(row["content_hash"]),
            payload_field_count=int(row["payload_field_count"]),
            summary=str(row["summary"]),
            created_at=str(row["created_at"]),
        )

    def _runner_plan_from_row(self, row: sqlite3.Row) -> RunnerPlanRecord:
        return RunnerPlanRecord(
            plan_id=str(row["plan_id"]),
            run_id=str(row["run_id"]),
            mode=str(row["mode"]),
            plan_hash=str(row["plan_hash"]),
            implementation_brief_hash=str(row["implementation_brief_hash"]),
            build_spec_hash=str(row["build_spec_hash"]),
            source_artifact_id=_not_null(row["source_artifact_id"]),
            planned_action_count=int(row["planned_action_count"]),
            action_role_counts=_json_loads_dict(str(row["action_role_counts"])),
            artifact_manifest_count=int(row["artifact_manifest_count"]),
            required_approval_count=int(row["required_approval_count"]),
            side_effect_count=int(row["side_effect_count"]),
            side_effects_zero=bool(row["side_effects_zero"]),
            payload_hash=str(row["payload_hash"]),
            payload_field_count=int(row["payload_field_count"]),
            visible_field_counts=_json_loads_dict(str(row["visible_field_counts"])),
            summary=str(row["summary"]),
            created_at=str(row["created_at"]),
        )

    def _verification_report_from_row(self, row: sqlite3.Row) -> VerificationReportRecord:
        return VerificationReportRecord(
            report_id=str(row["report_id"]),
            run_id=str(row["run_id"]),
            mode=str(row["mode"]),
            source_artifact_id=_not_null(row["source_artifact_id"]),
            runner_plan_hash=_not_null(row["runner_plan_hash"]),
            report_hash=str(row["report_hash"]),
            passed=bool(row["passed"]),
            check_count=int(row["check_count"]),
            failed_check_count=int(row["failed_check_count"]),
            error_count=int(row["error_count"]),
            generated_file_count=int(row["generated_file_count"]),
            metric_count=int(row["metric_count"]),
            metric_keys=_json_loads_str_tuple(str(row["metric_keys"])),
            checks_hash=str(row["checks_hash"]),
            errors_hash=str(row["errors_hash"]),
            metrics_hash=str(row["metrics_hash"]),
            generated_files_hash=str(row["generated_files_hash"]),
            visible_field_counts=_json_loads_dict(str(row["visible_field_counts"])),
            summary=str(row["summary"]),
            created_at=str(row["created_at"]),
        )

    def _audit_event_from_row(self, row: sqlite3.Row) -> AuditEventRecord:
        return AuditEventRecord(
            audit_event_id=str(row["audit_event_id"]),
            run_id=str(row["run_id"]),
            event_type=str(row["event_type"]),
            source=str(row["source"]),
            stage=str(row["stage"]),
            level=str(row["level"]),
            source_artifact_id=_not_null(row["source_artifact_id"]),
            linked_plan_hash=_not_null(row["linked_plan_hash"]),
            linked_report_hash=_not_null(row["linked_report_hash"]),
            message_hash=str(row["message_hash"]),
            payload_hash=str(row["payload_hash"]),
            payload_field_count=int(row["payload_field_count"]),
            visible_field_counts=_json_loads_dict(str(row["visible_field_counts"])),
            summary=str(row["summary"]),
            created_at=str(row["created_at"]),
        )


class SQLiteRunnerPlanRepository:
    """SQLite implementation that persists RunnerPlanRecord projections only."""

    def __init__(self, store: SQLiteRunnerReportAuditStore) -> None:
        self.store = store

    def save(self, plan: object, *, source_artifact_id: str = "") -> RunnerPlanRecord:
        record = runner_plan_record_from_plan(plan, source_artifact_id=source_artifact_id)
        with self.store.transaction() as connection:
            self.store._insert_runner_plan(connection, record)
        return record

    def get(self, plan_hash: str) -> RunnerPlanRecord | None:
        with self.store._connect() as connection:
            row = connection.execute(
                "SELECT * FROM runner_plans WHERE plan_hash = ?",
                (plan_hash,),
            ).fetchone()
        return self.store._runner_plan_from_row(row) if row else None

    def list_for_run(self, run_id: str) -> list[RunnerPlanRecord]:
        with self.store._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM runner_plans WHERE run_id = ? ORDER BY created_at",
                (run_id,),
            ).fetchall()
        return [self.store._runner_plan_from_row(row) for row in rows]


class SQLiteVerificationReportRepository:
    """SQLite implementation that persists VerificationReportRecord projections only."""

    def __init__(self, store: SQLiteRunnerReportAuditStore) -> None:
        self.store = store

    def save(
        self,
        report: VerificationReport,
        *,
        source_artifact_id: str = "",
        runner_plan_hash: str = "",
    ) -> VerificationReportRecord:
        record = verification_report_record_from_report(
            report,
            source_artifact_id=source_artifact_id,
            runner_plan_hash=runner_plan_hash,
        )
        with self.store.transaction() as connection:
            self.store._insert_verification_report(connection, record)
        return record

    def get(self, report_hash: str) -> VerificationReportRecord | None:
        with self.store._connect() as connection:
            row = connection.execute(
                "SELECT * FROM verification_reports WHERE report_hash = ?",
                (report_hash,),
            ).fetchone()
        return self.store._verification_report_from_row(row) if row else None

    def list_for_run(self, run_id: str) -> list[VerificationReportRecord]:
        with self.store._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM verification_reports WHERE run_id = ? ORDER BY created_at",
                (run_id,),
            ).fetchall()
        return [self.store._verification_report_from_row(row) for row in rows]


class SQLiteAuditEventRepository:
    """SQLite implementation that persists AuditEventRecord projections only."""

    def __init__(self, store: SQLiteRunnerReportAuditStore) -> None:
        self.store = store

    def save(
        self,
        event: object,
        *,
        source_artifact_id: str = "",
        linked_plan_hash: str = "",
        linked_report_hash: str = "",
    ) -> AuditEventRecord:
        record = audit_event_record_from_event(
            event,
            source_artifact_id=source_artifact_id,
            linked_plan_hash=linked_plan_hash,
            linked_report_hash=linked_report_hash,
        )
        with self.store.transaction() as connection:
            self.store._insert_audit_event(connection, record)
        return record

    def list_for_run(self, run_id: str) -> list[AuditEventRecord]:
        with self.store._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM audit_events WHERE run_id = ? ORDER BY created_at, audit_event_id",
                (run_id,),
            ).fetchall()
        return [self.store._audit_event_from_row(row) for row in rows]

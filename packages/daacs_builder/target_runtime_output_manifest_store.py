"""Persistence and read model for disabled DAACS target runtime output manifests.

This module stores only hash/status/count evidence from disabled target runtime
output manifest projections. It never stores raw prompts, raw logs, raw file
bodies, runtime payloads, provider payloads, generated artifact bodies, or
generated file paths.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import sqlite3
from typing import Iterator, Protocol

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys, sanitize_public_payload
from packages.core.pathing import resolve_within_root
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash, utc_now

from .runner_provider import is_safe_run_id, safe_public_run_id
from .target_runtime_output_manifest import (
    TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
    TargetRuntimeOutputManifestResult,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_OUTPUT_MANIFEST_SCHEMA_VERSION = 1
TARGET_RUNTIME_OUTPUT_MANIFEST_DB_NAME = "target-runtime-output-manifests.sqlite3"
TARGET_RUNTIME_OUTPUT_MANIFEST_EXPECTED_TABLES = {
    "schema_migrations",
    "target_runtime_output_manifests",
}
TARGET_RUNTIME_OUTPUT_MANIFEST_EXPECTED_COLUMNS = {
    "schema_migrations": {"version", "applied_at"},
    "target_runtime_output_manifests": {
        "record_id",
        "run_id",
        "mode",
        "status",
        "reason",
        "runner_plan_hash",
        "adapter_admission_hash",
        "adapter_admission_read_model_hash",
        "output_manifest_hash",
        "output_groups_hash",
        "counts_hash",
        "execution_boundary_hash",
        "claim_boundary_hash",
        "output_manifest_count",
        "check_count",
        "failed_check_count",
        "adapter_admission_read_model_count",
        "adapter_admission_record_count",
        "adapter_admission_hash_count",
        "adapter_admission_hash_match_count",
        "output_group_count",
        "output_group_hash_count",
        "generated_artifact_body_write_count",
        "execution_permission_count",
        "target_runtime_call_count",
        "filesystem_write_count",
        "subprocess_call_count",
        "network_call_count",
        "created_at",
    },
}


class TargetRuntimeOutputManifestStoreUnavailableError(RuntimeError):
    """Raised when output manifest evidence storage is unavailable."""


@dataclass(frozen=True, slots=True)
class TargetRuntimeOutputManifestRecord:
    """Hash/status/count-only disabled output manifest evidence row."""

    record_id: str
    run_id: str
    mode: str
    status: str
    reason: str
    runner_plan_hash: str
    adapter_admission_hash: str
    adapter_admission_read_model_hash: str
    output_manifest_hash: str
    output_groups_hash: str
    counts_hash: str
    execution_boundary_hash: str
    claim_boundary_hash: str
    output_manifest_count: int
    check_count: int
    failed_check_count: int
    adapter_admission_read_model_count: int
    adapter_admission_record_count: int
    adapter_admission_hash_count: int
    adapter_admission_hash_match_count: int
    output_group_count: int
    output_group_hash_count: int
    generated_artifact_body_write_count: int
    execution_permission_count: int
    target_runtime_call_count: int
    filesystem_write_count: int
    subprocess_call_count: int
    network_call_count: int
    created_at: str

    def to_dict(self) -> JsonDict:
        return sanitize_public_payload(asdict(self))


class TargetRuntimeOutputManifestRepository(Protocol):
    """Repository contract for sanitized output manifest evidence rows."""

    def save(
        self,
        record: TargetRuntimeOutputManifestRecord,
    ) -> TargetRuntimeOutputManifestRecord:
        ...

    def list_for_run(self, run_id: str) -> list[TargetRuntimeOutputManifestRecord]:
        ...


@dataclass(slots=True)
class InMemoryTargetRuntimeOutputManifestRepository:
    """In-memory repository for output manifest persistence tests."""

    records: dict[str, TargetRuntimeOutputManifestRecord] = field(default_factory=dict)

    def save(
        self,
        record: TargetRuntimeOutputManifestRecord,
    ) -> TargetRuntimeOutputManifestRecord:
        _assert_record_safe(record)
        existing = self.records.get(record.record_id)
        if existing is not None and existing != record:
            raise ValueError("target runtime output manifest id conflict")
        if any(
            existing_record.output_manifest_hash == record.output_manifest_hash
            and existing_record.record_id != record.record_id
            for existing_record in self.records.values()
        ):
            raise ValueError("target runtime output manifest duplicate hash")
        self.records[record.record_id] = record
        return record

    def list_for_run(self, run_id: str) -> list[TargetRuntimeOutputManifestRecord]:
        return sorted(
            (record for record in self.records.values() if record.run_id == run_id),
            key=lambda record: record.created_at,
        )


def _hash_valid(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


def _as_non_negative_int(value: object) -> int:
    if type(value) is int and value >= 0:
        return value
    return 0


def _assert_projection_safe(value: JsonDict) -> None:
    public = sanitize_public_payload(value)
    if not isinstance(public, dict):
        raise ValueError("target runtime output manifest projection must be a mapping")
    if find_forbidden_public_keys(public):
        raise ValueError("target runtime output manifest projection contains forbidden keys")
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError("target runtime output manifest projection contains claims")
    assert_public_projection_safe(public)


def _assert_record_safe(record: TargetRuntimeOutputManifestRecord) -> None:
    if not is_safe_run_id(record.run_id):
        raise ValueError("target runtime output manifest run_id is unsafe")
    if record.mode != TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED:
        raise ValueError("target runtime output manifest mode must be disabled")
    if record.status != "blocked":
        raise ValueError("target runtime output manifest status must be blocked")
    if record.reason != "target_runtime_output_manifest_execution_closed":
        raise ValueError("target runtime output manifest reason must be execution closed")
    for field_name in (
        "runner_plan_hash",
        "adapter_admission_hash",
        "adapter_admission_read_model_hash",
        "output_manifest_hash",
        "output_groups_hash",
        "counts_hash",
        "execution_boundary_hash",
        "claim_boundary_hash",
    ):
        if not _hash_valid(getattr(record, field_name)):
            raise ValueError(f"{field_name} must be a contract hash")
    for field_name in (
        "output_manifest_count",
        "check_count",
        "failed_check_count",
        "adapter_admission_read_model_count",
        "adapter_admission_record_count",
        "adapter_admission_hash_count",
        "adapter_admission_hash_match_count",
        "output_group_count",
        "output_group_hash_count",
        "generated_artifact_body_write_count",
        "execution_permission_count",
        "target_runtime_call_count",
        "filesystem_write_count",
        "subprocess_call_count",
        "network_call_count",
    ):
        if int(getattr(record, field_name)) < 0:
            raise ValueError(f"{field_name} must be non-negative")
    if record.output_manifest_count != 1:
        raise ValueError("target runtime output manifest count must be one")
    if record.failed_check_count != 0:
        raise ValueError("target runtime output manifest failed checks must be zero")
    if record.adapter_admission_read_model_count != 1:
        raise ValueError("target runtime output manifest requires adapter read model")
    if record.adapter_admission_hash_match_count != 1:
        raise ValueError("target runtime output manifest adapter hash must match")
    if record.output_group_count < 3 or record.output_group_hash_count < 3:
        raise ValueError("target runtime output manifest requires hash-only groups")
    if record.generated_artifact_body_write_count != 0:
        raise ValueError("target runtime output manifest cannot write generated bodies")
    if record.execution_permission_count != 0:
        raise ValueError("target runtime output manifest execution permission must be closed")
    if any(
        getattr(record, field_name) != 0
        for field_name in (
            "target_runtime_call_count",
            "filesystem_write_count",
            "subprocess_call_count",
            "network_call_count",
        )
    ):
        raise ValueError("target runtime output manifest side-effect counters must be zero")
    _assert_projection_safe(record.to_dict())


def target_runtime_output_manifest_record_from_result(
    result: TargetRuntimeOutputManifestResult | JsonDict,
    *,
    created_at: str | None = None,
) -> TargetRuntimeOutputManifestRecord:
    """Convert a disabled output manifest result into a hash-only row."""
    payload = result.to_dict() if hasattr(result, "to_dict") else dict(result)
    _assert_projection_safe(payload)
    counts = payload.get("counts", {})
    execution = payload.get("execution_boundary", {})
    claim_boundary = payload.get("claim_boundary", {})
    output_groups = payload.get("output_groups", [])
    if not isinstance(counts, dict):
        counts = {}
    if not isinstance(execution, dict):
        execution = {}
    if not isinstance(claim_boundary, dict):
        claim_boundary = {}
    if not isinstance(output_groups, list):
        output_groups = []

    record_hash = stable_contract_hash(
        {
            "run_id": safe_public_run_id(str(payload.get("run_id", ""))),
            "output_manifest_hash": str(payload.get("output_manifest_hash", "")),
            "adapter_admission_hash": str(payload.get("adapter_admission_hash", "")),
            "status": str(payload.get("status", "")),
            "reason": str(payload.get("reason", "")),
        }
    )
    record = TargetRuntimeOutputManifestRecord(
        record_id=f"target-runtime-output-manifest-{record_hash[:24]}",
        run_id=safe_public_run_id(str(payload.get("run_id", ""))),
        mode=str(payload.get("mode", "")),
        status=str(payload.get("status", "")),
        reason=str(payload.get("reason", "")),
        runner_plan_hash=str(payload.get("runner_plan_hash", "")),
        adapter_admission_hash=str(payload.get("adapter_admission_hash", "")),
        adapter_admission_read_model_hash=str(
            payload.get("adapter_admission_read_model_hash", "")
        ),
        output_manifest_hash=str(payload.get("output_manifest_hash", "")),
        output_groups_hash=stable_contract_hash(output_groups),
        counts_hash=stable_contract_hash(counts),
        execution_boundary_hash=stable_contract_hash(execution),
        claim_boundary_hash=stable_contract_hash(claim_boundary),
        output_manifest_count=_as_non_negative_int(counts.get("output_manifest_count")),
        check_count=_as_non_negative_int(counts.get("check_count")),
        failed_check_count=_as_non_negative_int(counts.get("failed_check_count")),
        adapter_admission_read_model_count=_as_non_negative_int(
            counts.get("adapter_admission_read_model_count")
        ),
        adapter_admission_record_count=_as_non_negative_int(
            counts.get("adapter_admission_record_count")
        ),
        adapter_admission_hash_count=_as_non_negative_int(
            counts.get("adapter_admission_hash_count")
        ),
        adapter_admission_hash_match_count=_as_non_negative_int(
            counts.get("adapter_admission_hash_match_count")
        ),
        output_group_count=_as_non_negative_int(counts.get("output_group_count")),
        output_group_hash_count=_as_non_negative_int(
            counts.get("output_group_hash_count")
        ),
        generated_artifact_body_write_count=_as_non_negative_int(
            counts.get("generated_artifact_body_write_count")
        ),
        execution_permission_count=_as_non_negative_int(
            counts.get("execution_permission_count")
        ),
        target_runtime_call_count=_as_non_negative_int(
            counts.get("target_runtime_call_count")
        ),
        filesystem_write_count=_as_non_negative_int(counts.get("filesystem_write_count")),
        subprocess_call_count=_as_non_negative_int(counts.get("subprocess_call_count")),
        network_call_count=_as_non_negative_int(counts.get("network_call_count")),
        created_at=created_at or utc_now(),
    )
    _assert_record_safe(record)
    return record


class SQLiteTargetRuntimeOutputManifestStore:
    """SQLite store for sanitized target runtime output manifest rows."""

    def __init__(
        self,
        root: str | Path,
        *,
        filename: str = TARGET_RUNTIME_OUTPUT_MANIFEST_DB_NAME,
    ) -> None:
        self.root = Path(root)
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            self.path = resolve_within_root(self.root, filename)
            self._ensure_schema()
        except (OSError, ValueError, sqlite3.DatabaseError) as exc:
            raise TargetRuntimeOutputManifestStoreUnavailableError(
                "target runtime output manifest sqlite store is unavailable"
            ) from exc

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        try:
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
            try:
                yield connection
            finally:
                connection.close()
        except sqlite3.DatabaseError as exc:
            raise TargetRuntimeOutputManifestStoreUnavailableError(
                "target runtime output manifest sqlite store is unavailable"
            ) from exc

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS target_runtime_output_manifests (
                    record_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    runner_plan_hash TEXT NOT NULL,
                    adapter_admission_hash TEXT NOT NULL,
                    adapter_admission_read_model_hash TEXT NOT NULL,
                    output_manifest_hash TEXT NOT NULL UNIQUE,
                    output_groups_hash TEXT NOT NULL,
                    counts_hash TEXT NOT NULL,
                    execution_boundary_hash TEXT NOT NULL,
                    claim_boundary_hash TEXT NOT NULL,
                    output_manifest_count INTEGER NOT NULL,
                    check_count INTEGER NOT NULL,
                    failed_check_count INTEGER NOT NULL,
                    adapter_admission_read_model_count INTEGER NOT NULL,
                    adapter_admission_record_count INTEGER NOT NULL,
                    adapter_admission_hash_count INTEGER NOT NULL,
                    adapter_admission_hash_match_count INTEGER NOT NULL,
                    output_group_count INTEGER NOT NULL,
                    output_group_hash_count INTEGER NOT NULL,
                    generated_artifact_body_write_count INTEGER NOT NULL,
                    execution_permission_count INTEGER NOT NULL,
                    target_runtime_call_count INTEGER NOT NULL,
                    filesystem_write_count INTEGER NOT NULL,
                    subprocess_call_count INTEGER NOT NULL,
                    network_call_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_target_runtime_output_manifests_run_created
                    ON target_runtime_output_manifests(run_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_target_runtime_output_manifests_adapter
                    ON target_runtime_output_manifests(adapter_admission_hash);
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (TARGET_RUNTIME_OUTPUT_MANIFEST_SCHEMA_VERSION, utc_now()),
            )
            connection.commit()
        self._assert_schema()

    def _assert_schema(self) -> None:
        with self._connect() as connection:
            tables = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if not TARGET_RUNTIME_OUTPUT_MANIFEST_EXPECTED_TABLES.issubset(tables):
                raise TargetRuntimeOutputManifestStoreUnavailableError(
                    "target runtime output manifest sqlite schema is unavailable"
                )
            for table, expected_columns in TARGET_RUNTIME_OUTPUT_MANIFEST_EXPECTED_COLUMNS.items():
                rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
                columns = {row["name"] for row in rows}
                if columns != expected_columns:
                    raise TargetRuntimeOutputManifestStoreUnavailableError(
                        "target runtime output manifest sqlite schema is unavailable"
                    )

    def repository(self) -> "SQLiteTargetRuntimeOutputManifestRepository":
        self._assert_schema()
        return SQLiteTargetRuntimeOutputManifestRepository(self)


class SQLiteTargetRuntimeOutputManifestRepository:
    """SQLite repository for sanitized output manifest rows."""

    def __init__(self, store: SQLiteTargetRuntimeOutputManifestStore) -> None:
        self.store = store

    def save(
        self,
        record: TargetRuntimeOutputManifestRecord,
    ) -> TargetRuntimeOutputManifestRecord:
        _assert_record_safe(record)
        with self.store._connect() as connection:
            self.store._assert_schema()
            try:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO target_runtime_output_manifests(
                            record_id,
                            run_id,
                            mode,
                            status,
                            reason,
                            runner_plan_hash,
                            adapter_admission_hash,
                            adapter_admission_read_model_hash,
                            output_manifest_hash,
                            output_groups_hash,
                            counts_hash,
                            execution_boundary_hash,
                            claim_boundary_hash,
                            output_manifest_count,
                            check_count,
                            failed_check_count,
                            adapter_admission_read_model_count,
                            adapter_admission_record_count,
                            adapter_admission_hash_count,
                            adapter_admission_hash_match_count,
                            output_group_count,
                            output_group_hash_count,
                            generated_artifact_body_write_count,
                            execution_permission_count,
                            target_runtime_call_count,
                            filesystem_write_count,
                            subprocess_call_count,
                            network_call_count,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record.record_id,
                            record.run_id,
                            record.mode,
                            record.status,
                            record.reason,
                            record.runner_plan_hash,
                            record.adapter_admission_hash,
                            record.adapter_admission_read_model_hash,
                            record.output_manifest_hash,
                            record.output_groups_hash,
                            record.counts_hash,
                            record.execution_boundary_hash,
                            record.claim_boundary_hash,
                            record.output_manifest_count,
                            record.check_count,
                            record.failed_check_count,
                            record.adapter_admission_read_model_count,
                            record.adapter_admission_record_count,
                            record.adapter_admission_hash_count,
                            record.adapter_admission_hash_match_count,
                            record.output_group_count,
                            record.output_group_hash_count,
                            record.generated_artifact_body_write_count,
                            record.execution_permission_count,
                            record.target_runtime_call_count,
                            record.filesystem_write_count,
                            record.subprocess_call_count,
                            record.network_call_count,
                            record.created_at,
                        ),
                    )
            except sqlite3.IntegrityError as exc:
                raise ValueError("target runtime output manifest duplicate hash or id") from exc
        return record

    def list_for_run(self, run_id: str) -> list[TargetRuntimeOutputManifestRecord]:
        with self.store._connect() as connection:
            self.store._assert_schema()
            rows = connection.execute(
                """
                SELECT * FROM target_runtime_output_manifests
                WHERE run_id = ?
                ORDER BY created_at ASC, record_id ASC
                """,
                (run_id,),
            ).fetchall()
        return [self._record_from_row(row) for row in rows]

    def _record_from_row(self, row: sqlite3.Row) -> TargetRuntimeOutputManifestRecord:
        record = TargetRuntimeOutputManifestRecord(
            record_id=str(row["record_id"]),
            run_id=str(row["run_id"]),
            mode=str(row["mode"]),
            status=str(row["status"]),
            reason=str(row["reason"]),
            runner_plan_hash=str(row["runner_plan_hash"]),
            adapter_admission_hash=str(row["adapter_admission_hash"]),
            adapter_admission_read_model_hash=str(
                row["adapter_admission_read_model_hash"]
            ),
            output_manifest_hash=str(row["output_manifest_hash"]),
            output_groups_hash=str(row["output_groups_hash"]),
            counts_hash=str(row["counts_hash"]),
            execution_boundary_hash=str(row["execution_boundary_hash"]),
            claim_boundary_hash=str(row["claim_boundary_hash"]),
            output_manifest_count=int(row["output_manifest_count"]),
            check_count=int(row["check_count"]),
            failed_check_count=int(row["failed_check_count"]),
            adapter_admission_read_model_count=int(
                row["adapter_admission_read_model_count"]
            ),
            adapter_admission_record_count=int(row["adapter_admission_record_count"]),
            adapter_admission_hash_count=int(row["adapter_admission_hash_count"]),
            adapter_admission_hash_match_count=int(
                row["adapter_admission_hash_match_count"]
            ),
            output_group_count=int(row["output_group_count"]),
            output_group_hash_count=int(row["output_group_hash_count"]),
            generated_artifact_body_write_count=int(
                row["generated_artifact_body_write_count"]
            ),
            execution_permission_count=int(row["execution_permission_count"]),
            target_runtime_call_count=int(row["target_runtime_call_count"]),
            filesystem_write_count=int(row["filesystem_write_count"]),
            subprocess_call_count=int(row["subprocess_call_count"]),
            network_call_count=int(row["network_call_count"]),
            created_at=str(row["created_at"]),
        )
        _assert_record_safe(record)
        return record


def target_runtime_output_manifest_public_read_model(
    repository: TargetRuntimeOutputManifestRepository,
    *,
    run_id: str,
) -> JsonDict:
    """Return hash/status/count-only output manifest evidence."""
    try:
        records = repository.list_for_run(run_id)
    except Exception:
        return _blocked_read_model(run_id)

    manifests = [
        {
            "status": record.status,
            "reason": record.reason,
            "runner_plan_hash": record.runner_plan_hash,
            "adapter_admission_hash": record.adapter_admission_hash,
            "adapter_admission_read_model_hash": record.adapter_admission_read_model_hash,
            "output_manifest_hash": record.output_manifest_hash,
            "output_groups_hash": record.output_groups_hash,
            "check_count": record.check_count,
            "failed_check_count": record.failed_check_count,
            "adapter_admission_read_model_count": (
                record.adapter_admission_read_model_count
            ),
            "adapter_admission_hash_match_count": (
                record.adapter_admission_hash_match_count
            ),
            "output_group_count": record.output_group_count,
            "output_group_hash_count": record.output_group_hash_count,
            "generated_artifact_body_write_count": (
                record.generated_artifact_body_write_count
            ),
            "execution_permission_count": record.execution_permission_count,
            "target_runtime_call_count": record.target_runtime_call_count,
            "filesystem_write_count": record.filesystem_write_count,
            "subprocess_call_count": record.subprocess_call_count,
            "network_call_count": record.network_call_count,
        }
        for record in records
    ]
    read_model = {
        "projection_version": "target-runtime-output-manifest-read-model-public-v1",
        "status": "available" if records else "not_found",
        "run_id": safe_public_run_id(run_id),
        "counts": {
            "output_manifest_record_count": len(records),
            "output_manifest_hash_count": len(
                {record.output_manifest_hash for record in records}
            ),
            "adapter_admission_hash_count": len(
                {record.adapter_admission_hash for record in records}
            ),
            "adapter_admission_read_model_hash_count": len(
                {record.adapter_admission_read_model_hash for record in records}
            ),
            "output_group_count": sum(record.output_group_count for record in records),
            "output_group_hash_count": sum(
                record.output_group_hash_count for record in records
            ),
            "generated_artifact_body_write_count": sum(
                record.generated_artifact_body_write_count for record in records
            ),
            "execution_permission_count": sum(
                record.execution_permission_count for record in records
            ),
            "target_runtime_call_count": sum(
                record.target_runtime_call_count for record in records
            ),
            "filesystem_write_count": sum(
                record.filesystem_write_count for record in records
            ),
            "subprocess_call_count": sum(record.subprocess_call_count for record in records),
            "network_call_count": sum(record.network_call_count for record in records),
        },
        "output_manifests": manifests,
        "repository_boundary": {
            "target_runtime_output_manifest_store": "available",
            "raw_row_returned": False,
            "root_path_returned": False,
        },
        "execution_boundary": {
            "target_runtime_calls": 0,
            "filesystem_writes": 0,
            "subprocess_calls": 0,
            "network_calls": 0,
            "generated_artifact_body_write_count": 0,
            "execution_permission_count": 0,
        },
    }
    sanitized = sanitize_public_payload(read_model)
    _assert_projection_safe(sanitized)
    return sanitized


def target_runtime_output_manifest_public_read_model_from_sqlite(
    root: str | Path,
    *,
    run_id: str,
    filename: str = TARGET_RUNTIME_OUTPUT_MANIFEST_DB_NAME,
) -> JsonDict:
    """Return a blocked read model if the SQLite store is unavailable."""
    try:
        store = SQLiteTargetRuntimeOutputManifestStore(root=root, filename=filename)
        return target_runtime_output_manifest_public_read_model(
            store.repository(),
            run_id=run_id,
        )
    except Exception:
        return _blocked_read_model(run_id)


def _blocked_read_model(run_id: str) -> JsonDict:
    read_model = {
        "projection_version": "target-runtime-output-manifest-read-model-public-v1",
        "status": "blocked",
        "run_id": safe_public_run_id(run_id),
        "counts": {
            "output_manifest_record_count": 0,
            "output_manifest_hash_count": 0,
            "adapter_admission_hash_count": 0,
            "adapter_admission_read_model_hash_count": 0,
            "output_group_count": 0,
            "output_group_hash_count": 0,
            "generated_artifact_body_write_count": 0,
            "execution_permission_count": 0,
            "target_runtime_call_count": 0,
            "filesystem_write_count": 0,
            "subprocess_call_count": 0,
            "network_call_count": 0,
        },
        "output_manifests": [],
        "repository_boundary": {
            "target_runtime_output_manifest_store": "blocked",
            "raw_row_returned": False,
            "root_path_returned": False,
        },
        "execution_boundary": {
            "target_runtime_calls": 0,
            "filesystem_writes": 0,
            "subprocess_calls": 0,
            "network_calls": 0,
            "generated_artifact_body_write_count": 0,
            "execution_permission_count": 0,
        },
    }
    sanitized = sanitize_public_payload(read_model)
    _assert_projection_safe(sanitized)
    return sanitized


__all__ = [
    "TARGET_RUNTIME_OUTPUT_MANIFEST_DB_NAME",
    "TARGET_RUNTIME_OUTPUT_MANIFEST_EXPECTED_COLUMNS",
    "TARGET_RUNTIME_OUTPUT_MANIFEST_SCHEMA_VERSION",
    "InMemoryTargetRuntimeOutputManifestRepository",
    "SQLiteTargetRuntimeOutputManifestRepository",
    "SQLiteTargetRuntimeOutputManifestStore",
    "TargetRuntimeOutputManifestRecord",
    "TargetRuntimeOutputManifestRepository",
    "TargetRuntimeOutputManifestStoreUnavailableError",
    "target_runtime_output_manifest_public_read_model",
    "target_runtime_output_manifest_public_read_model_from_sqlite",
    "target_runtime_output_manifest_record_from_result",
]

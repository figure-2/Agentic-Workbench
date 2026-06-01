"""Provider envelope persistence and public read model.

This module persists sanitized provider request/response envelope projections
only. It stores contract hashes, counts, status, and labels; it never stores
raw prompts, provider bodies, provider payloads, or authorization material.
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
from packages.core.schemas import JsonDict, stable_contract_hash, utc_now

from .provider_boundary import CONTRACT_HASH_PATTERN, SOLAR_PRO_3_MODEL, SOLAR_PRO_3_PROVIDER
from .runner_provider import is_safe_run_id, safe_public_run_id
from .solar_contracts import SolarContractFixtureResult


PROVIDER_ENVELOPE_SCHEMA_VERSION = 1
PROVIDER_ENVELOPE_DB_NAME = "provider-envelopes.sqlite3"
PROVIDER_ENVELOPE_EXPECTED_TABLES = {
    "schema_migrations",
    "provider_envelopes",
}
PROVIDER_ENVELOPE_EXPECTED_COLUMNS = {
    "schema_migrations": {"version", "applied_at"},
    "provider_envelopes": {
        "envelope_id",
        "run_id",
        "provider_name",
        "model_name",
        "mode",
        "status",
        "request_contract_hash",
        "response_contract_hash",
        "prompt_contract_hash",
        "content_hash",
        "request_field_count",
        "response_field_count",
        "policy_check_count",
        "summary",
        "created_at",
    },
}


class ProviderEnvelopeStoreUnavailableError(RuntimeError):
    """Raised when provider envelope storage cannot be trusted."""


@dataclass(frozen=True, slots=True)
class ProviderEnvelopeRecord:
    """Hash-only provider request/response envelope projection."""

    envelope_id: str
    run_id: str
    provider_name: str
    model_name: str
    mode: str
    status: str
    request_contract_hash: str
    response_contract_hash: str
    prompt_contract_hash: str
    content_hash: str
    request_field_count: int
    response_field_count: int
    policy_check_count: int
    summary: str
    created_at: str

    def to_dict(self) -> JsonDict:
        return sanitize_public_payload(asdict(self))


class ProviderEnvelopeRepository(Protocol):
    """Repository contract for sanitized provider envelope records."""

    def save(self, record: ProviderEnvelopeRecord) -> ProviderEnvelopeRecord:
        ...

    def list_for_run(self, run_id: str) -> list[ProviderEnvelopeRecord]:
        ...


@dataclass(slots=True)
class InMemoryProviderEnvelopeRepository:
    """In-memory provider envelope repository for contract tests."""

    records: dict[str, ProviderEnvelopeRecord] = field(default_factory=dict)

    def save(self, record: ProviderEnvelopeRecord) -> ProviderEnvelopeRecord:
        _assert_record_safe(record)
        existing = self.records.get(record.envelope_id)
        if existing is not None and existing != record:
            raise ValueError("provider envelope id conflict")
        self.records[record.envelope_id] = record
        return record

    def list_for_run(self, run_id: str) -> list[ProviderEnvelopeRecord]:
        return sorted(
            (record for record in self.records.values() if record.run_id == run_id),
            key=lambda record: record.created_at,
        )


def _hash_valid(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


def _assert_projection_safe(value: JsonDict) -> None:
    public = sanitize_public_payload(value)
    if find_forbidden_public_keys(public):
        raise ValueError("provider envelope projection contains forbidden public keys")
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError("provider envelope projection contains forbidden claims")


def _assert_record_safe(record: ProviderEnvelopeRecord) -> None:
    if not is_safe_run_id(record.run_id):
        raise ValueError("provider envelope run_id is unsafe")
    if record.provider_name != SOLAR_PRO_3_PROVIDER:
        raise ValueError("provider envelope provider_name is unsupported")
    if record.model_name != SOLAR_PRO_3_MODEL:
        raise ValueError("provider envelope model_name is unsupported")
    if record.mode != "live":
        raise ValueError("provider envelope mode must be live")
    for field_name in (
        "request_contract_hash",
        "response_contract_hash",
        "prompt_contract_hash",
        "content_hash",
    ):
        if not _hash_valid(getattr(record, field_name)):
            raise ValueError(f"{field_name} must be a contract hash")
    if record.status not in {"projected_fixture", "blocked"}:
        raise ValueError("provider envelope status is unsupported")
    if record.request_field_count < 0 or record.response_field_count < 0:
        raise ValueError("provider envelope field counts must be non-negative")
    _assert_projection_safe(record.to_dict())


def provider_envelope_record_from_contract_result(
    result: SolarContractFixtureResult,
    *,
    created_at: str | None = None,
) -> ProviderEnvelopeRecord:
    """Convert a no-call Solar contract fixture result into a hash-only record."""
    if result.status != "projected_fixture":
        raise ValueError("provider envelope requires a projected fixture result")
    request_contract = result.request_contract
    response_projection = result.response_projection
    if not request_contract or not response_projection:
        raise ValueError("provider envelope requires request and response contracts")
    _assert_projection_safe(request_contract)
    _assert_projection_safe(response_projection)

    run_id = safe_public_run_id(str(request_contract.get("run_id", "")))
    request_contract_hash = str(request_contract.get("request_contract_hash", ""))
    response_contract_hash = str(response_projection.get("response_contract_hash", ""))
    prompt_contract_hash = str(request_contract.get("prompt_contract_hash", ""))
    content_hash = str(response_projection.get("content_hash", ""))
    envelope_id_hash = stable_contract_hash(
        {
            "run_id": run_id,
            "provider_name": request_contract.get("provider_name", SOLAR_PRO_3_PROVIDER),
            "model_name": request_contract.get("model_name", SOLAR_PRO_3_MODEL),
            "request_contract_hash": request_contract_hash,
            "response_contract_hash": response_contract_hash,
            "content_hash": content_hash,
        }
    )
    record = ProviderEnvelopeRecord(
        envelope_id=f"provider-envelope-{envelope_id_hash[:24]}",
        run_id=run_id,
        provider_name=str(request_contract.get("provider_name", SOLAR_PRO_3_PROVIDER)),
        model_name=str(request_contract.get("model_name", SOLAR_PRO_3_MODEL)),
        mode=str(request_contract.get("mode", "live")),
        status=result.status,
        request_contract_hash=request_contract_hash,
        response_contract_hash=response_contract_hash,
        prompt_contract_hash=prompt_contract_hash,
        content_hash=content_hash,
        request_field_count=len(request_contract),
        response_field_count=len(response_projection),
        policy_check_count=len(result.checks),
        summary="provider envelope hash-only projection",
        created_at=created_at or utc_now(),
    )
    _assert_record_safe(record)
    return record


class SQLiteProviderEnvelopeStore:
    """SQLite store for sanitized provider request/response envelope rows."""

    def __init__(self, root: str | Path, *, filename: str = PROVIDER_ENVELOPE_DB_NAME) -> None:
        self.root = Path(root)
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            self.path = resolve_within_root(self.root, filename)
            self._ensure_schema()
        except (OSError, ValueError, sqlite3.DatabaseError) as exc:
            raise ProviderEnvelopeStoreUnavailableError(
                "provider envelope sqlite store is unavailable"
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
            raise ProviderEnvelopeStoreUnavailableError(
                "provider envelope sqlite store is unavailable"
            ) from exc

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS provider_envelopes (
                    envelope_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    provider_name TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_contract_hash TEXT NOT NULL UNIQUE,
                    response_contract_hash TEXT NOT NULL UNIQUE,
                    prompt_contract_hash TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    request_field_count INTEGER NOT NULL,
                    response_field_count INTEGER NOT NULL,
                    policy_check_count INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_provider_envelopes_run_created
                    ON provider_envelopes(run_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_provider_envelopes_status_created
                    ON provider_envelopes(status, created_at);
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (PROVIDER_ENVELOPE_SCHEMA_VERSION, utc_now()),
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
            if not PROVIDER_ENVELOPE_EXPECTED_TABLES.issubset(tables):
                raise ProviderEnvelopeStoreUnavailableError(
                    "provider envelope sqlite schema is unavailable"
                )
            for table, expected_columns in PROVIDER_ENVELOPE_EXPECTED_COLUMNS.items():
                rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
                columns = {row["name"] for row in rows}
                if columns != expected_columns:
                    raise ProviderEnvelopeStoreUnavailableError(
                        "provider envelope sqlite schema is unavailable"
                    )

    def repository(self) -> "SQLiteProviderEnvelopeRepository":
        self._assert_schema()
        return SQLiteProviderEnvelopeRepository(self)


class SQLiteProviderEnvelopeRepository:
    """SQLite repository for sanitized provider envelope rows."""

    def __init__(self, store: SQLiteProviderEnvelopeStore) -> None:
        self.store = store

    def save(self, record: ProviderEnvelopeRecord) -> ProviderEnvelopeRecord:
        _assert_record_safe(record)
        with self.store._connect() as connection:
            self.store._assert_schema()
            try:
                connection.execute(
                    """
                    INSERT INTO provider_envelopes(
                        envelope_id,
                        run_id,
                        provider_name,
                        model_name,
                        mode,
                        status,
                        request_contract_hash,
                        response_contract_hash,
                        prompt_contract_hash,
                        content_hash,
                        request_field_count,
                        response_field_count,
                        policy_check_count,
                        summary,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.envelope_id,
                        record.run_id,
                        record.provider_name,
                        record.model_name,
                        record.mode,
                        record.status,
                        record.request_contract_hash,
                        record.response_contract_hash,
                        record.prompt_contract_hash,
                        record.content_hash,
                        record.request_field_count,
                        record.response_field_count,
                        record.policy_check_count,
                        record.summary,
                        record.created_at,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("provider envelope duplicate hash or id") from exc
            connection.commit()
        return record

    def list_for_run(self, run_id: str) -> list[ProviderEnvelopeRecord]:
        with self.store._connect() as connection:
            self.store._assert_schema()
            rows = connection.execute(
                """
                SELECT * FROM provider_envelopes
                WHERE run_id = ?
                ORDER BY created_at ASC, envelope_id ASC
                """,
                (run_id,),
            ).fetchall()
        return [self._record_from_row(row) for row in rows]

    def _record_from_row(self, row: sqlite3.Row) -> ProviderEnvelopeRecord:
        record = ProviderEnvelopeRecord(
            envelope_id=str(row["envelope_id"]),
            run_id=str(row["run_id"]),
            provider_name=str(row["provider_name"]),
            model_name=str(row["model_name"]),
            mode=str(row["mode"]),
            status=str(row["status"]),
            request_contract_hash=str(row["request_contract_hash"]),
            response_contract_hash=str(row["response_contract_hash"]),
            prompt_contract_hash=str(row["prompt_contract_hash"]),
            content_hash=str(row["content_hash"]),
            request_field_count=int(row["request_field_count"]),
            response_field_count=int(row["response_field_count"]),
            policy_check_count=int(row["policy_check_count"]),
            summary=str(row["summary"]),
            created_at=str(row["created_at"]),
        )
        _assert_record_safe(record)
        return record


def provider_envelope_public_read_model(
    repository: ProviderEnvelopeRepository,
    *,
    run_id: str,
) -> JsonDict:
    """Return a sanitized public read model for provider envelope rows."""
    try:
        records = repository.list_for_run(run_id)
    except Exception:
        return _blocked_provider_envelope_read_model(run_id)

    envelopes = [
        {
            "envelope_id": record.envelope_id,
            "status": record.status,
            "request_contract_hash": record.request_contract_hash,
            "response_contract_hash": record.response_contract_hash,
            "prompt_contract_hash": record.prompt_contract_hash,
            "content_hash": record.content_hash,
            "request_field_count": record.request_field_count,
            "response_field_count": record.response_field_count,
            "policy_check_count": record.policy_check_count,
        }
        for record in records
    ]
    read_model = {
        "projection_version": "provider-envelope-read-model-public-v1",
        "status": "available" if records else "not_found",
        "run_id": safe_public_run_id(run_id),
        "counts": {
            "provider_envelope_count": len(records),
            "request_contract_hash_count": len({record.request_contract_hash for record in records}),
            "response_contract_hash_count": len({record.response_contract_hash for record in records}),
        },
        "provider_envelopes": envelopes,
        "repository_boundary": {
            "provider_envelope_store": "available",
            "raw_row_returned": False,
            "root_path_returned": False,
        },
        "execution_boundary": {
            "sdk_imports": 0,
            "env_value_reads": 0,
            "api_calls": 0,
            "network_calls": 0,
        },
    }
    sanitized = sanitize_public_payload(read_model)
    _assert_projection_safe(sanitized)
    return sanitized


def provider_envelope_public_read_model_from_sqlite(
    root: str | Path,
    *,
    run_id: str,
    filename: str = PROVIDER_ENVELOPE_DB_NAME,
) -> JsonDict:
    """Return a blocked read model if the provider envelope store is unavailable."""
    try:
        store = SQLiteProviderEnvelopeStore(root=root, filename=filename)
        return provider_envelope_public_read_model(store.repository(), run_id=run_id)
    except Exception:
        return _blocked_provider_envelope_read_model(run_id)


def _blocked_provider_envelope_read_model(run_id: str) -> JsonDict:
    read_model = {
        "projection_version": "provider-envelope-read-model-public-v1",
        "status": "blocked",
        "run_id": safe_public_run_id(run_id),
        "counts": {
            "provider_envelope_count": 0,
            "request_contract_hash_count": 0,
            "response_contract_hash_count": 0,
        },
        "provider_envelopes": [],
        "repository_boundary": {
            "provider_envelope_store": "blocked",
            "raw_row_returned": False,
            "root_path_returned": False,
        },
        "execution_boundary": {
            "sdk_imports": 0,
            "env_value_reads": 0,
            "api_calls": 0,
            "network_calls": 0,
        },
    }
    sanitized = sanitize_public_payload(read_model)
    _assert_projection_safe(sanitized)
    return sanitized


__all__ = [
    "PROVIDER_ENVELOPE_DB_NAME",
    "PROVIDER_ENVELOPE_SCHEMA_VERSION",
    "InMemoryProviderEnvelopeRepository",
    "ProviderEnvelopeRecord",
    "ProviderEnvelopeRepository",
    "ProviderEnvelopeStoreUnavailableError",
    "SQLiteProviderEnvelopeRepository",
    "SQLiteProviderEnvelopeStore",
    "provider_envelope_public_read_model",
    "provider_envelope_public_read_model_from_sqlite",
    "provider_envelope_record_from_contract_result",
]

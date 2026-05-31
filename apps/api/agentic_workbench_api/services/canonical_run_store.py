"""Sanitized canonical run/artifact persistence for API paths.

This service stores and reads run-session state separately from runner/report
evidence and approval/replay evidence. It persists only public projections:
hashes, lifecycle state, artifact metadata, and counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.core.exposure import sanitize_public_payload
from packages.core.public_projection import assert_public_projection_safe
from packages.core.repositories import reconstruct_workflow_session_read_model
from packages.core.schemas import WorkflowSession
from packages.core.sqlite_repositories import SQLiteRunArtifactStore


CANONICAL_RUN_WRITE_PROJECTION_VERSION = "canonical-run-persistence-public-v1"
CANONICAL_RUN_READ_PROJECTION_VERSION = "canonical-run-read-model-public-v1"
CANONICAL_ARTIFACT_READ_PROJECTION_VERSION = "canonical-artifact-read-model-public-v1"
SAFE_RUN_ID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")


@dataclass(frozen=True, slots=True)
class RunArtifactRepositoryConfig:
    """Explicit local SQLite selection for canonical run/artifact rows."""

    root: str | Path | None = None
    relative_path: str | Path | None = None


@dataclass(slots=True)
class RunArtifactRepositoryProvider:
    """Server-side selector for canonical run/artifact repositories."""

    config: RunArtifactRepositoryConfig | None = None
    _cached_store: SQLiteRunArtifactStore | None = None

    @property
    def backend(self) -> str:
        return "sqlite" if self.config and self.config.root is not None else "unconfigured"

    @property
    def configured(self) -> bool:
        return self.backend == "sqlite"

    def store(self) -> SQLiteRunArtifactStore:
        if not self.config or self.config.root is None:
            raise ValueError("canonical run/artifact repository is not configured")
        if self._cached_store is None:
            self._cached_store = SQLiteRunArtifactStore(
                root=self.config.root,
                relative_path=self.config.relative_path or "agentic_workbench_runs.sqlite3",
            )
        return self._cached_store


def _safe_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    if not isinstance(public_payload, dict):
        raise ValueError("canonical run public payload must be a mapping")
    assert_public_projection_safe(public_payload)
    return public_payload


def _safe_run_id(run_id: str) -> str:
    if (
        not isinstance(run_id, str)
        or not 1 <= len(run_id) <= 81
        or not run_id[0].isalnum()
        or ".." in run_id
        or any(char not in SAFE_RUN_ID_CHARS for char in run_id)
    ):
        raise ValueError("run_id is not valid")
    return run_id


def _zero_execution_boundary(*, local_repository_write_count: int = 0) -> dict[str, int]:
    return {
        "provider_calls": 0,
        "live_api_calls": 0,
        "live_llm_calls": 0,
        "network_calls": 0,
        "subprocess_calls": 0,
        "filesystem_writes": 0,
        "target_runtime_calls": 0,
        "solar_provider_calls": 0,
        "local_run_artifact_repository_write_count": local_repository_write_count,
    }


def _repository_boundary(provider: RunArtifactRepositoryProvider) -> dict[str, object]:
    return {
        "run_artifact_backend": provider.backend,
        "runner_report_audit_backend": "not_queried",
        "approval_replay_backend": "not_queried",
        "evidence_db_queried": False,
        "approval_replay_db_queried": False,
        "root_path_returned": False,
        "raw_row_returned": False,
    }


def _claim_boundary() -> dict[str, bool]:
    return {
        "local_read_model_only": True,
        "canonical_run_state_claim": True,
        "external_provider_outcome": False,
        "target_runtime_outcome": False,
        "production_trust_claim": False,
    }


def _write_summary(
    *,
    run_id: str,
    provider: RunArtifactRepositoryProvider,
    status: str,
    checks: list[dict[str, object]],
    errors: list[str],
    counts: dict[str, int] | None = None,
    run: dict[str, object] | None = None,
    local_repository_write_count: int = 0,
) -> dict[str, Any]:
    return _safe_public_payload(
        {
            "projection_version": CANONICAL_RUN_WRITE_PROJECTION_VERSION,
            "run_id": run_id,
            "status": status,
            "runtime_mode": "fixture",
            "fixture_mode": True,
            "approval_lifecycle": "synthetic",
            "durable_user_approval": False,
            "repository_boundary": _repository_boundary(provider),
            "run": run or {},
            "counts": counts or {"run_session_count": 0, "artifact_count": 0},
            "checks": checks,
            "errors": errors,
            "execution_boundary": _zero_execution_boundary(
                local_repository_write_count=local_repository_write_count
            ),
            "claim_boundary": _claim_boundary(),
        }
    )


def _read_summary(
    *,
    projection_version: str,
    run_id: str,
    provider: RunArtifactRepositoryProvider,
    status: str,
    checks: list[dict[str, object]],
    errors: list[str],
    run: dict[str, object] | None = None,
    artifacts: list[dict[str, object]] | None = None,
) -> dict[str, Any]:
    artifact_rows = artifacts or []
    return _safe_public_payload(
        {
            "projection_version": projection_version,
            "run_id": run_id,
            "status": status,
            "runtime_mode": "read_model",
            "fixture_mode": False,
            "repository_boundary": _repository_boundary(provider),
            "run": run or {},
            "artifacts": artifact_rows,
            "counts": {
                "run_session_count": 1 if run else 0,
                "artifact_count": len(artifact_rows),
                "runner_plan_count": 0,
                "verification_report_count": 0,
                "audit_event_count": 0,
                "approval_subject_snapshot_count": 0,
                "approval_count": 0,
                "replay_nonce_count": 0,
            },
            "checks": checks,
            "errors": errors,
            "execution_boundary": _zero_execution_boundary(),
            "claim_boundary": _claim_boundary(),
        }
    )


def persist_canonical_run_session(
    session: WorkflowSession,
    *,
    run_repository_provider: RunArtifactRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Persist sanitized canonical run/session projections when configured."""
    selected_provider = run_repository_provider or RunArtifactRepositoryProvider()
    if not selected_provider.configured:
        return _write_summary(
            run_id=session.id,
            provider=selected_provider,
            status="skipped",
            checks=[{"name": "run_artifact_repository_configured", "passed": False}],
            errors=[],
        )

    try:
        store = selected_provider.store()
        run_record, artifact_records = store.save_session_with_artifacts(session)
        return _write_summary(
            run_id=session.id,
            provider=selected_provider,
            status="persisted",
            checks=[
                {"name": "run_artifact_repository_configured", "passed": True},
                {"name": "canonical_run_session_persisted", "passed": True},
                {"name": "evidence_repository_not_queried", "passed": True},
                {"name": "approval_replay_repository_not_queried", "passed": True},
            ],
            errors=[],
            counts={
                "run_session_count": 1,
                "artifact_count": len(artifact_records),
            },
            run=run_record.to_dict(),
            local_repository_write_count=1,
        )
    except Exception:
        return _write_summary(
            run_id=session.id,
            provider=selected_provider,
            status="blocked",
            checks=[
                {"name": "run_artifact_repository_configured", "passed": True},
                {"name": "canonical_run_session_persisted", "passed": False},
                {"name": "evidence_repository_not_queried", "passed": True},
                {"name": "approval_replay_repository_not_queried", "passed": True},
            ],
            errors=["canonical run/artifact repository is unavailable"],
        )


def read_canonical_run(
    run_id: str,
    *,
    run_repository_provider: RunArtifactRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Return one sanitized canonical run-session row plus artifact metadata."""
    safe_run_id = _safe_run_id(run_id)
    selected_provider = run_repository_provider or RunArtifactRepositoryProvider()
    checks: list[dict[str, object]] = []
    errors: list[str] = []
    status = "passed"
    run: dict[str, object] = {}
    artifacts: list[dict[str, object]] = []

    try:
        store = selected_provider.store()
        run_record = store.run_sessions().get(safe_run_id)
        checks.append({"name": "run_artifact_repository_available", "passed": True})
        checks.append({"name": "evidence_repository_not_queried", "passed": True})
        checks.append({"name": "approval_replay_repository_not_queried", "passed": True})
        if run_record is None:
            status = "not_found"
        else:
            artifact_records = store.artifacts().list_for_run(safe_run_id)
            read_model = reconstruct_workflow_session_read_model(run_record, artifact_records)
            run = {
                "run_id": read_model.run_id,
                "stage": read_model.stage,
                "status": read_model.status,
                "prompt_contract_hash": read_model.prompt_contract_hash,
                "idea_summary": read_model.idea_summary,
                "created_at": read_model.created_at,
                "updated_at": read_model.updated_at,
            }
            artifacts = [artifact.to_dict() for artifact in read_model.artifacts]
    except Exception:
        status = "blocked"
        errors.append("canonical run/artifact repository is unavailable")
        checks.append({"name": "run_artifact_repository_available", "passed": False})
        checks.append({"name": "evidence_repository_not_queried", "passed": True})
        checks.append({"name": "approval_replay_repository_not_queried", "passed": True})

    return _read_summary(
        projection_version=CANONICAL_RUN_READ_PROJECTION_VERSION,
        run_id=safe_run_id,
        provider=selected_provider,
        status=status,
        checks=checks,
        errors=errors,
        run=run,
        artifacts=artifacts,
    )


def read_canonical_artifacts(
    run_id: str,
    *,
    run_repository_provider: RunArtifactRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Return sanitized artifact projection rows for one canonical run."""
    safe_run_id = _safe_run_id(run_id)
    selected_provider = run_repository_provider or RunArtifactRepositoryProvider()
    checks: list[dict[str, object]] = []
    errors: list[str] = []
    status = "passed"
    run: dict[str, object] = {}
    artifacts: list[dict[str, object]] = []

    try:
        store = selected_provider.store()
        run_record = store.run_sessions().get(safe_run_id)
        checks.append({"name": "run_artifact_repository_available", "passed": True})
        checks.append({"name": "evidence_repository_not_queried", "passed": True})
        checks.append({"name": "approval_replay_repository_not_queried", "passed": True})
        if run_record is None:
            status = "not_found"
        else:
            artifact_records = store.artifacts().list_for_run(safe_run_id)
            run = run_record.to_dict()
            artifacts = [artifact.to_dict() for artifact in artifact_records]
    except Exception:
        status = "blocked"
        errors.append("canonical run/artifact repository is unavailable")
        checks.append({"name": "run_artifact_repository_available", "passed": False})
        checks.append({"name": "evidence_repository_not_queried", "passed": True})
        checks.append({"name": "approval_replay_repository_not_queried", "passed": True})

    return _read_summary(
        projection_version=CANONICAL_ARTIFACT_READ_PROJECTION_VERSION,
        run_id=safe_run_id,
        provider=selected_provider,
        status=status,
        checks=checks,
        errors=errors,
        run=run,
        artifacts=artifacts,
    )

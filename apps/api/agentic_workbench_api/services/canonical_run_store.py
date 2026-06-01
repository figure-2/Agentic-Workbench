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

from .admission_demo import AdmissionRepositoryProvider
from .evidence_read_model import EvidenceRepositoryProvider


CANONICAL_RUN_WRITE_PROJECTION_VERSION = "canonical-run-persistence-public-v1"
CANONICAL_RUN_READ_PROJECTION_VERSION = "canonical-run-read-model-public-v1"
CANONICAL_RUN_COMPOSED_READ_PROJECTION_VERSION = "canonical-run-composed-read-model-public-v1"
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
        "canonical_run_artifact_backend": provider.backend,
        "runner_report_audit_backend": "not_queried",
        "approval_replay_backend": "not_queried",
        "evidence_db_queried": False,
        "approval_replay_db_queried": False,
        "root_path_returned": False,
        "raw_row_returned": False,
    }


def _composed_repository_boundary(
    *,
    run_provider: RunArtifactRepositoryProvider,
    evidence_provider: EvidenceRepositoryProvider,
    admission_provider: AdmissionRepositoryProvider,
    evidence_db_queried: bool,
    approval_replay_db_queried: bool,
) -> dict[str, object]:
    return {
        "run_artifact_backend": run_provider.backend,
        "canonical_run_artifact_backend": run_provider.backend,
        "runner_report_audit_backend": evidence_provider.backend,
        "approval_replay_backend": (
            admission_provider.backend
            if admission_provider.config is not None
            else "not_queried_or_unconfigured"
        ),
        "evidence_db_queried": evidence_db_queried,
        "approval_replay_db_queried": approval_replay_db_queried,
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


def _empty_evidence_counts() -> dict[str, int]:
    return {
        "source_artifact_count": 0,
        "runner_plan_count": 0,
        "verification_report_count": 0,
        "audit_event_count": 0,
        "approval_subject_snapshot_count": 0,
        "approval_count": 0,
        "replay_nonce_count": 0,
    }


def _evidence_summary(
    *,
    run_id: str,
    evidence_provider: EvidenceRepositoryProvider,
    admission_provider: AdmissionRepositoryProvider,
) -> tuple[dict[str, Any], bool, bool]:
    counts = _empty_evidence_counts()
    checks: list[dict[str, object]] = []
    errors: list[str] = []
    status = "available"
    evidence_db_queried = False
    approval_replay_db_queried = False
    evidence_linkage_checked = False
    approval_linkage_checked = False

    if not evidence_provider.configured:
        status = "unconfigured"
        checks.append({"name": "runner_report_audit_repository_configured", "passed": False})
    else:
        evidence_db_queried = True
        try:
            store = evidence_provider.store()
            artifact_records = store.list_artifacts_for_run(run_id)
            runner_plan_records = store.runner_plans().list_for_run(run_id)
            verification_report_records = store.verification_reports().list_for_run(run_id)
            audit_event_records = store.audit_events().list_for_run(run_id)
            counts["source_artifact_count"] = len(artifact_records)
            counts["runner_plan_count"] = len(runner_plan_records)
            counts["verification_report_count"] = len(verification_report_records)
            counts["audit_event_count"] = len(audit_event_records)
            evidence_linkage_checked = True
            checks.append({"name": "runner_report_audit_repository_available", "passed": True})
            checks.append(
                {
                    "name": "runner_report_audit_run_id_linkage",
                    "passed": all(
                        record.run_id == run_id
                        for record in [
                            *artifact_records,
                            *runner_plan_records,
                            *verification_report_records,
                            *audit_event_records,
                        ]
                    ),
                }
            )
            if not any(
                (
                    artifact_records,
                    runner_plan_records,
                    verification_report_records,
                    audit_event_records,
                )
            ):
                status = "not_found"
        except Exception:
            status = "blocked"
            errors.append("runner/report/audit repository is unavailable")
            checks.append({"name": "runner_report_audit_repository_available", "passed": False})

    if admission_provider.config is None:
        checks.append({"name": "approval_replay_repository_configured", "passed": False})
    else:
        approval_replay_db_queried = True
        try:
            repositories = admission_provider.repositories()
            snapshots = repositories.approval_repository.list_snapshots_for_run(run_id)
            approvals = repositories.approval_repository.list_approvals_for_run(run_id)
            replay_nonces = repositories.replay_nonce_repository.list_records_for_run(run_id)
            counts["approval_subject_snapshot_count"] = len(snapshots)
            counts["approval_count"] = len(approvals)
            counts["replay_nonce_count"] = len(replay_nonces)
            approval_linkage_checked = True
            checks.append({"name": "approval_replay_repository_available", "passed": True})
            checks.append(
                {
                    "name": "approval_replay_run_id_linkage",
                    "passed": all(
                        record.run_id == run_id
                        for record in [*snapshots, *approvals, *replay_nonces]
                    ),
                }
            )
        except Exception:
            status = "blocked"
            errors.append("approval/replay repository is unavailable")
            checks.append({"name": "approval_replay_repository_available", "passed": False})

    summary = {
        "status": status,
        "counts": counts,
        "checks": checks,
        "errors": errors,
        "linkage": {
            "run_id": run_id,
            "run_id_matched": True,
            "artifact_linkage_checked": evidence_linkage_checked,
            "approval_replay_linkage_checked": approval_linkage_checked,
        },
        "repository_boundary": {
            "runner_report_audit_backend": evidence_provider.backend,
            "approval_replay_backend": (
                admission_provider.backend
                if admission_provider.config is not None
                else "not_queried_or_unconfigured"
            ),
            "evidence_db_queried": evidence_db_queried,
            "approval_replay_db_queried": approval_replay_db_queried,
            "root_path_returned": False,
            "raw_row_returned": False,
        },
    }
    return summary, evidence_db_queried, approval_replay_db_queried


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


def read_composed_canonical_run(
    run_id: str,
    *,
    run_repository_provider: RunArtifactRepositoryProvider | None = None,
    evidence_repository_provider: EvidenceRepositoryProvider | None = None,
    admission_repository_provider: AdmissionRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Return canonical run state plus optional sanitized evidence summary."""
    safe_run_id = _safe_run_id(run_id)
    selected_run_provider = run_repository_provider or RunArtifactRepositoryProvider()
    selected_evidence_provider = evidence_repository_provider or EvidenceRepositoryProvider()
    selected_admission_provider = admission_repository_provider or AdmissionRepositoryProvider()
    checks: list[dict[str, object]] = []
    errors: list[str] = []
    status = "passed"
    run: dict[str, object] = {}
    artifacts: list[dict[str, object]] = []
    evidence_summary: dict[str, Any] = {
        "status": "not_queried",
        "counts": _empty_evidence_counts(),
        "checks": [],
        "errors": [],
        "linkage": {
            "run_id": safe_run_id,
            "run_id_matched": True,
            "artifact_linkage_checked": False,
            "approval_replay_linkage_checked": False,
        },
        "repository_boundary": {
            "runner_report_audit_backend": selected_evidence_provider.backend,
            "approval_replay_backend": "not_queried_or_unconfigured",
            "evidence_db_queried": False,
            "approval_replay_db_queried": False,
            "root_path_returned": False,
            "raw_row_returned": False,
        },
    }
    evidence_db_queried = False
    approval_replay_db_queried = False

    try:
        store = selected_run_provider.store()
        run_record = store.run_sessions().get(safe_run_id)
        checks.append({"name": "run_artifact_repository_available", "passed": True})
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
            evidence_summary, evidence_db_queried, approval_replay_db_queried = _evidence_summary(
                run_id=safe_run_id,
                evidence_provider=selected_evidence_provider,
                admission_provider=selected_admission_provider,
            )
            checks.append(
                {
                    "name": "evidence_summary_not_raw_rows",
                    "passed": not evidence_summary["repository_boundary"]["raw_row_returned"],
                }
            )
    except Exception:
        status = "blocked"
        errors.append("canonical run/artifact repository is unavailable")
        checks.append({"name": "run_artifact_repository_available", "passed": False})

    artifact_rows = artifacts or []
    return _safe_public_payload(
        {
            "projection_version": CANONICAL_RUN_COMPOSED_READ_PROJECTION_VERSION,
            "run_id": safe_run_id,
            "status": status,
            "runtime_mode": "read_model",
            "fixture_mode": False,
            "repository_boundary": _composed_repository_boundary(
                run_provider=selected_run_provider,
                evidence_provider=selected_evidence_provider,
                admission_provider=selected_admission_provider,
                evidence_db_queried=evidence_db_queried,
                approval_replay_db_queried=approval_replay_db_queried,
            ),
            "run": run,
            "artifacts": artifact_rows,
            "evidence_summary": evidence_summary,
            "counts": {
                "run_session_count": 1 if run else 0,
                "artifact_count": len(artifact_rows),
                "runner_plan_count": int(evidence_summary["counts"]["runner_plan_count"]),
                "verification_report_count": int(
                    evidence_summary["counts"]["verification_report_count"]
                ),
                "audit_event_count": int(evidence_summary["counts"]["audit_event_count"]),
                "approval_subject_snapshot_count": int(
                    evidence_summary["counts"]["approval_subject_snapshot_count"]
                ),
                "approval_count": int(evidence_summary["counts"]["approval_count"]),
                "replay_nonce_count": int(evidence_summary["counts"]["replay_nonce_count"]),
            },
            "checks": checks,
            "errors": errors,
            "execution_boundary": _zero_execution_boundary(),
            "claim_boundary": _claim_boundary()
            | {
                "composed_evidence_summary": True,
                "evidence_raw_rows_returned": False,
                "live_observability_claim": False,
            },
        }
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

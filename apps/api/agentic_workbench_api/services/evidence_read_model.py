"""Sanitized API read model for persisted local evidence rows.

This service reads repository projections only. It does not run providers,
invoke DAACS, read environment values, or return raw bodies/logs/payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.core.approval_replay_factory import ApprovalReplayRepositoryConfig
from packages.core.exposure import sanitize_public_payload
from packages.core.public_projection import assert_public_projection_safe
from packages.core.sqlite_repositories import SQLiteRunnerReportAuditStore

from .admission_demo import AdmissionRepositoryProvider


EVIDENCE_PROJECTION_VERSION = "evidence-read-model-public-v1"
RUN_READ_PROJECTION_VERSION = "run-read-model-public-v1"
ARTIFACT_READ_PROJECTION_VERSION = "artifact-read-model-public-v1"
SAFE_RUN_ID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")


@dataclass(frozen=True, slots=True)
class EvidenceRepositoryConfig:
    """Explicit local SQLite selection for evidence read-model API paths."""

    root: str | Path | None = None
    relative_path: str | Path | None = None


@dataclass(slots=True)
class EvidenceRepositoryProvider:
    """Server-side selector for runner/report/audit evidence repositories."""

    config: EvidenceRepositoryConfig | None = None
    _cached_store: SQLiteRunnerReportAuditStore | None = None

    @property
    def backend(self) -> str:
        return "sqlite" if self.config and self.config.root is not None else "unconfigured"

    @property
    def configured(self) -> bool:
        return self.backend == "sqlite"

    def store(self) -> SQLiteRunnerReportAuditStore:
        if not self.config or self.config.root is None:
            raise ValueError("evidence repository is not configured")
        if self._cached_store is None:
            self._cached_store = SQLiteRunnerReportAuditStore(
                root=self.config.root,
                relative_path=self.config.relative_path or "agentic_workbench.sqlite3",
            )
        return self._cached_store


def _safe_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    if not isinstance(public_payload, dict):
        raise ValueError("evidence public payload must be a mapping")
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


def _record_dicts(records: list[object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in records:
        if hasattr(record, "to_dict"):
            row = record.to_dict()
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _empty_counts() -> dict[str, int]:
    return {
        "runner_plan_count": 0,
        "verification_report_count": 0,
        "audit_event_count": 0,
        "approval_subject_snapshot_count": 0,
        "approval_count": 0,
        "replay_nonce_count": 0,
    }


def _zero_execution_boundary() -> dict[str, int]:
    return {
        "provider_calls": 0,
        "live_api_calls": 0,
        "live_llm_calls": 0,
        "network_calls": 0,
        "subprocess_calls": 0,
        "filesystem_writes": 0,
        "target_runtime_calls": 0,
        "solar_provider_calls": 0,
    }


def _artifact_read_counts(
    *,
    artifact_count: int = 0,
    runner_plan_count: int = 0,
    verification_report_count: int = 0,
    audit_event_count: int = 0,
) -> dict[str, int]:
    return {
        "artifact_count": artifact_count,
        "runner_plan_count": runner_plan_count,
        "verification_report_count": verification_report_count,
        "audit_event_count": audit_event_count,
        "approval_subject_snapshot_count": 0,
        "approval_count": 0,
        "replay_nonce_count": 0,
    }


def _artifact_read_base_projection(
    *,
    projection_version: str,
    run_id: str,
    evidence_provider: EvidenceRepositoryProvider,
    status: str,
    checks: list[dict[str, object]],
    errors: list[str],
    counts: dict[str, int],
    artifacts: list[dict[str, object]] | None = None,
    runner_plans: list[dict[str, object]] | None = None,
    verification_reports: list[dict[str, object]] | None = None,
    audit_events: list[dict[str, object]] | None = None,
    include_artifacts: bool = True,
) -> dict[str, Any]:
    return _safe_public_payload(
        {
            "projection_version": projection_version,
            "run_id": run_id,
            "status": status,
            "runtime_mode": "read_model",
            "fixture_mode": False,
            "checks": checks,
            "errors": errors,
            "repository_boundary": {
                "runner_report_audit_backend": evidence_provider.backend,
                "run_session_backend": "not_implemented",
                "canonical_run_record_included": False,
                "artifact_linkage_projection_only": True,
                "approval_replay_backend": "not_queried",
                "approval_replay_included": False,
                "root_path_returned": False,
                "raw_row_returned": False,
            },
            "counts": counts,
            "artifacts": artifacts or [],
            "runner_plans": runner_plans or [],
            "verification_reports": verification_reports or [],
            "audit_events": audit_events or [],
            "execution_boundary": _zero_execution_boundary(),
            "claim_boundary": {
                "local_read_model_only": True,
                "artifact_projection_only": include_artifacts,
                "canonical_run_state_claim": False,
                "approval_replay_evidence_included": False,
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
                "production_trust_claim": False,
            },
        }
    )


def _base_projection(
    *,
    run_id: str,
    evidence_provider: EvidenceRepositoryProvider,
    admission_provider: AdmissionRepositoryProvider,
    status: str,
    checks: list[dict[str, object]],
    errors: list[str],
    counts: dict[str, int],
    runner_plans: list[dict[str, object]] | None = None,
    verification_reports: list[dict[str, object]] | None = None,
    audit_events: list[dict[str, object]] | None = None,
    approval_subject_snapshots: list[dict[str, object]] | None = None,
    approvals: list[dict[str, object]] | None = None,
    replay_nonces: list[dict[str, object]] | None = None,
) -> dict[str, Any]:
    return _safe_public_payload(
        {
            "projection_version": EVIDENCE_PROJECTION_VERSION,
            "run_id": run_id,
            "status": status,
            "runtime_mode": "read_model",
            "fixture_mode": False,
            "checks": checks,
            "errors": errors,
            "repository_boundary": {
                "runner_report_audit_backend": evidence_provider.backend,
                "approval_replay_backend": admission_provider.backend,
                "root_path_returned": False,
                "raw_row_returned": False,
            },
            "counts": counts,
            "runner_plans": runner_plans or [],
            "verification_reports": verification_reports or [],
            "audit_events": audit_events or [],
            "approval_subject_snapshots": approval_subject_snapshots or [],
            "approvals": approvals or [],
            "replay_nonces": replay_nonces or [],
            "execution_boundary": _zero_execution_boundary(),
            "claim_boundary": {
                "local_read_model_only": True,
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
                "production_trust_claim": False,
            },
        }
    )


def read_run_evidence(
    run_id: str,
    *,
    evidence_provider: EvidenceRepositoryProvider | None = None,
    admission_repository_provider: AdmissionRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Return sanitized stored evidence projections for one run."""
    safe_run_id = _safe_run_id(run_id)
    selected_evidence_provider = evidence_provider or EvidenceRepositoryProvider()
    selected_admission_provider = admission_repository_provider or AdmissionRepositoryProvider(
        ApprovalReplayRepositoryConfig()
    )
    checks: list[dict[str, object]] = []
    errors: list[str] = []
    counts = _empty_counts()
    runner_plans: list[dict[str, object]] = []
    verification_reports: list[dict[str, object]] = []
    audit_events: list[dict[str, object]] = []
    approval_subject_snapshots: list[dict[str, object]] = []
    approvals: list[dict[str, object]] = []
    replay_nonces: list[dict[str, object]] = []
    status = "passed"

    try:
        store = selected_evidence_provider.store()
        runner_plan_records = store.runner_plans().list_for_run(safe_run_id)
        verification_report_records = store.verification_reports().list_for_run(safe_run_id)
        audit_event_records = store.audit_events().list_for_run(safe_run_id)
        runner_plans = _record_dicts(runner_plan_records)
        verification_reports = _record_dicts(verification_report_records)
        audit_events = _record_dicts(audit_event_records)
        counts["runner_plan_count"] = len(runner_plans)
        counts["verification_report_count"] = len(verification_reports)
        counts["audit_event_count"] = len(audit_events)
        checks.append({"name": "runner_report_audit_repository_available", "passed": True})
    except Exception:
        status = "blocked"
        errors.append("runner/report/audit repository is unavailable")
        checks.append({"name": "runner_report_audit_repository_available", "passed": False})

    try:
        repositories = selected_admission_provider.repositories()
        approval_repository = repositories.approval_repository
        replay_repository = repositories.replay_nonce_repository
        snapshot_records = approval_repository.list_snapshots_for_run(safe_run_id)
        approval_records = approval_repository.list_approvals_for_run(safe_run_id)
        replay_records = replay_repository.list_records_for_run(safe_run_id)
        approval_subject_snapshots = _record_dicts(snapshot_records)
        approvals = _record_dicts(approval_records)
        replay_nonces = _record_dicts(replay_records)
        counts["approval_subject_snapshot_count"] = len(approval_subject_snapshots)
        counts["approval_count"] = len(approvals)
        counts["replay_nonce_count"] = len(replay_nonces)
        checks.append({"name": "approval_replay_repository_available", "passed": True})
    except Exception:
        status = "blocked"
        errors.append("approval/replay repository is unavailable")
        checks.append({"name": "approval_replay_repository_available", "passed": False})

    return _base_projection(
        run_id=safe_run_id,
        evidence_provider=selected_evidence_provider,
        admission_provider=selected_admission_provider,
        status=status,
        checks=checks,
        errors=errors,
        counts=counts,
        runner_plans=runner_plans,
        verification_reports=verification_reports,
        audit_events=audit_events,
        approval_subject_snapshots=approval_subject_snapshots,
        approvals=approvals,
        replay_nonces=replay_nonces,
    )


def read_run_artifacts(
    run_id: str,
    *,
    evidence_provider: EvidenceRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Return sanitized artifact projection rows for one run."""
    safe_run_id = _safe_run_id(run_id)
    selected_evidence_provider = evidence_provider or EvidenceRepositoryProvider()
    checks: list[dict[str, object]] = []
    errors: list[str] = []
    artifacts: list[dict[str, object]] = []
    counts = _artifact_read_counts()
    status = "passed"

    try:
        store = selected_evidence_provider.store()
        artifact_records = store.list_artifacts_for_run(safe_run_id)
        artifacts = _record_dicts(artifact_records)
        counts["artifact_count"] = len(artifacts)
        checks.append({"name": "artifact_repository_available", "passed": True})
        checks.append({"name": "approval_replay_repository_not_queried", "passed": True})
        if not artifacts:
            status = "not_found"
    except Exception:
        status = "blocked"
        errors.append("artifact repository is unavailable")
        checks.append({"name": "artifact_repository_available", "passed": False})
        checks.append({"name": "approval_replay_repository_not_queried", "passed": True})

    return _artifact_read_base_projection(
        projection_version=ARTIFACT_READ_PROJECTION_VERSION,
        run_id=safe_run_id,
        evidence_provider=selected_evidence_provider,
        status=status,
        checks=checks,
        errors=errors,
        counts=counts,
        artifacts=artifacts,
    )


def read_run_summary(
    run_id: str,
    *,
    evidence_provider: EvidenceRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Return a sanitized repository-backed run summary without raw artifact bodies."""
    safe_run_id = _safe_run_id(run_id)
    selected_evidence_provider = evidence_provider or EvidenceRepositoryProvider()
    checks: list[dict[str, object]] = []
    errors: list[str] = []
    artifacts: list[dict[str, object]] = []
    runner_plans: list[dict[str, object]] = []
    verification_reports: list[dict[str, object]] = []
    audit_events: list[dict[str, object]] = []
    counts = _artifact_read_counts()
    status = "passed"

    try:
        store = selected_evidence_provider.store()
        artifact_records = store.list_artifacts_for_run(safe_run_id)
        runner_plan_records = store.runner_plans().list_for_run(safe_run_id)
        verification_report_records = store.verification_reports().list_for_run(safe_run_id)
        audit_event_records = store.audit_events().list_for_run(safe_run_id)
        artifacts = _record_dicts(artifact_records)
        runner_plans = _record_dicts(runner_plan_records)
        verification_reports = _record_dicts(verification_report_records)
        audit_events = _record_dicts(audit_event_records)
        counts = _artifact_read_counts(
            artifact_count=len(artifacts),
            runner_plan_count=len(runner_plans),
            verification_report_count=len(verification_reports),
            audit_event_count=len(audit_events),
        )
        checks.append({"name": "runner_report_audit_repository_available", "passed": True})
        checks.append({"name": "approval_replay_repository_not_queried", "passed": True})
        if not artifacts and not runner_plans and not verification_reports and not audit_events:
            status = "not_found"
    except Exception:
        status = "blocked"
        errors.append("runner/report/audit repository is unavailable")
        checks.append({"name": "runner_report_audit_repository_available", "passed": False})
        checks.append({"name": "approval_replay_repository_not_queried", "passed": True})

    return _artifact_read_base_projection(
        projection_version=RUN_READ_PROJECTION_VERSION,
        run_id=safe_run_id,
        evidence_provider=selected_evidence_provider,
        status=status,
        checks=checks,
        errors=errors,
        counts=counts,
        artifacts=artifacts,
        runner_plans=runner_plans,
        verification_reports=verification_reports,
        audit_events=audit_events,
        include_artifacts=True,
    )

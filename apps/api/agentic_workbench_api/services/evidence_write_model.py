"""Sanitized write path for fixture evidence projections.

This service persists only local fixture/dry-run evidence projections. It does
not persist raw prompts, raw artifact bodies, provider payloads, approval auth
material, or invoke live providers/runtimes.
"""

from __future__ import annotations

from typing import Any

from packages.core.exposure import sanitize_public_payload
from packages.core.public_projection import assert_public_projection_safe
from packages.core.repositories import (
    artifact_record_from_artifact,
    audit_event_record_from_event,
    runner_plan_record_from_plan,
    validate_runner_report_audit_linkage,
    verification_report_record_from_report,
)
from packages.core.schemas import (
    Artifact,
    ArtifactKind,
    BuildSpec,
    ImplementationBrief,
    PRDPackage,
    SpecApproval,
    WorkflowSession,
)
from packages.daacs_builder.adapters import build_spec_to_daacs_initial_state
from packages.daacs_builder.dry_run_runner import DAACSDryRunRunner, ZERO_DRY_RUN_SIDE_EFFECTS

from .evidence_read_model import EvidenceRepositoryProvider


EVIDENCE_WRITE_PROJECTION_VERSION = "fixture-evidence-persistence-public-v1"


def _safe_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    if not isinstance(public_payload, dict):
        raise ValueError("fixture evidence public payload must be a mapping")
    assert_public_projection_safe(public_payload)
    return public_payload


def _zero_runtime_boundary(*, local_repository_write_count: int) -> dict[str, int]:
    return {
        "provider_calls": 0,
        "live_api_calls": 0,
        "live_llm_calls": 0,
        "network_calls": 0,
        "subprocess_calls": 0,
        "target_runtime_calls": 0,
        "solar_provider_calls": 0,
        "local_evidence_repository_write_count": local_repository_write_count,
    }


def _summary(
    *,
    run_id: str,
    backend: str,
    status: str,
    checks: list[dict[str, object]],
    errors: list[str],
    counts: dict[str, int] | None = None,
    hashes: dict[str, str] | None = None,
    local_repository_write_count: int = 0,
) -> dict[str, Any]:
    return _safe_public_payload(
        {
            "projection_version": EVIDENCE_WRITE_PROJECTION_VERSION,
            "run_id": run_id,
            "status": status,
            "runtime_mode": "fixture",
            "fixture_mode": True,
            "approval_lifecycle": "synthetic",
            "durable_user_approval": False,
            "repository_boundary": {
                "runner_report_audit_backend": backend,
                "root_path_returned": False,
                "raw_row_returned": False,
                "writes_fixture_projection_only": True,
            },
            "counts": counts
            or {
                "artifact_count": 0,
                "runner_plan_count": 0,
                "verification_report_count": 0,
                "audit_event_count": 0,
            },
            "hashes": hashes or {},
            "checks": checks,
            "errors": errors,
            "execution_boundary": _zero_runtime_boundary(
                local_repository_write_count=local_repository_write_count
            ),
            "claim_boundary": {
                "local_fixture_evidence_only": True,
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
                "production_trust_claim": False,
            },
        }
    )


def _first_artifact(session: WorkflowSession, kind: ArtifactKind) -> Artifact:
    for artifact in session.artifacts:
        if artifact.kind == kind:
            return artifact
    raise ValueError(f"{kind.value} artifact is required")


def _contract_bundle_from_session(
    session: WorkflowSession,
) -> tuple[BuildSpec, ImplementationBrief, SpecApproval, str]:
    build_artifact = _first_artifact(session, ArtifactKind.BUILD_SPEC)
    brief_artifact = _first_artifact(session, ArtifactKind.IMPLEMENTATION_BRIEF)
    approval_artifact = _first_artifact(session, ArtifactKind.SPEC_APPROVAL)
    build_payload = build_artifact.payload
    brief_payload = brief_artifact.payload
    approval_payload = approval_artifact.payload
    if not isinstance(build_payload, dict):
        raise ValueError("build spec payload is invalid")
    if not isinstance(brief_payload, dict):
        raise ValueError("implementation brief payload is invalid")
    if not isinstance(approval_payload, dict):
        raise ValueError("spec approval payload is invalid")
    prd_payload = brief_payload.get("prd_package")
    if not isinstance(prd_payload, dict):
        raise ValueError("implementation brief PRD package payload is invalid")

    build_spec = BuildSpec(**build_payload)
    prd_package = PRDPackage(**prd_payload)
    brief_fields = dict(brief_payload)
    brief_fields.pop("brief_hash", None)
    brief_fields["prd_package"] = prd_package
    implementation_brief = ImplementationBrief(**brief_fields)
    spec_approval = SpecApproval(**approval_payload)
    return build_spec, implementation_brief, spec_approval, brief_artifact.id


def _dry_run_evidence_from_session(session: WorkflowSession):
    build_spec, implementation_brief, spec_approval, source_artifact_id = _contract_bundle_from_session(session)
    state = build_spec_to_daacs_initial_state(
        build_spec,
        run_id=session.id,
        implementation_brief=implementation_brief,
        approval=spec_approval,
        require_approval=True,
    )
    plan, report = DAACSDryRunRunner().run(
        run_id=session.id,
        state=state,
        implementation_brief=implementation_brief,
        approval=spec_approval,
    )
    if plan is None or not report.passed:
        raise ValueError("fixture dry-run evidence could not be created")
    return plan, report, source_artifact_id


def persist_fixture_run_evidence(
    session: WorkflowSession,
    events: list[dict[str, Any]],
    *,
    evidence_provider: EvidenceRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Persist sanitized fixture runner/report/audit projections when configured."""
    selected_provider = evidence_provider or EvidenceRepositoryProvider()
    if not selected_provider.configured:
        return _summary(
            run_id=session.id,
            backend=selected_provider.backend,
            status="skipped",
            checks=[{"name": "evidence_repository_configured", "passed": False}],
            errors=[],
        )

    try:
        store = selected_provider.store()
        artifact_records = [artifact_record_from_artifact(artifact) for artifact in session.artifacts]
        plan, report, source_artifact_id = _dry_run_evidence_from_session(session)
        plan_record = runner_plan_record_from_plan(
            plan,
            source_artifact_id=source_artifact_id,
        )
        report_record = verification_report_record_from_report(
            report,
            source_artifact_id=source_artifact_id,
            runner_plan_hash=plan_record.plan_hash,
        )
        audit_source_artifact_id = source_artifact_id
        dry_run_event = {
            "event": "dry_run_planned",
            "run_id": session.id,
            "stage": "build",
            "source": "fixture_evidence_write_model",
            "level": "info",
            "message": "Fixture evidence dry-run plan projected",
            "payload": {"side_effects": ZERO_DRY_RUN_SIDE_EFFECTS},
        }
        audit_records = [
            audit_event_record_from_event(
                event,
                source_artifact_id=audit_source_artifact_id,
                linked_plan_hash=plan_record.plan_hash,
                linked_report_hash=report_record.report_hash,
            )
            for event in [*events, dry_run_event]
        ]
        linkage = validate_runner_report_audit_linkage(
            run_id=session.id,
            runner_plans=[plan_record],
            verification_reports=[report_record],
            audit_events=audit_records,
            artifacts=artifact_records,
        )
        store.save_records_atomically(
            artifacts=artifact_records,
            runner_plans=[plan_record],
            verification_reports=[report_record],
            audit_events=audit_records,
        )
        return _summary(
            run_id=session.id,
            backend=selected_provider.backend,
            status="persisted",
            checks=[
                {"name": "evidence_repository_configured", "passed": True},
                {"name": "fixture_projection_persisted", "passed": True},
                {"name": "runner_report_audit_linkage_valid", "passed": True},
            ],
            errors=[],
            counts={
                "artifact_count": len(artifact_records),
                "runner_plan_count": 1,
                "verification_report_count": 1,
                "audit_event_count": len(audit_records),
                "run_id_linked": int(linkage["run_id_linked"]),
            },
            hashes={
                "runner_plan_hash": plan_record.plan_hash,
                "verification_report_hash": report_record.report_hash,
            },
            local_repository_write_count=1,
        )
    except Exception:
        return _summary(
            run_id=session.id,
            backend=selected_provider.backend,
            status="blocked",
            checks=[
                {"name": "evidence_repository_configured", "passed": True},
                {"name": "fixture_projection_persisted", "passed": False},
            ],
            errors=["runner/report/audit repository is unavailable"],
        )

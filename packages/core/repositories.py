"""Persistence boundary skeleton for run sessions and artifacts.

The first repository layer stores read-model projections only. It deliberately
does not persist raw prompts, raw request bodies, raw artifact payloads, logs,
provider responses, or generated file bodies.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Protocol
from uuid import uuid4

from .claims import find_forbidden_claims
from .exposure import find_forbidden_public_keys, sanitize_public_payload
from .pathing import normalize_public_relative_path, resolve_within_root
from .schemas import Artifact, VerificationReport, WorkflowSession, stable_contract_hash, utc_now
from .security import redact_secrets


APPROVAL_TYPES = {"spec_approval", "live_runner_approval", "provider_approval"}
REPLAY_APPROVAL_TYPES = {"live_runner_approval", "provider_approval"}
LIFECYCLE_CLASSES = {"fixture", "synthetic", "durable"}
CONTRACT_HASH_LENGTH = 64
SAFE_REPLAY_RUN_ID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")
SAFE_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")
UNSAFE_LABEL_TERMS = ("raw", "secret", "token", "body", "payload", "prompt", "content", "log")


@dataclass(frozen=True, slots=True)
class RunSessionRecord:
    """Sanitized durable projection for a workflow session."""

    run_id: str
    stage: str
    status: str
    prompt_contract_hash: str
    idea_summary: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    """Sanitized durable projection for an artifact."""

    artifact_id: str
    run_id: str
    kind: str
    name: str
    path: str | None
    content_hash: str
    payload_field_count: int
    summary: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ApprovalSubjectSnapshotRecord:
    """Immutable sanitized projection of the subject a user approved."""

    subject_snapshot_id: str
    approval_type: str
    snapshot_schema_version: str
    subject_schema_version: str
    lifecycle_class: str
    run_id: str
    subject_kind: str
    source_artifact_ids: tuple[str, ...]
    subject_hash: str
    subject_hashes: dict[str, str]
    scope_canonical: str
    sanitized_summary: str
    visible_field_counts: dict[str, int]
    snapshot_hash: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return sanitize_public_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ApprovalDecisionRecord:
    """Immutable approval decision row linked to a subject snapshot."""

    approval_id: str
    approval_type: str
    snapshot_schema_version: str
    subject_schema_version: str
    lifecycle_class: str
    run_id: str
    subject_snapshot_id: str
    subject_hash: str
    scope_canonical: str
    decision: str
    approval_hash: str
    approved_by_ref: str
    approver_role: str
    approved_at: str
    expires_at: str
    policy_id_ref: str
    key_identity_ref: str
    audit_log_id: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return sanitize_public_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class ReplayNonceRecord:
    """Hash-only replay claim tombstone."""

    scope_canonical: str
    nonce_hash: str
    approval_hash: str
    run_id: str
    approval_type: str
    claimed_at: str
    expires_at: str
    status: str = "claimed"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RunnerPlanRecord:
    """Sanitized durable projection of a dry-run runner plan."""

    plan_id: str
    run_id: str
    mode: str
    plan_hash: str
    implementation_brief_hash: str
    build_spec_hash: str
    source_artifact_id: str
    planned_action_count: int
    action_role_counts: dict[str, int]
    artifact_manifest_count: int
    required_approval_count: int
    side_effect_count: int
    side_effects_zero: bool
    payload_hash: str
    payload_field_count: int
    visible_field_counts: dict[str, int]
    summary: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return sanitize_public_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class VerificationReportRecord:
    """Sanitized durable projection of a verification report."""

    report_id: str
    run_id: str
    mode: str
    source_artifact_id: str
    runner_plan_hash: str
    report_hash: str
    passed: bool
    check_count: int
    failed_check_count: int
    error_count: int
    generated_file_count: int
    metric_count: int
    metric_keys: tuple[str, ...]
    checks_hash: str
    errors_hash: str
    metrics_hash: str
    generated_files_hash: str
    visible_field_counts: dict[str, int]
    summary: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return sanitize_public_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class AuditEventRecord:
    """Sanitized durable projection of an audit event."""

    audit_event_id: str
    run_id: str
    event_type: str
    source: str
    stage: str
    level: str
    source_artifact_id: str
    linked_plan_hash: str
    linked_report_hash: str
    message_hash: str
    payload_hash: str
    payload_field_count: int
    visible_field_counts: dict[str, int]
    summary: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return sanitize_public_payload(asdict(self))


class ReplayNonceReplayError(ValueError):
    """Raised when a replay nonce has already been claimed."""


class ReplayStoreUnavailableError(RuntimeError):
    """Raised when the replay store cannot be trusted."""


@dataclass(frozen=True, slots=True)
class WorkflowSessionReadModel:
    """Read model reconstructed from sanitized repository rows."""

    run_id: str
    stage: str
    status: str
    prompt_contract_hash: str
    idea_summary: str
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["artifacts"] = [artifact.to_dict() for artifact in self.artifacts]
        return data


class RunSessionRepository(Protocol):
    """Repository contract for sanitized run-session records."""

    def save(self, session: WorkflowSession) -> RunSessionRecord:
        ...

    def get(self, run_id: str) -> RunSessionRecord | None:
        ...


class ArtifactRepository(Protocol):
    """Repository contract for sanitized artifact records."""

    def save(self, artifact: Artifact) -> ArtifactRecord:
        ...

    def list_for_run(self, run_id: str) -> list[ArtifactRecord]:
        ...


class ApprovalRepository(Protocol):
    """Repository contract for sanitized approval subject and decision rows."""

    def save_subject_snapshot(
        self,
        *,
        approval_type: str,
        run_id: str,
        subject_kind: str,
        subject: dict[str, object],
        subject_schema_version: str,
        source_artifact_ids: list[str] | tuple[str, ...] = (),
        lifecycle_class: str = "durable",
        scope_canonical: str = "",
        sanitized_summary: str = "",
        created_at: str | None = None,
    ) -> ApprovalSubjectSnapshotRecord:
        ...

    def save_approval(
        self,
        *,
        approval_id: str,
        snapshot: ApprovalSubjectSnapshotRecord,
        decision: str,
        approved_by_ref: str,
        approver_role: str,
        approved_at: str,
        expires_at: str = "",
        policy_id_ref: str = "",
        key_identity_ref: str = "",
        audit_log_id: str = "",
        lifecycle_class: str | None = None,
        created_at: str | None = None,
    ) -> ApprovalDecisionRecord:
        ...

    def get_snapshot(self, subject_snapshot_id: str) -> ApprovalSubjectSnapshotRecord | None:
        ...

    def get_approval(self, approval_id: str) -> ApprovalDecisionRecord | None:
        ...


class ReplayNonceRepository(Protocol):
    """Repository contract for hash-only replay nonce tombstones."""

    def claim(
        self,
        *,
        scope_canonical: str,
        nonce: str,
        approval_hash: str,
        run_id: str,
        approval_type: str,
        expires_at: str,
        claimed_at: str | None = None,
    ) -> ReplayNonceRecord:
        ...

    def list_records(self) -> list[ReplayNonceRecord]:
        ...


class RunnerPlanRepository(Protocol):
    """Repository contract for sanitized runner-plan records."""

    def save(self, plan: object, *, source_artifact_id: str = "") -> RunnerPlanRecord:
        ...

    def get(self, plan_hash: str) -> RunnerPlanRecord | None:
        ...

    def list_for_run(self, run_id: str) -> list[RunnerPlanRecord]:
        ...


class VerificationReportRepository(Protocol):
    """Repository contract for sanitized verification report records."""

    def save(
        self,
        report: VerificationReport,
        *,
        source_artifact_id: str = "",
        runner_plan_hash: str = "",
    ) -> VerificationReportRecord:
        ...

    def get(self, report_hash: str) -> VerificationReportRecord | None:
        ...

    def list_for_run(self, run_id: str) -> list[VerificationReportRecord]:
        ...


class AuditEventRepository(Protocol):
    """Repository contract for sanitized audit-event records."""

    def save(
        self,
        event: object,
        *,
        source_artifact_id: str = "",
        linked_plan_hash: str = "",
        linked_report_hash: str = "",
    ) -> AuditEventRecord:
        ...

    def list_for_run(self, run_id: str) -> list[AuditEventRecord]:
        ...


def idea_summary_for_storage(session: WorkflowSession) -> str:
    """Return a non-prompt summary safe enough for a read model."""
    idea = session.idea
    parts: list[str] = []
    if idea.product_type:
        parts.append(f"product_type={redact_secrets(idea.product_type)}")
    if idea.target_user:
        parts.append(f"target_user={redact_secrets(idea.target_user)}")
    if idea.constraints:
        parts.append(f"constraints={len(idea.constraints)}")
    if idea.success_criteria:
        parts.append(f"success_criteria={len(idea.success_criteria)}")
    if not parts:
        return "idea captured; raw prompt omitted"
    return "; ".join(str(part) for part in parts)


def run_session_record_from_session(session: WorkflowSession) -> RunSessionRecord:
    """Project a workflow session into a raw-prompt-free storage row."""
    session.idea.validate()
    prompt_contract_hash = stable_contract_hash(session.idea.to_dict())
    return RunSessionRecord(
        run_id=session.id,
        stage=session.stage.value,
        status=session.stage.value,
        prompt_contract_hash=prompt_contract_hash,
        idea_summary=idea_summary_for_storage(session),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _payload_field_count(payload: object) -> int:
    if isinstance(payload, dict):
        return len(payload)
    if isinstance(payload, list | tuple):
        return len(payload)
    return 0 if payload in (None, "") else 1


def artifact_record_from_artifact(artifact: Artifact) -> ArtifactRecord:
    """Project an artifact into metadata and correlation hashes only."""
    public_artifact = artifact.to_dict()
    public_payload = sanitize_public_payload(public_artifact.get("payload", {}))
    path = normalize_public_relative_path(artifact.path) if artifact.path else None
    payload_field_count = _payload_field_count(public_payload)
    kind = str(public_artifact["kind"])
    name = str(redact_secrets(public_artifact["name"]))
    return ArtifactRecord(
        artifact_id=str(public_artifact["id"]),
        run_id=str(public_artifact["run_id"]),
        kind=kind,
        name=name,
        path=path,
        content_hash=stable_contract_hash(public_artifact),
        payload_field_count=payload_field_count,
        summary=f"{kind}:{name}; payload_fields={payload_field_count}",
        created_at=str(public_artifact["created_at"]),
    )


def _payload_from_object(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return dict(value)
    if is_dataclass(value):
        payload = asdict(value)
        return payload if isinstance(payload, dict) else {}
    if hasattr(value, "to_dict"):
        payload = value.to_dict()
        return payload if isinstance(payload, dict) else {}
    if hasattr(value, "model_dump"):
        payload = value.model_dump()
        return payload if isinstance(payload, dict) else {}
    if hasattr(value, "dict"):
        payload = value.dict()
        return payload if isinstance(payload, dict) else {}
    return {}


def _public_dict(payload: dict[str, object], *, label: str) -> dict[str, object]:
    sanitized = sanitize_public_payload(payload)
    if not isinstance(sanitized, dict):
        raise ValueError(f"{label} payload must be a mapping")
    return sanitized


def _visible_projection_counts(raw_payload: dict[str, object], public_payload: dict[str, object]) -> dict[str, int]:
    return {
        "raw_top_level_fields": len(raw_payload),
        "public_top_level_fields": len(public_payload),
        "forbidden_public_key_count": len(find_forbidden_public_keys(raw_payload)),
    }


def _role_counts(actions: object) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not isinstance(actions, list):
        return counts
    for action in actions:
        if not isinstance(action, dict):
            continue
        role = _safe_label(action.get("role"), fallback="task")
        counts[role] = counts.get(role, 0) + 1
    return dict(sorted(counts.items()))


def _safe_label(value: object, *, fallback: str) -> str:
    text = str(redact_secrets(value or "")).strip()
    if not text:
        return fallback
    if find_forbidden_claims(text):
        return fallback
    lowered = text.lower()
    if any(term in lowered for term in UNSAFE_LABEL_TERMS):
        return fallback
    if not SAFE_LABEL_PATTERN.fullmatch(text):
        return fallback
    return text


def _safe_reference(value: object) -> str:
    return _safe_label(value, fallback="")


def _safe_contract_hash_reference(value: object, *, label: str) -> str:
    text = str(redact_secrets(value or "")).strip()
    if not text:
        return ""
    if _is_contract_hash(text):
        return text
    raise ValueError(f"{label} must be a contract hash")


def _required_contract_hash_reference(value: object, *, label: str) -> str:
    text = _safe_contract_hash_reference(value, label=label)
    if not text:
        raise ValueError(f"{label} is required")
    return text


def runner_plan_record_from_plan(
    plan: object,
    *,
    source_artifact_id: str = "",
) -> RunnerPlanRecord:
    """Project a RunnerPlan into counts and hashes only."""
    if hasattr(plan, "validate"):
        plan.validate()
    raw_payload = _payload_from_object(plan)
    public_payload = _public_dict(plan.to_dict() if hasattr(plan, "to_dict") else raw_payload, label="runner plan")
    plan_hash = (
        _safe_contract_hash_reference(public_payload.get("plan_hash"), label="plan_hash")
        or stable_contract_hash(public_payload)
    )
    planned_actions = public_payload.get("planned_actions") if isinstance(public_payload.get("planned_actions"), list) else []
    artifact_manifest = (
        public_payload.get("artifact_manifest") if isinstance(public_payload.get("artifact_manifest"), list) else []
    )
    required_approvals = (
        public_payload.get("required_approvals") if isinstance(public_payload.get("required_approvals"), list) else []
    )
    side_effects = public_payload.get("side_effects") if isinstance(public_payload.get("side_effects"), dict) else {}
    side_effect_count = len(side_effects)
    side_effects_zero = all(value == 0 for value in side_effects.values())
    if not side_effects_zero:
        raise ValueError("runner plan repository only accepts zero-side-effect dry-run plans")
    run_id = str(public_payload.get("run_id") or "")
    if not run_id:
        raise ValueError("runner plan run_id is required")
    mode = _safe_label(public_payload.get("mode"), fallback="unknown")
    summary = (
        f"runner_plan:{mode}; "
        f"actions={len(planned_actions)}; artifacts={len(artifact_manifest)}; "
        f"approvals={len(required_approvals)}"
    )
    return RunnerPlanRecord(
        plan_id=f"plan-{plan_hash[:12]}",
        run_id=run_id,
        mode=mode,
        plan_hash=plan_hash,
        implementation_brief_hash=_required_contract_hash_reference(
            public_payload.get("implementation_brief_hash"),
            label="implementation_brief_hash",
        ),
        build_spec_hash=_required_contract_hash_reference(
            public_payload.get("build_spec_hash"),
            label="build_spec_hash",
        ),
        source_artifact_id=_safe_reference(source_artifact_id),
        planned_action_count=len(planned_actions),
        action_role_counts=_role_counts(planned_actions),
        artifact_manifest_count=len(artifact_manifest),
        required_approval_count=len(required_approvals),
        side_effect_count=side_effect_count,
        side_effects_zero=side_effects_zero,
        payload_hash=stable_contract_hash(public_payload),
        payload_field_count=_payload_field_count(public_payload),
        visible_field_counts=_visible_projection_counts(raw_payload, public_payload),
        summary=summary,
        created_at=str(public_payload.get("created_at") or utc_now()),
    )


def verification_report_record_from_report(
    report: VerificationReport,
    *,
    source_artifact_id: str = "",
    runner_plan_hash: str = "",
) -> VerificationReportRecord:
    """Project a VerificationReport into counts and hashes only."""
    raw_payload = _payload_from_object(report)
    public_payload = _public_dict(report.to_dict(), label="verification report")
    report_hash = stable_contract_hash(public_payload)
    run_id = str(public_payload.get("run_id") or "")
    if not run_id:
        raise ValueError("verification report run_id is required")
    checks = public_payload.get("checks") if isinstance(public_payload.get("checks"), list) else []
    errors = public_payload.get("errors") if isinstance(public_payload.get("errors"), list) else []
    generated_files = (
        public_payload.get("generated_files") if isinstance(public_payload.get("generated_files"), list) else []
    )
    metrics = public_payload.get("metrics") if isinstance(public_payload.get("metrics"), dict) else {}
    failed_check_count = sum(
        1
        for check in checks
        if isinstance(check, dict) and check.get("passed") is False
    )
    mode = _safe_label(metrics.get("boundary_mode") if isinstance(metrics, dict) else "", fallback="unknown")
    metric_keys = tuple(
        _safe_label(key, fallback="metric")
        for key in sorted(str(key) for key in metrics.keys())
    )
    summary = (
        f"verification_report:{'passed' if bool(public_payload.get('passed')) else 'failed'}; "
        f"checks={len(checks)}; errors={len(errors)}; generated_files={len(generated_files)}"
    )
    return VerificationReportRecord(
        report_id=f"report-{report_hash[:12]}",
        run_id=run_id,
        mode=mode,
        source_artifact_id=_safe_reference(source_artifact_id),
        runner_plan_hash=_safe_contract_hash_reference(runner_plan_hash, label="runner_plan_hash"),
        report_hash=report_hash,
        passed=bool(public_payload.get("passed")),
        check_count=len(checks),
        failed_check_count=failed_check_count,
        error_count=len(errors),
        generated_file_count=len(generated_files),
        metric_count=len(metrics),
        metric_keys=metric_keys,
        checks_hash=stable_contract_hash(checks),
        errors_hash=stable_contract_hash(errors),
        metrics_hash=stable_contract_hash(metrics),
        generated_files_hash=stable_contract_hash(generated_files),
        visible_field_counts=_visible_projection_counts(raw_payload, public_payload),
        summary=summary,
        created_at=str(public_payload.get("created_at") or utc_now()),
    )


def audit_event_record_from_event(
    event: object,
    *,
    source_artifact_id: str = "",
    linked_plan_hash: str = "",
    linked_report_hash: str = "",
) -> AuditEventRecord:
    """Project an audit event into metadata, counts, and hashes only."""
    raw_payload = _payload_from_object(event)
    public_payload = _public_dict(event.to_dict() if hasattr(event, "to_dict") else raw_payload, label="audit event")
    run_id = str(public_payload.get("run_id") or "")
    if not run_id:
        raise ValueError("audit event run_id is required")
    payload_body = public_payload.get("payload") if isinstance(public_payload.get("payload"), dict) else {}
    message = str(public_payload.get("message") or "")
    event_type = _safe_label(public_payload.get("event"), fallback="audit_event")
    source = _safe_label(public_payload.get("source"), fallback="event_source")
    stage = _safe_label(public_payload.get("stage"), fallback="unknown_stage")
    level = _safe_label(public_payload.get("level"), fallback="info")
    projection = {
        "run_id": run_id,
        "event_type": event_type,
        "source": source,
        "stage": stage,
        "level": level,
        "source_artifact_id": _safe_reference(source_artifact_id),
        "linked_plan_hash": _safe_contract_hash_reference(linked_plan_hash, label="linked_plan_hash"),
        "linked_report_hash": _safe_contract_hash_reference(linked_report_hash, label="linked_report_hash"),
        "message_hash": stable_contract_hash({"message": message}),
        "payload_hash": stable_contract_hash(payload_body),
        "payload_field_count": _payload_field_count(payload_body),
        "visible_field_counts": _visible_projection_counts(raw_payload, public_payload),
        "created_at": str(public_payload.get("created_at") or utc_now()),
    }
    event_hash = stable_contract_hash(projection)
    summary = f"audit_event:{event_type}; payload_fields={projection['payload_field_count']}"
    return AuditEventRecord(
        audit_event_id=f"audit-{event_hash[:12]}",
        summary=summary,
        **projection,
    )


def _is_contract_hash(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == CONTRACT_HASH_LENGTH
        and all(char in "0123456789abcdef" for char in value)
    )


def _validate_approval_type(approval_type: str) -> None:
    if approval_type not in APPROVAL_TYPES:
        raise ValueError("approval_type is not supported")


def _validate_lifecycle_class(lifecycle_class: str) -> None:
    if lifecycle_class not in LIFECYCLE_CLASSES:
        raise ValueError("lifecycle_class is not supported")


def _is_safe_replay_run_id(run_id: str) -> bool:
    return (
        isinstance(run_id, str)
        and 1 <= len(run_id) <= 81
        and run_id[0].isalnum()
        and all(char in SAFE_REPLAY_RUN_ID_CHARS for char in run_id)
    )


def canonical_replay_scope(*, approval_type: str, run_id: str, subject_hash: str) -> str:
    """Return the AW-SOT-10 canonical replay scope."""
    if approval_type not in REPLAY_APPROVAL_TYPES:
        raise ValueError("approval_type is not replay-consuming")
    if not _is_safe_replay_run_id(run_id):
        raise ValueError("run_id cannot be used in a replay scope")
    if not _is_contract_hash(subject_hash):
        raise ValueError("subject_hash must be a contract hash")
    return f"aw.approval.v1/{approval_type}/{run_id}/{subject_hash}"


def parse_replay_scope(scope_canonical: str) -> dict[str, str]:
    """Parse and validate the AW-SOT-10 replay scope."""
    parts = scope_canonical.split("/")
    if len(parts) != 4 or parts[0] != "aw.approval.v1":
        raise ValueError("scope_canonical is not canonical")
    approval_type, run_id, subject_hash = parts[1], parts[2], parts[3]
    if approval_type not in REPLAY_APPROVAL_TYPES:
        raise ValueError("scope_canonical approval type is not supported")
    if not _is_safe_replay_run_id(run_id):
        raise ValueError("scope_canonical run_id is not valid")
    if not _is_contract_hash(subject_hash):
        raise ValueError("scope_canonical subject_hash is not valid")
    return {
        "approval_type": approval_type,
        "run_id": run_id,
        "subject_hash": subject_hash,
    }


def replay_nonce_hash(*, scope_canonical: str, nonce: str) -> str:
    """Return a hash-only replay nonce claim key."""
    parse_replay_scope(scope_canonical)
    if not isinstance(nonce, str) or not nonce.strip():
        raise ValueError("nonce is required")
    serialized = json.dumps(
        {"v": 1, "scope": scope_canonical, "nonce": nonce},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _visible_field_counts(subject: dict[str, object], source_artifact_ids: tuple[str, ...]) -> dict[str, int]:
    return {
        "subject_top_level_fields": len(subject),
        "source_artifact_ids": len(source_artifact_ids),
        "forbidden_public_key_count": len(find_forbidden_public_keys(subject)),
    }


def approval_subject_snapshot_record(
    *,
    approval_type: str,
    run_id: str,
    subject_kind: str,
    subject: dict[str, object],
    subject_schema_version: str,
    source_artifact_ids: list[str] | tuple[str, ...] = (),
    lifecycle_class: str = "durable",
    scope_canonical: str = "",
    sanitized_summary: str = "",
    created_at: str | None = None,
) -> ApprovalSubjectSnapshotRecord:
    """Project an approval subject into an immutable hash-bound snapshot."""
    _validate_approval_type(approval_type)
    _validate_lifecycle_class(lifecycle_class)
    if not run_id.strip():
        raise ValueError("run_id is required")
    if not subject_kind.strip():
        raise ValueError("subject_kind is required")
    if not subject_schema_version.strip():
        raise ValueError("subject_schema_version is required")

    public_subject = sanitize_public_payload(subject)
    if not isinstance(public_subject, dict):
        raise ValueError("subject must be a mapping")

    subject_hash = stable_contract_hash(public_subject)
    if approval_type in REPLAY_APPROVAL_TYPES and not scope_canonical:
        scope_canonical = canonical_replay_scope(
            approval_type=approval_type,
            run_id=run_id,
            subject_hash=subject_hash,
        )
    elif approval_type in REPLAY_APPROVAL_TYPES:
        expected_scope = canonical_replay_scope(
            approval_type=approval_type,
            run_id=run_id,
            subject_hash=subject_hash,
        )
        if scope_canonical != expected_scope:
            raise ValueError("scope_canonical does not match approval subject")
    if approval_type not in REPLAY_APPROVAL_TYPES:
        scope_canonical = ""

    artifact_ids = tuple(str(item) for item in source_artifact_ids)
    visible_counts = _visible_field_counts(subject, artifact_ids)
    safe_summary = str(redact_secrets(sanitized_summary)) if sanitized_summary else (
        f"{approval_type}:{subject_kind}; fields={len(public_subject)}"
    )
    projection = {
        "approval_type": approval_type,
        "snapshot_schema_version": "approval-subject-snapshot-v1",
        "subject_schema_version": subject_schema_version,
        "lifecycle_class": lifecycle_class,
        "run_id": run_id,
        "subject_kind": subject_kind,
        "source_artifact_ids": artifact_ids,
        "subject_hash": subject_hash,
        "subject_hashes": {"subject": subject_hash},
        "scope_canonical": scope_canonical,
        "sanitized_summary": safe_summary,
        "visible_field_counts": visible_counts,
        "created_at": created_at or utc_now(),
    }
    snapshot_hash = stable_contract_hash(projection)
    return ApprovalSubjectSnapshotRecord(
        subject_snapshot_id=f"snapshot-{snapshot_hash[:12]}",
        snapshot_hash=snapshot_hash,
        **projection,
    )


def approval_decision_record(
    *,
    approval_id: str,
    snapshot: ApprovalSubjectSnapshotRecord,
    decision: str,
    approved_by_ref: str,
    approver_role: str,
    approved_at: str,
    expires_at: str = "",
    policy_id_ref: str = "",
    key_identity_ref: str = "",
    audit_log_id: str = "",
    lifecycle_class: str | None = None,
    created_at: str | None = None,
) -> ApprovalDecisionRecord:
    """Project an approval decision into an immutable hash-only row."""
    if not approval_id.strip():
        raise ValueError("approval_id is required")
    if decision not in {"approved", "changes_requested", "rejected"}:
        raise ValueError("decision is not supported")

    row_lifecycle = lifecycle_class or snapshot.lifecycle_class
    _validate_lifecycle_class(row_lifecycle)
    if row_lifecycle != snapshot.lifecycle_class:
        raise ValueError("approval lifecycle must match subject snapshot lifecycle")
    if snapshot.approval_type in REPLAY_APPROVAL_TYPES and row_lifecycle != "durable":
        raise ValueError("fixture/synthetic live/provider approvals cannot be persisted as durable approval rows")

    projection = {
        "approval_id": approval_id,
        "approval_type": snapshot.approval_type,
        "snapshot_schema_version": snapshot.snapshot_schema_version,
        "subject_schema_version": snapshot.subject_schema_version,
        "lifecycle_class": row_lifecycle,
        "run_id": snapshot.run_id,
        "subject_snapshot_id": snapshot.subject_snapshot_id,
        "subject_hash": snapshot.subject_hash,
        "scope_canonical": snapshot.scope_canonical,
        "decision": decision,
        "approved_by_ref": str(redact_secrets(approved_by_ref)),
        "approver_role": str(redact_secrets(approver_role)),
        "approved_at": approved_at,
        "expires_at": expires_at,
        "policy_id_ref": str(redact_secrets(policy_id_ref)),
        "key_identity_ref": str(redact_secrets(key_identity_ref)),
        "audit_log_id": str(redact_secrets(audit_log_id)),
        "created_at": created_at or utc_now(),
    }
    approval_hash = stable_contract_hash(projection)
    return ApprovalDecisionRecord(approval_hash=approval_hash, **projection)


def replay_nonce_record(
    *,
    scope_canonical: str,
    nonce: str,
    approval_hash: str,
    run_id: str,
    approval_type: str,
    expires_at: str,
    claimed_at: str | None = None,
    status: str = "claimed",
) -> ReplayNonceRecord:
    """Project a raw nonce into a hash-only replay tombstone."""
    if approval_type not in REPLAY_APPROVAL_TYPES:
        raise ValueError("approval_type is not replay-consuming")
    parsed_scope = parse_replay_scope(scope_canonical)
    if parsed_scope["approval_type"] != approval_type:
        raise ValueError("scope_canonical approval_type does not match row")
    if parsed_scope["run_id"] != run_id:
        raise ValueError("scope_canonical run_id does not match row")
    if not _is_contract_hash(approval_hash):
        raise ValueError("approval_hash must be a contract hash")
    return ReplayNonceRecord(
        scope_canonical=scope_canonical,
        nonce_hash=replay_nonce_hash(scope_canonical=scope_canonical, nonce=nonce),
        approval_hash=approval_hash,
        run_id=run_id,
        approval_type=approval_type,
        claimed_at=claimed_at or utc_now(),
        expires_at=expires_at,
        status=status,
    )


def reconstruct_workflow_session_read_model(
    run_record: RunSessionRecord,
    artifact_records: list[ArtifactRecord],
) -> WorkflowSessionReadModel:
    """Rebuild the public read model from sanitized rows."""
    for artifact in artifact_records:
        if artifact.run_id != run_record.run_id:
            raise ValueError("artifact run_id does not match run session")
    return WorkflowSessionReadModel(
        run_id=run_record.run_id,
        stage=run_record.stage,
        status=run_record.status,
        prompt_contract_hash=run_record.prompt_contract_hash,
        idea_summary=run_record.idea_summary,
        artifacts=sorted(artifact_records, key=lambda item: item.created_at),
        created_at=run_record.created_at,
        updated_at=run_record.updated_at,
    )


def validate_runner_report_audit_linkage(
    *,
    run_id: str,
    runner_plans: list[RunnerPlanRecord],
    verification_reports: list[VerificationReportRecord],
    audit_events: list[AuditEventRecord],
    artifacts: list[ArtifactRecord] | None = None,
) -> dict[str, int]:
    """Validate that runner/report/audit repository rows belong to one run."""
    if not run_id.strip():
        raise ValueError("run_id is required")
    artifact_ids: set[str] | None = None
    if artifacts is not None:
        artifact_ids = {record.artifact_id for record in artifacts}
        for record in artifacts:
            if record.run_id != run_id:
                raise ValueError("artifact run_id does not match")
    plan_hashes = {record.plan_hash for record in runner_plans}
    report_hashes = {record.report_hash for record in verification_reports}
    report_plan_hashes = {record.report_hash: record.runner_plan_hash for record in verification_reports}
    source_artifact_references: list[str] = []
    for record in runner_plans:
        if record.run_id != run_id:
            raise ValueError("runner plan run_id does not match")
        if record.source_artifact_id:
            source_artifact_references.append(record.source_artifact_id)
    for record in verification_reports:
        if record.run_id != run_id:
            raise ValueError("verification report run_id does not match")
        if record.runner_plan_hash and record.runner_plan_hash not in plan_hashes:
            raise ValueError("verification report runner_plan_hash does not match")
        if record.source_artifact_id:
            source_artifact_references.append(record.source_artifact_id)
    for record in audit_events:
        if record.run_id != run_id:
            raise ValueError("audit event run_id does not match")
        if record.linked_plan_hash and record.linked_plan_hash not in plan_hashes:
            raise ValueError("audit event linked_plan_hash does not match")
        if record.linked_report_hash and record.linked_report_hash not in report_hashes:
            raise ValueError("audit event linked_report_hash does not match")
        report_plan_hash = report_plan_hashes.get(record.linked_report_hash, "")
        if record.linked_plan_hash and report_plan_hash and record.linked_plan_hash != report_plan_hash:
            raise ValueError("audit event linked plan/report chain does not match")
        if record.source_artifact_id:
            source_artifact_references.append(record.source_artifact_id)
    if artifact_ids is not None:
        missing_artifact_ids = sorted(
            artifact_id
            for artifact_id in source_artifact_references
            if artifact_id not in artifact_ids
        )
        if missing_artifact_ids:
            raise ValueError("source_artifact_id does not match artifact repository")
    result = {
        "run_id_linked": 1,
        "runner_plan_count": len(runner_plans),
        "verification_report_count": len(verification_reports),
        "audit_event_count": len(audit_events),
    }
    if artifact_ids is not None:
        result["source_artifact_reference_count"] = len(source_artifact_references)
        result["artifact_linkage_count"] = len(source_artifact_references)
    return result


@dataclass(slots=True)
class InMemoryRunSessionRepository:
    """In-memory implementation used until a DB-backed adapter exists."""

    records: dict[str, RunSessionRecord] = field(default_factory=dict)

    def save(self, session: WorkflowSession) -> RunSessionRecord:
        record = run_session_record_from_session(session)
        self.records[record.run_id] = record
        return record

    def get(self, run_id: str) -> RunSessionRecord | None:
        return self.records.get(run_id)


@dataclass(slots=True)
class InMemoryArtifactRepository:
    """In-memory implementation that stores artifact metadata only."""

    records: dict[str, ArtifactRecord] = field(default_factory=dict)

    def save(self, artifact: Artifact) -> ArtifactRecord:
        record = artifact_record_from_artifact(artifact)
        self.records[record.artifact_id] = record
        return record

    def list_for_run(self, run_id: str) -> list[ArtifactRecord]:
        artifacts = [record for record in self.records.values() if record.run_id == run_id]
        return sorted(artifacts, key=lambda item: item.created_at)


@dataclass(slots=True)
class InMemoryRunnerPlanRepository:
    """In-memory repository that stores runner-plan projections only."""

    records: dict[str, RunnerPlanRecord] = field(default_factory=dict)

    def save(self, plan: object, *, source_artifact_id: str = "") -> RunnerPlanRecord:
        record = runner_plan_record_from_plan(plan, source_artifact_id=source_artifact_id)
        self.records[record.plan_hash] = record
        return record

    def get(self, plan_hash: str) -> RunnerPlanRecord | None:
        return self.records.get(plan_hash)

    def list_for_run(self, run_id: str) -> list[RunnerPlanRecord]:
        records = [record for record in self.records.values() if record.run_id == run_id]
        return sorted(records, key=lambda item: item.created_at)


@dataclass(slots=True)
class InMemoryVerificationReportRepository:
    """In-memory repository that stores verification report projections only."""

    records: dict[str, VerificationReportRecord] = field(default_factory=dict)

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
        self.records[record.report_hash] = record
        return record

    def get(self, report_hash: str) -> VerificationReportRecord | None:
        return self.records.get(report_hash)

    def list_for_run(self, run_id: str) -> list[VerificationReportRecord]:
        records = [record for record in self.records.values() if record.run_id == run_id]
        return sorted(records, key=lambda item: item.created_at)


@dataclass(slots=True)
class InMemoryAuditEventRepository:
    """In-memory repository that stores audit-event projections only."""

    records: dict[str, AuditEventRecord] = field(default_factory=dict)

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
        self.records[record.audit_event_id] = record
        return record

    def list_for_run(self, run_id: str) -> list[AuditEventRecord]:
        records = [record for record in self.records.values() if record.run_id == run_id]
        return sorted(records, key=lambda item: item.created_at)


@dataclass(slots=True)
class InMemoryApprovalRepository:
    """In-memory approval repository for hash-only approval persistence tests."""

    snapshots: dict[str, ApprovalSubjectSnapshotRecord] = field(default_factory=dict)
    approvals: dict[str, ApprovalDecisionRecord] = field(default_factory=dict)

    def save_subject_snapshot(
        self,
        *,
        approval_type: str,
        run_id: str,
        subject_kind: str,
        subject: dict[str, object],
        subject_schema_version: str,
        source_artifact_ids: list[str] | tuple[str, ...] = (),
        lifecycle_class: str = "durable",
        scope_canonical: str = "",
        sanitized_summary: str = "",
        created_at: str | None = None,
    ) -> ApprovalSubjectSnapshotRecord:
        record = approval_subject_snapshot_record(
            approval_type=approval_type,
            run_id=run_id,
            subject_kind=subject_kind,
            subject=subject,
            subject_schema_version=subject_schema_version,
            source_artifact_ids=source_artifact_ids,
            lifecycle_class=lifecycle_class,
            scope_canonical=scope_canonical,
            sanitized_summary=sanitized_summary,
            created_at=created_at,
        )
        self.snapshots[record.subject_snapshot_id] = record
        return record

    def save_approval(
        self,
        *,
        approval_id: str,
        snapshot: ApprovalSubjectSnapshotRecord,
        decision: str,
        approved_by_ref: str,
        approver_role: str,
        approved_at: str,
        expires_at: str = "",
        policy_id_ref: str = "",
        key_identity_ref: str = "",
        audit_log_id: str = "",
        lifecycle_class: str | None = None,
        created_at: str | None = None,
    ) -> ApprovalDecisionRecord:
        if snapshot.subject_snapshot_id not in self.snapshots:
            self.snapshots[snapshot.subject_snapshot_id] = snapshot
        record = approval_decision_record(
            approval_id=approval_id,
            snapshot=snapshot,
            decision=decision,
            approved_by_ref=approved_by_ref,
            approver_role=approver_role,
            approved_at=approved_at,
            expires_at=expires_at,
            policy_id_ref=policy_id_ref,
            key_identity_ref=key_identity_ref,
            audit_log_id=audit_log_id,
            lifecycle_class=lifecycle_class,
            created_at=created_at,
        )
        self.approvals[record.approval_id] = record
        return record

    def get_snapshot(self, subject_snapshot_id: str) -> ApprovalSubjectSnapshotRecord | None:
        return self.snapshots.get(subject_snapshot_id)

    def get_approval(self, approval_id: str) -> ApprovalDecisionRecord | None:
        return self.approvals.get(approval_id)


@dataclass(slots=True)
class InMemoryReplayNonceRepository:
    """Hash-only replay nonce repository with process-restart simulation support."""

    records: dict[tuple[str, str], ReplayNonceRecord] = field(default_factory=dict)

    @classmethod
    def from_records(cls, records: list[ReplayNonceRecord]) -> "InMemoryReplayNonceRepository":
        repository = cls()
        for record in records:
            repository.records[(record.scope_canonical, record.nonce_hash)] = record
        return repository

    def claim(
        self,
        *,
        scope_canonical: str,
        nonce: str,
        approval_hash: str,
        run_id: str,
        approval_type: str,
        expires_at: str,
        claimed_at: str | None = None,
    ) -> ReplayNonceRecord:
        record = replay_nonce_record(
            scope_canonical=scope_canonical,
            nonce=nonce,
            approval_hash=approval_hash,
            run_id=run_id,
            approval_type=approval_type,
            expires_at=expires_at,
            claimed_at=claimed_at,
        )
        key = (record.scope_canonical, record.nonce_hash)
        if key in self.records:
            raise ReplayNonceReplayError("replay nonce has already been claimed")
        self.records[key] = record
        return record

    def list_records(self) -> list[ReplayNonceRecord]:
        return sorted(self.records.values(), key=lambda item: (item.scope_canonical, item.nonce_hash))


class FileBackedReplayNonceRepository:
    """File-backed replay nonce repository with atomic replace writes."""

    def __init__(self, *, root: str | Path, relative_path: str | Path = "replay_nonces.json") -> None:
        self.root = Path(root)
        self.path = resolve_within_root(self.root, relative_path)

    def _load_rows(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReplayStoreUnavailableError("replay store is unavailable") from exc
        if not isinstance(payload, list):
            raise ReplayStoreUnavailableError("replay store is unavailable")
        rows: list[dict[str, object]] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ReplayStoreUnavailableError("replay store is unavailable")
            rows.append(item)
        return rows

    def _records_from_rows(self, rows: list[dict[str, object]]) -> list[ReplayNonceRecord]:
        records: list[ReplayNonceRecord] = []
        for row in rows:
            scope_canonical = str(row.get("scope_canonical") or "")
            nonce_hash = str(row.get("nonce_hash") or "")
            approval_hash = str(row.get("approval_hash") or "")
            run_id = str(row.get("run_id") or "")
            approval_type = str(row.get("approval_type") or "")
            claimed_at = str(row.get("claimed_at") or "")
            expires_at = str(row.get("expires_at") or "")
            status = str(row.get("status") or "")
            try:
                parsed_scope = parse_replay_scope(scope_canonical)
            except ValueError as exc:
                raise ReplayStoreUnavailableError("replay store is unavailable") from exc
            if not _is_contract_hash(nonce_hash):
                raise ReplayStoreUnavailableError("replay store is unavailable")
            if not _is_contract_hash(approval_hash):
                raise ReplayStoreUnavailableError("replay store is unavailable")
            if approval_type not in REPLAY_APPROVAL_TYPES or approval_type != parsed_scope["approval_type"]:
                raise ReplayStoreUnavailableError("replay store is unavailable")
            if not run_id or run_id != parsed_scope["run_id"]:
                raise ReplayStoreUnavailableError("replay store is unavailable")
            if not claimed_at or not expires_at or status != "claimed":
                raise ReplayStoreUnavailableError("replay store is unavailable")
            records.append(
                ReplayNonceRecord(
                    scope_canonical=scope_canonical,
                    nonce_hash=nonce_hash,
                    approval_hash=approval_hash,
                    run_id=run_id,
                    approval_type=approval_type,
                    claimed_at=claimed_at,
                    expires_at=expires_at,
                    status=status,
                )
            )
        return records

    def _write_records(self, records: list[ReplayNonceRecord]) -> None:
        rows = [record.to_dict() for record in records]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        try:
            temp_path.write_text(
                json.dumps(rows, ensure_ascii=True, sort_keys=True, indent=2),
                encoding="utf-8",
            )
            temp_path.replace(self.path)
        except OSError as exc:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass
            raise ReplayStoreUnavailableError("replay store is unavailable") from exc

    def claim(
        self,
        *,
        scope_canonical: str,
        nonce: str,
        approval_hash: str,
        run_id: str,
        approval_type: str,
        expires_at: str,
        claimed_at: str | None = None,
    ) -> ReplayNonceRecord:
        records = self._records_from_rows(self._load_rows())
        key_set = {(record.scope_canonical, record.nonce_hash) for record in records}
        record = replay_nonce_record(
            scope_canonical=scope_canonical,
            nonce=nonce,
            approval_hash=approval_hash,
            run_id=run_id,
            approval_type=approval_type,
            expires_at=expires_at,
            claimed_at=claimed_at,
        )
        if (record.scope_canonical, record.nonce_hash) in key_set:
            raise ReplayNonceReplayError("replay nonce has already been claimed")
        records.append(record)
        self._write_records(records)
        return record

    def list_records(self) -> list[ReplayNonceRecord]:
        return sorted(
            self._records_from_rows(self._load_rows()),
            key=lambda item: (item.scope_canonical, item.nonce_hash),
        )

    def load_records(self) -> list[dict[str, str]]:
        return [
            {key: str(value) for key, value in record.to_dict().items()}
            for record in self.list_records()
        ]

    def save_records(self, records: list[dict[str, str]]) -> None:
        replay_records = self._records_from_rows(records)
        self._write_records(replay_records)

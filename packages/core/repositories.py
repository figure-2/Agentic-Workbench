"""Persistence boundary skeleton for run sessions and artifacts.

The first repository layer stores read-model projections only. It deliberately
does not persist raw prompts, raw request bodies, raw artifact payloads, logs,
provider responses, or generated file bodies.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol

from .exposure import sanitize_public_payload
from .pathing import normalize_public_relative_path
from .schemas import Artifact, WorkflowSession, stable_contract_hash
from .security import redact_secrets


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


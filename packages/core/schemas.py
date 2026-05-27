"""Shared contracts for Agentic Workbench.

These dataclasses are the integration boundary between the DIV planning layer
and the DAACS build/verification layer. They intentionally avoid importing
either source project so the harness can test contract behavior in isolation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any
from uuid import uuid4

from .exposure import sanitize_public_payload
from .pathing import normalize_public_relative_path
from .security import redact_secrets


JsonDict = dict[str, Any]


def utc_now() -> str:
    """Return a stable UTC timestamp for artifacts and events."""
    return datetime.now(timezone.utc).isoformat()


class WorkflowStage(str, Enum):
    """Top-level stage names used by API, UI, and event logs."""

    CREATED = "created"
    IDEA = "idea"
    PLANNING = "planning"
    RESEARCH = "research"
    SPEC = "spec"
    APPROVAL = "approval"
    BUILD = "build"
    VERIFY = "verify"
    COMPLETE = "complete"
    FAILED = "failed"


class ArtifactKind(str, Enum):
    """Artifact classes produced by the harness."""

    IDEA_BRIEF = "idea_brief"
    PLANNING_BLUEPRINT = "planning_blueprint"
    RESEARCH_EVIDENCE = "research_evidence"
    VISUAL_ARTIFACT = "visual_artifact"
    PRD_PACKAGE = "prd_package"
    BUILD_SPEC = "build_spec"
    IMPLEMENTATION_BRIEF = "implementation_brief"
    SPEC_APPROVAL = "spec_approval"
    RUNNER_PLAN = "runner_plan"
    GENERATED_CODE = "generated_code"
    VERIFICATION_REPORT = "verification_report"
    LOG = "log"
    README = "readme"


@dataclass(slots=True)
class IdeaBrief:
    """Normalized user intent before planner execution."""

    raw_prompt: str
    target_user: str | None = None
    product_type: str | None = None
    constraints: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.raw_prompt.strip():
            raise ValueError("raw_prompt is required")

    def to_dict(self) -> JsonDict:
        self.validate()
        return asdict(self)


@dataclass(slots=True)
class PlanningBlueprint:
    """Planner output consumed by the DAACS adapter."""

    title: str
    problem: str
    goals: list[str] = field(default_factory=list)
    user_flows: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    evidence: list[JsonDict] = field(default_factory=list)
    visual_artifacts: list[JsonDict] = field(default_factory=list)
    markdown: str = ""
    assumptions: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.title.strip():
            raise ValueError("title is required")
        if not self.problem.strip():
            raise ValueError("problem is required")

    def to_dict(self) -> JsonDict:
        self.validate()
        return asdict(self)


@dataclass(slots=True)
class BuildSpec:
    """Implementation contract passed into the DAACS build layer."""

    app_name: str
    goal: str
    backend_required: bool
    frontend_required: bool
    api_spec: JsonDict = field(default_factory=dict)
    frontend_spec: JsonDict = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    source_blueprint_title: str | None = None

    def validate(self) -> None:
        if not self.app_name.strip():
            raise ValueError("app_name is required")
        if not self.goal.strip():
            raise ValueError("goal is required")
        if not self.backend_required and not self.frontend_required:
            raise ValueError("at least one build target is required")
        if self.backend_required and not self.api_spec.get("endpoints"):
            raise ValueError("api_spec.endpoints is required when backend_required is true")
        if self.frontend_required and not self.frontend_spec.get("api_calls"):
            raise ValueError("frontend_spec.api_calls is required when frontend_required is true")

    def to_dict(self) -> JsonDict:
        self.validate()
        return asdict(self)


def stable_contract_hash(payload: Any) -> str:
    """Return a deterministic hash for sanitized public contract payloads."""
    sanitized = sanitize_public_payload(payload)
    serialized = json.dumps(sanitized, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class PRDPackage:
    """Human-reviewable planning package created before DAACS handoff."""

    product_name: str
    problem: str
    prd_markdown: str
    feature_requirements: list[str] = field(default_factory=list)
    user_flows: list[str] = field(default_factory=list)
    api_requirements: list[JsonDict] = field(default_factory=list)
    data_entities: list[JsonDict] = field(default_factory=list)
    visual_requirements: list[JsonDict] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    test_scenarios: list[str] = field(default_factory=list)
    priorities: list[JsonDict] = field(default_factory=list)
    evidence_summary: list[JsonDict] = field(default_factory=list)
    source_blueprint_title: str | None = None
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        if not self.product_name.strip():
            raise ValueError("product_name is required")
        if not self.problem.strip():
            raise ValueError("problem is required")
        if not self.prd_markdown.strip():
            raise ValueError("prd_markdown is required")
        if not self.feature_requirements:
            raise ValueError("feature_requirements are required")
        if not self.acceptance_criteria:
            raise ValueError("acceptance_criteria are required")

    def to_dict(self) -> JsonDict:
        self.validate()
        return sanitize_public_payload(asdict(self))


@dataclass(slots=True)
class ImplementationBrief:
    """DAACS-readable handoff package derived from an approved PRD package."""

    app_name: str
    build_spec_hash: str
    prd_package: PRDPackage
    build_spec: JsonDict
    daacs_tasks: list[JsonDict] = field(default_factory=list)
    handoff_summary: str = ""
    constraints: list[str] = field(default_factory=list)
    approval_required: bool = True
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        if not self.app_name.strip():
            raise ValueError("app_name is required")
        if not self.build_spec_hash.strip():
            raise ValueError("build_spec_hash is required")
        self.prd_package.validate()
        if not self.build_spec.get("api_spec") or not self.build_spec.get("frontend_spec"):
            raise ValueError("build_spec must include api_spec and frontend_spec")
        if not self.build_spec.get("acceptance_criteria"):
            raise ValueError("build_spec.acceptance_criteria is required")
        if not self.daacs_tasks:
            raise ValueError("daacs_tasks are required")

    def to_dict(self) -> JsonDict:
        self.validate()
        data = asdict(self)
        data["brief_hash"] = stable_contract_hash(
            {
                "app_name": self.app_name,
                "build_spec_hash": self.build_spec_hash,
                "prd_package": self.prd_package.to_dict(),
                "build_spec": self.build_spec,
                "daacs_tasks": self.daacs_tasks,
                "constraints": self.constraints,
                "approval_required": self.approval_required,
            }
        )
        return sanitize_public_payload(data)


@dataclass(slots=True)
class SpecApproval:
    """User approval or requested-change record for a specific implementation brief."""

    approval_id: str
    approved: bool
    approved_build_spec_hash: str = ""
    approved_implementation_brief_hash: str = ""
    approval_scope: list[str] = field(default_factory=list)
    requested_changes: list[str] = field(default_factory=list)
    approver_role: str = "user"
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        if not self.approval_id.strip():
            raise ValueError("approval_id is required")
        if self.approved:
            if not self.approved_build_spec_hash.strip():
                raise ValueError("approved_build_spec_hash is required for approval")
            if not self.approved_implementation_brief_hash.strip():
                raise ValueError("approved_implementation_brief_hash is required for approval")
            if "daacs_build" not in self.approval_scope:
                raise ValueError("approval_scope must include daacs_build")
            if self.requested_changes:
                raise ValueError("approved records must not contain requested_changes")
        elif not self.requested_changes:
            raise ValueError("requested_changes are required when approval is false")

    def to_dict(self) -> JsonDict:
        self.validate()
        return sanitize_public_payload(asdict(self))


@dataclass(slots=True)
class VerificationReport:
    """Verification outcome from generated artifacts."""

    run_id: str
    passed: bool
    checks: list[JsonDict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    generated_files: list[str] = field(default_factory=list)
    metrics: JsonDict = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> JsonDict:
        data = asdict(self)
        data["generated_files"] = [
            normalize_public_relative_path(path) for path in self.generated_files
        ]
        return sanitize_public_payload(data)


@dataclass(slots=True)
class Artifact:
    """Artifact metadata used by the registry and UI."""

    id: str
    run_id: str
    kind: ArtifactKind
    name: str
    path: str | None = None
    payload: JsonDict = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        kind: ArtifactKind,
        name: str,
        path: str | None = None,
        payload: JsonDict | None = None,
    ) -> "Artifact":
        return cls(
            id=f"artifact-{uuid4().hex[:12]}",
            run_id=run_id,
            kind=kind,
            name=name,
            path=normalize_public_relative_path(path) if path else None,
            payload=sanitize_public_payload(payload or {}),
        )

    def to_dict(self) -> JsonDict:
        data = asdict(self)
        data["kind"] = self.kind.value
        data["payload"] = sanitize_public_payload(data["payload"])
        data["path"] = normalize_public_relative_path(data["path"]) if data["path"] else None
        return redact_secrets(data)


@dataclass(slots=True)
class WorkflowSession:
    """Single workbench run across planning, build, and verification."""

    id: str
    idea: IdeaBrief
    stage: WorkflowStage = WorkflowStage.CREATED
    artifacts: list[Artifact] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    @classmethod
    def create(cls, idea: IdeaBrief) -> "WorkflowSession":
        idea.validate()
        return cls(id=f"run-{uuid4().hex[:10]}", idea=idea)

    def add_artifact(self, artifact: Artifact) -> None:
        if artifact.run_id != self.id:
            raise ValueError("artifact run_id does not match session id")
        self.artifacts.append(artifact)
        self.updated_at = utc_now()

    def move_to(self, stage: WorkflowStage) -> None:
        self.stage = stage
        self.updated_at = utc_now()

    def to_dict(self) -> JsonDict:
        return {
            "id": self.id,
            "idea": self.idea.to_dict(),
            "stage": self.stage.value,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

"""MVP orchestration layer for Agentic Workbench."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from packages.core.artifacts import ArtifactRegistry
from packages.core.events import WorkflowEvent
from packages.core.schemas import (
    Artifact,
    ArtifactKind,
    BuildSpec,
    IdeaBrief,
    ImplementationBrief,
    PlanningBlueprint,
    PRDPackage,
    SpecApproval,
    VerificationReport,
    WorkflowSession,
    WorkflowStage,
)
from packages.daacs_builder.adapters import (
    create_spec_approval,
    ensure_implementation_approved,
    implementation_brief_from_prd_package,
    planning_to_build_spec,
)
from packages.div_planner.adapters import planning_to_prd_package


Planner = Callable[[IdeaBrief], PlanningBlueprint]
Builder = Callable[[BuildSpec, str], VerificationReport]
Approver = Callable[[PRDPackage, ImplementationBrief, BuildSpec, str], SpecApproval]


class WorkbenchHarness:
    """Coordinates planner and builder components through shared contracts."""

    def __init__(
        self,
        *,
        planner: Planner,
        builder: Builder,
        approver: Approver | None = None,
        registry: ArtifactRegistry | None = None,
    ) -> None:
        self.planner = planner
        self.builder = builder
        self.approver = approver
        self.registry = registry or ArtifactRegistry()
        self.events: list[WorkflowEvent] = []

    def emit(self, event: WorkflowEvent) -> None:
        self.events.append(event)

    def run(self, idea: IdeaBrief) -> WorkflowSession:
        session = WorkflowSession.create(idea)
        self.emit(
            WorkflowEvent(
                run_id=session.id,
                stage=WorkflowStage.CREATED,
                source="harness",
                message="Workflow session created",
            )
        )

        session.move_to(WorkflowStage.PLANNING)
        blueprint = self.planner(idea)
        blueprint_artifact = Artifact.create(
            run_id=session.id,
            kind=ArtifactKind.PLANNING_BLUEPRINT,
            name="planning-blueprint.json",
            payload=blueprint.to_dict(),
        )
        self.registry.add(blueprint_artifact)
        session.add_artifact(blueprint_artifact)

        session.move_to(WorkflowStage.SPEC)
        build_spec = planning_to_build_spec(blueprint)
        prd_package = planning_to_prd_package(blueprint, build_spec=build_spec)
        prd_artifact = Artifact.create(
            run_id=session.id,
            kind=ArtifactKind.PRD_PACKAGE,
            name="prd-package.json",
            payload=prd_package.to_dict(),
        )
        self.registry.add(prd_artifact)
        session.add_artifact(prd_artifact)

        build_artifact = Artifact.create(
            run_id=session.id,
            kind=ArtifactKind.BUILD_SPEC,
            name="build-spec.json",
            payload=build_spec.to_dict(),
        )
        self.registry.add(build_artifact)
        session.add_artifact(build_artifact)

        implementation_brief = implementation_brief_from_prd_package(prd_package, build_spec)
        brief_artifact = Artifact.create(
            run_id=session.id,
            kind=ArtifactKind.IMPLEMENTATION_BRIEF,
            name="implementation-brief.json",
            payload=implementation_brief.to_dict(),
        )
        self.registry.add(brief_artifact)
        session.add_artifact(brief_artifact)

        session.move_to(WorkflowStage.APPROVAL)
        if self.approver is None:
            self.emit(
                WorkflowEvent(
                    run_id=session.id,
                    stage=WorkflowStage.APPROVAL,
                    source="harness",
                    message="Workflow session awaits PRD and implementation brief approval",
                    payload={"builder_called": False, "approval_required": True},
                )
            )
            return session

        approval = self.approver(prd_package, implementation_brief, build_spec, session.id)
        approval_artifact = Artifact.create(
            run_id=session.id,
            kind=ArtifactKind.SPEC_APPROVAL,
            name="spec-approval.json",
            payload=approval.to_dict(),
        )
        self.registry.add(approval_artifact)
        session.add_artifact(approval_artifact)
        if not approval.approved:
            self.emit(
                WorkflowEvent(
                    run_id=session.id,
                    stage=WorkflowStage.APPROVAL,
                    source="harness",
                    message="Workflow session requires PRD or implementation brief changes",
                    payload={
                        "builder_called": False,
                        "requested_change_count": len(approval.requested_changes),
                    },
                )
            )
            return session

        ensure_implementation_approved(implementation_brief, approval)

        session.move_to(WorkflowStage.BUILD)
        report = self.builder(build_spec, session.id)
        report_artifact = Artifact.create(
            run_id=session.id,
            kind=ArtifactKind.VERIFICATION_REPORT,
            name="verification-report.json",
            payload=report.to_dict(),
        )
        self.registry.add(report_artifact)
        session.add_artifact(report_artifact)

        session.move_to(WorkflowStage.COMPLETE if report.passed else WorkflowStage.FAILED)
        self.emit(
            WorkflowEvent(
                run_id=session.id,
                stage=session.stage,
                source="harness",
                message="Workflow session finished",
                payload={"passed": report.passed, "generated_files": report.generated_files},
            )
        )
        return session

    def event_dicts(self) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self.events]


def fixture_spec_approver(
    prd_package: PRDPackage,
    implementation_brief: ImplementationBrief,
    build_spec: BuildSpec,
    run_id: str,
) -> SpecApproval:
    """Explicit fixture approval used only by offline tests and fixture services."""
    prd_package.validate()
    build_spec.validate()
    return create_spec_approval(
        implementation_brief,
        approval_id=f"{run_id}-spec-approval",
        approved=True,
        approver_role="fixture_user_approval",
    )

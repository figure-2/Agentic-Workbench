import pytest

from packages.core.schemas import (
    BuildSpec,
    IdeaBrief,
    ImplementationBrief,
    PRDPackage,
    PlanningBlueprint,
    SpecApproval,
    WorkflowSession,
    stable_contract_hash,
)


def test_idea_brief_requires_prompt():
    idea = IdeaBrief(raw_prompt="Build a small planner app")
    assert idea.to_dict()["raw_prompt"] == "Build a small planner app"


def test_workflow_session_rejects_cross_run_artifact():
    session = WorkflowSession.create(IdeaBrief(raw_prompt="Create an app"))
    assert session.id.startswith("run-")
    assert session.stage.value == "created"


def test_build_spec_requires_at_least_one_target():
    spec = BuildSpec(
        app_name="demo",
        goal="Build a demo",
        backend_required=True,
        frontend_required=False,
        api_spec={"endpoints": [{"method": "GET", "path": "/api/v1/health"}]},
    )
    assert spec.to_dict()["backend_required"] is True


def test_planning_blueprint_serializes_features():
    blueprint = PlanningBlueprint(
        title="Demo",
        problem="Users need a tracked workflow",
        features=["Plan", "Build", "Verify"],
    )
    assert blueprint.to_dict()["features"] == ["Plan", "Build", "Verify"]


def test_prd_package_requires_reviewable_content():
    package = PRDPackage(
        product_name="Demo",
        problem="Users need a tracked workflow",
        prd_markdown="# Demo",
        feature_requirements=["Plan"],
        acceptance_criteria=["Plan is visible."],
    )

    assert package.to_dict()["product_name"] == "Demo"


def test_implementation_brief_adds_stable_public_hash():
    build_spec = BuildSpec(
        app_name="demo",
        goal="Build a demo",
        backend_required=True,
        frontend_required=True,
        api_spec={"endpoints": [{"method": "GET", "path": "/api/v1/health"}]},
        frontend_spec={"api_calls": ["GET /api/v1/health"]},
        acceptance_criteria=["Backend implements GET /api/v1/health."],
    )
    package = PRDPackage(
        product_name="Demo",
        problem="Users need a tracked workflow",
        prd_markdown="# Demo",
        feature_requirements=["Plan"],
        acceptance_criteria=["Backend implements GET /api/v1/health."],
    )
    spec_hash = stable_contract_hash(build_spec.to_dict())
    brief = ImplementationBrief(
        app_name="demo",
        build_spec_hash=spec_hash,
        prd_package=package,
        build_spec=build_spec.to_dict(),
        daacs_tasks=[{"id": "backend-contract", "role": "backend"}],
    )

    first = brief.to_dict()
    second = brief.to_dict()
    assert first["build_spec_hash"] == spec_hash
    assert first["brief_hash"] == second["brief_hash"]


def test_spec_approval_requires_matching_approval_shape():
    with pytest.raises(ValueError):
        SpecApproval(
            approval_id="approval-1",
            approved=True,
            approved_build_spec_hash="hash",
            approval_scope=["prd_package"],
        ).validate()

    with pytest.raises(ValueError):
        SpecApproval(approval_id="approval-2", approved=False).validate()

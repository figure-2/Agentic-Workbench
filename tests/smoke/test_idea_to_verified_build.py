from packages.core.schemas import IdeaBrief, PlanningBlueprint, SpecApproval, VerificationReport
from packages.harness.orchestrator.workflow import WorkbenchHarness, fixture_spec_approver


def fake_planner(idea: IdeaBrief) -> PlanningBlueprint:
    return PlanningBlueprint(
        title="Agentic Workbench Demo",
        problem=idea.raw_prompt,
        features=["Plan", "Build", "Verify"],
        evidence=[{"title": "Fixture evidence", "url": "fixture://local"}],
    )


def fake_builder(build_spec, run_id: str) -> VerificationReport:
    return VerificationReport(
        run_id=run_id,
        passed=True,
        checks=[{"name": "fixture_builder", "passed": True}],
        generated_files=["backend/main.py", "frontend/src/App.jsx"],
        metrics={"backend_file_count": 1, "frontend_file_count": 1, "issue_count": 0},
    )


def test_idea_to_verified_build_smoke():
    harness = WorkbenchHarness(planner=fake_planner, builder=fake_builder, approver=fixture_spec_approver)
    session = harness.run(IdeaBrief(raw_prompt="Create a workbench demo"))
    assert session.stage.value == "complete"
    assert [artifact.kind.value for artifact in session.artifacts] == [
        "planning_blueprint",
        "prd_package",
        "build_spec",
        "implementation_brief",
        "spec_approval",
        "verification_report",
    ]


def test_idea_to_build_stops_for_approval_without_approver():
    builder_called = False

    def blocked_builder(build_spec, run_id: str) -> VerificationReport:
        nonlocal builder_called
        builder_called = True
        return fake_builder(build_spec, run_id)

    harness = WorkbenchHarness(planner=fake_planner, builder=blocked_builder)
    session = harness.run(IdeaBrief(raw_prompt="Create a workbench demo"))

    assert session.stage.value == "approval"
    assert builder_called is False
    assert [artifact.kind.value for artifact in session.artifacts] == [
        "planning_blueprint",
        "prd_package",
        "build_spec",
        "implementation_brief",
    ]


def test_idea_to_build_stops_when_approver_requests_changes():
    builder_called = False

    def blocked_builder(build_spec, run_id: str) -> VerificationReport:
        nonlocal builder_called
        builder_called = True
        return fake_builder(build_spec, run_id)

    def change_request_approver(prd_package, implementation_brief, build_spec, run_id: str) -> SpecApproval:
        return SpecApproval(
            approval_id=f"{run_id}-changes",
            approved=False,
            requested_changes=["Clarify acceptance criteria before DAACS handoff."],
        )

    harness = WorkbenchHarness(
        planner=fake_planner,
        builder=blocked_builder,
        approver=change_request_approver,
    )
    session = harness.run(IdeaBrief(raw_prompt="Create a workbench demo"))

    assert session.stage.value == "approval"
    assert builder_called is False
    assert session.artifacts[-1].kind.value == "spec_approval"

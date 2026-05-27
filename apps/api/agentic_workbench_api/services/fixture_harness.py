"""Fixture harness service used before live DAACS/DIV wiring."""

from __future__ import annotations

from packages.core.schemas import IdeaBrief, PlanningBlueprint, VerificationReport
from packages.harness.orchestrator.workflow import WorkbenchHarness, fixture_spec_approver


def fixture_planner(idea: IdeaBrief) -> PlanningBlueprint:
    return PlanningBlueprint(
        title="Agentic Workbench Fixture",
        problem=idea.raw_prompt,
        goals=["Create a reproducible workflow run"],
        user_flows=["Submit idea", "Generate BuildSpec", "Record VerificationReport"],
        features=["Plan", "Build", "Verify"],
        evidence=[{"title": "Fixture evidence", "url": "fixture://local", "snippet": "Offline fixture"}],
        assumptions=["Fixture mode does not call live APIs."],
    )


def fixture_builder(build_spec, run_id: str) -> VerificationReport:
    return VerificationReport(
        run_id=run_id,
        passed=True,
        checks=[{"name": "fixture_builder", "passed": True}],
        generated_files=["backend/main.py", "frontend/src/App.jsx"],
        metrics={"backend_file_count": 1, "frontend_file_count": 1, "issue_count": 0},
    )


def create_fixture_harness() -> WorkbenchHarness:
    return WorkbenchHarness(planner=fixture_planner, builder=fixture_builder, approver=fixture_spec_approver)

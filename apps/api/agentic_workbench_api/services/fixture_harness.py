"""Fixture harness service used before live DAACS/DIV wiring."""

from __future__ import annotations

from packages.core.security import redact_secrets
from packages.core.schemas import IdeaBrief, PlanningBlueprint, VerificationReport
from packages.harness.orchestrator.workflow import WorkbenchHarness, fixture_spec_approver


def fixture_problem_statement(idea: IdeaBrief) -> str:
    """Return a public-safe fixture problem statement without copying raw input."""
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
        return "Sanitized fixture idea; raw prompt omitted"
    return "Sanitized fixture idea; " + "; ".join(str(part) for part in parts)


def fixture_planner(idea: IdeaBrief) -> PlanningBlueprint:
    return PlanningBlueprint(
        title="Agentic Workbench Fixture",
        problem=fixture_problem_statement(idea),
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

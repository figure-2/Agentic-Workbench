import pytest

from packages.core.pathing import PathBoundaryError
from packages.core.schemas import IdeaBrief, PlanningBlueprint, VerificationReport
from packages.harness.orchestrator.workflow import WorkbenchHarness, fixture_spec_approver


def planner_with_raw_fields(idea: IdeaBrief) -> PlanningBlueprint:
    return PlanningBlueprint(
        title="Security Gate Demo",
        problem=idea.raw_prompt,
        features=["Inspect artifact boundaries"],
        evidence=[
            {
                "title": "Raw evidence owner@example.com",
                "url": "https://example.com",
                "summary": "Bearer live-secret-token",
                "raw_content": "full raw search result",
            }
        ],
        visual_artifacts=[{"private_corpus": "internal notes", "summary": "diagram"}],
        markdown="Generated from /home/user/private-plan.md",
    )


def safe_builder(build_spec, run_id: str) -> VerificationReport:
    return VerificationReport(
        run_id=run_id,
        passed=True,
        checks=[{"name": "offline_fixture", "passed": True}],
        errors=["see F:\\File\\02_Project\\.env"],
        generated_files=["backend/main.py", "frontend/src/App.jsx"],
        metrics={"backend_file_count": 1, "frontend_file_count": 1, "issue_count": 0},
    )


def unsafe_builder(build_spec, run_id: str) -> VerificationReport:
    return VerificationReport(
        run_id=run_id,
        passed=True,
        generated_files=["../../secret.txt"],
    )


def test_aw_next_01_public_artifacts_are_sanitized_and_redacted():
    harness = WorkbenchHarness(
        planner=planner_with_raw_fields,
        builder=safe_builder,
        approver=fixture_spec_approver,
    )
    session = harness.run(IdeaBrief(raw_prompt="Create a local security gate demo"))

    payloads = [artifact.to_dict()["payload"] for artifact in session.artifacts]
    serialized = str(payloads)

    assert "raw_content" not in serialized
    assert "private_corpus" not in serialized
    assert "live-secret-token" not in serialized
    assert "owner@example.com" not in serialized
    assert "F:\\File\\02_Project" not in serialized
    assert "/home/user" not in serialized
    assert session.artifacts[-1].to_dict()["payload"]["generated_files"] == [
        "backend/main.py",
        "frontend/src/App.jsx",
    ]


def test_aw_next_01_rejects_unsafe_generated_file_paths():
    harness = WorkbenchHarness(
        planner=planner_with_raw_fields,
        builder=unsafe_builder,
        approver=fixture_spec_approver,
    )

    with pytest.raises(PathBoundaryError):
        harness.run(IdeaBrief(raw_prompt="Create a local security gate demo"))

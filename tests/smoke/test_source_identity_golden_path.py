import json
from pathlib import Path

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys
from packages.core.public_projection import public_workflow_session_payload
from packages.core.schemas import Artifact, ArtifactKind, IdeaBrief, WorkflowSession, WorkflowStage
from packages.daacs_builder.adapters import (
    build_spec_to_daacs_initial_state,
    create_spec_approval,
    implementation_brief_from_prd_package,
    planning_to_build_spec,
)
from packages.daacs_builder.dry_run_runner import DAACSDryRunRunner, ZERO_DRY_RUN_SIDE_EFFECTS
from packages.div_planner.adapters import planning_blueprint_from_div_state, planning_to_prd_package


FIXTURE_PATH = Path("tests/fixtures/source_identity_golden_path.json")


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _fixture_by_id(fixture: dict, fixture_id: str) -> dict:
    return next(item for item in fixture["fixtures"] if item["fixture_id"] == fixture_id)


def _source_identity_div_state(fixture: dict) -> dict:
    blueprint_identity = _fixture_by_id(fixture, "div-blueprint-identity-v1")["source_identity"]
    document_identity = _fixture_by_id(fixture, "div-markdown-visual-identity-v1")["source_identity"]
    required_titles = set(blueprint_identity["required_information_titles"])
    section_titles = list(blueprint_identity["section_titles"])
    visual_types = document_identity["document_quality_signals"]["visual_artifact_types"]
    sections = [
        {
            "section_number": str(index + 1),
            "title": title,
            "content": f"Fixture-safe section preserving DIV planning identity: {title}.",
            "evidence": [
                {
                    "title": f"{title} source note",
                    "content": "Sanitized source note only; no raw page or prompt body.",
                }
            ],
        }
        for index, title in enumerate(section_titles)
    ]

    return {
        "idea": {
            "title": "Campus Trust Marketplace",
            "planning_style": blueprint_identity["planning_style"],
            "rationale": blueprint_identity["summary"],
            "goals": [
                "Preserve DIV planning, PRD, evidence, and visual intent as reviewable artifacts."
            ],
            "blueprint": [
                {
                    "title": title,
                    "content": "Seed content available" if title not in required_titles else "",
                    "guideline": f"Collect planning details for {title}.",
                    "is_required_from_user": title in required_titles,
                }
                for title in section_titles
            ],
        },
        "plan": {
            "title": "Campus Trust Marketplace",
            "summary": blueprint_identity["idea_summary"],
            "sections": sections,
            "final_markdown": "\n\n".join(
                [
                    "# Campus Trust Marketplace",
                    "## Rationale",
                    blueprint_identity["summary"],
                    *[f"## {section['title']}\n\n{section['content']}" for section in sections],
                ]
            ),
            "visual_artifacts": [
                {
                    "section_number": str(index + 1),
                    "meta": {
                        "visual_type": visual_type,
                        "purpose": f"Preserve DIV {visual_type} intent as metadata.",
                    },
                }
                for index, visual_type in enumerate(visual_types)
            ],
        },
        "research": {
            "evidence_store": [
                {
                    "title": "DIV source identity fixture",
                    "url": "fixture://source/div",
                    "summary": "Sanitized evidence summary only.",
                }
            ]
        },
        "visual": {
            "artifacts": {
                "primary_flow": {
                    "section_number": "1",
                    "meta": {
                        "visual_type": "mermaid_flowchart",
                        "purpose": "Preserve user-flow visual intent.",
                    },
                }
            }
        },
    }


def _add_artifact(session: WorkflowSession, kind: ArtifactKind, name: str, payload: dict) -> None:
    session.add_artifact(
        Artifact.create(
            run_id=session.id,
            kind=kind,
            name=name,
            payload=payload,
        )
    )


def test_source_identity_fixture_runs_through_golden_path_without_live_side_effects():
    fixture = _load_fixture()
    covered_trace_ids = {
        trace_id for source_fixture in fixture["fixtures"] for trace_id in source_fixture["covered_trace_ids"]
    }
    div_state = _source_identity_div_state(fixture)
    daacs_identity = _fixture_by_id(fixture, "daacs-todo-fullstack-runner-v1")["source_identity"]
    runner_config = daacs_identity["runner_config_signals"]

    session = WorkflowSession.create(
        IdeaBrief(
            raw_prompt="Fixture-only campus marketplace idea for source identity parity.",
            target_user="student founders",
            product_type="agentic workflow fixture",
            constraints=["fixture mode only", "no live provider or source runtime calls"],
            success_criteria=["reviewable PRD, dry-run RunnerPlan, and VerificationReport"],
        )
    )

    session.move_to(WorkflowStage.PLANNING)
    blueprint = planning_blueprint_from_div_state(div_state)
    _add_artifact(session, ArtifactKind.PLANNING_BLUEPRINT, "planning-blueprint.json", blueprint.to_dict())

    session.move_to(WorkflowStage.SPEC)
    build_spec = planning_to_build_spec(blueprint)
    prd_package = planning_to_prd_package(blueprint, build_spec=build_spec)
    implementation_brief = implementation_brief_from_prd_package(prd_package, build_spec)
    _add_artifact(session, ArtifactKind.PRD_PACKAGE, "prd-package.json", prd_package.to_dict())
    _add_artifact(session, ArtifactKind.BUILD_SPEC, "build-spec.json", build_spec.to_dict())
    _add_artifact(
        session,
        ArtifactKind.IMPLEMENTATION_BRIEF,
        "implementation-brief.json",
        implementation_brief.to_dict(),
    )

    session.move_to(WorkflowStage.APPROVAL)
    approval = create_spec_approval(
        implementation_brief,
        approval_id=f"{session.id}-spec-approval",
        approved=True,
        approver_role="fixture_user_approval",
    )
    _add_artifact(session, ArtifactKind.SPEC_APPROVAL, "spec-approval.json", approval.to_dict())

    daacs_state = build_spec_to_daacs_initial_state(
        build_spec,
        run_id=session.id,
        config={
            "execution": {
                "mode": "test",
                "parallel_execution": runner_config["parallel_execution_source_value"],
                "max_iterations": runner_config["max_iterations"],
                "max_subgraph_iterations": runner_config["max_subgraph_iterations"],
                "max_failures": runner_config["max_failures"],
            },
            "cli_assistant": {"type": runner_config["cli_assistant_type"]},
        },
        implementation_brief=implementation_brief,
        approval=approval,
        require_approval=True,
    )

    session.move_to(WorkflowStage.BUILD)
    runner_plan, report = DAACSDryRunRunner().run(
        run_id=session.id,
        state=daacs_state,
        implementation_brief=implementation_brief,
        approval=approval,
    )
    assert runner_plan is not None
    _add_artifact(session, ArtifactKind.RUNNER_PLAN, "runner-plan.json", runner_plan.to_dict())

    session.move_to(WorkflowStage.VERIFY)
    _add_artifact(session, ArtifactKind.VERIFICATION_REPORT, "verification-report.json", report.to_dict())
    session.move_to(WorkflowStage.COMPLETE)

    section_titles = _fixture_by_id(fixture, "div-blueprint-identity-v1")["source_identity"]["section_titles"]
    visual_types = set(
        _fixture_by_id(fixture, "div-markdown-visual-identity-v1")["source_identity"][
            "document_quality_signals"
        ]["visual_artifact_types"]
    )
    task_roles = {task["role"] for task in implementation_brief.daacs_tasks}
    planned_roles = {action["role"] for action in runner_plan.planned_actions}
    check_names = {check["name"] for check in report.checks}
    public_payload = public_workflow_session_payload(session)
    public_serialized = json.dumps(public_payload, ensure_ascii=True, sort_keys=True)

    assert session.stage == WorkflowStage.COMPLETE
    assert [artifact.kind for artifact in session.artifacts] == [
        ArtifactKind.PLANNING_BLUEPRINT,
        ArtifactKind.PRD_PACKAGE,
        ArtifactKind.BUILD_SPEC,
        ArtifactKind.IMPLEMENTATION_BRIEF,
        ArtifactKind.SPEC_APPROVAL,
        ArtifactKind.RUNNER_PLAN,
        ArtifactKind.VERIFICATION_REPORT,
    ]
    assert {artifact.run_id for artifact in session.artifacts} == {session.id}
    assert session.id == runner_plan.run_id == report.run_id

    assert set(section_titles) <= set(blueprint.features)
    assert set(section_titles) <= set(prd_package.feature_requirements)
    assert prd_package.evidence_summary
    assert prd_package.evidence_summary[0]["title"] == "DIV source identity fixture"
    assert visual_types <= {item["visual_type"] for item in prd_package.visual_requirements}
    assert visual_types <= {
        item["visual_type"] for item in build_spec.frontend_spec["visual_requirements"]
    }

    assert build_spec.backend_required is True
    assert build_spec.frontend_required is True
    assert len(build_spec.api_spec["endpoints"]) >= 3
    assert len(build_spec.frontend_spec["api_calls"]) == len(build_spec.api_spec["endpoints"])
    assert {"backend", "frontend", "verifier"} <= task_roles
    assert {"backend", "frontend", "verifier"} <= planned_roles
    assert runner_plan.mode == "dry_run"
    assert runner_plan.required_approvals[0]["status"] == "required_before_live"

    assert report.passed is True
    assert {"dry_run_runner_admission", "runner_plan_created", "dry_run_side_effects_zero"} <= check_names
    assert report.metrics["planned_backend_actions"] == 1
    assert report.metrics["planned_frontend_actions"] == 1
    assert report.metrics["planned_verification_actions"] == 1
    assert report.metrics["required_live_approval_count"] == 1
    assert report.metrics["next_action_placeholder_count"] == 1
    assert report.metrics["next_action_required_before_live_count"] == 1
    for key, expected_value in ZERO_DRY_RUN_SIDE_EFFECTS.items():
        assert report.metrics[key] == expected_value
        assert runner_plan.side_effects[key] == expected_value

    assert public_payload["runtime_mode"] == "fixture"
    assert public_payload["approval_lifecycle"] == "synthetic"
    assert public_payload["artifact_count"] == 7
    assert public_payload["execution_boundary"]["live_provider_call_count"] == 0
    assert public_payload["execution_boundary"]["live_source_runtime_call_count"] == 0
    assert public_payload["execution_boundary"]["subprocess_spawn_count"] == 0
    assert set(fixture["coverage_expectations"]["required_trace_ids"]) <= covered_trace_ids
    assert find_forbidden_public_keys(public_payload) == []
    assert find_forbidden_claims(public_serialized) == []
    assert "raw_prompt" not in public_serialized
    assert "provider_payload" not in public_serialized
    assert "file_body" not in public_serialized

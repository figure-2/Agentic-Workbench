import pytest

from packages.daacs_builder.adapters import (
    build_spec_to_daacs_initial_state,
    create_spec_approval,
    ensure_implementation_approved,
    implementation_brief_from_prd_package,
    planning_to_build_spec,
    verification_report_from_daacs_output,
)
from packages.core.pathing import PathBoundaryError
from packages.core.schemas import BuildSpec, SpecApproval
from packages.div_planner.adapters import planning_blueprint_from_div_state, planning_to_prd_package


def test_div_state_to_planning_blueprint():
    state = {
        "idea": {"toc": ["Agentic Workbench"], "rationale": "Need a harness"},
        "plan": {"sections": [{"title": "Planning", "content": "Structure requirements"}]},
        "research": {"evidence_store": [{"title": "Source", "url": "https://example.com"}]},
    }
    blueprint = planning_blueprint_from_div_state(state)
    assert blueprint.title == "Agentic Workbench"
    assert blueprint.features == ["Planning"]
    assert len(blueprint.evidence) == 1


def test_div_global_state_to_planning_blueprint_preserves_core_outputs():
    state = {
        "idea": {
            "planning_style": "Technical Product Brief",
            "rationale": "Need an agent workflow harness with auditable outputs.",
            "toc": ["Agentic Workbench", "Execution Flow"],
            "blueprint": [
                {
                    "title": "Target User",
                    "content": "AI builders who need repeatable agent runs",
                    "guideline": "Describe who uses the workbench",
                    "is_required_from_user": False,
                },
                {
                    "title": "Open Questions",
                    "guideline": "Collect missing deployment constraints",
                    "is_required_from_user": True,
                },
            ],
        },
        "plan": {
            "sections": [
                {
                    "section_number": "1",
                    "title": "Problem",
                    "content": "LLM workflows lack visible contracts.",
                    "evidence": ["Observed in local prototype notes"],
                },
                {
                    "section_number": "2",
                    "title": "Workflow",
                    "content": "Plan, build, verify, and report.",
                    "evidence": [{"title": "Internal fixture", "content": "token=secret-value"}],
                },
            ],
            "final_markdown": "# Agentic Workbench\n\n## Problem\nLLM workflows lack visible contracts.",
            "visual_artifacts": [
                {
                    "section_number": "2",
                    "meta": {
                        "visual_type": "diagram",
                        "purpose": "Show workflow",
                        "content": "Idea -> Plan -> Build -> Verify",
                    },
                }
            ],
        },
        "research": {
            "queries": ["agent workflow harness"],
            "evidence_store": [
                {
                    "title": "Workflow source",
                    "url": "https://example.com/workflow",
                    "content": "Research summary with owner@example.com",
                    "raw_content": "full raw page must not be exposed",
                    "score": 0.91,
                }
            ],
            "search_results": [
                {
                    "query": "agent harness",
                    "title": "Harness article",
                    "url": "https://example.com/harness",
                    "snippet": "Short search result",
                    "content": "Long search result",
                }
            ],
            "analysis_result": "The plan needs a deterministic artifact pipeline.",
        },
        "visual": {
            "artifacts": {
                "architecture": {
                    "section_number": "2",
                    "meta": {"visual_type": "diagram", "purpose": "Architecture"},
                }
            }
        },
        "supervision": {"goal": "Produce a high-quality vibe-based planning document"},
    }

    blueprint = planning_blueprint_from_div_state(state)

    assert blueprint.title == "Agentic Workbench"
    assert blueprint.problem == "Need an agent workflow harness with auditable outputs."
    assert blueprint.features == ["Target User", "Open Questions", "1. Problem", "2. Workflow"]
    assert blueprint.user_flows == ["Target User"]
    assert len(blueprint.evidence) == 5
    assert "owner@example.com" not in str(blueprint.evidence)
    assert "secret-value" not in str(blueprint.evidence)
    assert "raw_content" not in str(blueprint.evidence)
    assert len(blueprint.visual_artifacts) == 2
    assert blueprint.markdown.startswith("# Agentic Workbench")
    assert any("Qdrant/Tavily side effects" in item for item in blueprint.assumptions)


def test_div_state_without_sections_falls_back_to_blueprint_and_toc():
    state = {
        "idea": {
            "toc": ["Fallback Plan", "Risks"],
            "rationale": "Need offline adapter coverage.",
            "blueprint": [
                {"title": "Scope", "guideline": "Define adapter scope", "is_required_from_user": False}
            ],
        },
        "plan": {"sections": [], "final_markdown": ""},
    }

    blueprint = planning_blueprint_from_div_state(state)

    assert blueprint.title == "Fallback Plan"
    assert blueprint.features == ["Scope"]
    assert blueprint.user_flows == ["Scope"]
    assert blueprint.markdown == ""


def test_div_adapter_does_not_import_live_div_dependencies():
    import sys

    blocked_modules = {
        "langchain_upstage",
        "langchain_tavily",
        "qdrant_client",
        "streamlit",
    }

    planning_blueprint_from_div_state(
        {
            "idea": {"toc": ["Offline Adapter"], "rationale": "No live imports"},
            "plan": {"sections": [{"title": "Adapter", "content": "Plain dict only"}]},
        }
    )

    assert not (blocked_modules & set(sys.modules))


def test_div_adapter_handles_malformed_nested_state_without_live_failure():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {"toc": "String Title", "rationale": "String toc should remain whole"},
            "plan": "not-a-plan",
            "research": 123,
        }
    )

    assert blueprint.title == "String Title"
    assert blueprint.problem == "String toc should remain whole"
    assert blueprint.features == ["String Title"]


def test_div_adapter_supports_legacy_string_sections_and_evidence():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {"toc": ["Legacy DIV"], "rationale": "Handle old state shape"},
            "plan": {
                "sections": ["Legacy intro", "Legacy workflow"],
                "visual_artifacts": {},
            },
            "research": {
                "gathered_evidence": ["legacy evidence text"],
                "analysis_result": "analysis-only evidence",
            },
        }
    )

    assert blueprint.features == ["Legacy intro", "Legacy workflow"]
    assert "Legacy intro" in blueprint.markdown
    assert len(blueprint.evidence) == 2
    assert blueprint.evidence[0]["snippet"] == "legacy evidence text"
    assert blueprint.visual_artifacts == []


def test_div_adapter_preserves_single_dict_evidence_item():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {"toc": ["Single Evidence"], "rationale": "Do not split dict values"},
            "research": {
                "evidence_store": {
                    "title": "Single source",
                    "url": "https://example.com/single",
                    "content": "single dict evidence",
                }
            },
        }
    )

    assert len(blueprint.evidence) == 1
    assert blueprint.evidence[0]["title"] == "Single source"
    assert blueprint.evidence[0]["snippet"] == "single dict evidence"


def test_planning_to_build_spec_sets_contract_defaults():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {"toc": ["Workbench"], "rationale": "Need artifacts"},
            "plan": {"sections": [{"title": "Dashboard", "content": "Show status"}]},
        }
    )
    spec = planning_to_build_spec(blueprint)
    assert spec.backend_required is True
    assert spec.frontend_required is True
    assert spec.api_spec["endpoints"][0]["path"] == "/api/v1/health"
    assert spec.api_spec["endpoints"][1]["path"] == "/api/v1/dashboards"
    assert spec.frontend_spec["api_calls"] == [
        "GET /api/v1/health",
        "GET /api/v1/dashboards",
        "POST /api/v1/dashboards",
    ]


def test_planning_to_build_spec_generates_feature_based_contract():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {
                "toc": ["Workbench"],
                "rationale": "Need auditable artifact runs",
                "blueprint": [
                    {"title": "Run Timeline", "guideline": "show run events", "is_required_from_user": False},
                    {"title": "Evidence Review", "guideline": "show evidence", "is_required_from_user": False},
                ],
            },
            "plan": {
                "visual_artifacts": [
                    {
                        "section_number": "1",
                        "meta": {"visual_type": "diagram", "purpose": "Show execution flow"},
                    }
                ]
            },
            "research": {
                "evidence_store": [
                    {"title": "Source", "url": "https://example.com", "content": "Evidence summary"}
                ]
            },
        }
    )

    spec = planning_to_build_spec(blueprint)

    endpoint_paths = [endpoint["path"] for endpoint in spec.api_spec["endpoints"]]
    model_names = [model["name"] for model in spec.api_spec["data_models"]]
    assert endpoint_paths == [
        "/api/v1/health",
        "/api/v1/run-timelines",
        "/api/v1/run-timelines",
        "/api/v1/evidence-reviews",
        "/api/v1/evidence-reviews",
    ]
    assert model_names == ["RunTimeline", "EvidenceReview"]
    assert spec.api_spec["evidence_summary"][0]["snippet"] == "Evidence summary"
    assert spec.frontend_spec["visual_requirements"][0]["visual_type"] == "diagram"
    assert len(spec.acceptance_criteria) == len(spec.api_spec["endpoints"]) * 2 + 2


def test_planning_to_prd_package_creates_reviewable_handoff_artifact():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {
                "toc": ["Workbench"],
                "rationale": "Need auditable artifact runs",
                "blueprint": [{"title": "Run Timeline", "guideline": "show run events"}],
            },
            "research": {
                "evidence_store": [
                    {
                        "title": "Source",
                        "url": "https://example.com",
                        "content": "Evidence summary with owner@example.com",
                        "raw_content": "full raw page",
                    }
                ]
            },
        }
    )
    build_spec = planning_to_build_spec(blueprint)
    package = planning_to_prd_package(blueprint, build_spec=build_spec)
    payload = package.to_dict()

    assert payload["product_name"] == "Workbench"
    assert payload["api_requirements"][0]["path"] == "/api/v1/health"
    assert payload["acceptance_criteria"] == build_spec.acceptance_criteria
    assert "raw_content" not in str(payload)
    assert "owner@example.com" not in str(payload)


def test_implementation_brief_from_prd_package_creates_daacs_tasks_and_hash():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {"toc": ["Workbench"], "rationale": "Need artifacts"},
            "plan": {"sections": [{"title": "Dashboard", "content": "Show status"}]},
        }
    )
    build_spec = planning_to_build_spec(blueprint)
    package = planning_to_prd_package(blueprint, build_spec=build_spec)
    brief = implementation_brief_from_prd_package(package, build_spec)
    payload = brief.to_dict()

    assert payload["app_name"] == build_spec.app_name
    assert payload["build_spec_hash"]
    assert payload["brief_hash"]
    assert {task["role"] for task in payload["daacs_tasks"]} == {
        "backend",
        "frontend",
        "verifier",
    }
    assert payload["approval_required"] is True


def test_build_spec_to_daacs_state_requires_matching_spec_approval_when_enabled():
    blueprint = planning_blueprint_from_div_state(
        {"idea": {"toc": ["Workbench"], "rationale": "Need artifacts"}}
    )
    build_spec = planning_to_build_spec(blueprint)
    package = planning_to_prd_package(blueprint, build_spec=build_spec)
    brief = implementation_brief_from_prd_package(package, build_spec)
    approval = create_spec_approval(brief, approval_id="approval-run-test", approved=True)

    state = build_spec_to_daacs_initial_state(
        build_spec,
        run_id="run-test",
        implementation_brief=brief,
        approval=approval,
        require_approval=True,
    )

    assert state["approved_build_spec_hash"] == brief.build_spec_hash
    assert state["spec_approval_id"] == "approval-run-test"
    assert state["spec_approval_status"] == "approved"
    assert state["implementation_brief_hash"] == brief.to_dict()["brief_hash"]


def test_build_spec_to_daacs_state_blocks_missing_or_mismatched_spec_approval():
    blueprint = planning_blueprint_from_div_state(
        {"idea": {"toc": ["Workbench"], "rationale": "Need artifacts"}}
    )
    build_spec = planning_to_build_spec(blueprint)
    package = planning_to_prd_package(blueprint, build_spec=build_spec)
    brief = implementation_brief_from_prd_package(package, build_spec)

    with pytest.raises(ValueError, match="spec approval is required"):
        build_spec_to_daacs_initial_state(
            build_spec,
            run_id="run-test",
            implementation_brief=brief,
            require_approval=True,
        )

    mismatched = SpecApproval(
        approval_id="approval-mismatch",
        approved=True,
        approved_build_spec_hash="not-the-current-hash",
        approved_implementation_brief_hash=brief.to_dict()["brief_hash"],
        approval_scope=["prd_package", "implementation_brief", "build_spec", "daacs_build"],
    )
    with pytest.raises(ValueError, match="approval hash does not match"):
        ensure_implementation_approved(brief, mismatched)


def test_build_spec_to_daacs_state_maps_run_id():
    spec = planning_to_build_spec(
        planning_blueprint_from_div_state(
            {"idea": {"toc": ["Workbench"], "rationale": "Need artifacts"}}
        )
    )
    state = build_spec_to_daacs_initial_state(spec, run_id="run-test")
    assert state["session_id"] == "run-test"
    assert state["api_spec"] == spec.api_spec
    assert state["frontend_spec"] == spec.frontend_spec
    assert state["acceptance_criteria"] == spec.acceptance_criteria
    assert state["source_blueprint_title"] == spec.source_blueprint_title
    assert state["build_contract"]["api_endpoint_count"] == len(spec.api_spec["endpoints"])
    assert state["build_contract"]["frontend_api_call_count"] == len(spec.frontend_spec["api_calls"])
    assert state["project_dir"] == "examples/demo-projects/run-test"
    assert state["mode"] == "test"
    assert state["backend_status"] == "pending"
    assert state["frontend_status"] == "pending"
    assert state["current_phase"] == "spec_ready"
    assert state["completed_phases"] == ["build_spec_created"]
    assert state["cli_assistant_available"] is False


def test_build_spec_to_daacs_state_uses_runtime_config_without_live_call():
    spec = planning_to_build_spec(
        planning_blueprint_from_div_state(
            {"idea": {"toc": ["Workbench"], "rationale": "Need artifacts"}}
        )
    )
    state = build_spec_to_daacs_initial_state(
        spec,
        run_id="run-test",
        project_dir="runs/run-test",
        config={
            "execution": {
                "mode": "test",
                "parallel_execution": True,
                "max_iterations": 3,
                "max_subgraph_iterations": 1,
                "max_failures": 2,
            },
            "cli_assistant": {"type": "codex"},
        },
    )

    assert state["project_dir"] == "runs/run-test"
    assert state["parallel_execution"] is True
    assert state["max_iterations"] == 3
    assert state["max_subgraph_iterations"] == 1
    assert state["max_failures"] == 2
    assert state["turn_history"][0]["acceptance_criteria_count"] == len(spec.acceptance_criteria)


@pytest.mark.parametrize("run_id", ["../x", r"..\x", "/abs/path", r"F:\x", "run/x", "run\x00x"])
def test_build_spec_to_daacs_state_rejects_unsafe_run_id(run_id):
    spec = planning_to_build_spec(
        planning_blueprint_from_div_state(
            {"idea": {"toc": ["Workbench"], "rationale": "Need artifacts"}}
        )
    )

    with pytest.raises(ValueError):
        build_spec_to_daacs_initial_state(spec, run_id=run_id)


def test_build_spec_validate_requires_backend_and_frontend_contracts():
    with pytest.raises(ValueError):
        BuildSpec(
            app_name="bad",
            goal="missing endpoint contract",
            backend_required=True,
            frontend_required=True,
            api_spec={},
            frontend_spec={},
        ).validate()


def test_verification_report_from_daacs_output_counts_files():
    report = verification_report_from_daacs_output(
        run_id="run-test",
        daacs_output={
            "compatibility_verified": True,
            "backend_files": {"main.py": "print('ok')"},
            "frontend_files": {"src/App.jsx": "export default App"},
            "compatibility_issues": [],
        },
    )
    assert report.passed is True
    assert report.metrics["backend_file_count"] == 1
    assert report.metrics["frontend_file_count"] == 1


@pytest.mark.parametrize(
    "filename",
    ["../secret.txt", "backend/../secret.txt", r"frontend\..\x", "%2e%2e/secret.txt"],
)
def test_verification_report_from_daacs_output_rejects_namespace_escape(filename):
    with pytest.raises(PathBoundaryError):
        verification_report_from_daacs_output(
            run_id="run-test",
            daacs_output={
                "compatibility_verified": True,
                "backend_files": {filename: "print('unsafe')"},
                "frontend_files": {},
                "compatibility_issues": [],
            },
        )

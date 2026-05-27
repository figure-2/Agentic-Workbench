from packages.daacs_builder.adapters import (
    build_spec_to_daacs_initial_state,
    planning_to_build_spec,
)
from packages.daacs_builder.runner_provider import (
    ApprovalRecord,
    RunnerRequest,
    default_runner_provider_registry,
)
from packages.div_planner.adapters import planning_blueprint_from_div_state


def _state():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {
                "toc": ["Agentic Workbench"],
                "rationale": "Need a provider registry boundary.",
                "blueprint": [
                    {"title": "Runner Registry", "guideline": "route runner modes"},
                    {"title": "Approval Gate", "guideline": "block live execution"},
                ],
            }
        }
    )
    spec = planning_to_build_spec(blueprint)
    return build_spec_to_daacs_initial_state(spec, run_id="run-provider")


def test_default_registry_routes_offline_provider_without_live_execution():
    result = default_runner_provider_registry().run(
        RunnerRequest(run_id="run-provider", mode="offline", state=_state())
    )

    assert result.status == "passed"
    assert result.mode == "offline"
    assert result.verification_report.passed is True
    assert result.verification_report.metrics["boundary_mode"] == "offline"
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["subprocess_calls"] == 0
    assert result.verification_report.metrics["filesystem_writes"] == 0
    assert result.artifact_manifest == []


def test_registry_rejects_unknown_mode_as_blocked_result():
    result = default_runner_provider_registry().run(
        RunnerRequest(run_id="run-provider", mode="experimental", state=_state())
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert result.mode == "experimental"
    assert result.verification_report.passed is False
    assert checks["runner_mode_known"] is False
    assert "unknown runner mode" in result.verification_report.errors[0]
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["approval_bypass_count"] == 0


def test_registry_blocks_live_mode_without_approval():
    result = default_runner_provider_registry().run(
        RunnerRequest(run_id="run-provider", mode="live", state=_state())
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert result.verification_report.passed is False
    assert checks["live_approval_present"] is False
    assert result.verification_report.metrics["approval_bypass_count"] == 1
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["cli_agent_invocations"] == 0


def test_registry_blocks_live_mode_with_malformed_approval():
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=_state(),
            approval="approved in chat",
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_approval_valid"] is False
    assert result.verification_report.metrics["approval_bypass_count"] == 1
    assert result.verification_report.metrics["provider_calls"] == 0


def test_registry_keeps_live_mode_blocked_even_with_skeleton_approval():
    approval = ApprovalRecord(
        approved_by="local-user",
        approved_at="2026-05-27T00:00:00Z",
        run_id="run-provider",
        mode="live",
        allowed_operations=["provider_call"],
        max_provider_calls=1,
        max_subprocess_calls=0,
        max_package_installs=0,
        max_server_starts=0,
        max_files_written=0,
        workspace_root="runs/run-provider",
        expires_at="2026-05-27T01:00:00Z",
        rollback_plan_id="rollback-run-provider",
        audit_log_id="audit-run-provider",
    )

    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=_state(),
            approval=approval,
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_runner_registered"] is False
    assert result.verification_report.metrics["approval_bypass_count"] == 0
    assert result.verification_report.metrics["provider_calls"] == 0

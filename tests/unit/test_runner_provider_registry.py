import builtins
import os
import subprocess
import sys
import socket
import urllib.request
from pathlib import Path

from packages.daacs_builder.adapters import (
    build_spec_to_daacs_initial_state,
    create_spec_approval,
    implementation_brief_from_prd_package,
    planning_to_build_spec,
)
from packages.daacs_builder.runner_provider import (
    ApprovalRecord,
    RunnerPolicy,
    RunnerRequest,
    default_runner_provider_registry,
)
from packages.div_planner.adapters import planning_blueprint_from_div_state, planning_to_prd_package


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


def _approved_dry_run_parts():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {
                "toc": ["Agentic Workbench"],
                "rationale": "Need a dry-run runner plan.",
                "blueprint": [
                    {"title": "Runner Plan", "guideline": "plan DAACS actions"},
                    {"title": "Approval Gate", "guideline": "require content approval"},
                ],
            }
        }
    )
    spec = planning_to_build_spec(blueprint)
    prd_package = planning_to_prd_package(blueprint, build_spec=spec)
    brief = implementation_brief_from_prd_package(prd_package, spec)
    approval = create_spec_approval(brief, approval_id="approval-run-provider", approved=True)
    state = build_spec_to_daacs_initial_state(
        spec,
        run_id="run-provider",
        implementation_brief=brief,
        approval=approval,
        require_approval=True,
    )
    return state, brief, approval


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


def test_default_registry_registers_offline_and_dry_run_only():
    assert default_runner_provider_registry().registered_modes() == ["dry_run", "offline"]


def test_default_registry_routes_dry_run_provider_without_side_effects():
    state, brief, approval = _approved_dry_run_parts()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
            policy=RunnerPolicy(
                allow_provider_calls=True,
                allow_subprocess=True,
                allow_package_install=True,
                allow_server_start=True,
                allow_filesystem_write=True,
                allow_network=True,
            ),
        )
    )
    plan_payload = result.plan.to_dict()

    assert result.status == "approval_required"
    assert result.mode == "dry_run"
    assert result.verification_report.passed is True
    assert result.verification_report.generated_files == []
    assert result.verification_report.metrics["boundary_mode"] == "dry_run"
    assert result.verification_report.metrics["executed_action_count"] == 0
    assert result.verification_report.metrics["simulated_action_count"] > 0
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["subprocess_calls"] == 0
    assert result.verification_report.metrics["package_install_calls"] == 0
    assert result.verification_report.metrics["server_start_calls"] == 0
    assert result.verification_report.metrics["filesystem_writes"] == 0
    assert result.plan is not None
    assert plan_payload["mode"] == "dry_run"
    assert plan_payload["implementation_brief_hash"] == brief.to_dict()["brief_hash"]
    assert plan_payload["build_spec_hash"] == brief.build_spec_hash
    assert plan_payload["side_effects"]["provider_calls"] == 0
    assert "backend_files" not in str(plan_payload)
    assert "frontend_files" not in str(plan_payload)


def test_dry_run_blocks_without_spec_approval():
    state, brief, _approval = _approved_dry_run_parts()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
        )
    )

    assert result.status == "blocked"
    assert result.plan is None
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["subprocess_calls"] == 0
    assert result.verification_report.metrics["filesystem_writes"] == 0
    assert result.verification_report.metrics["spec_approval_missing_block_count"] == 1


def test_dry_run_blocks_mismatched_spec_approval():
    state, brief, approval = _approved_dry_run_parts()
    approval.approved_build_spec_hash = "not-current"
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "blocked"
    assert result.plan is None
    assert result.verification_report.metrics["spec_approval_mismatch_block_count"] == 1
    assert result.verification_report.metrics["provider_calls"] == 0


def test_dry_run_blocks_mutated_implementation_brief_after_approval():
    state, brief, approval = _approved_dry_run_parts()
    brief.daacs_tasks.append(
        {
            "id": "mutated-live-task",
            "role": "backend",
            "summary": "backend_llm.invoke(prompt)",
        }
    )

    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "blocked"
    assert result.plan is None
    assert result.verification_report.metrics["spec_approval_mismatch_block_count"] == 1
    assert result.verification_report.metrics["provider_calls"] == 0


def test_dry_run_rejects_unsafe_state_before_planning():
    state, brief, approval = _approved_dry_run_parts()
    state["backend_files"] = {"main.py": "print('should not exist in dry-run')"}

    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "blocked"
    assert result.plan is None
    assert result.verification_report.metrics["dry_run_state_rejection_count"] == 1
    assert result.verification_report.metrics["filesystem_writes"] == 0


def test_dry_run_does_not_call_process_network_or_file_write(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("dry-run attempted a blocked side effect")

    monkeypatch.setattr(subprocess, "run", fail_if_called)
    monkeypatch.setattr(subprocess, "Popen", fail_if_called)
    monkeypatch.setattr(os, "system", fail_if_called)
    monkeypatch.setattr(builtins, "open", fail_if_called)
    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "mkdir", fail_if_called)
    monkeypatch.setattr(socket, "create_connection", fail_if_called)
    monkeypatch.setattr(urllib.request, "urlopen", fail_if_called)

    state, brief, approval = _approved_dry_run_parts()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "approval_required"
    assert result.verification_report.metrics["executed_action_count"] == 0
    assert result.verification_report.metrics["network_calls"] == 0


def test_dry_run_does_not_import_provider_or_daacs_runtime_even_with_tripwire(monkeypatch):
    real_import = builtins.__import__

    def fail_blocked_import(name, *args, **kwargs):
        blocked_prefixes = (
            "daacs",
            "langchain_upstage",
            "langchain_tavily",
            "qdrant_client",
            "openai",
            "anthropic",
        )
        if name.startswith(blocked_prefixes):
            raise AssertionError(f"dry-run attempted blocked import: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_blocked_import)
    state, brief, approval = _approved_dry_run_parts()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "approval_required"
    assert result.verification_report.metrics["provider_imports"] == 0


def test_dry_run_plan_redacts_public_payloads():
    state, brief, approval = _approved_dry_run_parts()
    brief.constraints.append("Authorization: Bearer live-secret-token")
    approval = create_spec_approval(brief, approval_id="approval-redacted", approved=True)

    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )
    serialized = str(
        {
            "plan": result.plan.to_dict(),
            "audit_events": result.audit_events,
            "report": result.verification_report.to_dict(),
        }
    )

    assert result.status == "approval_required"
    assert "live-secret-token" not in serialized
    assert "Authorization" not in serialized
    assert "raw_content" not in serialized


def test_dry_run_does_not_import_daacs_or_provider_runtime_modules():
    blocked_modules = {
        "daacs.llm.cli_executor",
        "daacs.graph.backend_subgraph",
        "daacs.graph.frontend_subgraph",
        "langchain_upstage",
        "langchain_tavily",
        "qdrant_client",
    }

    state, brief, approval = _approved_dry_run_parts()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "approval_required"
    assert not (blocked_modules & set(sys.modules))


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

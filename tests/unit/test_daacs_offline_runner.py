import builtins
import os
import subprocess
import sys
from pathlib import Path

import pytest

from packages.daacs_builder.adapters import (
    build_spec_to_daacs_initial_state,
    planning_to_build_spec,
)
from packages.daacs_builder.offline_runner import (
    BLOCKED_OPERATION_PATTERNS,
    DAACSOfflineRunner,
    find_blocked_operation_attempts,
)
from packages.div_planner.adapters import planning_blueprint_from_div_state


def _offline_state():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {
                "toc": ["Agentic Workbench"],
                "rationale": "Need a deterministic offline DAACS boundary.",
                "blueprint": [
                    {"title": "Run Timeline", "guideline": "show run events"},
                    {"title": "Evidence Review", "guideline": "show evidence"},
                ],
            }
        }
    )
    spec = planning_to_build_spec(blueprint)
    return build_spec_to_daacs_initial_state(spec, run_id="run-offline")


def test_daacs_offline_runner_accepts_mapped_state_without_live_execution():
    report = DAACSOfflineRunner().run(_offline_state())
    checks = {check["name"]: check["passed"] for check in report.checks}

    assert report.passed is True
    assert report.generated_files == []
    assert checks["offline_runner_admission"] is True
    assert checks["state_contract_present"] is True
    assert checks["project_dir_safe"] is True
    assert checks["cli_agent_blocked"] is True
    assert checks["provider_calls_blocked"] is True
    assert checks["subprocess_blocked"] is True
    assert checks["package_install_blocked"] is True
    assert checks["server_start_blocked"] is True
    assert checks["filesystem_write_blocked"] is True
    assert report.metrics["blocked_operation_family_count"] == len(BLOCKED_OPERATION_PATTERNS)
    assert report.metrics["detected_blocked_operation_count"] == 0
    assert report.metrics["live_llm_calls"] == 0
    assert report.metrics["live_api_calls"] == 0
    assert report.metrics["provider_calls"] == 0
    assert report.metrics["cli_agent_invocations"] == 0
    assert report.metrics["subprocess_calls"] == 0
    assert report.metrics["package_install_calls"] == 0
    assert report.metrics["server_start_calls"] == 0
    assert report.metrics["filesystem_writes"] == 0
    assert report.metrics["backend_file_count"] == 0
    assert report.metrics["frontend_file_count"] == 0
    assert report.metrics["issue_count"] == 0
    assert report.metrics["unsafe_state_rejection_count"] == 0


@pytest.mark.parametrize(
    ("operation", "payload"),
    [
        ("cli_agent", "npx @openai/codex exec --sandbox danger-full-access"),
        ("provider_call", "backend_llm.invoke(prompt)"),
        ("subprocess", "subprocess.run('python -m py_compile main.py', shell=True)"),
        ("package_install", "npm install"),
        ("server_start", "python -m uvicorn main:app --reload"),
        ("filesystem_write", "Path('main.py').write_text(code)"),
    ],
)
def test_daacs_offline_runner_detects_blocked_operation_payloads(operation, payload):
    state = _offline_state()
    state["next_actions"] = [{"command": payload}]

    findings = find_blocked_operation_attempts(state)
    report = DAACSOfflineRunner().run(state)

    assert any(finding["operation"] == operation for finding in findings)
    assert report.passed is False
    assert report.metrics["detected_blocked_operation_count"] >= 1
    assert any(f"blocked {operation}" in error for error in report.errors)
    assert report.metrics["subprocess_calls"] == 0
    assert report.metrics["package_install_calls"] == 0
    assert report.metrics["server_start_calls"] == 0
    assert report.metrics["provider_calls"] == 0


def test_daacs_offline_runner_redacts_blocked_finding_text():
    state = _offline_state()
    state["next_actions"] = [
        {
            "command": (
                "backend_llm.invoke(prompt) with Bearer sk-secret-value "
                "for owner@example.com"
            )
        }
    ]

    findings = find_blocked_operation_attempts(state)
    report = DAACSOfflineRunner().run(state)

    assert findings
    assert "text" not in findings[0]
    assert "finding_hash" in findings[0]
    assert "redacted_excerpt" in findings[0]
    assert "sk-secret-value" not in str(findings)
    assert "owner@example.com" not in str(findings)
    assert "sk-secret-value" not in str(report.errors)
    assert "owner@example.com" not in str(report.errors)
    assert report.metrics["raw_secret_log_count"] == 0


def test_daacs_offline_runner_redacts_blocked_finding_path_keys():
    state = _offline_state()
    state["next_actions"] = [
        {
            "backend_llm.invoke(prompt) Bearer sk-path-secret owner@example.com": "planned"
        }
    ]

    findings = find_blocked_operation_attempts(state)
    report = DAACSOfflineRunner().run(state)

    assert findings
    assert "text" not in findings[0]
    assert "sk-path-secret" not in str(findings)
    assert "owner@example.com" not in str(findings)
    assert "sk-path-secret" not in str(report.errors)
    assert "owner@example.com" not in str(report.errors)
    assert report.metrics["raw_secret_log_count"] == 0


def test_daacs_offline_runner_rejects_cli_agent_availability():
    state = _offline_state()
    state["cli_assistant_available"] = True

    report = DAACSOfflineRunner().run(state)
    checks = {check["name"]: check["passed"] for check in report.checks}

    assert report.passed is False
    assert checks["cli_agent_blocked"] is False
    assert any("cli_assistant_available" in error for error in report.errors)


def test_daacs_offline_runner_rejects_unsafe_project_dir():
    state = _offline_state()
    state["project_dir"] = "../escape"

    report = DAACSOfflineRunner().run(state)
    checks = {check["name"]: check["passed"] for check in report.checks}

    assert report.passed is False
    assert checks["project_dir_safe"] is False
    assert any("project_dir" in error for error in report.errors)


@pytest.mark.parametrize(
    ("field", "value", "check_name"),
    [
        ("mode", "live", "offline_mode_declared"),
        ("llm_sources", {"backend": "solar-pro-3"}, "llm_sources_empty"),
        ("backend_files", {"main.py": "print('generated')"}, "generated_files_absent"),
        ("frontend_files", {"src/App.jsx": "export default App"}, "generated_files_absent"),
        ("all_files", {"backend/main.py": "print('generated')"}, "generated_files_absent"),
        ("compatibility_verified", True, "preverified_status_rejected"),
    ],
)
def test_daacs_offline_runner_rejects_unsafe_state_injections(field, value, check_name):
    state = _offline_state()
    state[field] = value

    report = DAACSOfflineRunner().run(state)
    checks = {check["name"]: check["passed"] for check in report.checks}

    assert report.passed is False
    assert checks[check_name] is False
    assert report.metrics["unsafe_state_rejection_count"] >= 1


def test_daacs_offline_runner_requires_state_contract_keys():
    state = _offline_state()
    del state["build_contract"]

    report = DAACSOfflineRunner().run(state)
    checks = {check["name"]: check for check in report.checks}

    assert report.passed is False
    assert checks["state_contract_present"]["passed"] is False
    assert checks["state_contract_present"]["missing_keys"] == ["build_contract"]


def test_daacs_offline_runner_does_not_call_subprocess_or_write_files(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("offline runner attempted a blocked side effect")

    monkeypatch.setattr(subprocess, "run", fail_if_called)
    monkeypatch.setattr(subprocess, "Popen", fail_if_called)
    monkeypatch.setattr(os, "system", fail_if_called)
    monkeypatch.setattr(builtins, "open", fail_if_called)
    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "mkdir", fail_if_called)

    report = DAACSOfflineRunner().run(_offline_state())

    assert report.passed is True
    assert report.metrics["subprocess_calls"] == 0
    assert report.metrics["filesystem_writes"] == 0


def test_daacs_offline_runner_does_not_import_daacs_or_provider_runtime_modules():
    blocked_modules = {
        "daacs.llm.cli_executor",
        "daacs.graph.backend_subgraph",
        "daacs.graph.frontend_subgraph",
        "langchain_upstage",
        "langchain_tavily",
        "qdrant_client",
    }

    DAACSOfflineRunner().run(_offline_state())

    assert not (blocked_modules & set(sys.modules))

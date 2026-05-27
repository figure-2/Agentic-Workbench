"""Offline DAACS runner boundary.

This module accepts a DAACS-compatible initial state and verifies the state
contract without importing or executing the original DAACS runtime.
"""

from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from packages.core.pathing import normalize_public_relative_path
from packages.core.schemas import VerificationReport
from packages.core.security import redact_text


BLOCKED_OPERATION_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "cli_agent": (
        re.compile(r"\bnpx\s+@openai/codex\b", re.IGNORECASE),
        re.compile(r"\bcodex\s+exec\b", re.IGNORECASE),
        re.compile(r"\bclaude\s+code\b", re.IGNORECASE),
        re.compile(r"\bgemini\s+(-p|--prompt)\b", re.IGNORECASE),
        re.compile(r"\bCodexClient\.execute\b", re.IGNORECASE),
    ),
    "provider_call": (
        re.compile(r"\b[a-z_]*llm\.invoke\s*\(", re.IGNORECASE),
        re.compile(r"\bprovider_call\b", re.IGNORECASE),
        re.compile(r"\bChatOpenAI\b", re.IGNORECASE),
        re.compile(r"\bChatUpstage\b", re.IGNORECASE),
        re.compile(r"\blangchain_upstage\b", re.IGNORECASE),
    ),
    "subprocess": (
        re.compile(r"\bsubprocess\.(run|Popen|call|check_output)\b", re.IGNORECASE),
        re.compile(r"\bos\.system\s*\(", re.IGNORECASE),
        re.compile(r"\bshell\s*=\s*True\b", re.IGNORECASE),
    ),
    "package_install": (
        re.compile(r"\bnpm\s+install\b", re.IGNORECASE),
        re.compile(r"\bpnpm\s+install\b", re.IGNORECASE),
        re.compile(r"\byarn\s+install\b", re.IGNORECASE),
        re.compile(r"\bpip\s+install\b", re.IGNORECASE),
    ),
    "server_start": (
        re.compile(r"\buvicorn\b", re.IGNORECASE),
        re.compile(r"\bnpm\s+run\s+(dev|start)\b", re.IGNORECASE),
        re.compile(r"\bpython\s+-m\s+http\.server\b", re.IGNORECASE),
        re.compile(r"\burlopen\s*\(", re.IGNORECASE),
    ),
    "filesystem_write": (
        re.compile(r"\bopen\s*\([^)]*,\s*[\"']w", re.IGNORECASE),
        re.compile(r"\bPath\s*\([^)]*\)\.write_text\b", re.IGNORECASE),
        re.compile(r"\bos\.makedirs\b", re.IGNORECASE),
        re.compile(r"\bwrite_file\b", re.IGNORECASE),
    ),
}

REQUIRED_STATE_KEYS = (
    "session_id",
    "project_dir",
    "mode",
    "cli_assistant_available",
    "api_spec",
    "frontend_spec",
    "acceptance_criteria",
    "build_contract",
    "current_phase",
    "turn_history",
)

OFFLINE_MODES = {"test", "fixture", "offline", "offline-fixture"}


def _iter_text(value: Any, *, path: str = "$") -> list[tuple[str, str]]:
    if isinstance(value, dict):
        items: list[tuple[str, str]] = []
        for key, item in value.items():
            key_path = f"{path}.{key}"
            items.append((key_path, str(key)))
            items.extend(_iter_text(item, path=key_path))
        return items
    if isinstance(value, list):
        items = []
        for index, item in enumerate(value):
            items.extend(_iter_text(item, path=f"{path}[{index}]"))
        return items
    if isinstance(value, tuple):
        items = []
        for index, item in enumerate(value):
            items.extend(_iter_text(item, path=f"{path}[{index}]"))
        return items
    if isinstance(value, str):
        return [(path, value)]
    return []


def find_blocked_operation_attempts(state: dict[str, Any]) -> list[dict[str, str]]:
    """Find blocked DAACS runtime operations encoded in state text fields."""
    findings: list[dict[str, str]] = []
    for path, text in _iter_text(state):
        for operation, patterns in BLOCKED_OPERATION_PATTERNS.items():
            if any(pattern.search(text) for pattern in patterns):
                redacted_excerpt = redact_text(text[:160])
                findings.append(
                    {
                        "operation": operation,
                        "path": redact_text(path),
                        "finding_hash": sha256(text.encode("utf-8")).hexdigest()[:16],
                        "redacted_excerpt": redacted_excerpt,
                        "classification": "blocked_operation",
                    }
                )
    return findings


def _endpoint_labels(api_spec: dict[str, Any]) -> list[str]:
    endpoints = api_spec.get("endpoints") or []
    labels: list[str] = []
    for endpoint in endpoints:
        if isinstance(endpoint, dict):
            method = str(endpoint.get("method", "GET")).upper()
            path = str(endpoint.get("path", ""))
            if path:
                labels.append(f"{method} {path}")
    return labels


def _zero_execution_metrics() -> dict[str, int]:
    return {
        "backend_file_count": 0,
        "frontend_file_count": 0,
        "issue_count": 0,
        "live_llm_calls": 0,
        "live_api_calls": 0,
        "provider_calls": 0,
        "cli_agent_invocations": 0,
        "subprocess_calls": 0,
        "package_install_calls": 0,
        "server_start_calls": 0,
        "filesystem_writes": 0,
        "provider_imports": 0,
        "network_calls": 0,
        "blocked_operation_count": len(BLOCKED_OPERATION_PATTERNS),
        "provider_import_attempt_count": 0,
        "subprocess_attempt_count": 0,
        "filesystem_write_attempt_count": 0,
        "unsafe_state_rejection_count": 0,
    }


class DAACSOfflineRunner:
    """Validate a DAACSState without opening any live execution surface."""

    def run(self, state: dict[str, Any]) -> VerificationReport:
        checks: list[dict[str, Any]] = []
        errors: list[str] = []

        if not isinstance(state, dict):
            return VerificationReport(
                run_id="offline-run",
                passed=False,
                checks=[{"name": "offline_runner_admission", "passed": False}],
                errors=["DAACS offline runner requires a state dictionary."],
                generated_files=[],
                metrics={
                    **_zero_execution_metrics(),
                    "blocked_operation_family_count": len(BLOCKED_OPERATION_PATTERNS),
                    "detected_blocked_operation_count": 0,
                    "state_check_count": len(REQUIRED_STATE_KEYS),
                    "state_key_count": 0,
                },
            )

        run_id = str(state.get("session_id") or "offline-run")
        checks.append({"name": "offline_runner_admission", "passed": True})

        missing_keys = [key for key in REQUIRED_STATE_KEYS if key not in state]
        checks.append(
            {
                "name": "state_contract_present",
                "passed": not missing_keys,
                "missing_keys": missing_keys,
            }
        )
        if missing_keys:
            errors.append(f"DAACSState is missing required keys: {', '.join(missing_keys)}")

        mode = str(state.get("mode", ""))
        checks.append(
            {
                "name": "offline_mode_declared",
                "passed": mode in OFFLINE_MODES,
                "mode": mode,
            }
        )
        if mode not in OFFLINE_MODES:
            errors.append(f"DAACSState mode is not offline/test safe: {mode}")

        project_dir = str(state.get("project_dir", ""))
        try:
            normalized_project_dir = normalize_public_relative_path(project_dir)
            project_dir_safe = True
        except ValueError as exc:
            normalized_project_dir = ""
            project_dir_safe = False
            errors.append(f"project_dir is outside the offline boundary: {exc}")
        checks.append(
            {
                "name": "project_dir_safe",
                "passed": project_dir_safe,
                "project_dir": normalized_project_dir,
            }
        )

        cli_available = bool(state.get("cli_assistant_available"))
        checks.append(
            {
                "name": "cli_agent_blocked",
                "passed": not cli_available,
                "cli_assistant_available": cli_available,
            }
        )
        if cli_available:
            errors.append("cli_assistant_available must remain false in offline runner mode.")

        llm_sources = state.get("llm_sources") or {}
        llm_sources_empty = not bool(llm_sources)
        checks.append(
            {
                "name": "llm_sources_empty",
                "passed": llm_sources_empty,
                "llm_source_count": len(llm_sources) if isinstance(llm_sources, dict) else 1,
            }
        )
        if not llm_sources_empty:
            errors.append("llm_sources must remain empty in offline runner mode.")

        api_spec = state.get("api_spec") if isinstance(state.get("api_spec"), dict) else {}
        frontend_spec = state.get("frontend_spec") if isinstance(state.get("frontend_spec"), dict) else {}
        endpoint_labels = _endpoint_labels(api_spec)
        frontend_calls = [
            str(call) for call in frontend_spec.get("api_calls", []) if str(call).strip()
        ]
        missing_frontend_calls = [
            endpoint for endpoint in endpoint_labels if endpoint not in frontend_calls
        ]
        checks.append(
            {
                "name": "api_frontend_contract_aligned",
                "passed": not missing_frontend_calls,
                "missing_frontend_calls": missing_frontend_calls,
            }
        )
        if missing_frontend_calls:
            errors.append(
                "frontend_spec.api_calls is missing BuildSpec endpoints: "
                + ", ".join(missing_frontend_calls)
            )

        backend_file_count = len(state.get("backend_files") or {})
        frontend_file_count = len(state.get("frontend_files") or {})
        all_file_count = len(state.get("all_files") or {})
        generated_file_count = backend_file_count + frontend_file_count + all_file_count
        generated_files_absent = generated_file_count == 0
        checks.append(
            {
                "name": "generated_files_absent",
                "passed": generated_files_absent,
                "generated_file_count": generated_file_count,
            }
        )
        if not generated_files_absent:
            errors.append("offline runner boundary must not receive generated file payloads.")

        preverified = bool(state.get("compatibility_verified"))
        checks.append(
            {
                "name": "preverified_status_rejected",
                "passed": not preverified,
                "compatibility_verified": preverified,
            }
        )
        if preverified:
            errors.append("compatibility_verified must not be pre-seeded as true in offline runner mode.")

        findings = find_blocked_operation_attempts(state)
        findings_by_operation = {
            operation: [
                finding for finding in findings if finding["operation"] == operation
            ]
            for operation in BLOCKED_OPERATION_PATTERNS
        }
        check_names = {
            "provider_call": "provider_calls_blocked",
            "subprocess": "subprocess_blocked",
            "package_install": "package_install_blocked",
            "server_start": "server_start_blocked",
            "filesystem_write": "filesystem_write_blocked",
        }
        for operation, name in check_names.items():
            operation_findings = findings_by_operation[operation]
            checks.append(
                {
                    "name": name,
                    "passed": not operation_findings,
                    "finding_count": len(operation_findings),
                }
            )
        cli_findings = findings_by_operation["cli_agent"]
        checks.append(
            {
                "name": "cli_agent_command_blocked",
                "passed": not cli_findings,
                "finding_count": len(cli_findings),
            }
        )
        if findings:
            for finding in findings:
                errors.append(
                    "blocked "
                    f"{finding['operation']} attempt at {finding['path']}: "
                    f"{finding['redacted_excerpt']}"
                )

        metrics = {
            **_zero_execution_metrics(),
            "blocked_operation_family_count": len(BLOCKED_OPERATION_PATTERNS),
            "detected_blocked_operation_count": len(findings),
            "state_check_count": len(REQUIRED_STATE_KEYS),
            "state_key_count": len(state),
            "api_endpoint_count": len(endpoint_labels),
            "frontend_api_call_count": len(frontend_calls),
            "acceptance_criteria_count": len(state.get("acceptance_criteria") or []),
            "backend_file_count": backend_file_count,
            "frontend_file_count": frontend_file_count,
            "issue_count": len(errors),
            "provider_import_attempt_count": len(findings_by_operation["provider_call"]),
            "subprocess_attempt_count": len(findings_by_operation["subprocess"]),
            "filesystem_write_attempt_count": len(findings_by_operation["filesystem_write"]),
            "raw_secret_log_count": 0,
            "unsafe_state_rejection_count": sum(
                1
                for check in checks
                if check["name"]
                in {
                    "state_contract_present",
                    "offline_mode_declared",
                    "project_dir_safe",
                    "cli_agent_blocked",
                    "llm_sources_empty",
                    "generated_files_absent",
                    "preverified_status_rejected",
                    "api_frontend_contract_aligned",
                }
                and not check["passed"]
            ),
        }

        return VerificationReport(
            run_id=run_id,
            passed=all(check["passed"] for check in checks),
            checks=checks,
            errors=errors,
            generated_files=[],
            metrics=metrics,
        )

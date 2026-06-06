"""Render an AW-APP-01 portfolio-facing artifact preview from public summary."""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import sys
from typing import Any


DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))

from packages.core.public_projection import assert_public_projection_safe
from run_local_demo import run_demo


ARTIFACT_PREVIEW_TITLE = "Agentic Workbench Artifact Preview"
REQUIRED_ARTIFACT_LABELS = ("backend", "frontend", "verification_report")
REQUIRED_GENERATED_FILE_LABELS = (
    "readme",
    "package_json",
    "index_html",
    "main_entrypoint",
    "app_component",
    "api_client",
    "vite_config",
    "tsconfig_json",
    "verification_notes",
)
DOCUMENT_ARTIFACTS = (
    "planning_blueprint",
    "prd_package",
    "implementation_brief",
    "runner_plan",
    "verification_report",
)


def _text(value: object, default: str = "unknown") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _count(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _short_hash(value: object) -> str:
    text = _text(value, "")
    return text[:12] if text else "none"


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def build_artifact_preview_model(summary: dict[str, Any]) -> dict[str, Any]:
    """Build a public-safe preview model from the demo summary only."""
    assert_public_projection_safe(summary)
    fixture = _mapping(summary.get("daacs_runtime_fixture_materialization"))
    generated_workspace = _mapping(
        summary.get("daacs_runtime_restricted_workspace_generation")
    )
    generated_artifact_verification = _mapping(
        summary.get("daacs_runtime_generated_artifact_verification")
    )
    generated_workspace_static_validation = _mapping(
        summary.get("daacs_runtime_generated_workspace_static_validation")
    )
    buildable_manifest = _mapping(
        summary.get("daacs_runtime_buildable_fixture_manifest")
    )
    local_build_preflight = _mapping(
        summary.get("daacs_runtime_local_build_preflight")
    )
    local_build_attempt = _mapping(
        summary.get("daacs_runtime_local_build_attempt")
    )
    local_preview_attempt = _mapping(
        summary.get("daacs_runtime_local_preview_attempt")
    )
    browser_setup_attempt = _mapping(
        summary.get("daacs_runtime_browser_setup_attempt")
    )
    comparison = _mapping(summary.get("daacs_runtime_comparison"))
    verification = _mapping(summary.get("verification_read_model"))
    stage_coverage = _mapping(summary.get("workflow_stage_coverage"))
    mvp_metrics = _mapping(summary.get("mvp_metrics"))
    fixture_counts = _mapping(fixture.get("counts"))
    fixture_execution = _mapping(fixture.get("execution_boundary"))
    repository = _mapping(fixture.get("repository_boundary"))
    claim_boundary = _mapping(fixture.get("claim_boundary"))
    records = _list_of_dicts(fixture.get("artifact_records"))
    generated_counts = _mapping(generated_workspace.get("counts"))
    generated_execution = _mapping(generated_workspace.get("execution_boundary"))
    generated_repository = _mapping(generated_workspace.get("repository_boundary"))
    generated_claim = _mapping(generated_workspace.get("claim_boundary"))
    generated_records = _list_of_dicts(generated_workspace.get("file_records"))
    generated_artifact_verification_counts = _mapping(
        generated_artifact_verification.get("counts")
    )
    generated_artifact_verification_execution = _mapping(
        generated_artifact_verification.get("execution_boundary")
    )
    generated_artifact_verification_repository = _mapping(
        generated_artifact_verification.get("repository_boundary")
    )
    generated_workspace_static_validation_counts = _mapping(
        generated_workspace_static_validation.get("counts")
    )
    generated_workspace_static_validation_execution = _mapping(
        generated_workspace_static_validation.get("execution_boundary")
    )
    generated_workspace_static_validation_repository = _mapping(
        generated_workspace_static_validation.get("repository_boundary")
    )
    buildable_manifest_counts = _mapping(buildable_manifest.get("counts"))
    buildable_manifest_execution = _mapping(
        buildable_manifest.get("execution_boundary")
    )
    buildable_manifest_repository = _mapping(
        buildable_manifest.get("repository_boundary")
    )
    buildable_package_manifest = _mapping(buildable_manifest.get("package_manifest"))
    local_build_preflight_counts = _mapping(local_build_preflight.get("counts"))
    local_build_preflight_execution = _mapping(
        local_build_preflight.get("execution_boundary")
    )
    local_build_preflight_repository = _mapping(
        local_build_preflight.get("repository_boundary")
    )
    local_build_command_plan = _list_of_dicts(
        local_build_preflight.get("command_plan")
    )
    local_build_attempt_counts = _mapping(local_build_attempt.get("counts"))
    local_build_attempt_execution = _mapping(
        local_build_attempt.get("execution_boundary")
    )
    local_build_attempt_repository = _mapping(
        local_build_attempt.get("repository_boundary")
    )
    local_build_command_results = _list_of_dicts(
        local_build_attempt.get("command_results")
    )
    local_preview_attempt_counts = _mapping(local_preview_attempt.get("counts"))
    local_preview_attempt_execution = _mapping(
        local_preview_attempt.get("execution_boundary")
    )
    local_preview_attempt_repository = _mapping(
        local_preview_attempt.get("repository_boundary")
    )
    local_preview_record = _mapping(local_preview_attempt.get("preview_record"))
    browser_preflight = _mapping(
        local_preview_attempt.get("browser_runtime_preflight")
    )
    browser_setup_counts = _mapping(browser_setup_attempt.get("counts"))
    browser_setup_execution = _mapping(browser_setup_attempt.get("execution_boundary"))
    browser_setup_repository = _mapping(browser_setup_attempt.get("repository_boundary"))
    post_setup_preflight = _mapping(
        browser_setup_attempt.get("post_setup_browser_runtime_preflight")
    )
    artifact_kinds = list(summary.get("artifact_kinds", []))
    stage_order = list(stage_coverage.get("stage_order", []))

    model = {
        "surface": "AW-APP-01",
        "title": ARTIFACT_PREVIEW_TITLE,
        "source_demo": summary.get("demo_id", "unknown"),
        "status": summary.get("status", "unknown"),
        "run_id": summary.get("run_id", "unknown"),
        "projection_version": summary.get("projection_version", "unknown"),
        "artifact_count": _count(summary.get("artifact_count")),
        "stage_coverage": {
            "covered": _count(stage_coverage.get("covered_stage_count")),
            "required": _count(stage_coverage.get("required_stage_count")),
            "percent": stage_coverage.get("coverage_percent", 0),
            "stage_order": stage_order,
        },
        "document_artifacts": [
            {
                "kind": kind,
                "present": kind in artifact_kinds
                or (kind == "runner_plan" and _count(summary.get("counts", {}).get("runner_plan_count")) > 0),
            }
            for kind in DOCUMENT_ARTIFACTS
        ],
        "fixture_materialization": {
            "status": fixture.get("status", "not_requested"),
            "reason": fixture.get("reason", "not_requested"),
            "materialization_hash": fixture.get("materialization_hash", ""),
            "artifact_record_count": _count(
                fixture_counts.get("fixture_artifact_record_count")
            ),
            "content_hash_count": _count(
                fixture_counts.get("fixture_artifact_content_hash_count")
            ),
            "workspace_write_count": _count(
                fixture_execution.get("fixture_workspace_file_write_count")
            ),
            "outside_workspace_write_count": _count(
                fixture_execution.get("filesystem_writes_outside_workspace")
            ),
            "artifact_content_returned": bool(
                repository.get("artifact_content_returned")
            ),
            "root_path_returned": bool(repository.get("root_path_returned")),
        },
        "artifact_cards": [
            {
                "label": record.get("label", "unknown"),
                "artifact_kind": record.get("artifact_kind", "unknown"),
                "workspace_relative_path": record.get(
                    "workspace_relative_path", "unknown"
                ),
                "content_hash": record.get("content_hash", ""),
                "byte_count": _count(record.get("byte_count")),
                "body_included": bool(record.get("body_included")),
                "root_path_returned": bool(record.get("root_path_returned")),
            }
            for record in records
            if record.get("label") in REQUIRED_ARTIFACT_LABELS
        ],
        "generated_workspace": {
            "status": generated_workspace.get("status", "not_requested"),
            "reason": generated_workspace.get("reason", "not_requested"),
            "generated_workspace_hash": generated_workspace.get(
                "generated_workspace_hash", ""
            ),
            "file_record_count": _count(
                generated_counts.get("generated_workspace_file_record_count")
            ),
            "file_hash_count": _count(
                generated_counts.get("generated_workspace_file_hash_count")
            ),
            "file_byte_count": _count(
                generated_counts.get("generated_workspace_file_byte_count")
            ),
            "workspace_write_count": _count(
                generated_execution.get("restricted_workspace_file_write_count")
            ),
            "outside_workspace_write_count": _count(
                generated_execution.get("filesystem_writes_outside_workspace")
            ),
            "file_content_returned": bool(
                generated_repository.get("file_content_returned")
            ),
            "root_path_returned": bool(generated_repository.get("root_path_returned")),
            "build_executed": bool(generated_claim.get("build_executed")),
            "server_started": bool(generated_claim.get("server_started")),
        },
        "generated_file_cards": [
            {
                "label": record.get("label", "unknown"),
                "artifact_kind": record.get("artifact_kind", "unknown"),
                "workspace_relative_path": record.get(
                    "workspace_relative_path", "unknown"
                ),
                "content_hash": record.get("content_hash", ""),
                "byte_count": _count(record.get("byte_count")),
                "content_included": bool(record.get("content_included")),
                "root_path_returned": bool(record.get("root_path_returned")),
            }
            for record in generated_records
            if record.get("label") in REQUIRED_GENERATED_FILE_LABELS
        ],
        "generated_artifact_verification": {
            "status": generated_artifact_verification.get(
                "status", "not_requested"
            ),
            "reason": generated_artifact_verification.get(
                "reason", "not_requested"
            ),
            "generated_artifact_verification_hash": (
                generated_artifact_verification.get(
                    "generated_artifact_verification_hash", ""
                )
            ),
            "expected_file_count": _count(
                generated_artifact_verification_counts.get("expected_file_count")
            ),
            "file_check_record_count": _count(
                generated_artifact_verification_counts.get("file_check_record_count")
            ),
            "content_hash_match_count": _count(
                generated_artifact_verification_counts.get("content_hash_match_count")
            ),
            "byte_count_match_count": _count(
                generated_artifact_verification_counts.get("byte_count_match_count")
            ),
            "missing_local_file_count": _count(
                generated_artifact_verification_counts.get("missing_local_file_count")
            ),
            "file_content_returned": bool(
                generated_artifact_verification_repository.get(
                    "file_content_returned"
                )
            ),
            "root_path_returned": bool(
                generated_artifact_verification_repository.get("root_path_returned")
            ),
        },
        "generated_workspace_static_validation": {
            "status": generated_workspace_static_validation.get(
                "status", "not_requested"
            ),
            "passed_validation_label": (
                "passed"
                if generated_workspace_static_validation.get("status") == "passed"
                else _text(generated_workspace_static_validation.get("status"))
            ),
            "reason": generated_workspace_static_validation.get(
                "reason", "not_requested"
            ),
            "generated_workspace_static_validation_hash": (
                generated_workspace_static_validation.get(
                    "generated_workspace_static_validation_hash", ""
                )
            ),
            "static_file_checked_count": _count(
                generated_workspace_static_validation_counts.get(
                    "static_file_checked_count"
                )
            ),
            "file_read_count": _count(
                generated_workspace_static_validation_counts.get("file_read_count")
            ),
            "package_json_parse_pass_count": _count(
                generated_workspace_static_validation_counts.get(
                    "package_json_parse_pass_count"
                )
            ),
            "required_script_present_count": _count(
                generated_workspace_static_validation_counts.get(
                    "required_script_present_count"
                )
            ),
            "app_component_marker_present_count": _count(
                generated_workspace_static_validation_counts.get(
                    "app_component_marker_present_count"
                )
            ),
            "api_marker_present_count": _count(
                generated_workspace_static_validation_counts.get(
                    "api_marker_present_count"
                )
            ),
            "verification_boundary_marker_present_count": _count(
                generated_workspace_static_validation_counts.get(
                    "verification_boundary_marker_present_count"
                )
            ),
            "zero_call_marker_present_count": _count(
                generated_workspace_static_validation_counts.get(
                    "zero_call_marker_present_count"
                )
            ),
            "file_content_returned": bool(
                generated_workspace_static_validation_repository.get(
                    "file_content_returned"
                )
            ),
            "root_path_returned": bool(
                generated_workspace_static_validation_repository.get(
                    "root_path_returned"
                )
            ),
        },
        "buildable_fixture_manifest": {
            "status": buildable_manifest.get("status", "not_requested"),
            "reason": buildable_manifest.get("reason", "not_requested"),
            "build_ready_candidate": bool(
                buildable_manifest.get("build_ready_candidate")
            ),
            "candidate_label": (
                "ready"
                if buildable_manifest.get("build_ready_candidate") is True
                else "not ready"
            ),
            "buildable_fixture_manifest_hash": buildable_manifest.get(
                "buildable_fixture_manifest_hash", ""
            ),
            "required_file_read_count": _count(
                buildable_manifest_counts.get("required_file_read_count")
            ),
            "required_script_present_count": _count(
                buildable_manifest_counts.get("required_script_present_count")
            ),
            "total_dependency_label_count": _count(
                buildable_manifest_counts.get("total_dependency_label_count")
            ),
            "placeholder_dependency_value_count": _count(
                buildable_manifest_counts.get("placeholder_dependency_value_count")
            ),
            "index_html_marker_present_count": _count(
                buildable_manifest_counts.get("index_html_marker_present_count")
            ),
            "main_entrypoint_marker_present_count": _count(
                buildable_manifest_counts.get("main_entrypoint_marker_present_count")
            ),
            "vite_config_marker_present_count": _count(
                buildable_manifest_counts.get("vite_config_marker_present_count")
            ),
            "tsconfig_marker_present_count": _count(
                buildable_manifest_counts.get("tsconfig_marker_present_count")
            ),
            "dependency_value_returned": bool(
                buildable_package_manifest.get("dependency_value_returned")
            ),
            "package_manifest_value_returns": _count(
                buildable_manifest_execution.get("package_manifest_values_returned")
            ),
            "file_content_returned": bool(
                buildable_manifest_repository.get("file_content_returned")
            ),
            "root_path_returned": bool(
                buildable_manifest_repository.get("root_path_returned")
            ),
        },
        "local_build_preflight": {
            "status": local_build_preflight.get("status", "not_requested"),
            "reason": local_build_preflight.get("reason", "not_requested"),
            "eligible": bool(local_build_preflight.get("local_build_eligible")),
            "eligible_label": (
                "eligible"
                if local_build_preflight.get("local_build_eligible") is True
                else "not eligible"
            ),
            "opt_in_required": bool(
                local_build_preflight.get("local_build_opt_in_required")
            ),
            "operator_opt_in_present": bool(
                local_build_preflight.get("operator_opt_in_present")
            ),
            "local_build_preflight_hash": local_build_preflight.get(
                "local_build_preflight_hash", ""
            ),
            "command_label_count": _count(
                local_build_preflight_counts.get("command_plan_label_count")
            ),
            "command_hash_count": _count(
                local_build_preflight_counts.get("command_plan_hash_count")
            ),
            "default_execution_permission_count": _count(
                local_build_preflight_counts.get(
                    "default_execution_permission_count"
                )
            ),
            "dependency_value_return_count": _count(
                local_build_preflight_counts.get("dependency_value_return_count")
            ),
            "file_content_returned": bool(
                local_build_preflight_repository.get("file_content_returned")
            ),
            "root_path_returned": bool(
                local_build_preflight_repository.get("root_path_returned")
            ),
            "dependency_value_returned": bool(
                local_build_preflight_repository.get("dependency_value_returned")
            ),
            "command_labels": [
                _text(record.get("label")) for record in local_build_command_plan
            ],
        },
        "local_build_attempt": {
            "status": local_build_attempt.get("status", "not_requested"),
            "reason": local_build_attempt.get("reason", "not_requested"),
            "attempted": bool(local_build_attempt.get("local_build_attempted")),
            "attempted_label": (
                "attempted"
                if local_build_attempt.get("local_build_attempted") is True
                else "not attempted"
            ),
            "opt_in_present": bool(
                local_build_attempt.get("local_build_opt_in_present")
            ),
            "command_execution_allowed": bool(
                local_build_attempt.get("local_command_execution_allowed")
            ),
            "local_build_attempt_hash": local_build_attempt.get(
                "local_build_attempt_hash", ""
            ),
            "command_result_count": _count(
                local_build_attempt_counts.get("command_result_count")
            ),
            "command_output_hash_count": _count(
                local_build_attempt_counts.get("command_output_hash_count")
            ),
            "package_install_attempt_count": _count(
                local_build_attempt_counts.get("package_install_attempt_count")
            ),
            "build_attempt_count": _count(
                local_build_attempt_counts.get("build_attempt_count")
            ),
            "server_start_attempt_count": _count(
                local_build_attempt_counts.get("server_start_attempt_count")
            ),
            "raw_output_public_return_count": _count(
                local_build_attempt_counts.get("raw_output_public_return_count")
            ),
            "file_content_returned": bool(
                local_build_attempt_repository.get("file_content_returned")
            ),
            "root_path_returned": bool(
                local_build_attempt_repository.get("root_path_returned")
            ),
            "command_output_returned": bool(
                local_build_attempt_repository.get("command_output_returned")
            ),
            "command_results": [
                {
                    "label": record.get("label", "unknown"),
                    "attempted": bool(record.get("attempted")),
                    "exit_code": record.get("exit_code"),
                    "timed_out": bool(record.get("timed_out")),
                    "output_hash": record.get("output_hash", ""),
                    "output_byte_count": _count(record.get("output_byte_count")),
                    "duration_ms": _count(record.get("duration_ms")),
                    "reason": record.get("reason", "unknown"),
                    "raw_output_returned": bool(record.get("raw_output_returned")),
                    "root_path_returned": bool(record.get("root_path_returned")),
                }
                for record in local_build_command_results
            ],
        },
        "local_preview_attempt": {
            "status": local_preview_attempt.get("status", "not_requested"),
            "reason": local_preview_attempt.get("reason", "not_requested"),
            "attempted": bool(
                local_preview_attempt.get("local_preview_attempted")
            ),
            "opt_in_present": bool(
                local_preview_attempt.get("local_preview_opt_in_present")
            ),
            "server_allowed": bool(
                local_preview_attempt.get("local_preview_server_allowed")
            ),
            "browser_verification_allowed": bool(
                local_preview_attempt.get("browser_verification_allowed")
            ),
            "browser_runtime_available": bool(browser_preflight.get("available")),
            "browser_runtime_reason": browser_preflight.get("reason", "not_checked"),
            "preflight_count": _count(
                local_preview_attempt_counts.get("browser_runtime_preflight_count")
            ),
            "browser_available_count": _count(
                local_preview_attempt_counts.get("browser_runtime_available_count")
            ),
            "server_start_count": _count(
                local_preview_attempt_counts.get("server_start_count")
            ),
            "server_start_attempt_count": _count(
                local_preview_attempt_counts.get("preview_server_start_attempt_count")
            ),
            "server_stop_count": _count(
                local_preview_attempt_counts.get("preview_server_stop_count")
            ),
            "server_cleanup_percent": (
                100.0
                if (
                    _count(local_preview_attempt_counts.get("server_start_count"))
                    and _count(
                        local_preview_attempt_counts.get(
                            "preview_server_stop_count"
                        )
                    )
                    >= _count(local_preview_attempt_counts.get("server_start_count"))
                )
                else 0.0
            ),
            "screenshot_evidence_count": _count(
                local_preview_attempt_counts.get("screenshot_evidence_count")
            ),
            "screenshot_hash_count": _count(
                local_preview_attempt_counts.get("screenshot_hash_count")
            ),
            "screenshot_byte_count": _count(
                local_preview_attempt_counts.get("screenshot_byte_count")
            ),
            "screenshot_capture_status": (
                "verified"
                if (
                    _count(
                        local_preview_attempt_counts.get(
                            "screenshot_evidence_count"
                        )
                    )
                    and _count(
                        local_preview_attempt_counts.get("screenshot_hash_count")
                    )
                )
                else local_preview_attempt.get("status", "not_requested")
            ),
            "screenshot_capture_reason": (
                "screenshot_hash_recorded"
                if (
                    _count(
                        local_preview_attempt_counts.get(
                            "screenshot_evidence_count"
                        )
                    )
                    and _count(
                        local_preview_attempt_counts.get("screenshot_hash_count")
                    )
                )
                else local_preview_attempt.get("reason", "not_requested")
            ),
            "owner_filter_click_status": local_preview_record.get(
                "owner_filter_click_status", "not_requested"
            ),
            "owner_filter_click_attempt_count": _count(
                local_preview_attempt_counts.get("owner_filter_click_attempt_count")
            ),
            "owner_filter_click_pass_count": _count(
                local_preview_attempt_counts.get("owner_filter_click_pass_count")
            ),
            "owner_filter_click_target_label_hash_count": _count(
                local_preview_attempt_counts.get(
                    "owner_filter_click_target_label_hash_count"
                )
            ),
            "owner_filter_before_task_count": _count(
                local_preview_attempt_counts.get("owner_filter_before_task_count")
            ),
            "owner_filter_after_task_count": _count(
                local_preview_attempt_counts.get("owner_filter_after_task_count")
            ),
            "owner_filter_changed_count": _count(
                local_preview_attempt_counts.get("owner_filter_changed_count")
            ),
            "reviewer_decision_click_status": local_preview_record.get(
                "reviewer_decision_click_status", "not_requested"
            ),
            "reviewer_decision_click_attempt_count": _count(
                local_preview_attempt_counts.get(
                    "reviewer_decision_click_attempt_count"
                )
            ),
            "reviewer_decision_click_pass_count": _count(
                local_preview_attempt_counts.get(
                    "reviewer_decision_click_pass_count"
                )
            ),
            "reviewer_decision_click_target_label_hash_count": _count(
                local_preview_attempt_counts.get(
                    "reviewer_decision_click_target_label_hash_count"
                )
            ),
            "reviewer_decision_state_hash_count": _count(
                local_preview_attempt_counts.get(
                    "reviewer_decision_state_hash_count"
                )
            ),
            "reviewer_decision_state_changed_count": _count(
                local_preview_attempt_counts.get(
                    "reviewer_decision_state_changed_count"
                )
            ),
            "raw_output_returned": _count(
                local_preview_attempt_counts.get("raw_output_public_return_count")
            ),
            "screenshot_path_returned": bool(
                local_preview_attempt_repository.get("screenshot_path_returned")
            )
            or bool(local_preview_record.get("screenshot_path_returned")),
            "page_text_returned": bool(
                local_preview_attempt_repository.get("page_text_returned")
            )
            or bool(local_preview_record.get("page_text_returned")),
        },
        "browser_setup_attempt": {
            "status": browser_setup_attempt.get("status", "not_requested"),
            "reason": browser_setup_attempt.get("reason", "not_requested"),
            "attempted": bool(browser_setup_attempt.get("setup_attempted")),
            "operator_opt_in_present": bool(
                browser_setup_attempt.get("operator_opt_in_present")
            ),
            "setup_allowed": bool(
                browser_setup_attempt.get("browser_runtime_setup_allowed")
            ),
            "setup_attempt_hash": browser_setup_attempt.get(
                "browser_runtime_setup_attempt_hash", ""
            ),
            "setup_command_attempt_count": _count(
                browser_setup_counts.get("setup_command_attempt_count")
            ),
            "browser_preflight_count": _count(
                browser_setup_counts.get("browser_runtime_preflight_count")
            ),
            "browser_available_before_setup_count": _count(
                browser_setup_counts.get(
                    "browser_runtime_available_before_setup_count"
                )
            ),
            "default_setup_command_execution_count": _count(
                browser_setup_counts.get("default_setup_command_execution_count")
            ),
            "explicit_setup_opt_in_count": _count(
                browser_setup_counts.get("explicit_setup_opt_in_count")
            ),
            "browser_available_after_setup_count": _count(
                browser_setup_counts.get(
                    "browser_runtime_available_after_setup_count"
                )
            ),
            "post_setup_available": bool(post_setup_preflight.get("available")),
            "raw_output_returned": _count(
                browser_setup_counts.get("raw_output_public_return_count")
            ),
            "argv_returned": _count(browser_setup_counts.get("argv_public_return_count")),
            "browser_error_returned": _count(
                browser_setup_counts.get("browser_error_public_return_count")
            ),
            "root_path_returned": bool(
                browser_setup_repository.get("local_root_path_returned")
            ),
        },
        "verification": {
            "status": verification.get("status", "unknown"),
            "report_count": _count(
                _mapping(verification.get("counts")).get("verification_report_count")
            ),
            "check_count": _count(_mapping(verification.get("counts")).get("check_count")),
            "failed_check_count": _count(
                _mapping(verification.get("counts")).get("failed_check_count")
            ),
        },
        "execution_boundary": {
            "target_runtime_calls": _count(
                fixture_execution.get("target_runtime_calls")
            ),
            "provider_calls": _count(fixture_execution.get("provider_calls")),
            "subprocess_calls": _count(fixture_execution.get("subprocess_calls")),
            "network_calls": _count(fixture_execution.get("network_calls")),
            "live_provider_calls": _count(mvp_metrics.get("live_provider_calls")),
            "generated_workspace_target_runtime_calls": _count(
                generated_execution.get("target_runtime_calls")
            ),
            "generated_workspace_provider_calls": _count(
                generated_execution.get("provider_calls")
            ),
            "generated_workspace_subprocess_calls": _count(
                generated_execution.get("subprocess_calls")
            ),
            "generated_workspace_network_calls": _count(
                generated_execution.get("network_calls")
            ),
            "generated_workspace_package_install_calls": _count(
                generated_execution.get("package_install_calls")
            ),
            "generated_workspace_build_calls": _count(
                generated_execution.get("build_calls")
            ),
            "generated_workspace_server_start_calls": _count(
                generated_execution.get("server_start_calls")
            ),
            "generated_artifact_verification_file_reads": _count(
                generated_artifact_verification_execution.get(
                    "generated_workspace_file_read_count"
                )
            ),
            "generated_artifact_verification_target_runtime_calls": _count(
                generated_artifact_verification_execution.get("target_runtime_calls")
            ),
            "generated_artifact_verification_provider_calls": _count(
                generated_artifact_verification_execution.get("provider_calls")
            ),
            "generated_artifact_verification_subprocess_calls": _count(
                generated_artifact_verification_execution.get("subprocess_calls")
            ),
            "generated_artifact_verification_network_calls": _count(
                generated_artifact_verification_execution.get("network_calls")
            ),
            "generated_workspace_static_validation_file_reads": _count(
                generated_workspace_static_validation_execution.get(
                    "static_validation_file_read_count"
                )
            ),
            "generated_workspace_static_validation_target_runtime_calls": _count(
                generated_workspace_static_validation_execution.get(
                    "target_runtime_calls"
                )
            ),
            "generated_workspace_static_validation_provider_calls": _count(
                generated_workspace_static_validation_execution.get("provider_calls")
            ),
            "generated_workspace_static_validation_subprocess_calls": _count(
                generated_workspace_static_validation_execution.get(
                    "subprocess_calls"
                )
            ),
            "generated_workspace_static_validation_network_calls": _count(
                generated_workspace_static_validation_execution.get("network_calls")
            ),
            "generated_workspace_static_validation_package_install_calls": _count(
                generated_workspace_static_validation_execution.get(
                    "package_install_calls"
                )
            ),
            "generated_workspace_static_validation_build_calls": _count(
                generated_workspace_static_validation_execution.get("build_calls")
            ),
            "generated_workspace_static_validation_server_start_calls": _count(
                generated_workspace_static_validation_execution.get(
                    "server_start_calls"
                )
            ),
            "buildable_manifest_file_reads": _count(
                buildable_manifest_execution.get("buildable_manifest_file_read_count")
            ),
            "buildable_manifest_target_runtime_calls": _count(
                buildable_manifest_execution.get("target_runtime_calls")
            ),
            "buildable_manifest_provider_calls": _count(
                buildable_manifest_execution.get("provider_calls")
            ),
            "buildable_manifest_subprocess_calls": _count(
                buildable_manifest_execution.get("subprocess_calls")
            ),
            "buildable_manifest_network_calls": _count(
                buildable_manifest_execution.get("network_calls")
            ),
            "buildable_manifest_package_install_calls": _count(
                buildable_manifest_execution.get("package_install_calls")
            ),
            "buildable_manifest_build_calls": _count(
                buildable_manifest_execution.get("build_calls")
            ),
            "buildable_manifest_server_start_calls": _count(
                buildable_manifest_execution.get("server_start_calls")
            ),
            "local_build_preflight_target_runtime_calls": _count(
                local_build_preflight_execution.get("target_runtime_calls")
            ),
            "local_build_preflight_provider_calls": _count(
                local_build_preflight_execution.get("provider_calls")
            ),
            "local_build_preflight_subprocess_calls": _count(
                local_build_preflight_execution.get("subprocess_calls")
            ),
            "local_build_preflight_network_calls": _count(
                local_build_preflight_execution.get("network_calls")
            ),
            "local_build_preflight_package_install_calls": _count(
                local_build_preflight_execution.get("package_install_calls")
            ),
            "local_build_preflight_build_calls": _count(
                local_build_preflight_execution.get("build_calls")
            ),
            "local_build_preflight_server_start_calls": _count(
                local_build_preflight_execution.get("server_start_calls")
            ),
            "local_build_preflight_execution_permission_count": _count(
                local_build_preflight_execution.get("execution_permission_count")
            ),
            "local_build_attempt_target_runtime_calls": _count(
                local_build_attempt_execution.get("target_runtime_calls")
            ),
            "local_build_attempt_provider_calls": _count(
                local_build_attempt_execution.get("provider_calls")
            ),
            "local_build_attempt_subprocess_calls": _count(
                local_build_attempt_execution.get("subprocess_calls")
            ),
            "local_build_attempt_network_calls": _count(
                local_build_attempt_execution.get("network_calls")
            ),
            "local_build_attempt_package_install_calls": _count(
                local_build_attempt_execution.get("package_install_calls")
            ),
            "local_build_attempt_build_calls": _count(
                local_build_attempt_execution.get("build_calls")
            ),
            "local_build_attempt_server_start_calls": _count(
                local_build_attempt_execution.get("server_start_calls")
            ),
            "local_build_attempt_execution_permission_count": _count(
                local_build_attempt_execution.get("execution_permission_count")
            ),
            "local_preview_attempt_server_start_calls": _count(
                local_preview_attempt_execution.get("server_start_calls")
            ),
            "local_preview_attempt_server_stop_calls": _count(
                local_preview_attempt_execution.get("server_stop_calls")
            ),
            "local_preview_attempt_provider_calls": _count(
                local_preview_attempt_execution.get("provider_calls")
            ),
            "local_preview_attempt_target_runtime_calls": _count(
                local_preview_attempt_execution.get("target_runtime_calls")
            ),
            "browser_setup_local_process_calls": _count(
                browser_setup_execution.get("local_process_calls")
            ),
            "browser_setup_package_install_calls": _count(
                browser_setup_execution.get("package_install_calls")
            ),
            "browser_setup_binary_install_calls": _count(
                browser_setup_execution.get("browser_binary_install_calls")
            ),
            "browser_setup_provider_calls": _count(
                browser_setup_execution.get("provider_calls")
            ),
            "browser_setup_target_runtime_calls": _count(
                browser_setup_execution.get("daacs_target_runtime_calls")
            ),
        },
        "claim_boundary": {
            "scope": claim_boundary.get(
                "scope", "fixture-backed local artifact materialization only"
            ),
            "target_runtime_outcome": bool(claim_boundary.get("target_runtime_outcome")),
            "external_provider_outcome": bool(
                claim_boundary.get("external_provider_outcome")
            ),
            "hosted_behavior": bool(claim_boundary.get("hosted_behavior")),
            "production_trust_claim": bool(
                claim_boundary.get("production_trust_claim")
            ),
        },
        "comparison": {
            "variant_count": _count(comparison.get("comparison_variant_count")),
            "raw_exposure_findings": _count(comparison.get("raw_exposure_findings")),
            "public_claim_drift_findings": _count(
                comparison.get("public_claim_drift_findings")
            ),
        },
    }
    assert_public_projection_safe(model)
    return model


def _metric(label: str, value: object) -> str:
    return (
        '<div class="metric">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(_text(value, '0'))}</strong>"
        "</div>"
    )


def _stage_pills(stage_order: list[str]) -> str:
    if not stage_order:
        return '<span class="pill muted">unknown</span>'
    return "\n".join(
        f'<span class="pill done">{escape(stage)}</span>' for stage in stage_order
    )


def _document_rows(documents: list[dict[str, Any]]) -> str:
    rows = []
    for item in documents:
        present = bool(item.get("present"))
        state = "ready" if present else "missing"
        label = "ready" if present else "missing"
        rows.append(
            '<li class="doc-row">'
            f"<span>{escape(_text(item.get('kind')).replace('_', ' '))}</span>"
            f'<strong class="{state}">{escape(label)}</strong>'
            "</li>"
        )
    return "\n".join(rows)


def _artifact_cards(records: list[dict[str, Any]]) -> str:
    if not records:
        return '<article class="artifact-card"><h3>none</h3><p>No fixture artifacts requested.</p></article>'
    cards = []
    for record in records:
        cards.append(
            '<article class="artifact-card">'
            f"<h3>{escape(_text(record.get('label')).replace('_', ' '))}</h3>"
            f"<p>{escape(_text(record.get('artifact_kind')).replace('_', ' '))}</p>"
            '<dl>'
            f"<dt>Relative path</dt><dd>{escape(_text(record.get('workspace_relative_path')))}</dd>"
            f"<dt>Content hash</dt><dd>{escape(_short_hash(record.get('content_hash')))}</dd>"
            f"<dt>Bytes</dt><dd>{_count(record.get('byte_count'))}</dd>"
            f"<dt>Content returned</dt><dd>{escape(_text(record.get('body_included')))}</dd>"
            f"<dt>Root returned</dt><dd>{escape(_text(record.get('root_path_returned')))}</dd>"
            "</dl>"
            "</article>"
        )
    return "\n".join(cards)


def _generated_file_cards(records: list[dict[str, Any]]) -> str:
    if not records:
        return '<p class="note">No generated workspace files requested.</p>'
    cards = []
    for record in records:
        cards.append(
            '<article class="artifact-card">'
            f"<h3>{escape(_text(record.get('label')).replace('_', ' '))}</h3>"
            f"<p>{escape(_text(record.get('artifact_kind')).replace('_', ' '))}</p>"
            '<dl>'
            f"<dt>Relative path</dt><dd>{escape(_text(record.get('workspace_relative_path')))}</dd>"
            f"<dt>Content hash</dt><dd>{escape(_short_hash(record.get('content_hash')))}</dd>"
            f"<dt>Bytes</dt><dd>{_count(record.get('byte_count'))}</dd>"
            f"<dt>Content returned</dt><dd>{escape(_text(record.get('content_included')))}</dd>"
            f"<dt>Root returned</dt><dd>{escape(_text(record.get('root_path_returned')))}</dd>"
            "</dl>"
            "</article>"
        )
    return "\n".join(cards)


def _command_result_cards(records: list[dict[str, Any]]) -> str:
    if not records:
        return '<p class="note">No local build commands were attempted.</p>'
    cards = []
    for record in records:
        cards.append(
            '<article class="artifact-card">'
            f"<h3>{escape(_text(record.get('label')))}</h3>"
            f"<p>{escape(_text(record.get('reason')))}</p>"
            '<dl>'
            f"<dt>Attempted</dt><dd>{escape(_text(record.get('attempted')))}</dd>"
            f"<dt>Exit code</dt><dd>{escape(_text(record.get('exit_code')))}</dd>"
            f"<dt>Timed out</dt><dd>{escape(_text(record.get('timed_out')))}</dd>"
            f"<dt>Output hash</dt><dd>{escape(_short_hash(record.get('output_hash')))}</dd>"
            f"<dt>Output bytes</dt><dd>{_count(record.get('output_byte_count'))}</dd>"
            f"<dt>Duration ms</dt><dd>{_count(record.get('duration_ms'))}</dd>"
            f"<dt>Output returned</dt><dd>{escape(_text(record.get('raw_output_returned')))}</dd>"
            "</dl>"
            "</article>"
        )
    return "\n".join(cards)


def render_artifact_preview(summary: dict[str, Any]) -> str:
    """Return a complete static HTML artifact preview."""
    model = build_artifact_preview_model(summary)
    fixture = model["fixture_materialization"]
    generated_workspace = model["generated_workspace"]
    generated_artifact_verification = model["generated_artifact_verification"]
    generated_workspace_static_validation = model[
        "generated_workspace_static_validation"
    ]
    buildable_manifest = model["buildable_fixture_manifest"]
    local_build_preflight = model["local_build_preflight"]
    local_build_attempt = model["local_build_attempt"]
    local_preview_attempt = model["local_preview_attempt"]
    browser_setup_attempt = model["browser_setup_attempt"]
    verification = model["verification"]
    execution = model["execution_boundary"]
    comparison = model["comparison"]
    claim = model["claim_boundary"]
    stage = model["stage_coverage"]

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(ARTIFACT_PREVIEW_TITLE)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #172033;
      --muted: #637082;
      --line: #d9e0e8;
      --bg: #f7f8fb;
      --panel: #ffffff;
      --green: #0f766e;
      --blue: #285c91;
      --amber: #9a650f;
      --red: #a13d4a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--bg);
      letter-spacing: 0;
    }}
    header {{
      min-height: 82px;
      padding: 18px clamp(18px, 4vw, 46px);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }}
    h1 {{ margin: 0; font-size: 22px; line-height: 1.15; }}
    header p {{ margin: 5px 0 0; color: var(--muted); font-size: 13px; }}
    .badges {{ display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
      color: var(--ink);
      font-size: 13px;
      white-space: nowrap;
    }}
    .badge.ready {{ color: var(--green); border-color: #9accc5; }}
    .badge.closed {{ color: var(--amber); border-color: #e4c384; }}
    main {{
      width: min(1180px, 100%);
      margin: 0 auto;
      padding: 26px clamp(18px, 4vw, 46px) 42px;
    }}
    .overview {{
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .metric {{
      min-height: 86px;
      padding: 14px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .metric strong {{ display: block; margin-top: 10px; font-size: 21px; line-height: 1.1; overflow-wrap: anywhere; }}
    section {{
      margin-top: 16px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }}
    h2 {{ margin: 0 0 14px; font-size: 17px; }}
    .stage-strip {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .pill {{
      min-height: 32px;
      display: inline-flex;
      align-items: center;
      padding: 0 10px;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: #f7fafc;
      font-size: 13px;
      font-weight: 650;
    }}
    .pill.done {{ border-color: #9accc5; color: var(--green); }}
    .pill.muted {{ color: var(--muted); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}
    .artifact-card {{
      min-height: 216px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
    }}
    .artifact-card h3 {{ margin: 0; font-size: 18px; }}
    .artifact-card p {{ margin: 5px 0 12px; color: var(--muted); }}
    dl {{ margin: 0; display: grid; gap: 8px; }}
    dt {{ color: var(--muted); font-size: 12px; }}
    dd {{ margin: -5px 0 0; font-weight: 650; font-size: 13px; overflow-wrap: anywhere; }}
    .split {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 16px;
    }}
    .doc-list {{
      margin: 0;
      padding: 0;
      list-style: none;
    }}
    .doc-row {{
      min-height: 36px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      border-bottom: 1px solid #eef2f6;
    }}
    .doc-row:last-child {{ border-bottom: 0; }}
    .doc-row strong {{ font-size: 12px; text-transform: uppercase; }}
    .doc-row strong.ready {{ color: var(--green); }}
    .doc-row strong.missing {{ color: var(--red); }}
    .boundary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .boundary div {{
      min-height: 58px;
      padding: 12px;
      background: #fafbfc;
      border: 1px solid #edf1f5;
      border-radius: 6px;
    }}
    .boundary span {{ display: block; color: var(--muted); font-size: 12px; }}
    .boundary strong {{ display: block; margin-top: 6px; font-size: 15px; overflow-wrap: anywhere; }}
    .note {{ color: var(--muted); font-size: 12px; margin-top: 16px; }}
    @media (max-width: 900px) {{
      header {{ align-items: flex-start; flex-direction: column; }}
      .badges {{ justify-content: flex-start; }}
      .overview, .grid, .split, .boundary {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body data-surface="AW-APP-01" data-projection="public-summary-only">
  <header>
    <div>
      <h1>{escape(ARTIFACT_PREVIEW_TITLE)}</h1>
      <p>Run {escape(_text(model["run_id"]))} over sanitized local demo summary</p>
    </div>
    <div class="badges">
      <span class="badge ready">status: {escape(_text(model["status"]))}</span>
      <span class="badge ready">artifact cards: {len(model["artifact_cards"])}</span>
      <span class="badge ready">generated files: {len(model["generated_file_cards"])}</span>
      <span class="badge ready">verified files: {generated_artifact_verification["file_check_record_count"]}</span>
      <span class="badge ready">static checks: {generated_workspace_static_validation["passed_validation_label"]}</span>
      <span class="badge ready">build-ready candidate: {buildable_manifest["candidate_label"]}</span>
      <span class="badge ready">local build preflight: {local_build_preflight["eligible_label"]}</span>
      <span class="badge ready">local build: {local_build_attempt["attempted_label"]}</span>
      <span class="badge closed">local preview: {escape(_text(local_preview_attempt["status"]))}</span>
      <span class="badge closed">browser setup: {escape(_text(browser_setup_attempt["status"]))}</span>
      <span class="badge closed">runtime: fixture / closed</span>
    </div>
  </header>
  <main>
    <div class="overview">
      {_metric("Stage coverage", f"{stage['covered']}/{stage['required']}")}
      {_metric("Artifact count", model["artifact_count"])}
      {_metric("Preview cards", len(model["artifact_cards"]))}
      {_metric("Generated files", len(model["generated_file_cards"]))}
      {_metric("Fixture status", fixture["status"])}
      {_metric("Runtime calls", execution["target_runtime_calls"])}
      {_metric("Local build opt-in", local_build_preflight["opt_in_required"])}
      {_metric("Screenshot status", local_preview_attempt["screenshot_capture_status"])}
      {_metric("Screenshot evidence", local_preview_attempt["screenshot_evidence_count"])}
      {_metric("Owner filter click", local_preview_attempt["owner_filter_click_status"])}
      {_metric("Owner filter pass", local_preview_attempt["owner_filter_click_pass_count"])}
      {_metric("Reviewer decision", local_preview_attempt["reviewer_decision_click_status"])}
      {_metric("Reviewer decision pass", local_preview_attempt["reviewer_decision_click_pass_count"])}
      {_metric("Setup commands", browser_setup_attempt["setup_command_attempt_count"])}
    </div>

    <section>
      <h2>Workflow Coverage</h2>
      <div class="stage-strip">{_stage_pills(list(stage["stage_order"]))}</div>
    </section>

    <section>
      <h2>Fixture Artifact Files</h2>
      <div class="grid">{_artifact_cards(model["artifact_cards"])}</div>
    </section>

    <section>
      <h2>Generated Workspace Files</h2>
      <div class="grid">{_generated_file_cards(model["generated_file_cards"])}</div>
    </section>

    <section>
      <h2>Generated Artifact Verification</h2>
      <div class="boundary">
        <div><span>Status</span><strong>{escape(_text(generated_artifact_verification["status"]))}</strong></div>
        <div><span>Expected files</span><strong>{generated_artifact_verification["expected_file_count"]}</strong></div>
        <div><span>Checked files</span><strong>{generated_artifact_verification["file_check_record_count"]}</strong></div>
        <div><span>Hash matches</span><strong>{generated_artifact_verification["content_hash_match_count"]}</strong></div>
        <div><span>Byte matches</span><strong>{generated_artifact_verification["byte_count_match_count"]}</strong></div>
        <div><span>Missing files</span><strong>{generated_artifact_verification["missing_local_file_count"]}</strong></div>
        <div><span>Content returned</span><strong>{escape(_text(generated_artifact_verification["file_content_returned"]))}</strong></div>
        <div><span>Root returned</span><strong>{escape(_text(generated_artifact_verification["root_path_returned"]))}</strong></div>
      </div>
    </section>

    <section>
      <h2>Generated Workspace Static Validation</h2>
      <div class="boundary">
        <div><span>Status</span><strong>{escape(_text(generated_workspace_static_validation["status"]))}</strong></div>
        <div><span>Files checked</span><strong>{generated_workspace_static_validation["static_file_checked_count"]}</strong></div>
        <div><span>Package JSON</span><strong>{generated_workspace_static_validation["package_json_parse_pass_count"]}</strong></div>
        <div><span>Script labels</span><strong>{generated_workspace_static_validation["required_script_present_count"]}/4</strong></div>
        <div><span>App markers</span><strong>{generated_workspace_static_validation["app_component_marker_present_count"]}/13</strong></div>
        <div><span>API markers</span><strong>{generated_workspace_static_validation["api_marker_present_count"]}/8</strong></div>
        <div><span>Verification boundary markers</span><strong>{generated_workspace_static_validation["verification_boundary_marker_present_count"]}/4</strong></div>
        <div><span>Zero-call markers</span><strong>{generated_workspace_static_validation["zero_call_marker_present_count"]}/5</strong></div>
        <div><span>Content returned</span><strong>{escape(_text(generated_workspace_static_validation["file_content_returned"]))}</strong></div>
      </div>
    </section>

    <section>
      <h2>Build-Ready Candidate Manifest</h2>
      <div class="boundary">
        <div><span>Status</span><strong>{escape(_text(buildable_manifest["status"]))}</strong></div>
        <div><span>Candidate</span><strong>{escape(_text(buildable_manifest["candidate_label"]))}</strong></div>
        <div><span>Files read</span><strong>{buildable_manifest["required_file_read_count"]}</strong></div>
        <div><span>Script labels</span><strong>{buildable_manifest["required_script_present_count"]}/4</strong></div>
        <div><span>Dependency labels</span><strong>{buildable_manifest["total_dependency_label_count"]}</strong></div>
        <div><span>Placeholder values</span><strong>{buildable_manifest["placeholder_dependency_value_count"]}</strong></div>
        <div><span>Index markers</span><strong>{buildable_manifest["index_html_marker_present_count"]}/2</strong></div>
        <div><span>Main markers</span><strong>{buildable_manifest["main_entrypoint_marker_present_count"]}/2</strong></div>
        <div><span>Vite config</span><strong>{buildable_manifest["vite_config_marker_present_count"]}/2</strong></div>
        <div><span>TS config</span><strong>{buildable_manifest["tsconfig_marker_present_count"]}/2</strong></div>
        <div><span>Dependency values returned</span><strong>{escape(_text(buildable_manifest["dependency_value_returned"]))}</strong></div>
        <div><span>Content returned</span><strong>{escape(_text(buildable_manifest["file_content_returned"]))}</strong></div>
      </div>
    </section>

    <section>
      <h2>Local Build Preflight</h2>
      <div class="boundary">
        <div><span>Status</span><strong>{escape(_text(local_build_preflight["status"]))}</strong></div>
        <div><span>Eligible</span><strong>{escape(_text(local_build_preflight["eligible"]))}</strong></div>
        <div><span>Opt-in required</span><strong>{escape(_text(local_build_preflight["opt_in_required"]))}</strong></div>
        <div><span>Operator opt-in</span><strong>{escape(_text(local_build_preflight["operator_opt_in_present"]))}</strong></div>
        <div><span>Command labels</span><strong>{local_build_preflight["command_label_count"]}</strong></div>
        <div><span>Command hashes</span><strong>{local_build_preflight["command_hash_count"]}</strong></div>
        <div><span>Execution permission</span><strong>{local_build_preflight["default_execution_permission_count"]}</strong></div>
        <div><span>Dependency values returned</span><strong>{local_build_preflight["dependency_value_return_count"]}</strong></div>
        <div><span>Package installs</span><strong>{execution["local_build_preflight_package_install_calls"]}</strong></div>
        <div><span>Builds</span><strong>{execution["local_build_preflight_build_calls"]}</strong></div>
        <div><span>Server starts</span><strong>{execution["local_build_preflight_server_start_calls"]}</strong></div>
        <div><span>Network calls</span><strong>{execution["local_build_preflight_network_calls"]}</strong></div>
      </div>
      <p class="note">Planned labels: {escape(", ".join(local_build_preflight["command_labels"]) or "none")}. No command is executed by this preview.</p>
    </section>

    <section>
      <h2>Local Build Attempt</h2>
      <div class="boundary">
        <div><span>Status</span><strong>{escape(_text(local_build_attempt["status"]))}</strong></div>
        <div><span>Reason</span><strong>{escape(_text(local_build_attempt["reason"]))}</strong></div>
        <div><span>Attempted</span><strong>{escape(_text(local_build_attempt["attempted"]))}</strong></div>
        <div><span>Opt-in</span><strong>{escape(_text(local_build_attempt["opt_in_present"]))}</strong></div>
        <div><span>Command execution</span><strong>{escape(_text(local_build_attempt["command_execution_allowed"]))}</strong></div>
        <div><span>Command results</span><strong>{local_build_attempt["command_result_count"]}</strong></div>
        <div><span>Output hashes</span><strong>{local_build_attempt["command_output_hash_count"]}</strong></div>
        <div><span>Package installs</span><strong>{local_build_attempt["package_install_attempt_count"]}</strong></div>
        <div><span>Build attempts</span><strong>{local_build_attempt["build_attempt_count"]}</strong></div>
        <div><span>Server starts</span><strong>{local_build_attempt["server_start_attempt_count"]}</strong></div>
        <div><span>Raw output returned</span><strong>{local_build_attempt["raw_output_public_return_count"]}</strong></div>
        <div><span>Root returned</span><strong>{escape(_text(local_build_attempt["root_path_returned"]))}</strong></div>
      </div>
      <div class="grid">{_command_result_cards(local_build_attempt["command_results"])}</div>
    </section>

    <section>
      <h2>Interaction-Backed Portfolio Evidence</h2>
      <div class="boundary">
        <div><span>Capture status</span><strong>{escape(_text(local_preview_attempt["screenshot_capture_status"]))}</strong></div>
        <div><span>Capture reason</span><strong>{escape(_text(local_preview_attempt["screenshot_capture_reason"]))}</strong></div>
        <div><span>Screenshot evidence</span><strong>{local_preview_attempt["screenshot_evidence_count"]}</strong></div>
        <div><span>Screenshot hashes</span><strong>{local_preview_attempt["screenshot_hash_count"]}</strong></div>
        <div><span>Screenshot bytes</span><strong>{local_preview_attempt["screenshot_byte_count"]}</strong></div>
        <div><span>Owner filter click</span><strong>{escape(_text(local_preview_attempt["owner_filter_click_status"]))}</strong></div>
        <div><span>Click attempts</span><strong>{local_preview_attempt["owner_filter_click_attempt_count"]}</strong></div>
        <div><span>Click passes</span><strong>{local_preview_attempt["owner_filter_click_pass_count"]}</strong></div>
        <div><span>Target label hashes</span><strong>{local_preview_attempt["owner_filter_click_target_label_hash_count"]}</strong></div>
        <div><span>Tasks before click</span><strong>{local_preview_attempt["owner_filter_before_task_count"]}</strong></div>
        <div><span>Tasks after click</span><strong>{local_preview_attempt["owner_filter_after_task_count"]}</strong></div>
        <div><span>Changed task count</span><strong>{local_preview_attempt["owner_filter_changed_count"]}</strong></div>
        <div><span>Reviewer decision click</span><strong>{escape(_text(local_preview_attempt["reviewer_decision_click_status"]))}</strong></div>
        <div><span>Reviewer click attempts</span><strong>{local_preview_attempt["reviewer_decision_click_attempt_count"]}</strong></div>
        <div><span>Reviewer click passes</span><strong>{local_preview_attempt["reviewer_decision_click_pass_count"]}</strong></div>
        <div><span>Reviewer target label hashes</span><strong>{local_preview_attempt["reviewer_decision_click_target_label_hash_count"]}</strong></div>
        <div><span>Reviewer state hashes</span><strong>{local_preview_attempt["reviewer_decision_state_hash_count"]}</strong></div>
        <div><span>Reviewer state changes</span><strong>{local_preview_attempt["reviewer_decision_state_changed_count"]}</strong></div>
        <div><span>Server cleanup</span><strong>{local_preview_attempt["server_cleanup_percent"]}%</strong></div>
        <div><span>Path returned</span><strong>{escape(_text(local_preview_attempt["screenshot_path_returned"]))}</strong></div>
        <div><span>Page text returned</span><strong>{escape(_text(local_preview_attempt["page_text_returned"]))}</strong></div>
      </div>
    </section>

    <section>
      <h2>Local Preview Browser Verification</h2>
      <div class="boundary">
        <div><span>Status</span><strong>{escape(_text(local_preview_attempt["status"]))}</strong></div>
        <div><span>Reason</span><strong>{escape(_text(local_preview_attempt["reason"]))}</strong></div>
        <div><span>Attempted</span><strong>{escape(_text(local_preview_attempt["attempted"]))}</strong></div>
        <div><span>Opt-in</span><strong>{escape(_text(local_preview_attempt["opt_in_present"]))}</strong></div>
        <div><span>Server allowed</span><strong>{escape(_text(local_preview_attempt["server_allowed"]))}</strong></div>
        <div><span>Browser verify allowed</span><strong>{escape(_text(local_preview_attempt["browser_verification_allowed"]))}</strong></div>
        <div><span>Browser preflights</span><strong>{local_preview_attempt["preflight_count"]}</strong></div>
        <div><span>Browser available</span><strong>{local_preview_attempt["browser_available_count"]}</strong></div>
        <div><span>Runtime reason</span><strong>{escape(_text(local_preview_attempt["browser_runtime_reason"]))}</strong></div>
        <div><span>Server start attempts</span><strong>{local_preview_attempt["server_start_attempt_count"]}</strong></div>
        <div><span>Server starts</span><strong>{local_preview_attempt["server_start_count"]}</strong></div>
        <div><span>Server stops</span><strong>{local_preview_attempt["server_stop_count"]}</strong></div>
        <div><span>Server cleanup</span><strong>{local_preview_attempt["server_cleanup_percent"]}%</strong></div>
        <div><span>Screenshot evidence</span><strong>{local_preview_attempt["screenshot_evidence_count"]}</strong></div>
        <div><span>Screenshot hashes</span><strong>{local_preview_attempt["screenshot_hash_count"]}</strong></div>
        <div><span>Screenshot bytes</span><strong>{local_preview_attempt["screenshot_byte_count"]}</strong></div>
        <div><span>Owner filter click</span><strong>{escape(_text(local_preview_attempt["owner_filter_click_status"]))}</strong></div>
        <div><span>Click attempts</span><strong>{local_preview_attempt["owner_filter_click_attempt_count"]}</strong></div>
        <div><span>Click passes</span><strong>{local_preview_attempt["owner_filter_click_pass_count"]}</strong></div>
        <div><span>Target label hashes</span><strong>{local_preview_attempt["owner_filter_click_target_label_hash_count"]}</strong></div>
        <div><span>Tasks before click</span><strong>{local_preview_attempt["owner_filter_before_task_count"]}</strong></div>
        <div><span>Tasks after click</span><strong>{local_preview_attempt["owner_filter_after_task_count"]}</strong></div>
        <div><span>Changed task count</span><strong>{local_preview_attempt["owner_filter_changed_count"]}</strong></div>
        <div><span>Reviewer decision click</span><strong>{escape(_text(local_preview_attempt["reviewer_decision_click_status"]))}</strong></div>
        <div><span>Reviewer click attempts</span><strong>{local_preview_attempt["reviewer_decision_click_attempt_count"]}</strong></div>
        <div><span>Reviewer click passes</span><strong>{local_preview_attempt["reviewer_decision_click_pass_count"]}</strong></div>
        <div><span>Reviewer target label hashes</span><strong>{local_preview_attempt["reviewer_decision_click_target_label_hash_count"]}</strong></div>
        <div><span>Reviewer state hashes</span><strong>{local_preview_attempt["reviewer_decision_state_hash_count"]}</strong></div>
        <div><span>Reviewer state changes</span><strong>{local_preview_attempt["reviewer_decision_state_changed_count"]}</strong></div>
        <div><span>Raw output returned</span><strong>{local_preview_attempt["raw_output_returned"]}</strong></div>
        <div><span>Screenshot path returned</span><strong>{escape(_text(local_preview_attempt["screenshot_path_returned"]))}</strong></div>
        <div><span>Page text returned</span><strong>{escape(_text(local_preview_attempt["page_text_returned"]))}</strong></div>
      </div>
    </section>

    <section>
      <h2>Browser Runtime Setup Attempt</h2>
      <div class="boundary">
        <div><span>Status</span><strong>{escape(_text(browser_setup_attempt["status"]))}</strong></div>
        <div><span>Reason</span><strong>{escape(_text(browser_setup_attempt["reason"]))}</strong></div>
        <div><span>Attempted</span><strong>{escape(_text(browser_setup_attempt["attempted"]))}</strong></div>
        <div><span>Operator opt-in</span><strong>{escape(_text(browser_setup_attempt["operator_opt_in_present"]))}</strong></div>
        <div><span>Setup allowed</span><strong>{escape(_text(browser_setup_attempt["setup_allowed"]))}</strong></div>
        <div><span>Setup hash</span><strong>{escape(_short_hash(browser_setup_attempt["setup_attempt_hash"]))}</strong></div>
        <div><span>Browser preflights</span><strong>{browser_setup_attempt["browser_preflight_count"]}</strong></div>
        <div><span>Available before setup</span><strong>{browser_setup_attempt["browser_available_before_setup_count"]}</strong></div>
        <div><span>Setup command attempts</span><strong>{browser_setup_attempt["setup_command_attempt_count"]}</strong></div>
        <div><span>Default command executions</span><strong>{browser_setup_attempt["default_setup_command_execution_count"]}</strong></div>
        <div><span>Explicit opt-ins</span><strong>{browser_setup_attempt["explicit_setup_opt_in_count"]}</strong></div>
        <div><span>Available after setup</span><strong>{browser_setup_attempt["browser_available_after_setup_count"]}</strong></div>
        <div><span>Post-setup available</span><strong>{escape(_text(browser_setup_attempt["post_setup_available"]))}</strong></div>
        <div><span>Raw output returned</span><strong>{browser_setup_attempt["raw_output_returned"]}</strong></div>
        <div><span>Argv returned</span><strong>{browser_setup_attempt["argv_returned"]}</strong></div>
        <div><span>Browser errors returned</span><strong>{browser_setup_attempt["browser_error_returned"]}</strong></div>
        <div><span>Root returned</span><strong>{escape(_text(browser_setup_attempt["root_path_returned"]))}</strong></div>
      </div>
    </section>

    <div class="split">
      <section>
        <h2>Document Chain</h2>
        <ul class="doc-list">{_document_rows(model["document_artifacts"])}</ul>
      </section>
      <section>
        <h2>Verification</h2>
        <div class="boundary">
          <div><span>Status</span><strong>{escape(_text(verification["status"]))}</strong></div>
          <div><span>Reports</span><strong>{verification["report_count"]}</strong></div>
          <div><span>Checks</span><strong>{verification["check_count"]}</strong></div>
          <div><span>Failed</span><strong>{verification["failed_check_count"]}</strong></div>
        </div>
      </section>
    </div>

    <section>
      <h2>Execution Boundary</h2>
      <div class="boundary">
        <div><span>DAACS target runtime</span><strong>{execution["target_runtime_calls"]}</strong></div>
        <div><span>Provider calls</span><strong>{execution["provider_calls"]}</strong></div>
        <div><span>Subprocess calls</span><strong>{execution["subprocess_calls"]}</strong></div>
        <div><span>Network calls</span><strong>{execution["network_calls"]}</strong></div>
        <div><span>Package installs</span><strong>{execution["generated_workspace_package_install_calls"]}</strong></div>
        <div><span>Builds</span><strong>{execution["generated_workspace_build_calls"]}</strong></div>
        <div><span>Server starts</span><strong>{execution["generated_workspace_server_start_calls"]}</strong></div>
        <div><span>Verification file reads</span><strong>{execution["generated_artifact_verification_file_reads"]}</strong></div>
        <div><span>Static file reads</span><strong>{execution["generated_workspace_static_validation_file_reads"]}</strong></div>
        <div><span>Static package installs</span><strong>{execution["generated_workspace_static_validation_package_install_calls"]}</strong></div>
        <div><span>Static builds</span><strong>{execution["generated_workspace_static_validation_build_calls"]}</strong></div>
        <div><span>Static server starts</span><strong>{execution["generated_workspace_static_validation_server_start_calls"]}</strong></div>
        <div><span>Build-ready file reads</span><strong>{execution["buildable_manifest_file_reads"]}</strong></div>
        <div><span>Build-ready package installs</span><strong>{execution["buildable_manifest_package_install_calls"]}</strong></div>
        <div><span>Build-ready builds</span><strong>{execution["buildable_manifest_build_calls"]}</strong></div>
        <div><span>Build-ready server starts</span><strong>{execution["buildable_manifest_server_start_calls"]}</strong></div>
        <div><span>Local preflight package installs</span><strong>{execution["local_build_preflight_package_install_calls"]}</strong></div>
        <div><span>Local preflight builds</span><strong>{execution["local_build_preflight_build_calls"]}</strong></div>
        <div><span>Local preflight server starts</span><strong>{execution["local_build_preflight_server_start_calls"]}</strong></div>
        <div><span>Local preflight execution permission</span><strong>{execution["local_build_preflight_execution_permission_count"]}</strong></div>
        <div><span>Local build package installs</span><strong>{execution["local_build_attempt_package_install_calls"]}</strong></div>
        <div><span>Local build builds</span><strong>{execution["local_build_attempt_build_calls"]}</strong></div>
        <div><span>Local build server starts</span><strong>{execution["local_build_attempt_server_start_calls"]}</strong></div>
        <div><span>Local build subprocesses</span><strong>{execution["local_build_attempt_subprocess_calls"]}</strong></div>
        <div><span>Local build network attempts</span><strong>{execution["local_build_attempt_network_calls"]}</strong></div>
        <div><span>Local build target runtime</span><strong>{execution["local_build_attempt_target_runtime_calls"]}</strong></div>
        <div><span>Local build provider calls</span><strong>{execution["local_build_attempt_provider_calls"]}</strong></div>
        <div><span>Preview server starts</span><strong>{execution["local_preview_attempt_server_start_calls"]}</strong></div>
        <div><span>Preview server stops</span><strong>{execution["local_preview_attempt_server_stop_calls"]}</strong></div>
        <div><span>Preview target runtime</span><strong>{execution["local_preview_attempt_target_runtime_calls"]}</strong></div>
        <div><span>Preview provider calls</span><strong>{execution["local_preview_attempt_provider_calls"]}</strong></div>
        <div><span>Browser setup processes</span><strong>{execution["browser_setup_local_process_calls"]}</strong></div>
        <div><span>Browser setup package installs</span><strong>{execution["browser_setup_package_install_calls"]}</strong></div>
        <div><span>Browser binary installs</span><strong>{execution["browser_setup_binary_install_calls"]}</strong></div>
        <div><span>Browser setup target runtime</span><strong>{execution["browser_setup_target_runtime_calls"]}</strong></div>
        <div><span>Browser setup provider calls</span><strong>{execution["browser_setup_provider_calls"]}</strong></div>
        <div><span>Outside workspace writes</span><strong>{fixture["outside_workspace_write_count"]}</strong></div>
        <div><span>Artifact content returned</span><strong>{escape(_text(fixture["artifact_content_returned"]))}</strong></div>
        <div><span>Generated content returned</span><strong>{escape(_text(generated_workspace["file_content_returned"]))}</strong></div>
        <div><span>Root path returned</span><strong>{escape(_text(fixture["root_path_returned"]))}</strong></div>
        <div><span>Claim drift</span><strong>{comparison["public_claim_drift_findings"]}</strong></div>
      </div>
    </section>

    <section>
      <h2>Claim Boundary</h2>
      <div class="boundary">
        <div><span>Scope</span><strong>{escape(_text(claim["scope"]))}</strong></div>
        <div><span>Runtime outcome</span><strong>{escape(_text(claim["target_runtime_outcome"]))}</strong></div>
        <div><span>Provider outcome</span><strong>{escape(_text(claim["external_provider_outcome"]))}</strong></div>
        <div><span>Hosted behavior</span><strong>{escape(_text(claim["hosted_behavior"]))}</strong></div>
      </div>
    </section>

    <p class="note">This preview uses sanitized public summary fields only. It renders labels, counts, hashes, and workspace-relative paths without file contents, local roots, or secret values.</p>
  </main>
</body>
</html>
"""
    assert_public_projection_safe({"artifact_preview_html": html})
    return html


def write_artifact_preview(summary: dict[str, Any], output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    html = render_artifact_preview(summary)
    output.write_text(html, encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the AW-APP-01 artifact preview.")
    parser.add_argument(
        "--store-root",
        default=None,
        help="Optional local store root. Defaults to examples/demo-service-flow/.local.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output HTML path. If omitted, HTML is printed to stdout.",
    )
    parser.add_argument(
        "--include-local-build-attempt",
        action="store_true",
        help=(
            "Include the AW-BUILD-04 local build attempt boundary. Without "
            "--allow-local-build-attempt it renders a blocked opt-in state."
        ),
    )
    parser.add_argument(
        "--allow-local-build-attempt",
        action="store_true",
        help="Allow local npm install/build in the generated fixture app workspace.",
    )
    args = parser.parse_args()

    summary = run_demo(
        args.store_root,
        include_daacs_runtime_local_build_preflight=True,
        include_daacs_runtime_local_build_attempt=args.include_local_build_attempt,
        allow_local_build_attempt=args.allow_local_build_attempt,
    )
    if args.output:
        output = write_artifact_preview(summary, args.output)
        print(f"Wrote {output.name}")
        return
    print(render_artifact_preview(summary))


if __name__ == "__main__":
    main()

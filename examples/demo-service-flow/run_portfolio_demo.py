"""Run the portfolio-facing local Agentic Workbench demo package."""

from __future__ import annotations

import argparse
import json
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
from packages.core.schemas import stable_contract_hash
from render_artifact_preview import write_artifact_preview
from run_local_demo import run_demo


PORTFOLIO_DEMO_ID = "AW-DEMO-FINAL-04"
DEFAULT_OUTPUT_DIR = Path(".local") / "aw-demo-final-04"
DEFAULT_SUMMARY_NAME = "aw-demo-final-04-summary.json"
DEFAULT_PREVIEW_NAME = "aw-demo-final-04-preview.html"


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _count(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _interaction_package_status(
    *,
    screenshot_hash_count: int,
    owner_pass_count: int,
    reviewer_pass_count: int,
) -> tuple[str, str]:
    if screenshot_hash_count and owner_pass_count and reviewer_pass_count:
        return "verified", "screenshot_owner_reviewer_evidence_packaged"
    if owner_pass_count or reviewer_pass_count:
        return "partial", "interaction_evidence_partial"
    return "blocked", "interaction_evidence_not_available"


def _build_interaction_evidence_package(
    *,
    local_preview_attempt: dict[str, Any],
    local_preview_counts: dict[str, Any],
    screenshot_hash_count: int,
    preview_cleanup_percent: float,
) -> dict[str, Any]:
    preview_record = _mapping(local_preview_attempt.get("preview_record"))
    owner_pass_count = _count(
        local_preview_counts.get("owner_filter_click_pass_count")
    )
    reviewer_pass_count = _count(
        local_preview_counts.get("reviewer_decision_click_pass_count")
    )
    status, reason = _interaction_package_status(
        screenshot_hash_count=screenshot_hash_count,
        owner_pass_count=owner_pass_count,
        reviewer_pass_count=reviewer_pass_count,
    )
    owner_hash_evidence_count = _count(
        local_preview_counts.get("owner_filter_click_target_label_hash_count")
    )
    reviewer_hash_evidence_count = _count(
        local_preview_counts.get(
            "reviewer_decision_click_target_label_hash_count"
        )
    ) + _count(local_preview_counts.get("reviewer_decision_state_hash_count"))
    package = {
        "package_id": PORTFOLIO_DEMO_ID,
        "status": status,
        "reason": reason,
        "interaction_path_count": 2,
        "verified_interaction_path_count": (
            (1 if owner_pass_count else 0)
            + (1 if reviewer_pass_count else 0)
        ),
        "interaction_hash_evidence_count": (
            owner_hash_evidence_count + reviewer_hash_evidence_count
        ),
        "screenshot_hash_count": screenshot_hash_count,
        "preview_server_cleanup_percent": preview_cleanup_percent,
        "paths": [
            {
                "name": "owner_filter",
                "status": preview_record.get(
                    "owner_filter_click_status", "not_requested"
                ),
                "click_attempt_count": _count(
                    local_preview_counts.get("owner_filter_click_attempt_count")
                ),
                "click_pass_count": owner_pass_count,
                "target_label_hash_count": owner_hash_evidence_count,
                "before_count": _count(
                    local_preview_counts.get("owner_filter_before_task_count")
                ),
                "after_count": _count(
                    local_preview_counts.get("owner_filter_after_task_count")
                ),
                "changed_count": _count(
                    local_preview_counts.get("owner_filter_changed_count")
                ),
                "dom_text_return_count": _count(
                    local_preview_counts.get("owner_filter_dom_text_return_count")
                ),
                "event_return_count": _count(
                    local_preview_counts.get("owner_filter_raw_event_return_count")
                ),
            },
            {
                "name": "reviewer_decision",
                "status": preview_record.get(
                    "reviewer_decision_click_status", "not_requested"
                ),
                "click_attempt_count": _count(
                    local_preview_counts.get(
                        "reviewer_decision_click_attempt_count"
                    )
                ),
                "click_pass_count": reviewer_pass_count,
                "target_label_hash_count": _count(
                    local_preview_counts.get(
                        "reviewer_decision_click_target_label_hash_count"
                    )
                ),
                "state_hash_count": _count(
                    local_preview_counts.get(
                        "reviewer_decision_state_hash_count"
                    )
                ),
                "state_changed_count": _count(
                    local_preview_counts.get(
                        "reviewer_decision_state_changed_count"
                    )
                ),
                "dom_text_return_count": _count(
                    local_preview_counts.get(
                        "reviewer_decision_dom_text_return_count"
                    )
                ),
                "event_return_count": _count(
                    local_preview_counts.get(
                        "reviewer_decision_raw_event_return_count"
                    )
                ),
            },
        ],
        "exposure_counts": {
            "dom_text_return_count": _count(
                local_preview_counts.get("owner_filter_dom_text_return_count")
            )
            + _count(
                local_preview_counts.get(
                    "reviewer_decision_dom_text_return_count"
                )
            ),
            "event_return_count": _count(
                local_preview_counts.get("owner_filter_raw_event_return_count")
            )
            + _count(
                local_preview_counts.get(
                    "reviewer_decision_raw_event_return_count"
                )
            ),
            "page_text_return_count": _count(
                local_preview_counts.get("page_text_return_count")
            ),
            "screenshot_path_return_count": _count(
                local_preview_counts.get("screenshot_path_return_count")
            ),
        },
    }
    package["package_evidence_hash"] = stable_contract_hash(package)
    assert_public_projection_safe(package)
    return package


def build_portfolio_demo_report(
    summary: dict[str, Any],
    *,
    summary_name: str = DEFAULT_SUMMARY_NAME,
    preview_name: str = DEFAULT_PREVIEW_NAME,
    local_build_opt_in: bool = False,
    local_preview_opt_in: bool = False,
    browser_runtime_setup_opt_in: bool = False,
    screenshot_backed_opt_in: bool = False,
) -> dict[str, Any]:
    """Build a public-safe portfolio report from the demo summary."""
    assert_public_projection_safe(summary)
    stage_coverage = _mapping(summary.get("workflow_stage_coverage"))
    generated_workspace = _mapping(
        summary.get("daacs_runtime_restricted_workspace_generation")
    )
    generated_counts = _mapping(generated_workspace.get("counts"))
    local_build_attempt = _mapping(
        summary.get("daacs_runtime_local_build_attempt")
    )
    local_build_counts = _mapping(local_build_attempt.get("counts"))
    local_build_execution = _mapping(local_build_attempt.get("execution_boundary"))
    local_preview_attempt = _mapping(
        summary.get("daacs_runtime_local_preview_attempt")
    )
    local_preview_counts = _mapping(local_preview_attempt.get("counts"))
    local_preview_execution = _mapping(
        local_preview_attempt.get("execution_boundary")
    )
    browser_preflight = _mapping(
        local_preview_attempt.get("browser_runtime_preflight")
    )
    browser_setup_attempt = _mapping(
        summary.get("daacs_runtime_browser_setup_attempt")
    )
    browser_setup_counts = _mapping(browser_setup_attempt.get("counts"))
    browser_setup_execution = _mapping(
        browser_setup_attempt.get("execution_boundary")
    )
    post_setup_preflight = _mapping(
        browser_setup_attempt.get("post_setup_browser_runtime_preflight")
    )
    comparison = _mapping(summary.get("daacs_runtime_comparison"))
    preview_server_start_attempt_count = _count(
        local_preview_counts.get("preview_server_start_attempt_count")
    )
    preview_server_started_count = _count(
        local_preview_counts.get("server_start_count")
    )
    preview_server_stop_count = _count(
        local_preview_counts.get("preview_server_stop_count")
    )
    screenshot_evidence_count = _count(
        local_preview_counts.get("screenshot_evidence_count")
    )
    screenshot_hash_count = _count(local_preview_counts.get("screenshot_hash_count"))
    screenshot_byte_count = _count(local_preview_counts.get("screenshot_byte_count"))
    owner_filter_click_pass_count = _count(
        local_preview_counts.get("owner_filter_click_pass_count")
    )
    owner_filter_click_status = _mapping(
        local_preview_attempt.get("preview_record")
    ).get("owner_filter_click_status", "not_requested")
    reviewer_decision_click_pass_count = _count(
        local_preview_counts.get("reviewer_decision_click_pass_count")
    )
    reviewer_decision_click_status = _mapping(
        local_preview_attempt.get("preview_record")
    ).get("reviewer_decision_click_status", "not_requested")
    screenshot_status = (
        "verified"
        if screenshot_evidence_count and screenshot_hash_count
        else local_preview_attempt.get("status", "not_requested")
    )
    screenshot_reason = (
        "screenshot_hash_recorded"
        if screenshot_evidence_count and screenshot_hash_count
        else local_preview_attempt.get("reason", "not_requested")
    )
    preview_cleanup_percent = (
        100.0
        if (
            preview_server_started_count
            and preview_server_stop_count >= preview_server_started_count
        )
        else 0.0
    )
    interaction_evidence_package = _build_interaction_evidence_package(
        local_preview_attempt=local_preview_attempt,
        local_preview_counts=local_preview_counts,
        screenshot_hash_count=screenshot_hash_count,
        preview_cleanup_percent=preview_cleanup_percent,
    )

    server_start_count = _count(
        local_build_execution.get("server_start_call_count")
    ) + _count(local_preview_execution.get("server_start_calls"))
    provider_call_count = (
        _count(local_build_execution.get("provider_call_count"))
        + _count(local_preview_execution.get("provider_calls"))
        + _count(browser_setup_execution.get("provider_calls"))
    )
    daacs_target_runtime_call_count = (
        _count(local_build_execution.get("target_runtime_call_count"))
        + _count(local_preview_execution.get("target_runtime_calls"))
        + _count(browser_setup_execution.get("daacs_target_runtime_calls"))
    )
    raw_public_body_exposure_count = (
        _count(local_build_counts.get("raw_output_public_return_count"))
        + _count(local_build_counts.get("file_content_public_return_count"))
        + _count(local_preview_counts.get("raw_output_public_return_count"))
        + _count(browser_setup_counts.get("raw_output_public_return_count"))
        + _count(browser_setup_counts.get("argv_public_return_count"))
        + _count(browser_setup_counts.get("browser_error_public_return_count"))
    )

    report = {
        "demo_id": PORTFOLIO_DEMO_ID,
        "source_demo_id": summary.get("demo_id", "unknown"),
        "status": summary.get("status", "unknown"),
        "run_id": summary.get("run_id", "unknown"),
        "projection_version": "portfolio-demo-public-v1",
        "outputs": {
            "summary_json": Path(summary_name).name,
            "preview_html": Path(preview_name).name,
        },
        "stage_coverage": {
            "covered": _count(stage_coverage.get("covered_stage_count")),
            "required": _count(stage_coverage.get("required_stage_count")),
            "percent": stage_coverage.get("coverage_percent", 0),
        },
        "portfolio_metrics": {
            "portfolio_command_count": 1,
            "screenshot_backed_package_count": 1
            if screenshot_backed_opt_in
            else 0,
            "preview_html_generated": 1,
            "generated_fixture_app_file_count": _count(
                generated_counts.get("generated_workspace_file_record_count")
            ),
            "local_build_attempt_evidence_count": (
                1 if local_build_attempt else 0
            ),
            "local_build_opt_in_present": 1 if local_build_opt_in else 0,
            "local_build_attempt_status": local_build_attempt.get(
                "status", "not_requested"
            ),
            "local_build_attempt_reason": local_build_attempt.get(
                "reason", "not_requested"
            ),
            "local_build_command_result_count": _count(
                local_build_counts.get("command_result_count")
            ),
            "local_build_package_install_attempts": _count(
                local_build_counts.get("package_install_attempt_count")
            ),
            "local_build_build_attempts": _count(
                local_build_counts.get("build_attempt_count")
            ),
            "local_preview_attempt_evidence_count": (
                1 if local_preview_attempt else 0
            ),
            "local_preview_opt_in_present": 1 if local_preview_opt_in else 0,
            "local_preview_status": local_preview_attempt.get(
                "status", "not_requested"
            ),
            "local_preview_reason": local_preview_attempt.get(
                "reason", "not_requested"
            ),
            "browser_runtime_preflight_count": _count(
                local_preview_counts.get("browser_runtime_preflight_count")
            ),
            "browser_runtime_available_count": _count(
                local_preview_counts.get("browser_runtime_available_count")
            ),
            "browser_runtime_available": bool(browser_preflight.get("available")),
            "preview_server_start_count": preview_server_start_attempt_count,
            "preview_server_start_attempt_count": preview_server_start_attempt_count,
            "preview_server_started_count": preview_server_started_count,
            "preview_server_stop_count": preview_server_stop_count,
            "preview_server_cleanup_percent": preview_cleanup_percent,
            "screenshot_capture_status": screenshot_status,
            "screenshot_capture_reason": screenshot_reason,
            "screenshot_capture_ready_count": 1
            if screenshot_evidence_count and screenshot_hash_count
            else 0,
            "screenshot_capture_blocked_count": 0
            if screenshot_evidence_count
            else (1 if local_preview_opt_in else 0),
            "screenshot_evidence_count": screenshot_evidence_count,
            "screenshot_hash_count": screenshot_hash_count,
            "screenshot_byte_count": screenshot_byte_count,
            "owner_filter_click_status": owner_filter_click_status,
            "owner_filter_click_attempt_count": _count(
                local_preview_counts.get("owner_filter_click_attempt_count")
            ),
            "owner_filter_click_pass_count": owner_filter_click_pass_count,
            "owner_filter_click_target_label_hash_count": _count(
                local_preview_counts.get(
                    "owner_filter_click_target_label_hash_count"
                )
            ),
            "owner_filter_before_task_count": _count(
                local_preview_counts.get("owner_filter_before_task_count")
            ),
            "owner_filter_after_task_count": _count(
                local_preview_counts.get("owner_filter_after_task_count")
            ),
            "owner_filter_changed_count": _count(
                local_preview_counts.get("owner_filter_changed_count")
            ),
            "owner_filter_e2e_verified_count": 1
            if owner_filter_click_pass_count
            else 0,
            "reviewer_decision_click_status": reviewer_decision_click_status,
            "reviewer_decision_click_attempt_count": _count(
                local_preview_counts.get("reviewer_decision_click_attempt_count")
            ),
            "reviewer_decision_click_pass_count": (
                reviewer_decision_click_pass_count
            ),
            "reviewer_decision_click_target_label_hash_count": _count(
                local_preview_counts.get(
                    "reviewer_decision_click_target_label_hash_count"
                )
            ),
            "reviewer_decision_state_hash_count": _count(
                local_preview_counts.get("reviewer_decision_state_hash_count")
            ),
            "reviewer_decision_state_changed_count": _count(
                local_preview_counts.get(
                    "reviewer_decision_state_changed_count"
                )
            ),
            "reviewer_decision_e2e_verified_count": 1
            if reviewer_decision_click_pass_count
            else 0,
            "interaction_backed_package_count": (
                1 if interaction_evidence_package["status"] == "verified" else 0
            ),
            "interaction_path_count": interaction_evidence_package[
                "interaction_path_count"
            ],
            "interaction_verified_path_count": interaction_evidence_package[
                "verified_interaction_path_count"
            ],
            "interaction_hash_evidence_count": interaction_evidence_package[
                "interaction_hash_evidence_count"
            ],
            "interaction_package_hash_count": (
                1 if interaction_evidence_package.get("package_evidence_hash") else 0
            ),
            "interaction_dom_text_exposure_count": (
                interaction_evidence_package["exposure_counts"][
                    "dom_text_return_count"
                ]
            ),
            "interaction_event_exposure_count": (
                interaction_evidence_package["exposure_counts"][
                    "event_return_count"
                ]
            ),
            "local_preview_retry_after_browser_setup_count": _count(
                comparison.get("local_preview_retry_after_browser_setup_count")
            ),
            "browser_setup_status_field_count": (
                1 if browser_setup_attempt else 0
            ),
            "browser_setup_opt_in_present": (
                1 if browser_runtime_setup_opt_in else 0
            ),
            "browser_setup_status": browser_setup_attempt.get(
                "status", "not_requested"
            ),
            "browser_setup_reason": browser_setup_attempt.get(
                "reason", "not_requested"
            ),
            "browser_setup_preflight_count": _count(
                browser_setup_counts.get("browser_runtime_preflight_count")
            ),
            "browser_runtime_available_before_setup_count": _count(
                browser_setup_counts.get(
                    "browser_runtime_available_before_setup_count"
                )
            ),
            "browser_setup_command_attempt_count": _count(
                browser_setup_counts.get("setup_command_attempt_count")
            ),
            "browser_setup_default_command_execution_count": _count(
                browser_setup_counts.get("default_setup_command_execution_count")
            ),
            "browser_runtime_available_after_setup_count": _count(
                browser_setup_counts.get(
                    "browser_runtime_available_after_setup_count"
                )
            ),
            "browser_runtime_available_after_setup": bool(
                post_setup_preflight.get("available")
            ),
            "server_start_count": server_start_count,
            "provider_call_count": provider_call_count,
            "daacs_target_runtime_call_count": daacs_target_runtime_call_count,
            "raw_public_body_exposure_count": raw_public_body_exposure_count,
            "local_root_path_exposure_count": _count(
                local_build_counts.get("local_root_path_return_count")
            )
            + _count(local_preview_counts.get("local_root_path_return_count"))
            + _count(browser_setup_counts.get("local_root_path_return_count")),
            "screenshot_path_exposure_count": _count(
                local_preview_counts.get("screenshot_path_return_count")
            ),
            "page_text_exposure_count": _count(
                local_preview_counts.get("page_text_return_count")
            ),
            "public_claim_drift_findings": _count(
                comparison.get("public_claim_drift_findings")
            ),
        },
        "claim_boundary": {
            "scope": "local_fixture_portfolio_demo",
            "hosted_behavior": False,
            "external_provider_outcome": False,
            "target_runtime_outcome": False,
            "raw_file_body_returned": False,
            "raw_command_output_returned": False,
            "local_root_path_returned": False,
            "screenshot_success_claim": False,
            "browser_setup_success_claim": False,
            "owner_filter_click_path_claim": False,
            "reviewer_decision_click_path_claim": False,
            "interaction_package_live_claim": False,
        },
        "interaction_evidence_package": interaction_evidence_package,
        "next_action": "review_interaction_backed_package_and_choose_demo_readme_or_deployment_packaging",
    }
    assert_public_projection_safe(report)
    return report


def run_portfolio_demo(
    *,
    store_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    allow_local_build_attempt: bool = False,
    allow_local_preview_attempt: bool = False,
    allow_browser_runtime_setup: bool = False,
    screenshot_backed: bool = False,
) -> dict[str, Any]:
    """Run demo, write sanitized summary JSON and static preview HTML."""
    if screenshot_backed:
        allow_local_build_attempt = True
        allow_local_preview_attempt = True

    output_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    output_root.mkdir(parents=True, exist_ok=True)
    summary_path = output_root / DEFAULT_SUMMARY_NAME
    preview_path = output_root / DEFAULT_PREVIEW_NAME

    summary = run_demo(
        store_root or output_root / "store",
        include_daacs_runtime_local_build_attempt=True,
        include_daacs_runtime_local_preview_attempt=True,
        include_daacs_runtime_browser_setup_attempt=True,
        allow_local_build_attempt=allow_local_build_attempt,
        allow_local_preview_attempt=allow_local_preview_attempt,
        allow_browser_runtime_setup=allow_browser_runtime_setup,
    )
    assert_public_projection_safe(summary)
    write_artifact_preview(summary, preview_path)
    report = build_portfolio_demo_report(
        summary,
        summary_name=summary_path.name,
        preview_name=preview_path.name,
        local_build_opt_in=allow_local_build_attempt,
        local_preview_opt_in=allow_local_preview_attempt,
        browser_runtime_setup_opt_in=allow_browser_runtime_setup,
        screenshot_backed_opt_in=screenshot_backed,
    )
    summary_path.write_text(
        json.dumps(
            {
                "portfolio_report": report,
                "public_demo_summary": summary,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the portfolio-facing Agentic Workbench local demo."
    )
    parser.add_argument(
        "--store-root",
        default=None,
        help="Optional local demo store root. Defaults under the output directory.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory. Defaults to .local/aw-demo-final-04.",
    )
    parser.add_argument(
        "--screenshot-backed",
        action="store_true",
        help=(
            "Run the portfolio package with explicit local build and local "
            "preview screenshot evidence opt-ins. Browser runtime setup still "
            "requires --allow-browser-runtime-setup."
        ),
    )
    parser.add_argument(
        "--allow-local-build-attempt",
        action="store_true",
        help=(
            "Allow one local npm install/build attempt inside the run-scoped "
            "generated fixture app workspace."
        ),
    )
    parser.add_argument(
        "--allow-local-preview-attempt",
        action="store_true",
        help=(
            "Allow the existing local preview-server/browser verification "
            "attempt. Defaults to blocked evidence only."
        ),
    )
    parser.add_argument(
        "--allow-browser-runtime-setup",
        action="store_true",
        help=(
            "Allow the existing browser runtime setup attempt. Defaults to "
            "zero setup command executions."
        ),
    )
    args = parser.parse_args()

    report = run_portfolio_demo(
        store_root=args.store_root,
        output_dir=args.output_dir,
        allow_local_build_attempt=args.allow_local_build_attempt,
        allow_local_preview_attempt=args.allow_local_preview_attempt,
        allow_browser_runtime_setup=args.allow_browser_runtime_setup,
        screenshot_backed=args.screenshot_backed,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

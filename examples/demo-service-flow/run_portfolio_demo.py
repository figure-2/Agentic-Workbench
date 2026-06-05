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
from render_artifact_preview import write_artifact_preview
from run_local_demo import run_demo


PORTFOLIO_DEMO_ID = "AW-DEMO-FINAL-01"
DEFAULT_OUTPUT_DIR = Path(".local") / "aw-demo-final-01"
DEFAULT_SUMMARY_NAME = "aw-demo-final-01-summary.json"
DEFAULT_PREVIEW_NAME = "aw-demo-final-01-preview.html"


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _count(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def build_portfolio_demo_report(
    summary: dict[str, Any],
    *,
    summary_name: str = DEFAULT_SUMMARY_NAME,
    preview_name: str = DEFAULT_PREVIEW_NAME,
    local_build_opt_in: bool = False,
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
    comparison = _mapping(summary.get("daacs_runtime_comparison"))

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
            "server_start_count": _count(
                local_build_execution.get("server_start_call_count")
            ),
            "provider_call_count": _count(
                local_build_execution.get("provider_call_count")
            ),
            "daacs_target_runtime_call_count": _count(
                local_build_execution.get("target_runtime_call_count")
            ),
            "raw_public_body_exposure_count": _count(
                local_build_counts.get("raw_output_public_return_count")
            )
            + _count(local_build_counts.get("file_content_public_return_count")),
            "local_root_path_exposure_count": _count(
                local_build_counts.get("local_root_path_return_count")
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
        },
        "next_action": "review_static_preview_and_decide_live_planner_or_runtime_mvp",
    }
    assert_public_projection_safe(report)
    return report


def run_portfolio_demo(
    *,
    store_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    allow_local_build_attempt: bool = False,
) -> dict[str, Any]:
    """Run demo, write sanitized summary JSON and static preview HTML."""
    output_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    output_root.mkdir(parents=True, exist_ok=True)
    summary_path = output_root / DEFAULT_SUMMARY_NAME
    preview_path = output_root / DEFAULT_PREVIEW_NAME

    summary = run_demo(
        store_root or output_root / "store",
        include_daacs_runtime_local_build_attempt=True,
        allow_local_build_attempt=allow_local_build_attempt,
    )
    assert_public_projection_safe(summary)
    write_artifact_preview(summary, preview_path)
    report = build_portfolio_demo_report(
        summary,
        summary_name=summary_path.name,
        preview_name=preview_path.name,
        local_build_opt_in=allow_local_build_attempt,
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
        help="Optional output directory. Defaults to .local/aw-demo-final-01.",
    )
    parser.add_argument(
        "--allow-local-build-attempt",
        action="store_true",
        help=(
            "Allow one local npm install/build attempt inside the run-scoped "
            "generated fixture app workspace."
        ),
    )
    args = parser.parse_args()

    report = run_portfolio_demo(
        store_root=args.store_root,
        output_dir=args.output_dir,
        allow_local_build_attempt=args.allow_local_build_attempt,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

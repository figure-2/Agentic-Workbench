import importlib.util
import json
from pathlib import Path

from packages.core.public_projection import assert_public_projection_safe


PORTFOLIO_DEMO_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "demo-service-flow"
    / "run_portfolio_demo.py"
)


def _load_portfolio_demo_module():
    spec = importlib.util.spec_from_file_location(
        "aw_demo_final_02_portfolio_demo", PORTFOLIO_DEMO_SCRIPT
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_no_setup_command_path(metrics):
    """Browser setup may be blocked or already satisfied by a system browser."""

    assert metrics["browser_setup_status"] in {"blocked", "passed"}
    assert metrics["browser_setup_opt_in_present"] == 0
    assert metrics["browser_setup_preflight_count"] == 1
    assert metrics["browser_setup_command_attempt_count"] == 0
    assert metrics["browser_setup_default_command_execution_count"] == 0
    if metrics["browser_setup_status"] == "blocked":
        assert metrics["browser_setup_reason"] == (
            "browser_runtime_setup_opt_in_required"
        )
        assert metrics["browser_runtime_available_before_setup_count"] == 0
    else:
        assert metrics["browser_setup_reason"] == "browser_runtime_already_available"
        assert metrics["browser_runtime_available_before_setup_count"] == 1


def test_portfolio_demo_writes_summary_and_preview_without_local_root(tmp_path):
    module = _load_portfolio_demo_module()
    output_dir = tmp_path / "portfolio-output"

    report = module.run_portfolio_demo(output_dir=output_dir)

    summary_path = output_dir / "aw-demo-final-04-summary.json"
    preview_path = output_dir / "aw-demo-final-04-preview.html"
    assert summary_path.exists()
    assert preview_path.exists()
    assert report["demo_id"] == "AW-DEMO-FINAL-04"
    assert report["status"] == "passed"
    assert report["outputs"] == {
        "summary_json": "aw-demo-final-04-summary.json",
        "preview_html": "aw-demo-final-04-preview.html",
    }
    assert report["stage_coverage"]["covered"] == 7
    assert report["stage_coverage"]["required"] == 7
    metrics = report["portfolio_metrics"]
    assert metrics["portfolio_command_count"] == 1
    assert metrics["screenshot_backed_package_count"] == 0
    assert metrics["preview_html_generated"] == 1
    assert metrics["generated_fixture_app_file_count"] == 9
    assert metrics["local_build_attempt_evidence_count"] == 1
    assert metrics["local_build_opt_in_present"] == 0
    assert metrics["local_build_attempt_status"] == "blocked"
    assert metrics["local_build_package_install_attempts"] == 0
    assert metrics["local_build_build_attempts"] == 0
    assert metrics["local_preview_attempt_evidence_count"] == 1
    assert metrics["local_preview_status"] == "blocked"
    assert metrics["local_preview_reason"] == "local_preview_opt_in_required"
    assert metrics["local_preview_opt_in_present"] == 0
    assert metrics["browser_runtime_preflight_count"] == 0
    assert metrics["preview_server_start_count"] == 0
    assert metrics["preview_server_start_attempt_count"] == 0
    assert metrics["preview_server_started_count"] == 0
    assert metrics["preview_server_stop_count"] == 0
    assert metrics["preview_server_cleanup_percent"] == 0
    assert metrics["screenshot_capture_status"] == "blocked"
    assert metrics["screenshot_capture_reason"] == "local_preview_opt_in_required"
    assert metrics["screenshot_capture_ready_count"] == 0
    assert metrics["screenshot_capture_blocked_count"] == 0
    assert metrics["screenshot_evidence_count"] == 0
    assert metrics["screenshot_hash_count"] == 0
    assert metrics["screenshot_byte_count"] == 0
    assert metrics["interaction_backed_package_count"] == 0
    assert metrics["interaction_path_count"] == 2
    assert metrics["interaction_verified_path_count"] == 0
    assert metrics["interaction_hash_evidence_count"] == 0
    assert metrics["interaction_package_hash_count"] == 1
    assert metrics["interaction_dom_text_exposure_count"] == 0
    assert metrics["interaction_event_exposure_count"] == 0
    assert metrics["browser_setup_status_field_count"] == 1
    _assert_no_setup_command_path(metrics)
    assert metrics["local_preview_retry_after_browser_setup_count"] == 0
    assert metrics["server_start_count"] == 0
    assert metrics["provider_call_count"] == 0
    assert metrics["daacs_target_runtime_call_count"] == 0
    assert metrics["raw_public_body_exposure_count"] == 0
    assert metrics["local_root_path_exposure_count"] == 0
    assert metrics["screenshot_path_exposure_count"] == 0
    assert metrics["page_text_exposure_count"] == 0
    assert_public_projection_safe(report)

    summary_text = summary_path.read_text(encoding="utf-8")
    html = preview_path.read_text(encoding="utf-8")
    assert "Agentic Workbench Artifact Preview" in html
    assert "local build: not attempted" in html
    assert "Local Preview Browser Verification" in html
    assert "Interaction-Backed Portfolio Evidence" in html
    assert "Browser Runtime Setup Attempt" in html
    assert "AW-DEMO-FINAL-04" in summary_text
    assert report["interaction_evidence_package"]["status"] == "blocked"
    assert report["interaction_evidence_package"]["interaction_path_count"] == 2
    assert report["interaction_evidence_package"]["package_evidence_hash"]
    assert str(tmp_path) not in json.dumps(report, ensure_ascii=False)
    assert str(tmp_path) not in html


def test_portfolio_demo_cli_prints_sanitized_report(tmp_path, capsys):
    module = _load_portfolio_demo_module()
    output_dir = tmp_path / "portfolio-cli-output"

    old_argv = module.sys.argv
    try:
        module.sys.argv = [
            "run_portfolio_demo.py",
            "--output-dir",
            str(output_dir),
        ]
        module.main()
    finally:
        module.sys.argv = old_argv

    stdout = capsys.readouterr().out
    data = json.loads(stdout)
    assert data["demo_id"] == "AW-DEMO-FINAL-04"
    assert data["outputs"]["summary_json"] == "aw-demo-final-04-summary.json"
    assert data["outputs"]["preview_html"] == "aw-demo-final-04-preview.html"
    assert data["portfolio_metrics"]["screenshot_backed_package_count"] == 0
    assert data["portfolio_metrics"]["interaction_backed_package_count"] == 0
    assert data["portfolio_metrics"]["local_preview_status"] == "blocked"
    _assert_no_setup_command_path(data["portfolio_metrics"])
    assert data["portfolio_metrics"]["server_start_count"] == 0
    assert data["portfolio_metrics"]["provider_call_count"] == 0
    assert data["portfolio_metrics"]["daacs_target_runtime_call_count"] == 0
    assert str(tmp_path) not in stdout
    assert_public_projection_safe(data)


def test_portfolio_demo_can_include_opt_in_local_build_attempt(tmp_path):
    module = _load_portfolio_demo_module()

    report = module.run_portfolio_demo(
        output_dir=tmp_path / "portfolio-build-output",
        allow_local_build_attempt=True,
    )

    metrics = report["portfolio_metrics"]
    assert report["status"] == "passed"
    assert metrics["local_build_opt_in_present"] == 1
    assert metrics["screenshot_backed_package_count"] == 0
    assert metrics["local_build_attempt_status"] == "passed"
    assert metrics["local_build_command_result_count"] == 2
    assert metrics["local_build_package_install_attempts"] == 1
    assert metrics["local_build_build_attempts"] == 1
    assert metrics["local_preview_status"] == "blocked"
    _assert_no_setup_command_path(metrics)
    assert metrics["server_start_count"] == 0
    assert metrics["provider_call_count"] == 0
    assert metrics["daacs_target_runtime_call_count"] == 0
    assert metrics["raw_public_body_exposure_count"] == 0
    assert metrics["local_root_path_exposure_count"] == 0
    assert_public_projection_safe(report)


def test_portfolio_report_records_screenshot_evidence_from_public_summary():
    module = _load_portfolio_demo_module()
    summary = {
        "demo_id": "AW-MVP-01",
        "status": "passed",
        "run_id": "portfolio-screenshot-run",
        "workflow_stage_coverage": {
            "covered_stage_count": 7,
            "required_stage_count": 7,
            "coverage_percent": 100.0,
        },
        "daacs_runtime_restricted_workspace_generation": {
            "counts": {"generated_workspace_file_record_count": 9},
        },
        "daacs_runtime_local_build_attempt": {
            "status": "passed",
            "reason": "local_fixture_app_build_passed",
            "counts": {
                "command_result_count": 2,
                "package_install_attempt_count": 1,
                "build_attempt_count": 1,
                "raw_output_public_return_count": 0,
                "file_content_public_return_count": 0,
                "local_root_path_return_count": 0,
            },
            "execution_boundary": {
                "server_start_call_count": 0,
                "provider_call_count": 0,
                "target_runtime_call_count": 0,
            },
        },
        "daacs_runtime_local_preview_attempt": {
            "status": "passed",
            "reason": "local_fixture_app_preview_verified",
            "browser_runtime_preflight": {"available": True},
            "counts": {
                "browser_runtime_preflight_count": 1,
                "browser_runtime_available_count": 1,
                "preview_server_start_attempt_count": 1,
                "server_start_count": 1,
                "preview_server_stop_count": 1,
                "screenshot_evidence_count": 1,
                "screenshot_hash_count": 1,
                "screenshot_byte_count": 4096,
                "owner_filter_click_attempt_count": 1,
                "owner_filter_click_pass_count": 1,
                "owner_filter_click_target_label_hash_count": 1,
                "owner_filter_before_task_count": 3,
                "owner_filter_after_task_count": 1,
                "owner_filter_changed_count": 2,
                "reviewer_decision_click_attempt_count": 1,
                "reviewer_decision_click_pass_count": 1,
                "reviewer_decision_click_target_label_hash_count": 1,
                "reviewer_decision_state_hash_count": 2,
                "reviewer_decision_state_changed_count": 1,
                "raw_output_public_return_count": 0,
                "local_root_path_return_count": 0,
                "screenshot_path_return_count": 0,
                "page_text_return_count": 0,
            },
            "preview_record": {
                "owner_filter_click_status": "passed",
                "reviewer_decision_click_status": "passed",
            },
            "execution_boundary": {
                "server_start_calls": 1,
                "provider_calls": 0,
                "target_runtime_calls": 0,
            },
        },
        "daacs_runtime_browser_setup_attempt": {
            "status": "passed",
            "reason": "browser_runtime_already_available",
            "post_setup_browser_runtime_preflight": {"available": True},
            "counts": {
                "browser_runtime_preflight_count": 1,
                "browser_runtime_available_before_setup_count": 1,
                "setup_command_attempt_count": 0,
                "default_setup_command_execution_count": 0,
                "browser_runtime_available_after_setup_count": 1,
                "raw_output_public_return_count": 0,
                "argv_public_return_count": 0,
                "browser_error_public_return_count": 0,
                "local_root_path_return_count": 0,
            },
            "execution_boundary": {
                "provider_calls": 0,
                "daacs_target_runtime_calls": 0,
            },
        },
        "daacs_runtime_comparison": {
            "public_claim_drift_findings": 0,
            "local_preview_retry_after_browser_setup_count": 0,
        },
    }

    report = module.build_portfolio_demo_report(
        summary,
        local_build_opt_in=True,
        local_preview_opt_in=True,
        browser_runtime_setup_opt_in=False,
        screenshot_backed_opt_in=True,
    )

    metrics = report["portfolio_metrics"]
    assert report["demo_id"] == "AW-DEMO-FINAL-04"
    assert metrics["screenshot_backed_package_count"] == 1
    assert metrics["screenshot_capture_status"] == "verified"
    assert metrics["screenshot_capture_reason"] == "screenshot_hash_recorded"
    assert metrics["screenshot_capture_ready_count"] == 1
    assert metrics["screenshot_capture_blocked_count"] == 0
    assert metrics["preview_server_start_attempt_count"] == 1
    assert metrics["preview_server_started_count"] == 1
    assert metrics["preview_server_cleanup_percent"] == 100.0
    assert metrics["screenshot_evidence_count"] == 1
    assert metrics["screenshot_hash_count"] == 1
    assert metrics["screenshot_byte_count"] == 4096
    assert metrics["owner_filter_click_status"] == "passed"
    assert metrics["owner_filter_click_attempt_count"] == 1
    assert metrics["owner_filter_click_pass_count"] == 1
    assert metrics["owner_filter_click_target_label_hash_count"] == 1
    assert metrics["owner_filter_before_task_count"] == 3
    assert metrics["owner_filter_after_task_count"] == 1
    assert metrics["owner_filter_changed_count"] == 2
    assert metrics["owner_filter_e2e_verified_count"] == 1
    assert metrics["reviewer_decision_click_status"] == "passed"
    assert metrics["reviewer_decision_click_attempt_count"] == 1
    assert metrics["reviewer_decision_click_pass_count"] == 1
    assert metrics["reviewer_decision_click_target_label_hash_count"] == 1
    assert metrics["reviewer_decision_state_hash_count"] == 2
    assert metrics["reviewer_decision_state_changed_count"] == 1
    assert metrics["reviewer_decision_e2e_verified_count"] == 1
    assert metrics["interaction_backed_package_count"] == 1
    assert metrics["interaction_path_count"] == 2
    assert metrics["interaction_verified_path_count"] == 2
    assert metrics["interaction_hash_evidence_count"] == 4
    assert metrics["interaction_package_hash_count"] == 1
    assert metrics["interaction_dom_text_exposure_count"] == 0
    assert metrics["interaction_event_exposure_count"] == 0
    interaction_package = report["interaction_evidence_package"]
    assert interaction_package["status"] == "verified"
    assert interaction_package["reason"] == (
        "screenshot_owner_reviewer_evidence_packaged"
    )
    assert interaction_package["verified_interaction_path_count"] == 2
    assert interaction_package["interaction_hash_evidence_count"] == 4
    assert interaction_package["paths"][0]["name"] == "owner_filter"
    assert interaction_package["paths"][0]["click_pass_count"] == 1
    assert interaction_package["paths"][1]["name"] == "reviewer_decision"
    assert interaction_package["paths"][1]["state_hash_count"] == 2
    assert interaction_package["exposure_counts"]["dom_text_return_count"] == 0
    assert interaction_package["exposure_counts"]["page_text_return_count"] == 0
    assert metrics["screenshot_path_exposure_count"] == 0
    assert metrics["page_text_exposure_count"] == 0
    assert metrics["provider_call_count"] == 0
    assert metrics["daacs_target_runtime_call_count"] == 0
    assert_public_projection_safe(report)

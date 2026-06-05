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
        "aw_demo_final_01_portfolio_demo", PORTFOLIO_DEMO_SCRIPT
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_portfolio_demo_writes_summary_and_preview_without_local_root(tmp_path):
    module = _load_portfolio_demo_module()
    output_dir = tmp_path / "portfolio-output"

    report = module.run_portfolio_demo(output_dir=output_dir)

    summary_path = output_dir / "aw-demo-final-01-summary.json"
    preview_path = output_dir / "aw-demo-final-01-preview.html"
    assert summary_path.exists()
    assert preview_path.exists()
    assert report["demo_id"] == "AW-DEMO-FINAL-01"
    assert report["status"] == "passed"
    assert report["outputs"] == {
        "summary_json": "aw-demo-final-01-summary.json",
        "preview_html": "aw-demo-final-01-preview.html",
    }
    assert report["stage_coverage"]["covered"] == 7
    assert report["stage_coverage"]["required"] == 7
    metrics = report["portfolio_metrics"]
    assert metrics["portfolio_command_count"] == 1
    assert metrics["preview_html_generated"] == 1
    assert metrics["generated_fixture_app_file_count"] == 9
    assert metrics["local_build_attempt_evidence_count"] == 1
    assert metrics["local_build_opt_in_present"] == 0
    assert metrics["local_build_attempt_status"] == "blocked"
    assert metrics["local_build_package_install_attempts"] == 0
    assert metrics["local_build_build_attempts"] == 0
    assert metrics["server_start_count"] == 0
    assert metrics["provider_call_count"] == 0
    assert metrics["daacs_target_runtime_call_count"] == 0
    assert metrics["raw_public_body_exposure_count"] == 0
    assert metrics["local_root_path_exposure_count"] == 0
    assert_public_projection_safe(report)

    summary_text = summary_path.read_text(encoding="utf-8")
    html = preview_path.read_text(encoding="utf-8")
    assert "Agentic Workbench Artifact Preview" in html
    assert "local build: not attempted" in html
    assert "AW-DEMO-FINAL-01" in summary_text
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
    assert data["demo_id"] == "AW-DEMO-FINAL-01"
    assert data["outputs"]["summary_json"] == "aw-demo-final-01-summary.json"
    assert data["outputs"]["preview_html"] == "aw-demo-final-01-preview.html"
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
    assert metrics["local_build_attempt_status"] == "passed"
    assert metrics["local_build_command_result_count"] == 2
    assert metrics["local_build_package_install_attempts"] == 1
    assert metrics["local_build_build_attempts"] == 1
    assert metrics["server_start_count"] == 0
    assert metrics["provider_call_count"] == 0
    assert metrics["daacs_target_runtime_call_count"] == 0
    assert metrics["raw_public_body_exposure_count"] == 0
    assert metrics["local_root_path_exposure_count"] == 0
    assert_public_projection_safe(report)

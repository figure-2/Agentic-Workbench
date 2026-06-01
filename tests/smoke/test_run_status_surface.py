import importlib.util
from pathlib import Path


SURFACE_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "demo-service-flow"
    / "render_status_surface.py"
)


def _load_surface_module():
    spec = importlib.util.spec_from_file_location("aw_demo_02_run_status_surface", SURFACE_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_status_surface_renders_human_readable_boundary_summary(tmp_path):
    module = _load_surface_module()
    summary = module.run_demo(tmp_path / "surface-store")

    report = module.render_status_surface(summary)

    assert "Agentic Workbench Run Status" in report
    assert "## Run" in report
    assert "## Artifact Chain" in report
    assert "## DIV Identity Signals" in report
    assert "## DAACS Identity Signals" in report
    assert "## Evidence Summary" in report
    assert "## Execution Boundary" in report
    assert "## Claim Boundary" in report
    assert "## Next Action" in report
    assert "Surface: `AW-DEMO-02`" in report
    assert "Source demo: `AW-DEMO-01`" in report
    assert f"Run ID: `{summary['run_id']}`" in report
    assert "Artifact count: `6`" in report
    assert "Solar Pro 3 calls: `0`" in report
    assert "Target runtime calls: `0`" in report
    assert "External provider outcome: `False`" in report
    assert "Target runtime outcome: `False`" in report
    assert "`planning_blueprint`" in report
    assert "`prd_package`" in report
    assert "`build_spec`" in report
    assert "`implementation_brief`" in report

    for forbidden in (
        "raw_prompt",
        "Build a small task collaboration app",
        "provider_payload",
        "runtime_payload",
        "file_body",
        "signature_id",
        "signed_contract_hash",
        str(tmp_path),
    ):
        assert forbidden not in report


def test_run_status_surface_cli_main_outputs_markdown(tmp_path, capsys):
    module = _load_surface_module()

    old_argv = module.sys.argv
    try:
        module.sys.argv = [
            "render_status_surface.py",
            "--store-root",
            str(tmp_path / "cli-store"),
        ]
        module.main()
    finally:
        module.sys.argv = old_argv

    output = capsys.readouterr().out
    assert "Agentic Workbench Run Status" in output
    assert "Solar Pro 3 calls: `0`" in output
    assert "Target runtime calls: `0`" in output
    assert str(tmp_path) not in output

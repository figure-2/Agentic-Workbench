import importlib.util
from pathlib import Path

from packages.core.public_projection import assert_public_projection_safe


STATIC_UI_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "demo-service-flow"
    / "render_static_ui_shell.py"
)


def _load_static_ui_module():
    spec = importlib.util.spec_from_file_location("aw_demo_03_static_ui_shell", STATIC_UI_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_static_ui_shell_renders_public_projection_only(tmp_path):
    module = _load_static_ui_module()
    summary = module.run_demo(tmp_path / "static-ui-store")

    html = module.render_static_ui_shell(summary)

    assert html.startswith("<!doctype html>")
    assert "Agentic Workbench Static Demo Shell" in html
    assert "data-projection=\"public-summary-only\"" in html
    assert "data-live-policy=\"closed / eligible only\"" in html
    assert "AW-DEMO-03 static UI shell" in html
    assert "DIV Identity" in html
    assert "DAACS Identity" in html
    assert "Solar Pro 3 calls</span><strong>0</strong>" in html
    assert "DAACS target runtime calls</span><strong>0</strong>" in html
    assert "Allowed to execute</span><strong>False</strong>" in html
    assert "Env value loaded</span><strong>False</strong>" in html
    assert "eligible_for_separate_live_implementation" in html
    assert "planning_blueprint" in html
    assert "implementation_brief" in html
    assert_public_projection_safe({"html": html})

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
        assert forbidden not in html


def test_static_ui_shell_cli_can_write_html_without_echoing_store_path(tmp_path, capsys):
    module = _load_static_ui_module()
    output = tmp_path / "aw-demo-03-static-ui.html"

    old_argv = module.sys.argv
    try:
        module.sys.argv = [
            "render_static_ui_shell.py",
            "--store-root",
            str(tmp_path / "cli-store"),
            "--output",
            str(output),
        ]
        module.main()
    finally:
        module.sys.argv = old_argv

    stdout = capsys.readouterr().out
    html = output.read_text(encoding="utf-8")
    assert "Wrote aw-demo-03-static-ui.html" in stdout
    assert str(tmp_path) not in stdout
    assert "Agentic Workbench Static Demo Shell" in html
    assert str(tmp_path) not in html
    assert "Solar Pro 3 calls</span><strong>0</strong>" in html
    assert "DAACS target runtime calls</span><strong>0</strong>" in html

import importlib.util
from pathlib import Path

from packages.core.public_projection import assert_public_projection_safe


ARTIFACT_PREVIEW_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "demo-service-flow"
    / "render_artifact_preview.py"
)


def _load_artifact_preview_module():
    spec = importlib.util.spec_from_file_location(
        "aw_app_01_artifact_preview", ARTIFACT_PREVIEW_SCRIPT
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_artifact_preview_renders_public_summary_only(tmp_path):
    module = _load_artifact_preview_module()
    summary = module.run_demo(
        tmp_path / "artifact-preview-store",
        include_daacs_runtime_fixture_materialization=True,
    )

    html = module.render_artifact_preview(summary)

    assert html.startswith("<!doctype html>")
    assert "Agentic Workbench Artifact Preview" in html
    assert "data-surface=\"AW-APP-01\"" in html
    assert "data-projection=\"public-summary-only\"" in html
    assert "Stage coverage</span><strong>7/7</strong>" in html
    assert "Artifact count</span><strong>6</strong>" in html
    assert "Preview cards</span><strong>3</strong>" in html
    assert "Fixture status</span><strong>passed</strong>" in html
    assert html.count('class="artifact-card"') == 3
    assert "backend" in html
    assert "frontend" in html
    assert "verification report" in html
    assert "prd package" in html
    assert "implementation brief" in html
    assert "runner plan" in html
    assert "DAACS target runtime</span><strong>0</strong>" in html
    assert "Provider calls</span><strong>0</strong>" in html
    assert "Network calls</span><strong>0</strong>" in html
    assert "Subprocess calls</span><strong>0</strong>" in html
    assert "Artifact content returned</span><strong>False</strong>" in html
    assert "Root path returned</span><strong>False</strong>" in html
    assert_public_projection_safe({"html": html})

    for forbidden in (
        "raw_prompt",
        "raw_log",
        "raw_file_body",
        "Build a small task collaboration app",
        "provider_payload",
        "runtime_payload",
        "file_body",
        "signature_id",
        "signed_contract_hash",
        str(tmp_path),
    ):
        assert forbidden not in html


def test_artifact_preview_cli_can_write_html_without_echoing_store_path(
    tmp_path, capsys
):
    module = _load_artifact_preview_module()
    output = tmp_path / "aw-app-01-preview.html"

    old_argv = module.sys.argv
    try:
        module.sys.argv = [
            "render_artifact_preview.py",
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
    assert "Wrote aw-app-01-preview.html" in stdout
    assert str(tmp_path) not in stdout
    assert "Agentic Workbench Artifact Preview" in html
    assert str(tmp_path) not in html
    assert html.count('class="artifact-card"') == 12
    assert "Artifact count</span><strong>6</strong>" in html
    assert "Generated files</span><strong>9</strong>" in html
    assert "Generated Workspace Files" in html
    assert "Generated Artifact Verification" in html
    assert "Generated Workspace Static Validation" in html
    assert "Build-Ready Candidate Manifest" in html
    assert "Local Build Preflight" in html
    assert "Local Build Attempt" in html
    assert "Interaction-Backed Portfolio Evidence" in html
    assert "verified files: 9" in html
    assert "static checks: passed" in html
    assert "build-ready candidate: ready" in html
    assert "local build preflight: eligible" in html
    assert "local build: not attempted" in html
    assert "Screenshot status</span><strong>skipped</strong>" in html
    assert "Capture status</span><strong>skipped</strong>" in html
    assert "Server cleanup</span><strong>0.0%</strong>" in html
    assert "Expected files</span><strong>9</strong>" in html
    assert "Checked files</span><strong>9</strong>" in html
    assert "Hash matches</span><strong>9</strong>" in html
    assert "Byte matches</span><strong>9</strong>" in html
    assert "Files checked</span><strong>9</strong>" in html
    assert "Package JSON</span><strong>1</strong>" in html
    assert "Script labels</span><strong>4/4</strong>" in html
    assert "App markers</span><strong>13/13</strong>" in html
    assert "API markers</span><strong>8/8</strong>" in html
    assert "Verification boundary markers</span><strong>4/4</strong>" in html
    assert "Zero-call markers</span><strong>5/5</strong>" in html
    assert "Candidate</span><strong>ready</strong>" in html
    assert "Files read</span><strong>5</strong>" in html
    assert "Dependency labels</span><strong>7</strong>" in html
    assert "Placeholder values</span><strong>0</strong>" in html
    assert "Index markers</span><strong>2/2</strong>" in html
    assert "Main markers</span><strong>2/2</strong>" in html
    assert "Vite config</span><strong>2/2</strong>" in html
    assert "TS config</span><strong>2/2</strong>" in html
    assert "Verification file reads</span><strong>9</strong>" in html
    assert "Static file reads</span><strong>9</strong>" in html
    assert "Build-ready file reads</span><strong>5</strong>" in html
    assert "Eligible</span><strong>True</strong>" in html
    assert "Opt-in required</span><strong>True</strong>" in html
    assert "Operator opt-in</span><strong>False</strong>" in html
    assert "Command labels</span><strong>4</strong>" in html
    assert "Command hashes</span><strong>4</strong>" in html
    assert "Execution permission</span><strong>0</strong>" in html
    assert "Dependency values returned</span><strong>0</strong>" in html
    assert (
        "Planned labels: npm install, npm run verify, npm run build, npm run preview"
        in html
    )
    assert "package json" in html
    assert "index html" in html
    assert "main entrypoint" in html
    assert "app component" in html
    assert "api client" in html
    assert "vite config" in html
    assert "tsconfig json" in html
    assert "DAACS target runtime</span><strong>0</strong>" in html
    assert "Provider calls</span><strong>0</strong>" in html
    assert "Package installs</span><strong>0</strong>" in html
    assert "Builds</span><strong>0</strong>" in html
    assert "Server starts</span><strong>0</strong>" in html
    assert "Static package installs</span><strong>0</strong>" in html
    assert "Static builds</span><strong>0</strong>" in html
    assert "Static server starts</span><strong>0</strong>" in html
    assert "Build-ready package installs</span><strong>0</strong>" in html
    assert "Build-ready builds</span><strong>0</strong>" in html
    assert "Build-ready server starts</span><strong>0</strong>" in html
    assert "Local preflight package installs</span><strong>0</strong>" in html
    assert "Local preflight builds</span><strong>0</strong>" in html
    assert "Local preflight server starts</span><strong>0</strong>" in html
    assert "Local preflight execution permission</span><strong>0</strong>" in html
    assert "Local build package installs</span><strong>0</strong>" in html
    assert "Local build builds</span><strong>0</strong>" in html
    assert "Local build server starts</span><strong>0</strong>" in html


def test_artifact_preview_can_render_local_build_attempt_result(tmp_path):
    module = _load_artifact_preview_module()
    summary = module.run_demo(
        tmp_path / "artifact-preview-build-attempt-store",
        include_daacs_runtime_local_build_attempt=True,
        allow_local_build_attempt=True,
    )

    html = module.render_artifact_preview(summary)

    assert summary["status"] == "passed"
    assert "Local Build Attempt" in html
    assert "local build: attempted" in html
    assert "Status</span><strong>passed</strong>" in html
    assert "Reason</span><strong>local_fixture_app_build_passed</strong>" in html
    assert "Attempted</span><strong>True</strong>" in html
    assert "Opt-in</span><strong>True</strong>" in html
    assert "Command execution</span><strong>True</strong>" in html
    assert "Command results</span><strong>2</strong>" in html
    assert "Output hashes</span><strong>2</strong>" in html
    assert "Package installs</span><strong>1</strong>" in html
    assert "Build attempts</span><strong>1</strong>" in html
    assert "Server starts</span><strong>0</strong>" in html
    assert "Raw output returned</span><strong>0</strong>" in html
    assert "npm install" in html
    assert "npm run build" in html
    assert "Local build package installs</span><strong>1</strong>" in html
    assert "Local build builds</span><strong>1</strong>" in html
    assert "Local build server starts</span><strong>0</strong>" in html
    assert "Local build target runtime</span><strong>0</strong>" in html
    assert "Local build provider calls</span><strong>0</strong>" in html
    assert str(tmp_path) not in html
    assert "Build a small task collaboration app" not in html
    assert "raw_file_body" not in html
    assert "provider_payload" not in html
    assert_public_projection_safe({"html": html})

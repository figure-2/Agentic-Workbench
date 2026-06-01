"""Render the AW-DEMO-03 static HTML shell from the public demo summary."""

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

from packages.core.live_open_policy import (
    DAACS_TARGET_RUNTIME_SURFACE,
    LIVE_OPEN_REQUIRED_CONTROLS,
    SOLAR_PRO_3_ENV_KEY_NAME,
    SOLAR_PROVIDER_SURFACE,
    LiveOpenRequest,
    evaluate_live_open_request,
)
from packages.core.public_projection import assert_public_projection_safe
from run_local_demo import run_demo


STATIC_UI_TITLE = "Agentic Workbench Static Demo Shell"


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


def _ready_controls() -> dict[str, bool]:
    return {field_name: True for field_name in LIVE_OPEN_REQUIRED_CONTROLS}


def _live_policy_projection(run_id: str) -> dict[str, Any]:
    controls = _ready_controls()
    solar = evaluate_live_open_request(
        LiveOpenRequest(
            run_id=run_id,
            surface=SOLAR_PROVIDER_SURFACE,
            env_key_name=SOLAR_PRO_3_ENV_KEY_NAME,
            **controls,
        )
    ).to_dict()
    daacs = evaluate_live_open_request(
        LiveOpenRequest(
            run_id=run_id,
            surface=DAACS_TARGET_RUNTIME_SURFACE,
            **controls,
        )
    ).to_dict()
    return {
        "display_state": "closed / eligible only",
        "solar_status": solar["status"],
        "daacs_status": daacs["status"],
        "allowed_to_execute": False,
        "solar_provider_calls": solar["execution_boundary"]["solar_provider_calls"],
        "target_runtime_calls": daacs["execution_boundary"]["target_runtime_calls"],
        "env_key_value_loaded": solar["execution_boundary"]["env_key_value_loaded"],
    }


def build_static_ui_model(summary: dict[str, Any]) -> dict[str, Any]:
    """Build the UI view model from the sanitized public summary only."""
    assert_public_projection_safe(summary)
    run_id = _text(summary.get("run_id"), "run-unknown")
    model = {
        "surface": "AW-DEMO-03",
        "source_demo": summary.get("demo_id", "unknown"),
        "status": summary.get("status", "unknown"),
        "run_id": run_id,
        "projection_version": summary.get("projection_version", "unknown"),
        "runtime_mode": summary.get("runtime_mode", "unknown"),
        "fixture_mode": bool(summary.get("fixture_mode")),
        "artifact_count": _count(summary.get("artifact_count")),
        "artifact_kinds": list(summary.get("artifact_kinds", [])),
        "identity_signals": summary.get("identity_signals", {}),
        "evidence_summary": summary.get("evidence_summary", {}),
        "execution_boundary": summary.get("execution_boundary", {}),
        "claim_boundary": summary.get("claim_boundary", {}),
        "checks": summary.get("checks", {}),
        "live_open_policy": _live_policy_projection(run_id),
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


def _signal_rows(signals: dict[str, Any]) -> str:
    rows = []
    for key, value in sorted(signals.items()):
        state = "on" if bool(value) else "off"
        label = "yes" if bool(value) else "no"
        rows.append(
            '<li class="signal-row">'
            f"<span>{escape(str(key).replace('_', ' '))}</span>"
            f'<b class="{state}">{label}</b>'
            "</li>"
        )
    return "\n".join(rows) if rows else '<li class="signal-row"><span>none</span><b>0</b></li>'


def _artifact_rows(artifact_kinds: list[str]) -> str:
    if not artifact_kinds:
        return '<li><span class="dot"></span><span>none</span></li>'
    return "\n".join(
        f'<li><span class="dot"></span><span>{escape(kind)}</span></li>'
        for kind in artifact_kinds
    )


def _check_summary(checks: dict[str, Any]) -> tuple[int, str]:
    failed = [name for name, passed in sorted(checks.items()) if not passed]
    return len(failed), ", ".join(failed) if failed else "none"


def render_static_ui_shell(summary: dict[str, Any]) -> str:
    """Return a complete static HTML shell from the public demo summary."""
    model = build_static_ui_model(summary)
    evidence = model["evidence_summary"]
    evidence_counts = evidence.get("counts", {})
    execution = model["execution_boundary"]
    claim = model["claim_boundary"]
    policy = model["live_open_policy"]
    div_signals = model["identity_signals"].get("div", {})
    daacs_signals = model["identity_signals"].get("daacs", {})
    failed_count, failed_names = _check_summary(model["checks"])

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(STATIC_UI_TITLE)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #18212f;
      --muted: #657287;
      --line: #d8dee8;
      --bg: #f7f8fb;
      --panel: #ffffff;
      --teal: #127f76;
      --blue: #2f5f9f;
      --amber: #b26c14;
      --rose: #b3374a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--bg);
      letter-spacing: 0;
    }}
    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      min-height: 72px;
      padding: 18px clamp(18px, 4vw, 44px);
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }}
    .brand strong {{ display: block; font-size: 20px; line-height: 1.15; }}
    .brand span {{ display: block; color: var(--muted); font-size: 13px; margin-top: 3px; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fdfefe;
      color: var(--ink);
      font-size: 13px;
      white-space: nowrap;
    }}
    .badge.good {{ border-color: #9ccfc8; color: var(--teal); }}
    .badge.warn {{ border-color: #e5c28c; color: var(--amber); }}
    .workspace {{
      width: min(1180px, 100%);
      margin: 0 auto;
      padding: 28px clamp(18px, 4vw, 44px) 44px;
    }}
    .overview {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 22px;
    }}
    .metric {{
      min-height: 86px;
      padding: 15px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .metric strong {{ display: block; margin-top: 10px; font-size: 22px; line-height: 1.1; overflow-wrap: anywhere; }}
    .section {{
      margin-top: 16px;
      padding: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .section h2 {{ margin: 0 0 14px; font-size: 17px; }}
    .flow {{
      display: grid;
      grid-template-columns: repeat(6, minmax(108px, 1fr));
      gap: 8px;
      padding: 0;
      margin: 0;
      list-style: none;
    }}
    .flow li {{
      min-height: 64px;
      padding: 12px;
      border-left: 4px solid var(--blue);
      background: #f6f9fd;
      border-radius: 6px;
      font-weight: 650;
      font-size: 13px;
    }}
    .split {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .signal-list, .artifact-list {{
      list-style: none;
      margin: 0;
      padding: 0;
    }}
    .signal-row, .artifact-list li {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      min-height: 34px;
      border-bottom: 1px solid #eef2f6;
      font-size: 14px;
    }}
    .signal-row:last-child, .artifact-list li:last-child {{ border-bottom: 0; }}
    .signal-row b {{ font-size: 12px; text-transform: uppercase; }}
    .signal-row b.on {{ color: var(--teal); }}
    .signal-row b.off {{ color: var(--rose); }}
    .dot {{
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--teal);
      flex: 0 0 auto;
      margin-right: 8px;
    }}
    .artifact-list li {{ justify-content: flex-start; }}
    .grid-two {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      margin-top: 16px;
    }}
    .boundary {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
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
    .policy {{
      border-color: #b9d8d4;
      background: #f5fbfa;
    }}
    .footer {{
      margin-top: 20px;
      color: var(--muted);
      font-size: 12px;
    }}
    @media (max-width: 840px) {{
      .topbar {{ align-items: flex-start; flex-direction: column; }}
      .badges {{ justify-content: flex-start; }}
      .overview, .split, .grid-two, .boundary {{ grid-template-columns: 1fr; }}
      .flow {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
  </style>
</head>
<body data-projection="public-summary-only" data-live-policy="{escape(policy['display_state'])}">
  <header class="topbar">
    <div class="brand">
      <strong>Agentic Workbench</strong>
      <span>{escape(model['surface'])} static UI shell</span>
    </div>
    <div class="badges">
      <span class="badge good">status: {escape(_text(model['status']))}</span>
      <span class="badge">runtime: {escape(_text(model['runtime_mode']))}</span>
      <span class="badge warn">live policy: {escape(policy['display_state'])}</span>
    </div>
  </header>
  <main class="workspace">
    <section class="overview" aria-label="Run overview">
      {_metric("Run ID", model["run_id"])}
      {_metric("Artifacts", model["artifact_count"])}
      {_metric("Failed checks", failed_count)}
      {_metric("Execution permission", "closed")}
    </section>

    <section class="section">
      <h2>Workflow</h2>
      <ol class="flow">
        <li>Idea</li>
        <li>Planning</li>
        <li>PRD / BuildSpec</li>
        <li>ImplementationBrief</li>
        <li>Dry-run Plan</li>
        <li>Verification</li>
      </ol>
    </section>

    <section class="grid-two">
      <div class="section">
        <h2>DIV Identity</h2>
        <ul class="signal-list">{_signal_rows(div_signals)}</ul>
      </div>
      <div class="section">
        <h2>DAACS Identity</h2>
        <ul class="signal-list">{_signal_rows(daacs_signals)}</ul>
      </div>
    </section>

    <section class="grid-two">
      <div class="section">
        <h2>Artifacts</h2>
        <ul class="artifact-list">{_artifact_rows(model["artifact_kinds"])}</ul>
      </div>
      <div class="section">
        <h2>Evidence</h2>
        <div class="boundary">
          <div><span>Status</span><strong>{escape(_text(evidence.get("status")))}</strong></div>
          <div><span>Runner plans</span><strong>{_count(evidence_counts.get("runner_plan_count"))}</strong></div>
          <div><span>Reports</span><strong>{_count(evidence_counts.get("verification_report_count"))}</strong></div>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>Execution Boundary</h2>
      <div class="boundary">
        <div><span>Solar Pro 3 calls</span><strong>{_count(execution.get("solar_provider_calls"))}</strong></div>
        <div><span>Provider calls</span><strong>{_count(execution.get("provider_calls"))}</strong></div>
        <div><span>DAACS target runtime calls</span><strong>{_count(execution.get("target_runtime_calls"))}</strong></div>
        <div><span>Network calls</span><strong>{_count(execution.get("network_calls"))}</strong></div>
        <div><span>Subprocess calls</span><strong>{_count(execution.get("subprocess_calls"))}</strong></div>
        <div><span>External outcome</span><strong>{escape(_text(claim.get("external_provider_outcome")))}</strong></div>
      </div>
    </section>

    <section class="section policy">
      <h2>Live-Open Policy</h2>
      <div class="boundary">
        <div><span>Display state</span><strong>{escape(policy["display_state"])}</strong></div>
        <div><span>Solar policy</span><strong>{escape(policy["solar_status"])}</strong></div>
        <div><span>DAACS policy</span><strong>{escape(policy["daacs_status"])}</strong></div>
        <div><span>Allowed to execute</span><strong>{escape(_text(policy["allowed_to_execute"]))}</strong></div>
        <div><span>Env value loaded</span><strong>{escape(_text(policy["env_key_value_loaded"]))}</strong></div>
        <div><span>Failed checks</span><strong>{escape(failed_names)}</strong></div>
      </div>
    </section>

    <p class="footer">Projection: {escape(_text(model["projection_version"]))}. Source: {escape(_text(model["source_demo"]))}. This shell renders sanitized local summary fields only.</p>
  </main>
</body>
</html>
"""
    assert_public_projection_safe({"static_ui_shell": html})
    return html


def write_static_ui_shell(summary: dict[str, Any], output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    html = render_static_ui_shell(summary)
    output.write_text(html, encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the AW-DEMO-03 static UI shell.")
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
    args = parser.parse_args()

    summary = run_demo(args.store_root)
    if args.output:
        output = write_static_ui_shell(summary, args.output)
        print(f"Wrote {output.name}")
        return
    print(render_static_ui_shell(summary))


if __name__ == "__main__":
    main()

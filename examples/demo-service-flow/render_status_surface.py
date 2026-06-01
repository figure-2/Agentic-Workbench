"""Render a human-readable AW-DEMO-02 run status surface."""

from __future__ import annotations

import argparse
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


STATUS_SURFACE_TITLE = "Agentic Workbench Run Status"


def _yes_no(value: object) -> str:
    return "yes" if bool(value) else "no"


def _count(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _artifact_line(artifact_kinds: list[str]) -> str:
    if not artifact_kinds:
        return "- none"
    return "\n".join(f"- `{kind}`" for kind in artifact_kinds)


def _identity_lines(signals: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for key in sorted(signals):
        rows.append(f"- `{key}`: {_yes_no(signals[key])}")
    return rows or ["- none"]


def render_status_surface(summary: dict[str, Any]) -> str:
    """Return a Markdown report from the sanitized demo summary."""
    assert_public_projection_safe(summary)
    div_signals = summary.get("identity_signals", {}).get("div", {})
    daacs_signals = summary.get("identity_signals", {}).get("daacs", {})
    counts = summary.get("counts", {})
    evidence = summary.get("evidence_summary", {})
    evidence_counts = evidence.get("counts", {})
    execution = summary.get("execution_boundary", {})
    claim = summary.get("claim_boundary", {})
    repository = summary.get("repository_boundary", {})
    all_checks = summary.get("checks", {})
    failed_checks = [name for name, passed in sorted(all_checks.items()) if not passed]
    next_action = (
        "Review the local run status, then proceed to AW-DEMO-03 UI shell or "
        "AW-LIVE-00 live-open policy. Do not open live execution from this demo."
    )

    report = f"""# {STATUS_SURFACE_TITLE}

## Run

- Surface: `AW-DEMO-02`
- Source demo: `{summary.get("demo_id", "unknown")}`
- Status: `{summary.get("status", "unknown")}`
- Run ID: `{summary.get("run_id", "unknown")}`
- Projection: `{summary.get("projection_version", "unknown")}`
- Runtime mode: `{summary.get("runtime_mode", "unknown")}`
- Fixture mode: `{summary.get("fixture_mode", "unknown")}`

## Artifact Chain

- Artifact count: `{_count(summary.get("artifact_count"))}`
{_artifact_line(list(summary.get("artifact_kinds", [])))}

## DIV Identity Signals

{chr(10).join(_identity_lines(div_signals))}

## DAACS Identity Signals

{chr(10).join(_identity_lines(daacs_signals))}

## Evidence Summary

- Evidence status: `{evidence.get("status", "unknown")}`
- Source artifact count: `{_count(evidence_counts.get("source_artifact_count"))}`
- Runner plan count: `{_count(evidence_counts.get("runner_plan_count"))}`
- Verification report count: `{_count(evidence_counts.get("verification_report_count"))}`
- Audit event count: `{_count(evidence_counts.get("audit_event_count"))}`
- Approval count: `{_count(evidence_counts.get("approval_count"))}`
- Replay nonce count: `{_count(evidence_counts.get("replay_nonce_count"))}`

## Repository Boundary

- Canonical run/artifact backend: `{repository.get("canonical_run_artifact_backend", "unknown")}`
- Runner/report/audit backend: `{repository.get("runner_report_audit_backend", "unknown")}`
- Approval/replay backend: `{repository.get("approval_replay_backend", "unknown")}`
- Raw rows returned: `{repository.get("raw_row_returned", "unknown")}`
- Root path returned: `{repository.get("root_path_returned", "unknown")}`

## Execution Boundary

- Solar Pro 3 calls: `{_count(execution.get("solar_provider_calls"))}`
- Provider calls: `{_count(execution.get("provider_calls"))}`
- Target runtime calls: `{_count(execution.get("target_runtime_calls"))}`
- Network calls: `{_count(execution.get("network_calls"))}`
- Subprocess calls: `{_count(execution.get("subprocess_calls"))}`

## Claim Boundary

- Local read model only: `{claim.get("local_read_model_only", "unknown")}`
- External provider outcome: `{claim.get("external_provider_outcome", "unknown")}`
- Target runtime outcome: `{claim.get("target_runtime_outcome", "unknown")}`
- Production trust claim: `{claim.get("production_trust_claim", "unknown")}`

## Checks

- Failed checks: `{len(failed_checks)}`
- Failed check names: `{", ".join(failed_checks) if failed_checks else "none"}`

## Next Action

{next_action}
"""
    assert_public_projection_safe({"surface": report})
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the AW-DEMO-02 run status surface.")
    parser.add_argument(
        "--store-root",
        default=None,
        help="Optional local store root. Defaults to examples/demo-service-flow/.local.",
    )
    args = parser.parse_args()

    summary = run_demo(args.store_root)
    print(render_status_surface(summary))


if __name__ == "__main__":
    main()

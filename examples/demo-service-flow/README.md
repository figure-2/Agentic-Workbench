# AW-DEMO-01 Local Service-Shaped Demo

## Purpose

This demo proves the local Agentic Workbench flow through the public API
boundary:

```text
Idea
-> POST /api/v1/runs
-> sanitized artifact chain
-> local dry-run evidence persistence
-> GET /api/v1/runs/{run_id}
-> composed canonical run/evidence read model
```

The demo is fixture/dry-run only. It does not call Solar Pro 3, Upstage,
external providers, original DIV runtime, DAACS target runtime, CLI agents,
package installers, local app servers, or generated app builds.

## Run

From the project root:

```powershell
python examples/demo-service-flow/run_local_demo.py
```

To keep the local SQLite projection stores outside the example folder:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-demo-01
```

The printed JSON is a sanitized summary. It includes run status, artifact
kinds, evidence counts, linkage markers, repository boundary flags, and
zero-call execution metrics. It does not include raw prompts, provider payloads,
runtime payloads, logs, file bodies, raw approval signatures, raw nonces, or
local database root paths.

## Human-Readable Status Surface

For a reviewer-friendly Markdown report:

```powershell
python examples/demo-service-flow/render_status_surface.py
```

The status surface reads the same local API demo path and prints sections for
run state, artifact chain, DIV identity signals, DAACS identity signals,
evidence summary, execution boundary, claim boundary, checks, and next action.
It does not read repository tables directly and does not open live execution.

## Static UI Shell

For a local HTML shell over the same public summary:

```powershell
python examples/demo-service-flow/render_static_ui_shell.py --output .local/aw-demo-03-static-ui.html
```

The shell renders run status, artifact chain, DIV/DAACS identity signals,
evidence counts, execution boundary counters, and the live-open policy state.
It consumes the public demo summary only. It does not read repository tables,
load `.env` values, call Solar Pro 3, or run the DAACS target runtime.

## Expected Signals

- DIV identity is represented by planning and PRD artifacts.
- DAACS identity is represented by BuildSpec, ImplementationBrief, dry-run
  RunnerPlan evidence, and VerificationReport evidence.
- The composed read model remains local and fixture-based.
- Provider and target runtime call counts remain `0`.
- The static UI marks live policy as `closed / eligible only`.
- When `--include-provider-precheck` is used, manual proposal, disabled
  executor, one-shot permission, preflight audit, readiness decision, review
  packet, review packet export/read-model, handoff packet, and operator opt-in
  summaries remain blocked and hash-only. The sealed pre-execution packet also
  remains blocked and exposes only hashes and counts. The arming record
  remains blocked and exposes only hashes and counts. The release proposal
  remains blocked and exposes only hashes and counts. The final release packet
  remains blocked and exposes only hashes and counts. The execution switch
  remains blocked and exposes only hashes and counts. The executor preflight
  remains blocked and exposes only hashes and counts. The executor dispatch
  record remains blocked and exposes only hashes and counts. The invocation
  receipt remains blocked and exposes only hashes and counts. The
  post-invocation audit remains blocked and exposes only hashes and counts.
  The completion summary remains blocked and exposes only hashes and counts.
  The closeout record remains blocked and exposes only hashes and counts. The
  operator handback remains blocked and exposes only hashes and counts. The
  operator decision packet remains blocked and exposes only hashes and counts.

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

## Expected Signals

- DIV identity is represented by planning and PRD artifacts.
- DAACS identity is represented by BuildSpec, ImplementationBrief, dry-run
  RunnerPlan evidence, and VerificationReport evidence.
- The composed read model remains local and fixture-based.
- Provider and target runtime call counts remain `0`.

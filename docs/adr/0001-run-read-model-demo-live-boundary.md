# ADR 0001: Run Read Model, Demo Scope, and Live Boundary

## Status

Accepted

## Date

2026-06-01

## Context

Agentic Workbench now has separate local projection stores for:

- canonical run-session and artifact rows
- runner plan, verification report, audit event, and source artifact evidence
- approval subject, approval decision, and replay nonce evidence

The project needs one user-facing run read path that can explain a run without
returning raw prompts, raw artifact bodies, raw logs, provider payloads,
runtime payloads, or approval authorization material.

The project also needs a demo path that can grow toward real service behavior
without claiming live provider success or target runtime execution before those
boundaries are explicitly opened.

## Decision

`GET /api/v1/runs/{run_id}` will treat canonical run-session state as the
primary source of truth for run status, lifecycle stage, prompt contract hash,
and idea summary.

Evidence will be composed into a separate optional summary section. Evidence
composition may include sanitized counts, hashes, linkage status, check names,
blocked status, and safe summaries. It must not replace the canonical run
record and must not expose raw repository rows.

The canonical run/artifact store, runner/report/audit evidence store, and
approval/replay store remain separate persistence boundaries. API composition
is a read-model concern only.

The next demo scope is a local service-shaped path:

```text
Idea
-> sanitized planning/build artifacts
-> approved fixture or synthetic boundary
-> dry-run RunnerPlan
-> VerificationReport
-> canonical run read model
-> safe evidence summary
```

This demo may be implemented as if it will later become a real service path,
but current execution remains fixture/dry-run/fake-boundary only.

Solar Pro 3 and DAACS target runtime execution stay closed by default. A stored
API key is not sufficient to open live execution. Live/provider execution may be
opened only through a later explicit implementation unit after review of:

- provider approval policy
- replay persistence
- cost and quota guard
- timeout and retry limits
- workspace sandbox
- write allowlist
- rollback plan
- secret and payload redaction
- generated artifact sanitizer
- audit event projection

## Rationale

Canonical run state answers "what is this run?" Evidence answers "what did the
local harness observe?" Keeping them separate prevents fixture evidence,
approval evidence, and canonical lifecycle state from being confused.

A composed read model is necessary before UI or demo expansion because the UI
needs one safe endpoint to describe the run. Without this layer, a demo would
either duplicate repository logic or accidentally expose raw evidence.

Opening Solar Pro 3 or DAACS target runtime before the read model and live-open
checklist are fixed would increase secret exposure, cost, side-effect, and
claim drift risk.

## Consequences

- `AW-API-06` becomes the next implementation unit.
- UI/demo work should consume the composed run read model rather than querying
  individual repositories directly.
- Missing evidence should not block canonical run lookup.
- Corrupted evidence should mark only the evidence summary section as blocked.
- Corrupted canonical run store may block canonical run lookup.
- Public claims remain limited to local/dev fixture, dry-run, and fake-boundary
  behavior until a separate live-open ADR and implementation unit are accepted.

## Rejected Alternatives

### Return only canonical run state

Rejected because users cannot inspect dry-run, verification, and audit evidence
from the main run endpoint.

### Merge all repository rows into one API response

Rejected because raw-row leakage and trust-boundary confusion risks are high.

### Open Solar Pro 3 immediately because the API key exists

Rejected because credential availability is not an execution policy. Live
provider calls need explicit approval, budget, replay, redaction, and audit
controls.

### Open DAACS live runtime immediately

Rejected because CLI execution, package install, server start, file mutation,
and generated artifact output still require sandbox and rollback controls.

## Acceptance Criteria

- The composed run read model returns canonical run state plus optional safe
  evidence summary.
- Raw prompt, raw log, raw file body, provider payload, runtime payload, and raw
  approval authorization material are absent from public responses.
- Missing evidence store does not block canonical run lookup.
- Corrupted evidence store blocks only the evidence summary section.
- Repository boundary fields state which stores were queried.
- Solar Pro 3 calls remain 0 in current paths.
- DAACS target runtime calls remain 0 in current paths.

# AW-SOLAR-LIVE-01 One-Shot Planner Live Spike

## Summary

```text
id: AW-SOLAR-LIVE-01
depends_on:
  - AW-DEMO-FINAL-01
  - AW-SOLAR-02
scope:
  Run one tightly scoped Solar planner live spike for a representative idea,
  then project the result as sanitized planning evidence. The fixture planner
  remains the default path.
risk_level: high
rollback_plan:
  Remove live spike selector/API/demo/docs and return to AW-SOLAR-02 mocked
  planner spike plus AW-DEMO-FINAL-01 local portfolio demo.
```

## Goal

Move from mock/preflight planner evidence to one measured planner call under
operator-controlled conditions. The purpose is to compare whether a live Solar
planner can improve the PlanningBlueprint/PRD/ImplementationBrief stage without
opening DAACS target runtime execution.

## Scope

### A. Live Planner Admission

Acceptance tests:

- The fixture planner remains default.
- Live planner mode requires an explicit operator flag.
- Missing API key name or unavailable key blocks before request creation.
- Timeout, max input size, max output tokens, and cost/quota label are required.
- Request body is constructed from a sanitized prompt contract, not raw public
  prompt text.
- API key value is never printed, stored, or returned.

### B. One Live Call Execution

Acceptance tests:

- Exactly one provider call is allowed for one representative idea.
- DAACS target runtime call count remains `0`.
- Server start count remains `0`.
- Raw provider response body is not stored in public projection.
- Response projection includes summary hash, section count, artifact hints, and
  status only.
- Timeout or provider error returns a sanitized blocked/failed projection.

### C. Comparison Evidence

Acceptance tests:

- Fixture planner output remains available.
- Live planner projection is linked to the same run_id.
- Comparison records fixture stage coverage and live planner projection status.
- Public claim text does not describe this as hosted behavior, target runtime
  execution, or generated app completion.

## Out Of Scope

- DAACS target runtime execution
- Generated app server start
- Browser e2e
- Hosting/deployment
- Multi-call planner loops
- Long-running research/search
- Storing raw prompt/provider payloads

## Quantitative Targets

| Metric | Target |
|---|---:|
| Representative live planner scenarios | 1 |
| Explicit operator opt-in | 1 |
| Provider call count | 1 |
| DAACS target runtime calls | 0 |
| Server starts | 0 |
| Raw provider body exposure | 0 |
| API key value exposure | 0 |
| Public local root path exposure | 0 |

## Verification Plan

- Unit tests for admission blocking and sanitized projection.
- Smoke test with fake provider runner.
- Manual live command only after operator confirms budget/timeout/input size.
- Record exact provider call count, timeout, status, and sanitized response
  projection counts in `docs/metrics.md`.

## Done Criteria

- Default demo still uses fixture planner.
- Live planner path requires explicit flag.
- One manual live spike is either passed or failed with sanitized evidence.
- No API key value, raw prompt, raw provider body, local root path, server
  state, or DAACS target runtime output is exposed.
- Targeted tests pass.
- Full regression is run once, or any blocker is recorded with exact failing
  tests and cause.

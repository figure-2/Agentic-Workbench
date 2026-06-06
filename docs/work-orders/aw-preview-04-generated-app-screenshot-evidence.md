# AW-PREVIEW-04 Generated App Screenshot Evidence

## Summary

```text
id: AW-PREVIEW-04
depends_on:
  - AW-GENERATED-QUALITY-01
  - AW-PREVIEW-03
scope:
  Capture browser screenshot evidence for the improved generated fixture app
  under explicit operator opt-in. If browser runtime is unavailable, record a
  clear environment-blocked result and keep the portfolio bundle honest.
risk_level: high
rollback_plan:
  Remove screenshot capture hook/docs and keep AW-GENERATED-QUALITY-01 plus
  AW-PREVIEW-03 browser setup boundary.
```

## Goal

Show the improved generated app as visual evidence, not only JSON/static
summary evidence.

## Team Decision

Product lens: the next portfolio gap is a screenshot or browser-verified first
screen of the improved generated app.

Frontend lens: the screenshot should show workflow stages, artifact cards,
runner plan, verification summary, execution boundary counters, and task board
sections.

Security lens: public output must expose only screenshot hash, byte count,
status, reason, and counts. Screenshot path, page text, raw command output,
local root path, provider payload, and credentials remain hidden.

Operations lens: browser package/runtime setup may require local installation or
download. It must remain explicit opt-in and must be documented before running.

QA lens: this task must record quantitative before/after results in
`docs/metrics.md`, including screenshot availability, screenshot hash count,
byte count, server start/stop counts, and the exact blocked reason if browser
runtime remains unavailable.

## Scope

### A. Browser Runtime Preflight Refresh

Acceptance tests:

- Browser runtime unavailable returns `environment_blocked` with install
  guidance labels/hashes only.
- Browser runtime available returns availability count `1`.
- No server starts before browser runtime availability is confirmed.
- Public projection exposes browser status/reason/count only.

### B. Explicit Screenshot Capture

Acceptance tests:

- Without explicit local preview opt-in, server start is blocked.
- With explicit local preview opt-in and browser runtime available, generated app
  preview server starts inside the run-scoped workspace only.
- Screenshot evidence includes screenshot hash and byte count.
- Preview server cleanup count is `100%`.
- Screenshot path, page text, command output, and local root path exposure are
  `0`.
- Browser package/runtime setup command count is recorded separately from
  preview server start count.

### C. Portfolio Bundle Integration

Acceptance tests:

- `run_portfolio_demo.py` can include screenshot status in the same final
  preview summary.
- If screenshot is unavailable, the bundle states blocked/environment-blocked,
  not screenshot verified.
- Provider calls, Solar additional calls, and DAACS target runtime calls remain
  `0`.

## Quantitative Targets

| Metric | Target |
|---|---:|
| Representative scenario count | 1 |
| Generated app screenshot evidence count | 1 when browser runtime is available |
| Screenshot hash count | 1 when browser runtime is available |
| Screenshot byte count | >0 when browser runtime is available |
| Preview server cleanup count | 100% |
| Provider calls | 0 |
| Solar additional calls | 0 |
| DAACS target runtime calls | 0 |
| Raw/public exposure findings | 0 |

## Out Of Scope

- New Solar planner call
- DAACS target runtime execution
- Hosted deployment
- Automatic browser setup without explicit operator approval
- Public screenshot file path or page text return

## Done Criteria

- The project can produce visual browser evidence when the browser runtime is
  available and explicitly approved.
- If the runtime is unavailable, the blocker is specific and documented.
- Metrics record exact screenshot availability, hash, byte count, cleanup, and
  zero-call counters.

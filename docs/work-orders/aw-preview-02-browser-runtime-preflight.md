# AW-PREVIEW-02 Browser Runtime Preflight

## Summary

```text
id: AW-PREVIEW-02
depends_on:
  - AW-PREVIEW-01
scope:
  Add repeatable browser runtime availability preflight before local fixture app
  preview server/browser verification.
risk_level: medium
rollback_plan:
  Remove browser runtime preflight/probe/docs/tests and return to AW-PREVIEW-01.
```

## Goal

Reduce ambiguous preview `environment_blocked` states by distinguishing:

- missing Python Playwright package
- missing/unlaunchable Playwright browser runtime
- browser runtime available and eligible for screenshot verification

The public projection must provide status, reason, labels, hashes, and counts
only. It must not expose raw exception messages, local paths, environment
values, page text, screenshot paths, command output bodies, provider payloads,
or secrets.

## Scope

### A. Browser Runtime Preflight

Acceptance tests:

- If Python Playwright is unavailable, return `environment_blocked`.
- If browser runtime is unavailable or unlaunchable, return
  `environment_blocked`.
- If browser runtime is available, allow preview server/browser verification to
  proceed.
- Preflight returns install guidance labels and hashes only.
- Preflight is injectable for deterministic tests.

### B. Preview Attempt Integration

Acceptance tests:

- Browser preflight runs only after preview opt-in and build evidence are valid.
- Missing opt-in still blocks before preflight.
- Missing browser runtime blocks before preview server start.
- When preview server starts, cleanup is recorded.
- Provider/Solar/DAACS target runtime calls remain `0`.

### C. Docs And Metrics

Acceptance tests:

- docs/evals records official Playwright references.
- docs/metrics records current browser availability count.
- README/demo docs clarify that browser runtime setup is not automatic.

## Out Of Scope

- Installing Playwright or browser binaries automatically
- Starting preview server without opt-in
- Returning raw browser exception text
- Returning screenshot path or page text
- Hosted/deployed app claims
- Original DAACS runtime execution

## Quantitative Targets

| Metric | Target |
|---|---:|
| Browser runtime preflight records | 1 |
| Install guidance label count | 2 |
| Install guidance hash count | 2 |
| Missing-browser server start count | 0 |
| Provider calls | 0 |
| Solar additional live calls | 0 |
| DAACS target runtime calls | 0 |
| Raw error/path/body exposure | 0 |

## Done Criteria

- Targeted unit/smoke tests pass.
- One opt-in demo command records browser runtime preflight status.
- Docs and metrics record exact current-environment numbers.
- Full regression passes once, or any blocker is recorded with exact failing
  test and cause.

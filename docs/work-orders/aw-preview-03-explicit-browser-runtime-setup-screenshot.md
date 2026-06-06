# AW-PREVIEW-03 Explicit Browser Runtime Setup And Screenshot Evidence

## Summary

```text
id: AW-PREVIEW-03
depends_on:
  - AW-PREVIEW-02
scope:
  Add an explicitly approved browser runtime setup path and rerun local preview
  screenshot verification for the generated fixture app.
risk_level: medium
rollback_plan:
  Remove browser runtime setup hook/docs and keep AW-PREVIEW-02
  environment_blocked preflight behavior.
```

## Goal

Turn the current AW-PREVIEW-02 `environment_blocked` state into repeatable
screenshot evidence when the operator explicitly approves local browser runtime
setup. The default path must remain no-install and no-server-start.

## Context

AW-PREVIEW-02 proved that the local preview flow now blocks before server start
when Python Playwright or its browser runtime is unavailable. Official
Playwright guidance says the matching browser binaries must be installed for
the installed Playwright version before browser automation can run.

Official references:

- Playwright Python browsers: https://playwright.dev/python/docs/browsers
- Playwright screenshots: https://playwright.dev/docs/screenshots

## Scope

### A. Browser Runtime Setup Gate

Acceptance tests:

- No setup command runs without explicit operator opt-in.
- Setup guidance uses official Playwright browser install flow.
- Public projection returns setup status/hash/count only.
- Raw command output, local paths, env values, and browser error text are not
  returned.

### B. Screenshot Verification Rerun

Acceptance tests:

- With browser runtime available, local preview server starts only inside the
  generated app workspace.
- Screenshot verification returns `screenshot_hash` and
  `screenshot_byte_count`.
- Screenshot path and raw page text are not returned.
- Preview server start/stop cleanup count is `1/1`.
- Provider, Solar, and DAACS target runtime calls remain `0`.

### C. Docs And Metrics

Acceptance tests:

- `docs/metrics.md` records browser availability count before and after setup.
- Eval doc records screenshot byte count and hash count.
- README/demo docs explain the opt-in setup path and default blocked behavior.
- Claims do not state hosted, production, or real DAACS runtime success.

## Out Of Scope

- Automatic package/browser installation
- Hosted deployment
- Solar planner additional live call
- Original DAACS runtime execution
- Returning screenshot files or page text through public API

## Quantitative Targets

| Metric | Target |
|---|---:|
| Default setup command executions | 0 |
| Explicit setup opt-in count | 1 |
| Browser runtime available count after setup | 1 |
| Screenshot evidence count after setup | 1 |
| Screenshot hash count | 1 |
| Screenshot byte count | >0 |
| Preview server start/stop cleanup | 1/1 |
| Provider/Solar/DAACS runtime calls | 0 |
| Raw path/body/error exposure | 0 |

## Done Criteria

- Setup remains blocked by default.
- Explicit opt-in path can produce screenshot evidence on a prepared local
  browser runtime.
- Targeted tests and one full regression pass.
- Metrics record exact numeric results from this environment.

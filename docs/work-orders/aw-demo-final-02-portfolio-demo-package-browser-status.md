# AW-DEMO-FINAL-02 Portfolio Demo Package With Browser Status

## Summary

```text
id: AW-DEMO-FINAL-02
depends_on:
  - AW-DEMO-FINAL-01
  - AW-PREVIEW-03
scope:
  Package the service-shaped demo, generated fixture app evidence, local build
  evidence, local preview status, and browser runtime setup status into one
  portfolio-facing command/output bundle.
risk_level: medium
rollback_plan:
  Remove AW-DEMO-FINAL-02 package script/docs and keep AW-DEMO-FINAL-01 plus
  AW-PREVIEW-03 public evidence.
```

## Goal

Make the current project understandable to a first-time reviewer in one local
portfolio bundle:

```text
Idea
-> SoT/PRD/ImplementationBrief
-> RunnerPlan
-> VerificationReport
-> generated fixture app files
-> local build evidence
-> local preview/browser setup status
```

The bundle must be honest about the current environment. If browser runtime is
not available, it must show `environment_blocked` or setup `blocked` status
instead of claiming screenshot verification success.

## Scope

### A. One Command Portfolio Bundle

Acceptance tests:

- One command creates JSON summary and static HTML preview.
- HTML includes stage coverage, artifact linkage, generated app file count,
  local build status, local preview status, browser setup status, and next
  action.
- The command does not install packages or browser binaries by default.
- The command does not start a preview server unless the existing explicit
  preview opt-in is passed.

### B. Browser Status Section

Acceptance tests:

- Shows browser runtime preflight availability count.
- Shows browser setup attempt status and setup command attempt count.
- Shows screenshot evidence count and screenshot byte count when available.
- Shows setup command execution count `0` by default.
- Does not expose raw command output, argv, browser errors, screenshot paths,
  page text, or local root paths.

### C. Portfolio Claim Boundary

Acceptance tests:

- Public text says local service-shaped demo, not hosted/production success.
- Fixture/dry-run/live states remain visually distinct.
- Provider/Solar/DAACS target runtime call counts are visible and remain `0`
  unless separately approved.
- Screenshot success is claimed only if screenshot hash and byte count are
  present from a real verification run.

### D. Metrics And Verification

Acceptance tests:

- `docs/metrics.md` records exact bundle file count, stage coverage, generated
  file count, build status, browser setup status, screenshot evidence count,
  and raw exposure count.
- Targeted tests cover bundle generation and public safety.
- One full regression run is recorded.

## Out Of Scope

- Automatic Playwright/package/browser installation
- Hosted deployment
- Additional Solar live calls
- Original DAACS runtime execution
- Returning generated file bodies or screenshot paths through public output

## Quantitative Targets

| Metric | Target |
|---|---:|
| Portfolio bundle command count | 1 |
| Generated output files | >=2 |
| Stage coverage | 7/7 |
| Generated fixture app file count | >=3 |
| Local build status field count | >=1 |
| Browser setup status field count | >=1 |
| Default setup command executions | 0 |
| Raw exposure findings | 0 |
| Provider/Solar/DAACS target runtime calls | 0 |

## Done Criteria

- A first-time reviewer can open one generated HTML file and understand the
  document-to-app workflow.
- The bundle is portfolio-useful even when browser runtime is unavailable.
- The implementation remains public-safe and test-backed.

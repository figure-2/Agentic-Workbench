# AW-DEMO-FINAL-01 Portfolio Demo Package

## Summary

```text
id: AW-DEMO-FINAL-01
depends_on:
  - AW-MVP-01
  - AW-APP-01
  - AW-BUILD-04
scope:
  Package the service-shaped local demo into one reviewer-friendly command
  that produces a sanitized JSON summary and static HTML preview with local
  fixture app build-attempt evidence.
risk_level: medium
rollback_plan:
  Remove demo packaging script/docs and keep the existing AW-BUILD-04 demo,
  preview, and tests.
```

## Goal

Make the portfolio review path obvious to a first-time reviewer:

```text
Idea
-> PlanningBlueprint
-> PRDPackage
-> ImplementationBrief
-> Approval
-> RunnerPlan
-> VerificationReport
-> Generated Fixture App Files
-> Local Fixture Build Attempt Evidence
-> Static Preview
```

## Scope

### A. One-Command Demo Wrapper

Acceptance tests:

- One command creates a local demo store under `.local`.
- The command runs the public demo summary path.
- The command renders the static preview HTML.
- The command records output file locations as sanitized relative labels only.
- Local root paths are not returned in public summary.

### B. Portfolio Summary

Acceptance tests:

- Stage coverage is `7/7`.
- Generated fixture app file count is `9`.
- Local build attempt evidence is included when opt-in is explicitly enabled.
- Server start count remains `0`.
- Provider call count remains `0`.
- DAACS target runtime call count remains `0`.
- Raw file bodies and command output bodies are not returned.

### C. README Quickstart

Acceptance tests:

- README has a short portfolio demo command.
- README explains the result is local fixture/demo evidence.
- README does not claim hosted behavior, external provider output, or target
  runtime execution.

## Out Of Scope

- Starting a dev server
- Browser e2e against a running generated app
- Hosting or deployment
- Solar Pro 3 provider call
- DAACS target runtime execution
- Raw file body viewer
- Tracking `.local`, `node_modules`, or `dist`

## Quantitative Targets

| Metric | Target |
|---|---:|
| Portfolio command count | 1 |
| Stage coverage | 7/7 |
| Preview HTML generated | 1 |
| Generated fixture app files | 9 |
| Local build attempt evidence records | 1 |
| Server starts | 0 |
| Provider calls | 0 |
| DAACS target runtime calls | 0 |
| Raw public body exposure | 0 |

## Done Criteria

- Targeted demo/preview tests pass.
- One manual portfolio command completes locally.
- `docs/metrics.md` records exact command/result counts.
- `git diff --check` passes.
- Full regression is run once, or any blocker is recorded with exact failing
  tests and cause.

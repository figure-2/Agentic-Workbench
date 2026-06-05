# AW-BUILD-04 Explicit Local Fixture App Build Attempt

## Summary

```text
id: AW-BUILD-04
depends_on:
  - AW-BUILD-03
scope:
  Run one explicit local fixture app package install/build attempt inside an
  isolated run-scoped generated workspace after opt-in.
  This is the first step that may execute local package manager/build commands.
  It must not call Solar Pro 3, any external LLM provider, or DAACS target
  runtime execution.
risk_level: high
rollback_plan:
  Remove local build executor/API/demo/preview/tests/docs and return to
  AW-BUILD-03 local build preflight projection.
```

## Goal

Move the portfolio demo from "build preflight eligible" to "local fixture app
build attempted" with measured results. The result can be success, failure, or
environment-blocked, but it must be recorded with sanitized public evidence.

## Scope

### A. Explicit Opt-In Build Executor

Acceptance tests:

- AW-BUILD-03 `local_build_preflight_hash` must exist and match expected hash.
- A separate local build opt-in flag must be present.
- If opt-in is missing, package install/build execution remains blocked.
- If opt-in is present, only the generated fixture app workspace is eligible.
- Local root path is never returned in public projection.
- Raw file bodies, package output, stderr/stdout bodies, env values, provider
  payloads, and secrets are never returned.

### B. Local Command Attempt

Acceptance tests:

- package install attempt count is recorded.
- build attempt count is recorded.
- command exit codes are summarized as status/reason/count/hash only.
- server start count remains `0`.
- provider calls remain `0`.
- DAACS target runtime calls remain `0`.
- network access, if package manager requires it, is explicitly measured and
  documented as local build dependency resolution only, not provider/runtime
  execution.

### C. Demo/Preview/Docs

Acceptance tests:

- demo summary shows build attempt status, reason, command count, and sanitized
  result hashes.
- preview shows "build attempted" separately from "hosted" or "production".
- docs/evals records exact numeric results.
- docs/metrics records package install attempts, build attempts, server starts,
  provider calls, DAACS runtime calls, raw exposure findings, and claim drift
  findings.

## Out Of Scope

- Solar Pro 3 live call
- DAACS target runtime execution
- generated app hosting/deployment
- browser e2e against a running server
- permanent build cache tracking
- committing `.local`, `node_modules`, `dist`, or generated build outputs

## Quantitative Targets

| Metric | Target |
|---|---:|
| Explicit build attempt scenarios | 1 |
| Required preflight hash match | 1/1 |
| Operator opt-in required | 1 |
| Package install attempt count | 1 |
| Build attempt count | 1 |
| Server start count | 0 |
| Provider calls | 0 |
| DAACS target runtime calls | 0 |
| Public raw output/body exposure | 0 |
| Local root path exposure | 0 |

## Implementation Notes

- Prefer a small service boundary before demo/preview wiring.
- Use the generated app workspace from AW-DAACS-RUNTIME-MVP-01 through
  AW-BUILD-03 rather than creating a separate app.
- Record command labels and exit-code hashes, not raw output bodies.
- Keep generated local artifacts under ignored `.local` paths.

## Done Criteria

- Targeted tests pass.
- One manual demo command records a sanitized build attempt result.
- Full regression passes once, or any full-regression blocker is recorded with
  exact failing tests and cause.
- No tracked local artifacts, `node_modules`, `dist`, raw command output, or
  secrets are added.

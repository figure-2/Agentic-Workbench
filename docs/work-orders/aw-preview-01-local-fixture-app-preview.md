# AW-PREVIEW-01 Local Fixture App Preview

## Summary

```text
id: AW-PREVIEW-01
depends_on:
  - AW-DAACS-RUNTIME-MVP-02
  - AW-BUILD-04
scope:
  Start the document-linked generated fixture app through an explicit opt-in
  local preview boundary and verify the first screen when browser runtime
  support is available.
risk_level: high
rollback_plan:
  Remove preview runner/API/demo/tests/docs and return to
  AW-DAACS-RUNTIME-MVP-02 + AW-BUILD-04.
```

## Goal

Show the portfolio-visible flow:

```text
SoT/PRD/ImplementationBrief
-> document-linked generated fixture app files
-> explicit local package/build attempt
-> explicit local preview server
-> first-screen browser verification evidence
```

The preview evidence must remain public-safe. It may report status, reason,
hashes, counts, visible marker count, screenshot hash/byte count, and server
start/stop counters. It must not return local root paths, file bodies, page
text, command output bodies, provider payloads, prompts, credentials, or
screenshots paths.

## Scope

### A. Preview Attempt Service

Acceptance tests:

- `local_build_attempt_hash` must exist and match the build-attempt projection.
- The local build attempt must have passed before preview execution.
- Separate local preview opt-in must be present.
- If opt-in is missing, preview server start is blocked.
- Preview server starts only inside the run-scoped generated app workspace.
- Server cleanup is recorded.
- Provider calls, Solar additional live calls, and DAACS target runtime calls
  remain `0`.

### B. Browser Verification

Acceptance tests:

- First screen checks markers for workflow, task board, and verification
  summary.
- Screenshot evidence is represented as hash/byte count only.
- If Playwright/browser runtime support is unavailable, status is
  `environment_blocked` instead of falsely claiming success.
- Raw page body, screenshot path, and local root path exposure remain `0`.

### C. API/Demo/Docs

Acceptance tests:

- API exposes `/api/v1/daacs/runtime/local-preview-attempt`.
- Demo supports `--include-daacs-runtime-local-preview-attempt`.
- Demo supports explicit `--allow-local-preview-attempt`.
- Default demo path records blocked preview with server starts `0`.
- Metrics and eval docs record exact numeric results and environment blockers.

## Out Of Scope

- Solar Pro 3 additional live call
- Original DAACS target runtime execution
- Deployment or hosted app success claim
- Raw command output viewer
- Raw generated file body viewer
- Committing `.local`, `node_modules`, `dist`, screenshots, or browser cache

## Quantitative Targets

| Metric | Target |
|---|---:|
| Representative preview scenario count | 1 |
| Required visible marker count | 4 |
| Default path preview server starts | 0 |
| Opt-in path preview server starts | 1 |
| Opt-in path server cleanup count | 1 |
| Provider calls | 0 |
| Solar additional live calls | 0 |
| DAACS target runtime calls | 0 |
| Public raw output/body exposure | 0 |
| Public local root path exposure | 0 |

## Done Criteria

- Unit tests cover blocked, success via fake runner, hash mismatch, and
  environment-blocked browser runtime.
- Smoke tests cover API/demo default blocked path.
- One opt-in local demo command records sanitized preview attempt evidence.
- Full regression passes once, or any blocker is recorded with exact failing
  test and cause.
- No tracked local artifact, secret, screenshot, build output, or local cache is
  added.

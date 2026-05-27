# AW-NEXT-04 Eval Report

## Summary

| Field | Value |
|---|---|
| Date | 2026-05-27 |
| Result | PASS |
| Scope | DAACS offline runner boundary |
| Eval mode | offline-fixture-only |
| Live LLM calls | 0 |
| Live API calls | 0 |
| Model provider | Not used |

## Gates

| Gate | Result | Evidence |
|---|---|---|
| Offline Runner Admission Gate | PASS | mapped DAACSState accepted without live execution |
| State Integrity Gate | PASS | required state keys and offline invariants checked |
| Blocked Operation Gate | PASS | CLI/provider/subprocess/install/server/write payloads fail closed |
| No-Subprocess Gate | PASS | subprocess APIs monkeypatched to fail; runner does not call them |
| No-Filesystem-Write Gate | PASS | write APIs monkeypatched to fail; runner does not call them |
| No-Package-Install Gate | PASS | `npm install` and related install commands detected as blocked payloads |
| No-Server-Start Gate | PASS | `uvicorn` and dev server commands detected as blocked payloads |
| No-Provider-Import Gate | PASS | DAACS/provider runtime modules are not imported |
| Namespace Boundary Gate | PASS | generated file parent traversal fixtures are rejected |
| Regression Gate | PASS | all previous tests still pass |

## Quantitative Metrics

| Metric | Value |
|---|---:|
| Pytest collected cases | 67 |
| Pytest passed cases | 67 |
| New runner/security test cases in this step | 22 |
| Runner boundary test cases | 18 |
| Generated file namespace rejection fixtures | 4 |
| Blocked operation families | 6 |
| Required state checks | 10 |
| Live LLM calls | 0 |
| Live API calls | 0 |
| Provider calls | 0 |
| CLI agent invocations | 0 |
| Subprocess calls | 0 |
| Package install calls | 0 |
| Server start calls | 0 |
| Filesystem writes | 0 |
| Provider runtime imports | 0 |

## Blocked Operation Families

- CLI agent execution
- provider/LLM call
- subprocess execution
- package install
- local server start
- filesystem write

## Unsafe State Rejections

- `mode='live'`
- non-empty `llm_sources`
- `cli_assistant_available=true`
- unsafe `project_dir`
- prefilled `backend_files`, `frontend_files`, or `all_files`
- pre-seeded `compatibility_verified=true`
- missing required state contract key

## Coverage Character

This eval measures offline boundary enforcement only. It does not measure live DAACS execution, generated code quality, package install success, local server startup, Solar Pro 3 quality, hosted success, or production readiness.

## Next Eligible Work

The next safe step is a live-runner design document that separates offline runner, dry-run runner, and live runner responsibilities before any provider call or host command is enabled.


# AW-DAACS-RUNTIME-00 Work Order: Target Runtime Sandbox Design

## Conclusion

`AW-DAACS-RUNTIME-00` is the target runtime preparation step after
`AW-SOLAR-01`. Its purpose is to define the sandbox, file boundary, command
policy, rollback policy, and audit contract required before any DAACS target
runtime adapter can be connected to the service-shaped flow.

This is not target runtime execution. It is a sandbox design and preflight
contract.

## Implementation Unit

```text
id: AW-DAACS-RUNTIME-00
depends_on:
  - AW-MVP-01
  - AW-SOLAR-01
scope: DAACS target runtime sandbox contract and preflight design, still no target runtime call
risk_level: high
rollback_plan: remove sandbox design/preflight docs/tests and keep AW-MVP-01 dry-run runner path
```

## Senior Review Decision

Product lens:

- The final target is generated backend/frontend artifacts, but the next safe
  step is not execution. The next step is defining what a controlled execution
  workspace may touch.
- Users should be able to see why a target runtime run is still closed and what
  must be approved before opening it.

Architecture lens:

- Keep `RunnerPlan` as the source of intended actions.
- Add a target runtime preflight boundary between `RunnerPlan` and any future
  DAACS runtime adapter.
- Treat the runtime workspace as a disposable, run-scoped sandbox with explicit
  input, output, command, network, and rollback controls.

Security lens:

- No unrestricted file writes.
- No package installation, server start, subprocess, or network call by default.
- All paths must resolve under a run-scoped workspace root.
- Public projection must contain only status, reason, hashes, counts, and
  allowlist/denylist summaries.

Data lens:

- Persist only sandbox policy hash, workspace intent hash, allowed path count,
  denied path count, command policy hash, rollback hash, and no-call counters.
- Do not persist raw generated file bodies, raw logs, raw command output, or raw
  runtime payloads.

QA lens:

- Compare the current dry-run runner path with a target runtime preflight path.
- The preflight path must prove it blocks before DAACS target runtime admission.

Audit lens:

- Public wording must call this a sandbox preflight design.
- Do not claim generated backend/frontend output, hosted behavior, install
  success, build success, or runtime verification.

## Scope

Define the sandbox contract for a later runtime adapter:

```text
RunnerPlan
-> TargetRuntimePreflightRequest
-> workspace policy validation
-> path allowlist validation
-> command/network/install policy validation
-> rollback/abort policy validation
-> TargetRuntimePreflightResult
-> blocked public projection
```

Recommended implementation shape:

- `TargetRuntimeSandboxPolicy`
- `TargetRuntimeWorkspaceIntent`
- `TargetRuntimeCommandPolicy`
- `TargetRuntimeRollbackPolicy`
- `TargetRuntimePreflightRequest`
- `TargetRuntimePreflightResult`
- tests for path traversal, disallowed writes, install/server commands,
  missing rollback, and no-call counters

## Non-Scope

- No DAACS target runtime call.
- No source DAACS subprocess.
- No package installation.
- No generated app build.
- No local app server start.
- No unrestricted file write.
- No network call.
- No raw generated file body persistence.
- No raw log or command output persistence.
- No provider/planner call.

## Acceptance Tests

- Missing sandbox policy blocks before runtime admission.
- Missing run-scoped workspace intent blocks before runtime admission.
- Path traversal is blocked.
- Absolute path outside workspace is blocked.
- File write outside allowlist is blocked.
- Package install command is blocked.
- Server start command is blocked.
- Network command is blocked.
- Missing rollback/abort policy blocks.
- Public projection exposes hash/status/reason/count only.
- Filesystem write count remains `0`.
- Subprocess count remains `0`.
- Network call count remains `0`.
- DAACS target runtime call count remains `0`.
- Raw file/log/runtime payload findings remain `0`.
- Existing regression suite remains green.

## Comparison Experiment

Run the same `RunnerPlan` through two paths:

| Variant | Expected status | Filesystem writes | Subprocess calls | Runtime calls |
|---|---|---:|---:|---:|
| `dry_run_runner` | passed | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | 0 | 0 | 0 |

Record these metrics in `docs/metrics.md` after implementation:

| Metric | Target |
|---|---:|
| Comparison variants | 2 |
| Path traversal fixtures blocked | 100% |
| Disallowed write fixtures blocked | 100% |
| Package install fixtures blocked | 100% |
| Server start fixtures blocked | 100% |
| Filesystem writes | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |

## Suggested Files

- `packages/daacs_builder/target_runtime_sandbox.py`
- `apps/api/agentic_workbench_api/services/target_runtime_preflight.py`
- `tests/unit/test_target_runtime_sandbox.py`
- `tests/smoke/test_daacs_runtime_preflight.py`
- `docs/evals/aw-daacs-runtime-00-target-runtime-sandbox-design.md`
- `docs/metrics.md`
- `README.md`
- `docs/architecture.md`

## Completion Criteria

- Runtime preflight cannot be confused with execution.
- Every denied operation has a public-safe reason.
- Quantitative comparison data is recorded.
- The follow-up implementation can add a disabled runtime adapter skeleton
  without changing the AW-MVP-01 dry-run behavior.

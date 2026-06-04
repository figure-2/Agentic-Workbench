# AW-DAACS-RUNTIME-01 Work Order: Disabled Target Runtime Adapter Admission

## Summary

`AW-DAACS-RUNTIME-01` connects the `AW-DAACS-RUNTIME-00` preflight hash to a
disabled DAACS target runtime adapter admission boundary. It does not execute
DAACS runtime code, write files, spawn subprocesses, install packages, start
servers, read environment values, import provider SDKs, or open network
connections.

## Work Unit

```text
id: AW-DAACS-RUNTIME-01
depends_on:
  - AW-DAACS-RUNTIME-00
scope:
  Disabled target runtime adapter admission skeleton.
  A public-safe preflight projection and expected preflight hash are required
  before the disabled adapter admission path can be reached. Even after
  admission passes, the adapter remains disabled and execution permission
  remains 0.
risk_level: high
rollback_plan:
  Remove target runtime adapter admission module, API route, demo hook, tests,
  and AW-DAACS-RUNTIME-01 docs. Return to AW-DAACS-RUNTIME-00 preflight-only
  state.
```

## Acceptance Tests

- Preflight projection is required before disabled adapter admission.
- `expected_preflight_hash` must match the supplied preflight projection hash.
- `run_id` and `runner_plan_hash` must match between request and preflight.
- Dirty preflight evidence, including denied paths or blocked operations, is
  blocked before adapter reachability.
- Valid preflight evidence can reach the disabled adapter skeleton.
- Disabled adapter result remains `blocked`.
- Execution permission remains `0`.
- Filesystem writes, subprocess calls, package installs, server starts, network
  calls, provider calls, and DAACS target runtime calls remain `0`.
- Public projection exposes only hash/status/reason/count-safe evidence.
- Raw prompt, raw log, raw file body, provider payload, runtime payload, secret,
  SDK import, env value, and local path exposure remain `0`.

## Boundary Flow

```text
RunnerPlan hash
-> AW-DAACS-RUNTIME-00 TargetRuntimePreflightResult
-> expected_preflight_hash
-> TargetRuntimeAdapterAdmissionRequest
-> TargetRuntimeAdapterAdmissionService
-> DisabledTargetRuntimeAdapter
-> blocked public projection
```

## Public Projection Shape

The public projection may include:

- `projection_version`
- `run_id`
- `mode`
- `status`
- `reason`
- `runner_plan_hash`
- `expected_preflight_hash`
- `preflight_hash`
- `adapter_admission_hash`
- `checks`
- `counts`
- `execution_boundary`
- `claim_boundary`

The public projection must not include:

- raw prompt
- raw file body
- raw logs
- generated artifact body
- provider payload
- runtime payload
- provider response body
- secret values
- local absolute paths

## Comparison Experiment

| Variant | Expected Status | Purpose |
|---|---|---|
| `dry_run_runner` | `passed` | Existing service-shaped fixture flow remains the artifact source. |
| `target_runtime_preflight` | `blocked` | Sandbox/write/operation/rollback readiness is checked with no runtime call. |
| `disabled_adapter_admission` | `blocked` | Preflight hash is required before adapter reachability, and execution remains closed. |

## Quantitative Targets

| Metric | Target |
|---|---:|
| Comparison variants | 3 |
| Dry-run stage coverage | 7/7 |
| Preflight hash required block coverage | 1/1 |
| Preflight hash mismatch block coverage | 1/1 |
| Dirty preflight block coverage | 1/1 |
| Valid preflight adapter reach count | 1 |
| Disabled adapter block count | 1 |
| Execution permission count | 0 |
| Filesystem writes | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |

## Implementation Files

- `packages/daacs_builder/target_runtime_admission.py`
- `apps/api/agentic_workbench_api/services/target_runtime_admission.py`
- `apps/api/agentic_workbench_api/main.py`
- `examples/demo-service-flow/run_local_demo.py`
- `tests/unit/test_target_runtime_adapter_admission.py`
- `tests/smoke/test_daacs_runtime_preflight.py`
- `docs/evals/aw-daacs-runtime-01-disabled-adapter-admission.md`
- `docs/metrics.md`

## Non-Goals

- No DAACS runtime execution.
- No generated application delivery.
- No package install, server start, subprocess execution, or filesystem write.
- No provider/API/network call.
- No Solar Pro 3 call.
- No claim that the target runtime has successfully produced a runnable app.

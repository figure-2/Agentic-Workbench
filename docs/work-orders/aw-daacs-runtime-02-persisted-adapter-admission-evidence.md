# AW-DAACS-RUNTIME-02 Work Order: Persisted Adapter Admission Evidence

## Summary

`AW-DAACS-RUNTIME-02` persists disabled DAACS target runtime adapter admission
evidence to a local SQLite store and exposes a public read model. The stored
row is hash/status/count-only. It does not store raw prompts, raw logs, raw file
bodies, runtime payloads, provider payloads, generated artifact bodies, secrets,
environment values, SDK output, local store roots, or raw database rows.

This work still does not execute the DAACS target runtime.

## Work Unit

```text
id: AW-DAACS-RUNTIME-02
depends_on:
  - AW-DAACS-RUNTIME-01
scope:
  Persist disabled target runtime adapter admission evidence in SQLite and
  expose a sanitized read-model API. The adapter admission result must remain
  blocked, execution permission must remain 0, and public output must be
  limited to hashes, status, reason, counts, and repository boundary flags.
risk_level: high
rollback_plan:
  Remove target runtime adapter admission store, read-model API route, demo
  persistence hook, tests, and AW-DAACS-RUNTIME-02 docs. Return to
  AW-DAACS-RUNTIME-01 disabled adapter admission projection only.
```

## Acceptance Tests

- Adapter admission evidence is saved only after a valid preflight hash reaches
  the disabled adapter result.
- SQLite rows contain `adapter_admission_hash`, `preflight_hash`, status,
  reason, and count fields only.
- Public read model returns status/hash/count/repository boundary fields only.
- Duplicate `adapter_admission_hash` is blocked and leaves partial row count at
  `0`.
- Corrupted, unavailable, or wrong-schema SQLite stores return a blocked public
  read model.
- API/demo path can optionally configure the target runtime admission
  repository.
- `GET /api/v1/daacs/runtime/adapter/admissions/{run_id}` returns sanitized
  evidence for the requested run only.
- Raw prompt, raw log, raw file body, provider payload, runtime payload, secret,
  env value, SDK import, network call, and local path exposure remain `0`.
- DAACS target runtime call count remains `0`.

## Boundary Flow

```text
RunnerPlan hash
-> target runtime preflight projection
-> disabled adapter admission projection
-> TargetRuntimeAdapterAdmissionRecord
-> SQLite target runtime admission store
-> public adapter admission read model
```

## Public Read Model Shape

The read model may include:

- `projection_version`
- `status`
- `run_id`
- `counts`
- `adapter_admissions`
- `repository_boundary`
- `execution_boundary`

Each `adapter_admissions` item may include only status, reason, hashes, and
count fields. It must not include database roots, raw rows, raw payloads, raw
logs, file bodies, provider responses, or generated artifact bodies.

## Comparison Experiment

| Variant | Expected Status | Purpose |
|---|---|---|
| `dry_run_runner` | `passed` | Existing service-shaped fixture path remains the artifact source. |
| `target_runtime_preflight` | `blocked` | Sandbox/write/operation/rollback readiness is checked with no runtime call. |
| `persisted_disabled_adapter_admission` | `blocked` + read model `available` | Disabled adapter evidence is persisted and read back as hash/count-only evidence. |

## Quantitative Targets

| Metric | Target |
|---|---:|
| Comparison variants | 3 |
| Dry-run stage coverage | 7/7 |
| Adapter admission persisted count | 1 |
| Adapter admission read-model record count | 1 |
| Adapter admission hash count | 1 |
| Corrupted/unavailable/wrong-schema store block coverage | 3/3 |
| Duplicate rollback partial row count | 0 |
| Execution permission count | 0 |
| Filesystem writes outside local SQLite evidence store | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |

## Implementation Files

- `packages/daacs_builder/target_runtime_admission_store.py`
- `packages/daacs_builder/__init__.py`
- `apps/api/agentic_workbench_api/services/target_runtime_admission.py`
- `apps/api/agentic_workbench_api/main.py`
- `examples/demo-service-flow/run_local_demo.py`
- `tests/unit/test_target_runtime_admission_store.py`
- `tests/smoke/test_daacs_runtime_preflight.py`
- `docs/evals/aw-daacs-runtime-02-persisted-adapter-admission-evidence.md`
- `docs/metrics.md`

## Non-Goals

- No DAACS runtime execution.
- No generated application delivery.
- No package install, server start, subprocess execution, or artifact file
  write.
- No provider/API/network call.
- No Solar Pro 3 call.
- No claim that the target runtime produced a runnable app.

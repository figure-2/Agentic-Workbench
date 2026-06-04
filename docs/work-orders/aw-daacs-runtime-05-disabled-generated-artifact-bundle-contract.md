# AW-DAACS-RUNTIME-05 Work Order: Disabled Generated Artifact Bundle Contract

## Summary

`AW-DAACS-RUNTIME-05` adds a disabled generated artifact bundle contract over
the persisted output manifest read model from `AW-DAACS-RUNTIME-04`.

This work is intentionally faster than the previous persistence-heavy steps:
it does not add another SQLite store. It adds a contract, API route, demo
comparison, tests, and eval/metrics documentation so the service-shaped demo can
move toward visible generated artifacts without opening DAACS runtime execution.

## Work Unit

```text
id: AW-DAACS-RUNTIME-05
depends_on:
  - AW-DAACS-RUNTIME-04
scope:
  Define a disabled generated artifact bundle contract over the persisted
  output manifest read model. Return only run_id, hashes, status, reason,
  artifact unit labels, counts, execution counters, and claim boundary.
risk_level: high
rollback_plan:
  Remove generated artifact bundle contract module, API route, demo flag,
  tests, eval document, metrics updates, and this work order. Return to
  AW-DAACS-RUNTIME-04 output manifest read-model behavior.
```

## 담당 관점

제품:
The demo needs to move faster toward the portfolio story. Show the future
"generated artifact bundle" stage now, but label it as disabled/no-call.

아키텍처:
Do not bypass runtime preflight, adapter admission, or output manifest evidence.
The bundle contract must depend on the persisted output manifest read model.

보안:
The bundle projection must not expose raw prompt, raw logs, raw file body,
runtime payload, provider payload, generated source, local root path, secret,
environment value, or executable output.

백엔드:
Add a narrow contract and API service. Do not create a new persistence adapter
for this step. Reuse the existing persisted output manifest read model as the
prerequisite.

테스트:
Cover successful disabled projection, missing read model, unavailable read
model, manifest hash mismatch, raw sentinel stripping, API route, demo
comparison, and zero-call counters.

문서/감사:
Record comparison experiment results and numeric metrics in eval/metrics docs.
Do not describe this as generated file output or runtime execution.

## Acceptance Tests

- output manifest read-model prerequisite count is `1`
- output manifest hash match count is `1`
- generated artifact bundle hash coverage is `1/1`
- artifact unit count is at least `3`
- artifact unit hash count is at least `3`
- generated artifact body writes remain `0`
- filesystem writes outside local SQLite evidence stores remain `0`
- subprocess calls remain `0`
- network calls remain `0`
- DAACS target runtime calls remain `0`
- public response raw prompt/log/body/provider/runtime payload exposure remains `0`

## Comparison Experiment

| Variant | Expected Status | Purpose |
|---|---|---|
| `dry_run_runner` | `passed` | Existing fixture path remains the only artifact-producing path. |
| `target_runtime_preflight` | `blocked` | Runtime sandbox policy is checked without execution. |
| `persisted_disabled_adapter_admission` | `blocked` + read-model `available` | Adapter admission evidence is durable and queryable. |
| `persisted_disabled_output_manifest` | `blocked` + read-model `available` | Future output manifest evidence is durable and queryable. |
| `disabled_generated_artifact_bundle` | `blocked` | Future generated artifact bundle shape is visible without file writes. |

## Target Metrics

| Metric | Target |
|---|---:|
| Comparison variants | 5 |
| Output manifest read-model prerequisite count | 1 |
| Output manifest hash match count | 1 |
| Generated artifact bundle hash coverage | 1/1 |
| Artifact unit count | 3 |
| Generated artifact body writes | 0 |
| DAACS target runtime calls | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |

## Next Recommended Work

`AW-DAACS-RUNTIME-06` should stop extending no-call gates and start a
fixture-backed local artifact materialization scaffold in a run-scoped
workspace. It should write only sanitized sample files under an allowlisted
workspace path, keep DAACS live runtime calls at `0`, and verify that the
generated artifact bundle can point to sanitized artifact records without
exposing file bodies.

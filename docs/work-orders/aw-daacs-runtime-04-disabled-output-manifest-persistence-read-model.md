# AW-DAACS-RUNTIME-04 Work Order: Disabled Output Manifest Persistence Read Model

## Summary

`AW-DAACS-RUNTIME-04` persists the disabled output manifest contract from
`AW-DAACS-RUNTIME-03` into a local SQLite evidence store and exposes a public
read model. The row and read model are hash/status/count-only.

This work does not generate files, write generated file bodies, run DAACS
target runtime code, spawn subprocesses, start servers, install packages, call
providers, or open network connections.

## Work Unit

```text
id: AW-DAACS-RUNTIME-04
depends_on:
  - AW-DAACS-RUNTIME-03
scope:
  Add a disabled output manifest persistence/read-model boundary. Persist only
  manifest hashes, status, reason, prerequisite hashes, counts, and zero-call
  counters. Expose API/demo read-model access by run_id.
risk_level: high
rollback_plan:
  Remove output manifest store module, API/demo persistence hook, tests, eval
  document, metrics updates, and this work order. Return to AW-DAACS-RUNTIME-03
  contract-only output manifest behavior.
```

## 담당 관점

제품:
The demo should show that output manifest evidence is durable and queryable
without implying the target runtime generated files.

아키텍처:
Keep output manifest evidence separate from canonical run/artifact rows and
adapter admission rows. Link by run_id and hashes only.

보안:
The SQLite row and read model must exclude raw prompt, raw logs, raw file body,
runtime payload, provider payload, generated source, local root path, secret,
environment value, and executable output.

백엔드:
Follow the existing `target_runtime_admission_store` pattern: schema validation,
unique hash constraint, transaction rollback, blocked read-model on bad stores.

테스트:
Cover record safety, SQLite row shape, duplicate rollback, bad store blocking,
API persistence/read, demo comparison, and zero-call counters.

문서/감사:
Record comparison experiment results and numeric metrics in eval/metrics docs.
Do not describe this as runtime execution or generated app success.

## Acceptance Tests

- output manifest row stores raw body/material count `0`
- `output_manifest_hash` unique constraint exists
- duplicate save leaves no extra partial row
- corrupted/unavailable/wrong-column store returns blocked read model
- API POST with configured store persists valid disabled manifest
- API GET returns hash/status/count read model by run_id
- fixture/dry-run path remains separate from runtime evidence
- generated artifact body writes remain `0`
- Solar Pro 3 calls remain `0`
- DAACS target runtime calls remain `0`
- public response raw prompt/log/body/provider/runtime payload exposure remains `0`

## Comparison Experiment

| Variant | Expected Status | Purpose |
|---|---|---|
| `dry_run_runner` | `passed` | Existing fixture path remains the only artifact-producing path. |
| `target_runtime_preflight` | `blocked` | Runtime sandbox policy is checked without execution. |
| `persisted_disabled_adapter_admission` | `blocked` + read-model `available` | Adapter admission evidence is durable and queryable. |
| `persisted_disabled_output_manifest` | `blocked` + read-model `available` | Future output manifest evidence is durable and queryable. |

## Target Metrics

| Metric | Target |
|---|---:|
| Comparison variants | 4 |
| Output manifest persisted count | 1 |
| Output manifest read-model record count | 1 |
| Output manifest hash count | 1 |
| Output group count | 3 |
| Generated artifact body writes | 0 |
| DAACS target runtime calls | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |

## Next Recommended Work

`AW-DAACS-RUNTIME-05` should define a disabled generated artifact bundle
contract over the persisted output manifest read model. It should still avoid
generated file bodies and keep execution permission `0`.

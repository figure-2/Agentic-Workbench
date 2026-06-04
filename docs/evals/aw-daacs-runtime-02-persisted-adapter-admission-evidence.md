# AW-DAACS-RUNTIME-02 Persisted Adapter Admission Evidence

## Summary

`AW-DAACS-RUNTIME-02` adds SQLite persistence and a public read model for the
disabled DAACS target runtime adapter admission result. The row stores only
hash/status/count evidence, and the read model exposes only hashes, status,
reason, counts, repository boundary flags, and zero-call execution counters.

This is not DAACS runtime execution and not a generated app result.

## Implemented Boundary

```text
dry-run RunnerPlan hash
-> target runtime sandbox preflight projection
-> disabled target runtime adapter admission
-> hash/status/count SQLite evidence row
-> public adapter admission read model
```

## Acceptance Evidence

| Acceptance | Result |
|---|---|
| disabled adapter admission can be persisted after valid preflight hash | covered |
| DB row stores no raw prompt/log/body/runtime/provider payload | covered |
| public read model exposes hash/status/count fields only | covered |
| duplicate adapter admission hash leaves partial row count at 0 | covered |
| corrupted/unavailable/wrong-schema stores are blocked | covered |
| API path can persist and read adapter admission evidence | covered |
| demo summary includes persistence and read-model counts | covered |
| execution permission remains 0 | covered |
| filesystem/subprocess/network/runtime calls remain 0 | covered |

## Quantitative Comparison

| Metric | Value |
|---|---:|
| Comparison variants | 3 |
| Dry-run fixture stage coverage | 7/7 |
| Dry-run fixture stage coverage percent | 100.0% |
| Target runtime preflight status | blocked |
| Disabled adapter admission status | blocked |
| Adapter admission persistence status | persisted |
| Adapter admission persisted count | 1 |
| Adapter admission read-model status | available |
| Adapter admission read-model record count | 1 |
| Adapter admission hash count | 1 |
| Store block fixtures, corrupted/unavailable/wrong-schema | 3/3 |
| Duplicate rollback partial row count | 0 |
| Execution permission count | 0 |
| Filesystem writes outside local SQLite evidence store | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 5 |
| Updated smoke tests | 4 |

| Comparison Variant | Status | Stage Coverage | Persisted Rows | Filesystem Writes | Subprocess Calls | Network Calls | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | 1 | 0 | 0 | 0 | 0 |

## Verification

| Command | Result |
|---|---:|
| `python -m pytest tests\unit\test_target_runtime_admission_store.py tests\unit\test_target_runtime_adapter_admission.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 16 passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py tests\unit\test_target_runtime_admission_store.py tests\unit\test_target_runtime_adapter_admission.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 19 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-02-demo --include-daacs-runtime-adapter-admission` | passed |
| `python -m compileall apps examples packages tests` | passed |
| `python -m pytest tests -q --color=no` | 612 passed |

## External Audit Notes

- Product: this makes the disabled runtime path inspectable in the local demo,
  but still does not claim generated app delivery.
- Architecture: adapter admission evidence now has a durable boundary separate
  from canonical run/artifact rows, approval/replay rows, and provider envelope
  rows.
- Security: SQLite rows and public read models exclude raw prompts, raw file
  bodies, runtime payloads, provider payloads, env values, SDK responses, local
  store roots, and raw database rows.
- Test: positive persistence, duplicate rollback, corrupted/unavailable store,
  wrong-schema store, API read model, and local demo comparison are covered.

## Claim Boundary

Allowed wording:

- "Disabled DAACS target runtime adapter admission evidence is persisted as
  hash/status/count rows."
- "The public read model can show adapter admission status and counts without
  raw payloads."
- "Target runtime execution remains closed."

Forbidden wording:

- "DAACS runtime generated an app."
- "The target runtime executed successfully."
- "Solar Pro 3 or DAACS live execution succeeded."
- "Production app generation is complete."

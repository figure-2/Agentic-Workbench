# AW-DAACS-RUNTIME-04 Disabled Output Manifest Persistence Read Model

## Summary

`AW-DAACS-RUNTIME-04` persists the disabled DAACS target runtime output
manifest from `AW-DAACS-RUNTIME-03` as a hash/status/count-only SQLite evidence
row and exposes a public read model.

This is not DAACS runtime execution and not a generated app result.

## Implemented Boundary

```text
dry-run RunnerPlan hash
-> target runtime sandbox preflight projection
-> disabled adapter admission
-> persisted adapter admission read model
-> disabled target runtime output manifest contract
-> persisted output manifest read model
```

## Acceptance Evidence

| Acceptance | Result |
|---|---|
| output manifest row stores hash/status/count only | covered |
| output_manifest_hash unique constraint prevents duplicates | covered |
| duplicate save leaves no extra partial row | covered |
| corrupted/unavailable/wrong-schema store returns blocked read model | covered |
| API POST persists valid disabled manifest when store is configured | covered |
| API GET returns output manifest read model by run_id | covered |
| demo comparison records persisted/read-model counts | covered |
| generated artifact body writes remain 0 | covered |
| filesystem writes outside local SQLite evidence stores remain 0 | covered |
| subprocess/network/target runtime calls remain 0 | covered |
| public projection raw exposure remains 0 | covered |

## Quantitative Comparison

| Metric | Value |
|---|---:|
| Comparison variants | 4 |
| Dry-run fixture stage coverage | 7/7 |
| Dry-run fixture stage coverage percent | 100.0% |
| Target runtime preflight status | blocked |
| Disabled adapter admission status | blocked |
| Adapter admission read-model status | available |
| Output manifest status | blocked |
| Output manifest persistence status | persisted |
| Output manifest read-model status | available |
| Output manifest persisted count | 1 |
| Output manifest read-model record count | 1 |
| Output manifest read-model hash count | 1 |
| Output group count | 3 |
| Output group hash count | 3 |
| Generated artifact body writes | 0 |
| Execution permission count | 0 |
| Filesystem writes outside local SQLite evidence stores | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| Bad SQLite store block cases | 3/3 |
| Duplicate partial extra rows | 0 |
| New unit tests | 5 |
| Updated smoke tests | 5 |

| Comparison Variant | Status | Stage Coverage | Persisted Rows | Read Model Hashes | Filesystem Writes | Subprocess Calls | Network Calls | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | 1 | 1 | 0 | 0 | 0 | 0 |
| `persisted_disabled_output_manifest` | blocked/read-model available | manifest-only | 1 | 1 | 0 | 0 | 0 | 0 |

## Verification

| Command | Result |
|---|---:|
| `python -m compileall apps examples packages tests` | passed |
| `python -m pytest tests\unit\test_target_runtime_output_manifest_store.py tests\unit\test_target_runtime_output_manifest.py tests\unit\test_target_runtime_admission_store.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 22 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-04-demo --include-daacs-runtime-output-manifest` | passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py tests\unit\test_target_runtime_output_manifest_store.py tests\unit\test_target_runtime_output_manifest.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 20 passed |

## External Audit Notes

- Product: reviewers can now see that the future output manifest evidence is
  durable and queryable, but the demo still does not claim generated files.
- Architecture: output manifest evidence is separate from canonical run
  artifacts and from adapter admission evidence. It is linked by run_id and
  hashes only.
- Security: SQLite rows and public read models exclude raw prompts, raw logs,
  raw file bodies, runtime payloads, provider payloads, generated source, local
  root paths, env values, and secrets.
- Test: persistence, duplicate rollback, bad store blocking, API read model,
  demo comparison, zero-call counters, and claim boundary are covered.

## Claim Boundary

Allowed wording:

- "Disabled output manifest evidence is persisted as hash/status/count rows."
- "The public read model shows output manifest hashes, status, reason, and
  counts."
- "Target runtime execution remains closed."

Forbidden wording:

- "DAACS runtime generated an app."
- "Generated application files were written."
- "The target runtime executed successfully."
- "Solar Pro 3 or DAACS live execution succeeded."
- "Production app generation is complete."

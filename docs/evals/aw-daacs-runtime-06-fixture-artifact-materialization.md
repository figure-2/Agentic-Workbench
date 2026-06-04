# AW-DAACS-RUNTIME-06 Fixture Artifact Materialization

## Summary

`AW-DAACS-RUNTIME-06` materializes sanitized fixture artifacts inside a
run-scoped local workspace after the disabled generated artifact bundle
boundary.

This is a local fixture materialization scaffold. It is not target-runtime
execution, not provider output, not a build result, and not a hosted app.
Public projections return only hashes, status, reason, counts, relative paths,
and claim-boundary fields.

## Implemented Boundary

```text
dry-run RunnerPlan hash
-> target runtime sandbox preflight projection
-> disabled adapter admission
-> persisted adapter admission read model
-> disabled target runtime output manifest contract
-> persisted output manifest read model
-> disabled generated artifact bundle contract
-> sanitized fixture artifact materialization
```

## Acceptance Evidence

| Acceptance | Result |
|---|---|
| generated artifact bundle projection is required | covered |
| generated artifact bundle hash must match projection | covered |
| unsafe run_id blocks materialization | covered |
| sanitized fixture artifacts are written under run-scoped workspace | covered |
| public projection exposes relative path/hash/count only | covered |
| local workspace root is not returned | covered |
| raw prompt/log/body/provider/runtime payload exposure remains 0 | covered |
| provider/subprocess/network/target runtime calls remain 0 | covered |
| API route returns public-safe materialization projection | covered |
| demo comparison records six variants | covered |

## Quantitative Comparison

| Metric | Value |
|---|---:|
| Comparison variants | 6 |
| Dry-run fixture stage coverage | 7/7 |
| Dry-run fixture stage coverage percent | 100.0% |
| Target runtime preflight status | blocked |
| Disabled adapter admission status | blocked |
| Adapter admission read-model status | available |
| Output manifest status | blocked |
| Output manifest read-model status | available |
| Generated artifact bundle status | blocked |
| Fixture materialization status | passed |
| Fixture materialization reason | target_runtime_fixture_artifacts_materialized |
| Generated artifact bundle hash match count | 1 |
| Fixture artifact record count | 3 |
| Fixture artifact content hash count | 3 |
| Fixture workspace file write count | 3 |
| Filesystem writes outside workspace | 0 |
| Public artifact body return count | 0 |
| Execution permission count | 0 |
| Provider calls | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 6 |
| Updated smoke tests | 7 |

| Comparison Variant | Status | Stage Coverage | Hash Evidence | Workspace Writes | Subprocess Calls | Network Calls | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | 1 | 0 | 0 | 0 | 0 |
| `persisted_disabled_output_manifest` | blocked/read-model available | manifest-only | 1 | 0 | 0 | 0 | 0 |
| `disabled_generated_artifact_bundle` | blocked | bundle-only | 1 | 0 | 0 | 0 | 0 |
| `fixture_artifact_materialization` | passed | fixture-only | 3 | 3 | 0 | 0 | 0 |

## Verification

| Command | Result |
|---|---:|
| `python -m pytest tests\unit\test_target_runtime_fixture_materialization.py -q --color=no` | 6 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 7 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-06-demo --include-daacs-runtime-fixture-materialization` | passed |
| `python -m compileall apps examples packages tests` | passed |
| `python -m pytest tests -q --color=no` | 640 passed |

## External Audit Notes

Product:
This is the first DAACS runtime-track step that creates visible local artifact
files, which is useful for portfolio review. It remains explicitly fixture
scoped.

Architecture:
Materialization is layered after the generated artifact bundle projection and
does not bypass runtime preflight, disabled adapter admission, or output
manifest evidence.

Security:
The workspace root is server-side configured and not returned publicly. Public
responses include relative paths and hashes only.

Testing:
The new unit tests cover success, missing prerequisite, hash mismatch, unsafe
run_id, raw sentinel stripping, and env/network/subprocess tripwires. Smoke
coverage includes API materialization and demo comparison.

## Claim Boundary

Allowed wording:

- "Sanitized fixture artifacts were written in a run-scoped local workspace."
- "The public projection returns relative paths, hashes, status, and counts."
- "Target runtime calls remain 0."

Forbidden wording:

- "DAACS target runtime produced the files."
- "The generated app was built or hosted."
- "The fixture artifacts contain public source bodies."
- "Solar Pro 3 or target runtime calls succeeded."

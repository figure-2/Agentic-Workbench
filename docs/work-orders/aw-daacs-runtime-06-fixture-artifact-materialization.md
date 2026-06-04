# AW-DAACS-RUNTIME-06 Work Order: Fixture Artifact Materialization

## Summary

`AW-DAACS-RUNTIME-06` moves the DAACS runtime track from hash-only bundle
evidence to portfolio-visible local fixture artifacts.

The implementation writes sanitized sample artifact files under a run-scoped
workspace. It still does not run the DAACS target runtime, call providers,
install packages, start servers, or expose file bodies in public projections.

## Work Unit

```text
id: AW-DAACS-RUNTIME-06
depends_on:
  - AW-DAACS-RUNTIME-05
scope:
  Materialize sanitized fixture artifacts inside a configured run-scoped
  workspace and return only relative paths, hashes, status, reason, counts,
  and claim-boundary fields.
risk_level: high
rollback_plan:
  Remove the fixture materialization module, API service/route, demo flag,
  tests, eval document, metrics updates, and this work order. Return to
  AW-DAACS-RUNTIME-05 disabled generated artifact bundle behavior.
```

## Specialist Review

Product:
The portfolio needs visible artifact shape, not more closed gates. This step
creates tangible local files while labeling them as fixture artifacts.

Architecture:
The materialization boundary must depend on `AW-DAACS-RUNTIME-05` generated
artifact bundle evidence. It must not bypass preflight, adapter admission,
output manifest, or bundle prerequisites.

Security:
Public API/demo projections must not include raw prompt, raw log, raw file
body, generated source body, local root path, provider payload, runtime
payload, env value, or secret.

Backend:
Use a server-side configured workspace root. Do not accept arbitrary public
workspace roots from the request payload.

Testing:
Cover successful fixture writes, missing bundle projection, bundle hash
mismatch, unsafe run_id, public redaction, side-effect tripwires, API route,
demo comparison, and path-boundary behavior.

Documentation:
Record comparison results and numeric metrics. Do not describe the fixture
files as target-runtime output.

## Acceptance Tests

- generated artifact bundle projection is required
- generated artifact bundle hash must match the projection
- sanitized fixture artifact record count is at least `3`
- artifact content hash count is at least `3`
- fixture workspace file write count is `3`
- filesystem writes outside the configured workspace remain `0`
- public response root path exposure remains `0`
- public response artifact body exposure remains `0`
- provider calls remain `0`
- subprocess calls remain `0`
- network calls remain `0`
- DAACS target runtime calls remain `0`

## Comparison Experiment

| Variant | Expected Status | Purpose |
|---|---|---|
| `dry_run_runner` | `passed` | Existing fixture service path remains the stable baseline. |
| `target_runtime_preflight` | `blocked` | Runtime sandbox policy is checked without execution. |
| `persisted_disabled_adapter_admission` | `blocked` + read-model `available` | Adapter admission evidence remains durable and queryable. |
| `persisted_disabled_output_manifest` | `blocked` + read-model `available` | Future output manifest evidence remains durable and queryable. |
| `disabled_generated_artifact_bundle` | `blocked` | Future bundle shape is visible without generated bodies. |
| `fixture_artifact_materialization` | `passed` | Sanitized fixture files are written under a run-scoped workspace. |

## Target Metrics

| Metric | Target |
|---|---:|
| Comparison variants | 6 |
| Fixture artifact records | 3 |
| Fixture content hashes | 3 |
| Fixture workspace file writes | 3 |
| Filesystem writes outside workspace | 0 |
| Public root path exposure | 0 |
| Public artifact body exposure | 0 |
| DAACS target runtime calls | 0 |
| Provider calls | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |

## Next Recommended Work

`AW-APP-01` should add a portfolio-facing artifact preview/read surface over
the public materialization projection. It should show artifact labels, relative
paths, hashes, and fixture status, while keeping raw file bodies and local root
paths hidden.

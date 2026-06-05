# AW-DAACS-RUNTIME-MVP-02 Document-Linked Codegen Eval

## Summary

AW-DAACS-RUNTIME-MVP-02 upgrades the restricted fixture app generation path
from a static skeleton to a document-linked codegen fixture. The generated app
still writes only inside a run-scoped workspace, but its public projection now
binds the codegen input to PlanningBlueprint, PRDPackage,
ImplementationBrief, and optional Solar draft projection hashes.

This is not uncontrolled DAACS target runtime execution. It does not call a
provider, read credentials, execute the original DAACS runtime, start a server,
or expose generated file bodies.

## Team Review

| Lens | Finding |
|---|---|
| Product | This moves the demo from "fixture files exist" to "document evidence drives generated app shape," which is the portfolio-critical story. |
| Architecture | The existing restricted workspace boundary remains the write boundary; the new `codegen_input_hash` is a public-safe contract over document hashes. |
| Security | Raw prompt text, provider response bodies, credentials, local root paths, and generated file bodies remain outside public projection. |
| Backend | API and local demo payloads now pass planning/PRD/Solar draft hash evidence into the generator. |
| Frontend | The generated `App.tsx` fixture includes task/status cards and a simple task board while preserving existing static validation markers. |
| Test | Unit and smoke coverage now assert document hash counts, codegen input hash presence, file counts, and zero-call counters. |
| External Audit | Claims remain fixture/local. There is no hosted app, production deployment, Solar-authored canonical artifact, or DAACS runtime execution claim. |

## Quantitative Results

| Metric | Result |
|---|---:|
| Representative scenario count | 1 |
| Generated app file records | 9 |
| Generated app file hashes | 9 |
| Required core files present | 3/3 |
| Codegen input hash count | 1 |
| Codegen input document hash count | 3 |
| PlanningBlueprint hash present count | 1 |
| PRDPackage hash present count | 1 |
| ImplementationBrief hash present count | 1 |
| Solar draft hash present count | 0 by default |
| Workspace writes | 9 |
| Workspace outside writes | 0 |
| Public file body returns | 0 |
| Public local root path returns | 0 |
| Provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Package install calls | 0 |
| Build calls | 0 |
| Server starts | 0 |
| DAACS target runtime calls | 0 |

## Comparison

| Variant | Status | Document hash count | Generated files | Provider calls | Runtime calls |
|---|---|---:|---:|---:|---:|
| MVP-01 static restricted fixture skeleton | passed | 1 | 9 | 0 | 0 |
| MVP-02 document-linked fixture codegen | passed | 3 | 9 | 0 | 0 |

Interpretation: MVP-02 increases document traceability without increasing
side effects. The output is still a local fixture app, but reviewers can now
trace the generated app projection back to the document chain.

## Public Projection

Public output may include:

- `planning_blueprint_hash`
- `prd_package_hash`
- `implementation_brief_hash`
- `solar_draft_projection_hash`
- `codegen_input_hash`
- `document_input_summary`
- generated file `workspace_relative_path`
- generated file `content_hash`
- generated file `byte_count`
- generated file `status`
- zero-call counters

Public output must not include:

- raw prompt text
- raw provider response body
- credential or environment value
- generated file body
- local root path
- raw command output

## Verification

```text
python -m compileall packages\daacs_builder\target_runtime_restricted_workspace_generation.py apps\api\agentic_workbench_api\services\target_runtime_restricted_workspace_generation.py examples\demo-service-flow\run_local_demo.py -q
passed

python -m pytest tests\unit\test_target_runtime_restricted_workspace_generation.py -q --color=no
9 passed

python -m pytest tests\unit\test_target_runtime_generated_artifact_verification.py tests\unit\test_target_runtime_generated_workspace_static_validation.py tests\unit\test_target_runtime_buildable_fixture_manifest.py tests\unit\test_target_runtime_local_build_preflight.py tests\unit\test_target_runtime_local_build_attempt.py -q --color=no
43 passed

python -m pytest tests\smoke\test_daacs_runtime_preflight.py::test_local_service_demo_generates_restricted_workspace_skeleton -q --color=no
1 passed

python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-mvp-02 --include-daacs-runtime-restricted-workspace-generation
status passed, codegen_input_hash_count 1, codegen_input_document_hash_count 3, generated file count 9, outside writes 0, provider calls 0, target runtime calls 0

python -m pytest tests -q --color=no
729 passed
```

## Claim Boundary

Allowed:

- Document-linked local fixture app files were generated.
- Generated file records are exposed as hash/path/count-only projection.
- Codegen input evidence is tied to fixture document hashes.

Not allowed:

- Claiming the original DAACS runtime executed.
- Claiming Solar generated the canonical app unless a reviewer-approved Solar
  draft path is explicitly present.
- Claiming hosted, production, or real-user deployment success.
- Returning generated file bodies through public APIs, docs, previews, or
  evidence.

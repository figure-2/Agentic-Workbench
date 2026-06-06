# AW-GENERATED-QUALITY-01 Portfolio Generated App Realism Eval

## Summary

`AW-GENERATED-QUALITY-01` improves the generated fixture app from a minimal
task board into a reviewer-facing workbench screen. The generated app now
includes workflow stages, artifact cards, runner plan, verification summary,
execution boundary counters, and a task board.

This remains a local fixture app. It does not open a new Solar call, execute the
DAACS target runtime, start a server by default, or claim hosted behavior.

## Team Review

Product lens: the previous portfolio package explained the pipeline, but the
generated app itself still looked too thin. This pass increases visible
portfolio value without expanding runtime risk.

Architecture lens: the change stays inside the existing restricted workspace
generation and static validation path. No new repository or API boundary was
added.

Frontend lens: the generated screen now uses a workbench layout with summary
metrics and distinct workflow, artifact, runner, verification, boundary, and
task sections.

Security lens: public outputs still expose only labels, status, counts, hashes,
relative paths, and byte counts. Generated file bodies remain local workspace
contents, not public projection payloads.

Testing lens: static validation now records app marker, API marker, and
verification/boundary marker counts. The portfolio command still performs only
the explicit local build attempt requested by the operator flag.

## Measured Result

Command:

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-generated-quality-01 --allow-local-build-attempt
```

| Metric | Value |
|---|---:|
| Portfolio command count | 1 |
| Stage coverage | 7/7 |
| Generated app file records | 9 |
| Generated app byte count | 11176 |
| Static files checked | 9 |
| Static file reads | 9 |
| App markers | 7/7 |
| API markers | 4/4 |
| Verification/boundary markers | 4/4 |
| Zero-call markers | 5/5 |
| Comparison variants | 13 |
| Local build status | passed |
| Local build command results | 2 |
| Package install attempts | 1 |
| Build attempts | 1 |
| Browser setup command attempts by default | 0 |
| Server starts | 0 |
| Provider calls | 0 |
| DAACS target runtime calls | 0 |
| Public raw body exposure | 0 |
| Public local root path exposure | 0 |

## Verification

| Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_restricted_workspace_generation.py packages\daacs_builder\target_runtime_generated_workspace_static_validation.py examples\demo-service-flow\run_local_demo.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_restricted_workspace_generation.py tests\unit\test_target_runtime_generated_workspace_static_validation.py tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py` | passed |
| `python -m pytest tests\unit\test_target_runtime_restricted_workspace_generation.py tests\unit\test_target_runtime_generated_workspace_static_validation.py tests\smoke\test_artifact_preview_surface.py -q --color=no` | 22 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py::test_daacs_runtime_restricted_workspace_generation_api_writes_app_skeleton tests\smoke\test_daacs_runtime_preflight.py::test_local_service_demo_statically_validates_generated_workspace -q --color=no` | 2 passed |
| `python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-generated-quality-01 --allow-local-build-attempt` | passed |
| `git diff --check` | passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no` | 3 passed |
| `python -m pytest tests\unit\test_target_runtime_restricted_workspace_generation.py tests\unit\test_target_runtime_generated_workspace_static_validation.py tests\smoke\test_daacs_runtime_preflight.py::test_daacs_runtime_restricted_workspace_generation_api_writes_app_skeleton tests\smoke\test_daacs_runtime_preflight.py::test_local_service_demo_statically_validates_generated_workspace tests\smoke\test_artifact_preview_surface.py tests\smoke\test_portfolio_demo_package.py -q --color=no` | 27 passed |
| `python -m pytest tests -q --color=no` | 740 passed in 238.93s |

## Interpretation

The generated app is now a stronger portfolio artifact because it shows a
complete workbench-style surface. The remaining visual gap is browser
screenshot evidence from the generated app, which requires an explicit browser
runtime setup decision in this environment.

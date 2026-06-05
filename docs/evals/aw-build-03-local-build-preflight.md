# AW-BUILD-03 Local Build Preflight Eval

## Summary

AW-BUILD-03 adds a local build preflight projection over the AW-BUILD-02
buildable fixture app manifest. It makes a future local package install/build
attempt reviewable, but it does not run package installation, build commands,
server start commands, provider calls, network calls, subprocess calls, or the
DAACS target runtime.

## Team Review

| Lens | Finding |
|---|---|
| Product | The preview now shows the generated app moving from build-ready candidate to local build preflight eligibility. |
| Architecture | The local build preflight is a separate projection boundary, so actual build execution can be added later behind explicit opt-in. |
| Security | Public output stays limited to hashes, labels, counts, status, reason, and zero-call counters. |
| Test | Unit, API smoke, demo smoke, and preview smoke cover the new path. |
| External audit | No evidence supports claiming local build success, server start, hosted behavior, Solar Pro 3 output, or DAACS runtime execution. |

## Quantitative Result

| Metric | Result |
|---|---:|
| Build preflight scenario count | 1 |
| Demo comparison variants | 11 |
| Stage coverage | 7/7 |
| Generated fixture app files | 9 |
| Buildable manifest required file reads | 5 |
| Local build command labels | 4 |
| Local build command hashes | 4 |
| Local build opt-in required count | 1 |
| Operator opt-in present by default | 0 |
| Execution permission count | 0 |
| Package installs | 0 |
| Builds | 0 |
| Server starts | 0 |
| Provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| DAACS target runtime calls | 0 |
| Dependency value returns | 0 |
| Public file body returns | 0 |
| Public local root path returns | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |

## Verification

| Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_local_build_preflight.py apps\api\agentic_workbench_api\services\target_runtime_local_build_preflight.py apps\api\agentic_workbench_api\main.py examples\demo-service-flow\run_local_demo.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_local_build_preflight.py tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py` | passed |
| `python -m pytest tests\unit\test_target_runtime_local_build_preflight.py tests\unit\test_target_runtime_buildable_fixture_manifest.py -q --color=no` | 17 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py -q --color=no` | 16 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-build-03-demo --include-daacs-runtime-local-build-preflight` | passed |
| `python examples\demo-service-flow\render_artifact_preview.py --store-root .local\aw-build-03-preview --output .local\aw-build-03-preview.html` | passed |
| `python -m pytest tests -q --color=no` | 701 passed |

## Claim Boundary

This eval supports these claims:

- The generated fixture app has a public local build preflight projection.
- The local build preflight is linked to the AW-BUILD-02 buildable manifest
  hash.
- The public preview shows command labels, opt-in requirement, and zero default
  execution counters.

This eval does not support these claims:

- Package installation succeeded.
- A local build succeeded.
- A dev server started.
- The generated app was hosted or deployed.
- Solar Pro 3 produced planner output.
- DAACS target runtime executed generated code.

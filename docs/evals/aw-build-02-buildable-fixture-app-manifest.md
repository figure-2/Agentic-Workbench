# AW-BUILD-02 Buildable Fixture App Manifest Eval

## Summary

AW-BUILD-02 converts the generated fixture app workspace from static shape
validation to a build-ready candidate manifest. It records package script
labels, dependency labels, required source-entry markers, hashes, counts, and
zero-call boundaries.

This eval does not claim package install success, build success, server start,
hosted behavior, Solar Pro 3 output, or DAACS target runtime execution.

## Team Review

| Lens | Finding |
|---|---|
| Product | This improves visible portfolio value faster than adding another no-call gate because reviewers can see a realistic React/Vite app candidate. |
| Architecture | The manifest is a separate service/API boundary after AW-BUILD-01 and reuses existing public projection patterns. |
| Security | Dependency values are validated locally but not returned publicly; only labels, counts, hashes, and status are exposed. |
| Backend | The demo path remains fixture-first and adds one optional buildable manifest endpoint. |
| Frontend | The fixture workspace now includes `index.html`, `src/main.tsx`, `vite.config.ts`, and `tsconfig.json` so the output resembles a conventional Vite app. |
| Test | Unit and smoke tests cover success, missing/mismatched prerequisites, invalid package JSON, placeholder dependency values, missing entry markers, public projection safety, and side-effect guards. |

## Quantitative Results

| Metric | Result |
|---|---:|
| Build-readiness scenarios | 1 |
| Demo comparison variants | 10 |
| Generated fixture files | 9 |
| Verified file records used | 9 |
| Static validation file reads | 9 |
| Build-ready required file reads | 5 |
| Required script labels | 4/4 |
| Dependency labels | 7 |
| Placeholder dependency values | 0 |
| Index entry markers | 2/2 |
| Main entrypoint markers | 2/2 |
| Vite config markers | 2/2 |
| TS config markers | 2/2 |
| Package manifest dependency values returned | 0 |
| Raw file content returns | 0 |
| Local root path returns | 0 |
| Provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Package installs | 0 |
| Builds | 0 |
| Server starts | 0 |
| DAACS target runtime calls | 0 |

## Verification

```text
python -m compileall packages\daacs_builder\target_runtime_restricted_workspace_generation.py packages\daacs_builder\target_runtime_buildable_fixture_manifest.py apps\api\agentic_workbench_api\services\target_runtime_buildable_fixture_manifest.py apps\api\agentic_workbench_api\main.py examples\demo-service-flow\run_local_demo.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_buildable_fixture_manifest.py tests\unit\test_target_runtime_restricted_workspace_generation.py tests\unit\test_target_runtime_generated_artifact_verification.py tests\unit\test_target_runtime_generated_workspace_static_validation.py tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py
passed

python -m pytest tests\unit\test_target_runtime_buildable_fixture_manifest.py tests\unit\test_target_runtime_restricted_workspace_generation.py tests\unit\test_target_runtime_generated_artifact_verification.py tests\unit\test_target_runtime_generated_workspace_static_validation.py -q --color=no
38 passed

python -m pytest tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py -q --color=no
14 passed

python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-build-02-demo --include-daacs-runtime-buildable-fixture-manifest
status passed, comparison_variant_count 10, buildable manifest passed, build_ready_candidate true, required file reads 5, script labels 4, dependency labels 7, package installs 0, builds 0, server starts 0

python examples\demo-service-flow\render_artifact_preview.py --store-root .local\aw-build-02-preview --output .local\aw-build-02-preview.html
preview HTML written
```

Full regression and whitespace checks are recorded in `docs/metrics.md`.

## Claim Boundary

Allowed:

- Claiming the generated fixture workspace has a build-ready candidate
  manifest.
- Claiming script labels, dependency labels, entry markers, hashes, and counts
  were verified locally.
- Claiming package installs, builds, server starts, provider calls, network
  calls, subprocess calls, and DAACS target runtime calls remained `0` in this
  eval.

Not allowed:

- Claiming `npm install` success.
- Claiming generated app build success.
- Claiming server start or hosted behavior.
- Claiming DAACS target runtime execution.
- Claiming Solar Pro 3 output.

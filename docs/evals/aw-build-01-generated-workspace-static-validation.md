# AW-BUILD-01 Generated Workspace Static Validation Eval

## Summary

AW-BUILD-01 adds a fast static validation boundary over the verified restricted
fixture app workspace. It validates the generated app skeleton shape without
running package install, build, server start, DAACS target runtime execution, or
provider calls.

The validation checks:

- `package.json` parses as JSON.
- required script labels exist: `dev`, `build`, `preview`, `verify`.
- `src/App.tsx` contains fixture app component markers.
- `src/api.ts` contains fixture API summary markers.
- `tests/verification.md` contains zero-call marker rows.
- public projection returns status, hashes, counts, and reasons only.

## Team Review

| Lens | Finding |
|---|---|
| Product | This improves portfolio value because the generated workspace is now checked for app shape, not only file presence. |
| Architecture | Static validation is a separate service/API boundary after AW-VERIFY-01 and reuses the existing workspace-provider pattern. |
| Security | File bodies are read locally for validation but are not returned in public API, preview, eval, or metrics. |
| Backend | API and demo wiring keep fixture mode as the default and add one optional static validation path. |
| Frontend | Preview now shows generated workspace static validation counts alongside file and hash verification. |
| Test | Unit tests cover success, missing hash, hash mismatch, unpassed verification, incomplete checks, invalid JSON, missing script, missing component marker, exposure, and side-effect guards. |

## Quantitative Results

| Metric | Result |
|---|---:|
| Static validation scenarios | 1 |
| Demo comparison variants | 9 |
| Verified file records used | 9 |
| Files statically checked | 9 |
| Static file reads | 9 |
| JSON parse checks | 1 |
| JSON parse passes | 1 |
| Required script labels | 4/4 |
| App component markers | 2/2 |
| API client markers | 2/2 |
| Zero-call report markers | 5/5 |
| Invalid package JSON blocked fixtures | 1 |
| Missing script blocked fixtures | 1 |
| Missing component marker blocked fixtures | 1 |
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
python -m compileall packages\daacs_builder\target_runtime_generated_workspace_static_validation.py apps\api\agentic_workbench_api\services\target_runtime_generated_workspace_static_validation.py apps\api\agentic_workbench_api\main.py examples\demo-service-flow\run_local_demo.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_generated_workspace_static_validation.py tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py
passed

python -m pytest tests\unit\test_target_runtime_generated_workspace_static_validation.py -q --color=no
10 passed

python -m pytest tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py -q --color=no
13 passed

python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-build-01-demo --include-daacs-runtime-generated-workspace-static-validation
status passed, comparison_variant_count 9, static validation passed, files checked 5, script labels 4, build calls 0

python examples\demo-service-flow\render_artifact_preview.py --store-root .local\aw-build-01-preview --output .local\aw-build-01-preview.html
preview HTML written

python -m pytest tests -q --color=no
681 passed

git diff --check
passed
```

Full regression and whitespace checks are also recorded in `docs/metrics.md`.

## Claim Boundary

Allowed:

- Claiming generated fixture workspace files passed local static validation.
- Claiming the public preview shows static validation counts.

Not allowed:

- Claiming package install success.
- Claiming generated app build success.
- Claiming server or hosted behavior.
- Claiming DAACS target runtime execution.
- Claiming Solar Pro 3 output.

# AW-GENERATED-E2E-01 Owner Filter Click-Path Eval

## Summary

`AW-GENERATED-E2E-01` verifies one real browser interaction in the generated
fixture app. The explicit screenshot-backed portfolio command now starts the
local preview server, opens the generated app in a browser path, clicks the
first non-`All` owner filter, and records only hash/count/status evidence.

This remains local fixture evidence. It does not claim hosted deployment,
production readiness, external provider success, or uncontrolled DAACS target
runtime execution.

## Team Review

Product lens: this moves the generated app from "visible" to "lightly
interactive," which is a stronger portfolio signal.

Frontend lens: stable `data-aw-owner-filter` and `data-aw-task-card` selectors
make the click path testable without relying on fragile text scraping.

Architecture lens: the change extends the existing local preview attempt
boundary rather than adding a new runtime/provider path.

Security lens: public evidence exposes click status, target label hash count,
before/after task counts, screenshot hash count, and cleanup counters only. It
does not return DOM text, screenshot paths, raw command output, local root
paths, provider payloads, or credentials.

QA lens: the default path remains opt-in gated. The measured path includes one
local preview server start/stop cycle and records cleanup `100.0%`.

## Measured Result

Command:

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-generated-e2e-01 --screenshot-backed
```

| Metric | Value |
|---|---:|
| Stage coverage | 7/7 |
| Generated fixture app file count | 9 |
| Local build status | passed |
| Local preview status | passed |
| Owner filter click status | passed |
| Owner filter click attempts | 1 |
| Owner filter click passes | 1 |
| Owner filter target label hash count | 1 |
| Task count before click | 3 |
| Task count after click | 1 |
| Changed task count | 2 |
| Screenshot evidence count | 1 |
| Screenshot hash count | 1 |
| Screenshot byte count | 143515 |
| Preview server starts/stops | 1/1 |
| Preview server cleanup percent | 100.0 |
| Provider calls | 0 |
| Solar additional calls | 0 |
| DAACS target runtime calls | 0 |
| Raw/public body exposure | 0 |
| Screenshot path exposure | 0 |
| Page text exposure | 0 |

## Verification

| Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_local_preview_attempt.py packages\daacs_builder\target_runtime_restricted_workspace_generation.py examples\demo-service-flow\run_portfolio_demo.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_local_preview_attempt.py tests\unit\test_target_runtime_restricted_workspace_generation.py tests\smoke\test_portfolio_demo_package.py` | passed |
| `python -m pytest tests\unit\test_target_runtime_local_preview_attempt.py tests\unit\test_target_runtime_restricted_workspace_generation.py tests\smoke\test_portfolio_demo_package.py -q --color=no` | 19 passed |
| `python -m pytest tests\unit\test_target_runtime_local_preview_attempt.py tests\unit\test_target_runtime_restricted_workspace_generation.py tests\smoke\test_portfolio_demo_package.py tests\unit\test_public_claim_projection_docs.py -q --color=no` | 22 passed |
| `python -m pytest tests\smoke\test_artifact_preview_surface.py -q --color=no` | 3 passed |
| `python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-generated-e2e-01 --screenshot-backed` | passed |
| `git diff --check` | passed |
| `python -m pytest tests -q --color=no` | 743 passed in 239.00s |

## Interpretation

The generated fixture app now has one verified interaction path. The next
portfolio step should expand from one click path to a reviewer-facing decision
flow or package the interaction evidence into the final demo narrative.

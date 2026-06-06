# AW-GENERATED-E2E-02 Reviewer Decision Click-Path Eval

## Summary

`AW-GENERATED-E2E-02` verifies a second browser interaction in the generated
fixture app. The screenshot-backed portfolio command now clicks the owner filter
and then clicks one reviewer decision control. Public evidence remains limited
to hash/count/status values.

This is local fixture/demo evidence only. It does not claim hosted deployment,
production readiness, external provider success, or uncontrolled DAACS target
runtime execution.

## Team Review

Product lens: this improves portfolio credibility because the generated app now
shows two meaningful user interactions instead of a static preview.

Frontend lens: stable `data-aw-reviewer-decision-*` selectors make the reviewer
decision path testable without scraping raw page text.

Architecture lens: the change extends the existing local preview attempt
boundary and reuses the existing screenshot-backed portfolio package path.

Security lens: public output exposes click status, target label hash count,
before/after state hash count, state changed count, screenshot hash count, and
cleanup counters only. It does not return DOM text, screenshot paths, raw
command output, local root paths, provider payloads, or credentials.

QA lens: the first command hit a local browser runtime probe timeout. The probe
was changed from `--dump-dom` to a Chrome DevTools Protocol readiness check,
matching the official headless Chrome remote debugging guidance. The final
measured command passed.

Official references checked after the browser probe issue:

- https://developer.chrome.com/docs/chromium/new-headless
- https://playwright.dev/python/docs/screenshots

## Measured Result

Command:

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --store-root .local\aw-generated-e2e-02-store --output-dir .local\aw-generated-e2e-02 --screenshot-backed
```

| Metric | Value |
|---|---:|
| Stage coverage | 7/7 |
| Generated fixture app file count | 9 |
| Local build status | passed |
| Local preview status | passed |
| Owner filter click status | passed |
| Owner filter click attempts/passes | 1/1 |
| Owner filter task count before/after | 3/1 |
| Reviewer decision click status | passed |
| Reviewer decision click attempts/passes | 1/1 |
| Reviewer decision target label hash count | 1 |
| Reviewer decision state hash count | 2 |
| Reviewer decision state changed count | 1 |
| Screenshot evidence count | 1 |
| Screenshot hash count | 1 |
| Screenshot byte count | 146487 |
| Preview server starts/stops | 1/1 |
| Preview server cleanup percent | 100.0 |
| Browser setup command attempts | 0 |
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
| `python -m pytest tests\unit\test_target_runtime_local_preview_attempt.py tests\unit\test_target_runtime_restricted_workspace_generation.py tests\smoke\test_portfolio_demo_package.py tests\unit\test_public_claim_projection_docs.py -q --color=no` | 23 passed |
| `python -m pytest tests\smoke\test_artifact_preview_surface.py -q --color=no` | 3 passed |
| `python examples\demo-service-flow\run_portfolio_demo.py --store-root .local\aw-generated-e2e-02-store --output-dir .local\aw-generated-e2e-02 --screenshot-backed` | passed |

## Interpretation

The generated fixture app now has two browser-verified interactions: owner
filter and reviewer decision. The next portfolio step should package both
interaction paths into the final demo narrative and keep raw UI/runtime evidence
out of public projections.

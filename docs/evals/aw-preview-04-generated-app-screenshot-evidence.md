# AW-PREVIEW-04 Generated App Screenshot Evidence Eval

## Summary

AW-PREVIEW-04 adds explicit opt-in browser screenshot evidence for the
generated fixture app. The implementation first probes Python Playwright, then
falls back to an installed system Chromium-family browser in headless mode when
Playwright is not installed. Public output remains hash/status/count-only.

Official references checked:

- Playwright Python getting started: https://playwright.dev/python/docs/intro
- Chrome headless mode: https://developer.chrome.com/docs/chromium/headless

## Team Review

Product lens: this closes the current portfolio evidence gap by moving from
generated files and static HTML to a real first-screen screenshot signal.

Frontend lens: the verified screen must include the generated workbench surface,
including workflow stages, artifact cards, runner plan, verification summary,
and task board sections.

Security lens: public evidence may include screenshot hash, byte count, status,
reason, and counters. It must not include screenshot paths, page text, raw
command output, local root paths, provider payloads, or credential material.

Operations lens: browser runtime setup remains explicit opt-in. In the measured
environment, setup was not needed because a system headless browser was already
available.

QA lens: the measured path records server start/stop cleanup, screenshot hash
count, screenshot byte count, and zero exposure findings.

## Measured Result

Command:

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-preview-04-system-browser --allow-local-build-attempt --allow-local-preview-attempt
```

| Metric | Value |
|---|---:|
| Representative scenario count | 1 |
| Stage coverage | 7/7 |
| Generated fixture app file count | 9 |
| Local build status | passed |
| Browser runtime available | 1 |
| Browser setup command attempts | 0 |
| Local preview status | passed |
| Preview server start attempts | 1 |
| Preview server starts | 1 |
| Preview server stops | 1 |
| Preview server cleanup percent | 100.0 |
| Screenshot capture status | verified |
| Screenshot evidence count | 1 |
| Screenshot hash count | 1 |
| Screenshot byte count | 53009 |
| Provider calls | 0 |
| Solar additional calls | 0 |
| DAACS target runtime calls | 0 |
| Raw/public body exposure findings | 0 |
| Screenshot path exposure findings | 0 |
| Page text exposure findings | 0 |

## Public Claim Boundary

This eval proves only that the local generated fixture app can be built,
started in a run-scoped preview attempt, and browser-verified with screenshot
hash evidence in this environment. It does not claim hosted deployment,
production readiness, external provider success, or uncontrolled DAACS target
runtime execution.

## Verification

| Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_local_preview_attempt.py examples\demo-service-flow\run_local_demo.py examples\demo-service-flow\run_portfolio_demo.py tests\unit\test_target_runtime_local_preview_attempt.py tests\smoke\test_portfolio_demo_package.py tests\smoke\test_daacs_runtime_preflight.py` | passed |
| `python -m pytest tests\unit\test_target_runtime_local_preview_attempt.py -q --color=no` | 5 passed |
| `python -m pytest tests\smoke\test_portfolio_demo_package.py tests\smoke\test_daacs_runtime_preflight.py::test_local_service_demo_retries_preview_when_browser_setup_makes_runtime_available -q --color=no` | 5 passed |
| `python -m pytest tests\smoke\test_artifact_preview_surface.py -q --color=no` | 3 passed |
| `python -m pytest tests\unit\test_target_runtime_local_preview_attempt.py tests\smoke\test_portfolio_demo_package.py tests\smoke\test_daacs_runtime_preflight.py::test_local_service_demo_retries_preview_when_browser_setup_makes_runtime_available tests\smoke\test_artifact_preview_surface.py tests\unit\test_public_claim_projection_docs.py -q --color=no` | 16 passed |
| `git diff --check` | passed |
| `python -m pytest tests -q --color=no` | 742 passed in 242.41s |

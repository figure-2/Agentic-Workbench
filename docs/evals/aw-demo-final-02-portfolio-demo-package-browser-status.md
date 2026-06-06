# AW-DEMO-FINAL-02 Portfolio Demo Package Browser Status Eval

## Summary

`AW-DEMO-FINAL-02` packages the current service-shaped demo into one
portfolio-facing local bundle. It writes a public-safe JSON summary and a
static HTML preview that includes document chain evidence, generated fixture app
files, local build evidence, local preview status, and browser runtime setup
status.

This eval records the measured local result. It does not claim hosted behavior,
provider outcome, Solar planner outcome, or DAACS target runtime outcome.

## Team Review

Product lens: the bundle improves reviewer comprehension because one command
now shows the document-to-app flow plus the current browser/setup status.

Architecture lens: the implementation reuses the existing public demo summary
and artifact preview model. No new repository layer was added.

Security lens: raw command output, file bodies, screenshot paths, page text,
local root paths, provider payloads, and credentials remain outside public
output.

Testing lens: targeted smoke tests cover bundle generation, CLI output, local
build opt-in, browser setup default blocking, and public projection safety.

## Measured Result

Command:

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-demo-final-02 --allow-local-build-attempt
```

| Metric | Value |
|---|---:|
| Portfolio command count | 1 |
| Summary JSON generated | 1 |
| Static HTML preview generated | 1 |
| Stage coverage | 7/7 |
| Stage coverage percent | 100.0 |
| Generated fixture app files | 9 |
| Local build status | passed |
| Local build command results | 2 |
| Package install attempts | 1 |
| Build attempts | 1 |
| Local preview status | blocked |
| Local preview reason | local_preview_opt_in_required |
| Browser setup status | blocked |
| Browser setup reason | browser_runtime_setup_opt_in_required |
| Browser setup preflight count | 1 |
| Browser setup command attempts | 0 |
| Browser setup default command executions | 0 |
| Screenshot evidence count | 0 |
| Screenshot hash count | 0 |
| Screenshot byte count | 0 |
| Server starts | 0 |
| Provider calls | 0 |
| DAACS target runtime calls | 0 |
| Public raw body exposure | 0 |
| Public local root path exposure | 0 |
| Screenshot path exposure | 0 |
| Page text exposure | 0 |
| Public claim drift findings | 0 |

## Verification

| Command | Result |
|---|---:|
| `python -m compileall examples\demo-service-flow\run_portfolio_demo.py examples\demo-service-flow\render_artifact_preview.py tests\smoke\test_portfolio_demo_package.py` | passed |
| `python -m pytest tests\smoke\test_portfolio_demo_package.py -q --color=no` | 3 passed |
| `python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-demo-final-02 --allow-local-build-attempt` | passed |
| `python -m pytest tests -q --color=no` | 740 passed in 239.36s |

## Interpretation

`AW-DEMO-FINAL-02` is a portfolio packaging improvement, not a new runtime
execution path. The bundle is useful for review now, and it keeps the next
engineering choice explicit: improve generated app quality, or opt into browser
runtime setup for screenshot evidence.

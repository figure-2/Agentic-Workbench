# AW-DEMO-FINAL-01 Portfolio Demo Package Eval

## Summary

AW-DEMO-FINAL-01 packages the service-shaped local demo into one
reviewer-facing command. The command writes a sanitized JSON summary and static
HTML preview, and it can include the AW-BUILD-04 local fixture app build-attempt
evidence when explicit opt-in is provided.

This eval supports only local fixture/demo evidence. It does not claim hosted
behavior, server start, Solar Pro 3 output, external provider output, or DAACS
target runtime execution.

## Team Review

| Lens | Finding |
|---|---|
| Product | This is the first reviewer-friendly package: one command produces a summary and preview that show the full local workflow and fixture app build evidence. |
| Architecture | The wrapper reuses existing public demo and preview boundaries instead of adding new persistence or execution paths. |
| Security | Public report output contains file names, counts, hashes/status summaries, and booleans only; local root paths and raw bodies stay out. |
| Frontend | The static preview is the visible portfolio surface for the current stage. |
| Test | Smoke tests cover default blocked build path, CLI output, and opt-in local build attempt. |
| External audit | The evidence is suitable for portfolio-local review, not for hosted or runtime/provider success claims. |

## Quantitative Result

| Metric | Result |
|---|---:|
| Portfolio demo scenario count | 1 |
| Portfolio command count | 1 |
| Stage coverage | 7/7 |
| Stage coverage percent | 100.0 |
| Summary JSON generated | 1 |
| Preview HTML generated | 1 |
| Generated fixture app files | 9 |
| Local build attempt evidence records | 1 |
| Local build attempt status | passed |
| Local build command results | 2 |
| Package install attempts | 1 |
| Build attempts | 1 |
| Server starts | 0 |
| Provider calls | 0 |
| DAACS target runtime calls | 0 |
| Public raw body exposure | 0 |
| Public local root path exposure | 0 |
| Public claim drift findings | 0 |
| New smoke tests | 3 |

## Manual Command Result

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-demo-final-01 --allow-local-build-attempt
```

Result:

```text
status passed
summary_json aw-demo-final-01-summary.json
preview_html aw-demo-final-01-preview.html
stage coverage 7/7
generated fixture app files 9
local build attempt passed
package install attempts 1
build attempts 1
server starts 0
provider calls 0
DAACS target runtime calls 0
raw public body exposure 0
local root path exposure 0
```

## Verification

| Command | Result |
|---|---:|
| `python -m compileall examples\demo-service-flow\run_portfolio_demo.py tests\smoke\test_portfolio_demo_package.py` | passed |
| `python -m pytest tests\smoke\test_portfolio_demo_package.py -q --color=no` | 3 passed |
| `python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-demo-final-01 --allow-local-build-attempt` | passed |
| `python -m pytest tests\smoke\test_portfolio_demo_package.py tests\unit\test_public_claim_projection_docs.py -q --color=no` | 6 passed |
| `python -m pytest tests -q --color=no` | 713 passed |
| `git diff --check` | passed |

Full regression and whitespace checks are recorded in `docs/metrics.md`.

## Claim Boundary

Allowed:

- Claiming a one-command local portfolio demo package exists.
- Claiming the command writes a sanitized JSON summary and static HTML preview.
- Claiming the local fixture app build attempt passed in the measured local
  environment when explicit opt-in was provided.

Not allowed:

- Claiming hosted behavior.
- Claiming a server was started.
- Claiming Solar Pro 3 output.
- Claiming external provider output.
- Claiming DAACS target runtime execution.
- Claiming raw file body, raw command output, local root path, dependency
  value, or secret exposure.

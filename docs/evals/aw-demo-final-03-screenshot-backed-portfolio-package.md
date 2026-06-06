# AW-DEMO-FINAL-03 Screenshot-Backed Portfolio Package Eval

## Summary

`AW-DEMO-FINAL-03` packages the local service-shaped demo, generated fixture app
build evidence, browser preview verification, and screenshot evidence status
behind one explicit command.

This is still a local portfolio package. It does not claim hosted deployment,
production readiness, external provider success, or uncontrolled DAACS target
runtime execution.

## Team Review

Product lens: the package now gives a reviewer one command that reaches
document output, generated app files, local build evidence, and screenshot hash
evidence.

Architecture lens: the implementation reuses the existing public demo summary
and static artifact preview. No new persistence layer or live runtime path was
added.

Security lens: screenshot path, page text, raw command output, local root path,
provider payload, and credential material remain outside the public report.

Frontend lens: the HTML preview now includes a dedicated
`Screenshot-Backed Portfolio Evidence` section with capture status, reason,
hash count, byte count, cleanup percentage, and exposure flags.

QA lens: the command is explicit. `--screenshot-backed` enables local build and
local preview verification; browser runtime setup still requires its own
separate flag.

## Measured Result

Command:

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-demo-final-03 --screenshot-backed
```

| Metric | Value |
|---|---:|
| Portfolio command count | 1 |
| Summary JSON generated | 1 |
| Static HTML preview generated | 1 |
| Stage coverage | 7/7 |
| Generated fixture app files | 9 |
| Local build status | passed |
| Package install attempts | 1 |
| Build attempts | 1 |
| Local preview status | passed |
| Browser runtime available | 1 |
| Browser setup command attempts | 0 |
| Preview server start attempts | 1 |
| Preview server starts | 1 |
| Preview server stops | 1 |
| Preview server cleanup percent | 100.0 |
| Screenshot capture status | verified |
| Screenshot evidence count | 1 |
| Screenshot hash count | 1 |
| Screenshot byte count | 52645 |
| Server starts | 1 |
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
| `python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-demo-final-03 --screenshot-backed` | passed |
| `python -m compileall examples\demo-service-flow\run_portfolio_demo.py examples\demo-service-flow\render_artifact_preview.py tests\smoke\test_portfolio_demo_package.py tests\smoke\test_artifact_preview_surface.py` | passed |
| `python -m pytest tests\smoke\test_portfolio_demo_package.py tests\smoke\test_artifact_preview_surface.py tests\unit\test_public_claim_projection_docs.py -q --color=no` | 10 passed |
| `git diff --check` | passed |
| `python -m pytest tests -q --color=no` | 742 passed in 245.38s |

## Interpretation

`AW-DEMO-FINAL-03` is the first package where a reviewer can see the whole
portfolio chain and a browser screenshot evidence status together. It is not a
hosted app demo, and it does not use Solar or DAACS live runtime calls.

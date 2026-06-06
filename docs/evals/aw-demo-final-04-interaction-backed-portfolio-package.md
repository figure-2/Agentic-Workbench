# AW-DEMO-FINAL-04 Interaction-Backed Portfolio Package Eval

## Summary

`AW-DEMO-FINAL-04` packages the local service-shaped demo, generated fixture app
files, local build evidence, browser screenshot evidence, owner filter click
evidence, and reviewer decision click evidence into one public-safe portfolio
report.

This is local fixture/demo evidence only. It does not claim hosted deployment,
production readiness, external provider success, or uncontrolled DAACS target
runtime execution.

## Team Review

Product lens: the package now gives a reviewer one command and one summary that
show the document-to-app chain plus two meaningful browser interaction paths.

Architecture lens: the implementation reuses the existing public demo summary,
static preview, and local preview attempt evidence. No persistence layer,
provider path, or target runtime path was added.

Security lens: public output exposes status, hashes, counts, and reasons only.
It does not return DOM text, page text, screenshot paths, command output bodies,
local root paths, provider output, or credential material.

Frontend lens: the preview now labels the combined section as
`Interaction-Backed Portfolio Evidence`, making the owner filter and reviewer
decision checks visible in the same screen as screenshot evidence.

QA lens: the command is explicit. `--screenshot-backed` enables one local build
attempt and one local preview/browser verification attempt; browser runtime
setup commands still require a separate opt-in.

## Measured Result

Command:

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --store-root .local\aw-demo-final-04-store --output-dir .local\aw-demo-final-04 --screenshot-backed
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
| Preview server starts/stops | 1/1 |
| Preview server cleanup percent | 100.0 |
| Screenshot capture status | verified |
| Screenshot evidence count | 1 |
| Screenshot hash count | 1 |
| Screenshot byte count | 146583 |
| Owner filter click status | passed |
| Owner filter click attempts/passes | 1/1 |
| Owner filter task count before/after | 3/1 |
| Reviewer decision click status | passed |
| Reviewer decision click attempts/passes | 1/1 |
| Reviewer decision target label hash count | 1 |
| Reviewer decision state hash count | 2 |
| Reviewer decision state changed count | 1 |
| Interaction package status | verified |
| Interaction package hash count | 1 |
| Interaction paths verified | 2/2 |
| Interaction hash evidence count | 4 |
| Interaction DOM text exposure | 0 |
| Interaction event exposure | 0 |
| Provider calls | 0 |
| Solar additional calls | 0 |
| DAACS target runtime calls | 0 |
| Public raw body exposure | 0 |
| Screenshot path exposure | 0 |
| Page text exposure | 0 |

## Verification

| Command | Result |
|---|---:|
| `python -m compileall examples\demo-service-flow\run_portfolio_demo.py examples\demo-service-flow\render_artifact_preview.py tests\smoke\test_portfolio_demo_package.py tests\smoke\test_artifact_preview_surface.py` | passed |
| `python -m pytest tests\smoke\test_portfolio_demo_package.py tests\smoke\test_artifact_preview_surface.py tests\unit\test_public_claim_projection_docs.py -q --color=no` | 10 passed |
| `python examples\demo-service-flow\run_portfolio_demo.py --store-root .local\aw-demo-final-04-store --output-dir .local\aw-demo-final-04 --screenshot-backed` | passed |
| `git diff --check` | passed |
| `python -m pytest tests -q --color=no` | 744 passed in 386.24s |

## Interpretation

`AW-DEMO-FINAL-04` is the current portfolio package baseline. It shows the
document chain, generated fixture app, local build, browser screenshot, owner
filter interaction, and reviewer decision interaction as one local evidence
package while keeping live provider and uncontrolled runtime calls closed.

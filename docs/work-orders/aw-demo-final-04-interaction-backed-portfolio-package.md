# AW-DEMO-FINAL-04 Interaction-Backed Portfolio Package

## Summary

```text
id: AW-DEMO-FINAL-04
depends_on:
  - AW-DEMO-FINAL-03
  - AW-GENERATED-E2E-01
  - AW-GENERATED-E2E-02
scope:
  Package the screenshot-backed portfolio demo with both verified interaction
  paths: owner filter and reviewer decision. Keep the package local, fixture
  backed, and public-safe.
risk_level: medium
rollback_plan:
  Remove interaction-backed portfolio report/readme/docs changes and keep
  AW-DEMO-FINAL-03 plus AW-GENERATED-E2E-01/02 evidence as separate artifacts.
```

## Goal

Make the portfolio demo easier for a first-time reviewer to understand:

```text
Idea
-> SoT/PRD/ImplementationBrief
-> Generated fixture app files
-> Local build evidence
-> Browser screenshot evidence
-> Owner filter click evidence
-> Reviewer decision click evidence
```

## Acceptance Tests

- One command writes sanitized JSON summary and static HTML preview.
- Portfolio report includes owner filter click status/count/hash metrics.
- Portfolio report includes reviewer decision click status/count/hash metrics.
- Screenshot evidence count and screenshot hash count are present.
- Preview server start/stop cleanup remains `100.0%` when preview passes.
- Public report returns raw DOM text count `0`.
- Public report returns screenshot path count `0`.
- Public report returns local root path count `0`.
- Provider/Solar additional calls remain `0`.
- DAACS uncontrolled target runtime calls remain `0`.
- README and metrics record measured numeric values.

## Implementation Notes

- Do not add a new persistence layer.
- Do not add a new browser action unless it improves the portfolio narrative.
- Reuse `run_portfolio_demo.py` and `render_artifact_preview.py`.
- Keep local artifacts under `.local` and out of Git tracking.
- If browser runtime is unavailable, report `environment_blocked` with counts
  rather than claiming screenshot success.

## Suggested Verification

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-demo-final-04 --screenshot-backed
python -m pytest tests\smoke\test_portfolio_demo_package.py tests\smoke\test_artifact_preview_surface.py tests\unit\test_public_claim_projection_docs.py -q --color=no
python -m pytest tests -q --color=no
git diff --check
```

## Completion Evidence

Implemented as the current `run_portfolio_demo.py` package baseline.

Measured command:

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --store-root .local\aw-demo-final-04-store --output-dir .local\aw-demo-final-04 --screenshot-backed
```

Measured counts:

| Metric | Value |
|---|---:|
| Package status | verified |
| Stage coverage | 7/7 |
| Generated fixture app files | 9 |
| Local build status | passed |
| Local preview status | passed |
| Screenshot evidence/hash count | 1/1 |
| Screenshot byte count | 146583 |
| Owner filter click attempts/passes | 1/1 |
| Reviewer decision click attempts/passes | 1/1 |
| Interaction paths verified | 2/2 |
| Interaction hash evidence count | 4 |
| Preview server starts/stops | 1/1 |
| Preview server cleanup percent | 100.0 |
| Provider calls | 0 |
| DAACS target runtime calls | 0 |
| DOM text / event exposure | 0 / 0 |
| Screenshot path / page text exposure | 0 / 0 |

Verification:

| Command | Result |
|---|---:|
| `python -m compileall examples\demo-service-flow\run_portfolio_demo.py examples\demo-service-flow\render_artifact_preview.py tests\smoke\test_portfolio_demo_package.py tests\smoke\test_artifact_preview_surface.py` | passed |
| `python -m pytest tests\smoke\test_portfolio_demo_package.py tests\smoke\test_artifact_preview_surface.py tests\unit\test_public_claim_projection_docs.py -q --color=no` | 10 passed |
| `git diff --check` | passed |
| `python -m pytest tests -q --color=no` | 744 passed in 386.24s |

No live provider call, Solar additional call, hosted deployment, or
uncontrolled DAACS target runtime execution was added.

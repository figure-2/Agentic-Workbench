# Portfolio Evidence Index

## Purpose

This index gives a first-time reviewer the shortest verified path through the
current Agentic Workbench portfolio baseline.

The current baseline is `AW-DEMO-FINAL-04`: a local, interaction-backed demo
package. It is not a hosted deployment, production service, external provider
success claim, or uncontrolled DAACS target runtime execution.

## One Command

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-demo-final-04 --screenshot-backed
```

Expected local outputs:

```text
aw-demo-final-04-summary.json
aw-demo-final-04-preview.html
```

The output directory is local development evidence and must remain untracked.

## Evidence Map

| Area | Current evidence | Measured value |
|---|---|---:|
| Workflow coverage | Required stages covered | 7/7 |
| Document chain | Idea -> SoT/PRD/ImplementationBrief present in public summary | covered |
| Generated app | Fixture app files written under run-scoped workspace | 9 |
| Local build | Explicit opt-in package/build attempt | passed |
| Browser preview | Explicit opt-in preview-server/browser attempt | passed |
| Screenshot | Screenshot evidence/hash count | 1/1 |
| Owner interaction | Owner filter click attempts/passes | 1/1 |
| Reviewer interaction | Reviewer decision click attempts/passes | 1/1 |
| Interaction package | Verified interaction paths | 2/2 |
| Interaction package | Hash evidence count | 4 |
| Cleanup | Preview server starts/stops | 1/1 |
| Cleanup | Preview server cleanup percent | 100.0 |
| Test suite | Full local test suite | 744 passed |

## Boundary Evidence

| Boundary | Current value |
|---|---:|
| External provider calls in AW-DEMO-FINAL-04 package | 0 |
| Solar additional calls in AW-DEMO-FINAL-04 package | 0 |
| DAACS uncontrolled target runtime calls | 0 |
| Public raw body exposure | 0 |
| Local root path exposure | 0 |
| Screenshot path exposure | 0 |
| Page text exposure | 0 |
| Interaction DOM text exposure | 0 |
| Interaction event exposure | 0 |

## Source Identity Mapping

The integration target is one service-shaped workflow, not a direct runtime copy
of either reference project.

| Reference identity | Preserved in this project as |
|---|---|
| DIV-style planning | Idea structuring, planning blueprint, PRD-style package, evidence labels, visual/product intent |
| DAACS-style implementation | Build spec, backend/frontend/API split, runner plan, verification report, generated workspace, build and browser evidence |

## Public Claim Boundary

Allowed claims:

- Local AI agent workflow harness prototype.
- Service-shaped local demo over sanitized public projections.
- Fixture-backed generated app files with local build and browser evidence.
- Two verified browser interaction paths represented by status/hash/count only.

Not claimed:

- Hosted app success.
- Production readiness.
- External provider quality benchmark.
- Uncontrolled DAACS target runtime execution.
- Raw provider response, raw prompt, raw DOM text, screenshot path, or local
  root path publication.

## Linked Evidence

- Eval: [docs/evals/aw-demo-final-04-interaction-backed-portfolio-package.md](evals/aw-demo-final-04-interaction-backed-portfolio-package.md)
- Publish gate: [docs/evals/aw-portfolio-release-03-github-publish-gate.md](evals/aw-portfolio-release-03-github-publish-gate.md)
- Push verification: [docs/evals/aw-portfolio-release-04-github-push-post-push-verification.md](evals/aw-portfolio-release-04-github-push-post-push-verification.md)
- Recruiter walkthrough: [docs/recruiter-walkthrough.md](recruiter-walkthrough.md)
- Public visibility: [docs/evals/aw-portfolio-release-06-public-visibility-execution.md](evals/aw-portfolio-release-06-public-visibility-execution.md)
- Metrics: [docs/metrics.md](metrics.md)
- Work order: [docs/work-orders/aw-demo-final-04-interaction-backed-portfolio-package.md](work-orders/aw-demo-final-04-interaction-backed-portfolio-package.md)
- Release work order: [docs/work-orders/aw-portfolio-release-01-recruiter-ready-repo-package.md](work-orders/aw-portfolio-release-01-recruiter-ready-repo-package.md)

## Verification Record

Latest recorded verification:

| Command | Result |
|---|---:|
| `python examples\demo-service-flow\run_portfolio_demo.py --store-root .local\aw-demo-final-04-store --output-dir .local\aw-demo-final-04 --screenshot-backed` | passed |
| `python -m pytest tests\smoke\test_portfolio_demo_package.py tests\smoke\test_artifact_preview_surface.py tests\unit\test_public_claim_projection_docs.py -q --color=no` | 10 passed |
| `python -m pytest tests -q --color=no` | 744 passed in 386.24s |
| `git diff --check` | passed |

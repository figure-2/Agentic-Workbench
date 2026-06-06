# AW-PORTFOLIO-RELEASE-01 Recruiter-Ready Repo Package Eval

## Summary

`AW-PORTFOLIO-RELEASE-01` makes the repository easier to review from GitHub by
adding a top-level portfolio snapshot, a current demo command, a public evidence
index, and explicit local/fixture claim boundaries.

This is documentation and release packaging work. It does not add a provider
call, hosted deployment, or uncontrolled DAACS target runtime execution.

## Team Review

Product lens: the README now explains the project as a portfolio-visible
workflow: idea to document artifacts, generated fixture app, build evidence,
browser screenshot, and two interaction checks.

Architecture lens: the release package links to existing AW-DEMO-FINAL-04
evidence instead of adding a new runtime path.

Security lens: `.local` output remains local evidence and is not part of the
tracked repository. Public docs list status/count/hash evidence only.

QA lens: the package records the current full test result and the current demo
baseline without claiming unexecuted live behavior.

## Measured Result

| Metric | Value |
|---|---:|
| README portfolio snapshot | added |
| Current demo command in README | 1 |
| Evidence index | added |
| Evidence index linked from README | 1 |
| AW-DEMO-FINAL-04 eval linked | 1 |
| Metrics linked | 1 |
| Stage coverage recorded | 7/7 |
| Generated fixture app files recorded | 9 |
| Local build status recorded | passed |
| Screenshot evidence/hash count recorded | 1/1 |
| Owner filter click status recorded | passed |
| Reviewer decision click status recorded | passed |
| Verified interaction paths recorded | 2/2 |
| Full test result recorded | 744 passed |
| Provider calls in package | 0 |
| Solar additional calls in package | 0 |
| DAACS uncontrolled target runtime calls | 0 |
| `.local` tracked output findings | 0 |

## Verification

| Command | Result |
|---|---:|
| `python examples\demo-service-flow\run_portfolio_demo.py --store-root .local\aw-demo-final-04-store --output-dir .local\aw-demo-final-04 --screenshot-backed` | passed |
| `python -m pytest tests -q --color=no` | 744 passed in 386.24s |
| `git diff --check` | passed |

## Interpretation

The project now has a clearer GitHub-facing review path. The next step is a
source-control handoff: decide whether to commit the accumulated portfolio
baseline and push it, or split the commit first.

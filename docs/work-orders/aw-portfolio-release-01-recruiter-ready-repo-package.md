# AW-PORTFOLIO-RELEASE-01 Recruiter-Ready Repo Package

## Summary

```text
id: AW-PORTFOLIO-RELEASE-01
depends_on:
  - AW-DEMO-FINAL-04
scope:
  Make the repository reviewable by a first-time portfolio reviewer. Consolidate
  the current interaction-backed local demo baseline into a clear README,
  evidence index, verification record, and clean handoff state.
risk_level: medium
rollback_plan:
  Remove recruiter-facing README/evidence-index updates and keep
  AW-DEMO-FINAL-04 code, eval, and metrics as the latest functional baseline.
```

## Goal

A reviewer should understand the project in under five minutes:

```text
What it is
-> what original identities it integrates
-> how to run the local demo
-> what evidence is real local execution
-> what remains fixture/mock/live-closed
-> which tests passed
```

## Acceptance Tests

- README top section explains the product in portfolio language, not internal
  gate names only.
- README includes one current command:
  `python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-demo-final-04 --screenshot-backed`.
- README links to AW-DEMO-FINAL-04 eval and metrics.
- Evidence index lists stage coverage, generated app files, build status,
  screenshot evidence, owner filter click, reviewer decision click, and zero
  live/runtime calls.
- Claim boundary states local fixture/demo, not hosted or production.
- Git status check confirms local `.local` outputs remain untracked.
- Full test suite result is recorded.
- If a commit is requested, commit message uses:
  `feat: package interaction-backed portfolio demo`.

## Out Of Scope

- Hosted deployment.
- New Solar live call.
- New DAACS uncontrolled runtime execution.
- New generated-app feature work.
- Tracking `.local` output files.

## Suggested Verification

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --store-root .local\aw-demo-final-04-store --output-dir .local\aw-demo-final-04 --screenshot-backed
python -m pytest tests -q --color=no
git diff --check
git status --short --branch
```

## Team Decision

Product lens: the current feature baseline is portfolio-visible enough. The
next highest value is making the repository easy to understand and evaluate.

Architecture lens: do not add more runtime paths before the current baseline is
cleanly packaged.

Security lens: keep `.local`, raw command output, screenshot paths, page text,
provider output, and credentials out of tracked files.

QA lens: record the full test count and demo command result in the handoff
notes. Do not claim a test or live path that was not executed.

## Completion Evidence

Implemented as README/evidence-index/eval/metrics packaging work over the
current `AW-DEMO-FINAL-04` baseline.

Changed public review surfaces:

| Surface | Status |
|---|---:|
| README portfolio snapshot | added |
| Current one-command demo path | added |
| Evidence index | added |
| AW-DEMO-FINAL-04 eval link | added |
| Metrics link | added |
| Local/fixture claim boundary | recorded |

Recorded baseline:

| Metric | Value |
|---|---:|
| Stage coverage | 7/7 |
| Generated fixture app files | 9 |
| Local build status | passed |
| Screenshot evidence/hash count | 1/1 |
| Owner filter click status | passed |
| Reviewer decision click status | passed |
| Verified interaction paths | 2/2 |
| Full test suite | 744 passed |
| Provider calls in package | 0 |
| Solar additional calls in package | 0 |
| DAACS uncontrolled target runtime calls | 0 |
| `.local` tracked output findings | 0 |

Verification:

| Command | Result |
|---|---:|
| `python examples\demo-service-flow\run_portfolio_demo.py --store-root .local\aw-demo-final-04-store --output-dir .local\aw-demo-final-04 --screenshot-backed` | passed |
| `python -m pytest tests -q --color=no` | 744 passed in 386.24s |
| `git diff --check` | passed |

No commit was created by this work order.

# AW-PORTFOLIO-RELEASE-04 GitHub Push and Post-Push Verification

## Summary

```text
id: AW-PORTFOLIO-RELEASE-04
depends_on:
  - AW-PORTFOLIO-RELEASE-03
scope:
  Push the local portfolio release commits to the configured GitHub remote only
  after explicit operator approval, then verify that the public repository
  presents the intended README, evidence index, metrics, and claim boundary.
risk_level: medium
rollback_plan:
  If push is not approved, leave local commits unchanged. If push succeeds but
  public verification fails, create a follow-up corrective commit; do not force
  push or rewrite public history unless explicitly approved.
```

## Goal

Move the local portfolio release from a verified local branch to a publicly
reviewable GitHub baseline, while keeping the evidence and claim boundary clear:
local demo success is allowed; hosted, production, external provider benchmark,
and uncontrolled DAACS runtime success are not claimed.

## Current Starting State

| Item | Value |
|---|---:|
| Local branch | `main` |
| Remote target | `origin/main` |
| Local commits ahead of origin | 14 |
| Local commits behind origin | 0 |
| Current worktree | clean |
| Push approval state | blocked pending operator approval |

## Acceptance Tests

- Operator explicitly approves `git push -u origin main`.
- Before push, `git status --short --branch` shows no unstaged or staged local
  changes.
- Before push, `git rev-list --count origin/main..HEAD` is recorded.
- Before push, `git rev-list --count HEAD..origin/main` is `0`.
- Push target is `origin/main`; no alternate remote is used.
- Push command output is summarized without exposing credentials or tokens.
- After push, local branch shows `main...origin/main` with ahead `0` and behind
  `0`, or any divergence is recorded as blocked.
- Public GitHub repository page is checked for README visibility.
- Public evidence index path is checked:
  `docs/portfolio-evidence-index.md`.
- Public release work order path is checked:
  `docs/work-orders/aw-portfolio-release-03-github-publish-gate.md`.
- Public claim boundary remains sanitized:
  - raw prompt/body/provider payload exposure: `0`
  - `.local` output publication: `0`
  - hosted/production/live-runtime success claim: `0`
- If public verification requires network/browser access and fails due to
  environment, record `environment_blocked` rather than claiming success.

## Quantitative Target Metrics

| Metric | Target |
|---|---:|
| Local commits pushed | 14 |
| Pre-push unstaged/staged changes | 0 |
| Post-push ahead count | 0 |
| Post-push behind count | 0 |
| README public visibility check | 1 |
| Evidence index public visibility check | 1 |
| Public raw exposure findings | 0 |
| Hosted/production overclaim findings | 0 |
| Force push usage | 0 |

## Out Of Scope

- Force push.
- History rewrite or squash after public push.
- New feature development.
- Hosted deployment.
- Live Solar provider execution.
- Uncontrolled DAACS target runtime execution.
- Publishing `.local`, screenshots, raw browser output, raw DOM text, or local
  machine paths.

## Suggested Execution

Run only after explicit operator approval:

```powershell
git status --short --branch
git rev-list --count origin/main..HEAD
git rev-list --count HEAD..origin/main
git push -u origin main
git status --short --branch
```

Then verify public repository visibility using the GitHub page or a read-only
GitHub check.

## Team Decision

Product lens: pushing now is valuable because the repository has a coherent
portfolio story from README to evidence index.

Architecture lens: publish the stable baseline before starting another feature
track, so future changes can be reviewed incrementally.

Security lens: push is acceptable only if the current sanitized claim boundary
is preserved and no ignored local evidence becomes tracked.

Operations lens: push is the only external state change in this work order and
requires explicit approval. If network or GitHub verification fails, diagnose
and retry using official Git/GitHub behavior rather than marking the task done.

## Next Recommended Work After Push

```text
id: AW-PORTFOLIO-RELEASE-05
scope:
  Visibility decision and recruiter walkthrough. The push succeeded, but the
  repository is currently PRIVATE, so public portfolio reviewers cannot inspect
  unauthenticated README/evidence URLs until an access decision is made.
risk_level: medium
rollback_plan:
  Remove the walkthrough doc/README links and keep the pushed baseline intact.
```

## Execution Result

| Check | Result |
|---|---:|
| Push executed | 1 |
| Push result | passed |
| Pre-push ahead/behind | 15/0 |
| Post-push ahead/behind | 0/0 |
| Local HEAD equals remote HEAD | 1 |
| Remote HEAD | `3b010cb15e0177c7d21cc36e4c0d99306fe82678` |
| GitHub visibility | `PRIVATE` |
| Unauthenticated raw README check | `404` |
| Remote README/evidence content via git | verified |

Interpretation: source push succeeded. Public reviewer access is not yet
available because the GitHub repository is private.

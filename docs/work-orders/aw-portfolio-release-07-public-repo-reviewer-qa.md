# AW-PORTFOLIO-RELEASE-07 Public Repo Reviewer QA

## Summary

```text
id: AW-PORTFOLIO-RELEASE-07
depends_on:
  - AW-PORTFOLIO-RELEASE-06
scope:
  Review the public GitHub repository as a first-time portfolio reviewer. Verify
  README clarity, evidence navigation, local demo command accuracy, public claim
  boundary, and repository metadata readiness.
risk_level: low
rollback_plan:
  Revert only the reviewer-facing README/docs polish changes. Keep repository
  visibility public unless a separate explicit approval changes it.
```

## Goal

Make the now-public repository easy to evaluate in five minutes without adding
new runtime behavior.

## Acceptance Tests

- Public GitHub repository page loads without authentication.
- README explains the project in the first viewport.
- README links to recruiter walkthrough and evidence index.
- Recruiter walkthrough gives a one-command demo path.
- Evidence index links to metrics and AW-PORTFOLIO-RELEASE-06 public visibility
  eval.
- Public wording does not claim hosted, production, external provider benchmark,
  or uncontrolled DAACS runtime success.
- Repo metadata is reviewed:
  - description present or intentionally deferred;
  - topics present or intentionally deferred;
  - license status recorded;
  - default branch is `main`.
- Public raw URL checks return HTTP `200` for README, evidence index, recruiter
  walkthrough, and public visibility eval.

## Quantitative Target Metrics

| Metric | Target |
|---|---:|
| Public README HTTP status | 200 |
| Public evidence index HTTP status | 200 |
| Public recruiter walkthrough HTTP status | 200 |
| Public visibility eval HTTP status | 200 |
| Broken core public links | 0 |
| Hosted/production overclaim findings | 0 |
| Raw prompt/provider/body exposure findings | 0 |

## Out Of Scope

- New application features.
- Hosted deployment.
- Live Solar provider call.
- DAACS target runtime execution.
- Force push or history rewrite.

## Team Decision

Product lens: after public release, the biggest remaining value is reducing
reviewer friction.

Security lens: public claims and raw exposure checks remain mandatory because
the repository is now visible without authentication.

Operations lens: keep changes small, docs-focused, and easy to revert.

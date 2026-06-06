# AW-PORTFOLIO-RELEASE-05 Visibility Decision and Recruiter Walkthrough

## Summary

```text
id: AW-PORTFOLIO-RELEASE-05
depends_on:
  - AW-PORTFOLIO-RELEASE-04
scope:
  Decide how reviewers should access the pushed GitHub repository, then add a
  short recruiter walkthrough that explains the one-command local demo, evidence
  index, verification metrics, and explicit non-claims.
risk_level: medium
rollback_plan:
  Remove the walkthrough doc/README links. If repository visibility is changed,
  revert visibility only after explicit operator approval and after reviewing
  GitHub's visibility-change consequences.
```

## Context

`AW-PORTFOLIO-RELEASE-04` pushed `main` to `origin/main`, but GitHub reports the
repository visibility as `PRIVATE`. Unauthenticated raw GitHub README/evidence
URLs return `404`.

This means the push succeeded, but public portfolio reviewers cannot inspect the
repository unless one of these decisions is made:

- keep repository private and invite specific reviewers;
- make repository public after public-exposure review;
- keep repository private and export a separate sanitized portfolio packet.

Official GitHub references:

- Repository visibility overview:
  https://docs.github.com/github/creating-cloning-and-archiving-repositories/about-repository-visibility
- Changing repository visibility:
  https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility

## Acceptance Tests

- Repository visibility decision is recorded as one of:
  `private_with_invites`, `public_after_review`, or `private_with_export`.
- If public visibility is selected, public-exposure review is completed first.
- README or a dedicated walkthrough gives a first-time reviewer a 5-minute path:
  - what the project is;
  - how to run the local portfolio demo;
  - where the evidence index lives;
  - what metrics are currently verified;
  - what the project does not claim.
- Walkthrough includes current quantitative evidence:
  - stage coverage `7/7`;
  - generated fixture app files `9`;
  - full local test suite `744 passed`;
  - owner/reviewer interaction paths `2/2`;
  - provider/Solar/DAACS uncontrolled runtime calls `0`.
- Walkthrough does not publish raw prompt/body/provider payload, `.local`
  outputs, local root path, screenshot path, raw DOM text, or credentials.
- If repository remains private, README must not claim public availability.
- If repository is made public, unauthenticated README and evidence index checks
  must return HTTP `200`.

## Out Of Scope

- Force push.
- History rewrite.
- Hosted deployment.
- Live Solar provider execution.
- Uncontrolled DAACS target runtime execution.
- Publishing local `.local` outputs or screenshots.

## Team Decision

Product lens: recruiter review now needs an access decision more than another
feature. A private repository is valid only if reviewers are explicitly granted
access or given a separate sanitized packet.

Security lens: making the repository public exposes the entire tracked history
and files. Before changing visibility, perform one final public-exposure scan
for secrets, raw evidence, local paths, and overclaims.

Operations lens: GitHub visibility change is an external state change. It must
not be performed without explicit approval.

Documentation lens: regardless of visibility, add a short walkthrough so a
first-time reviewer understands the project in minutes rather than reverse
engineering the full evidence chain.

## Recommended Implementation Order

1. Run public-exposure scan on tracked files and recent history.
2. Decide visibility mode.
3. Add `docs/recruiter-walkthrough.md`.
4. Link the walkthrough from README.
5. Run public claim tests.
6. Commit the walkthrough.
7. If approved, push the walkthrough commit.
8. If public visibility is approved, change GitHub visibility and verify
   unauthenticated README/evidence HTTP `200`.

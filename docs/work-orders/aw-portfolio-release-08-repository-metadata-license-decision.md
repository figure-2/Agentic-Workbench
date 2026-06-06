# AW-PORTFOLIO-RELEASE-08 Repository Metadata and License Decision

## Summary

```text
id: AW-PORTFOLIO-RELEASE-08
depends_on:
  - AW-PORTFOLIO-RELEASE-07
scope:
  Decide and, if explicitly approved, apply reviewer-facing GitHub repository
  metadata: description, topics, and license status.
risk_level: medium
rollback_plan:
  Revert metadata text changes or remove newly added local license file. Do not
  rewrite git history. Do not change repository visibility unless separately
  approved.
```

## Goal

Make the public repository easier to discover and evaluate while keeping legal
and public-claim boundaries explicit.

## Acceptance Tests

- Repository description is present and reviewer-facing.
- Topics are either applied on GitHub or intentionally deferred with a reason.
- License is either added as a local `LICENSE` file or intentionally deferred
  with a reason.
- README/evidence docs do not claim hosted, production, live provider benchmark,
  or uncontrolled target runtime success.
- Public raw README/evidence/walkthrough URLs still return HTTP `200`.
- No secret, `.env`, `.local`, build output, or raw evidence artifact becomes
  tracked.

## Operator Decisions Required

- Whether to edit GitHub repository description/topics.
- Which license to use, or whether to keep all rights reserved for now.

## Out Of Scope

- Force push or history rewrite.
- Visibility change.
- Hosted deployment.
- Live Solar provider call.
- DAACS target runtime execution.

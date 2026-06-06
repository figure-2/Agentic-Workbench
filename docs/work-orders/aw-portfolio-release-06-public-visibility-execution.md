# AW-PORTFOLIO-RELEASE-06 Public Visibility Execution

## Summary

```text
id: AW-PORTFOLIO-RELEASE-06
depends_on:
  - AW-PORTFOLIO-RELEASE-05
scope:
  If explicitly approved, change the GitHub repository visibility from private
  to public and verify unauthenticated README/evidence access.
risk_level: high
rollback_plan:
  If public verification exposes a blocking issue, change visibility back to
  private only after explicit approval and create a corrective commit. Do not
  rewrite public history unless explicitly approved.
```

## Goal

Make the portfolio repository publicly accessible only after the exposure review
and explicit operator approval.

## Acceptance Tests

- Operator explicitly approves public visibility change.
- GitHub repository target is confirmed as `figure-2/Agentic-Workbench`.
- Repository visibility before change is `PRIVATE`.
- Public-exposure scan from `AW-PORTFOLIO-RELEASE-05` is referenced.
- Visibility is changed using GitHub-supported settings or CLI/API behavior.
- Repository visibility after change is `PUBLIC`.
- Unauthenticated README check returns HTTP `200`.
- Unauthenticated evidence index check returns HTTP `200`.
- Unauthenticated recruiter walkthrough check returns HTTP `200`.
- Public claim boundary remains intact:
  - hosted/production success claim `0`;
  - raw prompt/provider/body exposure `0`;
  - tracked `.local` output `0`;
  - live provider/runtime claim drift `0`.

## Out Of Scope

- Force push.
- History rewrite.
- Hosted deployment.
- Live Solar provider call.
- Uncontrolled DAACS target runtime execution.
- Publishing generated `.local` outputs or screenshots.

## Team Decision

Product lens: public visibility is the best fit for portfolio review, provided
the operator accepts GitHub's public exposure consequences.

Security lens: making a private repository public exposes tracked files and
history. Do not proceed without explicit approval.

Operations lens: visibility change is an external GitHub state change. Verify
with read-only checks immediately after the change.

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

## Current Verified State

| Field | Current value |
|---|---|
| Repository visibility | `PUBLIC` |
| Default branch | `main` |
| Description | `Agentic Workbench` |
| Topics | none |
| License | none |
| Root `LICENSE*` file | none |

## Official Basis

- GitHub topics help people find repositories by subject area and appear on the
  repository main page.
- GitHub CLI `gh repo edit` supports repository description and topic changes.
- GitHub licensing guidance says a repository is not truly open source unless a
  license grants reuse rights. Without a license, default copyright rules apply.

## Team Recommendation

Product lens: add reviewer-facing description and topics because they improve
portfolio discoverability with low implementation risk.

Security lens: metadata must not imply hosted, production, live provider, or
uncontrolled target runtime success.

Legal/operations lens: do not add a license until the operator chooses the reuse
policy. A permissive license helps open-source reuse; no license preserves
default rights but is less reviewer-friendly.

## Proposed Metadata Draft

Description candidate:

```text
Portfolio AI agent workflow harness for turning ideas into SoT/PRD artifacts, generated fixture apps, build/browser evidence, and sanitized verification reports.
```

Topic candidates:

```text
ai-agents
agent-workflow
developer-tools
portfolio-project
python
fastapi
react
playwright
workflow-automation
```

License decision options:

| Option | Effect | When to choose |
|---|---|---|
| MIT | Permissive reuse with minimal restrictions | You want recruiter-friendly open-source reuse |
| Apache-2.0 | Permissive reuse plus explicit patent grant language | You want a more formal open-source license |
| No license for now | Default copyright rules apply | You want to keep reuse rights closed while reviewing |

Recommended default for this project: apply description/topics after approval,
then either choose MIT for a portfolio/open-source posture or defer license if
reuse rights are not decided yet.

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

- Whether to apply the proposed description.
- Whether to apply the proposed topics.
- Which license option to choose: MIT, Apache-2.0, or no license for now.

## Verification Plan

- `gh repo view figure-2/Agentic-Workbench --json nameWithOwner,visibility,url,defaultBranchRef,description,repositoryTopics,licenseInfo`
- Root `LICENSE*` file check.
- Public raw README/evidence/walkthrough HTTP `200` checks.
- `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no`
- `git diff --check`
- Tracked local artifact and high-confidence secret scans.

## Out Of Scope

- Force push or history rewrite.
- Visibility change.
- Hosted deployment.
- Live Solar provider call.
- DAACS target runtime execution.

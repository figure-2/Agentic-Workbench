# AW-PORTFOLIO-RELEASE-07 Public Repo Reviewer QA

## Summary

`AW-PORTFOLIO-RELEASE-07` reviews the public GitHub repository as a first-time
portfolio reviewer. It verifies public access, README navigation, evidence
links, local demo instructions, claim boundaries, and repository metadata
readiness without adding runtime behavior.

## Repository Metadata

| Field | Result |
|---|---|
| Repository | `figure-2/Agentic-Workbench` |
| URL | `https://github.com/figure-2/Agentic-Workbench` |
| Visibility | `PUBLIC` |
| Default branch | `main` |
| Description | present: `Agentic Workbench` |
| Topics | intentionally deferred |
| License | intentionally deferred |

Description/topics can be changed with `gh repo edit`; license selection should
remain a separate operator decision because it changes reuse rights.

## Public URL Checks

| Target | HTTP status | Marker check |
|---|---:|---|
| GitHub repository page | 200 | passed |
| README raw URL | 200 | passed |
| Evidence index raw URL | 200 | passed |
| Recruiter walkthrough raw URL | 200 | passed |
| AW-PORTFOLIO-RELEASE-06 eval raw URL | 200 | passed |
| AW-PORTFOLIO-RELEASE-07 work order raw URL | 200 | passed |

## Reviewer Navigation Checks

| Check | Result |
|---|---|
| README first viewport explains project identity | passed |
| README links evidence index | passed |
| README links recruiter walkthrough | passed |
| Recruiter walkthrough gives one-command demo path | passed |
| Evidence index links metrics | passed |
| Evidence index links AW-PORTFOLIO-RELEASE-06 eval | passed |
| Evidence index links this AW-PORTFOLIO-RELEASE-07 eval | passed |

## Public Boundary Checks

| Metric | Value |
|---|---:|
| Broken core public links | 0 |
| Hosted/production overclaim findings | 0 |
| Raw prompt/provider/body exposure findings | 0 |
| Tracked local artifact findings | 0 |
| High-confidence tracked secret findings | 0 |
| Provider calls | 0 |
| Solar additional calls | 0 |
| DAACS uncontrolled target runtime calls | 0 |

## Verification

| Command | Result |
|---|---|
| `gh repo view figure-2/Agentic-Workbench --json nameWithOwner,visibility,url,defaultBranchRef,description,repositoryTopics,licenseInfo` | passed |
| Public HTTP checks for repo page and raw docs | passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no` | passed |
| `git diff --check` | passed |

## Interpretation

The repository is publicly reviewable and the main portfolio path is visible
without authentication. Metadata polish remains open: topics and license are not
set yet, and should be handled in a separate operator-approved step.

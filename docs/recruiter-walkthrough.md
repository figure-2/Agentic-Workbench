# Recruiter Walkthrough

## What This Project Is

Agentic Workbench is a local AI agent workflow harness prototype. It turns a
vague software idea into a reviewable workflow:

```text
Idea
-> SoT / PRD / ImplementationBrief
-> generated fixture app
-> local build evidence
-> browser screenshot evidence
-> owner filter click evidence
-> reviewer decision click evidence
```

The project is designed to show disciplined agent workflow engineering:
planning artifacts, approval boundaries, generated workspace evidence, local
build evidence, screenshot evidence, and interaction evidence.

## Five-Minute Review Path

1. Read the portfolio snapshot in [README.md](../README.md).
2. Review the evidence map in
   [docs/portfolio-evidence-index.md](portfolio-evidence-index.md).
3. Run the local portfolio demo:

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-demo-final-04 --screenshot-backed
```

4. Open the generated local HTML preview from the command output directory.
5. Check the metrics in [docs/metrics.md](metrics.md).

## Current Verified Evidence

| Evidence | Value |
|---|---:|
| Workflow stage coverage | 7/7 |
| Generated fixture app files | 9 |
| Local build status | passed |
| Screenshot evidence/hash count | 1/1 |
| Owner filter click path | passed |
| Reviewer decision click path | passed |
| Verified interaction paths | 2/2 |
| Full local test suite | 744 passed |
| External provider calls in portfolio package | 0 |
| Solar additional calls in portfolio package | 0 |
| DAACS uncontrolled target runtime calls | 0 |

## What To Look For

- The project separates planning, approval, implementation planning, execution
  evidence, and verification evidence.
- Public outputs use sanitized status/hash/count summaries instead of raw prompt,
  provider response, DOM text, screenshot path, or local root path.
- The generated app is fixture-backed and locally verified; it is not claimed as
  a hosted production deployment.
- The integration preserves DIV-like planning identity and DAACS-like
  implementation/verification identity as a single service-shaped workflow.

## What This Project Does Not Claim

- Hosted application success.
- Production readiness.
- External provider quality benchmark.
- Uncontrolled DAACS target runtime execution.
- Publication of raw prompts, raw provider payloads, raw DOM text, screenshot
  paths, local root paths, secrets, or `.local` output files.

## Repository Access Decision

Current repository visibility is `PRIVATE`.

Recommended portfolio decision: `public_after_review`.

Reason: the project is meant for portfolio review, and the current
public-exposure scan found no tracked `.local`, `.env`, build output, live
credential, or raw evidence file that should block public review. The remaining
high-confidence secret-like strings are test sentinel values used to verify
blocking behavior.

Status: visibility change is blocked until the operator explicitly approves the
external GitHub state change.

## Public Exposure Scan Summary

| Check | Result |
|---|---:|
| Tracked `.local`, `.env`, `dist`, `build`, or `node_modules` findings | 0 |
| High-confidence tracked secret files | 3 test sentinel files |
| Remote README marker | verified |
| Remote evidence index marker | verified |
| History commits scanned for release docs | 121 |
| GitHub repository visibility | PRIVATE |
| Public unauthenticated raw README check | 404 |

Interpretation: the repository has been pushed, but public unauthenticated
access is blocked by private visibility.

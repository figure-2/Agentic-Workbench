# AW-PORTFOLIO-RELEASE-02 Commit and Push Handoff

## Summary

```text
id: AW-PORTFOLIO-RELEASE-02
depends_on:
  - AW-PORTFOLIO-RELEASE-01
scope:
  Prepare the accumulated interaction-backed portfolio baseline for source
  control handoff. Review the dirty worktree, confirm tracked/untracked files,
  create a clean commit if approved, and push to the configured GitHub remote
  if approved.
risk_level: medium
rollback_plan:
  If commit/push is not approved, leave the worktree unchanged. If commit is
  created locally but push is not approved, keep the local commit and report the
  exact ahead count.
```

## Goal

Move from a verified local portfolio baseline to a clean source-control handoff
without accidentally tracking local outputs, secrets, raw evidence, or temporary
files.

## Acceptance Tests

- `git status --short --branch` reviewed before staging.
- `.local` outputs remain untracked.
- No `.env`, credential, raw provider output, screenshot path dump, page text
  dump, or local root evidence file is staged.
- `git diff --check` passes before commit.
- Public claim docs pass before commit.
- Full test result is either current and recorded or explicitly rerun.
- Commit message, if approved:
  `feat: package interaction-backed portfolio demo`
- Push, if approved, targets the configured `origin` remote and `main` branch.

## Out Of Scope

- Rewriting prior commits.
- Force push.
- Deleting user files.
- Adding new runtime/provider functionality.
- Tracking generated `.local` demo outputs.

## Suggested Verification

```powershell
git status --short --branch
git diff --check
python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no
python -m pytest tests -q --color=no
git add README.md docs examples packages apps tests
git status --short --branch
git commit -m "feat: package interaction-backed portfolio demo"
git push -u origin main
```

## Team Decision

Product lens: the project is portfolio-visible enough to publish once the
worktree is cleanly committed.

Architecture lens: commit current baseline before adding another feature track.

Security lens: stage only source/docs/tests; do not stage local artifacts or
credential files.

Operations lens: push is an external state change and requires explicit user
approval before execution.

## Pre-Commit Review

Status on 2026-06-06:

| Check | Result |
|---|---:|
| Branch state | `main...origin/main [ahead 12]` |
| Local commits ahead of origin | 12 |
| Local commits behind origin | 0 |
| Modified tracked files | 15 |
| Untracked source/docs/test files | 32 |
| Total staging candidates | 47 |
| `.local` or local build output in staging candidates | 0 |
| Tracked `.local`, `.env`, `dist`, `build`, or `node_modules` findings | 0 |
| High-confidence secret scan findings | 3 test sentinel files |
| `git diff --check` | passed |
| Configured push target | `origin` / `main` |

High-confidence secret scan findings are existing negative-test sentinel values
used to verify raw credential/material blocking. They are not live credentials
and should remain limited to test files.

Recommended staging scope:

```powershell
git add README.md apps docs examples packages tests
```

Recommended commit message:

```text
feat: package interaction-backed portfolio demo
```

Hold points:

- Do not stage `.local`, `.env*`, `dist`, `build`, screenshots, browser raw
  output, or generated local evidence files.
- Do not push until the operator explicitly approves the external GitHub state
  change.

# AW-PORTFOLIO-RELEASE-03 GitHub Publish Gate

## Summary

```text
id: AW-PORTFOLIO-RELEASE-03
depends_on:
  - AW-PORTFOLIO-RELEASE-02
scope:
  Record the post-commit GitHub publish readiness gate. Confirm the local
  branch, commit hash, ahead/behind state, remote target, verification results,
  and public claim boundary before any push is attempted.
risk_level: medium
rollback_plan:
  Remove this publish-gate documentation and keep the local release commit
  state unchanged. Do not rewrite history or force push.
```

## Goal

Make the repository push-ready without performing the external GitHub state
change until the operator explicitly approves it.

## Current Release Candidate

| Item | Value |
|---|---:|
| Release commit | `6847089` |
| Commit message | `feat: package interaction-backed portfolio demo` |
| Branch | `main` |
| Remote target | `origin/main` |
| Ahead count after release commit | 13 |
| Behind count after release commit | 0 |
| Worktree after release commit | clean |
| Push executed | 0 |

## Acceptance Tests

- Release commit hash is recorded.
- `origin/main` ahead/behind state is recorded.
- Push target is recorded without embedding credentials.
- Full local test result is recorded.
- Public claim test result is recorded.
- `.local`, `.env`, build outputs, raw browser output, and screenshot files are
  not part of the release commit.
- Public docs do not claim hosted, production, external provider benchmark, or
  uncontrolled DAACS runtime success.
- `git push` remains blocked until explicit operator approval.

## Verification Record

| Command | Result |
|---|---:|
| `git diff --cached --check` | passed before commit |
| `python -m compileall examples\demo-service-flow\run_portfolio_demo.py examples\demo-service-flow\render_artifact_preview.py packages\daacs_builder\target_runtime_local_preview_attempt.py packages\daacs_builder\target_runtime_browser_setup_attempt.py tests\smoke\test_portfolio_demo_package.py tests\unit\test_target_runtime_local_preview_attempt.py tests\unit\test_target_runtime_browser_setup_attempt.py` | passed before commit |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no` | 3 passed in 0.19s |
| `python -m pytest tests -q --color=no` | 744 passed in 386.37s |
| `git commit -m "feat: package interaction-backed portfolio demo"` | `6847089` |

## Team Decision

Product lens: the portfolio baseline is publishable after this gate because the
README, evidence index, generated app evidence, build evidence, screenshot
evidence, and two interaction paths are visible from the repository.

Architecture lens: the release commit should be pushed before starting another
large feature track, so GitHub reviewers see a coherent baseline.

Security lens: no push should occur unless the operator confirms that the public
claim boundary and repository target are acceptable.

Operations lens: push is the only remaining external state change. It must be a
separate, explicit action.

## Next Action

Blocked pending operator approval:

```powershell
git push -u origin main
```

Do not run this command without explicit approval.

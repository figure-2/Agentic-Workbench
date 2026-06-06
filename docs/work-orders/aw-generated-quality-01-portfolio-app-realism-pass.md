# AW-GENERATED-QUALITY-01 Portfolio Generated App Realism Pass

## Summary

```text
id: AW-GENERATED-QUALITY-01
depends_on:
  - AW-DEMO-FINAL-02
  - AW-DAACS-RUNTIME-MVP-02
  - AW-BUILD-04
scope:
  Improve the generated fixture app so the portfolio preview feels like a
  concrete service output, not only a minimal scaffold. Use the existing SoT,
  PRDPackage, ImplementationBrief, RunnerPlan, and VerificationReport public
  projections as the content source.
risk_level: medium
rollback_plan:
  Remove generated app content refinements and keep the AW-DEMO-FINAL-02
  package plus existing fixture app generation path.
```

## Goal

Make the generated app screen easier for a reviewer to understand at a glance:

```text
document output -> implementation plan -> generated app workspace -> build evidence
```

The work should increase visible product quality without opening additional
provider calls, DAACS target runtime execution, or hosted deployment.

## Team Decision

Product lens: the next portfolio gap is app realism. Reviewers can now see the
pipeline; the generated screen should look more like a useful workbench output.

Architecture lens: reuse the existing generated fixture app writer and public
document projections. Do not add a new persistence layer.

Frontend lens: improve the generated `App.tsx` and supporting styles/content
with dense workbench-style sections: workflow stages, artifact cards, runner
plan, verification summary, and boundary counters.

Security lens: generated file contents may exist inside the run-scoped
workspace, but public projections should continue to expose relative path,
hash, byte count, label, status, and counts only.

Testing lens: keep verification fast. Static validation, build preflight, and
local build attempt evidence are enough for this pass.

## Scope

### A. Generated App Content Upgrade

Acceptance tests:

- Generated `App.tsx` includes workflow stages, artifact summary, runner plan,
  verification summary, and execution boundary sections.
- Generated `api.ts` or equivalent fixture data keeps public-safe labels and
  counts only.
- Generated app file count remains at least `9`.
- Required files remain present: `package.json`, `src/App.tsx`, `src/api.ts`.
- Raw prompt, provider body, credential, command output, screenshot path, page
  text, and local root path exposure remain `0`.

### B. Static Validation Extension

Acceptance tests:

- Static validation checks at least `6` app markers.
- Static validation checks at least `4` verification/boundary markers.
- Package JSON parse remains passing.
- Required script labels remain `4/4`.
- Build-ready candidate remains true.

### C. Portfolio Bundle Refresh

Acceptance tests:

- `run_portfolio_demo.py --allow-local-build-attempt` still writes one JSON
  summary and one static HTML preview.
- Stage coverage remains `7/7`.
- Local build status remains measured and public-safe.
- Browser setup command attempts remain `0` by default.
- Provider calls and DAACS target runtime calls remain `0`.

## Quantitative Targets

| Metric | Target |
|---|---:|
| Representative scenario count | 1 |
| Generated app file records | >=9 |
| Required core files present | 3/3 |
| App marker count | >=6 |
| Verification/boundary marker count | >=4 |
| Stage coverage | 7/7 |
| Local build command results | >=2 when opt-in is used |
| Browser setup command attempts by default | 0 |
| Provider calls | 0 |
| DAACS target runtime calls | 0 |
| Public raw exposure findings | 0 |

## Out Of Scope

- New Solar live call
- Original DAACS runtime execution
- Hosted deployment
- Automatic browser/package setup
- Public raw file body viewer

## Done Criteria

- Generated app looks like a reviewer-facing Agentic Workbench output.
- Static validation records the improved markers.
- Portfolio bundle still runs in one command.
- Metrics and eval docs record the measured numbers.

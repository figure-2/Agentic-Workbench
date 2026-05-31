# AW-PARITY-01B Source Identity Golden Path

## Scope

Connect the AW-PARITY-01A source identity fixture to the Workbench artifact
chain as a smoke/parity test.

This step verifies fixture-based identity preservation only. It does not run
source runtimes, provider clients, CLI tools, package installs, local servers,
or file-writing build runtimes.

## Current Implementation

- `tests/smoke/test_source_identity_golden_path.py`
  - builds a fixture-safe DIV-like state from
    `tests/fixtures/source_identity_golden_path.json`
  - converts the state into `PlanningBlueprint`
  - derives `BuildSpec` and `PRDPackage`
  - creates an `ImplementationBrief` and matching `SpecApproval`
  - maps the approved build spec into a DAACS-compatible offline state
  - runs `DAACSDryRunRunner` to produce `RunnerPlan` and
    `VerificationReport`
  - projects the session through `public_workflow_session_payload`

The test intentionally uses public projection for leakage checks. Internal
contracts may include blocking language for safety policy; public leakage is
measured only on the projected API-safe payload.

## Acceptance Results

| Gate | Result |
|---|---|
| Idea -> PlanningBlueprint -> PRDPackage -> ImplementationBrief -> SpecApproval -> RunnerPlan -> VerificationReport | covered |
| DIV section identity reflected in planning and PRD artifacts | covered |
| DIV evidence summary reflected as sanitized summary | covered |
| DIV visual intent reflected as visual requirements | covered |
| DAACS backend/frontend/API split reflected in BuildSpec and RunnerPlan | covered |
| VerificationReport includes dry-run checks and metrics | covered |
| RunnerPlan next-action placeholder and VerificationReport placeholder metrics | covered |
| public raw field leakage | 0 |
| public forbidden claim findings | 0 |
| live provider calls | 0 |
| direct source-runtime calls | 0 |
| subprocess/package/server/filesystem write counters | 0 |

## Quantitative Results

| Metric | Value |
|---|---:|
| Source identity smoke tests | 1 |
| Session artifact records excluding IdeaBrief | 7 |
| Artifact run_id linkage | 7 / 7 |
| DIV section titles preserved | 7 / 7 |
| Fixture baseline trace-row coverage asserted in smoke test | 8 / 8 |
| RunnerPlan backend planned actions | 1 |
| RunnerPlan frontend planned actions | 1 |
| RunnerPlan verifier planned actions | 1 |
| Required live-runner approval placeholders | 1 |
| VerificationReport next-action placeholder metrics | 2 |
| Public projection forbidden key findings | 0 |
| Public projection forbidden claim findings | 0 |
| Side-effect counters | all 0 |
| Full pytest result | 261 / 261 passed |

## Test Commands

```powershell
python -m pytest tests/smoke/test_source_identity_golden_path.py -q
python -m pytest tests -q
```

## Non-Current Claims

- This test does not prove source runtime reproduction.
- This test does not prove app generation.
- This test does not prove provider quality.
- This test does not expose raw prompts, logs, file bodies, provider payloads,
  approval authorization material, or generated source bodies.

## Audit Notes

- Product/architecture review: the test correctly treats DIV as the upstream
  planning/document/evidence/visual identity and DAACS as the downstream
  build-plan/verifier identity.
- Security review: leakage scanning must stay on the public projection, not on
  internal safety contracts.
- Test review: `WorkbenchHarness.run()` is not used because it does not emit a
  `RunnerPlan` artifact; the smoke test constructs the artifact chain
  explicitly.

## Next Step

`AW-PARITY-01C` should map this smoke evidence back into source-to-target trace
documentation and public portfolio claim boundaries. After that, persistence can
continue with runner plan, verification report, and audit event repositories.

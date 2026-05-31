# AW-PARITY-01C Trace And Claim Projection

## Scope

Map the AW-PARITY-01B smoke evidence into source-to-target trace rows and a
portfolio-safe public wording boundary.

This step is documentation and claim control. It does not add provider calls,
runtime execution, CLI execution, package installs, server starts, or generated
source artifacts.

## Evidence Inputs

| Evidence | Path | Role |
|---|---|---|
| Source identity fixture | `tests/fixtures/source_identity_golden_path.json` | Source identity baseline |
| Golden path smoke test | `tests/smoke/test_source_identity_golden_path.py` | E1 proof that the fixture reaches the artifact chain |
| Public projection helper | `packages/core/public_projection.py` | E1 proof that public output uses sanitized projection |
| Dry-run runner | `packages/daacs_builder/dry_run_runner.py` | E1 proof of side-effect-free runner planning |
| Metrics record | `docs/metrics.md` | Quantitative regression snapshot |

## Trace Closure

| Trace row | Preserved identity | Workbench artifact | E1 evidence |
|---|---|---|---|
| `TR-DIV-01` | Idea structuring into a planning blueprint | `PlanningBlueprint.features` | `test_source_identity_fixture_runs_through_golden_path_without_live_side_effects` |
| `TR-DIV-02` | Sectioned planning document and PRD handoff | `PlanningBlueprint.markdown`, `PRDPackage.prd_markdown` | same smoke test |
| `TR-DIV-03` | Research/evidence intent as summary metadata | `PlanningBlueprint.evidence`, `PRDPackage.evidence_summary` | same smoke test |
| `TR-DIV-04` | Visual/user-flow intent as metadata | `PlanningBlueprint.visual_artifacts`, `PRDPackage.visual_requirements` | same smoke test |
| `TR-DAACS-01` | Backend/frontend/API decomposition | `BuildSpec`, `ImplementationBrief.daacs_tasks` | same smoke test |
| `TR-DAACS-03` | DAACS-compatible state bridge | DAACS-compatible offline state | same smoke test |
| `TR-DAACS-04` | Verifier/replanning identity as report and next action | `VerificationReport.metrics` | same smoke test |
| `TR-DAACS-07` | Runner/provider config boundary | `RunnerPlan`, dry-run side-effect counters | same smoke test |

## Public Projection

<!-- public-portfolio-safe-start -->
Portfolio-safe wording:

Agentic Workbench is a local/dev AI agent workflow harness prototype. It links
idea planning, PRD packaging, implementation handoff, approval, dry-run runner
planning, and verification reporting through fixture-based regression tests.
Current evidence covers contract wiring, sanitized public projection, and
side-effect-free dry-run planning. External provider calls and executable build
runtimes remain outside the current public capability claim.
<!-- public-portfolio-safe-end -->

Use the wording above only with the qualifiers `local/dev`, `prototype`,
`fixture-based`, and `dry-run`.

## Claim Boundary Decisions

| Claim area | Current decision | Evidence |
|---|---|---|
| Source identity preservation | Allowed with fixture/dry-run qualifier | AW-PARITY-01A fixture and AW-PARITY-01B smoke test |
| Public API exposure | Allowed as sanitized projection only | `public_workflow_session_payload` smoke assertion |
| Build output | Not a current public claim | runner plan is planned-only |
| Provider output | Not a current public claim | provider metrics remain 0 in current path |
| Production use | Not a current public claim | no production deployment or production security evidence |

## Acceptance Results

| Acceptance test | Result | Evidence |
|---|---|---|
| source-to-target trace row linked to 01B smoke test | pass | Trace Closure table |
| public README/portfolio wording separates fixture, dry-run, and future runtime surfaces | pass | Public Projection section and README Claim Boundary |
| DIV identity preservation linked to test name | pass | `TR-DIV-01` to `TR-DIV-04` rows |
| DAACS identity preservation linked to test name | pass | `TR-DAACS-01`, `TR-DAACS-03`, `TR-DAACS-04`, `TR-DAACS-07` rows |
| overclaim findings in public-safe block | 0 | `test_public_claim_projection_docs.py` |

## Quantitative Results

| Metric | Value |
|---|---:|
| Trace rows closed by 01B smoke evidence | 8 |
| DIV trace rows closed | 4 |
| DAACS trace rows closed | 4 |
| Public-safe projection blocks | 1 |
| Public-safe block forbidden claim findings | 0 |
| Public-safe block forbidden key findings | 0 |
| README forbidden claim findings | 0 |
| Full local pytest result | 264 / 264 passed |

## Next Step

`AW-PERSIST-03` can start after this step. Its scope should be limited to
`RunnerPlanRepository`, `VerificationReportRepository`, and `AuditEventRepository`
boundaries that store sanitized summaries, hashes, counts, and status metadata.

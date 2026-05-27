# AW-NEXT-07A PRDPackage / ImplementationBrief Approval Gate

## Scope

`PlanningBlueprint -> PRDPackage -> BuildSpec -> ImplementationBrief -> SpecApproval` contract formalization.

This eval adds the human approval gate before DAACS handoff. It does not implement dry-run execution, live DAACS execution, Solar Pro 3 provider calls, package installation, server startup, or generated-code quality verification.

## Gates

| Gate | Status | Evidence |
|---|---|---|
| PRD Package Gate | PASS | `PlanningBlueprint` plus `BuildSpec` creates reviewable `PRDPackage` |
| Implementation Brief Gate | PASS | `PRDPackage` plus `BuildSpec` creates DAACS-readable `ImplementationBrief` with stable hashes |
| Approval Required Gate | PASS | Harness stops at `approval` stage and does not call builder without approver |
| Requested Changes Gate | PASS | Rejected approval records remain in `approval` stage and do not call builder |
| Hash Match Gate | PASS | DAACS state mapping with `require_approval=true` rejects missing or mismatched approval |
| Public Artifact Gate | PASS | PRD/brief payloads pass existing redaction and forbidden public-key sanitation |
| No-Live-Call Gate | PASS | No provider, subprocess, package install, server start, or filesystem write surface added |

## Metrics

| Metric | Value |
|---|---:|
| Pytest collected cases | 83 |
| Pytest passed cases | 83 |
| Regression delta vs AW-NEXT-06 baseline | +9 |
| New schema tests | 3 |
| New adapter/approval tests | 5 |
| New smoke approval-gate tests | 2 |
| New artifact kinds | 3 |
| New workflow stage | 1 |
| Builder calls before approval | 0 |
| Approval hash mismatch rejection fixtures | 1 |
| Requested-change rejection fixtures | 1 |
| Live LLM/API calls during eval | 0 |
| Provider calls during eval | 0 |
| Subprocess calls during eval | 0 |
| Package install calls during eval | 0 |
| Server start calls during eval | 0 |
| Filesystem writes during eval | 0 |

## Interpretation

This proves the Workbench has a first-class PRD/brief approval contract before DAACS handoff. It does not prove that DAACS can generate a working project, does not run DAACS subgraphs, and does not validate Solar Pro 3 quality.

## Next Step

Implement `AW-NEXT-07B`: dry-run runner that consumes an approved `ImplementationBrief`, emits a `RunnerPlan`, and keeps all side-effect counters at 0.

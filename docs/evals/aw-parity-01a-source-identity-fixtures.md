# AW-PARITY-01A Source Identity Fixtures

## Scope

Add test-only source identity fixtures for DIV and DAACS parity.

This step fixes the reference set for source identity preservation. It does not
run DIV, DAACS, provider clients, CLI tools, package installs, local servers, or
file-writing runtimes.

## Current Implementation

- `tests/fixtures/source_identity_golden_path.json`
  - DIV blueprint fixture: planning style, TOC counts, section titles, required
    information count, and Workbench mapping.
  - DIV markdown/visual fixture: sectioned document, evidence policy, visual
    intent signals, and Workbench mapping.
  - DAACS fixture: TODO-style full-stack goal, backend/frontend/API split,
    runner config signals, verifier/replanning identity, and Workbench mapping.
  - Composite fixture: target artifact chain and cross-source invariants.
- `tests/unit/test_source_identity_fixtures.py`
  - verifies fixture count and source coverage
  - verifies 8 trace rows:
    `TR-DIV-01` to `TR-DIV-04`,
    `TR-DAACS-01`, `TR-DAACS-03`, `TR-DAACS-04`, `TR-DAACS-07`
  - verifies fixture public-safety and deterministic hash stability

## Acceptance Results

| Gate | Result |
|---|---|
| source identity fixture count | 4 |
| required trace-row parity coverage | 8 / 8 |
| DIV planning/PRD/evidence/visual identity signals | covered |
| DAACS backend/frontend/API/state/verifier/runner identity signals | covered |
| forbidden public field leakage in fixture | 0 in covered fixture |
| forbidden claim findings in fixture | 0 |
| deterministic fixture hash | covered |
| live provider call | 0 |
| direct original runtime call | 0 |

## Test Commands

```powershell
python -m compileall packages apps tests
python -m pytest tests/unit/test_source_identity_fixtures.py -q
python -m pytest tests -q
```

## Non-Current Claims

- The fixture does not prove source runtime reproduction.
- The fixture does not prove app generation.
- The fixture does not prove live provider quality.
- The fixture does not expose raw source prompts, logs, file bodies, provider
  payloads, or approval authorization material.

## Next Step

`AW-PARITY-01B` should use this fixture set to create the golden path
smoke/parity test:

```text
Idea -> PlanningBlueprint -> PRDPackage -> ImplementationBrief
-> SpecApproval -> RunnerPlan -> VerificationReport
```

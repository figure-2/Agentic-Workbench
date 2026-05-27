# Quantitative Baseline

## Measurement Date

2026-05-27

## Source Project Metrics

| Source | Files measured | Counted code/doc files | Counted lines | Python | TS/TSX | Markdown | Test signals |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ai01-2nd-S_P_-DAACS` | 123 | 118 | 24,279 | 30 | 78 | 3 | 1 |
| `pro-nlp-finalproject-nlp-04` | 52 | 47 | 5,608 | 43 | 0 | 2 | 0 |

Focused core directories:

| Source path | Files | Python files | Python lines |
|---|---:|---:|---:|
| `DAACS/transformers7-project-feature-backend2/daacs` | 31 | 30 | 6,220 |
| `DIV/src` | 44 | 43 | 5,054 |

## Interpretation

- DAACS has more reusable integration surface because it already includes backend workflow, API server, logging, and Nova-Canvas UI.
- DIV has high-value planning/research logic but should be extracted as graph modules rather than copied as a Streamlit app.
- Both source projects have weak automated verification signals. The first integration work therefore adds schema, adapter, redaction, claim, and smoke tests before live graph wiring.

## Reuse Summary

| Source | Reuse candidates | Primary role in Agentic Workbench |
|---|---:|---|
| DAACS | 14 | Build and verification layer |
| DIV | 15 | Planning, research, and document layer |

## Agentic Workbench Metrics

Current snapshot after `AW-NEXT-10` approval signature and nonce replay gate skeleton.

| Metric | Value |
|---|---:|
| Project files, excluding cache | 64 |
| Counted code/doc files, excluding cache | 64 |
| Project lines, excluding cache | 7,309 |
| Python files | 37 |
| Markdown files | 23 |
| Test files | 10 |
| Unit test files | 8 |
| Smoke test files | 2 |
| Integration test files | 0 |
| Pytest collected cases | 162 |
| Pytest passed cases | 162 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |

## AW-NEXT-01 Gate Metrics

| Gate | Quantitative target | Result |
|---|---:|---:|
| Path boundary | 7 unsafe path fixtures rejected | 7/7 |
| Public artifact exposure | raw prompt/search/corpus forbidden keys in public payload | 0 found after sanitization |
| Redaction | secret, Bearer token, DB URL, email, phone, Windows path, Linux path | 7/7 fixture classes covered |
| Claim scan | forbidden claim variants detected | 2/2 variant classes in test |
| Smoke | sanitized harness run and unsafe generated path rejection | 2/2 |

Interpretation: this is contract/gate coverage, not model quality or production security certification.

## AW-NEXT-02 DIV Adapter Metrics

Measured after `DIV GlobalState -> PlanningBlueprint` adapter expansion.

| Metric | Value |
|---|---:|
| Pytest collected cases | 36 |
| Pytest passed cases | 36 |
| Adapter test cases | 8 |
| New adapter test cases | 6 |
| DIV state families covered | 5 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| External provider imports in adapter test | 0 |

| Covered source field family | Status |
|---|---|
| `idea.blueprint` | covered |
| `idea.planning_style`, `idea.rationale`, `idea.toc` | covered |
| `plan.sections` dict and legacy string forms | covered |
| `plan.final_markdown` | covered |
| `plan.visual_artifacts` and `visual.artifacts` | covered |
| `research.evidence_store`, `gathered_evidence`, `search_results`, `analysis_result` | covered |
| malformed nested state | covered |

Interpretation: this measures offline adapter contract coverage. It does not claim live DIV graph execution, live Upstage/Solar quality, or production readiness.

## AW-NEXT-03 BuildSpec to DAACSState Metrics

Measured after `PlanningBlueprint -> BuildSpec -> DAACSState` formalization.

| Metric | Value |
|---|---:|
| Pytest collected cases | 45 |
| Pytest passed cases | 45 |
| Adapter test cases | 18 |
| New adapter/schema test cases | 9 |
| Representative BuildSpec endpoint count | 5 |
| Representative API data model count | 2 |
| Representative frontend API call count | 5 |
| Representative acceptance criteria count | 12 |
| DAACSState mapped key count | 56 |
| `build_contract` key count | 8 |
| Unsafe run id fixtures rejected | 6 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |

| API surface | Count | Notes |
|---|---:|---|
| Implemented Workbench API endpoint | 1 | `POST /api/v1/runs` fixture endpoint |
| BuildSpec contract endpoint | 5 | representative two-feature blueprint |
| BuildSpec data model | 2 | representative two-feature blueprint |

Interpretation: this measures deterministic contract construction and DAACSState mapping, not live DAACS execution or generated-code quality.

## AW-NEXT-04 DAACS Offline Runner Metrics

Measured after `DAACSState -> VerificationReport` offline runner boundary implementation.

| Metric | Value |
|---|---:|
| Pytest collected cases | 67 |
| Pytest passed cases | 67 |
| New runner/security test cases | 22 |
| Runner boundary test cases | 18 |
| Generated file namespace rejection fixtures | 4 |
| Required DAACSState checks | 10 |
| Representative runner checks | 15 |
| Representative DAACSState mapped keys | 56 |
| Representative BuildSpec endpoint count | 5 |
| Representative frontend API call count | 5 |
| Representative acceptance criteria count | 12 |
| Blocked operation families | 6 |
| Detected blocked operation attempts in happy path | 0 |
| Unsafe state rejections in happy path | 0 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| CLI agent invocations during eval | 0 |
| Subprocess calls during eval | 0 |
| Package install calls during eval | 0 |
| Server start calls during eval | 0 |
| Filesystem writes during eval | 0 |
| Provider runtime imports during eval | 0 |

| Blocked family | Fixture coverage |
|---|---:|
| CLI agent execution | 1 |
| provider/LLM call | 1 |
| subprocess execution | 1 |
| package install | 1 |
| local server start | 1 |
| filesystem write | 1 |

Interpretation: this measures offline boundary enforcement. It does not claim live DAACS execution, generated-code quality, install/build success, hosted success, or production readiness.

## AW-NEXT-05 Runner Provider Boundary Design Metrics

Measured after offline/dry-run/live runner provider boundary design.

| Metric | Value |
|---|---:|
| Existing pytest baseline referenced | 67 |
| Runner modes designed | 3 |
| Boundary layers designed | 4 |
| Core runner contracts designed | 4 |
| State transitions documented | 7 |
| Mode-specific transition paths | 3 |
| Blocked direct transitions documented | 4 |
| Operation policy rows | 10 |
| Approval record fields | 13 |
| Execution units added | 5 |
| Live LLM/API calls during design | 0 |
| Provider imports during design | 0 |
| Subprocess calls during design | 0 |
| Package install calls during design | 0 |
| Server start calls during design | 0 |
| Filesystem writes during design | 0 |

Target metrics before real live execution:

| Metric | Required value |
|---|---:|
| Raw secret log count | 0 |
| Approval bypass count | 0 |
| Provider imports in offline/dry-run | 0 |
| Provider calls in offline/dry-run | 0 |
| Subprocess/package/server/write in offline/dry-run | 0 |
| Rollback coverage rate | 100% |
| Audit log completeness rate | 100% |

Interpretation: this is a design metric set. It does not implement dry-run, live execution, Solar Pro 3 provider calls, or DAACS runtime execution.

## AW-NEXT-06 Runner Provider Registry Metrics

Measured after `RunnerProvider` skeleton and fail-closed registry implementation.

| Metric | Value |
|---|---:|
| Pytest collected cases | 74 |
| Pytest passed cases | 74 |
| Regression delta vs AW-NEXT-04 baseline | +7 |
| New provider/registry unit tests | 5 |
| New finding redaction tests | 2 |
| Default registered runner modes | 1 |
| Offline provider compatibility fixtures | 1 |
| Unknown mode rejection fixtures | 1 |
| Live without approval rejection fixtures | 1 |
| Malformed live approval rejection fixtures | 1 |
| Missing live provider block fixtures | 1 |
| Raw finding text fields | 0 |
| Redacted finding coverage | 2/2 |
| Raw secret log count | 0 |
| Approval bypass count in offline path | 0 |
| Provider imports during eval | 0 |
| Provider calls during eval | 0 |
| CLI agent invocations during eval | 0 |
| Subprocess calls during eval | 0 |
| Package install calls during eval | 0 |
| Server start calls during eval | 0 |
| Filesystem writes during eval | 0 |

Interpretation: this implements only the runner provider skeleton and registry. It does not implement dry-run, live execution, Solar Pro 3 provider calls, or DAACS runtime execution.

## AW-NEXT-07A PRDPackage / ImplementationBrief Approval Gate Metrics

Measured after explicit PRD/brief artifacts and user approval gate implementation.

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
| PRDPackage artifact generated in approved smoke | 1 |
| ImplementationBrief artifact generated in approved smoke | 1 |
| SpecApproval artifact generated in approved smoke | 1 |
| Builder calls before approval | 0 |
| Approval hash mismatch rejection fixtures | 1 |
| Requested-change rejection fixtures | 1 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Subprocess calls during eval | 0 |
| Package install calls during eval | 0 |
| Server start calls during eval | 0 |
| Filesystem writes during eval | 0 |

| Gate | Result |
|---|---|
| `PlanningBlueprint -> PRDPackage` | covered |
| `PRDPackage + BuildSpec -> ImplementationBrief` | covered |
| no approver blocks builder | covered |
| requested changes block builder | covered |
| approved hash mismatch blocks DAACSState mapping | covered |

Interpretation: this measures offline content-approval contract coverage before DAACS handoff. It does not implement dry-run, live DAACS execution, Solar Pro 3 provider calls, generated-code quality, install/build success, hosted success, or production readiness.

## AW-NEXT-07B DAACS Dry-Run Runner Metrics

Measured after side-effect-free dry-run runner and `RunnerPlan` implementation.

| Metric | Value |
|---|---:|
| Pytest collected cases | 94 |
| Pytest passed cases | 94 |
| Regression delta vs AW-NEXT-07A baseline | +11 |
| Dry-run provider tests | 9 |
| New security redaction tests | 1 |
| Default registered runner modes | 2 |
| Live registered runner modes | 0 |
| Missing approval block fixtures | 1 |
| Mismatched approval block fixtures | 1 |
| Mutated brief block fixtures | 1 |
| Unsafe state block fixtures | 1 |
| Process/file/network/import tripwire tests | 2 |
| Plan redaction fixtures | 1 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Provider imports during eval | 0 |
| CLI agent invocations during eval | 0 |
| Subprocess calls during eval | 0 |
| Package install calls during eval | 0 |
| Server start calls during eval | 0 |
| Filesystem writes during eval | 0 |
| Network calls during eval | 0 |
| Executed action count | 0 |
| Raw secret log count | 0 |

| Gate | Result |
|---|---|
| approved `ImplementationBrief -> RunnerPlan` | covered |
| no approval blocks dry-run | covered |
| mismatched approval blocks dry-run | covered |
| mutated brief after approval blocks dry-run | covered |
| unsafe generated state blocks dry-run | covered |
| process/file/network/import tripwire | covered |
| plan/report/audit redaction fixture | covered |

Interpretation: this measures dry-run planning coverage only. It does not implement live DAACS execution, Solar Pro 3 provider calls, generated-code quality, install/build success, hosted success, or production readiness.

## AW-NEXT-08 Gated Fake Live Runner Metrics

Measured after `LiveRunnerProvider` and `FakeLiveRuntime` implementation.

| Metric | Value |
|---|---:|
| Pytest collected cases | 121 |
| Pytest passed cases | 121 |
| Regression delta vs AW-NEXT-07B baseline | +27 |
| Runner provider registry tests | 42 |
| AW-NEXT-08 live/fake test cases | 27 |
| Unsafe `run_id` public exposure regression cases | 1 |
| Approval validation negative cases | 13 |
| Workspace boundary negative cases | 6 |
| Host command tripwire tests | 1 |
| File/network tripwire tests | 1 |
| DAACS/provider import tripwire tests | 1 |
| Default registered runner modes | 3 |
| Live provider registrations | 1 |
| Fake live runtime invocations on approved fake path | 1 |
| Real DAACS invocations on approved fake path | 0 |
| Solar/provider calls on approved fake path | 0 |
| Executed actions on approved fake path | 0 |
| Generated files on approved fake path | 0 |
| Artifact manifest entries on approved fake path | 0 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Provider imports during eval | 0 |
| CLI agent invocations during eval | 0 |
| Subprocess calls during eval | 0 |
| Package install calls during eval | 0 |
| Server start calls during eval | 0 |
| Filesystem writes during eval | 0 |
| Network calls during eval | 0 |
| Raw secret exposure in tested public payload | 0 |

| Gate | Result |
|---|---|
| live without approval blocked | covered |
| malformed live approval blocked | covered |
| live without dry-run plan blocked | covered |
| unsafe `run_id` blocked without public exposure | covered |
| approval field validation | covered |
| workspace root boundary | covered |
| policy escalation blocked | covered |
| dry-run plan hash/state mismatch blocked | covered |
| fake live side-effect zero path | covered |
| process/file/network/import tripwire | covered |
| public payload sanitization | covered |

Interpretation: this measures fake live admission gate coverage only. It does not implement real DAACS execution, Solar Pro 3 provider calls, generated-code quality, install/build success, hosted success, or production readiness.

## AW-NEXT-09 Solar Pro 3 Provider Boundary Metrics

Measured after `ProviderRequest`, `ProviderApprovalRecord`, `ProviderResult`, and `FakeSolarProProvider` implementation.

| Metric | Value |
|---|---:|
| Pytest collected cases | 148 |
| Pytest passed cases | 148 |
| Regression delta vs AW-NEXT-08 baseline | +27 |
| Provider boundary test cases | 27 |
| Provider/request negative cases | 22 |
| Unsafe `run_id` public exposure regression cases | 1 |
| Secret/env read tripwire tests | 2 |
| Provider import tripwire tests | 2 |
| Offline/dry-run provider import regression tests | 1 |
| Fake provider invocations on approved fake path | 1 |
| Env key name references on approved fake path | 1 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Provider imports during eval | 0 |
| Provider secret value reads during eval | 0 |
| Network calls during eval | 0 |
| `.env` file reads during eval | 0 |
| Raw secret exposure in tested public payload | 0 |

| Gate | Result |
|---|---|
| provider approval missing blocked | covered |
| malformed provider approval blocked | covered |
| provider/request field mismatch blocked | covered |
| non-fake mode blocked | covered |
| invalid env key names blocked | covered |
| live API/LLM limits above 0 blocked | covered |
| invalid prompt contract hash blocked | covered |
| unsafe `run_id` blocked without public exposure | covered |
| fake provider success path live calls 0 | covered |
| `.env`/env secret value read tripwire | covered |
| Solar/Upstage/provider import tripwire | covered |
| offline/dry-run provider import regression | covered |
| public payload keeps env key name only | covered |

Interpretation: this measures provider boundary contract coverage only. It does not implement Solar Pro 3 API calls, Upstage SDK imports, real token usage, response quality, DAACS live execution, or production readiness.

## AW-NEXT-10 ProviderApproval Signature / Nonce Gate Metrics

Measured after structural approval signature fields and in-memory nonce replay guard were added to both fake live runner and fake provider boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 162 |
| Pytest passed cases | 162 |
| Regression delta vs AW-NEXT-09 baseline | +14 |
| Provider boundary test cases | 34 |
| Runner provider registry tests | 49 |
| New approval signature/replay test cases | 14 |
| Unsigned approval block fixtures | 2 |
| Tampered signed approval block fixtures | 2 |
| Reused nonce block fixtures | 4 |
| Malformed signature envelope fixtures | 6 |
| Approval signature fields added | 3 |
| Replay guard implementations | 1 process-local in-memory skeleton |
| Approval hash/audit public secret exposure in tested payloads | 0 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Provider imports during eval | 0 |
| Network calls during eval | 0 |
| `.env` file reads during eval | 0 |

| Gate | Result |
|---|---|
| provider unsigned approval blocked | covered |
| provider tampered signed approval blocked | covered |
| provider reused nonce blocked | covered |
| live unsigned approval blocked | covered |
| live tampered signed approval blocked | covered |
| live reused nonce blocked | covered |
| fresh provider/registry instance reused nonce blocked | covered |
| malformed signature envelope blocked | covered |
| expired approval blocked 유지 | covered by existing provider/live expiry fixtures |
| public runtime output excludes signature_id, nonce, signed_contract_hash | covered |

Interpretation: this is a structural approval gate skeleton. `signed_contract_hash` is internal canonical contract binding for tests, not a production cryptographic signature. The replay store is process-local in-memory and must become persistent before real live/provider execution.

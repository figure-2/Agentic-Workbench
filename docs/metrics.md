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

Current snapshot after `AW-NEXT-13` policy resolver, key identity registry, and durable replay boundary skeleton.

| Metric | Value |
|---|---:|
| Project files, excluding cache | 68 |
| Counted code/doc files, excluding cache | 68 |
| Project lines, excluding cache | 9,399 |
| Python files | 38 |
| Markdown files | 26 |
| Test files | 11 |
| Unit test files | 9 |
| Smoke test files | 2 |
| Integration test files | 0 |
| Pytest collected cases | 223 |
| Pytest passed cases | 223 |
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

## AW-NEXT-11 PersistentReplayStore / ApprovalVerifier Metrics

Measured after `PersistentReplayStore`, `ApprovalVerifier`, and `FakeApprovalVerifier` skeletons were added.

| Metric | Value |
|---|---:|
| Pytest collected cases | 172 |
| Pytest passed cases | 172 |
| Regression delta vs AW-NEXT-10 baseline | +10 |
| Approval security unit tests | 2 |
| Provider boundary test cases | 38 |
| Runner provider registry tests | 53 |
| New verifier/replay store test cases | 10 |
| Verifier-missing block fixtures | 2 |
| Verifier exception block fixtures | 2 |
| Replay store exception block fixtures | 2 |
| Restart simulation replay fixtures | 3 |
| Scope isolation fixtures | 1 |
| Fake verifier implementations | 1 |
| Replay store implementations | 1 export/import skeleton |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Provider imports during eval | 0 |
| Network calls during eval | 0 |
| Verifier secret value reads | 0 |
| Verifier key file reads | 0 |
| `.env` file reads during eval | 0 |

| Gate | Result |
|---|---|
| provider without verifier blocked | covered |
| live without verifier blocked | covered |
| provider verifier exception blocked without public leakage | covered |
| live verifier exception blocked without public leakage | covered |
| provider replay store exception blocks fake provider invocation | covered |
| live replay store exception blocks fake runtime invocation | covered |
| provider restart simulation reused authorization blocked | covered |
| live restart simulation reused authorization blocked | covered |
| replay store export excludes raw nonce | covered |
| same nonce across live/provider scopes remains isolated | covered |
| Solar Pro 3/DAACS live call 0 유지 | covered |

Interpretation: this adds verifier/store boundaries and restart-simulation coverage. It is still not production cryptographic signing, not durable disk/DB persistence, and not real Solar Pro 3 or DAACS live execution.

## AW-NEXT-12 ApprovalVerifier Policy / Key Identity Metrics

Measured after static verifier trust policy, key identity references, scope binding, and future approval timestamp skew gates were added to provider/live approval verification.

| Metric | Value |
|---|---:|
| Pytest collected cases | 201 |
| Pytest passed cases | 201 |
| Regression delta vs AW-NEXT-11 baseline | +29 |
| Approval security unit tests | 3 |
| Provider boundary test cases | 52 |
| Runner provider registry tests | 67 |
| New verifier policy/key identity test cases | 29 |
| Provider policy block fixtures | 7 |
| Live policy block fixtures | 7 |
| Custom verifier contract fixtures | 12 |
| Cross-boundary signature reuse fixtures | 2 |
| Direct verifier metric regression tests | 1 |
| Unknown verifier fixtures | 2 |
| Revoked verifier fixtures | 2 |
| Unknown key fixtures | 2 |
| Revoked key fixtures | 2 |
| Scope mismatch fixtures | 2 |
| Future `approved_at` skew fixtures | 2 |
| Approval identity fields added | 3 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Provider imports during eval | 0 |
| Network calls during eval | 0 |
| Verifier secret value reads | 0 |
| Verifier key file reads | 0 |
| Verifier policy public secret exposure | 0 |
| Solar Pro 3/DAACS live calls | 0 |

| Gate | Result |
|---|---|
| provider unknown verifier blocked | covered |
| provider revoked verifier blocked | covered |
| provider unknown key blocked | covered |
| provider revoked key blocked | covered |
| provider scope mismatch blocked | covered |
| provider future `approved_at` skew blocked | covered |
| live unknown verifier blocked | covered |
| live revoked verifier blocked | covered |
| live unknown key blocked | covered |
| live revoked key blocked | covered |
| live scope mismatch blocked | covered |
| live future `approved_at` skew blocked | covered |
| public output excludes verifier/key/signature/nonce/signed hash values | covered |
| Solar Pro 3/DAACS live call 0 유지 | covered |

Interpretation: this is a static policy/key identity skeleton for local boundary tests. It is not a production trust root, not key rotation, not external identity verification, and not real provider/runtime admission.

## AW-NEXT-13 ApprovalPolicyResolver / DurableReplayStore Metrics

Measured after resolver, registry, adapter-backed replay boundary skeletons, and public approval-field sanitizer coverage were added.

| Metric | Value |
|---|---:|
| Pytest collected cases | 223 |
| Pytest passed cases | 223 |
| Regression delta vs AW-NEXT-12 baseline | +22 |
| Approval security unit tests | 7 |
| Provider boundary test cases | 61 |
| Runner provider registry tests | 76 |
| New resolver/registry/durable replay test cases | 22 |
| Direct approval security fixtures | 4 |
| Provider resolver/registry/durable fixtures | 9 |
| Live resolver/registry/durable fixtures | 9 |
| Policy resolver block fixtures | 5 |
| Empty resolver/registry fixtures | 4 |
| Revoked key identity fixtures | 2 |
| Policy/key mismatch fixtures | 3 |
| Missing resolver/registry fixtures | 4 |
| Durable replay adapter unavailable fixtures | 3 |
| Durable restart replay fixtures | 3 |
| Public sanitizer sensitive approval key coverage | 7 fields |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Provider imports during eval | 0 |
| Network calls during eval | 0 |
| Verifier secret value reads | 0 |
| Verifier key file reads | 0 |
| Solar Pro 3/DAACS live calls | 0 |

| Gate | Result |
|---|---|
| unknown `policy_id` blocked | covered |
| missing policy resolver blocked | covered |
| missing key identity registry blocked | covered |
| revoked key identity blocked | covered |
| policy/key identity mismatch blocked | covered |
| replay adapter unavailable blocks admission | covered |
| process restart simulation preserves replay record | covered |
| public output excludes signature_id, signed_contract_hash, nonce, verifier/key/policy/key identity IDs | covered |
| Solar Pro 3/DAACS live call 0 유지 | covered |

Interpretation: this adds admission boundary skeletons only. Safe contract hashes such as `approval_hash`, `state_hash`, `plan_hash`, `prompt_contract_hash`, and `content_hash` remain allowed as sanitized correlation evidence. `DurableReplayStore` with the in-memory adapter simulates restart durability, but it is not atomic disk/DB persistence and is not a production replay store.

## AW-PERSIST-01 Repository Boundary Metrics

Measured after `RunSessionRepository` and `ArtifactRepository` skeletons were added.

| Metric | Value |
|---|---:|
| Pytest collected cases | 227 |
| Pytest passed cases | 227 |
| Regression delta vs AW-NEXT-13 baseline | +4 |
| Repository boundary unit tests | 4 |
| Raw prompt storage fields in run records | 0 |
| Raw artifact payload/body storage fields in artifact records | 0 |
| Read-model reconstruction tests | 1 |
| Cross-run artifact lineage rejection tests | 1 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Network calls during eval | 0 |

| Gate | Result |
|---|---|
| raw prompt/body storage blocked | covered |
| workflow read model reconstructed from sanitized rows | covered |
| artifact lineage `run_id` mismatch blocked | covered |
| repository stores metadata and correlation hashes only | covered |

Interpretation: this is an in-memory persistence boundary skeleton. It is not a DB-backed repository, migration, transaction layer, or production persistence guarantee.

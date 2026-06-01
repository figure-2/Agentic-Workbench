# Quantitative Baseline

## Measurement Date

2026-06-01

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

Current snapshot after `AW-LIVE-03` provider envelope read model.

| Metric | Value |
|---|---:|
| Project files, excluding cache and private SoT | 139 |
| Counted code/doc files, excluding cache and private SoT | 139 |
| Project lines, excluding cache and private SoT | 25,897 |
| Python files | 73 |
| Markdown files | 61 |
| Test files | 30 |
| Unit test files | 23 |
| Smoke test files | 6 |
| Integration test files | 1 |
| Pytest collected cases | 384 |
| Pytest passed cases | 384 |
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

Interpretation: this measures fake live admission gate coverage only. It does not implement DAACS source-runtime outcome, Solar Pro 3 provider calls, generated-code quality, install/build success, hosted success, or production readiness.

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

Interpretation: this measures provider boundary contract coverage only. It does not implement Solar Pro 3 API calls, Upstage SDK imports, real token usage, response quality, DAACS source-runtime outcome, or production readiness.

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

Interpretation: this adds verifier/store boundaries and restart-simulation coverage. It is still not production cryptographic signing, not durable disk/DB persistence, and not Solar Pro 3 or DAACS source-runtime outcome.

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

## AW-PERSIST-02 Approval / Replay Repository Metrics

Measured after `ApprovalRepository`, `ReplayNonceRepository`, and file-backed replay adapter skeletons were added.

| Metric | Value |
|---|---:|
| Pytest collected cases | 250 |
| Pytest passed cases | 250 |
| Regression delta vs AW-PERSIST-01 baseline | +23 |
| Repository boundary unit test files | 2 |
| New approval/replay repository test cases | 19 |
| New provider/live file-backed replay integration tests | 2 |
| New provider/live subject-bound approval reuse tests | 2 |
| Provider boundary test cases | 63 |
| Runner provider registry test cases | 78 |
| Approval subject snapshot record types | 1 |
| Approval decision record types | 1 |
| Replay nonce record types | 1 |
| Replay repository implementations | 2 |
| File-backed replay corrupted/partial/path fixtures | 3 |
| Atomic write failure preservation fixtures | 1 |
| Raw nonce/signature/verifier/key/policy identity fields in tested repository rows | 0 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Network calls during eval | 0 |
| Solar Pro 3/DAACS live calls | 0 |

| Gate | Result |
|---|---|
| immutable approval subject snapshot stores sanitized projection only | covered |
| approval record stores `subject_hash`, `approval_hash`, `scope_canonical` refs only | covered |
| raw authorization material storage count 0 | covered |
| supplied `scope_canonical` bound to subject hash | covered |
| canonical replay scope rejects unsafe public `run_id` | covered |
| durable replay row metadata cannot be defaulted | covered |
| file-backed durable row missing metadata blocked | covered |
| signed provider/live approval cannot authorize a different subject | covered |
| same canonical scope replay blocked | covered |
| process restart simulation keeps replay tombstone | covered |
| file-backed replay path traversal blocked | covered |
| corrupted/partial replay store blocked fail-closed | covered |
| atomic write failure preserves existing tombstone | covered |
| provider/live file-backed replay reuse blocked before fake runtime/provider invocation | covered |

Interpretation: this is a hash-only repository boundary skeleton with a local file-backed replay fixture. It is not production DB persistence, production cryptographic signing, multi-host replay prevention, DAACS source-runtime outcome, or Solar Pro 3 live provider integration.

## AW-PARITY-00 Public API / Fixture Boundary Metrics

Measured after public API projection, fixture mode markers, raw-field denylist
expansion, and claim scanner expansion were added.

| Metric | Value |
|---|---:|
| Pytest collected cases | 255 |
| Pytest passed cases | 255 |
| Regression delta vs AW-PERSIST-02 baseline | +5 |
| New public projection unit tests | 3 |
| New API integration tests | 1 |
| New claim scanner fixture tests | 1 |
| Public API raw prompt exposure fixtures | 0 exposed |
| Public API raw log/file body exposure fixtures | 0 exposed |
| Public API provider payload exposure fixtures | 0 exposed |
| Public API approval auth material exposure fixtures | 0 exposed |
| Fixture/synthetic marker coverage in API fixture path | covered |
| `WorkflowSession.to_dict()` direct API return | 0 covered paths |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Network calls during eval | 0 |
| Solar Pro 3/DAACS live calls | 0 |

| Gate | Result |
|---|---|
| API response uses sanitized public projection | covered |
| fixture planner does not copy raw input into public problem text | covered |
| public sanitizer drops raw prompt/log/file/provider/approval auth fields | covered |
| public event/session projection blocks forbidden claim language | covered |
| public correlation IDs remain visible after redaction | covered |

Interpretation: this closes the fixture API exposure boundary before source
identity parity fixtures are added. It does not claim external provider outcome,
DAACS source-runtime outcome, source-runtime reproduction, generated-app production, or
production API security.

## AW-PARITY-01A Source Identity Fixture Metrics

Measured after DIV and DAACS test-only source identity fixtures were added.

| Metric | Value |
|---|---:|
| Pytest collected cases | 260 |
| Pytest passed cases | 260 |
| Regression delta vs AW-PARITY-00 baseline | +5 |
| Source identity fixture files | 1 |
| Source identity unit tests | 5 |
| Source fixtures | 4 |
| DIV fixture trace rows | 4 |
| DAACS fixture trace rows | 4 |
| Required trace-row parity coverage | 8 / 8 |
| Public fixture forbidden key findings | 0 |
| Public fixture forbidden claim findings | 0 |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Network calls during eval | 0 |
| Solar Pro 3/DAACS live calls | 0 |

| Gate | Result |
|---|---|
| DIV planning/PRD/evidence/visual identity signals fixed as fixture | covered |
| DAACS backend/frontend/API/state/verifier/runner identity signals fixed as fixture | covered |
| fixture avoids raw source body, system prompt, provider payload, and file body | covered |
| fixture hash is deterministic | covered |

Interpretation: this creates the parity reference set only. It does not run
source runtimes, generate an app, execute CLI tools, call providers, or prove
source-runtime reproduction.

## AW-PARITY-01B Source Identity Golden Path Metrics

Measured after connecting the source identity fixture to the Workbench artifact
chain through the dry-run runner.

| Metric | Value |
|---|---:|
| Pytest collected cases | 261 |
| Pytest passed cases | 261 |
| Regression delta vs AW-PARITY-01A baseline | +1 |
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
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Network calls during eval | 0 |
| Direct source-runtime calls during eval | 0 |
| Subprocess/package/server/filesystem write counters | 0 |

| Gate | Result |
|---|---|
| Idea -> PlanningBlueprint -> PRDPackage -> ImplementationBrief -> SpecApproval -> RunnerPlan -> VerificationReport | covered |
| DIV section/visual/evidence identity reflected in artifacts | covered |
| DAACS backend/frontend/API split reflected in BuildSpec and RunnerPlan | covered |
| VerificationReport dry-run checks and metrics reflected | covered |
| public leakage scan uses public projection, not internal safety contracts | covered |

Interpretation: this proves fixture-based source identity preservation through
the local artifact chain. It does not run source runtimes, generate an app, call
providers, or prove production readiness.

## AW-PARITY-01C Trace And Claim Projection Metrics

Measured after mapping AW-PARITY-01B smoke evidence to source-to-target trace
rows and scanner-safe public wording.

| Metric | Value |
|---|---:|
| Pytest collected cases | 264 |
| Pytest passed cases | 264 |
| Regression delta vs AW-PARITY-01B baseline | +3 |
| Trace rows linked to 01B smoke evidence | 8 |
| DIV trace rows linked | 4 |
| DAACS trace rows linked | 4 |
| Public claim docs scanned | 7 |
| Public claim doc forbidden findings | 0 |
| Public-safe portfolio wording blocks | 1 |
| Public-safe block forbidden key findings | 0 |
| README forbidden claim findings | 0 |
| Metrics/eval public forbidden claim findings | 0 |
| Solar Pro 3/DAACS live calls | 0 |

| Gate | Result |
|---|---|
| source-to-target trace rows linked to 01B smoke evidence | covered |
| README/portfolio wording separates fixture, dry-run, and target-only runtime surfaces | covered |
| DIV/DAACS identity preservation evidence linked to test names | covered |
| public claim projection remains scanner-safe | covered |

Interpretation: this closes the documentation and claim boundary for the
fixture-based parity evidence. It does not add runtime execution, provider
calls, generated files, hosted status, or production readiness.

## AW-PERSIST-03 Runner / Report / Audit Repository Metrics

Measured after adding sanitized projection repositories for runner plans,
verification reports, and audit events.

| Metric | Value |
|---|---:|
| Pytest collected cases | 280 |
| Pytest passed cases | 280 |
| Regression delta vs AW-PARITY-01C baseline | +16 |
| Runner/report/audit repository tests | 16 |
| New repository protocols | 3 |
| New in-memory repository implementations | 3 |
| New projection record types | 3 |
| New linkage validation helper | 1 |
| Extended forbidden public key classes | 9 |
| Focused repository regression result | 127 / 127 passed |
| RunnerPlan raw planned payload/body findings in record | 0 |
| VerificationReport raw log/file body findings in record | 0 |
| AuditEvent provider/runtime payload findings in record | 0 |
| Repository projection forbidden key findings | 0 |
| Repository projection forbidden claim findings | 0 |
| Solar Pro 3/DAACS live calls | 0 |

| Gate | Result |
|---|---|
| RunnerPlan stores hash/count/role projection only | covered |
| VerificationReport stores counts and hashes, not raw errors/logs/files | covered |
| AuditEvent stores metadata and hashes, not provider/runtime payloads | covered |
| run/report/audit linkage rejects cross-run rows | covered |
| source artifact references resolve to artifact repository rows | covered |
| public repository projection remains scanner-safe | covered |

Interpretation: this adds repository skeletons for sanitized runner/report/audit
evidence. It does not add DB-backed persistence, generated app delivery, live
runtime execution, external provider outcome, or production readiness.

## AW-PERSIST-04 SQLite Runner / Report / Audit Adapter Metrics

Measured after adding a SQLite adapter skeleton for sanitized runner/report/audit
projection rows and source artifact linkage rows.

| Metric | Value |
|---|---:|
| Pytest collected cases | 297 |
| Pytest passed cases | 297 |
| Regression delta vs AW-PERSIST-03 baseline | +17 |
| SQLite runner/report/audit tests | 16 |
| Runner/report/audit repository tests | 17 |
| SQLite schema migration version | 1 |
| SQLite projection tables | 4 |
| SQLite explicit indexes | 5 |
| SQLite unique constraint classes | 3 |
| Public claim docs scanned | 10 |
| DB row raw planned payload/body findings | 0 |
| DB row raw log/file body findings | 0 |
| DB row provider/runtime payload findings | 0 |
| DB row forbidden public key findings | 0 |
| DB row forbidden claim findings | 0 |
| Partial rows after rollback fixture | 0 |
| Target runtime calls | 0 |

| Gate | Result |
|---|---|
| SQLite schema migration is idempotent | covered |
| corrupted, unavailable, partial, and path traversal DB setup blocked | covered |
| duplicate plan/report/audit rows blocked by constraints | covered |
| source artifact, runner plan, report, and audit chain linkage enforced | covered |
| cross-run artifact/plan/report/audit linkage blocked | covered |
| wrong-column partial schema blocked | covered |
| rollback leaves no partial rows | covered |
| public architecture/eval claim docs remain scanner-safe | covered |

Interpretation: this adds a local SQLite adapter skeleton for sanitized
projection rows. It does not add production persistence, target runtime
execution, external provider outcome, generated app delivery, or production
readiness.

## AW-PERSIST-05 SQLite Approval / Replay Adapter Metrics

Measured after adding a separate SQLite adapter skeleton for sanitized approval
subject, approval decision, and replay nonce rows.

| Metric | Value |
|---|---:|
| Pytest collected cases | 312 |
| Pytest passed cases | 312 |
| Regression delta vs AW-PERSIST-04 baseline | +15 |
| SQLite approval/replay tests | 15 |
| SQLite approval/replay schema migration version | 1 |
| SQLite approval/replay tables | 3 |
| SQLite approval/replay explicit indexes | 3 |
| SQLite approval/replay unique constraint classes | 3 |
| Approval/replay public claim docs scanned | 12 |
| DB row raw authorization material findings | 0 |
| DB row raw replay nonce findings | 0 |
| DB row forbidden public key findings | 0 |
| DB row forbidden claim findings | 0 |
| Partial approval/replay rows after rollback fixture | 0 |
| Target runtime calls | 0 |

| Gate | Result |
|---|---|
| SQLite approval/replay schema migration is idempotent | covered |
| approval subject and approval rows round-trip as sanitized projections | covered |
| raw authorization material in subject or text fields rejected | covered |
| duplicate `snapshot_hash` and `approval_hash` blocked | covered |
| duplicate `(scope_canonical, nonce_hash)` replay tombstone blocked | covered |
| reused nonce after store restart blocked | covered |
| fixture/synthetic approval rows blocked from SQLite durable adapter | covered |
| tampered approval scope and snapshot linkage blocked | covered |
| replay tombstone approval scope mismatch blocked | covered |
| mixed SQLite store schema file blocked | covered |
| direct non-hash record insertion blocked | covered |
| corrupted, unavailable, partial, wrong-column, and wrong-contract schema blocked | covered |
| relaxed approval/replay check constraint schema blocked | covered |
| rollback leaves no partial approval/replay rows | covered |
| public architecture/eval claim docs remain scanner-safe | covered |

Interpretation: this adds a local SQLite adapter skeleton for approval/replay
projection rows. It does not add production persistence, external provider
outcome, target runtime outcome, generated app delivery, hosted status, or
production-grade approval trust.

## AW-PERSIST-06 Approval / Replay Factory Wiring Metrics

Measured after adding an explicit repository factory and optional SQLite-backed
replay wiring for fake provider/live admission gates.

| Metric | Value |
|---|---:|
| Pytest collected cases | 323 |
| Pytest passed cases | 323 |
| Regression delta vs AW-PERSIST-05 baseline | +11 |
| Repository factory tests | 5 |
| Provider SQLite admission wiring tests | 3 |
| Live SQLite admission wiring tests | 3 |
| Repository backends covered | 3 |
| SQLite replay repository selected by factory | covered |
| Canonical approval row precondition before replay claim | covered |
| Missing canonical approval row before replay claim | blocked |
| Provider reused nonce after process restart simulation | blocked |
| Live reused nonce after process restart simulation | blocked |
| Unavailable SQLite repository root | blocked |
| Corrupted SQLite DB before fake provider invocation | blocked |
| Corrupted SQLite DB before fake runtime invocation | blocked |
| Fixture/synthetic approval durable storage | blocked |
| DB row raw authorization material findings | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| memory/file/SQLite approval replay factory selection | covered |
| SQLite-backed replay path requires canonical approval evidence before nonce claim | covered |
| missing canonical approval row fails closed before fake invocation | covered |
| provider boundary blocks reused SQLite nonce before fake invocation | covered |
| live boundary blocks reused SQLite nonce before fake invocation | covered |
| unavailable/corrupted SQLite storage fails closed before fake invocation | covered |
| public architecture/eval claim docs remain scanner-safe | covered |

Interpretation: this is optional local wiring for fake admission gates. It does
not add production persistence, external provider outcome, target runtime
outcome, generated app delivery, hosted status, or production approval trust.

## AW-PERSIST-07 Canonical Approval Persistence Service Metrics

Measured after adding the service boundary that persists canonical provider/live
approval rows before durable replay claim.

| Metric | Value |
|---|---:|
| Pytest collected cases | 326 |
| Pytest passed cases | 326 |
| Regression delta vs AW-PERSIST-06 baseline | +3 |
| Provider approval persistence service tests | 2 |
| Live approval persistence service tests | 2 |
| Canonical approval service implementation files | 1 |
| Provider/live fake admission paths using service | 2 |
| Missing persistence service block fixtures | 2 |
| Duplicate canonical approval handling | idempotent |
| Raw nonce/signature/signed contract hash findings in persisted rows | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| provider canonical approval row persisted before replay claim | covered |
| live canonical approval row persisted before replay claim | covered |
| persisted approval hash equals canonical helper hash | covered |
| missing service fails closed before fake provider/runtime invocation | covered |
| duplicate canonical approval row is idempotent | covered |
| corrupted SQLite approval store fails closed before fake runtime | covered |
| public architecture/eval claim docs remain scanner-safe | covered |

Interpretation: this is a local service boundary for canonical approval
persistence before fake admission replay claim. It is not production
persistence, external provider outcome, target runtime outcome, generated app
delivery, hosted status, or production approval trust.

## AW-API-01 Sanitized Approval Admission API Metrics

Measured after adding API-facing fake provider/live admission demo paths that
reuse `CanonicalApprovalPersistenceService` before replay claim.

| Metric | Value |
|---|---:|
| Pytest collected cases | 329 |
| Pytest passed cases | 329 |
| Regression delta vs AW-PERSIST-07 baseline | +3 |
| API admission service implementation files | 1 |
| New API integration tests | 3 |
| Fake provider admission API paths | 1 |
| Fake live admission API paths | 1 |
| Fixture/synthetic rejection API tests | 1 |
| Public response raw nonce/signature/signed contract findings | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| provider API path uses canonical approval persistence service | covered |
| live API path uses canonical approval persistence service | covered |
| fixture/synthetic approval path remains separate from durable demo path | covered |
| public API response excludes raw authorization fields | covered |
| provider/live fake admission stores approval row before replay claim | covered |
| fake admission keeps provider/runtime calls at zero | covered |
| public eval claim docs remain scanner-safe | covered |

Interpretation: this is local API/service wiring for fake admission paths. It
is not a public approval product, production persistence, external provider
outcome, target runtime outcome, generated app delivery, hosted status, or
production approval trust. The current API demo uses request-scoped memory
repositories and does not prove cross-request durable evidence.

## AW-API-02 SQLite Admission Repository Wiring Metrics

Measured after adding explicit API repository backend selection and SQLite
request persistence wiring for fake admission paths.

| Metric | Value |
|---|---:|
| Pytest collected cases | 335 |
| Pytest passed cases | 335 |
| Regression delta vs AW-API-01 baseline | +6 |
| API admission integration tests | 9 |
| New SQLite-backed API tests | 6 |
| Configurable admission repository backends in API | 2 |
| Provider repeated nonce across API requests | blocked |
| Live repeated nonce across API requests | blocked |
| Corrupted SQLite store before fake provider invocation | blocked |
| Corrupted SQLite store before fake runtime invocation | blocked |
| Unavailable SQLite store before fake provider invocation | blocked |
| Fixture `/api/v1/runs` durable admission store writes | 0 |
| Public response raw nonce/signature/signed contract findings | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| API fake admission can select explicit SQLite approval/replay repository | covered |
| SQLite replay evidence persists across API requests in the same configured app | covered |
| repeated provider/live nonce blocks before fake invocation | covered |
| corrupted/unavailable SQLite store fails closed before fake provider invocation | covered |
| fixture/synthetic run path stays separate from durable admission store | covered |
| public response returns backend markers but not database root path | covered |

Interpretation: this is local SQLite-backed API wiring for fake admission
evidence. It does not add a hosted approval system, multi-host replay
protection, external provider outcome, target runtime outcome, generated app
delivery, or production approval trust.

## AW-API-03 Evidence Read Model API Metrics

Measured after adding a sanitized read-only API over local repository evidence
projections.

| Metric | Value |
|---|---:|
| Pytest collected cases | 338 |
| Pytest passed cases | 338 |
| Regression delta vs AW-API-02 baseline | +3 |
| API evidence read-model tests | 3 |
| Evidence read-model API paths | 1 |
| Runner/report/audit repository backends exposed by API | 1 |
| Approval/replay repository backends reused by API | 2 |
| Raw planned payload/log/file/provider/runtime body findings | 0 |
| Raw approval authorization material findings | 0 |
| Local DB root path findings | 0 |
| Cross-run evidence leakage findings | 0 |
| Corrupted runner/report/audit store | blocked |
| Corrupted approval/replay store | blocked |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| stored runner plan evidence exposed as hash/count projection | covered |
| stored verification report evidence exposed as hash/count projection | covered |
| stored audit event evidence exposed as metadata/hash projection | covered |
| approval/replay evidence exposed as sanitized projection rows | covered |
| corrupted evidence store fails closed without path exposure | covered |
| read-model API keeps provider/runtime calls at 0 | covered |

Interpretation: this is a local read-model API for sanitized repository
evidence. It does not execute providers, run the target runtime, generate an
application, host an evidence service, or certify repository trust.

## AW-API-04 Fixture Evidence Persistence Metrics

Measured after adding an optional write path from `/api/v1/runs` fixture output
to the configured local runner/report/audit evidence repository.

| Metric | Value |
|---|---:|
| Pytest collected cases | 340 |
| Pytest passed cases | 340 |
| Regression delta vs AW-API-03 baseline | +2 |
| API evidence write-path integration tests | 2 |
| Evidence write service implementation files | 1 |
| Fixture runner plan rows persisted per configured run | 1 |
| Fixture verification report rows persisted per configured run | 1 |
| Fixture audit event rows persisted per configured run | 3 |
| Fixture path durable approval/replay rows | 0 |
| Raw prompt/log/file/provider/runtime findings in run response | 0 |
| Raw prompt/log/file/provider/runtime findings in read-model response | 0 |
| Local DB root path findings in public response | 0 |
| Corrupted evidence store | blocked |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| `/api/v1/runs` persists evidence only when explicit evidence repo is configured | covered |
| configured fixture evidence can be read back by `GET /api/v1/evidence/runs/{run_id}` | covered |
| fixture path stays separate from durable approval/replay storage | covered |
| corrupted evidence DB fails closed without path/raw echo | covered |
| public response keeps provider/runtime calls at 0 | covered |

Interpretation: this adds local fixture evidence persistence for sanitized
repository projections. It does not add external provider outcome, target
runtime outcome, generated app delivery, hosted evidence service, or repository
trust certification.

## AW-API-05 Run / Artifact Read API Metrics

Measured after adding repository-backed read APIs for sanitized run and artifact
projection rows.

| Metric | Value |
|---|---:|
| Pytest collected cases | 342 |
| Pytest passed cases | 342 |
| Regression delta vs AW-API-04 baseline | +2 |
| API run/artifact read integration tests | 2 |
| Run/artifact read API paths | 2 |
| Artifact payload body findings | 0 |
| Raw prompt/log/file/provider/runtime findings | 0 |
| Cross-run leakage findings | 0 |
| Durable approval/replay evidence mixed into run/artifact read API | 0 |
| Canonical run-session state claims | 0 |
| Corrupted evidence store | blocked |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| `GET /api/v1/runs/{run_id}` returns local projection summary | covered |
| `GET /api/v1/runs/{run_id}/artifacts` returns local artifact projection rows | covered |
| approval/replay repositories are not queried by run/artifact read APIs | covered |
| corrupted evidence DB fails closed without path/raw echo | covered |
| public response keeps provider/runtime calls at 0 | covered |

Interpretation: this adds local read APIs for sanitized repository projections.
It does not add canonical run-session state, raw artifact storage, durable
approval authority, external provider outcome, target runtime outcome, generated
app delivery, hosted read service, or repository trust certification.

## AW-PERSIST-08 SQLite Run / Artifact Repository Metrics

Measured after adding a separate SQLite adapter skeleton for canonical
run-session and artifact projection rows.

| Metric | Value |
|---|---:|
| Pytest collected cases | 348 |
| Pytest passed cases | 348 |
| Regression delta vs AW-API-05 baseline | +6 |
| SQLite run/artifact repository unit tests | 5 |
| API public projection integration tests | 18 |
| Canonical run/artifact SQLite tables | 2 |
| Canonical run/artifact explicit indexes | 3 |
| Raw prompt findings in canonical DB rows | 0 |
| Artifact payload body findings in canonical DB rows | 0 |
| Cross-run artifact leakage findings | 0 |
| Evidence DB queried by canonical read API | 0 |
| Approval/replay DB queried by canonical read API | 0 |
| Corrupted canonical store | blocked |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| `/api/v1/runs` persists sanitized `RunSessionRecord` when explicitly configured | covered |
| `GET /api/v1/runs/{run_id}` returns canonical run projection fields | covered |
| `GET /api/v1/runs/{run_id}/artifacts` returns artifact metadata rows | covered |
| canonical DB file is separate from evidence and approval/replay DB files | covered |
| mixed SQLite schema files fail closed | covered |
| transaction rollback leaves no partial run/artifact rows | covered |
| public response keeps provider/runtime calls at 0 | covered |

Interpretation: this adds local canonical run/artifact projection persistence.
It does not add external provider outcome, target runtime outcome, generated app
delivery, hosted persistence, or repository trust certification.

## AW-API-06 Run / Evidence Composition Metrics

Measured after making `GET /api/v1/runs/{run_id}` return canonical run state
plus an optional sanitized evidence summary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 350 |
| Pytest passed cases | 350 |
| Regression delta vs AW-PERSIST-08 baseline | +2 |
| API public projection integration tests | 20 |
| Composed run read API paths | 1 |
| Canonical run/artifact primary store queried | covered |
| Optional evidence summary section | covered |
| Missing evidence store canonical lookup block count | 0 |
| Corrupted evidence store canonical lookup block count | 0 |
| Corrupted evidence store evidence summary blocked | covered |
| Corrupted canonical store canonical lookup blocked | covered |
| Raw prompt/log/file/provider/runtime findings | 0 |
| Raw approval authorization material findings | 0 |
| Cross-run leakage findings | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| `GET /api/v1/runs/{run_id}` returns canonical run state with evidence summary | covered |
| missing evidence repository reports evidence `unconfigured` while canonical lookup passes | covered |
| corrupted evidence repository blocks only evidence summary section | covered |
| repository boundary records which stores were queried | covered |
| public response keeps provider/runtime calls at 0 | covered |

Interpretation: this adds local read-model composition for sanitized projection
rows. It does not add live observability, production monitoring, external
provider outcome, target runtime outcome, generated app delivery, hosted
persistence, or repository trust certification.

## AW-DEMO-01 Local Service-Shaped Demo Metrics

Measured after adding the local demo script and smoke tests.

| Metric | Value |
|---|---:|
| Pytest collected cases | 352 |
| Pytest passed cases | 352 |
| Regression delta vs AW-API-06 baseline | +2 |
| Demo scripts | 1 |
| Demo README files | 1 |
| Demo smoke tests | 2 |
| Demo artifact count in current fixture | 6 |
| Demo runner plan evidence count | 1 |
| Demo verification report evidence count | 1 |
| Demo audit event evidence count | 3 |
| Structural repeatability fixtures | 2 fresh stores |
| Raw prompt/log/file/provider/runtime findings | 0 |
| Raw approval authorization material findings | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| demo creates a run through `POST /api/v1/runs` | covered |
| demo reads composed run state through `GET /api/v1/runs/{run_id}` | covered |
| demo uses canonical and evidence SQLite stores configured server-side | covered |
| DIV identity signals appear through planning/PRD artifacts | covered |
| DAACS identity signals appear through BuildSpec, ImplementationBrief, RunnerPlan, VerificationReport | covered |
| public demo summary keeps provider/runtime calls at 0 | covered |

Interpretation: this is a local fixture/dry-run demo over the public API and
composed read model. It does not add Solar Pro 3 integration, DAACS target
runtime execution, original DIV live graph execution, generated app delivery,
hosted demo behavior, production persistence, or production observability.

## AW-DEMO-02 Minimal Run Status Surface Metrics

Measured after adding the reviewer-facing Markdown/CLI status surface.

| Metric | Value |
|---|---:|
| Pytest collected cases | 354 |
| Pytest passed cases | 354 |
| Regression delta vs AW-DEMO-01 baseline | +2 |
| Status surface scripts | 1 |
| Status surface smoke tests | 2 |
| Status report sections | 9 |
| Raw prompt findings | 0 |
| Raw artifact body findings | 0 |
| Raw provider/runtime payload findings | 0 |
| Raw approval signature/nonce value findings | 0 |
| Local store path findings | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| `render_status_surface(summary)` returns Markdown report | covered |
| report includes run, artifact chain, DIV, DAACS, evidence, execution, claim, checks, next action | covered |
| report consumes public demo summary rather than SQLite internals | covered |
| report keeps provider/runtime calls at 0 | covered |

Interpretation: this adds a local reviewer-facing status surface over sanitized
fixture/dry-run projections. It does not add a web dashboard, hosted
observability, live runtime monitoring, provider integration, target runtime
execution, or generated app delivery.

## AW-LIVE-00 Live-Open Policy Gate Metrics

Measured after adding the fail-closed live-open readiness policy gate.

| Metric | Value |
|---|---:|
| Pytest collected cases | 360 |
| Pytest passed cases | 360 |
| Regression delta vs AW-DEMO-02 baseline | +6 |
| Live-open policy unit tests | 6 |
| Supported readiness surfaces | 2 |
| Required readiness controls | 10 |
| Unknown surface block cases | covered |
| Missing control block cases | covered |
| Requested call/write/network attempt block cases | covered |
| Forbidden public key findings | 0 |
| Env secret value reads | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| default request with missing controls blocks | covered |
| unknown surface blocks | covered |
| complete readiness remains `allowed_to_execute=false` | covered |
| Solar provider references only env key name | covered |
| DAACS target runtime rejects provider env key names | covered |
| public response keeps provider/runtime calls at 0 | covered |

Interpretation: this adds a local readiness policy gate for future
provider/runtime work. It does not add Solar Pro 3 integration, DAACS target
runtime execution, generated app delivery, hosted execution, production signing,
production key registry, or production sandbox enforcement.

## AW-DEMO-03 Static UI Shell Metrics

Measured after adding the local static HTML shell over the public demo summary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 362 |
| Pytest passed cases | 362 |
| Regression delta vs AW-LIVE-00 baseline | +2 |
| Static UI scripts | 1 |
| Static UI smoke tests | 2 |
| Static UI sections | 7 |
| Public summary input path | covered |
| Raw prompt findings | 0 |
| Raw artifact body findings | 0 |
| Raw provider/runtime payload findings | 0 |
| Raw approval authorization findings | 0 |
| Local path findings | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| `render_static_ui_shell(summary)` returns complete HTML | covered |
| HTML marks `public-summary-only` projection | covered |
| HTML displays live policy as `closed / eligible only` | covered |
| HTML keeps execution permission closed | covered |
| HTML can be written only through explicit `--output` | covered |
| public response keeps provider/runtime calls at 0 | covered |

Interpretation: this adds a local static UI shell for the fixture/dry-run demo.
It does not add a hosted dashboard, production UI, browser runtime integration,
external provider outcome, target runtime outcome, or generated app delivery.

## AW-LIVE-01 Disabled Solar Pro 3 Provider Adapter Metrics

Measured after adding the disabled Solar Pro 3 live-path adapter skeleton.

| Metric | Value |
|---|---:|
| Pytest collected cases | 369 |
| Pytest passed cases | 369 |
| Regression delta vs AW-DEMO-03 baseline | +7 |
| Solar live adapter unit tests | 7 |
| Registered provider modes tested | 2 |
| Default invocation blocked | covered |
| Missing live-open policy blocked | covered |
| Missing timeout/cost/quota blocked | covered |
| Fake/live provider path separation | covered |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| disabled live adapter can be registered | covered |
| adapter rejects fake mode | covered |
| eligible live-open policy still keeps execution permission closed | covered |
| public output forbidden key findings | 0 |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a disabled local adapter skeleton for a future Solar
Pro 3 provider path. It does not add SDK integration, external provider
outcome, model-quality proof, token/cost metering implementation, hosted
execution, or production provider readiness.

## AW-LIVE-02 Solar Pro 3 Contract Fixture Metrics

Measured after adding no-call request/response contract fixtures and
cost/timeout policy checks.

| Metric | Value |
|---|---:|
| Pytest collected cases | 376 |
| Pytest passed cases | 376 |
| Regression delta vs AW-LIVE-01 baseline | +7 |
| Solar contract unit tests | 7 |
| Cost/timeout policy check count | 5 |
| Request contract fixture count | 1 |
| Response projection fixture count | 1 |
| Raw input/body/provider leakage findings | 0 |
| Forbidden public key findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| request fixture uses `prompt_contract_hash` only | covered |
| timeout/cost/API quota/token quota omissions block | covered |
| invalid prompt contract hash blocks | covered |
| fake mode blocks in request contract fixture | covered |
| response projection uses sanitized summary and hashes only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds no-call contract fixtures for a future Solar Pro 3
provider path. It does not add SDK integration, provider response parsing,
external provider outcome, model-quality proof, live cost metering, hosted
execution, or production provider readiness.

## AW-LIVE-03 Provider Envelope Persistence and Read Model Metrics

Measured after adding hash-only provider envelope persistence and public read
model projection for no-call Solar contract evidence.

| Metric | Value |
|---|---:|
| Pytest collected cases | 384 |
| Pytest passed cases | 384 |
| Regression delta vs AW-LIVE-02 baseline | +8 |
| Provider envelope unit tests | 8 |
| Provider envelope SQLite tables | 2 |
| Public read-model envelope field count | 9 |
| Raw prompt/provider body/provider payload DB findings | 0 |
| Forbidden public key findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| request contract hash stored | covered |
| response contract hash stored | covered |
| DB rows exclude raw prompt/provider body/provider payload | covered |
| public read model returns hash/count/status fields only | covered |
| corrupted SQLite store blocked | covered |
| unavailable SQLite store blocked | covered |
| wrong-schema SQLite store blocked | covered |
| escaping SQLite filename blocked | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds no-call provider envelope evidence storage and read
model projection. It does not add SDK integration, provider response parsing,
external provider outcome, model-quality proof, hosted execution, or production
provider readiness.

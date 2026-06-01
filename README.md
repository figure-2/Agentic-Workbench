# Agentic Workbench

Agentic Workbench는 아이디어를 명세, 승인, dry-run 실행 계획, 검증 리포트로 연결하는 로컬/개발용 AI agent workflow harness prototype이다.

이 프로젝트의 중심은 앱 생성 결과를 주장하는 것이 아니라, agent workflow가 실행되기 전에 필요한 계약, 승인, 실행 계획, 검증 경계를 명시하는 것이다.

## Problem

LLM에게 앱 구현을 한 번에 맡기면 요구사항 누락, 문서와 코드의 불일치, 실행 전 위험 확인 부족, 검증 누락이 동시에 발생할 수 있다. Agentic Workbench는 이 과정을 artifact pipeline으로 나누고, 승인 전 handoff와 side effect를 통제한다.

## Identity

```text
Agentic Workbench
AI Agent Workflow Harness

Current path:
IdeaBrief
-> PlanningBlueprint
-> PRDPackage / BuildSpec
-> ImplementationBrief
-> SpecApproval
-> offline validation
-> dry-run RunnerPlan
-> fake-only admission gates
-> VerificationReport
```

## Architecture

```mermaid
flowchart TD
    A["User Idea"] --> B["Planning Contract"]
    B --> C["PlanningBlueprint"]
    C --> D["PRDPackage"]
    C --> E["BuildSpec"]
    D --> F["ImplementationBrief"]
    E --> F
    F --> G{"SpecApproval"}
    G -- "changes requested" --> B
    G -- "approved" --> H["Offline Validation"]
    H --> I["Dry-run RunnerPlan"]
    I --> J["Fake-only Admission Gates"]
    J --> K["VerificationReport"]
    G -- "missing or mismatched" --> L["Blocked"]
    H -- "contract failure" --> L
    J -- "policy or replay failure" --> L
```

## Current MVP Scope

Current implementation:

- Shared contracts: `IdeaBrief`, `PlanningBlueprint`, `PRDPackage`, `ImplementationBrief`, `SpecApproval`, `BuildSpec`, `RunnerPlan`, `VerificationReport`
- Planning-state adapter that preserves idea, plan sections, research evidence, visual requirements, and markdown structure
- Build-spec adapter that derives API, frontend, data model, and acceptance criteria contracts
- Human-reviewable `PRDPackage` and execution-oriented `ImplementationBrief`
- `SpecApproval` gate that blocks missing or mismatched approval
- Offline validation for execution-state compatibility
- Side-effect-free dry-run runner that emits `RunnerPlan`
- Fail-closed runner provider registry for offline, dry-run, and gated fake paths
- Fake-only admission gates for future live/provider boundaries
- In-memory repository boundaries for sanitized run and artifact read models
- In-memory repository boundaries for sanitized runner plan, verification report, and audit event read models
- SQLite adapter skeleton for sanitized runner plan, verification report, audit event, and source artifact projection rows
- SQLite adapter skeleton for sanitized approval subject, approval decision, and replay nonce rows
- Separate SQLite adapter skeleton for sanitized canonical run-session and artifact rows
- Public API projection for sanitized fixture responses with fixture/synthetic markers
- Sanitized fake provider/live admission API demo paths that reuse canonical approval persistence
- Explicit SQLite-backed fake admission API wiring for cross-request replay evidence
- Sanitized evidence read-model API for persisted runner/report/audit and approval/replay rows
- Optional fixture evidence write path for `/api/v1/runs` into sanitized local runner/report/audit rows
- Repository-backed run/artifact read APIs for sanitized local projection rows
- Canonical run/artifact read APIs for sanitized local run-session and artifact rows
- Composed canonical run/evidence read API that keeps canonical run state primary and evidence as a sanitized summary
- Local service-shaped demo script over the public API and composed read model
- Minimal Markdown/CLI run status surface over the local demo summary
- Fail-closed live-open policy gate for future Solar Pro 3 / DAACS target runtime work
- Static HTML UI shell over the same sanitized public demo summary
- Disabled-by-default Solar Pro 3 provider adapter skeleton with fake/live path separation
- No-call Solar Pro 3 request/response contract fixtures with cost/timeout policy checks
- Provider envelope persistence/read-model projection for no-call Solar contract evidence
- Provider envelope admission service before disabled Solar adapter invocation
- Provider envelope admission API/read-model hook for local no-call precheck evidence
- Operator approval envelope for provider precheck policy summary hash binding
- Live provider dry-admission checklist and manual runbook projection
- Manual provider test proposal gate that remains disabled by default
- Disabled manual provider test executor boundary
- Blocked manual provider test review packet for policy/preflight/readiness hashes
- Hash-only manual provider test review packet export/read-model
- Final no-call manual provider test handoff packet over policy/preflight/readiness/review/export hashes
- First live-call operator opt-in checklist bound to the handoff packet hash, still execution-closed
- Sealed pre-execution packet over handoff, opt-in, cost/timeout/quota, and rollback/abort hashes
- No-call live execution arming record over sealed packet, operator, expiry, rollback, and abort hashes
- No-call execution authorization release proposal over arming record, operator, release window, and rollback hashes
- No-call final release packet over release proposal, arming record, operator, release window, and rollback hashes
- Disabled first-call execution switch over final release packet and switch-enable hashes
- Disabled first-call executor preflight over execution switch, final release packet, and no-call counter hashes
- Disabled first-call executor dispatch record over executor preflight, planned dispatch, and no-call counter hashes
- Disabled first-call invocation receipt over dispatch record, result placeholder, and no-call counter hashes
- Disabled first-call post-invocation audit over invocation receipt, claim-boundary, and no-call counter hashes
- Disabled first-call completion summary over post-invocation audit, claim-boundary, and no-call counter hashes
- Disabled first-call closeout record over completion summary, claim-boundary, and no-call counter hashes
- Disabled first-call operator handback over closeout, operator-review, claim-boundary, and no-call counter hashes
- Disabled first-call operator decision packet over handback, operator-decision, claim-boundary, and no-call counter hashes
- Disabled first-call operator release attestation over decision packet, operator-attestation, claim-boundary, and no-call counter hashes
- Disabled first-call release authorization seal over release-attestation, seal-material, claim-boundary, and no-call counter hashes
- Disabled first-call execution authorization capsule over release seal, final authorization, claim-boundary, and no-call counter hashes
- Disabled first-call execution capsule export/read-model over execution capsule, export metadata, claim-boundary, and no-call counter hashes
- Disabled first-call execution capsule handoff packet over export, export read-model, claim-boundary, and no-call counter hashes
- Disabled first-call execution capsule operator review over handoff packet, operator-review, claim-boundary, and no-call counter hashes
- Disabled first-call execution capsule operator decision over operator review, operator-decision, claim-boundary, and no-call counter hashes
- Disabled first-call execution capsule release attestation over operator decision, release-attestation, claim-boundary, and no-call counter hashes
- Disabled first-call execution capsule release seal over release-attestation, seal-material, claim-boundary, and no-call counter hashes
- Disabled first-call execution capsule final authorization over release seal, final authorization, claim-boundary, and no-call counter hashes
- Disabled first-call execution capsule authorization export/read-model over final authz, export metadata, claim-boundary, and no-call counter hashes
- Test-only DIV/DAACS source identity fixtures for parity reference
- Fixture-based source identity smoke path from planning artifact to dry-run report
- Source-to-target trace and portfolio-safe claim projection for parity evidence
- Sanitizers for secrets, PII-like values, unsafe paths, raw payload fields, and public artifact exposure
- Local unit/smoke/eval documentation for regression tracking

Not included in the current scope:

- Real external provider calls
- Direct original runtime execution
- Generated application artifact production
- CLI agent execution
- Package install, server start, unrestricted file write
- Hosted deployment success claim
- Production security, trust, or durable persistence claim
- Hosted or production database persistence claim
- Source UI shell migration

## Project Structure

```text
apps/api/agentic_workbench_api/   FastAPI entrypoint sketch
packages/core/                    shared schemas, artifacts, events, safety gates
packages/                         planning adapters, build boundaries, runner gates
packages/harness/                 workflow orchestration
examples/                         fixture inputs/outputs
tests/                            unit, smoke, and integration test folders
docs/                             public architecture, migration, metrics, eval notes
```

## Verification

Run the local test suite:

```powershell
python -m pytest tests
```

Latest documented local baseline:

```text
Measurement date: 2026-06-01
Pytest: 489 / 489 passed
Live LLM calls in offline/dry-run/fake paths: 0
Live API calls in offline/dry-run/fake paths: 0
Provider calls/imports in the latest documented eval: 0
Network calls in the latest documented eval: 0
Direct original-runtime calls in the latest documented eval: 0
```

These numbers describe local regression and boundary checks. They are not production, hosting, model-quality, or security-certification claims.

## Claim Boundary

Allowed public summary:

- Local/dev AI agent workflow harness prototype
- Contract-based artifact pipeline from idea to planning package, build spec, approval, dry-run plan, and verification report
- Approval gate before execution handoff
- Side-effect-free dry-run plan generation
- Fake-only admission gates with external calls kept at 0 in current paths
- Optional SQLite-backed replay wiring for fake admission gates
- Canonical approval persistence service before durable replay claim
- Sanitized fake admission API demo paths for provider/live approval persistence
- SQLite-backed fake admission API mode selected only through server-side config
- Sanitized evidence read-model API for local repository projections
- Optional fixture evidence persistence for local repository projections
- Repository-backed run/artifact read APIs for local projection rows
- SQLite-backed canonical run/artifact read APIs for local projection rows
- Composed canonical run/evidence read models for local projection rows
- Local fixture/dry-run service-shaped demo over the public API boundary
- Minimal local Markdown/CLI run status surface over fixture/dry-run projections
- Live-open readiness policy gate that keeps provider/runtime calls at 0 and does not grant execution permission
- Static local UI shell over sanitized fixture/dry-run projections
- Disabled Solar Pro 3 provider adapter skeleton with provider calls kept at 0
- No-call Solar Pro 3 request/response contract fixtures with sanitized summary/hash projection
- Sanitized provider envelope read model for no-call contract hashes, counts, and status
- Local no-call provider envelope admission service before disabled Solar adapter invocation
- Local no-call provider envelope admission API/read-model hook with status/hash/count projection
- Local no-call operator approval envelope for provider precheck policy summaries
- Local dry-admission checklist and manual runbook for future provider test proposals
- Local manual provider test proposal gate with execution disabled by default
- Disabled local executor boundary for manual provider test proposals
- Blocked local review packet for manual provider test policy, preflight, and readiness hashes
- Hash-only local review packet export/read-model for manual provider test evidence
- Final no-call local handoff packet for manual provider test evidence
- Local no-call operator opt-in checklist bound to the handoff packet hash
- Local no-call sealed pre-execution packet over pre-call hashes and counts
- Local no-call arming record over sealed packet, operator, expiry, rollback, and abort hashes
- Local no-call release proposal over arming record, operator, release window, and rollback hashes
- Local no-call final release packet over release proposal, arming record, operator, release window, and rollback hashes
- Local disabled execution switch over final release packet and switch-enable hashes
- Local disabled executor preflight over execution switch and no-call counter hashes
- Local disabled executor dispatch record over executor preflight and planned dispatch hashes
- Local disabled invocation receipt over dispatch record and result-placeholder hashes
- Local disabled post-invocation audit over invocation receipt, claim-boundary, and no-call counter hashes
- Local disabled completion summary over post-invocation audit, claim-boundary, and no-call counter hashes
- Local disabled closeout record over completion summary, claim-boundary, and no-call counter hashes
- Local disabled operator handback over closeout, operator-review, claim-boundary, and no-call counter hashes
- Local disabled operator decision packet over handback, operator-decision, claim-boundary, and no-call counter hashes
- Local disabled operator release attestation over decision packet, operator-attestation, claim-boundary, and no-call counter hashes
- Local disabled release authorization seal over release-attestation, seal-material, claim-boundary, and no-call counter hashes
- Local disabled execution authorization capsule over release seal, final authorization, claim-boundary, and no-call counter hashes
- Local disabled execution capsule export/read-model over execution capsule, export metadata, claim-boundary, and no-call counter hashes
- Local disabled execution capsule handoff packet over export, export read-model, claim-boundary, and no-call counter hashes
- Local disabled execution capsule operator review over handoff packet, operator-review, claim-boundary, and no-call counter hashes
- Local disabled execution capsule operator decision over operator review, operator-decision, claim-boundary, and no-call counter hashes
- Local disabled execution capsule release attestation over operator decision, release-attestation, claim-boundary, and no-call counter hashes
- Local disabled execution capsule release seal over release-attestation, seal-material, claim-boundary, and no-call counter hashes
- Local disabled execution capsule final authorization over release seal, final authorization, claim-boundary, and no-call counter hashes
- Local disabled execution capsule authorization export/read-model over final authz, export metadata, claim-boundary, and no-call counter hashes
- Public output designed around sanitized summaries and correlation hashes

Do not interpret current results as:

- Real external-provider integration success
- Direct original runtime execution success
- Generated application production
- Hosted deployment success
- Production security or durable replay infrastructure
- Benchmark, success-rate, or productivity proof
- Solar Pro 3 model-quality or response-quality proof
- Provider envelope read model as provider outcome, hosted observability, or production provider readiness
- Provider envelope admission service as provider execution, model-quality proof, hosted provider service, or production provider readiness
- Provider envelope admission API hook as external provider behavior, hosted provider service, or production provider readiness
- Operator approval envelope as production operator identity, provider execution permission, or external provider outcome
- Dry-admission checklist as live permission, provider behavior evidence, hosted approval authority, or production provider readiness
- Manual provider test proposal gate as provider execution permission, provider behavior evidence, hosted approval authority, or production provider readiness
- Disabled manual provider test executor boundary as provider execution, provider behavior evidence, hosted execution, or production provider readiness
- One-shot permission contract as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Preflight audit bundle as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Readiness decision record as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Review packet as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Review packet export/read-model as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Handoff packet as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Operator opt-in checklist as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Sealed pre-execution packet as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Arming record as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Release proposal as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Final release packet as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Execution switch as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Post-invocation audit as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Completion summary as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Closeout record as provider execution permission, provider behavior evidence, hosted execution, or production provider readiness
- Operator handback as provider execution permission, provider behavior evidence, live operator approval, hosted execution, or production provider readiness
- Operator decision packet as provider execution permission, provider behavior evidence, live operator approval, hosted execution, or production provider readiness
- Operator release attestation as provider execution permission, provider behavior evidence, live operator approval, hosted execution, or production provider readiness
- Release authorization seal as provider execution permission, provider behavior evidence, live operator approval, hosted execution, or production provider readiness
- Execution authorization capsule as provider execution permission, provider behavior evidence, live operator approval, hosted execution, or production provider readiness
- Execution capsule export/read-model as provider execution permission, provider behavior evidence, live operator approval, hosted execution, or production provider readiness
- Execution capsule handoff packet as provider execution permission, provider behavior evidence, live operator approval, hosted execution, or production provider readiness
- Execution capsule operator review as provider execution permission, provider behavior evidence, live operator approval, hosted execution, or production provider readiness
- Execution capsule operator decision as provider execution permission, provider behavior evidence, live operator approval, hosted execution, or production provider readiness
- Execution capsule release attestation as provider execution permission, provider behavior evidence, live operator approval, hosted execution, or production provider readiness
- Execution capsule release seal as provider execution permission, provider behavior evidence, live operator approval, hosted execution, or production provider readiness

## Status

Current status: contract/gate/dry-run/fake-boundary MVP with sanitized public API fixture projection, source identity golden path smoke coverage, claim-safe trace projection, hash/count repository boundaries, SQLite adapter skeletons for runner/report/audit evidence, approval/replay evidence, canonical run/artifact rows, and provider envelope evidence, canonical approval persistence service wiring before replay claim, sanitized fake admission API demo paths, explicit SQLite-backed fake admission API wiring, sanitized evidence read-model API skeleton, optional fixture evidence persistence, canonical run/artifact read APIs, composed canonical run/evidence read API, local service-shaped demo script, minimal Markdown/CLI run status surface, static HTML UI shell, disabled Solar Pro 3 provider adapter skeleton, no-call Solar Pro 3 contract fixtures, provider envelope read-model projection, provider envelope admission service, provider envelope admission API/read-model hook, operator approval envelope for local no-call provider precheck evidence, dry-admission checklist/runbook projection, manual provider test proposal gate, disabled manual provider test executor boundary, blocked one-shot permission contract projection, blocked manual provider test preflight audit bundle, blocked readiness decision record, blocked manual provider test review packet, hash-only review packet export/read-model, final no-call handoff packet, first live-call operator opt-in checklist boundary, sealed pre-execution packet boundary, no-call live execution arming record, no-call execution authorization release proposal, no-call final release packet, disabled first-call execution switch, disabled first-call executor preflight, disabled first-call executor dispatch record, disabled first-call invocation receipt, disabled first-call post-invocation audit, disabled first-call completion summary, disabled first-call closeout record, disabled first-call operator handback, disabled first-call operator decision packet, disabled first-call operator release attestation, disabled first-call release authorization seal, disabled first-call execution authorization capsule, disabled first-call execution capsule export/read-model, disabled first-call execution capsule handoff packet, disabled first-call execution capsule operator review, disabled first-call execution capsule operator decision, disabled first-call execution capsule release attestation, disabled first-call execution capsule release seal, disabled first-call execution capsule final authorization, and disabled first-call execution capsule authorization export/read-model.

Current status also includes a fail-closed live-open policy gate. A passing policy decision can only mark a future surface as eligible for a separate implementation unit; it does not grant execution permission.

Next implementation track: disabled first-call final no-call execution capsule authorization handoff packet boundary. It must still keep external calls closed by default until a later explicitly approved call-opening task.

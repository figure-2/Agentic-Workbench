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
- Public API projection for sanitized fixture responses with fixture/synthetic markers
- Sanitized fake provider/live admission API demo paths that reuse canonical approval persistence
- Explicit SQLite-backed fake admission API wiring for cross-request replay evidence
- Sanitized evidence read-model API for persisted runner/report/audit and approval/replay rows
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
Measurement date: 2026-05-31
Pytest: 338 / 338 passed
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
- Public output designed around sanitized summaries and correlation hashes

Do not interpret current results as:

- Real external-provider integration success
- Direct original runtime execution success
- Generated application production
- Hosted deployment success
- Production security or durable replay infrastructure
- Benchmark, success-rate, or productivity proof

## Status

Current status: contract/gate/dry-run/fake-boundary MVP with sanitized public API fixture projection, source identity golden path smoke coverage, claim-safe trace projection, hash/count repository boundaries, SQLite adapter skeletons for runner/report/audit plus approval/replay evidence, canonical approval persistence service wiring before replay claim, sanitized fake admission API demo paths, explicit SQLite-backed fake admission API wiring, and sanitized evidence read-model API skeleton.

Next implementation track: local end-to-end demo that remains fake-only for live/provider execution, or repository-backed run/artifact read APIs.

# Quantitative Baseline

## Measurement Date

2026-06-05

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

Current snapshot after `AW-SOLAR-QUALITY-01` fixture-vs-Solar quality comparison.

| Metric | Value |
|---|---:|
| Project files, excluding cache and local artifacts | 461 |
| Counted code/doc files, excluding cache and local artifacts | 458 |
| Project lines, excluding cache and local artifacts | 121,319 |
| Python files | 127 |
| Markdown files | 327 |
| Test files | 52 |
| Unit test files | 40 |
| Smoke test files | 11 |
| Integration test files | 1 |
| Pytest collected cases | 724 |
| Pytest passed cases | 724 |
| Live LLM calls during eval | 1 |
| Live API calls during eval | 1 |

## AW-DAACS-RUNTIME-MVP-01 Restricted Workspace Generation Metrics

Measured after adding the local restricted fixture app skeleton generation
surface.

| Metric | Value |
|---|---:|
| Generated workspace scenarios | 1 |
| Generated files | 9 |
| File hash count | 9 |
| Required generated paths | 9/9 |
| Demo comparison variants | 7 |
| Write allowlist violations | 0 |
| Path traversal-like template fixtures blocked | 1 |
| Absolute-like template fixtures blocked | 1 |
| Unsafe run id fixtures blocked | 1 |
| Raw file content returns | 0 |
| Local root path returns | 0 |
| Solar Pro 3 provider calls | 0 |
| DAACS target runtime calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Package installs | 0 |
| Builds | 0 |
| Server starts | 0 |
| New unit tests | 9 |
| New smoke tests | 2 |

| Surface | Generated file cards | Stage coverage | Provider calls | Target runtime calls | Builds |
|---|---:|---:|---:|---:|---:|
| JSON demo summary | 9 | 7/7 | 0 | 0 | 0 |
| AW-APP-01 preview | 9 | 7/7 | 0 | 0 | 0 |

Verification:

```text
python -m pytest tests\unit\test_target_runtime_restricted_workspace_generation.py tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py -q
20 passed
python -m pytest tests -q
659 passed in 234.11s
```

## AW-SOLAR-02 Planner One-Shot Spike Metrics

Measured after adding the controlled Solar planner spike envelope and mocked
response projection.

| Metric | Value |
|---|---:|
| Default planner mode | fixture |
| Solar spike modes added | 2 |
| Official references checked | 3 |
| Planner spike envelope count in demo | 1 |
| Mocked response projection count in demo | 1 |
| Demo comparison variants | 3 |
| Fixture stage coverage | 7/7 |
| Raw prompt persistence findings | 0 |
| Raw provider body persistence findings | 0 |
| Env value reads in automated tests | 0 |
| SDK imports in automated tests | 0 |
| Network calls in automated tests | 0 |
| Provider calls in automated tests | 0 |
| New unit tests | 4 |
| New smoke tests | 2 |

| Variant | Status | Stage coverage | Provider calls | SDK imports | Env value reads | Network calls |
|---|---|---:|---:|---:|---:|---:|
| `fixture_planner` | passed | 7/7 | 0 | 0 | 0 | 0 |
| `solar_pro_3_disabled_preflight` | preflight_only | preflight-only | 0 | 0 | 0 | 0 |
| `solar_spike_preflight_mock` | mock_projected | fixture remains 7/7 | 0 | 0 | 0 | 0 |

Verification:

```text
python -m pytest tests\unit\test_planner_provider_preflight.py tests\smoke\test_solar_planner_preflight.py -q
15 passed
python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-solar-02-demo --include-solar-planner-spike
status passed, solar_spike_status mock_projected, provider/network calls 0
python -m pytest tests -q
648 passed in 230.04s
```

## AW-SOLAR-LIVE-01 One-Shot Planner Live Spike Metrics

Measured after adding the explicit Solar planner live spike path and running one
operator-opted representative scenario.

| Metric | Value |
|---|---:|
| Representative live planner scenarios | 1 |
| Explicit operator opt-in count | 1 |
| Provider call count in manual spike | 1 |
| Network call count in manual spike | 1 |
| Env value reads in manual spike | 1 |
| SDK imports in manual spike | 0 |
| Response projection count | 1 |
| Response status code | 200 |
| Response body bytes observed privately | 2300 |
| Response section count | 18 |
| Artifact hint count | 3 |
| Fixture stage coverage | 7/7 |
| DAACS target runtime calls | 0 |
| Server starts | 0 |
| Credential value exposure findings | 0 |
| Raw prompt/body exposure findings | 0 |
| Public local root path exposure findings | 0 |
| New unit tests | 4 |
| New smoke tests | 2 |

| Variant | Status | Stage coverage | Provider calls | Env reads | Network calls | Target runtime calls |
|---|---|---:|---:|---:|---:|---:|
| `fixture_planner` | passed | 7/7 | 0 | 0 | 0 | 0 |
| `solar_live_one_shot_blocked` | blocked | fixture remains 7/7 | 0 | 0 | 0 | 0 |
| `solar_live_one_shot_projected` | projected | fixture remains 7/7 | 1 | 1 | 1 | 0 |

Verification:

```text
python -m pytest tests\unit\test_solar_planner_live_spike.py -q --color=no
4 passed
python -m pytest tests\smoke\test_solar_planner_preflight.py -q --color=no
6 passed
python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-solar-live-01 --include-solar-planner-live-spike --allow-solar-planner-live-call
status passed, solar_live_spike_status projected, provider/network calls 1, target runtime calls 0
python -m pytest tests -q --color=no
719 passed in 256.87s
```

## AW-SOLAR-QUALITY-01 Fixture vs Solar Quality Comparison Metrics

Measured after adding the fixture-vs-Solar quality comparison projection.

| Metric | Value |
|---|---:|
| Comparison scenarios | 1 |
| Fixture stage coverage | 7/7 |
| Fixture artifact count | 6 |
| Default additional provider calls | 0 |
| Default additional network calls | 0 |
| Default additional env value reads | 0 |
| Default reviewer approval count | 0 |
| Default artifact binding permission count | 0 |
| Default artifact binding performed count | 0 |
| Default Solar summary section count | 0 |
| Default Solar artifact hint count | 0 |
| Default missing required stage count | 4 |
| Raw provider body stored/returned | 0 |
| Credential value exposure findings | 0 |
| DAACS target runtime calls | 0 |
| Server starts | 0 |
| New unit tests | 3 |
| New smoke tests | 2 |

| Variant | Status | Stage coverage | Additional provider calls | Reviewer approval | Artifact binding performed |
|---|---|---:|---:|---:|---:|
| `fixture_planner` | passed | 7/7 | 0 | 0 | 0 |
| `solar_quality_default_blocked` | review_blocked | 7/7 | 0 | 0 | 0 |
| `solar_quality_api_fake_projected` | review_blocked | 7/7 | 0 | 0 | 0 |

Verification:

```text
python -m pytest tests\unit\test_solar_planner_quality_comparison.py tests\unit\test_solar_planner_live_spike.py -q --color=no
7 passed
python -m pytest tests\smoke\test_solar_planner_preflight.py -q --color=no
8 passed
python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-solar-quality-01 --include-solar-planner-quality-comparison
status passed, quality_comparison_status review_blocked, additional live/provider/env/network calls 0, target runtime calls 0
python -m pytest tests -q --color=no
724 passed in 343.27s
```

## AW-SOLAR-DRAFT-01 Solar Draft Projection Metrics

Measured after adding reviewer-gated Solar draft `PlanningBlueprint` and
`PRDPackage` projection over `AW-SOLAR-QUALITY-01` evidence.

| Metric | Value |
|---|---:|
| Draft projection scenarios | 1 |
| Successful API draft labels | 2 |
| PlanningBlueprint draft projection count | 1 |
| PRDPackage draft projection count | 1 |
| Default local demo draft artifact count | 0 |
| Default local demo canonical artifact writes | 0 |
| Default additional provider calls | 0 |
| Default additional network calls | 0 |
| Default additional env value reads | 0 |
| Raw provider body stored/returned | 0 |
| Credential value exposure findings | 0 |
| DAACS target runtime calls | 0 |
| Server starts | 0 |
| New unit tests | 3 |
| New smoke tests | 2 |

| Variant | Status | Draft artifacts | Canonical writes | Additional provider calls | Target runtime calls |
|---|---|---:|---:|---:|---:|
| `solar_draft_default_demo` | blocked | 0 | 0 | 0 | 0 |
| `solar_draft_api_reviewer_bound` | draft_projected | 2 | 0 | 0 | 0 |

Verification:

```text
python -m pytest tests\unit\test_solar_planner_draft_projection.py -q --color=no
3 passed
python -m pytest tests\smoke\test_solar_planner_preflight.py -q --color=no
10 passed
python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-solar-draft-01 --include-solar-planner-draft-projection
status passed, draft_projection_status blocked, draft artifacts 0, canonical writes 0, additional live/provider/env/network calls 0, target runtime calls 0
python -m pytest tests -q --color=no
729 passed in 385.62s
```

## AW-APP-01 Artifact Preview Metrics

Measured after adding the local portfolio-facing artifact preview surface.

| Metric | Value |
|---|---:|
| Golden path scenario count | 1 |
| Workflow stage coverage | 7/7 |
| Workflow stage coverage percent | 100.0 |
| Demo artifact count | 6 |
| Preview fixture artifact cards | 3 |
| Document chain rows | 5 |
| DAACS runtime comparison variants | 6 |
| Fixture materialization record count | 3 |
| Fixture materialization content hash count | 3 |
| Fixture workspace writes | 3 |
| Fixture writes outside workspace | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| Solar Pro 3 provider calls | 0 |
| DAACS target runtime calls | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Local root path returns | 0 |
| Artifact content returns | 0 |
| New smoke tests | 2 |

| Surface | Artifact cards | Stage coverage | Provider calls | Target runtime calls |
|---|---:|---:|---:|---:|
| JSON demo summary | 0 | 7/7 | 0 | 0 |
| Static UI shell | 0 | 7/7 | 0 | 0 |
| AW-APP-01 preview | 3 | 7/7 | 0 | 0 |

Verification:

```text
python -m pytest tests\smoke\test_artifact_preview_surface.py -q
2 passed
python -m pytest tests -q
642 passed in 201.61s
```

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

## AW-LIVE-04 Provider Envelope Admission Service Metrics

Measured after adding a provider envelope admission service before disabled
Solar adapter invocation.

| Metric | Value |
|---|---:|
| Pytest collected cases | 392 |
| Pytest passed cases | 392 |
| Regression delta vs AW-LIVE-03 baseline | +8 |
| Provider envelope admission unit tests | 8 |
| Adapter invocation before successful envelope admission | 0 |
| Adapter invocation after successful envelope admission | 1 fixture path |
| Request/response hash mismatch block fixtures | 2 |
| Corrupted store block fixtures | 1 |
| Raw prompt/provider body/provider payload findings | 0 |
| Forbidden public key findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| provider envelope row saved before disabled adapter invocation | covered |
| provider envelope read model checked before disabled adapter invocation | covered |
| missing admission service blocked before adapter invocation | covered |
| request contract hash mismatch blocked | covered |
| response contract hash mismatch blocked | covered |
| corrupted envelope store blocked | covered |
| duplicate matching evidence admitted as duplicate | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds local no-call admission ordering in front of the
disabled Solar adapter path. It does not add SDK integration, provider response
parsing, external provider outcome, model-quality proof, hosted execution, or
production provider readiness.

## AW-LIVE-05 Provider Envelope API Hook Metrics

Measured after adding an optional API/demo hook over provider envelope admission
and read-model projections.

| Metric | Value |
|---|---:|
| Pytest collected cases | 397 |
| Pytest passed cases | 397 |
| Regression delta vs AW-LIVE-04 baseline | +5 |
| API provider envelope integration tests | 4 |
| Demo provider envelope smoke tests | 1 |
| Provider envelope API paths | 2 |
| Provider envelope store writes from fixture `/api/v1/runs` | 0 |
| Missing provider envelope store | blocked |
| Corrupted provider envelope store | blocked |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| optional API precheck uses `ProviderEnvelopeAdmissionService` | covered |
| optional demo precheck uses API public projection | covered |
| read model returns status/hash/count projection | covered |
| missing/corrupted store blocks before adapter admission | covered |
| fixture/dry-run run creation remains separate | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this exposes local no-call provider envelope admission evidence
through sanitized API/demo projections. It does not add SDK integration,
provider response parsing, external provider outcome, model-quality proof,
hosted execution, or production provider readiness.

## AW-LIVE-06 Operator Approval Envelope Metrics

Measured after making provider envelope precheck require an explicit operator
approval envelope bound to the public policy summary hash.

| Metric | Value |
|---|---:|
| Pytest collected cases | 398 |
| Pytest passed cases | 398 |
| Regression delta vs AW-LIVE-05 baseline | +1 |
| API operator approval integration tests | 1 |
| Provider envelope API integration tests | 5 |
| Demo provider envelope smoke tests | 1 |
| Operator policy summary fields | 7 groups |
| Missing operator approval | blocked |
| Provider envelope store writes before missing operator approval | 0 |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| provider precheck requires operator approval envelope | covered |
| operator approval references exact policy summary hash | covered |
| cost/timeout/quota/readiness summary is public-safe | covered |
| missing operator approval blocks before store write | covered |
| fixture/dry-run run creation remains separate | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds local operator approval evidence for provider
precheck policy summaries. It does not add production operator identity,
external provider execution, provider response parsing, model-quality proof,
hosted execution, or production provider readiness.

## AW-LIVE-07 Live Provider Dry-Admission Runbook Metrics

Measured after adding the manual dry-admission checklist projection and runbook.

| Metric | Value |
|---|---:|
| Pytest collected cases | 398 |
| Pytest passed cases | 398 |
| Regression delta vs AW-LIVE-06 baseline | +0 |
| API dry-admission integration assertions | covered |
| Demo dry-admission smoke assertions | covered |
| Dry-admission checklist projection fields | 13 groups |
| Checklist item count in current projection | 9 |
| Manual-required checklist items | 2 |
| API/demo `live_ready` | false |
| API/demo `allowed_to_execute` | false |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| live call preconditions documented | covered |
| cost/timeout/quota/rollback/operator approval conditions explicit | covered |
| API/demo status is dry-admission only | covered |
| missing operator approval remains blocked before store write | covered |
| fixture/dry-run run creation remains separate | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local checklist and manual runbook for future
provider test proposals. It does not add provider execution, SDK integration,
env value access, network access, provider response parsing, hosted execution,
or production provider readiness.

## AW-LIVE-08 Manual Provider Test Proposal Gate Metrics

Measured after adding the manual provider test proposal gate.

| Metric | Value |
|---|---:|
| Pytest collected cases | 399 |
| Pytest passed cases | 399 |
| Regression delta vs AW-LIVE-07 baseline | +1 |
| API manual proposal integration tests | 1 |
| Provider envelope API integration tests | 6 |
| Demo provider envelope smoke tests | 1 |
| Manual proposal required fields | 8 |
| Proposal status with matching approval | approved_disabled |
| Proposal `allowed_to_execute` | false |
| Proposal `disabled_by_default` | true |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| missing proposal approval blocked | covered |
| proposal run id / prompt contract hash binding | covered |
| cost / timeout / quota proposal fields | covered |
| rollback id and abort criteria hash/count | covered |
| proposal approval hash match | covered |
| proposal accepted but execution disabled | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local proposal gate for a later first provider test
discussion. It does not add an executor, SDK integration, env value access,
network access, provider response parsing, hosted execution, or production
provider readiness.

## AW-LIVE-09 Disabled Manual Provider Test Executor Metrics

Measured after adding the disabled manual provider test executor boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 400 |
| Pytest passed cases | 400 |
| Regression delta vs AW-LIVE-08 baseline | +1 |
| API disabled executor integration tests | 1 |
| Provider envelope API integration tests | 7 |
| Demo provider envelope smoke tests | 1 |
| Executor public projection fields | 3 |
| Executor status with approved proposal and no flag | blocked |
| Executor reason with approved proposal and no flag | executor_enable_required |
| Executor status with approved proposal and enable flag | blocked |
| Executor reason with approved proposal and enable flag | executor_disabled_by_default |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| approved proposal still leaves executor blocked | covered |
| missing executor flag blocked | covered |
| executor flag present still blocked | covered |
| executor projection narrowed to status/reason/planned_call_hash | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a disabled local executor boundary. It does not add
an external call path, SDK integration, env value access, network access,
provider response parsing, hosted execution, or production provider readiness.

## AW-LIVE-10 One-Shot Permission Contract Metrics

Measured after adding the blocked one-shot permission contract projection.

| Metric | Value |
|---|---:|
| Pytest collected cases | 401 |
| Pytest passed cases | 401 |
| Regression delta vs AW-LIVE-09 baseline | +1 |
| API one-shot permission integration tests | 1 |
| Provider envelope API integration tests | 8 |
| Demo provider envelope smoke tests | 1 |
| Permission public projection fields | 5 |
| Permission required field count | 11 |
| Permission status with valid candidate and blocked executor | blocked |
| Permission reason with valid candidate and blocked executor | executor_blocked |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| executor blocked state keeps permission blocked | covered |
| one-shot candidate binds run/proposal/planned-call hashes | covered |
| cost/timeout/quota/rollback/abort hash/count included | covered |
| permission projection narrowed to status/reason/hash/expiry/count | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a blocked local permission contract projection for a
later manual provider test candidate. It does not add an external call path,
SDK integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-11 Manual Provider Test Preflight Audit Bundle Metrics

Measured after adding the blocked manual provider test preflight audit bundle.

| Metric | Value |
|---|---:|
| Pytest collected cases | 402 |
| Pytest passed cases | 402 |
| Regression delta vs AW-LIVE-10 baseline | +1 |
| API preflight audit integration tests | 2 |
| Provider envelope API integration tests | 8 |
| Demo provider envelope smoke tests | 1 |
| Preflight component count | 5 |
| Preflight public projection fields | 8 |
| No-call counter names checked | 13 |
| Preflight status with consistent local candidate | blocked |
| Preflight reason with consistent local candidate | preflight_execution_closed |
| Preflight reason with mismatched permission | permission_component_missing_or_mismatch |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| proposal/executor/permission/checklist/counters in one bundle | covered |
| bundle remains blocked | covered |
| missing proposal reason | covered |
| mismatched permission reason | covered |
| projection narrowed to status/reason/hash/count fields | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a blocked local preflight audit bundle for a later
manual provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-12 Readiness Decision Record Metrics

Measured after adding the blocked readiness decision record.

| Metric | Value |
|---|---:|
| Pytest collected cases | 405 |
| Pytest passed cases | 405 |
| Regression delta vs AW-LIVE-11 baseline | +3 |
| API readiness decision integration tests | 3 |
| Provider envelope API integration tests | 11 |
| Demo provider envelope smoke tests | 1 |
| Readiness decision public projection fields | 9 |
| Supported decision values | 3 |
| Execution permission count with approve decision | 0 |
| Decision reason with approve | readiness_execution_closed |
| Decision reason with reject | readiness_rejected |
| Decision reason with defer | readiness_deferred |
| Decision reason with preflight hash mismatch | preflight_hash_mismatch |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| readiness decision binds current preflight hash | covered |
| approve/reject/defer represented by count fields | covered |
| execution permission remains 0 | covered |
| preflight hash mismatch blocked | covered |
| projection narrowed to status/reason/hash/count fields | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a blocked local readiness decision record for a later
manual provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-13 Review Packet Metrics

Measured after adding the blocked manual provider test review packet.

| Metric | Value |
|---|---:|
| Pytest collected cases | 407 |
| Pytest passed cases | 407 |
| Regression delta vs AW-LIVE-12 baseline | +2 |
| API review packet integration tests | 2 |
| Provider envelope API integration tests | 13 |
| Demo provider envelope smoke tests | 1 |
| Review packet public projection fields | 8 |
| Review packet component count | 3 |
| Execution permission count with approve decision | 0 |
| Packet reason with complete local candidate | review_packet_execution_closed |
| Packet reason with readiness mismatch | readiness_decision_missing_or_mismatched |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| policy summary hash included in packet hash input | covered |
| preflight audit hash included in packet hash input | covered |
| readiness decision hash included in packet hash input | covered |
| approve decision still leaves execution permission at 0 | covered |
| missing or mismatched component blocked | covered |
| projection narrowed to status/reason/hash/count fields | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a blocked local review packet for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-14 Review Packet Export Read Model Metrics

Measured after adding the hash-only review packet export/read-model.

| Metric | Value |
|---|---:|
| Pytest collected cases | 411 |
| Pytest passed cases | 411 |
| Regression delta vs AW-LIVE-13 baseline | +4 |
| Provider envelope store review packet export tests | 2 |
| API review packet export/read-model integration tests | 2 |
| Provider envelope API integration tests | 16 |
| Demo provider envelope smoke tests | 1 |
| Review packet export public summary fields | 10 |
| Stored review packet export rows in golden path | 1 |
| Execution permission count with approve decision | 0 |
| Export reason with complete local candidate | review_packet_execution_closed |
| Export reason with expected hash mismatch | review_packet_hash_mismatch |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| review packet export row stores hash/status/reason/count fields | covered |
| API read-model retrieves stored packet export | covered |
| demo summary reads stored packet export | covered |
| expected review packet hash mismatch blocks before adapter admission | covered |
| approve decision still leaves execution permission at 0 | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local hash-only export/read-model for a later
manual provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-15 Final No-Call Handoff Packet Metrics

Measured after adding the blocked manual provider test handoff packet.

| Metric | Value |
|---|---:|
| Pytest collected cases | 414 |
| Pytest passed cases | 414 |
| Regression delta vs AW-LIVE-14 baseline | +3 |
| API handoff packet integration tests | 3 |
| Provider envelope API integration tests | 19 |
| Demo provider envelope smoke tests | 1 |
| Handoff packet public summary fields | 9 |
| Handoff packet component count | 5 |
| Handoff packet component hash count | 5 |
| Handoff packet export count in golden path | 1 |
| Execution permission count with approve decision | 0 |
| Handoff reason with complete local candidate | handoff_packet_execution_closed |
| Export mismatch reason | review_packet_export_hash_mismatch |
| Handoff mismatch reason | handoff_packet_hash_mismatch |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| policy/preflight/readiness/review/export evidence summarized in one packet | covered |
| public handoff packet exposes status/reason/hash/count fields only | covered |
| expected review packet export hash mismatch blocks before adapter admission | covered |
| expected handoff packet hash mismatch blocks before adapter admission | covered |
| approve decision still leaves execution permission at 0 | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local no-call audit handoff packet for a later
manual provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-16 Operator Opt-In Checklist Boundary Metrics

Measured after adding the blocked operator opt-in checklist boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 417 |
| Pytest passed cases | 417 |
| Regression delta vs AW-LIVE-15 baseline | +3 |
| API operator opt-in integration tests | 3 |
| Provider envelope API integration tests | 22 |
| Demo provider envelope smoke tests | 1 |
| Operator opt-in public summary fields | 8 |
| Operator opt-in checklist item count | 5 |
| Operator opt-in passed count with missing opt-in | 1 |
| Operator opt-in mismatch count with missing opt-in | 4 |
| Operator opt-in passed count with complete opt-in | 5 |
| Execution permission count with complete opt-in | 0 |
| Missing opt-in reason | operator_opt_in_required |
| Complete opt-in reason | operator_opt_in_execution_closed |
| Handoff mismatch reason | handoff_packet_hash_mismatch |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| handoff packet hash is required before opt-in | covered |
| missing operator opt-in is blocked | covered |
| complete operator opt-in remains execution-closed | covered |
| opt-in handoff hash mismatch is blocked | covered |
| public opt-in projection exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local no-call operator opt-in checklist for a later
manual provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-17 Sealed Pre-Execution Packet Boundary Metrics

Measured after adding the blocked sealed pre-execution packet boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 420 |
| Pytest passed cases | 420 |
| Regression delta vs AW-LIVE-16 baseline | +3 |
| API sealed packet integration tests | 3 |
| Provider envelope API integration tests | 25 |
| Demo provider envelope smoke tests | 1 |
| Sealed packet public summary fields | 12 |
| Sealed packet component count | 6 |
| Sealed packet component hash count | 4 |
| Sealed packet passed count with missing expected opt-in hash | 5 |
| Sealed packet mismatch count with missing expected opt-in hash | 1 |
| Sealed packet passed count with complete packet | 6 |
| Execution permission count with complete packet | 0 |
| Missing expected opt-in hash reason | expected_operator_opt_in_hash_required |
| Complete packet reason | sealed_pre_execution_packet_execution_closed |
| Operator opt-in hash mismatch reason | operator_opt_in_hash_mismatch |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| operator opt-in hash is required before sealed packet hash | covered |
| expected operator opt-in hash must match | covered |
| cost/timeout/quota hash is included | covered |
| rollback/abort criteria hash is included | covered |
| public sealed packet exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local no-call sealed pre-execution packet for a
later manual provider test candidate. It does not add an external call path,
SDK integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-18 Live Execution Arming Record Metrics

Measured after adding the blocked no-call live execution arming record.

| Metric | Value |
|---|---:|
| Pytest collected cases | 423 |
| Pytest passed cases | 423 |
| Regression delta vs AW-LIVE-17 baseline | +3 |
| API arming record integration tests | 3 |
| Provider envelope API integration tests | 28 |
| Demo provider envelope smoke tests | 1 |
| Arming record public summary fields | 13 |
| Arming record component count | 8 |
| Arming record component hash count | 5 |
| Arming record passed count with missing expected sealed hash | 1 |
| Arming record mismatch count with missing expected sealed hash | 7 |
| Arming record passed count with complete record | 8 |
| Execution permission count with complete record | 0 |
| Missing expected sealed hash reason | expected_sealed_packet_hash_required |
| Complete record reason | arming_record_execution_closed |
| Arming sealed hash mismatch reason | arming_record_sealed_hash_mismatch |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| sealed packet hash exists before arming | covered |
| expected sealed packet hash must match | covered |
| operator and expiry are represented as hashes | covered |
| rollback/abort and abort policy hashes are included | covered |
| public arming record exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local no-call arming record for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-19 Execution Authorization Release Proposal Metrics

Measured after adding the blocked no-call execution authorization release
proposal.

| Metric | Value |
|---|---:|
| Pytest collected cases | 426 |
| Pytest passed cases | 426 |
| Regression delta vs AW-LIVE-18 baseline | +3 |
| API release proposal integration tests | 3 |
| Provider envelope API integration tests | 31 |
| Demo provider envelope smoke tests | 1 |
| Release proposal public summary fields | 12 |
| Release proposal component count | 7 |
| Release proposal component hash count | 4 |
| Release proposal passed count with missing expected arming hash | 1 |
| Release proposal mismatch count with missing expected arming hash | 6 |
| Release proposal passed count with complete proposal | 7 |
| Execution permission count with complete proposal | 0 |
| Missing expected arming hash reason | expected_arming_record_hash_required |
| Complete proposal reason | release_proposal_execution_closed |
| Release proposal arming hash mismatch reason | release_proposal_arming_hash_mismatch |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| arming record hash exists before release proposal | covered |
| expected arming record hash must match | covered |
| operator and release window are represented as hashes | covered |
| rollback/abort hash is included | covered |
| public release proposal exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local no-call release proposal for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-20 Final Release Packet Metrics

Measured after adding the blocked no-call final release packet.

| Metric | Value |
|---|---:|
| Pytest collected cases | 429 |
| Pytest passed cases | 429 |
| Regression delta vs AW-LIVE-19 baseline | +3 |
| API final release packet integration tests | 3 |
| Provider envelope API integration tests | 34 |
| Demo provider envelope smoke tests | 1 |
| Final release packet public summary fields | 13 |
| Final release packet component count | 8 |
| Final release packet component hash count | 5 |
| Final release packet passed count with missing expected release hash | 5 |
| Final release packet mismatch count with missing expected release hash | 3 |
| Final release packet passed count with complete packet | 8 |
| Execution permission count with complete packet | 0 |
| Missing expected release hash reason | expected_release_proposal_hash_required |
| Complete packet reason | final_release_packet_execution_closed |
| Final packet proposal hash mismatch reason | final_release_packet_proposal_hash_mismatch |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| release proposal hash exists before final packet | covered |
| expected release proposal hash must match | covered |
| arming record, operator, and release window hashes are included | covered |
| rollback/abort hash is included | covered |
| public final release packet exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local no-call final release packet for a later
manual provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-21 Disabled Execution Switch Metrics

Measured after adding the blocked disabled first-call execution switch.

| Metric | Value |
|---|---:|
| Pytest collected cases | 432 |
| Pytest passed cases | 432 |
| Regression delta vs AW-LIVE-20 baseline | +3 |
| API execution switch integration tests | 3 |
| Provider envelope API integration tests | 37 |
| Demo provider envelope smoke tests | 1 |
| Execution switch public summary fields | 11 |
| Execution switch component count | 5 |
| Execution switch component hash count | 2 |
| Execution switch passed count with missing expected final hash | 1 |
| Execution switch mismatch count with missing expected final hash | 4 |
| Execution switch passed count without enable flag | 4 |
| Execution switch mismatch count without enable flag | 1 |
| Execution switch passed count with complete switch | 5 |
| Execution permission count with complete switch | 0 |
| Missing expected final hash reason | expected_final_release_packet_hash_required |
| Missing enable flag reason | execution_switch_enable_required |
| Complete switch reason | execution_switch_disabled_by_default |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| final release packet hash exists before switch | covered |
| expected final release packet hash must match | covered |
| separate enable flag is required | covered |
| enable flag still leaves execution permission at 0 | covered |
| public execution switch exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution switch for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-22 Disabled Executor Preflight Metrics

Measured after adding the blocked disabled first-call executor preflight.

| Metric | Value |
|---|---:|
| Pytest collected cases | 435 |
| Pytest passed cases | 435 |
| Regression delta vs AW-LIVE-21 baseline | +3 |
| API executor preflight integration tests | 3 |
| Provider envelope API integration tests | 40 |
| Demo provider envelope smoke tests | 1 |
| Executor preflight public summary fields | 12 |
| Executor preflight component count | 5 |
| Executor preflight component hash count | 3 |
| Executor preflight no-call counter count | 13 |
| Executor preflight passed count with missing expected switch hash | 2 |
| Executor preflight mismatch count with missing expected switch hash | 3 |
| Executor preflight passed count without preflight payload | 3 |
| Executor preflight mismatch count without preflight payload | 2 |
| Executor preflight passed count with complete preflight | 5 |
| Execution permission count with complete preflight | 0 |
| Missing expected switch hash reason | expected_execution_switch_hash_required |
| Missing preflight payload reason | executor_preflight_required |
| Complete preflight reason | executor_preflight_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution switch hash exists before executor preflight | covered |
| expected execution switch hash must match | covered |
| executor preflight payload is required | covered |
| no-call counters are represented as hash/count evidence | covered |
| public executor preflight exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled executor preflight for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-23 Disabled Executor Dispatch Record Metrics

Measured after adding the blocked disabled first-call executor dispatch record.

| Metric | Value |
|---|---:|
| Pytest collected cases | 438 |
| Pytest passed cases | 438 |
| Regression delta vs AW-LIVE-22 baseline | +3 |
| API executor dispatch record integration tests | 3 |
| Provider envelope API integration tests | 43 |
| Demo provider envelope smoke tests | 1 |
| Executor dispatch record public summary fields | 13 |
| Executor dispatch record component count | 6 |
| Executor dispatch record component hash count | 3 |
| Executor dispatch record no-call counter count | 13 |
| Dispatch record passed count with missing expected preflight hash | 2 |
| Dispatch record mismatch count with missing expected preflight hash | 4 |
| Dispatch record passed count without dispatch payload | 3 |
| Dispatch record mismatch count without dispatch payload | 3 |
| Dispatch record passed count with complete dispatch record | 6 |
| Execution permission count with complete dispatch record | 0 |
| Missing expected preflight hash reason | expected_executor_preflight_hash_required |
| Missing dispatch payload reason | executor_dispatch_record_required |
| Complete dispatch record reason | executor_dispatch_record_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| executor preflight hash exists before dispatch record | covered |
| expected executor preflight hash must match | covered |
| dispatch record payload is required | covered |
| planned dispatch is represented as hash/count evidence | covered |
| public dispatch record exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled executor dispatch record for a later
manual provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-24 Disabled Invocation Receipt Metrics

Measured after adding the blocked disabled first-call invocation receipt.

| Metric | Value |
|---|---:|
| Pytest collected cases | 441 |
| Pytest passed cases | 441 |
| Regression delta vs AW-LIVE-23 baseline | +3 |
| API invocation receipt integration tests | 3 |
| Provider envelope API integration tests | 46 |
| Demo provider envelope smoke tests | 1 |
| Invocation receipt public summary fields | 13 |
| Invocation receipt component count | 6 |
| Invocation receipt component hash count | 3 |
| Invocation receipt no-call counter count | 13 |
| Receipt passed count with missing expected dispatch hash | 2 |
| Receipt mismatch count with missing expected dispatch hash | 4 |
| Receipt passed count without receipt payload | 3 |
| Receipt mismatch count without receipt payload | 3 |
| Receipt passed count with complete receipt | 6 |
| Execution permission count with complete receipt | 0 |
| Missing expected dispatch hash reason | expected_dispatch_record_hash_required |
| Missing receipt payload reason | invocation_receipt_required |
| Complete receipt reason | invocation_receipt_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| dispatch record hash exists before invocation receipt | covered |
| expected dispatch record hash must match | covered |
| invocation receipt payload is required | covered |
| result placeholder is represented as hash/count evidence | covered |
| public receipt exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled invocation receipt for a later
manual provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-25 Disabled Post-Invocation Audit Metrics

Measured after adding the blocked disabled first-call post-invocation audit.

| Metric | Value |
|---|---:|
| Pytest collected cases | 444 |
| Pytest passed cases | 444 |
| Regression delta vs AW-LIVE-24 baseline | +3 |
| API post-invocation audit integration tests | 3 |
| Provider envelope API integration tests | 49 |
| Demo provider envelope smoke tests | 1 |
| Post-invocation audit public summary fields | 14 |
| Post-invocation audit component count | 7 |
| Post-invocation audit component hash count | 3 |
| Post-invocation audit no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Audit passed count with missing expected receipt hash | 3 |
| Audit mismatch count with missing expected receipt hash | 4 |
| Audit passed count without audit payload | 4 |
| Audit mismatch count without audit payload | 3 |
| Audit passed count with complete audit | 7 |
| Execution permission count with complete audit | 0 |
| Missing expected receipt hash reason | expected_invocation_receipt_hash_required |
| Missing audit payload reason | post_invocation_audit_required |
| Complete audit reason | post_invocation_audit_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| invocation receipt hash exists before post-invocation audit | covered |
| expected invocation receipt hash must match | covered |
| post-invocation audit payload is required | covered |
| claim boundary is represented as hash/count evidence | covered |
| public audit exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled post-invocation audit for a later
manual provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-26 Disabled Completion Summary Metrics

Measured after adding the blocked disabled first-call completion summary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 447 |
| Pytest passed cases | 447 |
| Regression delta vs AW-LIVE-25 baseline | +3 |
| API completion summary integration tests | 3 |
| Provider envelope API integration tests | 52 |
| Demo provider envelope smoke tests | 1 |
| Completion summary public summary fields | 14 |
| Completion summary component count | 7 |
| Completion summary component hash count | 3 |
| Completion summary no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Summary passed count with missing expected audit hash | 3 |
| Summary mismatch count with missing expected audit hash | 4 |
| Summary passed count without summary payload | 4 |
| Summary mismatch count without summary payload | 3 |
| Summary passed count with complete summary | 7 |
| Execution permission count with complete summary | 0 |
| Missing expected audit hash reason | expected_post_invocation_audit_hash_required |
| Missing summary payload reason | completion_summary_required |
| Complete summary reason | completion_summary_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| post-invocation audit hash exists before completion summary | covered |
| expected post-invocation audit hash must match | covered |
| completion summary payload is required | covered |
| claim boundary is represented as hash/count evidence | covered |
| public summary exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled completion summary for a later
manual provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-27 Disabled Closeout Record Metrics

Measured after adding the blocked disabled first-call closeout record.

| Metric | Value |
|---|---:|
| Pytest collected cases | 450 |
| Pytest passed cases | 450 |
| Regression delta vs AW-LIVE-26 baseline | +3 |
| API closeout record integration tests | 3 |
| Provider envelope API integration tests | 55 |
| Demo provider envelope smoke tests | 1 |
| Closeout record public summary fields | 14 |
| Closeout record component count | 7 |
| Closeout record component hash count | 3 |
| Closeout record no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Closeout passed count with missing expected summary hash | 3 |
| Closeout mismatch count with missing expected summary hash | 4 |
| Closeout passed count without closeout payload | 4 |
| Closeout mismatch count without closeout payload | 3 |
| Closeout passed count with complete record | 7 |
| Execution permission count with complete closeout | 0 |
| Missing expected summary hash reason | expected_completion_summary_hash_required |
| Missing closeout payload reason | closeout_record_required |
| Complete closeout reason | closeout_record_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| completion summary hash exists before closeout record | covered |
| expected completion summary hash must match | covered |
| closeout record payload is required | covered |
| claim boundary is represented as hash/count evidence | covered |
| public closeout exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled closeout record for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, or production provider readiness.

## AW-LIVE-28 Disabled Operator Handback Metrics

Measured after adding the blocked disabled first-call operator handback.

| Metric | Value |
|---|---:|
| Pytest collected cases | 453 |
| Pytest passed cases | 453 |
| Regression delta vs AW-LIVE-27 baseline | +3 |
| API operator handback integration tests | 3 |
| Provider envelope API integration tests | 58 |
| Demo provider envelope smoke tests | 1 |
| Operator handback public summary fields | 16 |
| Operator handback component count | 8 |
| Operator handback component hash count | 4 |
| Operator handback no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Handback passed count with missing expected closeout hash | 3 |
| Handback mismatch count with missing expected closeout hash | 5 |
| Handback passed count without handback payload | 4 |
| Handback mismatch count without handback payload | 4 |
| Handback passed count with complete handback | 8 |
| Execution permission count with complete handback | 0 |
| Missing expected closeout hash reason | expected_closeout_record_hash_required |
| Missing handback payload reason | operator_handback_required |
| Complete handback reason | operator_handback_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| closeout record hash exists before operator handback | covered |
| expected closeout record hash must match | covered |
| operator handback payload is required | covered |
| operator review is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public handback exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled operator handback for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-29 Disabled Operator Decision Packet Metrics

Measured after adding the blocked disabled first-call operator decision packet.

| Metric | Value |
|---|---:|
| Pytest collected cases | 456 |
| Pytest passed cases | 456 |
| Regression delta vs AW-LIVE-28 baseline | +3 |
| API operator decision packet integration tests | 3 |
| Provider envelope API integration tests | 61 |
| Demo provider envelope smoke tests | 1 |
| Operator decision packet public summary fields | 16 |
| Operator decision packet component count | 8 |
| Operator decision packet component hash count | 4 |
| Operator decision packet no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Decision packet passed count with missing expected handback hash | 3 |
| Decision packet mismatch count with missing expected handback hash | 5 |
| Decision packet passed count without packet payload | 4 |
| Decision packet mismatch count without packet payload | 4 |
| Decision packet passed count with complete packet | 8 |
| Execution permission count with complete packet | 0 |
| Missing expected handback hash reason | expected_operator_handback_hash_required |
| Missing packet payload reason | operator_decision_packet_required |
| Complete packet reason | operator_decision_packet_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| operator handback hash exists before decision packet | covered |
| expected operator handback hash must match | covered |
| operator decision packet payload is required | covered |
| operator decision is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public packet exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled operator decision packet for a later
manual provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-30 Disabled Operator Release Attestation Metrics

Measured after adding the blocked disabled first-call operator release
attestation.

| Metric | Value |
|---|---:|
| Pytest collected cases | 459 |
| Pytest passed cases | 459 |
| Regression delta vs AW-LIVE-29 baseline | +3 |
| API operator release attestation integration tests | 3 |
| Provider envelope API integration tests | 64 |
| Demo provider envelope smoke tests | 1 |
| Operator release attestation public summary fields | 16 |
| Operator release attestation component count | 8 |
| Operator release attestation component hash count | 4 |
| Operator release attestation no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Attestation passed count with missing expected decision packet hash | 3 |
| Attestation mismatch count with missing expected decision packet hash | 5 |
| Attestation passed count without attestation payload | 4 |
| Attestation mismatch count without attestation payload | 4 |
| Attestation passed count with complete attestation | 8 |
| Execution permission count with complete attestation | 0 |
| Missing expected decision packet hash reason | expected_operator_decision_packet_hash_required |
| Missing attestation payload reason | operator_release_attestation_required |
| Complete attestation reason | operator_release_attestation_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| operator decision packet hash exists before release attestation | covered |
| expected operator decision packet hash must match | covered |
| operator release attestation payload is required | covered |
| operator attestation is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public attestation exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled operator release attestation for a
later manual provider test candidate. It does not add an external call path,
SDK integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-31 Disabled Release Authorization Seal Metrics

Measured after adding the blocked disabled first-call release authorization
seal.

| Metric | Value |
|---|---:|
| Pytest collected cases | 462 |
| Pytest passed cases | 462 |
| Regression delta vs AW-LIVE-30 baseline | +3 |
| API release authorization seal integration tests | 3 |
| Provider envelope API integration tests | 67 |
| Demo provider envelope smoke tests | 1 |
| Release seal public summary fields | 16 |
| Release seal component count | 8 |
| Release seal component hash count | 4 |
| Release seal no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Seal passed count with missing expected release attestation hash | 3 |
| Seal mismatch count with missing expected release attestation hash | 5 |
| Seal passed count without seal payload | 4 |
| Seal mismatch count without seal payload | 4 |
| Seal passed count with complete seal | 8 |
| Execution permission count with complete seal | 0 |
| Missing expected release attestation hash reason | expected_operator_release_attestation_hash_required |
| Missing seal payload reason | release_authorization_seal_required |
| Complete seal reason | release_authorization_seal_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| operator release attestation hash exists before seal | covered |
| expected operator release attestation hash must match | covered |
| release seal payload is required | covered |
| seal material is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public seal exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled release authorization seal for a
later manual provider test candidate. It does not add an external call path,
SDK integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-32 Disabled Execution Authorization Capsule Metrics

Measured after adding the blocked disabled first-call execution authorization
capsule.

| Metric | Value |
|---|---:|
| Pytest collected cases | 465 |
| Pytest passed cases | 465 |
| Regression delta vs AW-LIVE-31 baseline | +3 |
| API execution authorization capsule integration tests | 3 |
| Provider envelope API integration tests | 70 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule public summary fields | 16 |
| Execution capsule component count | 8 |
| Execution capsule component hash count | 4 |
| Execution capsule no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Capsule passed count with missing expected release seal hash | 3 |
| Capsule mismatch count with missing expected release seal hash | 5 |
| Capsule passed count without capsule payload | 4 |
| Capsule mismatch count without capsule payload | 4 |
| Capsule passed count with complete capsule | 8 |
| Execution permission count with complete capsule | 0 |
| Missing expected release seal hash reason | expected_release_seal_hash_required |
| Missing capsule payload reason | execution_authorization_capsule_required |
| Complete capsule reason | execution_authorization_capsule_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| release seal hash exists before capsule | covered |
| expected release seal hash must match | covered |
| execution authorization capsule payload is required | covered |
| final authorization is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public capsule exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution authorization capsule for
a later manual provider test candidate. It does not add an external call path,
SDK integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-33 Disabled Execution Capsule Export Read Model Metrics

Measured after adding the blocked disabled first-call execution capsule
export/read-model boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 468 |
| Pytest passed cases | 468 |
| Regression delta vs AW-LIVE-32 baseline | +3 |
| API execution capsule export integration tests | 3 |
| Provider envelope API integration tests | 73 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule export public summary fields | 16 |
| Execution capsule export read-model public fields | 4 |
| Execution capsule export component count | 8 |
| Execution capsule export component hash count | 4 |
| Execution capsule export no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Export passed count with missing expected execution capsule hash | 3 |
| Export mismatch count with missing expected execution capsule hash | 5 |
| Export passed count without export payload | 4 |
| Export mismatch count without export payload | 4 |
| Export passed count with complete export | 8 |
| Execution permission count with complete export | 0 |
| Missing expected execution capsule hash reason | expected_execution_capsule_hash_required |
| Missing export payload reason | execution_capsule_export_required |
| Complete export reason | execution_capsule_export_execution_closed |
| Read-model available reason | execution_capsule_export_read_model_available |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule hash exists before export | covered |
| expected execution capsule hash must match | covered |
| execution capsule export payload is required | covered |
| export metadata is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public export exposes status/reason/hash/count fields only | covered |
| public read model exposes latest hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule export/read-model
for a later manual provider test candidate. It does not add an external call
path, SDK integration, env value access, network access, provider response
parsing, hosted execution, live operator approval, or production provider
readiness.

## AW-LIVE-34 Disabled Execution Capsule Handoff Packet Metrics

Measured after adding the blocked disabled first-call execution capsule handoff
packet boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 471 |
| Pytest passed cases | 471 |
| Regression delta vs AW-LIVE-33 baseline | +3 |
| API execution capsule handoff packet integration tests | 3 |
| Provider envelope API integration tests | 76 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule handoff packet public summary fields | 17 |
| Execution capsule handoff packet component count | 8 |
| Execution capsule handoff packet component hash count | 4 |
| Execution capsule handoff packet no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Packet passed count with missing expected export hash | 7 |
| Packet mismatch count with missing expected export hash | 1 |
| Packet passed count without packet payload | 5 |
| Packet mismatch count without packet payload | 3 |
| Packet passed count with complete packet | 8 |
| Execution permission count with complete packet | 0 |
| Missing expected export hash reason | expected_execution_capsule_export_hash_required |
| Missing packet payload reason | execution_capsule_handoff_packet_required |
| Complete packet reason | execution_capsule_handoff_packet_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule export hash exists before handoff | covered |
| expected execution capsule export hash must match | covered |
| execution capsule handoff packet payload is required | covered |
| export read model is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public packet exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule handoff packet
for a later manual provider test candidate. It does not add an external call
path, SDK integration, env value access, network access, provider response
parsing, hosted execution, live operator approval, or production provider
readiness.

## AW-LIVE-35 Disabled Execution Capsule Operator Review Metrics

Measured after adding the blocked disabled first-call execution capsule
operator review boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 474 |
| Pytest passed cases | 474 |
| Regression delta vs AW-LIVE-34 baseline | +3 |
| API execution capsule operator review integration tests | 3 |
| Provider envelope API integration tests | 79 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule operator review public summary fields | 16 |
| Execution capsule operator review component count | 8 |
| Execution capsule operator review component hash count | 4 |
| Execution capsule operator review no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Review passed count with missing expected handoff packet hash | 7 |
| Review mismatch count with missing expected handoff packet hash | 1 |
| Review passed count without review payload | 4 |
| Review mismatch count without review payload | 4 |
| Review passed count with complete review | 8 |
| Execution permission count with complete review | 0 |
| Missing expected handoff packet hash reason | expected_execution_capsule_handoff_packet_hash_required |
| Missing review payload reason | execution_capsule_operator_review_required |
| Complete review reason | execution_capsule_operator_review_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule handoff packet hash exists before review | covered |
| expected execution capsule handoff packet hash must match | covered |
| execution capsule operator review payload is required | covered |
| operator review is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public review exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule operator review
for a later manual provider test candidate. It does not add an external call
path, SDK integration, env value access, network access, provider response
parsing, hosted execution, live operator approval, or production provider
readiness.

## AW-LIVE-36 Disabled Execution Capsule Operator Decision Metrics

Measured after adding the blocked disabled first-call execution capsule
operator decision boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 477 |
| Pytest passed cases | 477 |
| Regression delta vs AW-LIVE-35 baseline | +3 |
| API execution capsule operator decision integration tests | 3 |
| Provider envelope API integration tests | 82 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule operator decision public summary fields | 16 |
| Execution capsule operator decision component count | 8 |
| Execution capsule operator decision component hash count | 4 |
| Execution capsule operator decision no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Decision passed count with missing expected review hash | 7 |
| Decision mismatch count with missing expected review hash | 1 |
| Decision passed count without decision payload | 4 |
| Decision mismatch count without decision payload | 4 |
| Decision passed count with complete decision | 8 |
| Execution permission count with complete decision | 0 |
| Missing expected review hash reason | expected_execution_capsule_operator_review_hash_required |
| Missing decision payload reason | execution_capsule_operator_decision_required |
| Complete decision reason | execution_capsule_operator_decision_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule operator review hash exists before decision | covered |
| expected execution capsule operator review hash must match | covered |
| execution capsule operator decision payload is required | covered |
| operator decision is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public decision exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule operator decision
for a later manual provider test candidate. It does not add an external call
path, SDK integration, env value access, network access, provider response
parsing, hosted execution, live operator approval, or production provider
readiness.

## AW-LIVE-37 Disabled Execution Capsule Release Attestation Metrics

Measured after adding the blocked disabled first-call execution capsule
release attestation boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 480 |
| Pytest passed cases | 480 |
| Regression delta vs AW-LIVE-36 baseline | +3 |
| API execution capsule release attestation integration tests | 3 |
| Provider envelope API integration tests | 85 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule release attestation public summary fields | 16 |
| Execution capsule release attestation component count | 8 |
| Execution capsule release attestation component hash count | 4 |
| Execution capsule release attestation no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Attestation passed count with missing expected decision hash | 7 |
| Attestation mismatch count with missing expected decision hash | 1 |
| Attestation passed count without attestation payload | 4 |
| Attestation mismatch count without attestation payload | 4 |
| Attestation passed count with complete attestation | 8 |
| Execution permission count with complete attestation | 0 |
| Missing expected decision hash reason | expected_execution_capsule_operator_decision_hash_required |
| Missing attestation payload reason | execution_capsule_release_attestation_required |
| Complete attestation reason | execution_capsule_release_attestation_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule operator decision hash exists before attestation | covered |
| expected execution capsule operator decision hash must match | covered |
| execution capsule release attestation payload is required | covered |
| release attestation is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public attestation exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule release
attestation for a later manual provider test candidate. It does not add an
external call path, SDK integration, env value access, network access, provider
response parsing, hosted execution, live operator approval, or production
provider readiness.

## AW-LIVE-38 Disabled Execution Capsule Release Seal Metrics

Measured after adding the blocked disabled first-call execution capsule
release seal boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 483 |
| Pytest passed cases | 483 |
| Regression delta vs AW-LIVE-37 baseline | +3 |
| API execution capsule release seal integration tests | 3 |
| Provider envelope API integration tests | 88 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule release seal public summary fields | 16 |
| Execution capsule release seal component count | 8 |
| Execution capsule release seal component hash count | 4 |
| Execution capsule release seal no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Seal passed count with missing expected attestation hash | 7 |
| Seal mismatch count with missing expected attestation hash | 1 |
| Seal passed count without seal payload | 4 |
| Seal mismatch count without seal payload | 4 |
| Seal passed count with complete seal | 8 |
| Execution permission count with complete seal | 0 |
| Missing expected attestation hash reason | expected_execution_capsule_release_attestation_hash_required |
| Missing seal payload reason | execution_capsule_release_seal_required |
| Complete seal reason | execution_capsule_release_seal_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule release attestation hash exists before seal | covered |
| expected execution capsule release attestation hash must match | covered |
| execution capsule release seal payload is required | covered |
| seal material is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public seal exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule release seal for
a later manual provider test candidate. It does not add an external call path,
SDK integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-39 Disabled Execution Capsule Final Authorization Metrics

Measured after adding the blocked disabled first-call execution capsule final
authorization boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 486 |
| Pytest passed cases | 486 |
| Regression delta vs AW-LIVE-38 baseline | +3 |
| API execution capsule final authorization integration tests | 3 |
| Provider envelope API integration tests | 90 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule final authorization public summary fields | 16 |
| Execution capsule final authorization component count | 8 |
| Execution capsule final authorization component hash count | 4 |
| Execution capsule final authorization no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Authorization passed count with missing expected release seal hash | 7 |
| Authorization mismatch count with missing expected release seal hash | 1 |
| Authorization passed count without authorization payload | 4 |
| Authorization mismatch count without authorization payload | 4 |
| Authorization passed count with complete authorization | 8 |
| Execution permission count with complete authorization | 0 |
| Missing expected release seal hash reason | expected_execution_capsule_release_seal_hash_required |
| Missing authorization payload reason | execution_capsule_final_authz_required |
| Complete authorization reason | execution_capsule_final_authz_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule release seal hash exists before final authorization | covered |
| expected execution capsule release seal hash must match | covered |
| execution capsule final authorization payload is required | covered |
| final authorization material is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public final authorization exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule final
authorization for a later manual provider test candidate. It does not add an
external call path, SDK integration, env value access, network access, provider
response parsing, hosted execution, live operator approval, or production
provider readiness.

## AW-LIVE-40 Disabled Execution Capsule Authz Export Read Model Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization export/read-model boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 489 |
| Pytest passed cases | 489 |
| Regression delta vs AW-LIVE-39 baseline | +3 |
| API execution capsule authz export integration tests | 3 |
| Provider envelope API integration tests | 93 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz export public summary fields | 16 |
| Execution capsule authz export read-model top-level fields | 4 |
| Execution capsule authz export component count | 8 |
| Execution capsule authz export component hash count | 4 |
| Execution capsule authz export no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Export passed count with missing expected final authz hash | 7 |
| Export mismatch count with missing expected final authz hash | 1 |
| Export passed count without export payload | 4 |
| Export mismatch count without export payload | 4 |
| Export passed count with complete export | 8 |
| Execution permission count with complete export | 0 |
| Missing expected final authz hash reason | expected_execution_capsule_final_authz_hash_required |
| Missing export payload reason | execution_capsule_authz_export_required |
| Complete export reason | execution_capsule_authz_export_execution_closed |
| Complete read-model reason | execution_capsule_authz_export_read_model_available |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule final authz hash exists before export | covered |
| expected execution capsule final authz hash must match | covered |
| execution capsule authz export payload is required | covered |
| export metadata is represented as hash/count evidence | covered |
| authz export read-model exposes latest hash and counts only | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz export exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
export/read-model for a later manual provider test candidate. It does not add
an external call path, SDK integration, env value access, network access,
provider response parsing, hosted execution, live operator approval, or
production provider readiness.

## AW-LIVE-41 Disabled Execution Capsule Authz Handoff Packet Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization handoff packet boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 492 |
| Pytest passed cases | 492 |
| Regression delta vs AW-LIVE-40 baseline | +3 |
| API execution capsule authz handoff integration tests | 3 |
| Provider envelope API integration tests | 96 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz handoff public summary fields | 17 |
| Execution capsule authz handoff component count | 8 |
| Execution capsule authz handoff component hash count | 4 |
| Execution capsule authz handoff no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Handoff passed count with missing expected authz export hash | 7 |
| Handoff mismatch count with missing expected authz export hash | 1 |
| Handoff passed count without handoff payload | 5 |
| Handoff mismatch count without handoff payload | 3 |
| Handoff passed count with complete handoff packet | 8 |
| Execution permission count with complete handoff packet | 0 |
| Missing expected authz export hash reason | expected_execution_capsule_authz_export_hash_required |
| Missing handoff payload reason | execution_capsule_authz_handoff_packet_required |
| Complete handoff packet reason | execution_capsule_authz_handoff_packet_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz export hash exists before handoff | covered |
| expected execution capsule authz export hash must match | covered |
| execution capsule authz handoff packet payload is required | covered |
| authz export read-model latest hash matches export hash | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz handoff exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
handoff packet for a later manual provider test candidate. It does not add an
external call path, SDK integration, env value access, network access, provider
response parsing, hosted execution, live operator approval, or production
provider readiness.

## AW-LIVE-42 Disabled Execution Capsule Authz Operator Review Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization operator review boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 495 |
| Pytest passed cases | 495 |
| Regression delta vs AW-LIVE-41 baseline | +3 |
| API execution capsule authz operator review integration tests | 3 |
| Provider envelope API integration tests | 99 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz operator review public summary fields | 16 |
| Execution capsule authz operator review component count | 8 |
| Execution capsule authz operator review component hash count | 4 |
| Execution capsule authz operator review no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Operator review count with complete review | 1 |
| Review request count with complete review | 1 |
| Review passed count with missing expected authz handoff hash | 7 |
| Review mismatch count with missing expected authz handoff hash | 1 |
| Review passed count without review payload | 4 |
| Review mismatch count without review payload | 4 |
| Review passed count with complete operator review | 8 |
| Execution permission count with complete operator review | 0 |
| Missing expected authz handoff hash reason | expected_execution_capsule_authz_handoff_packet_hash_required |
| Missing operator review payload reason | execution_capsule_authz_operator_review_required |
| Complete operator review reason | execution_capsule_authz_operator_review_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz handoff packet hash exists before review | covered |
| expected execution capsule authz handoff packet hash must match | covered |
| execution capsule authz operator review payload is required | covered |
| operator review is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz operator review exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
operator review for a later manual provider test candidate. It does not add an
external call path, SDK integration, env value access, network access, provider
response parsing, hosted execution, live operator approval, or production
provider readiness.

## AW-LIVE-43 Disabled Execution Capsule Authz Operator Decision Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization operator decision boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 498 |
| Pytest passed cases | 498 |
| Regression delta vs AW-LIVE-42 baseline | +3 |
| API execution capsule authz operator decision integration tests | 3 |
| Provider envelope API integration tests | 102 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz operator decision public summary fields | 16 |
| Execution capsule authz operator decision component count | 8 |
| Execution capsule authz operator decision component hash count | 4 |
| Execution capsule authz operator decision no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Operator decision count with complete decision | 1 |
| Decision request count with complete decision | 1 |
| Decision passed count with missing expected authz operator review hash | 7 |
| Decision mismatch count with missing expected authz operator review hash | 1 |
| Decision passed count without decision payload | 4 |
| Decision mismatch count without decision payload | 4 |
| Decision passed count with complete operator decision | 8 |
| Execution permission count with complete operator decision | 0 |
| Missing expected authz operator review hash reason | expected_execution_capsule_authz_operator_review_hash_required |
| Missing operator decision payload reason | execution_capsule_authz_operator_decision_required |
| Complete operator decision reason | execution_capsule_authz_operator_decision_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz operator review hash exists before decision | covered |
| expected execution capsule authz operator review hash must match | covered |
| execution capsule authz operator decision payload is required | covered |
| operator decision is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz operator decision exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
operator decision for a later manual provider test candidate. It does not add
an external call path, SDK integration, env value access, network access,
provider response parsing, hosted execution, live operator approval, or
production provider readiness.

## AW-LIVE-44 Disabled Execution Capsule Authz Release Attestation Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization release attestation boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 501 |
| Pytest passed cases | 501 |
| Regression delta vs AW-LIVE-43 baseline | +3 |
| API execution capsule authz release attestation integration tests | 3 |
| Provider envelope API integration tests | 105 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz release attestation public summary fields | 16 |
| Execution capsule authz release attestation component count | 8 |
| Execution capsule authz release attestation component hash count | 4 |
| Execution capsule authz release attestation no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Release attestation count with complete attestation | 1 |
| Attestation request count with complete attestation | 1 |
| Attestation passed count with missing expected authz operator decision hash | 7 |
| Attestation mismatch count with missing expected authz operator decision hash | 1 |
| Attestation passed count without attestation payload | 4 |
| Attestation mismatch count without attestation payload | 4 |
| Attestation passed count with complete release attestation | 8 |
| Execution permission count with complete release attestation | 0 |
| Missing expected authz operator decision hash reason | expected_execution_capsule_authz_operator_decision_hash_required |
| Missing release attestation payload reason | execution_capsule_authz_release_attestation_required |
| Complete release attestation reason | execution_capsule_authz_release_attestation_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz operator decision hash exists before attestation | covered |
| expected execution capsule authz operator decision hash must match | covered |
| execution capsule authz release attestation payload is required | covered |
| release attestation is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz release attestation exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
release attestation for a later manual provider test candidate. It does not add
an external call path, SDK integration, env value access, network access,
provider response parsing, hosted execution, live operator approval, or
production provider readiness.

## AW-LIVE-45 Disabled Execution Capsule Authz Release Seal Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization release seal boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 504 |
| Pytest passed cases | 504 |
| Regression delta vs AW-LIVE-44 baseline | +3 |
| API execution capsule authz release seal integration tests | 3 |
| Provider envelope API integration tests | 108 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz release seal public summary fields | 16 |
| Execution capsule authz release seal component count | 8 |
| Execution capsule authz release seal component hash count | 4 |
| Execution capsule authz release seal no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Seal material count with complete seal | 1 |
| Seal request count with complete seal | 1 |
| Seal passed count with missing expected authz release attestation hash | 7 |
| Seal mismatch count with missing expected authz release attestation hash | 1 |
| Seal passed count without seal payload | 4 |
| Seal mismatch count without seal payload | 4 |
| Seal passed count with complete release seal | 8 |
| Execution permission count with complete release seal | 0 |
| Missing expected authz release attestation hash reason | expected_execution_capsule_authz_release_attestation_hash_required |
| Missing release seal payload reason | execution_capsule_authz_release_seal_required |
| Complete release seal reason | execution_capsule_authz_release_seal_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz release attestation hash exists before seal | covered |
| expected execution capsule authz release attestation hash must match | covered |
| execution capsule authz release seal payload is required | covered |
| seal material is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz release seal exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
release seal for a later manual provider test candidate. It does not add an
external call path, SDK integration, env value access, network access, provider
response parsing, hosted execution, live operator approval, or production
provider readiness.

## AW-LIVE-46 Disabled Execution Capsule Authz Final Authorization Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 507 |
| Pytest passed cases | 507 |
| Regression delta vs AW-LIVE-45 baseline | +3 |
| API execution capsule authz final authorization integration tests | 3 |
| Provider envelope API integration tests | 111 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authorization public summary fields | 16 |
| Execution capsule authz final authorization component count | 8 |
| Execution capsule authz final authorization component hash count | 4 |
| Execution capsule authz final authorization no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Final authorization count with complete authorization | 1 |
| Authorization request count with complete authorization | 1 |
| Authorization passed count with missing expected authz release seal hash | 7 |
| Authorization mismatch count with missing expected authz release seal hash | 1 |
| Authorization passed count without authorization payload | 4 |
| Authorization mismatch count without authorization payload | 4 |
| Authorization passed count with complete final authorization | 8 |
| Execution permission count with complete final authorization | 0 |
| Missing expected authz release seal hash reason | expected_execution_capsule_authz_release_seal_hash_required |
| Missing final authorization payload reason | execution_capsule_authz_final_authz_required |
| Complete final authorization reason | execution_capsule_authz_final_authz_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz release seal hash exists before final authorization | covered |
| expected execution capsule authz release seal hash must match | covered |
| execution capsule authz final authorization payload is required | covered |
| final authorization is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authorization exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization for a later manual provider test candidate. It does not add
an external call path, SDK integration, env value access, network access,
provider response parsing, hosted execution, live operator approval, or
production provider readiness.

## AW-LIVE-47 Disabled Execution Capsule Authz Final Authz Export Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization export/read-model boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 510 |
| Pytest passed cases | 510 |
| Regression delta vs AW-LIVE-46 baseline | +3 |
| API execution capsule authz final authz export integration tests | 3 |
| Provider envelope API integration tests | 135 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz export public summary fields | 17 |
| Execution capsule authz final authz export read-model top-level fields | 4 |
| Execution capsule authz final authz export component count | 8 |
| Execution capsule authz final authz export component hash count | 4 |
| Execution capsule authz final authz export no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Export count with complete export | 1 |
| Export metadata count with complete export | 1 |
| Export request count with complete export | 1 |
| Export passed count with missing expected authz final authz hash | 7 |
| Export mismatch count with missing expected authz final authz hash | 1 |
| Export passed count without export payload | 4 |
| Export mismatch count without export payload | 4 |
| Export passed count with complete export | 8 |
| Execution permission count with complete export | 0 |
| Read-model latest export hash count with complete export | 1 |
| Read-model execution permission count with complete export | 0 |
| Missing expected authz final authz hash reason | expected_execution_capsule_authz_final_authz_hash_required |
| Missing final authz export payload reason | execution_capsule_authz_final_authz_export_required |
| Complete final authz export reason | execution_capsule_authz_final_authz_export_execution_closed |
| Read-model available reason | execution_capsule_authz_final_authz_export_read_model_available |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization hash exists before export | covered |
| expected execution capsule authz final authorization hash must match | covered |
| execution capsule authz final authorization export payload is required | covered |
| export metadata is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| read-model exposes latest export hash and counts only | covered |
| public authz final authz export exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization export/read-model for a later manual provider test
candidate. It does not add an external call path, SDK integration, env value
access, network access, provider response parsing, hosted execution, live
operator approval, or production provider readiness.

## AW-LIVE-48 Disabled Execution Capsule Authz Final Authz Handoff Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization handoff packet boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 513 |
| Pytest passed cases | 513 |
| Regression delta vs AW-LIVE-47 baseline | +3 |
| API execution capsule authz final authz handoff integration tests | 3 |
| Provider envelope API integration tests | 138 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz handoff public summary fields | 17 |
| Execution capsule authz final authz handoff component count | 8 |
| Execution capsule authz final authz handoff component hash count | 4 |
| Execution capsule authz final authz handoff no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Handoff packet count with complete handoff | 1 |
| Export read-model count with complete handoff | 1 |
| Handoff request count with complete handoff | 1 |
| Handoff passed count with missing expected authz final authz export hash | 7 |
| Handoff mismatch count with missing expected authz final authz export hash | 1 |
| Handoff passed count without handoff payload | 5 |
| Handoff mismatch count without handoff payload | 3 |
| Handoff passed count with complete handoff | 8 |
| Execution permission count with complete handoff | 0 |
| Missing expected authz final authz export hash reason | expected_execution_capsule_authz_final_authz_export_hash_required |
| Missing final authz handoff payload reason | execution_capsule_authz_final_authz_handoff_packet_required |
| Complete final authz handoff reason | execution_capsule_authz_final_authz_handoff_packet_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization export hash exists before handoff | covered |
| expected execution capsule authz final authorization export hash must match | covered |
| execution capsule authz final authorization handoff payload is required | covered |
| export read-model must point to the same export hash | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz handoff exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization handoff packet for a later manual provider test candidate.
It does not add an external call path, SDK integration, env value access,
network access, provider response parsing, hosted execution, live operator
approval, or production provider readiness.

## AW-LIVE-49 Disabled Execution Capsule Authz Final Authz Operator Review Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization operator review boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 516 |
| Pytest passed cases | 516 |
| Regression delta vs AW-LIVE-48 baseline | +3 |
| API execution capsule authz final authz operator review integration tests | 3 |
| Provider envelope API integration tests | 141 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz operator review public summary fields | 16 |
| Execution capsule authz final authz operator review component count | 8 |
| Execution capsule authz final authz operator review component hash count | 4 |
| Execution capsule authz final authz operator review no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Operator review count with complete review | 1 |
| Review request count with complete review | 1 |
| Review passed count with missing expected authz final authz handoff hash | 7 |
| Review mismatch count with missing expected authz final authz handoff hash | 1 |
| Review passed count without operator review payload | 4 |
| Review mismatch count without operator review payload | 4 |
| Review passed count with complete operator review | 8 |
| Execution permission count with complete operator review | 0 |
| Missing expected authz final authz handoff hash reason | expected_execution_capsule_authz_final_authz_handoff_packet_hash_required |
| Missing final authz operator review payload reason | execution_capsule_authz_final_authz_operator_review_required |
| Complete final authz operator review reason | execution_capsule_authz_final_authz_operator_review_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization handoff hash exists before review | covered |
| expected execution capsule authz final authorization handoff hash must match | covered |
| execution capsule authz final authorization operator review payload is required | covered |
| operator review is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz operator review exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization operator review for a later manual provider test candidate.
It does not add an external call path, SDK integration, env value access,
network access, provider response parsing, hosted execution, live operator
approval, or production provider readiness.

## AW-LIVE-50 Disabled Execution Capsule Authz Final Authz Operator Decision Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization operator decision boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 519 |
| Pytest passed cases | 519 |
| Regression delta vs AW-LIVE-49 baseline | +3 |
| API execution capsule authz final authz operator decision integration tests | 3 |
| Provider envelope API integration tests | 144 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz operator decision public summary fields | 16 |
| Execution capsule authz final authz operator decision component count | 8 |
| Execution capsule authz final authz operator decision component hash count | 4 |
| Execution capsule authz final authz operator decision no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Operator decision count with complete decision | 1 |
| Decision request count with complete decision | 1 |
| Decision passed count with missing expected authz final authz operator review hash | 7 |
| Decision mismatch count with missing expected authz final authz operator review hash | 1 |
| Decision passed count without operator decision payload | 4 |
| Decision mismatch count without operator decision payload | 4 |
| Decision passed count with complete operator decision | 8 |
| Execution permission count with complete operator decision | 0 |
| Missing expected authz final authz operator review hash reason | expected_execution_capsule_authz_final_authz_operator_review_hash_required |
| Missing final authz operator decision payload reason | execution_capsule_authz_final_authz_operator_decision_required |
| Complete final authz operator decision reason | execution_capsule_authz_final_authz_operator_decision_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization operator review hash exists before decision | covered |
| expected execution capsule authz final authorization operator review hash must match | covered |
| execution capsule authz final authorization operator decision payload is required | covered |
| operator decision is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz operator decision exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization operator decision for a later manual provider test
candidate. It does not add an external call path, SDK integration, env value
access, network access, provider response parsing, hosted execution, live
operator approval, or production provider readiness.

## AW-LIVE-51 Disabled Execution Capsule Authz Final Authz Release Attestation Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization release attestation boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 522 |
| Pytest passed cases | 522 |
| Regression delta vs AW-LIVE-50 baseline | +3 |
| API execution capsule authz final authz release attestation integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 147 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz release attestation public summary fields | 16 |
| Execution capsule authz final authz release attestation component count | 8 |
| Execution capsule authz final authz release attestation component hash count | 4 |
| Execution capsule authz final authz release attestation no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Release attestation count with complete attestation | 1 |
| Attestation request count with complete attestation | 1 |
| Attestation passed count with missing expected authz final authz operator decision hash | 7 |
| Attestation mismatch count with missing expected authz final authz operator decision hash | 1 |
| Attestation passed count without release attestation payload | 4 |
| Attestation mismatch count without release attestation payload | 4 |
| Attestation passed count with complete release attestation | 8 |
| Execution permission count with complete release attestation | 0 |
| Missing expected authz final authz operator decision hash reason | expected_execution_capsule_authz_final_authz_operator_decision_hash_required |
| Missing final authz release attestation payload reason | execution_capsule_authz_final_authz_release_attestation_required |
| Complete final authz release attestation reason | execution_capsule_authz_final_authz_release_attestation_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization operator decision hash exists before attestation | covered |
| expected execution capsule authz final authorization operator decision hash must match | covered |
| execution capsule authz final authorization release attestation payload is required | covered |
| release attestation is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz release attestation exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization release attestation for a later manual provider test
candidate. It does not add an external call path, SDK integration, env value
access, network access, provider response parsing, hosted execution, live
operator approval, or production provider readiness.

## AW-LIVE-52 Disabled Execution Capsule Authz Final Authz Release Seal Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization release seal boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 525 |
| Pytest passed cases | 525 |
| Regression delta vs AW-LIVE-51 baseline | +3 |
| API execution capsule authz final authz release seal integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 150 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz release seal public summary fields | 16 |
| Execution capsule authz final authz release seal component count | 8 |
| Execution capsule authz final authz release seal component hash count | 4 |
| Execution capsule authz final authz release seal no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Seal material count with complete seal | 1 |
| Seal request count with complete seal | 1 |
| Seal passed count with missing expected authz final authz release attestation hash | 7 |
| Seal mismatch count with missing expected authz final authz release attestation hash | 1 |
| Seal passed count without release seal payload | 4 |
| Seal mismatch count without release seal payload | 4 |
| Seal passed count with complete release seal | 8 |
| Execution permission count with complete release seal | 0 |
| Missing expected authz final authz release attestation hash reason | expected_execution_capsule_authz_final_authz_release_attestation_hash_required |
| Missing final authz release seal payload reason | execution_capsule_authz_final_authz_release_seal_required |
| Complete final authz release seal reason | execution_capsule_authz_final_authz_release_seal_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization release attestation hash exists before seal | covered |
| expected execution capsule authz final authorization release attestation hash must match | covered |
| execution capsule authz final authorization release seal payload is required | covered |
| release seal is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz release seal exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization release seal for a later manual provider test candidate.
It does not add an external call path, SDK integration, env value access,
network access, provider response parsing, hosted execution, live operator
approval, or production provider readiness.

## AW-LIVE-53 Disabled Execution Capsule Authz Final Authz Final Authorization Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 528 |
| Pytest passed cases | 528 |
| Regression delta vs AW-LIVE-52 baseline | +3 |
| API execution capsule authz final authz final authorization integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 153 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization public summary fields | 16 |
| Execution capsule authz final authz final authorization component count | 8 |
| Execution capsule authz final authz final authorization component hash count | 4 |
| Execution capsule authz final authz final authorization no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Final authz count with complete final authorization | 1 |
| Authz request count with complete final authorization | 1 |
| Authorization passed count with missing expected authz final authz release seal hash | 7 |
| Authorization mismatch count with missing expected authz final authz release seal hash | 1 |
| Authorization passed count without final authorization payload | 4 |
| Authorization mismatch count without final authorization payload | 4 |
| Authorization passed count with complete final authorization | 8 |
| Execution permission count with complete final authorization | 0 |
| Missing expected authz final authz release seal hash reason | expected_execution_capsule_authz_final_authz_release_seal_hash_required |
| Missing final authz final authorization payload reason | execution_capsule_authz_final_authz_final_authz_required |
| Complete final authz final authorization reason | execution_capsule_authz_final_authz_final_authz_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization release seal hash exists before final authorization | covered |
| expected execution capsule authz final authorization release seal hash must match | covered |
| execution capsule authz final authorization final authorization payload is required | covered |
| final authorization is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization for a later manual provider test
candidate. It does not add an external call path, SDK integration, env value
access, network access, provider response parsing, hosted execution, live
operator approval, or production provider readiness.

## AW-LIVE-54 Disabled Execution Capsule Authz Final Authz Final Authorization Export Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization export/read-model
boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 531 |
| Pytest passed cases | 531 |
| Regression delta vs AW-LIVE-53 baseline | +3 |
| API execution capsule authz final authz final authorization export integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 156 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization export public summary fields | 17 |
| Execution capsule authz final authz final authorization export read-model public summary fields | 4 |
| Execution capsule authz final authz final authorization export component count | 8 |
| Execution capsule authz final authz final authorization export component hash count | 4 |
| Execution capsule authz final authz final authorization export no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Export metadata count with complete export | 1 |
| Export request count with complete export | 1 |
| Export passed count with missing expected authz final authz final authorization hash | 7 |
| Export mismatch count with missing expected authz final authz final authorization hash | 1 |
| Export passed count without export payload | 4 |
| Export mismatch count without export payload | 4 |
| Export passed count with complete export | 8 |
| Execution permission count with complete export | 0 |
| Missing expected authz final authz final authorization hash reason | expected_execution_capsule_authz_final_authz_final_authz_hash_required |
| Missing final authz final authorization export payload reason | execution_capsule_authz_final_authz_final_authz_export_required |
| Complete final authz final authorization export reason | execution_capsule_authz_final_authz_final_authz_export_execution_closed |
| Complete export read-model reason | execution_capsule_authz_final_authz_final_authz_export_read_model_available |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization hash exists before export | covered |
| expected execution capsule authz final authorization final authorization hash must match | covered |
| execution capsule authz final authorization final authorization export payload is required | covered |
| final authorization export/read-model is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization export exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization export/read-model for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-55 Disabled Execution Capsule Authz Final Authz Final Authorization Handoff Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization handoff packet boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 534 |
| Pytest passed cases | 534 |
| Regression delta vs AW-LIVE-54 baseline | +3 |
| API execution capsule authz final authz final authorization handoff integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 159 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization handoff public summary fields | 17 |
| Execution capsule authz final authz final authorization handoff component count | 8 |
| Execution capsule authz final authz final authorization handoff component hash count | 4 |
| Execution capsule authz final authz final authorization handoff no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Export read-model count with complete handoff | 1 |
| Handoff request count with complete handoff | 1 |
| Handoff passed count with missing expected authz final authz final authorization export hash | 7 |
| Handoff mismatch count with missing expected authz final authz final authorization export hash | 1 |
| Handoff passed count without handoff payload | 5 |
| Handoff mismatch count without handoff payload | 3 |
| Handoff passed count with complete handoff | 8 |
| Execution permission count with complete handoff | 0 |
| Missing expected authz final authz final authorization export hash reason | expected_execution_capsule_authz_final_authz_final_authz_export_hash_required |
| Missing final authz final authorization handoff payload reason | execution_capsule_authz_final_authz_final_authz_handoff_packet_required |
| Complete final authz final authorization handoff reason | execution_capsule_authz_final_authz_final_authz_handoff_packet_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization export hash exists before handoff | covered |
| expected execution capsule authz final authorization final authorization export hash must match | covered |
| execution capsule authz final authorization final authorization handoff payload is required | covered |
| final authorization handoff packet is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization handoff exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization handoff packet for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-56 Disabled Execution Capsule Authz Final Authz Final Authorization Operator Review Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization operator review
boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 537 |
| Pytest passed cases | 537 |
| Regression delta vs AW-LIVE-55 baseline | +3 |
| API execution capsule authz final authz final authorization operator review integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 162 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization operator review public summary fields | 16 |
| Execution capsule authz final authz final authorization operator review component count | 8 |
| Execution capsule authz final authz final authorization operator review component hash count | 4 |
| Execution capsule authz final authz final authorization operator review no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Operator review count with complete review | 1 |
| Operator review request count with complete review | 1 |
| Review passed count with missing expected authz final authz final authorization handoff hash | 7 |
| Review mismatch count with missing expected authz final authz final authorization handoff hash | 1 |
| Review passed count without operator review payload | 4 |
| Review mismatch count without operator review payload | 4 |
| Review passed count with complete operator review | 8 |
| Execution permission count with complete operator review | 0 |
| Missing expected authz final authz final authorization handoff hash reason | expected_execution_capsule_authz_final_authz_final_authz_handoff_packet_hash_required |
| Missing final authz final authorization operator review payload reason | execution_capsule_authz_final_authz_final_authz_operator_review_required |
| Complete final authz final authorization operator review reason | execution_capsule_authz_final_authz_final_authz_operator_review_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization handoff hash exists before review | covered |
| expected execution capsule authz final authorization final authorization handoff hash must match | covered |
| execution capsule authz final authorization final authorization operator review payload is required | covered |
| final authorization operator review is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization operator review exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization operator review for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-57 Disabled Execution Capsule Authz Final Authz Final Authorization Operator Decision Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization operator decision
boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 540 |
| Pytest passed cases | 540 |
| Regression delta vs AW-LIVE-56 baseline | +3 |
| API execution capsule authz final authz final authorization operator decision integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 165 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization operator decision public summary fields | 16 |
| Execution capsule authz final authz final authorization operator decision component count | 8 |
| Execution capsule authz final authz final authorization operator decision component hash count | 4 |
| Execution capsule authz final authz final authorization operator decision no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Operator decision count with complete decision | 1 |
| Operator decision request count with complete decision | 1 |
| Decision passed count with missing expected authz final authz final authorization operator review hash | 7 |
| Decision mismatch count with missing expected authz final authz final authorization operator review hash | 1 |
| Decision passed count without operator decision payload | 4 |
| Decision mismatch count without operator decision payload | 4 |
| Decision passed count with complete operator decision | 8 |
| Execution permission count with complete operator decision | 0 |
| Missing expected authz final authz final authorization operator review hash reason | expected_execution_capsule_authz_final_authz_final_authz_operator_review_hash_required |
| Missing final authz final authorization operator decision payload reason | execution_capsule_authz_final_authz_final_authz_operator_decision_required |
| Complete final authz final authorization operator decision reason | execution_capsule_authz_final_authz_final_authz_operator_decision_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization operator review hash exists before decision | covered |
| expected execution capsule authz final authorization final authorization operator review hash must match | covered |
| execution capsule authz final authorization final authorization operator decision payload is required | covered |
| final authorization operator decision is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization operator decision exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization operator decision for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-58 Disabled Execution Capsule Authz Final Authz Final Authorization Release Attestation Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization release attestation
boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 543 |
| Pytest passed cases | 543 |
| Regression delta vs AW-LIVE-57 baseline | +3 |
| API execution capsule authz final authz final authorization release attestation integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 168 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization release attestation public summary fields | 16 |
| Execution capsule authz final authz final authorization release attestation component count | 8 |
| Execution capsule authz final authz final authorization release attestation component hash count | 4 |
| Execution capsule authz final authz final authorization release attestation no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Release attestation count with complete attestation | 1 |
| Release attestation request count with complete attestation | 1 |
| Attestation passed count with missing expected authz final authz final authorization operator decision hash | 7 |
| Attestation mismatch count with missing expected authz final authz final authorization operator decision hash | 1 |
| Attestation passed count without release attestation payload | 4 |
| Attestation mismatch count without release attestation payload | 4 |
| Attestation passed count with complete release attestation | 8 |
| Execution permission count with complete release attestation | 0 |
| Missing expected authz final authz final authorization operator decision hash reason | expected_execution_capsule_authz_final_authz_final_authz_operator_decision_hash_required |
| Missing final authz final authorization release attestation payload reason | execution_capsule_authz_final_authz_final_authz_release_attestation_required |
| Complete final authz final authorization release attestation reason | execution_capsule_authz_final_authz_final_authz_release_attestation_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization operator decision hash exists before attestation | covered |
| expected execution capsule authz final authorization final authorization operator decision hash must match | covered |
| execution capsule authz final authorization final authorization release attestation payload is required | covered |
| release attestation is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization release attestation exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization release attestation for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-59 Disabled Execution Capsule Authz Final Authz Final Authorization Release Seal Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization release seal boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 546 |
| Pytest passed cases | 546 |
| Regression delta vs AW-LIVE-58 baseline | +3 |
| API execution capsule authz final authz final authorization release seal integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 171 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization release seal public summary fields | 16 |
| Execution capsule authz final authz final authorization release seal component count | 8 |
| Execution capsule authz final authz final authorization release seal component hash count | 4 |
| Execution capsule authz final authz final authorization release seal no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Seal material count with complete seal | 1 |
| Seal request count with complete seal | 1 |
| Seal passed count with missing expected authz final authz final authorization release attestation hash | 7 |
| Seal mismatch count with missing expected authz final authz final authorization release attestation hash | 1 |
| Seal passed count without release seal payload | 4 |
| Seal mismatch count without release seal payload | 4 |
| Seal passed count with complete release seal | 8 |
| Execution permission count with complete release seal | 0 |
| Missing expected authz final authz final authorization release attestation hash reason | expected_execution_capsule_authz_final_authz_final_authz_release_attestation_hash_required |
| Missing final authz final authorization release seal payload reason | execution_capsule_authz_final_authz_final_authz_release_seal_required |
| Complete final authz final authorization release seal reason | execution_capsule_authz_final_authz_final_authz_release_seal_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization release attestation hash exists before seal | covered |
| expected execution capsule authz final authorization final authorization release attestation hash must match | covered |
| execution capsule authz final authorization final authorization release seal payload is required | covered |
| release seal is represented as hash/count evidence | covered |
| seal material is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization release seal exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization release seal for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-60 Disabled Execution Capsule Authz Final Authz Final Authorization Final Authorization Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization final authorization
boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 549 |
| Pytest passed cases | 549 |
| Regression delta vs AW-LIVE-59 baseline | +3 |
| API execution capsule authz final authz final authorization final authorization integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 174 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization final authorization public summary fields | 16 |
| Execution capsule authz final authz final authorization final authorization component count | 8 |
| Execution capsule authz final authz final authorization final authorization component hash count | 4 |
| Execution capsule authz final authz final authorization final authorization no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Final authorization material count with complete authorization | 1 |
| Final authorization request count with complete authorization | 1 |
| Authorization passed count with missing expected authz final authz final authorization release seal hash | 7 |
| Authorization mismatch count with missing expected authz final authz final authorization release seal hash | 1 |
| Authorization passed count without final authorization payload | 4 |
| Authorization mismatch count without final authorization payload | 4 |
| Authorization passed count with complete final authorization | 8 |
| Execution permission count with complete final authorization | 0 |
| Missing expected authz final authz final authorization release seal hash reason | expected_execution_capsule_authz_final_authz_final_authz_release_seal_hash_required |
| Missing final authz final authorization final authorization payload reason | execution_capsule_authz_final_authz_final_authz_final_authz_required |
| Complete final authz final authorization final authorization reason | execution_capsule_authz_final_authz_final_authz_final_authz_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization release seal hash exists before authorization | covered |
| expected execution capsule authz final authorization final authorization release seal hash must match | covered |
| execution capsule authz final authorization final authorization final authorization payload is required | covered |
| final authorization is represented as hash/count evidence | covered |
| final authorization material is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization final authorization exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization final authorization for a later manual
provider test candidate. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-61 Disabled Execution Capsule Authz Final Authz Final Authorization Final Authorization Export Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization final authorization
export/read-model boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 552 |
| Pytest passed cases | 552 |
| Regression delta vs AW-LIVE-60 baseline | +3 |
| API execution capsule authz final authz final authorization final authorization export integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 177 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization final authorization export public summary fields | 17 |
| Execution capsule authz final authz final authorization final authorization export read-model public fields | 4 |
| Execution capsule authz final authz final authorization final authorization export component count | 8 |
| Execution capsule authz final authz final authorization final authorization export component hash count | 4 |
| Execution capsule authz final authz final authorization final authorization export no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Export metadata count with complete export | 1 |
| Export request count with complete export | 1 |
| Export passed count with missing expected authz final authz final authorization final authorization hash | 7 |
| Export mismatch count with missing expected authz final authz final authorization final authorization hash | 1 |
| Export passed count without export payload | 4 |
| Export mismatch count without export payload | 4 |
| Export passed count with complete export | 8 |
| Export mismatch count with complete export | 0 |
| Execution permission count with complete export | 0 |
| Missing expected authz final authz final authorization final authorization hash reason | expected_execution_capsule_authz_final_authz_final_authz_final_authz_hash_required |
| Missing final authz final authorization final authorization export payload reason | execution_capsule_authz_final_authz_final_authz_final_authz_export_required |
| Complete final authz final authorization final authorization export reason | execution_capsule_authz_final_authz_final_authz_final_authz_export_execution_closed |
| Complete final authz final authorization final authorization export read-model reason | execution_capsule_authz_final_authz_final_authz_final_authz_export_read_model_available |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization final authorization hash exists before export | covered |
| expected execution capsule authz final authorization final authorization final authorization hash must match | covered |
| execution capsule authz final authorization final authorization final authorization export payload is required | covered |
| export metadata is represented as hash/count evidence | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization final authorization export exposes status/reason/hash/count fields only | covered |
| public authz final authz final authorization final authorization export read-model exposes latest hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization final authorization export/read-model
for a later manual provider test candidate. It does not add an external call
path, SDK integration, env value access, network access, provider response
parsing, hosted execution, live operator approval, or production provider
readiness.

## AW-LIVE-62 Disabled Execution Capsule Authz Final Authz Final Authorization Final Authorization Handoff Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization final authorization
handoff packet boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 555 |
| Pytest passed cases | 555 |
| Regression delta vs AW-LIVE-61 baseline | +3 |
| API execution capsule authz final authz final authorization final authorization handoff integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 180 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization final authorization handoff public summary fields | 17 |
| Execution capsule authz final authz final authorization final authorization handoff component count | 8 |
| Execution capsule authz final authz final authorization final authorization handoff component hash count | 4 |
| Execution capsule authz final authz final authorization final authorization handoff no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Export read-model count with complete handoff | 1 |
| Handoff request count with complete handoff | 1 |
| Handoff passed count with missing expected authz final authz final authorization final authorization export hash | 7 |
| Handoff mismatch count with missing expected authz final authz final authorization final authorization export hash | 1 |
| Handoff passed count without handoff payload | 5 |
| Handoff mismatch count without handoff payload | 3 |
| Handoff passed count with complete handoff | 8 |
| Handoff mismatch count with complete handoff | 0 |
| Execution permission count with complete handoff | 0 |
| Missing expected authz final authz final authorization final authorization export hash reason | expected_execution_capsule_authz_final_authz_final_authz_final_authz_export_hash_required |
| Missing final authz final authorization final authorization handoff payload reason | execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_required |
| Complete final authz final authorization final authorization handoff reason | execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization final authorization export hash exists before handoff | covered |
| expected execution capsule authz final authorization final authorization final authorization export hash must match | covered |
| execution capsule authz final authorization final authorization final authorization handoff payload is required | covered |
| supplied handoff upstream hash must match computed export hash | covered |
| export read-model points to the same export hash | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization final authorization handoff exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization final authorization handoff packet for
a later manual provider test candidate. It does not add an external call path,
SDK integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-63 Disabled Execution Capsule Authz Final Authz Final Authorization Final Authorization Operator Review Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization final authorization
operator review boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 558 |
| Pytest passed cases | 558 |
| Regression delta vs AW-LIVE-62 baseline | +3 |
| API execution capsule authz final authz final authorization final authorization operator review integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 183 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization final authorization operator review public summary fields | 16 |
| Execution capsule authz final authz final authorization final authorization operator review component count | 8 |
| Execution capsule authz final authz final authorization final authorization operator review component hash count | 4 |
| Execution capsule authz final authz final authorization final authorization operator review no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Operator review count with complete review | 1 |
| Review request count with complete review | 1 |
| Operator review passed count with missing expected handoff packet hash | 7 |
| Operator review mismatch count with missing expected handoff packet hash | 1 |
| Operator review passed count without review payload | 4 |
| Operator review mismatch count without review payload | 4 |
| Operator review passed count with complete review | 8 |
| Operator review mismatch count with complete review | 0 |
| Execution permission count with complete review | 0 |
| Missing expected handoff packet hash reason | expected_execution_capsule_authz_final_authz_final_authz_final_authz_handoff_packet_hash_required |
| Missing operator review payload reason | execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_required |
| Complete operator review reason | execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization final authorization handoff packet hash exists before operator review | covered |
| expected execution capsule authz final authorization final authorization final authorization handoff packet hash must match | covered |
| execution capsule authz final authorization final authorization final authorization operator review payload is required | covered |
| supplied review upstream hash must match computed handoff packet hash | covered |
| operator review is represented as hash/count evidence | covered |
| operator review request is required | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization final authorization operator review exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization final authorization operator review
for a later manual provider test candidate. It does not add an external call
path, SDK integration, env value access, network access, provider response
parsing, hosted execution, live operator approval, or production provider
readiness.

## AW-LIVE-64 Disabled Execution Capsule Authz Final Authz Final Authorization Final Authorization Operator Decision Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization final authorization
operator decision boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 561 |
| Pytest passed cases | 561 |
| Regression delta vs AW-LIVE-63 baseline | +3 |
| API execution capsule authz final authz final authorization final authorization operator decision integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 186 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization final authorization operator decision public summary fields | 16 |
| Execution capsule authz final authz final authorization final authorization operator decision component count | 8 |
| Execution capsule authz final authz final authorization final authorization operator decision component hash count | 4 |
| Execution capsule authz final authz final authorization final authorization operator decision no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Operator decision count with complete decision | 1 |
| Decision request count with complete decision | 1 |
| Operator decision passed count with missing expected operator review hash | 7 |
| Operator decision mismatch count with missing expected operator review hash | 1 |
| Operator decision passed count without decision payload | 4 |
| Operator decision mismatch count without decision payload | 4 |
| Operator decision passed count with complete decision | 8 |
| Operator decision mismatch count with complete decision | 0 |
| Execution permission count with complete decision | 0 |
| Missing expected operator review hash reason | expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_review_hash_required |
| Missing operator decision payload reason | execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_required |
| Complete operator decision reason | execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization final authorization operator review hash exists before operator decision | covered |
| expected execution capsule authz final authorization final authorization final authorization operator review hash must match | covered |
| execution capsule authz final authorization final authorization final authorization operator decision payload is required | covered |
| supplied decision upstream hash must match computed operator review hash | covered |
| operator decision is represented as hash/count evidence | covered |
| operator decision request is required | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization final authorization operator decision exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization final authorization operator decision
for a later manual provider test candidate. It does not add an external call
path, SDK integration, env value access, network access, provider response
parsing, hosted execution, live operator approval, or production provider
readiness.

## AW-LIVE-65 Disabled Execution Capsule Authz Final Authz Final Authorization Final Authorization Release Attestation Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization final authorization
release attestation boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 564 |
| Pytest passed cases | 564 |
| Regression delta vs AW-LIVE-64 baseline | +3 |
| API execution capsule authz final authz final authorization final authorization release attestation integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 189 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization final authorization release attestation public summary fields | 16 |
| Execution capsule authz final authz final authorization final authorization release attestation component count | 8 |
| Execution capsule authz final authz final authorization final authorization release attestation component hash count | 4 |
| Execution capsule authz final authz final authorization final authorization release attestation no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Release attestation count with complete attestation | 1 |
| Attestation request count with complete attestation | 1 |
| Release attestation passed count with missing expected operator decision hash | 7 |
| Release attestation mismatch count with missing expected operator decision hash | 1 |
| Release attestation passed count without attestation payload | 4 |
| Release attestation mismatch count without attestation payload | 4 |
| Release attestation passed count with complete attestation | 8 |
| Release attestation mismatch count with complete attestation | 0 |
| Execution permission count with complete attestation | 0 |
| Missing expected operator decision hash reason | expected_execution_capsule_authz_final_authz_final_authz_final_authz_operator_decision_hash_required |
| Missing release attestation payload reason | execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_required |
| Complete release attestation reason | execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization final authorization operator decision hash exists before release attestation | covered |
| expected execution capsule authz final authorization final authorization final authorization operator decision hash must match | covered |
| execution capsule authz final authorization final authorization final authorization release attestation payload is required | covered |
| supplied attestation upstream hash must match computed operator decision hash | covered |
| release attestation is represented as hash/count evidence | covered |
| release attestation request is required | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization final authorization release attestation exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization final authorization release attestation
for a later manual provider test candidate. It does not add an external call
path, SDK integration, env value access, network access, provider response
parsing, hosted execution, live operator approval, or production provider
readiness.

## AW-LIVE-66 Disabled Execution Capsule Authz Final Authz Final Authorization Final Authorization Release Seal Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization final authorization
release seal boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 567 |
| Pytest passed cases | 567 |
| Regression delta vs AW-LIVE-65 baseline | +3 |
| API execution capsule authz final authz final authorization final authorization release seal integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 192 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization final authorization release seal public summary fields | 16 |
| Execution capsule authz final authz final authorization final authorization release seal component count | 8 |
| Execution capsule authz final authz final authorization final authorization release seal component hash count | 4 |
| Execution capsule authz final authz final authorization final authorization release seal no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Seal material count with complete seal | 1 |
| Seal request count with complete seal | 1 |
| Seal passed count with missing expected release attestation hash | 7 |
| Seal mismatch count with missing expected release attestation hash | 1 |
| Seal passed count without release seal payload | 4 |
| Seal mismatch count without release seal payload | 4 |
| Seal passed count with complete release seal | 8 |
| Seal mismatch count with complete release seal | 0 |
| Execution permission count with complete seal | 0 |
| Missing expected release attestation hash reason | expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_attestation_hash_required |
| Missing release seal payload reason | execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_required |
| Complete release seal reason | execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization final authorization release-attestation hash exists before release seal | covered |
| expected execution capsule authz final authorization final authorization final authorization release-attestation hash must match | covered |
| execution capsule authz final authorization final authorization final authorization release seal payload is required | covered |
| supplied seal upstream hash must match computed release-attestation hash | covered |
| seal material is represented as hash/count evidence | covered |
| seal request is required | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization final authorization release seal exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization final authorization release seal for a
later manual provider test candidate. It does not add an external call path,
SDK integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, or production provider readiness.

## AW-LIVE-67 Disabled Execution Capsule Authz Final Authz Final Authorization Final Authorization Final Authorization Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization final authorization
final authorization boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 570 |
| Pytest passed cases | 570 |
| Regression delta vs AW-LIVE-66 baseline | +3 |
| API execution capsule authz final authz final authorization final authorization final authorization integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 195 |
| Demo provider envelope smoke tests | 1 |
| Execution capsule authz final authz final authorization final authorization final authorization public summary fields | 16 |
| Execution capsule authz final authz final authorization final authorization final authorization component count | 8 |
| Execution capsule authz final authz final authorization final authorization final authorization component hash count | 4 |
| Execution capsule authz final authz final authorization final authorization final authorization no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Final authorization count with complete authorization | 1 |
| Authorization request count with complete authorization | 1 |
| Authorization passed count with missing expected release seal hash | 7 |
| Authorization mismatch count with missing expected release seal hash | 1 |
| Authorization passed count without final authorization payload | 4 |
| Authorization mismatch count without final authorization payload | 4 |
| Authorization passed count with complete final authorization | 8 |
| Authorization mismatch count with complete final authorization | 0 |
| Execution permission count with complete authorization | 0 |
| Missing expected release seal hash reason | expected_execution_capsule_authz_final_authz_final_authz_final_authz_release_seal_hash_required |
| Missing final authorization payload reason | execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_required |
| Complete final authorization reason | execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization final authorization release-seal hash exists before final authorization | covered |
| expected execution capsule authz final authorization final authorization final authorization release-seal hash must match | covered |
| execution capsule authz final authorization final authorization final authorization final authorization payload is required | covered |
| supplied authorization upstream hash must match computed release-seal hash | covered |
| final authorization is represented as hash/count evidence | covered |
| authorization request is required | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization final authorization final authorization exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization final authorization final authorization
for a later manual provider test candidate. It does not add an external call
path, SDK integration, env value access, network access, provider response
parsing, hosted execution, live operator approval, or production provider
readiness.

Pattern note: the no-call evidence chain is now intentionally repetitive. A
future helper-pattern task should consolidate repeated gate construction while
preserving existing public fields and regression fixtures.

## AW-LIVE-68 Disabled Execution Capsule Authz Final Authz Final Authorization Final Authorization Final Authorization Export Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization final authorization
final authorization export/read-model boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 573 |
| Pytest passed cases | 573 |
| Regression delta vs AW-LIVE-67 baseline | +3 |
| API execution capsule authz final authz final authorization final authorization final authorization export integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 198 |
| Demo provider envelope smoke tests | 1 |
| Export public summary fields | 17 |
| Export read-model top-level fields | 3 |
| Export component count | 8 |
| Export component hash count | 4 |
| Export no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Export count with complete export | 1 |
| Export metadata count with complete export | 1 |
| Export request count with complete export | 1 |
| Export passed count with missing expected final authorization hash | 7 |
| Export mismatch count with missing expected final authorization hash | 1 |
| Export passed count without export payload | 4 |
| Export mismatch count without export payload | 4 |
| Export passed count with complete export | 8 |
| Export mismatch count with complete export | 0 |
| Read-model export count with complete export | 1 |
| Execution permission count with complete export | 0 |
| Missing expected final authorization hash reason | expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash_required |
| Missing export payload reason | execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_required |
| Complete export reason | execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_execution_closed |
| Complete read-model reason | execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model_available |
| Repeated helper flag references in integration fixture helper | 21 |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization final authorization final authorization hash exists before export | covered |
| expected execution capsule authz final authorization final authorization final authorization final authorization hash must match | covered |
| execution capsule authz final authorization final authorization final authorization final authorization export payload is required | covered |
| supplied export upstream hash must match computed final authorization hash | covered |
| export metadata is represented as hash/count evidence | covered |
| export request is required | covered |
| export read-model is available only after complete export | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization final authorization final authorization export exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization final authorization final authorization
export/read-model for a later manual provider test candidate. It does not add
an external call path, SDK integration, env value access, network access,
provider response parsing, hosted execution, live operator approval, or
production provider readiness.

Pattern note: AW-LIVE-68 confirms the repeated no-call gate structure is stable
but increasingly verbose. The next recommended task is `AW-LIVE-CHAIN-01`,
which should consolidate expected-hash validation, payload validation,
hash/count projection, claim-boundary hashing, and no-call counter hashing
without changing public field names.

## AW-LIVE-69 Disabled Execution Capsule Authz Final Authz Final Authorization Final Authorization Final Authorization Handoff Metrics

Measured after adding the blocked disabled first-call execution capsule
authorization final authorization final authorization final authorization
final authorization handoff packet boundary.

| Metric | Value |
|---|---:|
| Pytest collected cases | 576 |
| Pytest passed cases | 576 |
| Regression delta vs AW-LIVE-68 baseline | +3 |
| API execution capsule authz final authz final authorization final authorization final authorization handoff integration tests | 3 |
| Provider envelope API integration tests, cumulative documented boundary cases | 201 |
| Handoff public summary fields | 16 |
| Handoff component count | 8 |
| Handoff component hash count | 4 |
| Handoff no-call counter count | 13 |
| Claim-boundary check count | 3 |
| Handoff packet count with complete handoff | 1 |
| Export read-model count with complete handoff | 1 |
| Handoff request count with complete handoff | 1 |
| Handoff passed count with missing expected export hash | 7 |
| Handoff mismatch count with missing expected export hash | 1 |
| Handoff passed count with supplied export hash mismatch | 7 |
| Handoff mismatch count with supplied export hash mismatch | 1 |
| Handoff passed count with complete handoff | 8 |
| Handoff mismatch count with complete handoff | 0 |
| Execution permission count with complete handoff | 0 |
| Missing expected export hash reason | expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash_required |
| Supplied export hash mismatch reason | execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_packet_hash_mismatch |
| Complete handoff reason | execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_packet_execution_closed |
| Public raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Gate | Result |
|---|---|
| execution capsule authz final authorization final authorization final authorization final authorization export hash exists before handoff | covered |
| expected execution capsule authz final authorization final authorization final authorization final authorization export hash must match | covered |
| handoff packet payload is required | covered |
| supplied handoff upstream hash must match computed export hash | covered |
| export read-model is represented as hash/count evidence | covered |
| handoff request is required | covered |
| claim boundary is represented as hash/count evidence | covered |
| public authz final authz final authorization final authorization final authorization handoff exposes status/reason/hash/count fields only | covered |
| provider/runtime calls remain at 0 | covered |

Interpretation: this adds a local disabled execution capsule authorization
final authorization final authorization final authorization final authorization
handoff packet for a later manual provider test candidate. It does not add an
external call path, SDK integration, env value access, network access, provider
response parsing, hosted execution, live operator approval, or production
provider readiness.

## AW-LIVE-CHAIN-01 No-Call Boundary Helper Pattern Metrics

Measured after consolidating the repeated no-call boundary pattern into a
private helper and adopting it in `AW-LIVE-67` and `AW-LIVE-68`.

| Metric | Value |
|---|---:|
| Pytest collected cases | 573 |
| Pytest passed cases | 573 |
| Provider envelope integration tests passed | 198 |
| Public claim document tests passed | 3 |
| Demo provider envelope smoke tests passed | 1 |
| Compileall result | passed |
| Helper functions added | 1 |
| Helper-adopted projections | 2 |
| Helper-covered expected-hash validations | 2 |
| Helper-covered payload-presence validations | 2 |
| Helper-covered local evidence hash validations | 2 |
| Helper-covered request-presence validations | 2 |
| Helper-covered claim-boundary hash projections | 2 |
| Helper-covered no-call counter hash projections | 2 |
| Helper-covered hash/count projections | 2 |
| Public field name changes | 0 |
| Complete-path component count | 8 |
| Complete-path component hash count | 4 |
| No-call counter count | 13 |
| Claim-boundary check count | 3 |
| Execution permission count | 0 |
| Repeated claim-boundary blocks removed from latest projections | 2 |
| Repeated no-call counter blocks removed from latest projections | 2 |
| Repeated component-check blocks removed from latest projections | 2 |
| Product provider/env import findings | 0 |
| Non-zero provider/network/env counter findings | 0 |
| Raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Verification Command | Result |
|---|---:|
| `python -m compileall apps tests examples` | passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no` | 3 passed |
| `python -m pytest tests\integration\test_api_public_projection.py -q --color=no` | 198 passed |
| `python -m pytest tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q --color=no` | 1 passed |
| `python -m pytest tests -q --color=no` | 573 passed |
| `.\scripts\verify.ps1` | 573 passed |
| product provider/env import scan | 0 findings |
| non-zero provider/network/env counter scan | 0 findings |

Interpretation: AW-LIVE-CHAIN-01 is a local maintainability refactor over
existing disabled no-call evidence. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, execution permission, or production
provider readiness.

Next recommended task: `AW-LIVE-CHAIN-02`, extending helper adoption to
`AW-LIVE-60` through `AW-LIVE-66` in small batches while keeping public
projection tests green.

## AW-LIVE-CHAIN-02 No-Call Boundary Helper Rollout Metrics

Measured after extending the private no-call boundary helper to `AW-LIVE-60`
through `AW-LIVE-66`.

| Metric | Value |
|---|---:|
| Pytest collected cases | 573 |
| Pytest passed cases | 573 |
| Provider envelope integration tests passed | 198 |
| Helper functions total | 1 |
| Helper-adopted projections in CHAIN-01 | 2 |
| Newly helper-adopted projections in CHAIN-02 | 7 |
| Helper-adopted projections total | 9 |
| Public field name changes | 0 |
| Complete-path component count | 8 |
| Complete-path component hash count | 4 |
| No-call counter count | 13 |
| Claim-boundary check count | 3 |
| Execution permission count | 0 |
| Repeated claim-boundary blocks removed total | 9 |
| Repeated no-call counter blocks removed total | 9 |
| Repeated component-check blocks removed total | 9 |
| Product provider/env import findings | 0 |
| Non-zero provider/network/env counter findings | 0 |
| Raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Comparison Metric | AW-LIVE-CHAIN-01 | AW-LIVE-CHAIN-02 |
|---|---:|---:|
| helper-adopted projections total | 2 | 9 |
| newly helper-adopted projections | 2 | 7 |
| repeated direct no-call boundary blocks removed total | 2 | 9 |
| provider envelope integration tests passed | 198 | 198 |
| public field name changes | 0 | 0 |
| execution permission count | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m compileall apps tests examples` | passed |
| `python -m pytest tests\integration\test_api_public_projection.py -q --color=no` | 198 passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no` | 3 passed |
| `python -m pytest tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q --color=no` | 1 passed |
| `python -m pytest tests -q --color=no` | 573 passed |
| `.\scripts\verify.ps1` | 573 passed |
| `git diff --check` | passed |
| product provider/env import scan | 0 findings |
| non-zero provider/network/env counter scan | 0 findings |

Interpretation: AW-LIVE-CHAIN-02 is a local helper rollout over existing
disabled no-call evidence. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, execution permission, or production
provider readiness.

Next recommended task: `AW-LIVE-69` if the priority is continuing the disabled
no-call chain, or `AW-LIVE-CHAIN-03` if the priority is extending helper
adoption into older no-call stages first.

## AW-LIVE-CHAIN-03 No-Call Boundary Helper Rollout Metrics

Measured after extending the private no-call boundary helper to `AW-LIVE-53`
through `AW-LIVE-59`.

| Metric | Value |
|---|---:|
| Pytest collected cases | 573 |
| Pytest passed cases | 573 |
| Provider envelope integration tests passed | 198 |
| Helper functions total | 1 |
| Helper-adopted projections in CHAIN-01 | 2 |
| Newly helper-adopted projections in CHAIN-02 | 7 |
| Newly helper-adopted projections in CHAIN-03 | 7 |
| Helper-adopted projections total | 16 |
| Public field name changes | 0 |
| Complete-path component count | 8 |
| Complete-path component hash count | 4 |
| No-call counter count | 13 |
| Claim-boundary check count | 3 |
| Execution permission count | 0 |
| Repeated claim-boundary blocks removed total | 16 |
| Repeated no-call counter blocks removed total | 16 |
| Repeated component-check blocks removed total | 16 |
| Product provider/env import findings | 0 |
| Non-zero provider/network/env counter findings | 0 |
| Raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Comparison Metric | AW-LIVE-CHAIN-01 | AW-LIVE-CHAIN-02 | AW-LIVE-CHAIN-03 |
|---|---:|---:|---:|
| helper-adopted projections total | 2 | 9 | 16 |
| newly helper-adopted projections | 2 | 7 | 7 |
| repeated direct no-call boundary blocks removed total | 2 | 9 | 16 |
| provider envelope integration tests passed | 198 | 198 | 198 |
| public field name changes | 0 | 0 | 0 |
| execution permission count | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m compileall apps tests examples` | passed |
| `python -m pytest tests\integration\test_api_public_projection.py -q --color=no` | 198 passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no` | 3 passed |
| `python -m pytest tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q --color=no` | 1 passed |
| `python -m pytest tests -q --color=no` | 573 passed |
| `.\scripts\verify.ps1` | 573 passed |
| `git diff --check` | passed |
| product provider/env import scan | 0 findings |
| non-zero provider/network/env counter scan | 0 findings |

Interpretation: AW-LIVE-CHAIN-03 is a local helper rollout over existing
disabled no-call evidence. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, execution permission, or production
provider readiness.

Next recommended task: `AW-LIVE-69` if the priority is continuing the disabled
no-call chain, or `AW-LIVE-CHAIN-04` if the priority is extending helper
adoption into older no-call stages first.

## AW-LIVE-CHAIN-04 No-Call Boundary Helper Rollout Metrics

Measured after extending the private no-call boundary helper to `AW-LIVE-46`
through `AW-LIVE-52`.

| Metric | Value |
|---|---:|
| Pytest collected cases | 576 |
| Pytest passed cases | 576 |
| Provider envelope integration tests passed | 201 |
| Helper functions total | 1 |
| Helper-adopted projections in CHAIN-01 | 2 |
| Newly helper-adopted projections in CHAIN-02 | 7 |
| Newly helper-adopted projections in CHAIN-03 | 7 |
| Newly helper-adopted projections in CHAIN-04 | 7 |
| Helper-adopted projections total | 24 |
| Public field name changes | 0 |
| Complete-path component count | 8 |
| Complete-path component hash count | 4 |
| No-call counter count | 13 |
| Claim-boundary check count | 3 |
| Execution permission count | 0 |
| Repeated claim-boundary blocks removed total | 23 |
| Repeated no-call counter blocks removed total | 23 |
| Repeated component-check blocks removed total | 23 |
| Product provider/env import findings | 0 |
| Non-zero provider/network/env counter findings | 0 |
| Raw prompt/provider body/provider payload findings | 0 |
| Raw approval authorization field findings | 0 |
| Raw operator identity findings | 0 |
| Env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

| Comparison Metric | AW-LIVE-CHAIN-01 | AW-LIVE-CHAIN-02 | AW-LIVE-CHAIN-03 | AW-LIVE-CHAIN-04 |
|---|---:|---:|---:|---:|
| helper-adopted projections total | 2 | 9 | 16 | 24 |
| newly helper-adopted projections | 2 | 7 | 7 | 7 |
| repeated direct no-call boundary blocks removed total | 2 | 9 | 16 | 23 |
| provider envelope integration tests passed | 198 | 198 | 198 | 201 |
| public field name changes | 0 | 0 | 0 | 0 |
| execution permission count | 0 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m compileall apps tests examples` | passed |
| `python -m pytest tests\integration\test_api_public_projection.py -q --color=no` | 201 passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no` | 3 passed |
| `python -m pytest tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q --color=no` | 1 passed |
| `python -m pytest tests -q --color=no` | 576 passed |
| `.\scripts\verify.ps1` | 576 passed |
| `git diff --check` | passed |
| product provider/env import scan | 0 findings |
| non-zero provider/network/env counter scan | 0 findings |

Interpretation: AW-LIVE-CHAIN-04 is a local helper rollout over existing
disabled no-call evidence. It does not add an external call path, SDK
integration, env value access, network access, provider response parsing,
hosted execution, live operator approval, execution permission, or production
provider readiness.

Next recommended task: `AW-LIVE-70` if the priority is continuing the disabled
no-call chain. If maintainability remains the priority, inspect older duplicated
no-call blocks before adding another helper backfill.

## AW-MVP-01 Service-Shaped Vertical Slice Metrics

Measured after adding the local service-shaped path from idea intake to
verification read-model summary.

| Metric | Value |
|---|---:|
| Golden path scenario count | 1 |
| Required stage count | 7 |
| Covered stage count | 7 |
| Stage coverage | 100.0% |
| Artifact count in current fixture | 6 |
| Runner plan count | 1 |
| Verification report count | 1 |
| Runner plan hash count in verification read model | 1 |
| Failed report count | 0 |
| Artifact linkage by `run_id` | 100% |
| Forbidden public exposure findings | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |
| Public claim drift findings | 0 |
| Verification read API smoke tests | 2 |
| Verification read unavailable-store result | blocked |
| Pytest collected cases | 578 |
| Pytest passed cases | 578 |

| Verification Command | Result |
|---|---:|
| `python -m compileall apps examples tests` | passed |
| `python -m pytest tests\smoke\test_mvp_service_flow.py -q --color=no` | 2 passed |
| `python -m pytest tests -q --color=no` | 578 passed |
| `.\scripts\verify.ps1` | 578 passed |

Interpretation: AW-MVP-01 makes the current service flow easier to review by
connecting run creation, composed read model, artifact read model, and
verification read model in one local dry-run path. It does not add provider
execution, provider SDK import, env value access, network access, target
workspace execution, hosted behavior, or generated application delivery.

## AW-SOLAR-01 Planner Provider Preparation Metrics

Measured after adding the disabled Solar planner preflight boundary and the
fixture-vs-preflight comparison path.

| Metric | Value |
|---|---:|
| Comparison variants | 2 |
| Fixture stage coverage | 7/7 |
| Fixture stage coverage percent | 100.0% |
| Fixture artifact count | 6 |
| Solar preflight status | preflight_only |
| Solar preflight check count | 12 |
| Solar preflight failed check count | 0 |
| Solar preflight policy hash count | 1 |
| Solar preflight cost/timeout/quota hash count | 1 |
| Solar preflight request contract hash count | 1 |
| Solar planner provider success count | 0 |
| Provider-generated blueprint count | 0 |
| Solar disabled preflight provider calls | 0 |
| Solar provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 7 |
| New smoke tests | 2 |

| Comparison Variant | Status | Stage Coverage | Provider Calls | SDK Imports | Env Value Reads | Network Calls |
|---|---|---:|---:|---:|---:|---:|
| `fixture_planner` | passed | 7/7 | 0 | 0 | 0 | 0 |
| `solar_pro_3_disabled_preflight` | preflight_only | preflight-only | 0 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m pytest tests\unit\test_planner_provider_preflight.py -q --color=no` | 7 passed |
| `python -m pytest tests\smoke\test_solar_planner_preflight.py -q --color=no` | 2 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-solar-01-demo --include-solar-planner-preflight` | passed |
| `python -m compileall apps examples packages tests` | passed |
| `python -m pytest tests -q --color=no` | 587 passed |

Interpretation: AW-SOLAR-01 prepares the planner provider boundary while
keeping the existing fixture planner as the only artifact-producing path.
It does not add provider execution, provider SDK import, env value access,
network access, provider-generated planning output, target runtime execution,
hosted behavior, or generated application delivery.

## AW-DAACS-RUNTIME-00 Target Runtime Sandbox Metrics

Measured after adding the no-call DAACS target runtime sandbox preflight
contract and dry-run-vs-preflight comparison path.

| Metric | Value |
|---|---:|
| Comparison variants | 2 |
| Dry-run fixture stage coverage | 7/7 |
| Dry-run fixture stage coverage percent | 100.0% |
| Target runtime preflight status | blocked |
| Target runtime preflight check count | 19 |
| Target runtime preflight failed check count | 1 |
| Intentional execution-closed check count | 1 |
| Allowed write path count | 3 |
| Requested write path count | 3 |
| Expected output path count | 3 |
| Denied path count in clean comparison | 0 |
| Blocked operation count in clean comparison | 0 |
| Rollback plan count | 1 |
| Abort criteria count | 2 |
| Cleanup step count | 2 |
| Path traversal fixtures blocked | 1/1 |
| Absolute path fixtures blocked | 1/1 |
| Disallowed write fixtures blocked | 1/1 |
| Package install fixtures blocked | 1/1 |
| Server start fixtures blocked | 1/1 |
| Network command fixtures blocked | 1/1 |
| Filesystem writes | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 9 |
| New smoke tests | 2 |

| Comparison Variant | Status | Stage Coverage | Filesystem Writes | Subprocess Calls | Network Calls | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | 0 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m pytest tests\unit\test_target_runtime_sandbox.py -q --color=no` | 9 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 2 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-00-demo --include-daacs-runtime-preflight` | passed |
| `python -m compileall apps examples packages tests` | passed |
| `python -m pytest tests -q --color=no` | 598 passed |

Interpretation: AW-DAACS-RUNTIME-00 defines the target runtime sandbox
preflight contract over a RunnerPlan hash. It does not add target runtime
execution, subprocess execution, package installation, server start, filesystem
write, network access, raw log storage, generated file body storage, hosted
behavior, or generated application delivery.

## AW-DAACS-RUNTIME-01 Disabled Adapter Admission Metrics

Measured after adding the no-call DAACS target runtime disabled adapter
admission skeleton and dry-run-vs-preflight-vs-adapter comparison path.

| Metric | Value |
|---|---:|
| Comparison variants | 3 |
| Dry-run fixture stage coverage | 7/7 |
| Dry-run fixture stage coverage percent | 100.0% |
| Target runtime preflight status | blocked |
| Disabled adapter admission status | blocked |
| Target runtime adapter admission reason | target_runtime_adapter_disabled |
| Adapter admission check count | 14 |
| Adapter admission failed check count | 1 |
| Preflight hash required block fixtures | 1/1 |
| Preflight hash mismatch block fixtures | 1/1 |
| Dirty preflight block fixtures | 1/1 |
| Valid preflight adapter reach count | 1 |
| Disabled adapter block count | 1 |
| Adapter preflight hash match count | 1 |
| Adapter execution permission count | 0 |
| Adapter filesystem writes | 0 |
| Adapter subprocess calls | 0 |
| Adapter network calls | 0 |
| Adapter DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 7 |
| Updated smoke tests | 3 |

| Comparison Variant | Status | Stage Coverage | Filesystem Writes | Subprocess Calls | Network Calls | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | 0 | 0 | 0 | 0 |
| `disabled_adapter_admission` | blocked | adapter-disabled | 0 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m pytest tests\unit\test_target_runtime_adapter_admission.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 10 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-01-demo --include-daacs-runtime-adapter-admission` | passed |
| `python -m compileall apps examples packages tests` | passed |
| `python -m pytest tests -q --color=no` | 606 passed |

Interpretation: AW-DAACS-RUNTIME-01 requires target runtime preflight hash
evidence before the disabled adapter skeleton can be reached. It still does
not add target runtime execution, subprocess execution, package installation,
server start, filesystem write, network access, raw log storage, generated file
body storage, hosted behavior, or generated application delivery.

## AW-DAACS-RUNTIME-02 Persisted Adapter Admission Evidence Metrics

`AW-DAACS-RUNTIME-02` stores disabled target runtime adapter admission evidence
in SQLite and exposes a public read model. The measured result is still no-call:
the adapter remains disabled, execution permission remains `0`, and the
read-model is hash/status/count-only.

| Metric | Value |
|---|---:|
| Comparison variants | 3 |
| Dry-run fixture stage coverage | 7/7 |
| Dry-run fixture stage coverage percent | 100.0% |
| Target runtime preflight status | blocked |
| Disabled adapter admission status | blocked |
| Adapter admission persistence status | persisted |
| Adapter admission persisted count | 1 |
| Adapter admission read-model status | available |
| Adapter admission read-model record count | 1 |
| Adapter admission hash count | 1 |
| Store block fixtures, corrupted/unavailable/wrong-schema | 3/3 |
| Duplicate rollback partial row count | 0 |
| Execution permission count | 0 |
| Filesystem writes outside local SQLite evidence store | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 5 |
| Updated smoke tests | 4 |

| Comparison Variant | Status | Stage Coverage | Persisted Rows | Filesystem Writes | Subprocess Calls | Network Calls | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | 1 | 0 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m pytest tests\unit\test_target_runtime_admission_store.py tests\unit\test_target_runtime_adapter_admission.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 16 passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py tests\unit\test_target_runtime_admission_store.py tests\unit\test_target_runtime_adapter_admission.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 19 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-02-demo --include-daacs-runtime-adapter-admission` | passed |
| `python -m compileall apps examples packages tests` | passed |
| `python -m pytest tests -q --color=no` | 612 passed |

Interpretation: AW-DAACS-RUNTIME-02 makes disabled adapter admission evidence
durable and queryable without opening DAACS runtime execution. It does not add
generated application output, provider calls, network calls, subprocess calls,
package installation, server start, raw file storage, or hosted behavior.

## AW-DAACS-RUNTIME-03 Disabled Output Manifest Contract Metrics

`AW-DAACS-RUNTIME-03` defines a no-call output manifest contract over the
persisted target runtime adapter admission read model. It describes expected
output groups as labels, hashes, and counts only. It does not write generated
files or execute DAACS target runtime code.

| Metric | Value |
|---|---:|
| Comparison variants | 4 |
| Dry-run fixture stage coverage | 7/7 |
| Dry-run fixture stage coverage percent | 100.0% |
| Target runtime preflight status | blocked |
| Disabled adapter admission status | blocked |
| Adapter admission read-model status | available |
| Output manifest status | blocked |
| Output manifest reason | target_runtime_output_manifest_execution_closed |
| Adapter admission read-model prerequisite coverage | 1/1 |
| Adapter admission hash match count | 1 |
| Output manifest hash coverage | 1/1 |
| Output group count | 3 |
| Output group hash count | 3 |
| Generated artifact body writes | 0 |
| Execution permission count | 0 |
| Filesystem writes outside local SQLite evidence stores | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 7 |
| Updated smoke tests | 5 |

| Comparison Variant | Status | Stage Coverage | Output Groups | Filesystem Writes | Subprocess Calls | Network Calls | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | n/a | 0 | 0 | 0 | 0 |
| `disabled_output_manifest_contract` | blocked | manifest-only | 3 | 0 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m pytest tests\unit\test_target_runtime_output_manifest.py -q --color=no` | 7 passed |
| `python -m pytest tests\unit\test_target_runtime_output_manifest.py tests\unit\test_target_runtime_admission_store.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 17 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-03-demo --include-daacs-runtime-adapter-admission --include-daacs-runtime-output-manifest` | passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py tests\unit\test_target_runtime_output_manifest.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 15 passed |
| `python -m compileall apps examples packages tests` | passed |
| `python -m pytest tests -q --color=no` | 620 passed |

Interpretation: AW-DAACS-RUNTIME-03 makes the future output evidence shape
explicit while keeping runtime execution closed. It does not add generated app
files, provider calls, network calls, subprocess calls, package installation,
server start, raw file storage, or hosted behavior.

## AW-DAACS-RUNTIME-04 Disabled Output Manifest Persistence Read Model Metrics

`AW-DAACS-RUNTIME-04` persists the disabled output manifest contract as a
hash/status/count-only SQLite evidence row and exposes a public read model by
run_id. It does not store generated file bodies or open target runtime
execution.

| Metric | Value |
|---|---:|
| Comparison variants | 4 |
| Dry-run fixture stage coverage | 7/7 |
| Dry-run fixture stage coverage percent | 100.0% |
| Target runtime preflight status | blocked |
| Disabled adapter admission status | blocked |
| Adapter admission read-model status | available |
| Output manifest status | blocked |
| Output manifest persistence status | persisted |
| Output manifest read-model status | available |
| Output manifest persisted count | 1 |
| Output manifest read-model record count | 1 |
| Output manifest read-model hash count | 1 |
| Output group count | 3 |
| Output group hash count | 3 |
| Generated artifact body writes | 0 |
| Execution permission count | 0 |
| Filesystem writes outside local SQLite evidence stores | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| Bad SQLite store block cases | 3/3 |
| Duplicate partial extra rows | 0 |
| New unit tests | 5 |
| Updated smoke tests | 5 |

| Comparison Variant | Status | Stage Coverage | Persisted Rows | Read Model Hashes | Filesystem Writes | Subprocess Calls | Network Calls | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | 1 | 1 | 0 | 0 | 0 | 0 |
| `persisted_disabled_output_manifest` | blocked/read-model available | manifest-only | 1 | 1 | 0 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m compileall apps examples packages tests` | passed |
| `python -m pytest tests\unit\test_target_runtime_output_manifest_store.py tests\unit\test_target_runtime_output_manifest.py tests\unit\test_target_runtime_admission_store.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 22 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-04-demo --include-daacs-runtime-output-manifest` | passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py tests\unit\test_target_runtime_output_manifest_store.py tests\unit\test_target_runtime_output_manifest.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 20 passed |
| `python -m pytest tests -q --color=no` | 625 passed |

Interpretation: AW-DAACS-RUNTIME-04 makes disabled output manifest evidence
durable and queryable without storing generated file bodies or claiming a
runtime result. It does not add generated app files, provider calls, network
calls, subprocess calls, package installation, server start, raw file storage,
or hosted behavior.

## AW-DAACS-RUNTIME-05 Disabled Generated Artifact Bundle Contract Metrics

`AW-DAACS-RUNTIME-05` defines a disabled generated artifact bundle contract over
the persisted output manifest read model. It exposes artifact unit labels,
hashes, status, reasons, counts, and zero-call counters only. It does not write
generated file bodies or open DAACS target runtime execution.

| Metric | Value |
|---|---:|
| Comparison variants | 5 |
| Dry-run fixture stage coverage | 7/7 |
| Dry-run fixture stage coverage percent | 100.0% |
| Target runtime preflight status | blocked |
| Disabled adapter admission status | blocked |
| Adapter admission read-model status | available |
| Output manifest status | blocked |
| Output manifest read-model status | available |
| Generated artifact bundle status | blocked |
| Generated artifact bundle reason | target_runtime_generated_artifact_bundle_execution_closed |
| Output manifest read-model prerequisite count | 1 |
| Output manifest hash match count | 1 |
| Generated artifact bundle hash coverage | 1/1 |
| Artifact unit count | 3 |
| Artifact unit hash count | 3 |
| Generated artifact body writes | 0 |
| Execution permission count | 0 |
| Filesystem writes outside local SQLite evidence stores | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 7 |
| Updated smoke tests | 6 |

| Comparison Variant | Status | Stage Coverage | Hash Evidence | Filesystem Writes | Subprocess Calls | Network Calls | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | 1 | 0 | 0 | 0 | 0 |
| `persisted_disabled_output_manifest` | blocked/read-model available | manifest-only | 1 | 0 | 0 | 0 | 0 |
| `disabled_generated_artifact_bundle` | blocked | bundle-only | 1 | 0 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m compileall apps examples packages tests` | passed |
| `python -m pytest tests\unit\test_target_runtime_generated_artifact_bundle.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 13 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-05-demo --include-daacs-runtime-generated-artifact-bundle` | passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py tests\unit\test_target_runtime_generated_artifact_bundle.py tests\unit\test_target_runtime_output_manifest_store.py tests\unit\test_target_runtime_output_manifest.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 28 passed |
| `python -m pytest tests -q --color=no` | 633 passed |

Interpretation: AW-DAACS-RUNTIME-05 makes the next generated artifact bundle
stage visible in the service-shaped demo without claiming generated source
files or runtime execution. It does not add generated app files, provider calls,
network calls, subprocess calls, package installation, server start, raw file
storage, or hosted behavior.

## AW-DAACS-RUNTIME-06 Fixture Artifact Materialization Metrics

`AW-DAACS-RUNTIME-06` materializes sanitized fixture artifacts in a configured
run-scoped local workspace. Public projections return relative paths, hashes,
status, reason, counts, repository flags, and claim boundaries only.

| Metric | Value |
|---|---:|
| Comparison variants | 6 |
| Dry-run fixture stage coverage | 7/7 |
| Dry-run fixture stage coverage percent | 100.0% |
| Target runtime preflight status | blocked |
| Disabled adapter admission status | blocked |
| Adapter admission read-model status | available |
| Output manifest status | blocked |
| Output manifest read-model status | available |
| Generated artifact bundle status | blocked |
| Fixture materialization status | passed |
| Fixture materialization reason | target_runtime_fixture_artifacts_materialized |
| Generated artifact bundle hash match count | 1 |
| Fixture artifact record count | 3 |
| Fixture artifact content hash count | 3 |
| Fixture workspace file write count | 3 |
| Filesystem writes outside workspace | 0 |
| Public artifact body return count | 0 |
| Public root path return count | 0 |
| Execution permission count | 0 |
| Provider calls | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 6 |
| Updated smoke tests | 7 |

| Comparison Variant | Status | Stage Coverage | Hash Evidence | Workspace Writes | Subprocess Calls | Network Calls | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | 1 | 0 | 0 | 0 | 0 |
| `persisted_disabled_output_manifest` | blocked/read-model available | manifest-only | 1 | 0 | 0 | 0 | 0 |
| `disabled_generated_artifact_bundle` | blocked | bundle-only | 1 | 0 | 0 | 0 | 0 |
| `fixture_artifact_materialization` | passed | fixture-only | 3 | 3 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m pytest tests\unit\test_target_runtime_fixture_materialization.py -q --color=no` | 6 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py -q --color=no` | 7 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-06-demo --include-daacs-runtime-fixture-materialization` | passed |
| `python -m compileall apps examples packages tests` | passed |
| `python -m pytest tests -q --color=no` | 640 passed |

Interpretation: AW-DAACS-RUNTIME-06 makes the service-shaped demo more visible
by writing local sanitized fixture artifacts. It does not add provider calls,
subprocess execution, package installation, server start, network access,
target runtime execution, raw file storage, build success, or hosted behavior.

## AW-VERIFY-01 Generated Artifact Verification Metrics

`AW-VERIFY-01` verifies the restricted fixture app skeleton files generated
under a run-scoped workspace. It checks workspace-relative paths, content
hashes, and byte counts. Public projections return status, hashes, reasons,
counts, repository flags, and zero-call counters only.

| Metric | Value |
|---|---:|
| Verification scenarios | 1 |
| Comparison variants | 8 |
| Dry-run fixture stage coverage | 7/7 |
| Generated fixture files expected | 9 |
| Generated fixture files checked | 9 |
| Content hash matches | 9 |
| Byte count matches | 9 |
| File read count for hash verification | 9 |
| Missing file fixtures blocked | 1 |
| Path traversal fixtures blocked | 1 |
| Absolute path fixtures blocked | 1 |
| Workspace hash mismatch fixtures blocked | 1 |
| Public artifact body return count | 0 |
| Public root path return count | 0 |
| Execution permission count | 0 |
| Provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Package installs | 0 |
| Builds | 0 |
| Server starts | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 10 |
| Updated smoke tests | 2 |

| Comparison Variant | Status | Stage Coverage | Checked Files | File Reads | Subprocess Calls | Network Calls | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_output_manifest` | blocked/read-model available | manifest-only | n/a | 0 | 0 | 0 | 0 |
| `disabled_generated_artifact_bundle` | blocked | bundle-only | n/a | 0 | 0 | 0 | 0 |
| `fixture_artifact_materialization` | passed | fixture-only | 3 | 0 | 0 | 0 | 0 |
| `restricted_workspace_generation` | passed | fixture-only | 9 | 0 | 0 | 0 | 0 |
| `generated_artifact_verification` | passed | verification-only | 9 | 9 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_generated_artifact_verification.py apps\api\agentic_workbench_api\services\target_runtime_generated_artifact_verification.py apps\api\agentic_workbench_api\main.py examples\demo-service-flow\run_local_demo.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_generated_artifact_verification.py tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py` | passed |
| `python -m pytest tests\unit\test_target_runtime_generated_artifact_verification.py -q` | 10 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py -q` | 12 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-verify-01-demo --include-daacs-runtime-generated-artifact-verification` | passed |
| `python examples\demo-service-flow\render_artifact_preview.py --store-root .local\aw-verify-01-preview --output .local\aw-verify-01-preview.html` | passed |
| `python -m pytest tests -q --color=no` | 670 passed |
| `git diff --check` | passed |

Interpretation: AW-VERIFY-01 makes generated fixture files verifiable by local
hash and byte-count checks. It does not add package installation, build,
server start, DAACS target runtime execution, provider calls, network calls,
raw file exposure, or hosted behavior.

## AW-BUILD-01 Generated Workspace Static Validation Metrics

`AW-BUILD-01` statically validates the verified restricted fixture app
workspace. It checks package JSON parsing, script labels, frontend/API markers,
and zero-call verification notes without running install/build/server commands.

| Metric | Value |
|---|---:|
| Static validation scenarios | 1 |
| Comparison variants | 9 |
| Dry-run fixture stage coverage | 7/7 |
| Verified file records used | 9 |
| Files statically checked | 9 |
| Static file reads | 9 |
| JSON parse checks | 1 |
| JSON parse passes | 1 |
| Required script labels | 4/4 |
| App component markers | 2/2 |
| API client markers | 2/2 |
| Zero-call report markers | 5/5 |
| Invalid package JSON fixtures blocked | 1 |
| Missing script fixtures blocked | 1 |
| Missing component marker fixtures blocked | 1 |
| Public artifact body return count | 0 |
| Public root path return count | 0 |
| Execution permission count | 0 |
| Provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Package installs | 0 |
| Builds | 0 |
| Server starts | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 10 |
| Updated smoke tests | 2 |

| Comparison Variant | Status | Stage Coverage | Static Files | File Reads | Package Installs | Builds | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_output_manifest` | blocked/read-model available | manifest-only | n/a | 0 | 0 | 0 | 0 |
| `disabled_generated_artifact_bundle` | blocked | bundle-only | n/a | 0 | 0 | 0 | 0 |
| `fixture_artifact_materialization` | passed | fixture-only | 3 | 0 | 0 | 0 | 0 |
| `restricted_workspace_generation` | passed | fixture-only | 9 | 0 | 0 | 0 | 0 |
| `generated_artifact_verification` | passed | verification-only | 9 | 9 | 0 | 0 | 0 |
| `generated_workspace_static_validation` | passed | static-validation-only | 9 | 9 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_generated_workspace_static_validation.py apps\api\agentic_workbench_api\services\target_runtime_generated_workspace_static_validation.py apps\api\agentic_workbench_api\main.py examples\demo-service-flow\run_local_demo.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_generated_workspace_static_validation.py tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py` | passed |
| `python -m pytest tests\unit\test_target_runtime_generated_workspace_static_validation.py -q --color=no` | 10 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py -q --color=no` | 13 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-build-01-demo --include-daacs-runtime-generated-workspace-static-validation` | passed |
| `python examples\demo-service-flow\render_artifact_preview.py --store-root .local\aw-build-01-preview --output .local\aw-build-01-preview.html` | passed |
| `python -m pytest tests -q --color=no` | 681 passed |
| `git diff --check` | passed |

Interpretation: AW-BUILD-01 raises the generated fixture workspace from
hash-verified files to static app-shape validation. It does not add package
installation, build, server start, DAACS target runtime execution, provider
calls, network calls, raw file exposure, or hosted behavior.

## AW-BUILD-02 Buildable Fixture App Manifest Metrics

`AW-BUILD-02` hardens the generated fixture workspace into a build-ready
candidate manifest. It records package script labels, dependency labels,
source entrypoint markers, hashes, counts, and zero-call boundaries without
running package installation, build, server start, provider calls, network
calls, subprocess calls, or DAACS target runtime execution.

| Metric | Value |
|---|---:|
| Build-readiness scenarios | 1 |
| Comparison variants | 10 |
| Dry-run fixture stage coverage | 7/7 |
| Generated fixture files | 9 |
| Verified file records used | 9 |
| Static validation file reads | 9 |
| Build-ready required file reads | 5 |
| Required script labels | 4/4 |
| Dependency labels | 7 |
| Placeholder dependency values | 0 |
| Index entry markers | 2/2 |
| Main entrypoint markers | 2/2 |
| Vite config markers | 2/2 |
| TS config markers | 2/2 |
| Package manifest dependency values returned | 0 |
| Public artifact body return count | 0 |
| Public root path return count | 0 |
| Execution permission count | 0 |
| Provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Package installs | 0 |
| Builds | 0 |
| Server starts | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 9 |
| Updated smoke tests | 1 |

| Comparison Variant | Status | Stage Coverage | Generated Files | File Reads | Package Installs | Builds | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_output_manifest` | blocked/read-model available | manifest-only | n/a | 0 | 0 | 0 | 0 |
| `disabled_generated_artifact_bundle` | blocked | bundle-only | n/a | 0 | 0 | 0 | 0 |
| `fixture_artifact_materialization` | passed | fixture-only | 3 | 0 | 0 | 0 | 0 |
| `restricted_workspace_generation` | passed | fixture-only | 9 | 0 | 0 | 0 | 0 |
| `generated_artifact_verification` | passed | verification-only | 9 | 9 | 0 | 0 | 0 |
| `generated_workspace_static_validation` | passed | static-validation-only | 9 | 9 | 0 | 0 | 0 |
| `buildable_fixture_manifest` | passed | manifest-only | 9 | 5 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_restricted_workspace_generation.py packages\daacs_builder\target_runtime_buildable_fixture_manifest.py apps\api\agentic_workbench_api\services\target_runtime_buildable_fixture_manifest.py apps\api\agentic_workbench_api\main.py examples\demo-service-flow\run_local_demo.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_buildable_fixture_manifest.py tests\unit\test_target_runtime_restricted_workspace_generation.py tests\unit\test_target_runtime_generated_artifact_verification.py tests\unit\test_target_runtime_generated_workspace_static_validation.py tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py` | passed |
| `python -m pytest tests\unit\test_target_runtime_buildable_fixture_manifest.py tests\unit\test_target_runtime_restricted_workspace_generation.py tests\unit\test_target_runtime_generated_artifact_verification.py tests\unit\test_target_runtime_generated_workspace_static_validation.py -q --color=no` | 38 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py -q --color=no` | 14 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-build-02-demo --include-daacs-runtime-buildable-fixture-manifest` | passed |
| `python examples\demo-service-flow\render_artifact_preview.py --store-root .local\aw-build-02-preview --output .local\aw-build-02-preview.html` | passed |
| `python -m pytest tests -q --color=no` | 691 passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no` | 3 passed |
| `git diff --check` | passed |

Interpretation: AW-BUILD-02 makes the fixture app a build-ready candidate by
manifest and static source shape only. It does not claim package install
success, local build success, server start, hosted behavior, Solar Pro 3
output, or DAACS target runtime execution.

## AW-BUILD-03 Local Build Preflight Metrics

`AW-BUILD-03` adds an explicit local build preflight over the AW-BUILD-02
buildable fixture app manifest. It records command labels, manifest hash
linkage, opt-in requirement, and zero default execution counters without
running package installation, build, server start, provider calls, network
calls, subprocess calls, or DAACS target runtime execution.

| Metric | Value |
|---|---:|
| Build preflight scenarios | 1 |
| Comparison variants | 11 |
| Dry-run fixture stage coverage | 7/7 |
| Generated fixture files | 9 |
| Build-ready required file reads | 5 |
| Local build command labels | 4 |
| Local build command hashes | 4 |
| Explicit local build opt-in required | 1 |
| Operator opt-in present by default | 0 |
| Execution permission count | 0 |
| Dependency value returns | 0 |
| Public artifact body return count | 0 |
| Public root path return count | 0 |
| Provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Package installs | 0 |
| Builds | 0 |
| Server starts | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 8 |
| Updated smoke tests | 3 |

| Comparison Variant | Status | Stage Coverage | Generated Files | File Reads | Package Installs | Builds | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_output_manifest` | blocked/read-model available | manifest-only | n/a | 0 | 0 | 0 | 0 |
| `disabled_generated_artifact_bundle` | blocked | bundle-only | n/a | 0 | 0 | 0 | 0 |
| `fixture_artifact_materialization` | passed | fixture-only | 3 | 0 | 0 | 0 | 0 |
| `restricted_workspace_generation` | passed | fixture-only | 9 | 0 | 0 | 0 | 0 |
| `generated_artifact_verification` | passed | verification-only | 9 | 9 | 0 | 0 | 0 |
| `generated_workspace_static_validation` | passed | static-validation-only | 9 | 9 | 0 | 0 | 0 |
| `buildable_fixture_manifest` | passed | manifest-only | 9 | 5 | 0 | 0 | 0 |
| `local_build_preflight` | passed | preflight-only | 9 | 5 | 0 | 0 | 0 |

| Verification Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_local_build_preflight.py apps\api\agentic_workbench_api\services\target_runtime_local_build_preflight.py apps\api\agentic_workbench_api\main.py examples\demo-service-flow\run_local_demo.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_local_build_preflight.py tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py` | passed |
| `python -m pytest tests\unit\test_target_runtime_local_build_preflight.py tests\unit\test_target_runtime_buildable_fixture_manifest.py -q --color=no` | 17 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py -q --color=no` | 16 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-build-03-demo --include-daacs-runtime-local-build-preflight` | passed |
| `python examples\demo-service-flow\render_artifact_preview.py --store-root .local\aw-build-03-preview --output .local\aw-build-03-preview.html` | passed |
| `python -m pytest tests -q --color=no` | 701 passed |

Interpretation: AW-BUILD-03 makes the generated fixture app eligible for a
future explicit local build attempt by preflight only. It does not claim
package install success, local build success, server start, hosted behavior,
Solar Pro 3 output, or DAACS target runtime execution.

## AW-BUILD-04 Explicit Local Fixture App Build Attempt Metrics

`AW-BUILD-04` runs one explicit opt-in local fixture app package/build attempt
inside the run-scoped generated workspace. The default path remains blocked.
The attempted path records sanitized command labels, exit-code hashes, output
hashes, byte counts, durations, status, reason, and counters only.

| Metric | Value |
|---|---:|
| Local build attempt scenarios | 1 |
| Comparison variants | 12 |
| Dry-run fixture stage coverage | 7/7 |
| Generated fixture app files | 9 |
| Required preflight hash match | 1/1 |
| Operator opt-in present | 1 |
| Local command execution allowed | 1 |
| Command result count | 2 |
| Command output hash count | 2 |
| Package install attempts | 1 |
| Package install calls | 1 |
| Build attempts | 1 |
| Build calls | 1 |
| Server start attempts | 0 |
| Server start calls | 0 |
| Subprocess calls | 2 |
| Package-manager network attempts | 1 |
| Provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| DAACS target runtime calls | 0 |
| Raw command output returns | 0 |
| Public artifact body return count | 0 |
| Public root path return count | 0 |
| Failed checks | 0 |
| Public claim drift findings | 0 |
| New unit tests | 6 |
| Updated smoke tests | 3 |

| Comparison Variant | Status | Stage Coverage | Generated Files | Package Installs | Builds | Server Starts | Runtime Calls |
|---|---|---:|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | n/a | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_adapter_admission` | blocked/read-model available | adapter-disabled | n/a | 0 | 0 | 0 | 0 |
| `persisted_disabled_output_manifest` | blocked/read-model available | manifest-only | n/a | 0 | 0 | 0 | 0 |
| `disabled_generated_artifact_bundle` | blocked | bundle-only | n/a | 0 | 0 | 0 | 0 |
| `fixture_artifact_materialization` | passed | fixture-only | 3 | 0 | 0 | 0 | 0 |
| `restricted_workspace_generation` | passed | fixture-only | 9 | 0 | 0 | 0 | 0 |
| `generated_artifact_verification` | passed | verification-only | 9 | 0 | 0 | 0 | 0 |
| `generated_workspace_static_validation` | passed | static-validation-only | 9 | 0 | 0 | 0 | 0 |
| `buildable_fixture_manifest` | passed | manifest-only | 9 | 0 | 0 | 0 | 0 |
| `local_build_preflight` | passed | preflight-only | 9 | 0 | 0 | 0 | 0 |
| `local_build_attempt` | passed | local-build-attempt-only | 9 | 1 | 1 | 0 | 0 |

| Local Environment | Result |
|---|---|
| Node.js | `v24.15.0` |
| npm | `11.12.1` |
| Package install command | exit code `0` |
| Build command | exit code `0` |
| Sanitized install output byte count | `25` |
| Sanitized build output byte count | `389` |

| Verification Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_local_build_attempt.py apps\api\agentic_workbench_api\services\target_runtime_local_build_attempt.py apps\api\agentic_workbench_api\main.py` | passed |
| `python -m pytest tests\unit\test_target_runtime_local_build_attempt.py -q --color=no` | 6 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py::test_daacs_runtime_local_build_attempt_api_requires_explicit_opt_in tests\smoke\test_daacs_runtime_preflight.py::test_local_service_demo_records_local_build_attempt_as_blocked_without_allow -q --color=no` | 2 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-build-04-demo --include-daacs-runtime-local-build-attempt --allow-local-build-attempt` | passed |
| `python -m pytest tests\smoke\test_artifact_preview_surface.py -q --color=no` | 3 passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no` | 3 passed |
| `python -m pytest tests -q --color=no` | 710 passed |
| `git diff --check` | passed |

Interpretation: AW-BUILD-04 proves that the generated fixture app can reach a
measured opt-in local package/build attempt in the current local environment.
It does not claim server start, hosted behavior, external provider output,
Solar Pro 3 planner output, or DAACS target runtime execution.

## AW-DEMO-FINAL-01 Portfolio Demo Package Metrics

`AW-DEMO-FINAL-01` packages the service-shaped local demo into one
reviewer-facing command. The command writes a sanitized JSON summary and static
HTML preview. With explicit opt-in, it includes the AW-BUILD-04 local fixture
app build-attempt evidence.

| Metric | Value |
|---|---:|
| Portfolio demo scenarios | 1 |
| Portfolio command count | 1 |
| Dry-run fixture stage coverage | 7/7 |
| Stage coverage percent | 100.0 |
| Summary JSON generated | 1 |
| Preview HTML generated | 1 |
| Generated fixture app files | 9 |
| Local build attempt evidence records | 1 |
| Local build attempt status | passed |
| Local build command results | 2 |
| Package install attempts | 1 |
| Build attempts | 1 |
| Server starts | 0 |
| Provider calls | 0 |
| DAACS target runtime calls | 0 |
| Public raw body exposure | 0 |
| Public root path exposure | 0 |
| Public claim drift findings | 0 |
| New smoke tests | 3 |

| Verification Command | Result |
|---|---:|
| `python -m compileall examples\demo-service-flow\run_portfolio_demo.py tests\smoke\test_portfolio_demo_package.py` | passed |
| `python -m pytest tests\smoke\test_portfolio_demo_package.py -q --color=no` | 3 passed |
| `python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-demo-final-01 --allow-local-build-attempt` | passed |
| `python -m pytest tests\smoke\test_portfolio_demo_package.py tests\unit\test_public_claim_projection_docs.py -q --color=no` | 6 passed |
| `python -m pytest tests -q --color=no` | 713 passed |
| `git diff --check` | passed |

Interpretation: AW-DEMO-FINAL-01 gives reviewers one local command that creates
both machine-readable and human-readable demo evidence. It does not claim
server start, hosted behavior, external provider output, Solar Pro 3 planner
output, or DAACS target runtime execution.

## Next Implementation Measurement Plan

The next implementation work should choose between planner quality and
generated-code realism.

| Work Order | Primary target | Required boundary |
|---|---|---|
| `AW-SOLAR-LIVE-01` | one tightly scoped Solar planner live spike | one representative idea, timeout/cost/input-size cap, sanitized response projection, no DAACS target runtime execution |
| `AW-DAACS-RUNTIME-MVP-02` | dynamic fixture-to-code generation over SoT/Brief | run-scoped workspace only, no provider call unless explicitly routed, no server start by default |

| Planned Metric | Target |
|---|---:|
| Representative scenario count | 1 |
| Sanitized projection count | 1 |
| Server starts | 0 |
| Unapproved provider/DAACS runtime calls | 0 |
| Public raw file body exposure | 0 |
| Local root path exposure | 0 |

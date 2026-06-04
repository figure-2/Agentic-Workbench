# AW-SOLAR-01 Work Order: Solar Pro 3 Planner Provider Preparation

## Conclusion

`AW-SOLAR-01` is the next implementation unit after `AW-MVP-01`.
Its purpose is to prepare a provider-backed planner path for the first
service-shaped planning step while keeping the default runtime local,
deterministic, and no-call.

This is not a Solar Pro 3 provider call. It is a provider-readiness slice for
the planner boundary.

## Implementation Unit

```text
id: AW-SOLAR-01
depends_on:
  - AW-MVP-01
  - AW-LIVE-00
  - AW-LIVE-05
scope: provider-backed planner boundary preparation, still disabled by default
risk_level: high
rollback_plan: remove planner-provider selector/preflight/test/docs and keep AW-MVP-01 fixture planner path
```

## Senior Review Decision

Product lens:

- The next visible product improvement is better planning quality and document
  drafting, not target workspace execution.
- The user-facing path should remain: idea, planning artifacts, PRD package,
  implementation brief, approval, runner plan, verification report.

Architecture lens:

- Add a planner-provider boundary separate from the runner/provider boundary.
- Keep the current fixture planner as the default path.
- Route Solar Pro 3 through an explicit `planner_provider=solar_pro_3_disabled`
  or equivalent preflight mode before any future provider call is considered.

Security lens:

- The provider path may reference the env key name only.
- It must not read the env key value, import provider SDKs, call the network, or
  persist raw prompt/provider bodies.
- Raw idea text may be used only in request-scoped memory in later live work.
  This work order stores only hashes, counts, summaries, policy status, and
  reasons.

Data lens:

- Public records should bind the provider candidate to `run_id`,
  `prompt_contract_hash`, stage target, policy hash, timeout hash, cost/quota
  hash, and request summary hash.
- The provider response projection must be a placeholder with status and hash
  fields only.

QA lens:

- Compare the existing fixture planner path with the disabled Solar planner
  preflight path on the same representative idea.
- The comparison must record numeric counts for stage coverage, artifacts,
  provider calls, SDK imports, env value reads, and raw exposure findings.

Audit lens:

- Public wording must say planner provider preparation.
- Do not claim provider output quality, hosted behavior, generated application
  delivery, or target runtime execution.

## Scope

Add a disabled planner provider preparation layer:

```text
IdeaBrief
-> prompt_contract_hash
-> planner provider selector
-> fixture planner path OR disabled Solar preflight path
-> public provider-readiness projection
-> unchanged AW-MVP-01 artifact chain
```

Recommended implementation shape:

- `PlannerProviderMode`: `fixture`, `solar_pro_3_disabled`
- `PlannerProviderPreflightRequest`
- `PlannerProviderPreflightResult`
- `PlannerProviderSelector`
- optional API/demo flag for preflight-only mode
- comparison smoke test over the AW-MVP-01 demo idea

## Non-Scope

- No Solar Pro 3 provider call.
- No provider SDK import.
- No env key value read.
- No network call.
- No provider response parsing.
- No provider-generated PlanningBlueprint.
- No target runtime execution.
- No generated app delivery claim.
- No raw prompt, provider request body, or provider response body persistence.

## Acceptance Tests

- Default `/api/v1/runs` path still uses the fixture planner.
- Disabled Solar planner preflight can be requested explicitly.
- Missing provider policy blocks before provider admission.
- Missing timeout/cost/quota blocks before provider admission.
- Provider env key value read count remains `0`.
- Provider SDK import count remains `0`.
- Network call count remains `0`.
- Solar Pro 3 provider call count remains `0`.
- Raw prompt/provider request/provider response durable storage findings remain
  `0`.
- Fixture and disabled Solar-preflight paths are clearly separated in public
  projection.
- AW-MVP-01 stage coverage remains `7/7` for the fixture path.
- Disabled Solar-preflight path returns `blocked` or `preflight_only`, not
  provider success.
- Existing regression suite remains green.

## Comparison Experiment

Run one representative idea through two paths:

| Variant | Expected status | Provider call count | Stage coverage |
|---|---|---:|---:|
| `fixture_planner` | passed | 0 | 7/7 |
| `solar_pro_3_disabled_preflight` | blocked or preflight_only | 0 | 0/7 or inherited fixture-only if no run is created |

Record these metrics in `docs/metrics.md` after implementation:

| Metric | Target |
|---|---:|
| Comparison variants | 2 |
| Fixture stage coverage | 7/7 |
| Solar disabled preflight provider calls | 0 |
| Env value reads | 0 |
| SDK imports | 0 |
| Network calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |

## Suggested Files

- `packages/div_planner/provider_boundary.py`
- `apps/api/agentic_workbench_api/services/planner_provider_preflight.py`
- `apps/api/agentic_workbench_api/main.py`
- `examples/demo-service-flow/run_local_demo.py`
- `tests/unit/test_planner_provider_preflight.py`
- `tests/smoke/test_solar_planner_preflight.py`
- `docs/evals/aw-solar-01-planner-provider-preparation.md`
- `docs/metrics.md`
- `README.md`

## Completion Criteria

- Public field names are documented.
- Comparison experiment results are numeric and recorded.
- No-call counters remain zero.
- The next work item can decide whether to implement a first manual provider
  call proposal for planner generation or continue improving the fixture
  planner quality.

## Implementation Evidence

Implemented files:

- `packages/div_planner/provider_boundary.py`
- `apps/api/agentic_workbench_api/services/planner_provider_preflight.py`
- `apps/api/agentic_workbench_api/main.py`
- `examples/demo-service-flow/run_local_demo.py`
- `tests/unit/test_planner_provider_preflight.py`
- `tests/smoke/test_solar_planner_preflight.py`
- `docs/evals/aw-solar-01-planner-provider-preparation.md`
- `docs/metrics.md`

Observed comparison result:

| Variant | Status | Stage coverage | Provider calls | SDK imports | Env value reads | Network calls |
|---|---|---:|---:|---:|---:|---:|
| `fixture_planner` | passed | 7/7 | 0 | 0 | 0 | 0 |
| `solar_pro_3_disabled_preflight` | preflight_only | preflight-only | 0 | 0 | 0 | 0 |

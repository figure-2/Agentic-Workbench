# AW-SOLAR-01 Planner Provider Preparation

## Conclusion

AW-SOLAR-01은 Solar Pro 3 실제 호출이 아니라, planner 단계에 붙일
provider 후보 경계를 no-call preflight로 준비한 단계다. 기본
`/api/v1/runs` 흐름은 기존 fixture planner를 유지한다.

## Scope

포함:

- fixture planner 기본 경로 유지
- disabled Solar planner preflight selector
- `POST /api/v1/planner/provider/preflight`
- local demo의 optional Solar planner preflight 비교 실험
- hash/count/status/reason 중심 public projection
- env value read, SDK import, network call, provider call 0 검증

제외:

- Solar Pro 3 API 호출
- Upstage SDK import
- `.env` 값 로드
- provider-generated PlanningBlueprint
- raw prompt 또는 provider body persistence
- DAACS target runtime 실행
- generated app delivery claim

## Boundary Flow

```text
IdeaBrief
-> prompt_contract_hash
-> fixture planner path
-> AW-MVP-01 artifact chain
```

Optional preflight comparison:

```text
run_id + prompt_contract_hash
-> planner provider selector
-> solar_pro_3_disabled preflight
-> public status/hash/count projection
-> provider call remains 0
```

## Acceptance Results

| Acceptance | Result |
|---|---|
| Default `/api/v1/runs` path keeps fixture planner | covered |
| Disabled Solar planner preflight is explicit | covered |
| Missing provider policy blocks before provider admission | covered |
| Missing timeout/cost/quota blocks before provider admission | covered |
| Provider env value reads | 0 |
| Provider SDK imports | 0 |
| Network calls | 0 |
| Solar Pro 3 provider calls | 0 |
| Raw prompt/provider body durable storage findings | 0 |
| Fixture and disabled Solar paths separated in public projection | covered |
| AW-MVP-01 fixture stage coverage | 7/7 |
| Disabled Solar preflight status | preflight_only |

## Comparison Experiment

Representative local service demo command:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-solar-01-demo --include-solar-planner-preflight
```

| Variant | Status | Stage coverage | Provider calls | SDK imports | Env value reads | Network calls |
|---|---|---:|---:|---:|---:|---:|
| `fixture_planner` | passed | 7/7 | 0 | 0 | 0 | 0 |
| `solar_pro_3_disabled_preflight` | preflight_only | preflight-only | 0 | 0 | 0 | 0 |

## Quantitative Results

| Metric | Value |
|---|---:|
| Comparison variants | 2 |
| Fixture artifact count | 6 |
| Fixture stage coverage | 100.0% |
| Fixture required stages | 7 |
| Fixture covered stages | 7 |
| Solar preflight check count | 12 |
| Solar preflight failed check count | 0 |
| Solar preflight policy hash count | 1 |
| Solar preflight cost/timeout/quota hash count | 1 |
| Solar preflight request contract hash count | 1 |
| Solar planner provider success count | 0 |
| Provider-generated blueprint count | 0 |
| Provider calls | 0 |
| Solar provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 7 |
| New smoke tests | 2 |
| Full pytest passed cases | 587 |

## Verification

```powershell
python -m pytest tests/unit/test_planner_provider_preflight.py -q --color=no
python -m pytest tests/smoke/test_solar_planner_preflight.py -q --color=no
python -m compileall apps examples packages tests
python -m pytest tests -q --color=no
```

Observed result:

```text
7 passed
2 passed
compileall passed
587 passed
```

## Claim Boundary

This is planner provider preparation only. It does not prove provider output
quality, live Solar behavior, hosted behavior, generated application delivery,
or target runtime execution.

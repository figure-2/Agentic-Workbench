# AW-SOLAR-DRAFT-01 Solar Draft Projection

## Scope

`AW-SOLAR-DRAFT-01` projects reviewer-approved Solar quality comparison evidence
into draft `PlanningBlueprint` and `PRDPackage` public projections.

This is not canonical artifact binding. It does not write canonical artifact
rows, perform another Solar call, expose provider body text, or execute the
DAACS target runtime.

## Team Review

| Lens | Decision |
|---|---|
| Product | The project needs visible progress from planner quality evidence toward document candidates, but the candidate must stay review-only until a later handoff step. |
| Architecture | The draft projection consumes `AW-SOLAR-QUALITY-01` output by hash. `comparison_hash` mismatch or missing reviewer approval blocks the projection. |
| Security | Public output is limited to status, reason, hashes, labels, and counts. Provider body, prompt body, credential value, local root path, and runtime output are not returned. |
| QA | Unit tests cover missing reviewer approval, hash mismatch, and successful draft projection. Smoke tests cover API and local demo paths. |

## Boundary Flow

```text
Solar live-spike public projection
-> Solar quality comparison
-> reviewer approval hash
-> expected comparison hash validation
-> draft PlanningBlueprint / PRDPackage projection
-> canonical artifact write count remains 0
```

## Quantitative Results

Measured on 2026-06-05.

| Metric | Value |
|---|---:|
| Draft projection scenarios | 1 |
| Successful draft labels in API fixture | 2 |
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

The default local demo remains blocked because it does not perform a live Solar
call and does not carry reviewer-approved quality evidence. The API fixture
uses a fake projected Solar response to prove the hash and reviewer gates can
produce two draft projections without writing canonical artifacts.

## Verification

```powershell
python -m pytest tests\unit\test_solar_planner_draft_projection.py -q --color=no
```

Result:

```text
3 passed
```

```powershell
python -m pytest tests\smoke\test_solar_planner_preflight.py -q --color=no
```

Result:

```text
10 passed
```

```powershell
python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-solar-draft-01 --include-solar-planner-draft-projection
```

Observed:

```text
status: passed
draft_projection_status: blocked
fixture_stage_coverage: 7/7
draft_artifact_projection_count: 0
canonical_artifact_write_count: 0
additional_live_call_count: 0
draft_projection_provider_calls: 0
draft_projection_env_value_reads: 0
draft_projection_network_calls: 0
target_runtime_calls: 0
```

## Claim Boundary

This evidence may claim reviewer-gated Solar draft projection over public
quality evidence. It must not be described as canonical Solar artifact creation,
production planner quality proof, hosted behavior, or DAACS runtime execution.

## Next Work

The next implementation should connect draft projection review to a canonical
handoff gate or move directly to DAACS runtime MVP if portfolio-visible generated
code progress is the priority.

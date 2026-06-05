# AW-SOLAR-QUALITY-01 Fixture vs Solar Quality Comparison

## Scope

`AW-SOLAR-QUALITY-01` compares the existing fixture planner evidence with the
public projection from `AW-SOLAR-LIVE-01`. The goal is not to auto-apply Solar
output into planning artifacts. The goal is to decide whether Solar output is a
reviewer-approved draft candidate for future `PlanningBlueprint`, `PRDPackage`,
and `ImplementationBrief` generation.

The comparison consumes only public-safe fields: stage coverage, artifact count,
response hashes, summary section count, artifact hint count, missing required
stage count, reviewer approval hash status, and execution counters.

## Team Review

| Lens | Decision |
|---|---|
| Product | Quality comparison is the right next step because it connects the first live planner signal to visible planning quality without changing the artifact-producing path. |
| Architecture | The comparison is a separate projection. It does not mutate canonical run/artifact rows and does not create Solar-authored artifacts. |
| Security | Raw prompt text, provider body, credential value, local root paths, and generated file bodies remain absent from public output. |
| QA | Default comparison creates a blocked Solar projection and performs `0` additional live calls. Review approval is explicit and hash-only. |

## Boundary Flow

```text
fixture run summary
-> Solar live-spike public projection
-> section/hint/missing-stage comparison
-> reviewer approval hash gate
-> draft binding candidate only
```

## Quantitative Results

Measured on 2026-06-05.

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

The default scenario intentionally uses the blocked Solar live-spike projection,
so the Solar quality metrics remain `0` and the comparison is `review_blocked`.
A future reviewer-approved scenario can reuse the same comparison projection
after an explicit one-shot Solar measurement, but artifact creation remains a
separate implementation unit.

## Verification

```powershell
python -m pytest tests\unit\test_solar_planner_quality_comparison.py tests\unit\test_solar_planner_live_spike.py -q --color=no
```

Result:

```text
7 passed
```

```powershell
python -m pytest tests\smoke\test_solar_planner_preflight.py -q --color=no
```

Result:

```text
8 passed
```

```powershell
python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-solar-quality-01 --include-solar-planner-quality-comparison
```

Observed:

```text
status: passed
quality_comparison_status: review_blocked
fixture_stage_coverage: 7/7
additional_live_call_count: 0
comparison_provider_calls: 0
comparison_env_value_reads: 0
comparison_network_calls: 0
artifact_binding_permission_count: 0
target_runtime_calls: 0
```

## Claim Boundary

This evidence may claim fixture-vs-Solar public projection comparison and a
reviewer-gated draft binding boundary. It must not be described as Solar-authored
artifact generation, external-provider quality proof, hosted behavior, production
trust, or DAACS target runtime execution.

## Next Work

The next implementation should either:

1. Bind reviewer-approved Solar quality evidence into a draft
   `PlanningBlueprint`/`PRDPackage` projection without raw body storage.
2. Move to DAACS runtime MVP if generated-code realism is more important than
   planner quality.

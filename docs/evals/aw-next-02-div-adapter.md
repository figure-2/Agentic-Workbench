# AW-NEXT-02 Eval Report

## Summary

| Field | Value |
|---|---|
| Date | 2026-05-27 |
| Result | PASS |
| Scope | Offline DIV GlobalState to PlanningBlueprint adapter |
| Eval mode | offline-fixture-only |
| Live LLM calls | 0 |
| Live API calls | 0 |
| Model provider | Not used |

## Gates

| Gate | Result | Evidence |
|---|---|---|
| GlobalState Mapping Gate | PASS | `idea.blueprint`, `plan.sections`, `research`, `visual_artifacts` mapped |
| Backward Compatibility Gate | PASS | legacy string sections/evidence supported |
| Missing Evidence Gate | PASS | empty or analysis-only research does not break adapter |
| Raw Evidence Sanitization Gate | PASS | raw content, secrets, email, paths are removed/redacted through shared sanitizers |
| No-Live-Import Gate | PASS | adapter call does not import Streamlit, LangChain Upstage, Tavily, or Qdrant modules |
| Existing Regression Gate | PASS | prior schema, security, claim, path, smoke tests still pass |

## Quantitative Metrics

| Metric | Value |
|---|---:|
| Pytest collected cases | 36 |
| Pytest passed cases | 36 |
| Adapter test cases | 8 |
| New adapter test cases in this step | 6 |
| Source DIV state families covered | 5 |
| Live LLM calls | 0 |
| Live API calls | 0 |
| External provider imports in adapter test | 0 |

## Covered State Families

| State family | Covered |
|---|---|
| `idea.blueprint` runtime dict list | yes |
| `plan.sections` dict list | yes |
| `plan.sections` legacy string list | yes |
| `research.evidence_store` dict/string | yes |
| `research.gathered_evidence` legacy alias | yes |
| `research.search_results` | yes |
| `research.analysis_result` | yes |
| `plan.visual_artifacts` list/dict | yes |
| `visual.artifacts` map | yes |
| malformed nested state | yes |

## Coverage Character

This eval measures offline adapter contract behavior. It does not measure live DIV graph execution, Solar Pro 3 quality, external search quality, generated code quality, hosted success, or production security.

## Next Eligible Work

The next safe step is `PlanningBlueprint -> BuildSpec -> DAACSState` formalization. Solar Pro 3 should still remain outside the core schema and should enter through a later provider boundary.

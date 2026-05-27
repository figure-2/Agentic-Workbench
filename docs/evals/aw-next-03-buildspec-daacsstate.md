# AW-NEXT-03 Eval Report

## Summary

| Field | Value |
|---|---|
| Date | 2026-05-27 |
| Result | PASS |
| Scope | Offline PlanningBlueprint to BuildSpec to DAACSState contract |
| Eval mode | offline-fixture-only |
| Live LLM calls | 0 |
| Live API calls | 0 |
| Model provider | Not used |

## Gates

| Gate | Result | Evidence |
|---|---|---|
| Deterministic Endpoint Gate | PASS | feature-based resources generate stable `/api/v1` endpoints |
| API Contract Gate | PASS | endpoints, data models, evidence summary generated |
| Frontend Contract Gate | PASS | all API endpoints become frontend API calls |
| Acceptance Criteria Gate | PASS | endpoint and frontend call obligations preserved |
| DAACSState Mapping Gate | PASS | BuildSpec fields mapped into DAACS-compatible initial state |
| Path Boundary Gate | PASS | unsafe run ids are rejected |
| No-Live-Call Gate | PASS | no LLM/API/provider/DAACS runtime execution |
| Regression Gate | PASS | all previous tests still pass |

## Quantitative Metrics

| Metric | Value |
|---|---:|
| Pytest collected cases | 45 |
| Pytest passed cases | 45 |
| Adapter test cases | 18 |
| New adapter/schema test cases in this step | 9 |
| Representative BuildSpec endpoints | 5 |
| Representative API data models | 2 |
| Representative frontend API calls | 5 |
| Representative acceptance criteria | 12 |
| DAACSState mapped keys | 56 |
| `build_contract` keys | 8 |
| Unsafe run id fixtures rejected | 6 |
| Live LLM calls | 0 |
| Live API calls | 0 |

## Contract Snapshot

Representative feature inputs:

- `Run Timeline`
- `Evidence Review`

Generated endpoint set:

- `GET /api/v1/health`
- `GET /api/v1/run-timelines`
- `POST /api/v1/run-timelines`
- `GET /api/v1/evidence-reviews`
- `POST /api/v1/evidence-reviews`

Generated data models:

- `RunTimeline`
- `EvidenceReview`

## Coverage Character

This eval measures offline contract behavior. It does not measure live DAACS execution, generated code quality, package install success, local server startup, Solar Pro 3 quality, hosted success, or production readiness.

## Next Eligible Work

The next safe step is a DAACS offline runner boundary that can accept the mapped DAACSState without spawning CLI agents or running host-level package/server commands.

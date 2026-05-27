# AW-NEXT-01 Eval Report

## Summary

| Field | Value |
|---|---|
| Date | 2026-05-27 |
| Result | PASS |
| Scope | Offline P0 security/evidence/claim/path gate |
| Live LLM calls | 0 |
| Live API calls | 0 |
| Model provider | Not used |

## Conclusion

`AW-NEXT-01` does not require a live LLM. Upstage Solar Pro 3 should be added later behind a planner/provider boundary, after offline security and artifact gates remain stable.

## Gates

| Gate | Result | Evidence |
|---|---|---|
| Schema Gate | PASS | Existing schema tests pass |
| Adapter Gate | PASS | Existing DIV/DAACS adapter tests pass |
| Path Boundary Gate | PASS | 7 unsafe path fixtures rejected |
| Redaction Gate | PASS | secret, Bearer token, DB URL, email, phone, Windows path, Linux path fixtures covered |
| Public Artifact Exposure Gate | PASS | raw content, full prompt/search, private corpus keys removed from public payload |
| Claim Gate | PASS | forbidden claim variants blocked |
| Smoke Gate | PASS | fixture harness run succeeds and unsafe generated path is rejected |
| No-Live-Call Gate | PASS | no LLM/API provider client is invoked |

## Quantitative Metrics

| Metric | Value |
|---|---:|
| Test files | 7 |
| Unit test files | 5 |
| Smoke test files | 2 |
| Integration test files | 0 |
| Pytest collected cases | 30 |
| Pytest passed cases | 30 |
| Unsafe path fixtures | 7 |
| Redaction fixture classes | 7 |
| Live LLM calls | 0 |
| Live API calls | 0 |

## Coverage Character

This report measures contract/gate coverage. It does not measure generated-code quality, live planner quality, Solar Pro 3 output quality, hosted success, production security, or benchmark performance.

## Next Eligible Work

After this gate, the next safe step is `DIV GlobalState -> PlanningBlueprint` adapter expansion in offline mode. Live Solar Pro 3 integration should remain a separate provider boundary task.

# AW-DEMO-01 Local Service-Shaped Demo

## Scope

Add a repeatable local demo path that uses the public API boundary and composed
run read model:

```text
Idea
-> POST /api/v1/runs
-> sanitized artifact chain
-> local dry-run evidence persistence
-> GET /api/v1/runs/{run_id}
-> composed canonical run/evidence read model
```

The demo does not start a server. It runs the FastAPI app in-process through
`TestClient` and uses explicitly configured local SQLite projection stores.

## Current Implementation

- `examples/demo-service-flow/run_local_demo.py`
- `examples/demo-service-flow/README.md`
- `tests/smoke/test_local_service_demo.py`

The demo summary includes:

- run id and projection version
- artifact kinds and counts
- DIV identity signals from planning/PRD artifacts
- DAACS identity signals from BuildSpec, ImplementationBrief, RunnerPlan
  evidence, and VerificationReport evidence
- repository boundary markers
- zero-call execution boundary markers
- claim boundary markers

## Acceptance Results

| Gate | Result |
|---|---|
| demo creates one run through `POST /api/v1/runs` | covered |
| sanitized canonical run/artifact rows persisted | covered |
| sanitized runner/report/audit evidence rows persisted | covered |
| `GET /api/v1/runs/{run_id}` returns composed run/evidence read model | covered |
| `GET /api/v1/runs/{run_id}/artifacts` returns artifact metadata only | covered |
| artifact count at least 3 | covered, 6 in current fixture |
| same `run_id` links run, artifacts, runner plan, verification report, audit evidence | covered |
| DIV identity signals visible | planning blueprint and PRD artifacts covered |
| DAACS identity signals visible | BuildSpec, ImplementationBrief, RunnerPlan, VerificationReport covered |
| raw prompt leakage | 0 |
| raw artifact body leakage | 0 |
| raw log/file/provider/runtime payload leakage | 0 |
| raw approval authorization material leakage | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |
| structural counts repeatable with fresh stores | covered |

## Test Commands

```powershell
python -m pytest tests/smoke/test_local_service_demo.py -q
python examples/demo-service-flow/run_local_demo.py --store-root <temp-local-store>
python -m pytest tests -q
```

## Claim Boundary

This is a local fixture/dry-run demo. It is not Solar Pro 3 integration, DAACS
target runtime execution, original DIV live graph execution, generated app
delivery, hosted demo, production persistence, production observability, or
security certification.

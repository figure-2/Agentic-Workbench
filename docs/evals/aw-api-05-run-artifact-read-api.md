# AW-API-05 Run / Artifact Read API

## Scope

Add repository-backed read APIs for sanitized run and artifact projections:

- `GET /api/v1/runs/{run_id}`
- `GET /api/v1/runs/{run_id}/artifacts`

This step reads local runner/report/audit evidence repository rows only. It is
an evidence-backed skeleton, not a canonical run-session API. It does not query
durable approval/replay repositories, return raw artifact payloads, invoke
providers, or execute target runtimes.

## Current Implementation

- public projection version `run-read-model-public-v1`
- public projection version `artifact-read-model-public-v1`
- artifact rows come from `SQLiteRunnerReportAuditStore.list_artifacts_for_run`
- run summary is synthesized from stored artifact, runner plan, verification
  report, and audit event projection rows
- `canonical_run_record_included` is `false`
- `run_session_backend` is `not_implemented`
- approval/replay repository is marked `not_queried`

## Acceptance Results

| Gate | Result |
|---|---|
| repository-backed run summary API | covered |
| repository-backed artifact list API | covered |
| artifact payload body returned | 0 |
| raw prompt/log/file/provider/runtime body in public response | 0 |
| cross-run evidence leakage | 0 |
| fixture evidence and durable approval/replay evidence mixed | 0 |
| canonical run-session state claimed | 0 |
| corrupted evidence store | blocked |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

## Test Commands

```powershell
python -m pytest tests/integration/test_api_public_projection.py -q
python -m pytest tests -q
```

## Claim Boundary

This is a local read-model API over sanitized repository projections. It is not
a canonical run-session API, not an execution API, not durable approval
evidence, not external provider outcome, not target runtime outcome, not
generated app delivery, and not repository trust certification.

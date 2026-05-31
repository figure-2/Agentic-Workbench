# AW-API-02 SQLite Admission Repository Wiring

## Scope

Add server-side repository backend selection for fake admission API paths.
Provider/live fake admission can now use an explicit local SQLite
approval/replay repository while keeping the fixture `/api/v1/runs` path
separate.

This step does not open external provider calls, target DAACS runtime calls, or
provider SDK imports. It only proves that sanitized API wiring can reuse the
SQLite approval/replay boundary across requests.

## Current Implementation

- `create_app(admission_repository_config=...)`
- `AdmissionRepositoryProvider`
- `POST /api/v1/admissions/provider/fake`
- `POST /api/v1/admissions/live/fake`
- public projection version `approval-admission-public-v1`

The default API path still uses request-scoped memory repositories. SQLite is
selected only by explicit server-side configuration. Public responses report
the selected backend and whether it persists across requests, but never return
the database root path.

## Acceptance Results

| Gate | Result |
|---|---|
| API fake admission can select SQLite approval/replay repositories | covered |
| provider repeated nonce across API requests | blocked |
| live repeated nonce across API requests | blocked |
| corrupted SQLite store before fake provider invocation | blocked |
| corrupted SQLite store before fake runtime invocation | blocked |
| unavailable SQLite store before fake provider invocation | blocked |
| fixture `/api/v1/runs` path durable admission store writes | 0 |
| public response raw `signature_id` / `nonce` / `signed_contract_hash` | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

## Test Commands

```powershell
python -m pytest tests/integration/test_api_public_projection.py -q
python -m pytest tests -q
```

## Claim Boundary

This is local API wiring for SQLite-backed fake admission evidence. It is not a
hosted approval system, not multi-host replay protection, not external provider
outcome, not target runtime outcome, and not generated app delivery.

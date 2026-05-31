# AW-API-03 Evidence Read Model API

## Scope

Add a sanitized read-model API for persisted local evidence rows:

- runner plans
- verification reports
- audit events
- approval subject snapshots
- approval decisions
- replay nonce tombstones

This step only reads repository projections. It does not run providers, call
Solar Pro 3, execute DAACS, read environment values, or return raw bodies.

## Current Implementation

- `GET /api/v1/evidence/runs/{run_id}`
- `EvidenceRepositoryProvider`
- `EvidenceRepositoryConfig`
- public projection version `evidence-read-model-public-v1`

Runner/report/audit evidence is selected through explicit server-side SQLite
config. Approval/replay evidence reuses the admission repository provider from
the fake admission API path.

## Acceptance Results

| Gate | Result |
|---|---|
| runner plan read model exposes hash/count projection only | covered |
| verification report read model exposes hash/count projection only | covered |
| audit event read model exposes metadata/hash projection only | covered |
| approval/replay evidence exposes sanitized rows only | covered |
| cross-run evidence leakage | 0 |
| raw planned payload/log/file/provider/runtime body in public response | 0 |
| raw approval authorization material in public response | 0 |
| local DB root path in public response | 0 |
| corrupted runner/report/audit store | blocked |
| corrupted approval/replay store | blocked |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

## Test Commands

```powershell
python -m pytest tests/integration/test_api_public_projection.py -q
python -m pytest tests -q
```

## Claim Boundary

This is a local read-model API for sanitized repository evidence. It is not an
execution API, not external provider outcome, not target runtime outcome, not a
hosted evidence service, and not generated app delivery.

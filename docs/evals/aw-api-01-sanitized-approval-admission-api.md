# AW-API-01 Sanitized Approval Admission API Wiring

## Scope

Add API-facing demo paths that reuse `CanonicalApprovalPersistenceService`
before provider/live fake admission replay claim.

This step does not open external provider calls, target DAACS runtime calls, or
production approval infrastructure. It only proves that API/service wiring can
reuse the canonical approval persistence boundary and return a sanitized public
projection.

## Current Implementation

- `POST /api/v1/admissions/provider/fake`
- `POST /api/v1/admissions/live/fake`
- `run_provider_admission_demo`
- `run_live_admission_demo`
- public projection version `approval-admission-public-v1`

Both paths require `approval_lifecycle = durable` and reject fixture/synthetic
approval paths. The existing `POST /api/v1/runs` fixture endpoint remains
synthetic and separate.

The current demo uses request-scoped memory repositories. It proves API/service
wiring and public projection safety, not cross-request durable storage.

## Acceptance Results

| Gate | Result |
|---|---|
| API/demo path uses `CanonicalApprovalPersistenceService` | covered |
| provider fake admission persists approval row before replay claim | covered |
| live fake admission persists approval row before replay claim | covered |
| fixture/synthetic approval path remains separate | covered |
| public response raw `signature_id` / `nonce` / `signed_contract_hash` | 0 |
| provider fake admission external calls | 0 |
| live fake admission target runtime calls | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

## Test Commands

```powershell
python -m pytest tests/integration/test_api_public_projection.py -q
python -m pytest tests -q
```

## Claim Boundary

This is a local API/service wiring check for fake admission paths. It is not a
public approval product, not production persistence, not external provider
outcome, not target runtime outcome, not cross-request durable evidence, and
not generated app delivery.

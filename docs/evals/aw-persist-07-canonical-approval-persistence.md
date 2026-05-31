# AW-PERSIST-07 Canonical Approval Persistence Service

## Scope

Add a service boundary that persists provider/live canonical approval subject
snapshot and decision rows before durable replay claim.

This step does not expand the public API and does not open external provider
or target runtime calls. It replaces test-only pre-insert setup with an explicit
service that future API/demo paths can reuse.

## Current Implementation

- `CanonicalApprovalPersistenceService`
- `CanonicalApprovalPersistenceResult`
- `CanonicalApprovalPersistenceError`
- optional provider boundary wiring through `approval_persistence_service`
- default live registry service construction when `approval_replay_repositories`
  is supplied
- fail-closed `require_approval_persistence` gate for provider/live paths

The service persists only canonical snapshot/decision rows. Raw nonce,
signature id, signed contract hash, provider payload, prompt body, runtime
output, logs, and file body content are not stored.

## Acceptance Results

| Gate | Result |
|---|---|
| provider canonical approval row persisted before SQLite replay claim | covered |
| live canonical approval row persisted before SQLite replay claim | covered |
| persisted provider `approval_hash` matches canonical helper hash | covered |
| persisted live `approval_hash` matches canonical helper hash | covered |
| missing provider approval persistence service | blocked before fake provider invocation |
| missing live approval persistence service | blocked before fake runtime invocation |
| duplicate canonical approval row | idempotent |
| provider reused nonce after process restart simulation | blocked |
| live reused nonce after process restart simulation | blocked |
| raw nonce/signature/signed contract hash in persisted rows | 0 |
| corrupted SQLite approval store before fake runtime | blocked |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

## Test Commands

```powershell
python -m pytest tests/unit/test_provider_boundary.py -q
python -m pytest tests/unit/test_runner_provider_registry.py -q
python -m pytest tests -q
```

## Claim Boundary

This is a local service boundary for canonical approval persistence before
fake admission replay claim. It is not production persistence, not external
provider outcome, not target runtime outcome, not generated app delivery, and
not production approval trust.

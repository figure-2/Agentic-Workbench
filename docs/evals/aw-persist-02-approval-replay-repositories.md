# AW-PERSIST-02 Approval / Replay Repository Boundary

## Scope

Add hash-only repository skeletons for approval subject snapshots, approval
decision records, and replay nonce tombstones.

This eval includes the AW-NEXT-14 safety slice for file-backed replay storage:
atomic replace writes, corrupted/partial file fail-closed behavior, and path
traversal rejection.

## Current Implementation

- `ApprovalRepository` / `InMemoryApprovalRepository`
- `ReplayNonceRepository` / `InMemoryReplayNonceRepository`
- `FileBackedReplayNonceRepository`
- canonical replay scope helper:
  `aw.approval.v1/{approval_type}/{run_id}/{subject_hash}`
- hash-only nonce helper that does not use public-payload sanitization
- compatibility update for `DurableReplayStore` export/import rows using
  `scope_canonical`
- provider/live approval signatures are bound to the same canonical subject
  scope used by replay claims
- file-backed durable replay rows must include explicit approval/run metadata;
  missing/defaulted durable rows fail closed

## Acceptance Results

| Gate | Result |
|---|---|
| `python -m pytest tests -q` | 250 passed |
| immutable approval subject snapshot stores sanitized projection only | covered |
| approval record stores `subject_hash`, `approval_hash`, `scope_canonical` refs only | covered |
| raw nonce/signature/verifier/key/policy identity field storage count | 0 in tested repository rows |
| supplied `scope_canonical` must match subject hash | covered |
| replay row scope must match `approval_type` and `run_id` | covered |
| canonical replay scope rejects unsafe public `run_id` | covered |
| file-backed durable row missing metadata blocked | covered |
| same canonical scope replay blocked | covered |
| process restart simulation preserves replay tombstone | covered |
| cross-scope nonce policy explicit | same nonce allowed when subject hash changes |
| signed provider/live approval cannot authorize a different subject | covered |
| file-backed corrupted JSON blocked | covered |
| file-backed partial row blocked | covered |
| file-backed path traversal blocked | covered |
| file-backed atomic write failure preserves existing tombstone | covered |
| provider/live file-backed replay integration | covered |
| Solar Pro 3 live call | 0 |
| DAACS live call | 0 |

## Test Commands

```powershell
python -m compileall packages tests
python -m pytest tests/unit/test_approval_repositories.py tests/unit/test_approval_security.py tests/unit/test_provider_boundary.py tests/unit/test_runner_provider_registry.py -q
python -m pytest tests -q
```

## Non-Current Claims

- DB-backed approval storage is not implemented.
- Production cryptographic signing is not implemented.
- Production multi-host replay prevention is not implemented.
- Real DAACS live execution is not implemented.
- Solar Pro 3 live provider calls are not implemented.

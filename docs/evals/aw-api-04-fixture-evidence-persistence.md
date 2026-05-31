# AW-API-04 Fixture Evidence Persistence Write Path

## Scope

Add a local write path that persists `/api/v1/runs` fixture evidence into the
configured runner/report/audit repository:

- fixture-derived dry-run `RunnerPlan` projection
- fixture `VerificationReport` projection
- workflow `AuditEvent` projections
- source artifact projection rows for linkage

This step writes sanitized local evidence rows only when an explicit
server-side evidence repository is configured. It does not write durable
approval/replay rows from the fixture run path.

## Current Implementation

- `persist_fixture_run_evidence`
- public projection version `fixture-evidence-persistence-public-v1`
- `/api/v1/runs` response field `data.evidence_persistence`
- SQLite runner/report/audit store selected through `EvidenceRepositoryConfig`
- read-back verification through `GET /api/v1/evidence/runs/{run_id}`

When no evidence repository is configured, the persistence result is `skipped`.
When the repository is corrupted or unavailable, the persistence result is
`blocked` and fixture execution remains raw-output-free.

## Acceptance Results

| Gate | Result |
|---|---|
| `/api/v1/runs` fixture path can persist sanitized evidence rows | covered |
| persisted runner plan exposes hash/count/role projection only | covered |
| persisted verification report exposes counts and hashes only | covered |
| persisted audit events expose metadata and hashes only | covered |
| read-model API can verify the saved evidence chain by `run_id` | covered |
| fixture path writes durable approval/replay rows | 0 |
| raw prompt, raw log, raw file body, provider/runtime body in public response | 0 |
| local repository root path in public response | 0 |
| corrupted evidence store | blocked |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

## Test Commands

```powershell
python -m pytest tests/integration/test_api_public_projection.py -q
python -m pytest tests -q
```

## Claim Boundary

This is a local fixture evidence write path for sanitized repository
projections. It is not an execution API, not external provider outcome, not
target runtime outcome, not generated app delivery, and not repository trust
certification.

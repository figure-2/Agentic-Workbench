# AW-PERSIST-05 SQLite Approval / Replay Adapter

## Scope

Add a separate SQLite adapter skeleton for sanitized approval subject snapshots,
approval decision rows, and replay nonce tombstones.

The adapter intentionally stays separate from the runner/report/audit SQLite
store. The goal is to persist admission evidence as hash/count/linkage rows
without raw authorization material, not to open target runtime calls.

## Current Implementation

- `SQLiteApprovalReplayStore`
- `SQLiteApprovalRepository`
- `SQLiteReplayNonceRepository`
- separate SQLite file default: `approval_replay.sqlite3`
- schema migration version: `1`
- tables:
  - `approval_subject_snapshots`
  - `approvals`
  - `replay_nonces`
- unique constraints:
  - `approval_subject_snapshots.snapshot_hash`
  - `approvals.approval_hash`
  - `replay_nonces(scope_canonical, nonce_hash)`
- fail-closed schema validation for missing tables, wrong columns, missing
  primary keys, missing unique constraints, missing check constraints, and
  missing foreign-key contract text

## Acceptance Results

| Gate | Result |
|---|---|
| focused SQLite approval/replay tests | 15 passed |
| full local pytest baseline | 312 passed |
| approval subject snapshot raw authorization material storage | 0 findings |
| approval decision raw authorization material storage | 0 findings |
| replay nonce raw value storage | 0 findings |
| direct non-hash record insertion | blocked |
| `approval_hash` unique constraint | covered |
| `snapshot_hash` unique constraint | covered |
| `(scope_canonical, nonce_hash)` replay uniqueness | covered |
| reused nonce after store restart | blocked |
| fixture/synthetic approval row in SQLite durable adapter | blocked |
| tampered approval scope and snapshot linkage | blocked |
| replay tombstone with mismatched approval subject scope | blocked |
| mixed runner/report/audit and approval/replay SQLite schema file | blocked |
| corrupted, partial, wrong-column, and wrong-contract schema | blocked |
| relaxed approval/replay CHECK constraint schema | blocked |
| transaction rollback partial approval/replay rows | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

## Test Commands

```powershell
python -m pytest tests/unit/test_sqlite_approval_replay_repositories.py -q
python -m pytest tests/unit/test_sqlite_runner_report_audit_repositories.py -q
python -m pytest tests -q
```

## Claim Boundary

This is a local SQLite adapter skeleton for sanitized approval/replay
projection rows. It does not add production persistence, external provider
outcome, target runtime outcome, generated app delivery, hosted status, or
production-grade approval trust. Runtime/provider call counts are carried
forward from the full local regression suite; this adapter itself has no
runtime/provider call path.

# AW-PERSIST-04 SQLite Runner / Report / Audit Adapter

## Scope

Add a SQLite adapter skeleton for sanitized runner plan, verification report,
audit event, and source artifact projection rows. The adapter implements the
current repository record shape and migration `v1` only.

This step does not add production persistence, hosted deployment, provider
calls, target runtime execution, generated app delivery, or external benchmark
evidence.

## Current Implementation

- `SQLiteRunnerReportAuditStore`
  - owns schema migration `v1`, connection health checks, transactions, and
    source artifact rows used for linkage checks.
  - blocks corrupted, unavailable, partial, or path-traversal database setup.
- `SQLiteRunnerPlanRepository`
  - stores `RunnerPlanRecord` projection rows only.
  - enforces unique `plan_hash`.
- `SQLiteVerificationReportRepository`
  - stores `VerificationReportRecord` projection rows only.
  - enforces unique `report_hash` and runner plan linkage.
- `SQLiteAuditEventRepository`
  - stores `AuditEventRecord` projection rows only.
  - enforces unique `audit_event_id`, source artifact linkage, report linkage,
    and audit plan/report chain consistency.
- schema validation checks expected table names, columns, primary keys,
  explicit indexes, migration version, and unique `plan_hash` / `report_hash`
  indexes before trusting an existing database file.

## Acceptance Results

| Gate | Result |
|---|---|
| DB row raw planned payload/body storage | 0 findings |
| DB row raw log/file body storage | 0 findings |
| DB row provider/runtime payload storage | 0 findings |
| `plan_hash` unique constraint | covered |
| `report_hash` unique constraint | covered |
| `audit_event_id` unique constraint | covered |
| run/source artifact/plan/report linkage | covered |
| audit report-to-plan chain consistency | covered |
| cross-run artifact/plan/report/audit linkage | blocked |
| transaction rollback leaves partial rows | 0 rows |
| corrupted or unavailable DB | blocked |
| partial or wrong-column schema | blocked |
| missing primary key schema | blocked |
| path traversal DB path | blocked |
| target runtime calls | 0 |

## Quantitative Results

| Metric | Value |
|---|---:|
| SQLite runner/report/audit tests | 16 |
| Existing runner/report/audit repository tests | 17 |
| SQLite schema migration version | 1 |
| SQLite projection tables | 4 |
| SQLite explicit indexes | 5 |
| SQLite unique constraint classes | 3 |
| Forbidden public key findings in DB rows | 0 |
| Forbidden claim findings in DB rows | 0 |
| Partial rows after rollback fixture | 0 |

## Test Commands

```powershell
python -m pytest tests/unit/test_sqlite_runner_report_audit_repositories.py -q
python -m pytest tests/unit/test_runner_report_audit_repositories.py tests/unit/test_sqlite_runner_report_audit_repositories.py -q
python -m pytest tests -q
```

## Non-Current Claims

- This is not a production database layer.
- This does not add target runtime execution or external provider outcome.
- This does not persist raw planned actions, raw logs, raw file bodies,
  provider/runtime payloads, or approval authorization material.
- This does not prove generated app delivery or production readiness.

## Next Step

The next persistence slice should extend DB-backed adapters only after the
approval/replay contract is mapped to the same migration discipline. API usage
of the SQLite adapter should remain behind sanitized projection boundaries.

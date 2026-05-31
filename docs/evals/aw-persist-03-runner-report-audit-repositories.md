# AW-PERSIST-03 Runner / Report / Audit Repository Boundary

## Scope

Add repository skeletons for runner plans, verification reports, and audit
events. The repositories store durable projections only: hashes, counts,
status, safe labels, timestamps, and run/report linkage.

This step does not add DB persistence, live runner execution, provider calls,
CLI execution, package installs, server starts, or generated source artifacts.

## Current Implementation

- `RunnerPlanRepository` / `InMemoryRunnerPlanRepository`
  - stores `plan_id`, `plan_hash`, action counts, role counts, manifest count,
    approval count, side-effect status, and payload hash.
  - does not store `planned_actions`, approval reason text, artifact manifest
    body, provider payloads, runtime payloads, commands, or file bodies.
- `VerificationReportRepository` / `InMemoryVerificationReportRepository`
  - stores `report_hash`, pass/fail status, check/error/file/metric counts,
    failed check count, metric key labels, and hashes for checks/errors/files.
  - does not store raw errors, raw logs, stack traces, generated file bodies, or
    generated file paths as row fields.
- `AuditEventRepository` / `InMemoryAuditEventRepository`
  - stores event metadata, safe labels, message hash, payload hash, payload
    field count, and optional plan/report linkage hashes.
  - does not store provider/runtime payloads, stdout/stderr, command text,
    tool output, approval authorization material, nonce, or signature ids.
- `validate_runner_report_audit_linkage`
  - rejects cross-run runner/report/audit rows and mismatched plan/report links.
  - verifies source artifact references against artifact repository rows when
    artifact records are supplied.
- public exposure denylist now includes runtime payload, runtime response,
  stdout/stderr, command, and tool output fields.
- untrusted mode/source labels are reduced to safe fallbacks, and plan/report
  linkage hash references reject non-contract-hash input.
- runner plan `plan_hash`, `implementation_brief_hash`, and `build_spec_hash`
  reject non-contract-hash input before repository rows are created.

## Acceptance Results

| Gate | Result |
|---|---|
| RunnerPlan raw planned payload/body storage | 0 in repository rows |
| VerificationReport raw log/file body storage | 0 in repository rows |
| AuditEvent provider/runtime raw payload storage | 0 in repository rows |
| run_id/artifact/report linkage | covered with artifact repository rows |
| public repository projection forbidden key findings | 0 |
| public repository projection forbidden claim findings | 0 |
| Solar Pro 3 live call | 0 |
| DAACS live call | 0 |

## Quantitative Results

| Metric | Value |
|---|---:|
| Runner/report/audit repository tests | 16 |
| New repository protocols | 3 |
| New in-memory repository implementations | 3 |
| New projection record types | 3 |
| New linkage validation helper | 1 |
| Extended forbidden public key classes | 9 |
| Focused repository regression result | 127 / 127 passed |
| Full local pytest result | 280 / 280 passed |

## Test Commands

```powershell
python -m compileall packages apps tests
python -m pytest tests/unit/test_repositories.py tests/unit/test_approval_repositories.py tests/unit/test_runner_report_audit_repositories.py tests/unit/test_runner_provider_registry.py tests/unit/test_public_projection.py tests/unit/test_claims_and_evidence.py -q
python -m pytest tests -q
```

## Non-Current Claims

- DB-backed runner/report/audit persistence is not implemented.
- Raw runner, report, provider, runtime, log, or file bodies are not durable
  repository fields.
- Live runner execution and external provider outcome remain out of current
  scope.
- Repository projections do not prove generated app delivery or production
  readiness.

## Follow-Up

`AW-PERSIST-04` follows this boundary with a SQLite adapter skeleton for the
same sanitized projection rows, migration versioning, unique constraints, and
transaction rollback behavior. Target runtime execution remains closed.

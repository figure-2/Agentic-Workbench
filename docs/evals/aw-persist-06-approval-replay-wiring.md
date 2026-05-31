# AW-PERSIST-06 Approval / Replay Repository Factory Wiring

## Scope

Add an explicit approval/replay repository factory and wire fake provider/live
admission gates to an optional SQLite-backed replay path.

This step does not expand the public API and does not open external provider
or target runtime calls. It only proves that the existing fake admission
boundaries can choose the SQLite approval/replay adapter and fail closed before
fake provider/runtime invocation.

## Current Implementation

- `ApprovalReplayRepositoryConfig`
- `build_approval_replay_repositories`
- `RepositoryReplayStore`
- optional `default_runner_provider_registry(approval_replay_repositories=...)`
- canonical provider/live approval record helpers used by SQLite wiring tests

The SQLite replay repository remains foreign-key bound to canonical approval
rows. Fake admission gates therefore require a pre-persisted approval subject
snapshot and approval decision row before replay claim. Admission does not
synthesize durable approval rows.

## Acceptance Results

| Gate | Result |
|---|---|
| repository factory memory backend | covered |
| repository factory file replay backend | covered |
| repository factory SQLite backend | covered |
| provider fake admission can use SQLite replay repository | covered |
| live fake admission can use SQLite replay repository through registry wiring | covered |
| canonical approval row precondition before replay claim | covered |
| missing canonical approval row before replay claim | blocked |
| provider reused nonce after process restart simulation | blocked |
| live reused nonce after process restart simulation | blocked |
| unavailable SQLite repository root | blocked |
| corrupted SQLite replay DB before fake provider invocation | blocked |
| corrupted SQLite replay DB before fake runtime invocation | blocked |
| fixture/synthetic approval row in SQLite durable adapter | blocked |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

## Test Commands

```powershell
python -m pytest tests/unit/test_approval_replay_repository_factory.py -q
python -m pytest tests/unit/test_provider_boundary.py -q
python -m pytest tests/unit/test_runner_provider_registry.py -q
python -m pytest tests -q
```

## Claim Boundary

This is optional local wiring for fake admission gates and the SQLite
approval/replay adapter skeleton. It is not production persistence, not an
external provider outcome, not target runtime outcome, not generated app
delivery, and not production approval trust.

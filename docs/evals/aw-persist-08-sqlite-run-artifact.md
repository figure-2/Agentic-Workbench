# AW-PERSIST-08 SQLite Run / Artifact Repository

## Scope

Add a separate SQLite adapter skeleton for canonical `RunSessionRecord` and
`ArtifactRecord` projections.

This step stores sanitized run state and artifact metadata only. It does not
store raw prompts, artifact payload bodies, runner/report/audit evidence rows,
approval/replay evidence rows, provider payloads, logs, or generated file
bodies.

## Current Implementation

- `SQLiteRunArtifactStore`
- `SQLiteRunSessionRepository`
- `SQLiteArtifactRepository`
- `RunArtifactRepositoryConfig`
- `RunArtifactRepositoryProvider`
- `/api/v1/runs` optional canonical run/artifact persistence
- `GET /api/v1/runs/{run_id}` canonical run read model
- `GET /api/v1/runs/{run_id}/artifacts` canonical artifact read model

The canonical run/artifact SQLite file is separate from:

- runner/report/audit evidence store
- approval/replay evidence store

## Acceptance Results

| Gate | Result |
|---|---|
| `/api/v1/runs` stores sanitized `RunSessionRecord` when configured | covered |
| canonical run read API returns `prompt_contract_hash`, `stage`, `status`, `idea_summary` | covered |
| raw prompt stored in canonical DB rows | 0 |
| artifact payload body stored in canonical DB rows | 0 |
| evidence DB mixed into canonical read API | 0 |
| approval/replay DB mixed into canonical read API | 0 |
| corrupted canonical store | blocked |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

## Test Commands

```powershell
python -m pytest tests/unit/test_sqlite_run_artifact_repositories.py -q
python -m pytest tests/integration/test_api_public_projection.py -q
python -m pytest tests -q
```

## Claim Boundary

This is local projection persistence for canonical run and artifact read models.
It is not generated application delivery, target runtime outcome, external
provider outcome, hosted persistence, or repository trust certification.

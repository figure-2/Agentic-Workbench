import json
import sqlite3

import pytest

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys
from packages.core.repositories import RunSessionRecord, ArtifactRecord
from packages.core.schemas import Artifact, ArtifactKind, IdeaBrief, WorkflowSession, WorkflowStage
from packages.core.sqlite_repositories import (
    RUN_ARTIFACT_EXPECTED_COLUMNS,
    SQLiteApprovalReplayStore,
    SQLiteRepositoryUnavailableError,
    SQLiteRunArtifactStore,
    SQLiteRunnerReportAuditStore,
)


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def _session() -> WorkflowSession:
    session = WorkflowSession.create(
        IdeaBrief(
            raw_prompt="Build canonical run store with PERSIST08_RAW_PROMPT",
            target_user="persist08-owner@example.com",
            product_type="canonical run state",
            constraints=["never store PERSIST08_CONSTRAINT_BODY"],
            success_criteria=["read prompt contract hash"],
        )
    )
    session.move_to(WorkflowStage.COMPLETE)
    session.add_artifact(
        Artifact.create(
            run_id=session.id,
            kind=ArtifactKind.PRD_PACKAGE,
            name="prd-package.json",
            payload={
                "summary": "canonical projection only",
                "raw_content": "PERSIST08_RAW_ARTIFACT_BODY",
                "safe_nested": {
                    "full_prompt": "PERSIST08_FULL_PROMPT",
                    "safe_text": "PERSIST08_SAFE_PAYLOAD_BODY",
                },
            },
        )
    )
    session.add_artifact(
        Artifact.create(
            run_id=session.id,
            kind=ArtifactKind.BUILD_SPEC,
            name="build-spec.json",
            payload={
                "api_spec": {"endpoints": [{"path": "/api/v1/runs"}]},
                "file_body": "PERSIST08_FILE_BODY",
            },
        )
    )
    return session


def _sqlite_rows(path):
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = {}
        for table in ("run_sessions", "artifacts"):
            rows[table] = [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]
        return rows


def test_sqlite_run_artifact_schema_is_idempotent_and_round_trips_canonical_rows(tmp_path):
    store = SQLiteRunArtifactStore(root=tmp_path)
    same_store = SQLiteRunArtifactStore(root=tmp_path)
    session = _session()

    run_record, artifact_records = same_store.save_session_with_artifacts(session)
    loaded_run = same_store.run_sessions().get(session.id)
    loaded_artifacts = same_store.artifacts().list_for_run(session.id)

    assert loaded_run is not None
    assert loaded_run.to_dict() == run_record.to_dict()
    assert [record.to_dict() for record in loaded_artifacts] == [
        record.to_dict() for record in artifact_records
    ]
    assert loaded_run.prompt_contract_hash
    assert loaded_run.stage == "complete"
    assert loaded_run.status == "complete"
    assert set(RUN_ARTIFACT_EXPECTED_COLUMNS) == {"schema_migrations", "run_sessions", "artifacts"}
    assert store.path.name == "agentic_workbench_runs.sqlite3"


def test_sqlite_run_artifact_rows_do_not_store_raw_prompt_or_artifact_payload_body(tmp_path):
    store = SQLiteRunArtifactStore(root=tmp_path)
    session = _session()
    run_record, artifact_records = store.save_session_with_artifacts(session)
    rows = _sqlite_rows(store.path)
    serialized = _serialized(rows)

    assert rows["run_sessions"][0]["prompt_contract_hash"] == run_record.prompt_contract_hash
    assert len(rows["artifacts"]) == len(artifact_records)
    for sentinel in (
        "raw_prompt",
        "PERSIST08_RAW_PROMPT",
        "PERSIST08_CONSTRAINT_BODY",
        "persist08-owner@example.com",
        "PERSIST08_RAW_ARTIFACT_BODY",
        "PERSIST08_FULL_PROMPT",
        "PERSIST08_SAFE_PAYLOAD_BODY",
        "PERSIST08_FILE_BODY",
    ):
        assert sentinel not in serialized
    assert find_forbidden_public_keys(rows) == []
    assert find_forbidden_claims(serialized) == []


def test_sqlite_run_artifact_cross_run_artifacts_are_blocked_and_transaction_rolls_back(tmp_path):
    store = SQLiteRunArtifactStore(root=tmp_path)
    session = _session()
    run_record = RunSessionRecord(
        run_id=session.id,
        stage="complete",
        status="complete",
        prompt_contract_hash="a" * 64,
        idea_summary="canonical run state",
        created_at="2026-06-01T00:00:00+00:00",
        updated_at="2026-06-01T00:00:00+00:00",
    )
    bad_artifact = ArtifactRecord(
        artifact_id="artifact-bad-link",
        run_id="run-other",
        kind="build_spec",
        name="build-spec.json",
        path=None,
        content_hash="b" * 64,
        payload_field_count=0,
        summary="canonical artifact projection",
        created_at="2026-06-01T00:00:00+00:00",
    )

    with pytest.raises(ValueError, match="artifact repository"):
        store.save_records_atomically(run_session=run_record, artifacts=[bad_artifact])

    assert store.run_sessions().get(session.id) is None
    assert store.artifacts().list_for_run("run-other") == []


def test_sqlite_run_artifact_store_blocks_corrupted_unavailable_and_mixed_schema_files(tmp_path):
    corrupt_root = tmp_path / "corrupt"
    corrupt_root.mkdir()
    (corrupt_root / "agentic_workbench_runs.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteRunArtifactStore(root=corrupt_root)

    unavailable_root = tmp_path / "file-root"
    unavailable_root.write_text("not a directory", encoding="utf-8")
    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteRunArtifactStore(root=unavailable_root)

    mixed_root = tmp_path / "mixed"
    SQLiteRunnerReportAuditStore(root=mixed_root, relative_path="shared.sqlite3")
    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteRunArtifactStore(root=mixed_root, relative_path="shared.sqlite3")

    approval_root = tmp_path / "approval-first"
    SQLiteApprovalReplayStore(root=approval_root, relative_path="shared.sqlite3")
    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteRunArtifactStore(root=approval_root, relative_path="shared.sqlite3")


def test_sqlite_run_artifact_store_rejects_path_traversal_path(tmp_path):
    with pytest.raises(ValueError):
        SQLiteRunArtifactStore(root=tmp_path, relative_path="../agentic_workbench_runs.sqlite3")

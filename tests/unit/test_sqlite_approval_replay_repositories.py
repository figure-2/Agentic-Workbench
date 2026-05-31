from dataclasses import replace
import json
import sqlite3

import pytest

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys
from packages.core.repositories import (
    ReplayNonceReplayError,
    approval_decision_record,
    approval_subject_snapshot_record,
    replay_nonce_record,
)
from packages.core.sqlite_repositories import (
    APPROVAL_REPLAY_EXPECTED_COLUMNS,
    SQLiteApprovalReplayStore,
    SQLiteRepositoryUnavailableError,
)


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def _subject(**overrides):
    subject = {
        "plan_hash": "a" * 64,
        "state_hash": "b" * 64,
        "workspace_ref": "runs/run-persist-05",
        "allowed_operations": ["fake_runtime"],
        "signature_id": "sig-should-not-store",
        "signed_contract_hash": "c" * 64,
        "nonce": "nonce-should-not-store",
        "verifier_id": "verifier-should-not-store",
        "key_id": "key-should-not-store",
        "key_identity_id": "key-identity-should-not-store",
        "raw_prompt": "PERSIST05_RAW_PROMPT",
        "raw_content": "PERSIST05_RAW_FILE_BODY",
        "messages": ["PERSIST05_RAW_MESSAGE"],
    }
    subject.update(overrides)
    return subject


def _snapshot_record(**overrides):
    data = {
        "approval_type": "provider_approval",
        "run_id": "run-persist-05",
        "subject_kind": "provider_request",
        "subject": _subject(),
        "subject_schema_version": "provider-approval-subject-v1",
        "source_artifact_ids": (),
        "sanitized_summary": "provider request approval summary",
        "created_at": "2026-05-31T00:00:00+00:00",
    }
    data.update(overrides)
    return approval_subject_snapshot_record(**data)


def _approval_record(snapshot, **overrides):
    data = {
        "approval_id": "approval-persist-05",
        "snapshot": snapshot,
        "decision": "approved",
        "approved_by_ref": "local-user-ref",
        "approver_role": "local-user",
        "approved_at": "2026-05-31T00:01:00+00:00",
        "expires_at": "2026-06-01T00:01:00+00:00",
        "policy_id_ref": "policy-local-fake",
        "key_identity_ref": "key-identity-local-fake",
        "audit_log_id": "audit-persist-05",
        "created_at": "2026-05-31T00:01:01+00:00",
    }
    data.update(overrides)
    return approval_decision_record(**data)


def _replay_record(approval, **overrides):
    data = {
        "scope_canonical": approval.scope_canonical,
        "nonce": "nonce-replay-secret",
        "approval_hash": approval.approval_hash,
        "run_id": approval.run_id,
        "approval_type": approval.approval_type,
        "expires_at": "2026-06-01T00:01:00+00:00",
        "claimed_at": "2026-05-31T00:02:00+00:00",
    }
    data.update(overrides)
    return replay_nonce_record(**data)


def _sqlite_rows(path):
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = {}
        for table in ("approval_subject_snapshots", "approvals", "replay_nonces"):
            rows[table] = [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]
        return rows


def _row_counts(path):
    with sqlite3.connect(path) as connection:
        return {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in ("approval_subject_snapshots", "approvals", "replay_nonces")
        }


def _persist_approval_chain(store: SQLiteApprovalReplayStore):
    snapshot = _snapshot_record()
    approval = _approval_record(snapshot)
    store.save_records_atomically(approval_subject_snapshots=[snapshot], approvals=[approval])
    return snapshot, approval


def test_sqlite_approval_replay_schema_is_idempotent_and_round_trips_hash_rows(tmp_path):
    store = SQLiteApprovalReplayStore(root=tmp_path)
    same_store = SQLiteApprovalReplayStore(root=tmp_path)
    snapshot, approval = _persist_approval_chain(same_store)
    replay = same_store.replay_nonces().claim(
        scope_canonical=snapshot.scope_canonical,
        nonce="nonce-round-trip-secret",
        approval_hash=approval.approval_hash,
        run_id=snapshot.run_id,
        approval_type=snapshot.approval_type,
        expires_at="2026-06-01T00:01:00+00:00",
        claimed_at="2026-05-31T00:02:00+00:00",
    )

    assert store.path == same_store.path
    assert same_store.approvals().get_snapshot(snapshot.subject_snapshot_id).to_dict() == snapshot.to_dict()
    assert same_store.approvals().get_approval(approval.approval_id).to_dict() == approval.to_dict()
    assert [record.to_dict() for record in same_store.replay_nonces().list_records()] == [replay.to_dict()]


def test_sqlite_approval_replay_rows_do_not_store_raw_authorization_material(tmp_path):
    store = SQLiteApprovalReplayStore(root=tmp_path)
    snapshot, approval = _persist_approval_chain(store)
    store.replay_nonces().claim(
        scope_canonical=snapshot.scope_canonical,
        nonce="nonce-replay-secret",
        approval_hash=approval.approval_hash,
        run_id=snapshot.run_id,
        approval_type=snapshot.approval_type,
        expires_at="2026-06-01T00:01:00+00:00",
    )
    rows = _sqlite_rows(store.path)
    serialized = _serialized(rows)

    for sentinel in (
        "sig-should-not-store",
        "nonce-should-not-store",
        "nonce-replay-secret",
        "signed_contract_hash",
        "verifier-should-not-store",
        "key-should-not-store",
        "key-identity-should-not-store",
        "PERSIST05_RAW_PROMPT",
        "PERSIST05_RAW_FILE_BODY",
        "PERSIST05_RAW_MESSAGE",
    ):
        assert sentinel not in serialized
    assert find_forbidden_public_keys(rows) == []
    assert find_forbidden_claims(serialized) == []


def test_sqlite_approval_replay_rejects_raw_authorization_material_in_text_fields(tmp_path):
    store = SQLiteApprovalReplayStore(root=tmp_path)
    unsafe_snapshot = _snapshot_record(sanitized_summary="contains nonce-secret-value")

    with pytest.raises(ValueError, match="authorization material"):
        store.save_records_atomically(approval_subject_snapshots=[unsafe_snapshot])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 0,
        "approvals": 0,
        "replay_nonces": 0,
    }

    snapshot = _snapshot_record()
    unsafe_approval = _approval_record(snapshot, audit_log_id="signed_contract_hash=abc")
    with pytest.raises(ValueError, match="authorization material"):
        store.save_records_atomically(approval_subject_snapshots=[snapshot], approvals=[unsafe_approval])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 0,
        "approvals": 0,
        "replay_nonces": 0,
    }

    pem_approval = _approval_record(snapshot, key_identity_ref="-----BEGIN PRIVATE KEY-----")
    with pytest.raises(ValueError, match="authorization material"):
        store.save_records_atomically(approval_subject_snapshots=[snapshot], approvals=[pem_approval])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 0,
        "approvals": 0,
        "replay_nonces": 0,
    }

    date_field_pem_approval = _approval_record(snapshot, approved_at="-----BEGIN PRIVATE KEY-----")
    with pytest.raises(ValueError, match="authorization material"):
        store.save_records_atomically(approval_subject_snapshots=[snapshot], approvals=[date_field_pem_approval])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 0,
        "approvals": 0,
        "replay_nonces": 0,
    }

    redaction_bypass_approval = _approval_record(snapshot, approved_at="token=abc123")
    with pytest.raises(ValueError, match="authorization material"):
        store.save_records_atomically(approval_subject_snapshots=[snapshot], approvals=[redaction_bypass_approval])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 0,
        "approvals": 0,
        "replay_nonces": 0,
    }


def test_sqlite_approval_replay_rejects_fixture_or_synthetic_durable_rows(tmp_path):
    store = SQLiteApprovalReplayStore(root=tmp_path)
    snapshot = _snapshot_record(
        approval_type="spec_approval",
        lifecycle_class="synthetic",
        subject_kind="implementation_brief",
        subject_schema_version="spec-approval-subject-v1",
    )

    with pytest.raises(ValueError, match="fixture/synthetic"):
        store.save_records_atomically(approval_subject_snapshots=[snapshot])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 0,
        "approvals": 0,
        "replay_nonces": 0,
    }


def test_sqlite_approval_replay_blocks_tampered_scope_and_snapshot_linkage(tmp_path):
    store = SQLiteApprovalReplayStore(root=tmp_path)
    snapshot = _snapshot_record()
    tampered_scope = "aw.approval.v1/provider_approval/run-persist-05/" + ("d" * 64)

    with pytest.raises(ValueError, match="scope"):
        store.save_records_atomically(approval_subject_snapshots=[replace(snapshot, scope_canonical=tampered_scope)])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 0,
        "approvals": 0,
        "replay_nonces": 0,
    }

    snapshot, approval = _persist_approval_chain(store)
    tampered_approval = replace(approval, subject_schema_version="tampered-subject-schema")
    with pytest.raises(ValueError, match="subject schema"):
        store.save_records_atomically(approvals=[tampered_approval])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 1,
        "approvals": 1,
        "replay_nonces": 0,
    }


def test_sqlite_approval_replay_blocks_non_hash_values_on_direct_record_insert(tmp_path):
    store = SQLiteApprovalReplayStore(root=tmp_path)
    snapshot = _snapshot_record()

    with pytest.raises(ValueError, match="subject_hash"):
        store.save_records_atomically(approval_subject_snapshots=[replace(snapshot, subject_hash="raw-subject")])
    with pytest.raises(ValueError, match="snapshot_hash"):
        store.save_records_atomically(approval_subject_snapshots=[replace(snapshot, snapshot_hash="raw-snapshot")])
    with pytest.raises(ValueError, match="subject_hashes"):
        store.save_records_atomically(
            approval_subject_snapshots=[replace(snapshot, subject_hashes={"subject": "raw-subject"})]
        )
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 0,
        "approvals": 0,
        "replay_nonces": 0,
    }

    snapshot, approval = _persist_approval_chain(store)
    replay = _replay_record(approval)
    with pytest.raises(ValueError, match="approval_hash"):
        store.save_records_atomically(approvals=[replace(approval, approval_id="approval-bad-hash", approval_hash="raw")])
    with pytest.raises(ValueError, match="nonce_hash"):
        store.save_records_atomically(replay_nonces=[replace(replay, nonce_hash="nonce-raw-secret")])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 1,
        "approvals": 1,
        "replay_nonces": 0,
    }


def test_sqlite_approval_replay_unique_constraints_block_duplicate_snapshot_approval_and_replay(tmp_path):
    store = SQLiteApprovalReplayStore(root=tmp_path)
    snapshot, approval = _persist_approval_chain(store)

    with pytest.raises(ValueError, match="approval subject snapshot"):
        store.save_records_atomically(approval_subject_snapshots=[snapshot])
    with pytest.raises(ValueError, match="approval subject snapshot"):
        store.save_records_atomically(
            approval_subject_snapshots=[replace(snapshot, subject_snapshot_id="snapshot-duplicate-id")]
        )
    with pytest.raises(ValueError, match="approval repository"):
        store.save_records_atomically(approvals=[approval])
    with pytest.raises(ValueError, match="approval repository"):
        store.save_records_atomically(approvals=[replace(approval, approval_id="approval-duplicate-id")])

    first = store.replay_nonces().claim(
        scope_canonical=snapshot.scope_canonical,
        nonce="nonce-reused-secret",
        approval_hash=approval.approval_hash,
        run_id=snapshot.run_id,
        approval_type=snapshot.approval_type,
        expires_at="2026-06-01T00:01:00+00:00",
    )
    with pytest.raises(ReplayNonceReplayError):
        store.save_records_atomically(replay_nonces=[first])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 1,
        "approvals": 1,
        "replay_nonces": 1,
    }


def test_sqlite_approval_replay_blocks_reused_nonce_after_process_restart(tmp_path):
    store = SQLiteApprovalReplayStore(root=tmp_path)
    snapshot, approval = _persist_approval_chain(store)
    store.replay_nonces().claim(
        scope_canonical=snapshot.scope_canonical,
        nonce="nonce-restart-secret",
        approval_hash=approval.approval_hash,
        run_id=snapshot.run_id,
        approval_type=snapshot.approval_type,
        expires_at="2026-06-01T00:01:00+00:00",
    )
    restarted = SQLiteApprovalReplayStore(root=tmp_path)

    with pytest.raises(ReplayNonceReplayError):
        restarted.replay_nonces().claim(
            scope_canonical=snapshot.scope_canonical,
            nonce="nonce-restart-secret",
            approval_hash=approval.approval_hash,
            run_id=snapshot.run_id,
            approval_type=snapshot.approval_type,
            expires_at="2026-06-01T00:01:00+00:00",
        )


def test_sqlite_approval_replay_blocks_replay_scope_from_different_approval_subject(tmp_path):
    store = SQLiteApprovalReplayStore(root=tmp_path)
    first_snapshot, first_approval = _persist_approval_chain(store)
    second_snapshot = _snapshot_record(
        subject=_subject(plan_hash="d" * 64),
        sanitized_summary="second provider request approval summary",
    )
    second_approval = _approval_record(
        second_snapshot,
        approval_id="approval-persist-05-second",
        audit_log_id="audit-persist-05-second",
    )
    assert second_snapshot.scope_canonical != first_snapshot.scope_canonical
    store.save_records_atomically(approval_subject_snapshots=[second_snapshot], approvals=[second_approval])

    with pytest.raises(ValueError, match="approval_hash scope"):
        store.replay_nonces().claim(
            scope_canonical=second_snapshot.scope_canonical,
            nonce="nonce-cross-subject-secret",
            approval_hash=first_approval.approval_hash,
            run_id=second_snapshot.run_id,
            approval_type=second_snapshot.approval_type,
            expires_at="2026-06-01T00:01:00+00:00",
        )
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 2,
        "approvals": 2,
        "replay_nonces": 0,
    }


def test_sqlite_approval_replay_transaction_rollback_leaves_no_partial_rows(tmp_path):
    store = SQLiteApprovalReplayStore(root=tmp_path)
    snapshot = _snapshot_record()
    approval = _approval_record(snapshot)

    with pytest.raises(ValueError, match="approval repository"):
        store.save_records_atomically(approval_subject_snapshots=[snapshot], approvals=[approval, approval])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 0,
        "approvals": 0,
        "replay_nonces": 0,
    }

    store.save_records_atomically(approval_subject_snapshots=[snapshot], approvals=[approval])
    replay = _replay_record(approval)
    with pytest.raises(ReplayNonceReplayError):
        store.save_records_atomically(replay_nonces=[replay, replay])
    assert _row_counts(store.path) == {
        "approval_subject_snapshots": 1,
        "approvals": 1,
        "replay_nonces": 0,
    }


def test_sqlite_approval_replay_blocks_corrupted_unavailable_partial_and_wrong_column_schema(tmp_path):
    corrupt_root = tmp_path / "corrupt"
    corrupt_root.mkdir()
    (corrupt_root / "approval_replay.sqlite3").write_text("not a sqlite database", encoding="utf-8")
    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteApprovalReplayStore(root=corrupt_root)

    unavailable_root = tmp_path / "not-a-directory"
    unavailable_root.write_text("file blocks directory creation", encoding="utf-8")
    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteApprovalReplayStore(root=unavailable_root)

    partial_root = tmp_path / "partial"
    partial_root.mkdir()
    with sqlite3.connect(partial_root / "approval_replay.sqlite3") as connection:
        connection.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
        connection.execute("INSERT INTO schema_migrations(version, applied_at) VALUES (1, '2026-05-31T00:00:00+00:00')")
    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteApprovalReplayStore(root=partial_root)

    wrong_root = tmp_path / "wrong"
    wrong_root.mkdir()
    with sqlite3.connect(wrong_root / "approval_replay.sqlite3") as connection:
        connection.executescript(
            """
            CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
            INSERT INTO schema_migrations(version, applied_at) VALUES (1, '2026-05-31T00:00:00+00:00');
            CREATE TABLE approval_subject_snapshots(subject_snapshot_id TEXT PRIMARY KEY);
            CREATE TABLE approvals(approval_id TEXT PRIMARY KEY);
            CREATE TABLE replay_nonces(scope_canonical TEXT, nonce_hash TEXT);
            CREATE INDEX idx_approval_snapshots_run_created ON approval_subject_snapshots(subject_snapshot_id);
            CREATE INDEX idx_approvals_run_type_created ON approvals(approval_id);
            CREATE INDEX idx_replay_nonces_run_claimed ON replay_nonces(scope_canonical);
            """
        )
    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteApprovalReplayStore(root=wrong_root)


def test_sqlite_approval_replay_blocks_schema_without_pk_unique_check_or_fk_contract(tmp_path):
    db_path = tmp_path / "approval_replay.sqlite3"
    with sqlite3.connect(db_path) as connection:
        for table, columns in APPROVAL_REPLAY_EXPECTED_COLUMNS.items():
            definitions = []
            for column in sorted(columns):
                if table == "schema_migrations" and column == "version":
                    definitions.append("version INTEGER PRIMARY KEY")
                elif table == "approval_subject_snapshots" and column == "subject_snapshot_id":
                    definitions.append("subject_snapshot_id TEXT PRIMARY KEY")
                elif table == "approvals" and column == "approval_id":
                    definitions.append("approval_id TEXT PRIMARY KEY")
                elif table == "replay_nonces" and column == "scope_canonical":
                    definitions.append("scope_canonical TEXT")
                elif table == "replay_nonces" and column == "nonce_hash":
                    definitions.append("nonce_hash TEXT")
                elif column in {"snapshot_hash", "approval_hash"}:
                    definitions.append(f"{column} TEXT UNIQUE")
                else:
                    definitions.append(f"{column} TEXT")
            if table == "replay_nonces":
                definitions.append("PRIMARY KEY(scope_canonical, nonce_hash)")
            connection.execute(f"CREATE TABLE {table}({', '.join(definitions)})")
        connection.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (1, '2026-05-31T00:00:00+00:00')"
        )
        connection.execute(
            "CREATE INDEX idx_approval_snapshots_run_created ON approval_subject_snapshots(run_id, created_at)"
        )
        connection.execute("CREATE INDEX idx_approvals_run_type_created ON approvals(run_id, approval_type, created_at)")
        connection.execute("CREATE INDEX idx_replay_nonces_run_claimed ON replay_nonces(run_id, claimed_at)")

    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteApprovalReplayStore(root=tmp_path)


def test_sqlite_approval_replay_blocks_relaxed_check_constraint_schema(tmp_path):
    valid_root = tmp_path / "valid"
    SQLiteApprovalReplayStore(root=valid_root)
    relaxed_root = tmp_path / "relaxed"
    relaxed_root.mkdir()
    old_check = "approval_type IN ('spec_approval', 'live_runner_approval', 'provider_approval')"
    relaxed_check = old_check + " or approval_type = 'evil'"

    with sqlite3.connect(valid_root / "approval_replay.sqlite3") as source:
        source.row_factory = sqlite3.Row
        table_rows = source.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        index_rows = source.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'index' AND sql IS NOT NULL ORDER BY name"
        ).fetchall()
    with sqlite3.connect(relaxed_root / "approval_replay.sqlite3") as target:
        for row in table_rows:
            sql = str(row["sql"])
            if str(row["name"]) == "approval_subject_snapshots":
                sql = sql.replace(old_check, relaxed_check, 1)
            target.execute(sql)
        for row in index_rows:
            target.execute(str(row["sql"]))
        target.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (1, '2026-05-31T00:00:00+00:00')"
        )

    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteApprovalReplayStore(root=relaxed_root)


def test_sqlite_store_boundaries_reject_mixed_schema_files(tmp_path):
    from packages.core.sqlite_repositories import SQLiteRunnerReportAuditStore

    SQLiteRunnerReportAuditStore(root=tmp_path, relative_path="shared.sqlite3")
    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteApprovalReplayStore(root=tmp_path, relative_path="shared.sqlite3")

    other_root = tmp_path / "approval-first"
    SQLiteApprovalReplayStore(root=other_root, relative_path="shared.sqlite3")
    with pytest.raises(SQLiteRepositoryUnavailableError):
        SQLiteRunnerReportAuditStore(root=other_root, relative_path="shared.sqlite3")


def test_sqlite_approval_replay_rejects_path_traversal_path(tmp_path):
    with pytest.raises(ValueError):
        SQLiteApprovalReplayStore(root=tmp_path, relative_path="../approval_replay.sqlite3")

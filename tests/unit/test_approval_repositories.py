import json
from pathlib import Path

import pytest

from packages.core.pathing import PathBoundaryError
from packages.core.repositories import (
    FileBackedReplayNonceRepository,
    InMemoryApprovalRepository,
    InMemoryReplayNonceRepository,
    ReplayNonceReplayError,
    ReplayStoreUnavailableError,
    canonical_replay_scope,
)


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _snapshot_subject(**overrides):
    subject = {
        "plan_hash": "a" * 64,
        "state_hash": "b" * 64,
        "workspace_root": "runs/run-approval",
        "allowed_operations": ["fake_runtime"],
        "signature_id": "sig-should-not-store",
        "signed_contract_hash": "c" * 64,
        "nonce": "nonce-should-not-store",
        "verifier_id": "verifier-should-not-store",
        "key_id": "key-should-not-store",
        "verifier_policy_id": "policy-should-not-store",
        "key_identity_id": "key-identity-should-not-store",
        "raw_prompt": "PERSIST_RAW_PROMPT_FIXTURE",
        "raw_content": "PERSIST_RAW_FILE_BODY",
        "messages": ["PERSIST_RAW_MESSAGE"],
    }
    subject.update(overrides)
    return subject


def _durable_live_approval(repo: InMemoryApprovalRepository):
    snapshot = repo.save_subject_snapshot(
        approval_type="live_runner_approval",
        run_id="run-approval",
        subject_kind="runner_plan",
        subject=_snapshot_subject(),
        subject_schema_version="live-runner-approval-subject-v1",
        source_artifact_ids=("artifact-plan",),
        sanitized_summary="owner@example.com approved live fake runtime",
        created_at="2026-05-31T00:00:00+00:00",
    )
    approval = repo.save_approval(
        approval_id="approval-live-1",
        snapshot=snapshot,
        decision="approved",
        approved_by_ref="owner@example.com",
        approver_role="local-user",
        approved_at="2026-05-31T00:01:00+00:00",
        expires_at="2026-06-01T00:01:00+00:00",
        policy_id_ref="policy-local-fake",
        key_identity_ref="key-identity-local-fake",
        audit_log_id="audit-live-1",
        created_at="2026-05-31T00:01:01+00:00",
    )
    return snapshot, approval


def test_approval_repository_stores_immutable_subject_snapshot_hashes_only():
    snapshot, _approval = _durable_live_approval(InMemoryApprovalRepository())
    stored = snapshot.to_dict()
    serialized = _serialized(stored)

    assert stored["approval_type"] == "live_runner_approval"
    assert stored["subject_hash"]
    assert stored["snapshot_hash"]
    assert stored["scope_canonical"].startswith("aw.approval.v1/live_runner_approval/")
    assert stored["visible_field_counts"]["forbidden_public_key_count"] > 0
    assert "sig-should-not-store" not in serialized
    assert "nonce-should-not-store" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "PERSIST_RAW_PROMPT_FIXTURE" not in serialized
    assert "PERSIST_RAW_FILE_BODY" not in serialized
    assert "owner@example.com" not in serialized


def test_approval_repository_stores_approval_hash_subject_hash_and_scope_only():
    snapshot, approval = _durable_live_approval(InMemoryApprovalRepository())
    stored = approval.to_dict()
    serialized = _serialized(stored)

    assert stored["approval_id"] == "approval-live-1"
    assert stored["subject_hash"] == snapshot.subject_hash
    assert stored["scope_canonical"] == snapshot.scope_canonical
    assert stored["approval_hash"]
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "nonce" not in serialized
    assert "verifier_id" not in serialized
    assert "key_identity_id" not in serialized
    assert "owner@example.com" not in serialized


def test_approval_subject_hash_ignores_raw_authorization_material():
    repo = InMemoryApprovalRepository()
    first = repo.save_subject_snapshot(
        approval_type="provider_approval",
        run_id="run-provider",
        subject_kind="provider_request",
        subject=_snapshot_subject(nonce="nonce-first-secret"),
        subject_schema_version="provider-approval-subject-v1",
        created_at="2026-05-31T00:00:00+00:00",
    )
    second = repo.save_subject_snapshot(
        approval_type="provider_approval",
        run_id="run-provider",
        subject_kind="provider_request",
        subject=_snapshot_subject(nonce="nonce-second-secret"),
        subject_schema_version="provider-approval-subject-v1",
        created_at="2026-05-31T00:00:00+00:00",
    )

    assert first.subject_hash == second.subject_hash
    assert first.scope_canonical == second.scope_canonical


def test_approval_subject_snapshot_rejects_scope_not_bound_to_subject_hash():
    repo = InMemoryApprovalRepository()
    mismatched_scope = canonical_replay_scope(
        approval_type="provider_approval",
        run_id="run-provider",
        subject_hash="f" * 64,
    )

    with pytest.raises(ValueError, match="scope_canonical"):
        repo.save_subject_snapshot(
            approval_type="provider_approval",
            run_id="run-provider",
            subject_kind="provider_request",
            subject=_snapshot_subject(),
            subject_schema_version="provider-approval-subject-v1",
            scope_canonical=mismatched_scope,
        )


def test_approval_repository_rejects_fixture_or_synthetic_live_approval_rows():
    repo = InMemoryApprovalRepository()
    snapshot = repo.save_subject_snapshot(
        approval_type="live_runner_approval",
        run_id="run-approval",
        subject_kind="runner_plan",
        subject=_snapshot_subject(),
        subject_schema_version="live-runner-approval-subject-v1",
        lifecycle_class="synthetic",
    )

    with pytest.raises(ValueError, match="fixture/synthetic"):
        repo.save_approval(
            approval_id="approval-live-synthetic",
            snapshot=snapshot,
            decision="approved",
            approved_by_ref="local-user",
            approver_role="fixture",
            approved_at="2026-05-31T00:00:00+00:00",
            expires_at="2026-06-01T00:00:00+00:00",
        )


def test_replay_nonce_repository_stores_nonce_hash_only():
    _snapshot, approval = _durable_live_approval(InMemoryApprovalRepository())
    repo = InMemoryReplayNonceRepository()
    record = repo.claim(
        scope_canonical="aw.approval.v1/live_runner_approval/run-approval/" + ("d" * 64),
        nonce="nonce-replay-secret",
        approval_hash=approval.approval_hash,
        run_id="run-approval",
        approval_type="live_runner_approval",
        expires_at="2026-06-01T00:00:00+00:00",
    )
    serialized = _serialized(record.to_dict())

    assert record.nonce_hash
    assert "nonce-replay-secret" not in serialized
    assert "nonce_hash" in serialized


def test_replay_nonce_repository_rejects_scope_row_mismatch():
    _snapshot, approval = _durable_live_approval(InMemoryApprovalRepository())
    repo = InMemoryReplayNonceRepository()
    scope = canonical_replay_scope(
        approval_type="provider_approval",
        run_id="run-approval",
        subject_hash="e" * 64,
    )

    with pytest.raises(ValueError, match="approval_type"):
        repo.claim(
            scope_canonical=scope,
            nonce="nonce-row-mismatch",
            approval_hash=approval.approval_hash,
            run_id="run-approval",
            approval_type="live_runner_approval",
            expires_at="2026-06-01T00:00:00+00:00",
        )


@pytest.mark.parametrize("run_id", ["owner@example.com", "../run", "-run", "run/child"])
def test_canonical_replay_scope_rejects_unsafe_run_ids(run_id):
    with pytest.raises(ValueError, match="run_id"):
        canonical_replay_scope(
            approval_type="provider_approval",
            run_id=run_id,
            subject_hash="e" * 64,
        )


def test_replay_nonce_repository_blocks_same_scope_replay_after_restart_simulation():
    _snapshot, approval = _durable_live_approval(InMemoryApprovalRepository())
    scope = canonical_replay_scope(
        approval_type="provider_approval",
        run_id="run-approval",
        subject_hash="e" * 64,
    )
    first_repo = InMemoryReplayNonceRepository()
    first_repo.claim(
        scope_canonical=scope,
        nonce="nonce-restart-secret",
        approval_hash=approval.approval_hash,
        run_id="run-approval",
        approval_type="provider_approval",
        expires_at="2026-06-01T00:00:00+00:00",
    )
    restarted = InMemoryReplayNonceRepository.from_records(first_repo.list_records())

    with pytest.raises(ReplayNonceReplayError):
        restarted.claim(
            scope_canonical=scope,
            nonce="nonce-restart-secret",
            approval_hash=approval.approval_hash,
            run_id="run-approval",
            approval_type="provider_approval",
            expires_at="2026-06-01T00:00:00+00:00",
        )


def test_replay_nonce_repository_allows_cross_scope_nonce_when_subject_hash_differs():
    _snapshot, approval = _durable_live_approval(InMemoryApprovalRepository())
    repo = InMemoryReplayNonceRepository()
    first_scope = canonical_replay_scope(
        approval_type="provider_approval",
        run_id="run-approval",
        subject_hash="e" * 64,
    )
    second_scope = canonical_replay_scope(
        approval_type="provider_approval",
        run_id="run-approval",
        subject_hash="f" * 64,
    )

    repo.claim(
        scope_canonical=first_scope,
        nonce="nonce-cross-scope",
        approval_hash=approval.approval_hash,
        run_id="run-approval",
        approval_type="provider_approval",
        expires_at="2026-06-01T00:00:00+00:00",
    )
    second = repo.claim(
        scope_canonical=second_scope,
        nonce="nonce-cross-scope",
        approval_hash=approval.approval_hash,
        run_id="run-approval",
        approval_type="provider_approval",
        expires_at="2026-06-01T00:00:00+00:00",
    )

    assert second.scope_canonical == second_scope


def test_file_backed_replay_repository_uses_atomic_write_contract(tmp_path):
    _snapshot, approval = _durable_live_approval(InMemoryApprovalRepository())
    repo = FileBackedReplayNonceRepository(root=tmp_path)
    repo.claim(
        scope_canonical=canonical_replay_scope(
            approval_type="live_runner_approval",
            run_id="run-approval",
            subject_hash="a" * 64,
        ),
        nonce="nonce-file-backed",
        approval_hash=approval.approval_hash,
        run_id="run-approval",
        approval_type="live_runner_approval",
        expires_at="2026-06-01T00:00:00+00:00",
    )
    reloaded = FileBackedReplayNonceRepository(root=tmp_path)

    assert len(reloaded.list_records()) == 1
    assert "nonce-file-backed" not in repo.path.read_text(encoding="utf-8")


def test_file_backed_replay_repository_blocks_corrupted_file(tmp_path):
    path = tmp_path / "replay_nonces.json"
    path.write_text("{", encoding="utf-8")
    repo = FileBackedReplayNonceRepository(root=tmp_path)

    with pytest.raises(ReplayStoreUnavailableError):
        repo.list_records()


def test_file_backed_replay_repository_blocks_partial_write_file(tmp_path):
    path = tmp_path / "replay_nonces.json"
    path.write_text('[{"scope_canonical":"aw.approval.v1/provider_approval/run/x"}]', encoding="utf-8")
    repo = FileBackedReplayNonceRepository(root=tmp_path)

    with pytest.raises(ReplayStoreUnavailableError):
        repo.list_records()


def test_file_backed_replay_repository_blocks_missing_durable_metadata(tmp_path):
    path = tmp_path / "replay_nonces.json"
    path.write_text(
        json.dumps(
            [
                {
                    "scope_canonical": canonical_replay_scope(
                        approval_type="provider_approval",
                        run_id="run-approval",
                        subject_hash="e" * 64,
                    ),
                    "nonce_hash": "a" * 64,
                    "approval_hash": "b" * 64,
                    "run_id": "run-approval",
                    "approval_type": "provider_approval",
                }
            ],
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    repo = FileBackedReplayNonceRepository(root=tmp_path)

    with pytest.raises(ReplayStoreUnavailableError):
        repo.list_records()


def test_file_backed_replay_repository_rejects_path_traversal_path(tmp_path):
    with pytest.raises(PathBoundaryError):
        FileBackedReplayNonceRepository(root=tmp_path, relative_path="../escape.json")


def test_file_backed_replay_repository_preserves_existing_tombstone_on_write_failure(
    tmp_path,
    monkeypatch,
):
    _snapshot, approval = _durable_live_approval(InMemoryApprovalRepository())
    repo = FileBackedReplayNonceRepository(root=tmp_path)
    repo.claim(
        scope_canonical=canonical_replay_scope(
            approval_type="provider_approval",
            run_id="run-approval",
            subject_hash="1" * 64,
        ),
        nonce="nonce-existing",
        approval_hash=approval.approval_hash,
        run_id="run-approval",
        approval_type="provider_approval",
        expires_at="2026-06-01T00:00:00+00:00",
    )
    before = repo.path.read_text(encoding="utf-8")

    def fail_replace(self, target):
        raise OSError("simulated partial write")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(ReplayStoreUnavailableError):
        repo.claim(
            scope_canonical=canonical_replay_scope(
                approval_type="provider_approval",
                run_id="run-approval",
                subject_hash="2" * 64,
            ),
            nonce="nonce-new",
            approval_hash=approval.approval_hash,
            run_id="run-approval",
            approval_type="provider_approval",
            expires_at="2026-06-01T00:00:00+00:00",
        )

    assert repo.path.read_text(encoding="utf-8") == before
    assert len(FileBackedReplayNonceRepository(root=tmp_path).list_records()) == 1

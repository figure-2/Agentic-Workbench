import pytest

from packages.core.approval_replay_factory import (
    ApprovalReplayRepositoryConfig,
    build_approval_replay_repositories,
)
from packages.core.repositories import (
    FileBackedReplayNonceRepository,
    InMemoryApprovalRepository,
    InMemoryReplayNonceRepository,
)
from packages.core.sqlite_repositories import SQLiteReplayNonceRepository, SQLiteRepositoryUnavailableError


def test_approval_replay_repository_factory_builds_memory_repositories():
    repositories = build_approval_replay_repositories()

    assert repositories.backend == "memory"
    assert isinstance(repositories.approval_repository, InMemoryApprovalRepository)
    assert isinstance(repositories.replay_nonce_repository, InMemoryReplayNonceRepository)
    assert repositories.sqlite_store is None


def test_approval_replay_repository_factory_builds_file_replay_repository(tmp_path):
    repositories = build_approval_replay_repositories(
        ApprovalReplayRepositoryConfig(backend="file", root=tmp_path)
    )

    assert repositories.backend == "file"
    assert isinstance(repositories.approval_repository, InMemoryApprovalRepository)
    assert isinstance(repositories.replay_nonce_repository, FileBackedReplayNonceRepository)
    assert repositories.sqlite_store is None


def test_approval_replay_repository_factory_builds_sqlite_repositories(tmp_path):
    repositories = build_approval_replay_repositories(
        ApprovalReplayRepositoryConfig(backend="sqlite", root=tmp_path)
    )

    assert repositories.backend == "sqlite"
    assert isinstance(repositories.replay_nonce_repository, SQLiteReplayNonceRepository)
    assert repositories.sqlite_store is not None
    assert repositories.sqlite_store.path.name == "approval_replay.sqlite3"


def test_approval_replay_repository_factory_rejects_unsupported_or_unrooted_backends(tmp_path):
    with pytest.raises(ValueError, match="not supported"):
        build_approval_replay_repositories(ApprovalReplayRepositoryConfig(backend="provider"))

    with pytest.raises(ValueError, match="root is required"):
        build_approval_replay_repositories(ApprovalReplayRepositoryConfig(backend="sqlite"))

    with pytest.raises(ValueError):
        build_approval_replay_repositories(
            ApprovalReplayRepositoryConfig(
                backend="sqlite",
                root=tmp_path,
                relative_path="../approval_replay.sqlite3",
            )
        )

    unavailable_root = tmp_path / "not-a-directory"
    unavailable_root.write_text("file blocks sqlite directory", encoding="utf-8")
    with pytest.raises(SQLiteRepositoryUnavailableError, match="unavailable"):
        build_approval_replay_repositories(
            ApprovalReplayRepositoryConfig(backend="sqlite", root=unavailable_root)
        )


def test_sqlite_factory_keeps_fixture_synthetic_approval_rows_blocked(tmp_path):
    repositories = build_approval_replay_repositories(
        ApprovalReplayRepositoryConfig(backend="sqlite", root=tmp_path)
    )

    with pytest.raises(ValueError, match="fixture/synthetic"):
        repositories.approval_repository.save_subject_snapshot(
            approval_type="live_runner_approval",
            run_id="run-persist-06",
            subject_kind="live_runner_request",
            subject={"plan_hash": "a" * 64},
            subject_schema_version="live-runner-approval-subject-v1",
            lifecycle_class="synthetic",
        )

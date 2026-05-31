"""Factory for approval/replay repository boundary selection.

The factory is intentionally local and explicit. It does not read environment
values, open provider SDKs, or decide whether a live/provider boundary is
approved.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .repositories import (
    ApprovalRepository,
    FileBackedReplayNonceRepository,
    InMemoryApprovalRepository,
    InMemoryReplayNonceRepository,
    ReplayNonceRepository,
)
from .sqlite_repositories import SQLiteApprovalReplayStore


APPROVAL_REPLAY_REPOSITORY_BACKENDS = {"memory", "file", "sqlite"}


@dataclass(frozen=True, slots=True)
class ApprovalReplayRepositoryConfig:
    """Explicit storage selection for approval/replay repositories."""

    backend: str = "memory"
    root: str | Path | None = None
    relative_path: str | Path | None = None


@dataclass(frozen=True, slots=True)
class ApprovalReplayRepositories:
    """Constructed repositories and optional backing store reference."""

    backend: str
    approval_repository: ApprovalRepository
    replay_nonce_repository: ReplayNonceRepository
    sqlite_store: SQLiteApprovalReplayStore | None = None


def build_approval_replay_repositories(
    config: ApprovalReplayRepositoryConfig | None = None,
) -> ApprovalReplayRepositories:
    """Build approval/replay repositories from an explicit local config."""
    selected = config or ApprovalReplayRepositoryConfig()
    backend = selected.backend.strip().lower()
    if backend not in APPROVAL_REPLAY_REPOSITORY_BACKENDS:
        raise ValueError("approval/replay repository backend is not supported")

    if backend == "memory":
        return ApprovalReplayRepositories(
            backend=backend,
            approval_repository=InMemoryApprovalRepository(),
            replay_nonce_repository=InMemoryReplayNonceRepository(),
        )

    if selected.root is None:
        raise ValueError("approval/replay repository root is required")

    if backend == "file":
        return ApprovalReplayRepositories(
            backend=backend,
            approval_repository=InMemoryApprovalRepository(),
            replay_nonce_repository=FileBackedReplayNonceRepository(
                root=selected.root,
                relative_path=selected.relative_path or "replay_nonces.json",
            ),
        )

    sqlite_store = SQLiteApprovalReplayStore(
        root=selected.root,
        relative_path=selected.relative_path or "approval_replay.sqlite3",
    )
    return ApprovalReplayRepositories(
        backend=backend,
        approval_repository=sqlite_store.approvals(),
        replay_nonce_repository=sqlite_store.replay_nonces(),
        sqlite_store=sqlite_store,
    )

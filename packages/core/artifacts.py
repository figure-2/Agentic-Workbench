"""Artifact registry for the workbench MVP."""

from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import Artifact, ArtifactKind


@dataclass(slots=True)
class ArtifactRegistry:
    """In-memory registry used by tests and the first API service pass."""

    artifacts: dict[str, Artifact] = field(default_factory=dict)

    def add(self, artifact: Artifact) -> Artifact:
        if artifact.id in self.artifacts:
            raise ValueError(f"artifact already exists: {artifact.id}")
        self.artifacts[artifact.id] = artifact
        return artifact

    def list_for_run(self, run_id: str, kind: ArtifactKind | None = None) -> list[Artifact]:
        results = [
            artifact
            for artifact in self.artifacts.values()
            if artifact.run_id == run_id and (kind is None or artifact.kind == kind)
        ]
        return sorted(results, key=lambda artifact: artifact.created_at)

    def latest_for_run(self, run_id: str, kind: ArtifactKind) -> Artifact | None:
        artifacts = self.list_for_run(run_id, kind)
        return artifacts[-1] if artifacts else None


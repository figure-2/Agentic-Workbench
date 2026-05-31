import json

import pytest

from packages.core.repositories import (
    InMemoryArtifactRepository,
    InMemoryRunSessionRepository,
    reconstruct_workflow_session_read_model,
)
from packages.core.schemas import Artifact, ArtifactKind, IdeaBrief, WorkflowSession, WorkflowStage


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_run_session_repository_omits_raw_prompt_and_request_body():
    session = WorkflowSession.create(
        IdeaBrief(
            raw_prompt="Build a CRM for alice@example.com with PERSIST_RAW_PROMPT_FIXTURE",
            target_user="ops@example.com",
            product_type="internal workflow",
            constraints=["do not store PERSIST_CONSTRAINT_FIXTURE"],
            success_criteria=["reviewable approval gate"],
        )
    )
    session.move_to(WorkflowStage.APPROVAL)

    record = InMemoryRunSessionRepository().save(session)
    stored = record.to_dict()
    serialized = _serialized(stored)

    assert "raw_prompt" not in stored
    assert "Build a CRM" not in serialized
    assert "PERSIST_RAW_PROMPT_FIXTURE" not in serialized
    assert "PERSIST_CONSTRAINT_FIXTURE" not in serialized
    assert "[REDACTED_PII]" in stored["idea_summary"]
    assert stored["prompt_contract_hash"]


def test_artifact_repository_stores_metadata_hashes_not_raw_payload_body():
    artifact = Artifact.create(
        run_id="run-persist-1",
        kind=ArtifactKind.PRD_PACKAGE,
        name="prd-package.json",
        payload={
            "summary": "Reviewable PRD",
            "raw_content": "PERSIST_RAW_ARTIFACT_BODY",
            "full_prompt": "PERSIST_FULL_PROMPT_BODY",
            "nested": {
                "private_corpus": "PERSIST_PRIVATE_CORPUS_BODY",
                "safe": "PERSIST_SAFE_PAYLOAD_BODY",
            },
        },
    )

    record = InMemoryArtifactRepository().save(artifact)
    stored = record.to_dict()
    serialized = _serialized(stored)

    assert stored["run_id"] == "run-persist-1"
    assert stored["kind"] == "prd_package"
    assert stored["content_hash"]
    assert stored["payload_field_count"] == 2
    assert "PERSIST_RAW_ARTIFACT_BODY" not in serialized
    assert "PERSIST_FULL_PROMPT_BODY" not in serialized
    assert "PERSIST_PRIVATE_CORPUS_BODY" not in serialized
    assert "PERSIST_SAFE_PAYLOAD_BODY" not in serialized


def test_workflow_session_read_model_reconstructs_from_sanitized_rows():
    session = WorkflowSession.create(IdeaBrief(raw_prompt="Create a workbench demo"))
    session.move_to(WorkflowStage.SPEC)
    artifact = Artifact.create(
        run_id=session.id,
        kind=ArtifactKind.BUILD_SPEC,
        name="build-spec.json",
        payload={"api_spec": {"endpoints": [{"path": "/api/v1/runs"}]}},
    )
    session.add_artifact(artifact)

    run_repo = InMemoryRunSessionRepository()
    artifact_repo = InMemoryArtifactRepository()
    run_record = run_repo.save(session)
    artifact_repo.save(artifact)

    read_model = reconstruct_workflow_session_read_model(
        run_record,
        artifact_repo.list_for_run(session.id),
    )
    data = read_model.to_dict()
    serialized = _serialized(data)

    assert data["run_id"] == session.id
    assert data["stage"] == "spec"
    assert data["artifacts"][0]["run_id"] == session.id
    assert "raw_prompt" not in serialized
    assert "Create a workbench demo" not in serialized


def test_read_model_rejects_cross_run_artifact_lineage():
    session = WorkflowSession.create(IdeaBrief(raw_prompt="Create a workbench demo"))
    run_record = InMemoryRunSessionRepository().save(session)
    artifact = Artifact.create(
        run_id="run-other",
        kind=ArtifactKind.BUILD_SPEC,
        name="build-spec.json",
        payload={},
    )
    artifact_record = InMemoryArtifactRepository().save(artifact)

    with pytest.raises(ValueError, match="artifact run_id does not match"):
        reconstruct_workflow_session_read_model(run_record, [artifact_record])

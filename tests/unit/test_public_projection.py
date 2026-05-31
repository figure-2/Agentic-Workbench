import json

import pytest

from apps.api.agentic_workbench_api.services.fixture_harness import fixture_planner
from packages.core.events import WorkflowEvent
from packages.core.public_projection import public_workflow_event_payload, public_workflow_session_payload
from packages.core.schemas import Artifact, ArtifactKind, IdeaBrief, WorkflowSession, WorkflowStage


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_public_workflow_session_projection_omits_raw_fields_and_marks_fixture_mode():
    session = WorkflowSession.create(
        IdeaBrief(
            raw_prompt="Build app with API_KEY=secret-value and RAW_PUBLIC_SENTINEL",
            target_user="owner@example.com",
            product_type="internal workflow",
            constraints=["do not leak RAW_CONSTRAINT_SENTINEL"],
            success_criteria=["reviewable dry-run plan"],
        )
    )
    session.move_to(WorkflowStage.SPEC)
    session.add_artifact(
        Artifact.create(
            run_id=session.id,
            kind=ArtifactKind.PRD_PACKAGE,
            name="prd-package.json",
            payload={
                "summary": "public summary",
                "raw_prompt": "RAW_ARTIFACT_PROMPT_SENTINEL",
                "raw_log": "RAW_LOG_SENTINEL",
                "file_body": "RAW_FILE_BODY_SENTINEL",
                "provider_payload": {"body": "PROVIDER_PAYLOAD_SENTINEL"},
                "approval_authorization_material": "APPROVAL_AUTH_SENTINEL",
            },
        )
    )

    payload = public_workflow_session_payload(session)
    serialized = _serialized(payload)

    assert payload["runtime_mode"] == "fixture"
    assert payload["approval_lifecycle"] == "synthetic"
    assert payload["approval_mode"] == "fixture"
    assert payload["fixture_mode"] is True
    assert payload["durable_user_approval"] is False
    assert payload["run"]["run_id"] == session.id
    assert payload["data_contract"]["workflow_session_to_dict_returned"] is False
    assert "idea" not in payload["run"]
    assert "raw_prompt" not in serialized
    assert "raw_log" not in serialized
    assert "file_body" not in serialized
    assert "provider_payload" not in serialized
    assert "approval_authorization_material" not in serialized
    assert "RAW_PUBLIC_SENTINEL" not in serialized
    assert "RAW_CONSTRAINT_SENTINEL" not in serialized
    assert "RAW_ARTIFACT_PROMPT_SENTINEL" not in serialized
    assert "RAW_LOG_SENTINEL" not in serialized
    assert "RAW_FILE_BODY_SENTINEL" not in serialized
    assert "PROVIDER_PAYLOAD_SENTINEL" not in serialized
    assert "APPROVAL_AUTH_SENTINEL" not in serialized
    assert "owner@example.com" not in serialized
    assert payload["execution_boundary"]["live_provider_call_count"] == 0
    assert payload["execution_boundary"]["live_source_runtime_call_count"] == 0


def test_public_event_projection_blocks_forbidden_claim_language():
    event = WorkflowEvent(
        run_id="run-claim-1",
        stage=WorkflowStage.COMPLETE,
        source="fixture",
        message="real DAACS execution succeeded",
    )

    with pytest.raises(ValueError, match="forbidden claim"):
        public_workflow_event_payload(event)


def test_fixture_planner_does_not_copy_raw_prompt_into_problem_artifact():
    blueprint = fixture_planner(
        IdeaBrief(
            raw_prompt="Create product with FIXTURE_RAW_PROMPT_SENTINEL and token=secret",
            target_user="ops@example.com",
            product_type="approval workflow",
        )
    )
    payload = blueprint.to_dict()
    serialized = _serialized(payload)

    assert payload["problem"].startswith("Sanitized fixture idea")
    assert "FIXTURE_RAW_PROMPT_SENTINEL" not in serialized
    assert "token=secret" not in serialized
    assert "ops@example.com" not in serialized

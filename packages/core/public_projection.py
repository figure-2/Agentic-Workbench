"""Public API projections for workflow sessions.

Internal schemas may preserve raw input for contract conversion. Public API
responses must use this projection layer so raw prompts, file bodies, logs, and
provider authorization material never leave the harness boundary.
"""

from __future__ import annotations

from typing import Any

from .claims import assert_no_forbidden_claims
from .events import WorkflowEvent
from .exposure import assert_no_forbidden_public_keys, sanitize_public_payload
from .repositories import artifact_record_from_artifact, run_session_record_from_session
from .schemas import WorkflowSession


PUBLIC_PROJECTION_VERSION = "workflow-session-public-v1"
FIXTURE_RUNTIME_MODE = "fixture"
FIXTURE_APPROVAL_LIFECYCLE = "synthetic"
FIXTURE_APPROVAL_MODE = "fixture"


def _assert_no_forbidden_claims_in_strings(value: Any) -> None:
    if isinstance(value, str):
        assert_no_forbidden_claims(value)
    elif isinstance(value, dict):
        for item in value.values():
            _assert_no_forbidden_claims_in_strings(item)
    elif isinstance(value, list | tuple):
        for item in value:
            _assert_no_forbidden_claims_in_strings(item)


def assert_public_projection_safe(payload: dict[str, Any]) -> None:
    """Fail closed if a public projection still contains blocked material."""
    assert_no_forbidden_public_keys(payload)
    _assert_no_forbidden_claims_in_strings(payload)


def public_workflow_event_payload(event: WorkflowEvent | dict[str, Any]) -> dict[str, Any]:
    """Return a sanitized event projection suitable for API responses."""
    event_payload = event.to_dict() if isinstance(event, WorkflowEvent) else event
    public_payload = sanitize_public_payload(event_payload)
    if not isinstance(public_payload, dict):
        raise ValueError("public event projection must be a mapping")
    assert_public_projection_safe(public_payload)
    return public_payload


def public_workflow_event_payloads(events: list[WorkflowEvent] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return sanitized event projections for API responses."""
    return [public_workflow_event_payload(event) for event in events]


def public_workflow_session_payload(
    session: WorkflowSession,
    *,
    runtime_mode: str = FIXTURE_RUNTIME_MODE,
    approval_lifecycle: str = FIXTURE_APPROVAL_LIFECYCLE,
    approval_mode: str = FIXTURE_APPROVAL_MODE,
) -> dict[str, Any]:
    """Project a workflow session into a raw-prompt-free public response."""
    run_record = run_session_record_from_session(session)
    artifact_records = [artifact_record_from_artifact(artifact) for artifact in session.artifacts]
    public_payload = {
        "projection_version": PUBLIC_PROJECTION_VERSION,
        "runtime_mode": runtime_mode,
        "approval_lifecycle": approval_lifecycle,
        "approval_mode": approval_mode,
        "fixture_mode": runtime_mode == FIXTURE_RUNTIME_MODE,
        "durable_user_approval": False,
        "run": run_record.to_dict(),
        "artifact_count": len(artifact_records),
        "artifacts": [artifact.to_dict() for artifact in artifact_records],
        "execution_boundary": {
            "runner": "fixture_harness",
            "live_provider_call_count": 0,
            "live_source_runtime_call_count": 0,
            "subprocess_spawn_count": 0,
            "network_call_count": 0,
            "file_mutation_count": 0,
        },
        "claim_boundary": {
            "scope": "local/dev fixture projection",
            "fixture_only": runtime_mode == FIXTURE_RUNTIME_MODE,
            "provider_success_claim": False,
            "source_runtime_success_claim": False,
            "production_success_claim": False,
        },
        "data_contract": {
            "workflow_session_to_dict_returned": False,
            "input_text_returned": False,
            "artifact_body_returned": False,
        },
    }
    sanitized = sanitize_public_payload(public_payload)
    if not isinstance(sanitized, dict):
        raise ValueError("public workflow session projection must be a mapping")
    assert_public_projection_safe(sanitized)
    return sanitized

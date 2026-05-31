"""FastAPI entrypoint sketch for Agentic Workbench.

The current MVP service uses fixture mode so the API contract can be tested
without live LLM, Tavily, Qdrant, or CLI agent calls.
"""

from __future__ import annotations

from packages.core.public_projection import public_workflow_event_payloads, public_workflow_session_payload
from packages.core.schemas import IdeaBrief
from .services.fixture_harness import create_fixture_harness

try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover - documented fallback for local schema tests
    FastAPI = None


def create_app():
    if FastAPI is None:
        raise RuntimeError("fastapi is not installed. Install API dependencies before serving.")

    app = FastAPI(title="Agentic Workbench API", version="0.1.0")

    @app.post("/api/v1/runs")
    def create_run(payload: dict):
        idea = IdeaBrief(
            raw_prompt=payload["raw_prompt"],
            target_user=payload.get("target_user"),
            product_type=payload.get("product_type"),
            constraints=payload.get("constraints", []),
            success_criteria=payload.get("success_criteria", []),
        )
        harness = create_fixture_harness()
        session = harness.run(idea)
        return {
            "data": public_workflow_session_payload(session),
            "events": public_workflow_event_payloads(harness.event_dicts()),
        }

    return app


app = create_app() if FastAPI is not None else None

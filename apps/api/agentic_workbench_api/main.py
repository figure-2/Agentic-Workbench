"""FastAPI entrypoint sketch for Agentic Workbench.

The current MVP service uses fixture mode so the API contract can be tested
without live LLM, Tavily, Qdrant, or CLI agent calls.
"""

from __future__ import annotations

from packages.core.approval_replay_factory import ApprovalReplayRepositoryConfig
from packages.core.public_projection import (
    assert_public_projection_safe,
    public_workflow_event_payloads,
    public_workflow_session_payload,
)
from packages.core.schemas import IdeaBrief
from .services.admission_demo import (
    AdmissionRepositoryProvider,
    run_live_admission_demo,
    run_provider_admission_demo,
)
from .services.evidence_read_model import (
    EvidenceRepositoryConfig,
    EvidenceRepositoryProvider,
    read_run_evidence,
    read_run_verification,
)
from .services.evidence_write_model import persist_fixture_run_evidence
from .services.fixture_harness import create_fixture_harness
from .services.planner_provider_preflight import run_planner_provider_preflight
from .services.target_runtime_admission import (
    TargetRuntimeAdmissionRepositoryConfig,
    TargetRuntimeAdmissionRepositoryProvider,
    read_target_runtime_adapter_admissions,
    run_target_runtime_adapter_admission,
)
from .services.target_runtime_output_manifest import (
    TargetRuntimeOutputManifestRepositoryConfig,
    TargetRuntimeOutputManifestRepositoryProvider,
    read_target_runtime_output_manifests,
    run_target_runtime_output_manifest,
)
from .services.target_runtime_generated_artifact_bundle import (
    run_target_runtime_generated_artifact_bundle,
)
from .services.target_runtime_preflight import run_target_runtime_preflight
from .services.canonical_run_store import (
    RunArtifactRepositoryConfig,
    RunArtifactRepositoryProvider,
    persist_canonical_run_session,
    read_canonical_artifacts,
    read_composed_canonical_run,
)
from .services.provider_envelope_api import (
    ProviderEnvelopeRepositoryConfig,
    ProviderEnvelopeRepositoryProvider,
    read_provider_envelope_precheck,
    run_provider_envelope_precheck,
)

try:
    from fastapi import FastAPI, HTTPException
except ImportError:  # pragma: no cover - documented fallback for local schema tests
    FastAPI = None
    HTTPException = None


def create_app(
    *,
    admission_repository_config: ApprovalReplayRepositoryConfig | None = None,
    admission_repository_provider: AdmissionRepositoryProvider | None = None,
    evidence_repository_config: EvidenceRepositoryConfig | None = None,
    evidence_repository_provider: EvidenceRepositoryProvider | None = None,
    run_repository_config: RunArtifactRepositoryConfig | None = None,
    run_repository_provider: RunArtifactRepositoryProvider | None = None,
    provider_envelope_repository_config: ProviderEnvelopeRepositoryConfig | None = None,
    provider_envelope_repository_provider: ProviderEnvelopeRepositoryProvider | None = None,
    target_runtime_admission_repository_config: (
        TargetRuntimeAdmissionRepositoryConfig | None
    ) = None,
    target_runtime_admission_repository_provider: (
        TargetRuntimeAdmissionRepositoryProvider | None
    ) = None,
    target_runtime_output_manifest_repository_config: (
        TargetRuntimeOutputManifestRepositoryConfig | None
    ) = None,
    target_runtime_output_manifest_repository_provider: (
        TargetRuntimeOutputManifestRepositoryProvider | None
    ) = None,
):
    if FastAPI is None:
        raise RuntimeError("fastapi is not installed. Install API dependencies before serving.")

    app = FastAPI(title="Agentic Workbench API", version="0.1.0")
    admission_repositories = admission_repository_provider or AdmissionRepositoryProvider(
        admission_repository_config
    )
    evidence_repositories = evidence_repository_provider or EvidenceRepositoryProvider(
        evidence_repository_config
    )
    run_repositories = run_repository_provider or RunArtifactRepositoryProvider(
        run_repository_config
    )
    provider_envelope_repositories = (
        provider_envelope_repository_provider
        or ProviderEnvelopeRepositoryProvider(provider_envelope_repository_config)
    )
    target_runtime_admission_repositories = (
        target_runtime_admission_repository_provider
        or TargetRuntimeAdmissionRepositoryProvider(
            target_runtime_admission_repository_config
        )
    )
    target_runtime_output_manifest_repositories = (
        target_runtime_output_manifest_repository_provider
        or TargetRuntimeOutputManifestRepositoryProvider(
            target_runtime_output_manifest_repository_config
        )
    )

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
        events = public_workflow_event_payloads(harness.event_dicts())
        data = public_workflow_session_payload(session)
        data["canonical_persistence"] = persist_canonical_run_session(
            session,
            run_repository_provider=run_repositories,
        )
        data["evidence_persistence"] = persist_fixture_run_evidence(
            session,
            harness.event_dicts(),
            evidence_provider=evidence_repositories,
        )
        assert_public_projection_safe(data)
        return {
            "data": data,
            "events": events,
        }

    @app.post("/api/v1/admissions/provider/fake")
    def create_provider_admission(payload: dict):
        try:
            return {
                "data": run_provider_admission_demo(
                    payload,
                    repository_provider=admission_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/admissions/live/fake")
    def create_live_admission(payload: dict):
        try:
            return {
                "data": run_live_admission_demo(
                    payload,
                    repository_provider=admission_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/admissions/provider/envelope/precheck")
    def create_provider_envelope_precheck(payload: dict):
        try:
            return {
                "data": run_provider_envelope_precheck(
                    payload,
                    repository_provider=provider_envelope_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/planner/provider/preflight")
    def create_planner_provider_preflight(payload: dict):
        try:
            return {"data": run_planner_provider_preflight(payload)}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/daacs/runtime/preflight")
    def create_daacs_runtime_preflight(payload: dict):
        try:
            return {"data": run_target_runtime_preflight(payload)}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/daacs/runtime/adapter/admission")
    def create_daacs_runtime_adapter_admission(payload: dict):
        try:
            return {
                "data": run_target_runtime_adapter_admission(
                    payload,
                    repository_provider=target_runtime_admission_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/daacs/runtime/adapter/admissions/{run_id}")
    def get_daacs_runtime_adapter_admissions(run_id: str):
        try:
            return {
                "data": read_target_runtime_adapter_admissions(
                    run_id,
                    repository_provider=target_runtime_admission_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/daacs/runtime/output-manifest")
    def create_daacs_runtime_output_manifest(payload: dict):
        try:
            return {
                "data": run_target_runtime_output_manifest(
                    payload,
                    repository_provider=target_runtime_output_manifest_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/daacs/runtime/output-manifests/{run_id}")
    def get_daacs_runtime_output_manifests(run_id: str):
        try:
            return {
                "data": read_target_runtime_output_manifests(
                    run_id,
                    repository_provider=target_runtime_output_manifest_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/v1/daacs/runtime/generated-artifact-bundle")
    def create_daacs_runtime_generated_artifact_bundle(payload: dict):
        try:
            return {"data": run_target_runtime_generated_artifact_bundle(payload)}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/admissions/provider/envelopes/{run_id}")
    def get_provider_envelope_precheck(run_id: str):
        try:
            return {
                "data": read_provider_envelope_precheck(
                    run_id,
                    repository_provider=provider_envelope_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/evidence/runs/{run_id}")
    def get_run_evidence(run_id: str):
        try:
            return {
                "data": read_run_evidence(
                    run_id,
                    evidence_provider=evidence_repositories,
                    admission_repository_provider=admission_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/runs/{run_id}")
    def get_run(run_id: str):
        try:
            return {
                "data": read_composed_canonical_run(
                    run_id,
                    run_repository_provider=run_repositories,
                    evidence_repository_provider=evidence_repositories,
                    admission_repository_provider=admission_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/runs/{run_id}/artifacts")
    def get_run_artifacts(run_id: str):
        try:
            return {
                "data": read_canonical_artifacts(
                    run_id,
                    run_repository_provider=run_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/v1/runs/{run_id}/verification")
    def get_run_verification(run_id: str):
        try:
            return {
                "data": read_run_verification(
                    run_id,
                    evidence_provider=evidence_repositories,
                )
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    return app


app = create_app() if FastAPI is not None else None

"""API/read-model hook for provider envelope admission prechecks.

This service wires the no-call provider envelope admission boundary into API
and demo paths. It stores and returns only sanitized hash/count/status
projections; it never reads env values, imports provider SDKs, opens network
sockets, or calls external APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from packages.core.exposure import sanitize_public_payload
from packages.core.live_open_policy import (
    LIVE_OPEN_REQUIRED_CONTROLS,
    SOLAR_PRO_3_ENV_KEY_NAME,
    SOLAR_PROVIDER_SURFACE,
    LiveOpenRequest,
    evaluate_live_open_request,
)
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict
from packages.daacs_builder.provider_boundary import (
    SOLAR_PRO_3_MODEL,
    SOLAR_PRO_3_PROVIDER,
    ProviderApprovalRecord,
    ProviderRequest,
    zero_provider_side_effect_metrics,
)
from packages.daacs_builder.provider_envelope_admission import (
    ProviderEnvelopeAdmissionService,
    invoke_adapter_after_provider_envelope_admission,
)
from packages.daacs_builder.provider_envelope_store import (
    PROVIDER_ENVELOPE_DB_NAME,
    SQLiteProviderEnvelopeStore,
    provider_envelope_public_read_model,
)
from packages.daacs_builder.runner_provider import safe_public_run_id
from packages.daacs_builder.solar_contracts import (
    SolarCostTimeoutPolicy,
    attach_solar_response_projection_fixture,
    build_solar_request_contract_fixture,
)
from packages.daacs_builder.solar_live_adapter import (
    SOLAR_LIVE_ADAPTER_MODE,
    DisabledSolarPro3LiveAdapter,
    SolarPro3LiveAdapterConfig,
)


PROVIDER_ENVELOPE_API_PROJECTION_VERSION = "provider-envelope-admission-api-public-v1"
PROVIDER_ENVELOPE_PRECHECK_MODE = "live_admission_precheck"


@dataclass(slots=True)
class ProviderEnvelopeRepositoryConfig:
    """Server-side provider envelope store selector."""

    root: str | Path | None = None
    filename: str = PROVIDER_ENVELOPE_DB_NAME


@dataclass(slots=True)
class ProviderEnvelopeRepositoryProvider:
    """Cached SQLite provider envelope repository provider for API paths."""

    config: ProviderEnvelopeRepositoryConfig | None = None
    _cached_store: SQLiteProviderEnvelopeStore | None = None

    @property
    def configured(self) -> bool:
        return self.config is not None and self.config.root is not None

    @property
    def backend(self) -> str:
        return "sqlite" if self.configured else "unconfigured"

    def store(self) -> SQLiteProviderEnvelopeStore:
        if not self.configured or self.config is None or self.config.root is None:
            raise ValueError("provider envelope repository is not configured")
        if self._cached_store is None:
            self._cached_store = SQLiteProviderEnvelopeStore(
                root=self.config.root,
                filename=self.config.filename,
            )
        return self._cached_store

    def repository(self):
        return self.store().repository()


def _dataclass_payload(payload: dict[str, Any], cls: type) -> dict[str, Any]:
    allowed = {field.name for field in fields(cls)}
    return {key: value for key, value in payload.items() if key in allowed}


def _safe_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = sanitize_public_payload(payload)
    if not isinstance(sanitized, dict):
        raise ValueError("provider envelope public projection must be a mapping")
    assert_public_projection_safe(sanitized)
    return sanitized


def _check_map(checks: list[JsonDict]) -> list[JsonDict]:
    return [
        {
            "name": str(check.get("name", "")),
            "passed": bool(check.get("passed")),
        }
        for check in checks
    ]


def _zero_execution_boundary(extra: dict[str, Any] | None = None) -> JsonDict:
    return {
        **zero_provider_side_effect_metrics(),
        "provider_envelope_sdk_imports": 0,
        "provider_envelope_env_value_reads": 0,
        "provider_envelope_api_calls": 0,
        "provider_envelope_network_calls": 0,
        "solar_live_sdk_imports": 0,
        "solar_live_env_value_reads": 0,
        "solar_live_api_calls": 0,
        "adapter_invocation_count": 0,
        **(extra or {}),
    }


def _blocked_projection(
    *,
    run_id: str,
    repository_provider: ProviderEnvelopeRepositoryProvider,
    check_name: str,
    message: str,
    read_model: JsonDict | None = None,
    adapter_invocation_count: int = 0,
) -> dict[str, Any]:
    return _safe_public_payload(
        {
            "projection_version": PROVIDER_ENVELOPE_API_PROJECTION_VERSION,
            "admission_kind": "provider_envelope",
            "runtime_mode": PROVIDER_ENVELOPE_PRECHECK_MODE,
            "fixture_mode": False,
            "durable_user_approval": False,
            "run_id": safe_public_run_id(run_id),
            "status": "blocked",
            "provider_envelope_admission": {
                "status": "blocked",
                "adapter_reached": False,
                "request_contract_hash": "",
                "response_contract_hash": "",
                "counts": {
                    "provider_envelope_count": 0,
                    "request_contract_hash_count": 0,
                    "response_contract_hash_count": 0,
                },
            },
            "provider_envelope_read_model": read_model or {},
            "checks": [{"name": check_name, "passed": False}],
            "errors": [message],
            "repository_boundary": {
                "provider_envelope_backend": repository_provider.backend,
                "provider_envelope_store_configured": repository_provider.configured,
                "raw_row_returned": False,
                "root_path_returned": False,
            },
            "execution_boundary": _zero_execution_boundary(
                {"adapter_invocation_count": adapter_invocation_count}
            ),
            "claim_boundary": {
                "scope": "local provider envelope precheck only",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
                "production_trust_claim": False,
            },
        }
    )


def _policy_from_payload(payload: dict[str, Any]) -> SolarCostTimeoutPolicy:
    policy_payload = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    return SolarCostTimeoutPolicy(
        request_timeout_seconds=policy_payload.get("request_timeout_seconds"),
        max_cost_units=policy_payload.get("max_cost_units"),
        max_live_api_calls=policy_payload.get("max_live_api_calls"),
        max_output_tokens=policy_payload.get("max_output_tokens"),
        retry_count=int(policy_payload.get("retry_count", 0)),
    )


def _approval_from_payload(payload: dict[str, Any]) -> ProviderApprovalRecord:
    approval_payload = payload.get("approval")
    if not isinstance(approval_payload, dict):
        raise ValueError("provider envelope approval payload is required")
    return ProviderApprovalRecord(**_dataclass_payload(approval_payload, ProviderApprovalRecord))


def _request_from_payload(payload: dict[str, Any]) -> ProviderRequest:
    run_id = str(payload["run_id"])
    expected_hash = payload.get("expected_request_contract_hash")
    metadata: JsonDict = {}
    if isinstance(expected_hash, str) and expected_hash:
        metadata["expected_request_contract_hash"] = expected_hash
    return ProviderRequest(
        run_id=run_id,
        prompt_contract_hash=str(payload["prompt_contract_hash"]),
        provider_name=str(payload.get("provider_name", SOLAR_PRO_3_PROVIDER)),
        model_name=str(payload.get("model_name", SOLAR_PRO_3_MODEL)),
        mode=SOLAR_LIVE_ADAPTER_MODE,
        env_key_name=SOLAR_PRO_3_ENV_KEY_NAME,
        approval=_approval_from_payload(payload),
        metadata=metadata,
    )


def _ready_live_open_decision(payload: dict[str, Any], run_id: str):
    controls_payload = (
        payload.get("live_open_controls")
        if isinstance(payload.get("live_open_controls"), dict)
        else {}
    )
    controls = {
        field_name: bool(controls_payload.get(field_name, False))
        for field_name in LIVE_OPEN_REQUIRED_CONTROLS
    }
    return evaluate_live_open_request(
        LiveOpenRequest(
            run_id=run_id,
            surface=SOLAR_PROVIDER_SURFACE,
            env_key_name=SOLAR_PRO_3_ENV_KEY_NAME,
            **controls,
        )
    )


def _adapter_config(policy: SolarCostTimeoutPolicy) -> SolarPro3LiveAdapterConfig:
    return SolarPro3LiveAdapterConfig(
        enabled=True,
        request_timeout_seconds=policy.request_timeout_seconds,
        max_cost_units=policy.max_cost_units,
        max_output_tokens=policy.max_output_tokens,
        max_live_api_calls=policy.max_live_api_calls,
        allow_network=False,
    )


def _read_model_counts(read_model: JsonDict) -> JsonDict:
    counts = read_model.get("counts") if isinstance(read_model.get("counts"), dict) else {}
    return {
        "provider_envelope_count": int(counts.get("provider_envelope_count", 0)),
        "request_contract_hash_count": int(counts.get("request_contract_hash_count", 0)),
        "response_contract_hash_count": int(counts.get("response_contract_hash_count", 0)),
    }


def _projection_from_result(
    *,
    run_id: str,
    result,
    read_model: JsonDict,
    repository_provider: ProviderEnvelopeRepositoryProvider,
) -> dict[str, Any]:
    metrics = dict(result.metrics)
    request_hash = ""
    response_hash = ""
    if result.audit_events:
        first_event = result.audit_events[0]
        if isinstance(first_event, dict):
            request_hash = str(first_event.get("request_contract_hash", ""))
            response_hash = str(first_event.get("response_contract_hash", ""))
    admission_status = (
        "admitted"
        if int(metrics.get("provider_envelope_admission_hash_match_count", 0)) == 1
        else "blocked"
    )
    adapter_reached = int(metrics.get("provider_envelope_adapter_invocation_count", 0)) == 1
    return _safe_public_payload(
        {
            "projection_version": PROVIDER_ENVELOPE_API_PROJECTION_VERSION,
            "admission_kind": "provider_envelope",
            "runtime_mode": PROVIDER_ENVELOPE_PRECHECK_MODE,
            "fixture_mode": False,
            "durable_user_approval": False,
            "run_id": safe_public_run_id(run_id),
            "status": result.status,
            "provider_envelope_admission": {
                "status": admission_status,
                "adapter_reached": adapter_reached,
                "request_contract_hash": request_hash,
                "response_contract_hash": response_hash,
                "counts": _read_model_counts(read_model),
            },
            "provider_envelope_read_model": read_model,
            "checks": _check_map(result.checks),
            "errors": [str(error) for error in result.errors],
            "repository_boundary": {
                "provider_envelope_backend": repository_provider.backend,
                "provider_envelope_store_configured": repository_provider.configured,
                "raw_row_returned": False,
                "root_path_returned": False,
            },
            "execution_boundary": _zero_execution_boundary(
                {
                    **metrics,
                    "adapter_invocation_count": int(
                        metrics.get("provider_envelope_adapter_invocation_count", 0)
                    ),
                }
            ),
            "claim_boundary": {
                "scope": "local provider envelope precheck only",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
                "production_trust_claim": False,
            },
        }
    )


def run_provider_envelope_precheck(
    payload: dict[str, Any],
    *,
    repository_provider: ProviderEnvelopeRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Run a local no-call provider envelope admission precheck."""
    selected_provider = repository_provider or ProviderEnvelopeRepositoryProvider()
    if payload.get("fixture_mode") is True or str(payload.get("runtime_mode", "")) in {
        "fixture",
        "dry_run",
    }:
        raise ValueError("fixture/dry-run paths cannot use provider envelope live precheck")

    request = _request_from_payload(payload)
    if not selected_provider.configured:
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_repository_configured",
            message="provider envelope repository is required before adapter admission.",
        )

    policy = _policy_from_payload(payload)
    request_result = build_solar_request_contract_fixture(request, policy)
    contract_result = attach_solar_response_projection_fixture(
        request_result,
        response_summary=str(
            payload.get("response_summary") or "sanitized provider envelope precheck projection"
        ),
        raw_response_body=None,
    )
    if contract_result.status != "projected_fixture":
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_contract_projected",
            message="provider envelope contract fixture could not be projected.",
            adapter_invocation_count=0,
        )

    try:
        repository = selected_provider.repository()
    except Exception:
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_repository_available",
            message="provider envelope repository is unavailable.",
        )

    service = ProviderEnvelopeAdmissionService(repository)
    adapter = DisabledSolarPro3LiveAdapter(
        config=_adapter_config(policy),
        live_open_decision=_ready_live_open_decision(payload, request.run_id),
    )
    result = invoke_adapter_after_provider_envelope_admission(
        adapter=adapter,
        request=request,
        contract_result=contract_result,
        admission_service=service,
    )
    try:
        read_model = provider_envelope_public_read_model(repository, run_id=request.run_id)
    except Exception:
        read_model = {}
    return _projection_from_result(
        run_id=request.run_id,
        result=result,
        read_model=read_model,
        repository_provider=selected_provider,
    )


def read_provider_envelope_precheck(
    run_id: str,
    *,
    repository_provider: ProviderEnvelopeRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Read sanitized provider envelope evidence for API/demo responses."""
    selected_provider = repository_provider or ProviderEnvelopeRepositoryProvider()
    if not selected_provider.configured:
        return _blocked_projection(
            run_id=run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_repository_configured",
            message="provider envelope repository is not configured.",
        )
    try:
        read_model = provider_envelope_public_read_model(
            selected_provider.repository(),
            run_id=run_id,
        )
    except Exception:
        return _blocked_projection(
            run_id=run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_repository_available",
            message="provider envelope repository is unavailable.",
        )
    return _safe_public_payload(
        {
            "projection_version": PROVIDER_ENVELOPE_API_PROJECTION_VERSION,
            "admission_kind": "provider_envelope",
            "runtime_mode": PROVIDER_ENVELOPE_PRECHECK_MODE,
            "fixture_mode": False,
            "durable_user_approval": False,
            "run_id": safe_public_run_id(run_id),
            "status": read_model.get("status", "blocked"),
            "provider_envelope_admission": {
                "status": "read_model_only",
                "adapter_reached": False,
                "request_contract_hash": "",
                "response_contract_hash": "",
                "counts": _read_model_counts(read_model),
            },
            "provider_envelope_read_model": read_model,
            "checks": [{"name": "provider_envelope_read_model_available", "passed": True}],
            "errors": [],
            "repository_boundary": {
                "provider_envelope_backend": selected_provider.backend,
                "provider_envelope_store_configured": selected_provider.configured,
                "raw_row_returned": False,
                "root_path_returned": False,
            },
            "execution_boundary": _zero_execution_boundary(),
            "claim_boundary": {
                "scope": "local provider envelope read model only",
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
                "production_trust_claim": False,
            },
        }
    )


__all__ = [
    "ProviderEnvelopeRepositoryConfig",
    "ProviderEnvelopeRepositoryProvider",
    "read_provider_envelope_precheck",
    "run_provider_envelope_precheck",
]

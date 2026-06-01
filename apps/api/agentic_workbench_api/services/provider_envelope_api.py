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
from packages.core.schemas import JsonDict, stable_contract_hash
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
OPERATOR_POLICY_SUMMARY_VERSION = "provider-precheck-operator-policy-summary-v1"
OPERATOR_APPROVAL_ENVELOPE_VERSION = "provider-precheck-operator-approval-envelope-v1"
LIVE_PROVIDER_DRY_ADMISSION_VERSION = "live-provider-dry-admission-checklist-v1"


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


def _dry_admission_bool(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else False


def _live_provider_dry_admission_checklist(
    *,
    run_id: str,
    operator_policy_summary: JsonDict | None = None,
    operator_approval_envelope: JsonDict | None = None,
) -> JsonDict:
    policy_summary = operator_policy_summary or {}
    approval_envelope = operator_approval_envelope or _operator_approval_missing_projection()
    policy = policy_summary.get("policy") if isinstance(policy_summary.get("policy"), dict) else {}
    readiness = (
        policy_summary.get("readiness")
        if isinstance(policy_summary.get("readiness"), dict)
        else {}
    )
    expected_policy_hash = str(policy_summary.get("policy_summary_hash", ""))
    approved_policy_hash = str(approval_envelope.get("policy_summary_hash", ""))
    approval_status = str(approval_envelope.get("status", "missing"))
    approval_hash_match = bool(expected_policy_hash) and approved_policy_hash == expected_policy_hash
    checklist = [
        {
            "id": "operator_approval_envelope_present",
            "status": "passed" if approval_status == "approved" else "blocked",
            "passed": approval_status == "approved",
            "manual_review": False,
        },
        {
            "id": "policy_summary_hash_bound",
            "status": "passed" if approval_hash_match else "blocked",
            "passed": approval_hash_match,
            "manual_review": False,
        },
        {
            "id": "cost_limit_reviewed",
            "status": "passed" if int(policy.get("max_cost_units", 0)) > 0 else "blocked",
            "passed": int(policy.get("max_cost_units", 0)) > 0,
            "manual_review": False,
        },
        {
            "id": "timeout_limit_reviewed",
            "status": "passed"
            if int(policy.get("request_timeout_seconds", 0)) > 0
            else "blocked",
            "passed": int(policy.get("request_timeout_seconds", 0)) > 0,
            "manual_review": False,
        },
        {
            "id": "api_quota_reviewed",
            "status": "passed" if int(policy.get("max_live_api_calls", 0)) > 0 else "blocked",
            "passed": int(policy.get("max_live_api_calls", 0)) > 0,
            "manual_review": False,
        },
        {
            "id": "output_budget_reviewed",
            "status": "passed"
            if int(policy.get("max_output_unit_budget", 0)) > 0
            else "blocked",
            "passed": int(policy.get("max_output_unit_budget", 0)) > 0,
            "manual_review": False,
        },
        {
            "id": "rollback_plan_documented",
            "status": "manual_required",
            "passed": False,
            "manual_review": True,
        },
        {
            "id": "manual_operator_final_review",
            "status": "manual_required",
            "passed": False,
            "manual_review": True,
        },
        {
            "id": "execution_permission_closed",
            "status": "closed",
            "passed": not _dry_admission_bool(readiness.get("allowed_to_execute")),
            "manual_review": False,
        },
    ]
    passed_count = sum(1 for item in checklist if item["passed"] is True)
    blocked_count = sum(1 for item in checklist if item["status"] == "blocked")
    manual_required_count = sum(1 for item in checklist if item["manual_review"] is True)
    projection = {
        "projection_version": LIVE_PROVIDER_DRY_ADMISSION_VERSION,
        "status": "dry_admission_only",
        "run_id": safe_public_run_id(run_id),
        "provider_name": str(policy_summary.get("provider_name", SOLAR_PRO_3_PROVIDER)),
        "model_name": str(policy_summary.get("model_name", SOLAR_PRO_3_MODEL)),
        "runtime_mode": PROVIDER_ENVELOPE_PRECHECK_MODE,
        "live_ready": False,
        "allowed_to_execute": False,
        "checklist_item_count": len(checklist),
        "passed_check_count": passed_count,
        "blocked_check_count": blocked_count,
        "manual_required_count": manual_required_count,
        "checklist": checklist,
        "operator_approval": {
            "status": approval_status,
            "policy_summary_hash_present": bool(expected_policy_hash),
            "policy_summary_hash_match": approval_hash_match,
            "envelope_hash_present": bool(approval_envelope.get("envelope_hash")),
        },
        "policy_summary": {
            "cost_limit_configured": int(policy.get("max_cost_units", 0)) > 0,
            "timeout_configured": int(policy.get("request_timeout_seconds", 0)) > 0,
            "api_quota_configured": int(policy.get("max_live_api_calls", 0)) > 0,
            "output_budget_configured": int(policy.get("max_output_unit_budget", 0)) > 0,
            "required_control_count": int(readiness.get("required_control_count", 0)),
            "missing_control_count": int(readiness.get("missing_control_count", 0)),
            "eligible_for_later_live_open": _dry_admission_bool(
                readiness.get("eligible_for_live_open")
            ),
            "execution_permission_closed": not _dry_admission_bool(
                readiness.get("allowed_to_execute")
            ),
        },
        "execution_boundary": {
            "sdk_imports": 0,
            "env_value_reads": 0,
            "api_calls": 0,
            "network_calls": 0,
            "solar_provider_calls": 0,
            "target_runtime_calls": 0,
        },
        "claim_boundary": {
            "scope": "local provider dry-admission checklist only",
            "external_provider_outcome": False,
            "target_runtime_outcome": False,
            "production_trust_claim": False,
        },
    }
    projection["dry_admission_hash"] = stable_contract_hash(projection)
    return _safe_public_payload(projection)


def _blocked_projection(
    *,
    run_id: str,
    repository_provider: ProviderEnvelopeRepositoryProvider,
    check_name: str,
    message: str,
    read_model: JsonDict | None = None,
    adapter_invocation_count: int = 0,
    operator_policy_summary: JsonDict | None = None,
    operator_approval_envelope: JsonDict | None = None,
    live_provider_dry_admission: JsonDict | None = None,
) -> dict[str, Any]:
    selected_operator_approval = operator_approval_envelope or _operator_approval_missing_projection()
    selected_dry_admission = live_provider_dry_admission or _live_provider_dry_admission_checklist(
        run_id=run_id,
        operator_policy_summary=operator_policy_summary,
        operator_approval_envelope=selected_operator_approval,
    )
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
            "operator_policy_summary": operator_policy_summary or {},
            "operator_approval_envelope": selected_operator_approval,
            "live_provider_dry_admission": selected_dry_admission,
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


def _operator_policy_summary(
    *,
    request: ProviderRequest,
    policy: SolarCostTimeoutPolicy,
    live_open_decision,
) -> JsonDict:
    checks = getattr(live_open_decision, "checks", [])
    missing_controls = [
        str(check.get("name", ""))
        for check in checks
        if check.get("passed") is False and str(check.get("name", "")) in LIVE_OPEN_REQUIRED_CONTROLS
    ]
    summary = {
        "projection_version": OPERATOR_POLICY_SUMMARY_VERSION,
        "run_id": safe_public_run_id(request.run_id),
        "provider_name": request.provider_name,
        "model_name": request.model_name,
        "runtime_mode": PROVIDER_ENVELOPE_PRECHECK_MODE,
        "env_key_name": SOLAR_PRO_3_ENV_KEY_NAME,
        "policy": {
            "request_timeout_seconds": int(policy.request_timeout_seconds or 0),
            "max_cost_units": int(policy.max_cost_units or 0),
            "max_live_api_calls": int(policy.max_live_api_calls or 0),
            "max_output_unit_budget": int(policy.max_output_tokens or 0),
            "retry_count": int(policy.retry_count),
        },
        "readiness": {
            "surface": SOLAR_PROVIDER_SURFACE,
            "required_control_count": len(LIVE_OPEN_REQUIRED_CONTROLS),
            "satisfied_control_count": len(LIVE_OPEN_REQUIRED_CONTROLS) - len(missing_controls),
            "missing_control_count": len(missing_controls),
            "missing_controls": missing_controls,
            "eligible_for_live_open": bool(
                getattr(live_open_decision, "eligible_for_live_open", False)
            ),
            "allowed_to_execute": bool(getattr(live_open_decision, "allowed_to_execute", False)),
        },
        "approval_target": {
            "prompt_contract_hash": request.prompt_contract_hash,
            "input_text_included": False,
            "provider_body_included": False,
            "auth_material_included": False,
        },
        "execution_boundary": {
            "sdk_imports": 0,
            "env_value_reads": 0,
            "api_calls": 0,
            "network_calls": 0,
            "solar_provider_calls": 0,
            "target_runtime_calls": 0,
        },
        "claim_boundary": {
            "scope": "local provider precheck policy summary",
            "external_provider_outcome": False,
            "target_runtime_outcome": False,
            "production_trust_claim": False,
        },
    }
    summary["policy_summary_hash"] = stable_contract_hash(summary)
    return _safe_public_payload(summary)


def provider_precheck_operator_policy_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the public policy summary an operator must approve."""
    request = _request_from_payload(payload)
    policy = _policy_from_payload(payload)
    decision = _ready_live_open_decision(payload, request.run_id)
    return _operator_policy_summary(
        request=request,
        policy=policy,
        live_open_decision=decision,
    )


def _operator_approval_missing_projection() -> JsonDict:
    return {
        "projection_version": OPERATOR_APPROVAL_ENVELOPE_VERSION,
        "status": "missing",
        "decision": "missing",
        "operator_ref": "",
        "approved_at": "",
        "policy_summary_hash": "",
        "envelope_hash": "",
        "auth_material_returned": False,
    }


def _operator_approval_projection(
    *,
    payload: dict[str, Any],
    policy_summary: JsonDict,
) -> tuple[JsonDict, list[JsonDict], list[str]]:
    approval_payload = payload.get("operator_approval")
    checks: list[JsonDict] = []
    errors: list[str] = []
    expected_hash = str(policy_summary.get("policy_summary_hash", ""))
    if not isinstance(approval_payload, dict):
        checks.append({"name": "operator_approval_envelope_present", "passed": False})
        errors.append("operator approval envelope is required before provider precheck.")
        return _operator_approval_missing_projection(), checks, errors

    operator_ref = str(approval_payload.get("operator_ref", "")).strip()
    approved_at = str(approval_payload.get("approved_at", "")).strip()
    decision = str(approval_payload.get("decision", "")).strip().lower()
    approved_hash = str(approval_payload.get("approved_policy_summary_hash", "")).strip()
    checks.extend(
        [
            {
                "name": "operator_approval_envelope_present",
                "passed": True,
            },
            {
                "name": "operator_approval_identity_present",
                "passed": bool(operator_ref),
            },
            {
                "name": "operator_approval_timestamp_present",
                "passed": bool(approved_at),
            },
            {
                "name": "operator_approval_decision_approved",
                "passed": decision == "approved",
            },
            {
                "name": "operator_approval_policy_summary_hash_match",
                "passed": bool(expected_hash) and approved_hash == expected_hash,
            },
        ]
    )
    if not operator_ref:
        errors.append("operator approval identity is required.")
    if not approved_at:
        errors.append("operator approval timestamp is required.")
    if decision != "approved":
        errors.append("operator approval decision must be approved.")
    if approved_hash != expected_hash:
        errors.append("operator approval must reference the exact policy summary hash.")

    status = "approved" if not errors else "blocked"
    envelope = {
        "projection_version": OPERATOR_APPROVAL_ENVELOPE_VERSION,
        "status": status,
        "decision": decision or "missing",
        "operator_ref": operator_ref,
        "approved_at": approved_at,
        "policy_summary_hash": expected_hash,
        "envelope_hash": stable_contract_hash(
            {
                "run_id": policy_summary.get("run_id", ""),
                "operator_ref": operator_ref,
                "approved_at": approved_at,
                "decision": decision,
                "policy_summary_hash": expected_hash,
            }
        )
        if operator_ref and approved_at and decision
        else "",
        "auth_material_returned": False,
    }
    return _safe_public_payload(envelope), checks, errors


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
    operator_policy_summary: JsonDict,
    operator_approval_envelope: JsonDict,
    live_provider_dry_admission: JsonDict,
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
            "operator_policy_summary": operator_policy_summary,
            "operator_approval_envelope": operator_approval_envelope,
            "live_provider_dry_admission": live_provider_dry_admission,
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
    policy = _policy_from_payload(payload)
    live_open_decision = _ready_live_open_decision(payload, request.run_id)
    operator_policy_summary = _operator_policy_summary(
        request=request,
        policy=policy,
        live_open_decision=live_open_decision,
    )
    operator_approval, operator_checks, operator_errors = _operator_approval_projection(
        payload=payload,
        policy_summary=operator_policy_summary,
    )
    live_provider_dry_admission = _live_provider_dry_admission_checklist(
        run_id=request.run_id,
        operator_policy_summary=operator_policy_summary,
        operator_approval_envelope=operator_approval,
    )
    if operator_errors:
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name=operator_checks[-1]["name"] if operator_checks else "operator_approval_blocked",
            message=operator_errors[0],
            operator_policy_summary=operator_policy_summary,
            operator_approval_envelope=operator_approval,
            live_provider_dry_admission=live_provider_dry_admission,
        )

    if not selected_provider.configured:
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_repository_configured",
            message="provider envelope repository is required before adapter admission.",
            operator_policy_summary=operator_policy_summary,
            operator_approval_envelope=operator_approval,
            live_provider_dry_admission=live_provider_dry_admission,
        )

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
            operator_policy_summary=operator_policy_summary,
            operator_approval_envelope=operator_approval,
            live_provider_dry_admission=live_provider_dry_admission,
        )

    try:
        repository = selected_provider.repository()
    except Exception:
        return _blocked_projection(
            run_id=request.run_id,
            repository_provider=selected_provider,
            check_name="provider_envelope_repository_available",
            message="provider envelope repository is unavailable.",
            operator_policy_summary=operator_policy_summary,
            operator_approval_envelope=operator_approval,
            live_provider_dry_admission=live_provider_dry_admission,
        )

    service = ProviderEnvelopeAdmissionService(repository)
    adapter = DisabledSolarPro3LiveAdapter(
        config=_adapter_config(policy),
        live_open_decision=live_open_decision,
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
        operator_policy_summary=operator_policy_summary,
        operator_approval_envelope=operator_approval,
        live_provider_dry_admission=live_provider_dry_admission,
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
            "operator_policy_summary": {},
            "operator_approval_envelope": {
                "projection_version": OPERATOR_APPROVAL_ENVELOPE_VERSION,
                "status": "not_applicable",
                "decision": "not_applicable",
                "operator_ref": "",
                "approved_at": "",
                "policy_summary_hash": "",
                "envelope_hash": "",
                "auth_material_returned": False,
            },
            "live_provider_dry_admission": _live_provider_dry_admission_checklist(
                run_id=run_id,
                operator_policy_summary=None,
                operator_approval_envelope={
                    "projection_version": OPERATOR_APPROVAL_ENVELOPE_VERSION,
                    "status": "not_applicable",
                    "decision": "not_applicable",
                    "operator_ref": "",
                    "approved_at": "",
                    "policy_summary_hash": "",
                    "envelope_hash": "",
                    "auth_material_returned": False,
                },
            ),
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
    "LIVE_PROVIDER_DRY_ADMISSION_VERSION",
    "provider_precheck_operator_policy_summary",
    "read_provider_envelope_precheck",
    "run_provider_envelope_precheck",
]

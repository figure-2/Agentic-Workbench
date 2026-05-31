"""Sanitized API demo wiring for fake provider/live admission.

The service exists to prove that API-facing paths can reuse
CanonicalApprovalPersistenceService before replay claim. It does not read
environment values, open provider SDKs, call live APIs, run DAACS, write files,
or expose raw approval authorization material.
"""

from __future__ import annotations

from dataclasses import fields
from typing import Any

from packages.core.approval_replay_factory import build_approval_replay_repositories
from packages.core.exposure import sanitize_public_payload
from packages.core.public_projection import assert_public_projection_safe
from packages.daacs_builder.approval_persistence import CanonicalApprovalPersistenceService
from packages.daacs_builder.approval_security import (
    ApprovalPolicyResolver,
    FakeApprovalVerifier,
    KeyIdentityRegistry,
    replay_store_from_approval_replay_repositories,
)
from packages.daacs_builder.live_runner import (
    live_approval_decision_record_for_request,
    live_replay_scope_for_request,
)
from packages.daacs_builder.provider_boundary import (
    FakeSolarProProvider,
    ProviderApprovalRecord,
    ProviderRequest,
    provider_approval_decision_record_for_request,
    provider_replay_scope_for_request,
)
from packages.daacs_builder.runner_provider import (
    ApprovalRecord,
    RunnerPlan,
    RunnerPolicy,
    RunnerRequest,
    default_runner_provider_registry,
)


ADMISSION_PROJECTION_VERSION = "approval-admission-public-v1"
DURABLE_APPROVAL_LIFECYCLE = "durable"


def _dataclass_payload(payload: dict[str, Any], cls: type) -> dict[str, Any]:
    allowed = {field.name for field in fields(cls)}
    return {key: value for key, value in payload.items() if key in allowed}


def _require_durable_approval_path(payload: dict[str, Any]) -> None:
    if payload.get("fixture_mode") is True:
        raise ValueError("fixture approval path cannot use canonical durable admission demo")
    if str(payload.get("approval_lifecycle") or "") != DURABLE_APPROVAL_LIFECYCLE:
        raise ValueError("durable approval lifecycle is required")


def _safe_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    public_payload = sanitize_public_payload(payload)
    if not isinstance(public_payload, dict):
        raise ValueError("admission public payload must be a mapping")
    assert_public_projection_safe(public_payload)
    return public_payload


def _result_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"name": str(check.get("name", "")), "passed": bool(check.get("passed"))}
        for check in checks
    ]


def _approval_projection(
    *,
    admission_kind: str,
    status: str,
    result_metrics: dict[str, Any],
    checks: list[dict[str, Any]],
    errors: list[str],
    expected_approval,
    saved_approval,
    replay_record_count: int,
) -> dict[str, Any]:
    hash_match = (
        saved_approval is not None
        and saved_approval.approval_hash == expected_approval.approval_hash
    )
    return _safe_public_payload(
        {
            "projection_version": ADMISSION_PROJECTION_VERSION,
            "admission_kind": admission_kind,
            "runtime_mode": "fake",
            "approval_lifecycle": DURABLE_APPROVAL_LIFECYCLE,
            "fixture_mode": False,
            "synthetic_approval": False,
            "durable_approval_path": True,
            "run_id": expected_approval.run_id,
            "status": status,
            "checks": _result_checks(checks),
            "errors": [str(error) for error in errors],
            "approval_persistence": {
                "service_used": True,
                "approval_row_present": saved_approval is not None,
                "approval_hash": expected_approval.approval_hash,
                "persisted_approval_hash": saved_approval.approval_hash if saved_approval else "",
                "subject_snapshot_id": expected_approval.subject_snapshot_id,
                "scope_canonical": expected_approval.scope_canonical,
                "hash_match": hash_match,
            },
            "replay": {
                "record_count": replay_record_count,
                "claim_count": int(result_metrics.get("approval_replay_store_claim_count", 0)),
                "hit_count": int(result_metrics.get("approval_replay_store_hit_count", 0)),
            },
            "execution_boundary": {
                "provider_calls": int(result_metrics.get("provider_calls", 0)),
                "live_api_calls": int(result_metrics.get("live_api_calls", 0)),
                "live_llm_calls": int(result_metrics.get("live_llm_calls", 0)),
                "network_calls": int(result_metrics.get("network_calls", 0)),
                "subprocess_calls": int(result_metrics.get("subprocess_calls", 0)),
                "filesystem_writes": int(result_metrics.get("filesystem_writes", 0)),
                "fake_provider_invocations": int(result_metrics.get("fake_provider_invocations", 0)),
                "fake_live_runtime_invocations": int(result_metrics.get("fake_live_runtime_invocations", 0)),
                "target_runtime_calls": int(result_metrics.get("real_daacs_invocations", 0)),
                "solar_provider_calls": int(result_metrics.get("solar_provider_calls", 0)),
            },
            "metrics": result_metrics,
            "claim_boundary": {
                "local_demo_only": True,
                "external_provider_outcome": False,
                "target_runtime_outcome": False,
                "production_trust_claim": False,
            },
        }
    )


def run_provider_admission_demo(payload: dict[str, Any]) -> dict[str, Any]:
    """Run fake provider admission through canonical approval persistence."""
    _require_durable_approval_path(payload)
    approval_payload = payload.get("approval")
    if not isinstance(approval_payload, dict):
        raise ValueError("provider approval payload is required")
    approval = ProviderApprovalRecord(**_dataclass_payload(approval_payload, ProviderApprovalRecord))
    request = ProviderRequest(
        run_id=str(payload["run_id"]),
        prompt_contract_hash=str(payload["prompt_contract_hash"]),
        provider_name=str(payload.get("provider_name", "solar-pro-3")),
        model_name=str(payload.get("model_name", "solar-pro-3")),
        mode=str(payload.get("mode", "fake")),
        env_key_name=str(payload.get("env_key_name", "UPSTAGE_API_KEY")),
        approval=approval,
    )

    repositories = build_approval_replay_repositories()
    approval_service = CanonicalApprovalPersistenceService(repositories.approval_repository)
    provider = FakeSolarProProvider(
        approval_verifier=FakeApprovalVerifier(),
        approval_policy_resolver=ApprovalPolicyResolver(),
        key_identity_registry=KeyIdentityRegistry(),
        replay_store=replay_store_from_approval_replay_repositories(repositories),
        approval_persistence_service=approval_service,
        require_approval_persistence=True,
    )
    result = provider.invoke(request)
    replay_scope = provider_replay_scope_for_request(request)
    expected_approval = provider_approval_decision_record_for_request(
        request,
        scope_canonical=replay_scope,
    )
    saved_approval = repositories.approval_repository.get_approval(expected_approval.approval_id)
    return _approval_projection(
        admission_kind="provider",
        status=result.status,
        result_metrics=result.metrics,
        checks=result.checks,
        errors=result.errors,
        expected_approval=expected_approval,
        saved_approval=saved_approval,
        replay_record_count=len(repositories.replay_nonce_repository.list_records()),
    )


def run_live_admission_demo(payload: dict[str, Any]) -> dict[str, Any]:
    """Run fake live admission through canonical approval persistence."""
    _require_durable_approval_path(payload)
    approval_payload = payload.get("approval")
    plan_payload = payload.get("plan")
    state_payload = payload.get("state")
    if not isinstance(approval_payload, dict):
        raise ValueError("live approval payload is required")
    if not isinstance(plan_payload, dict):
        raise ValueError("runner plan payload is required")
    if not isinstance(state_payload, dict):
        raise ValueError("runner state payload is required")

    approval = ApprovalRecord(**_dataclass_payload(approval_payload, ApprovalRecord))
    plan = RunnerPlan(**_dataclass_payload(plan_payload, RunnerPlan))
    policy_payload = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    policy = RunnerPolicy(**_dataclass_payload(policy_payload, RunnerPolicy))
    request = RunnerRequest(
        run_id=str(payload["run_id"]),
        mode="live",
        state=dict(state_payload),
        approval=approval,
        plan=plan,
        policy=policy,
    )

    repositories = build_approval_replay_repositories()
    approval_service = CanonicalApprovalPersistenceService(repositories.approval_repository)
    registry = default_runner_provider_registry(
        approval_replay_repositories=repositories,
        approval_persistence_service=approval_service,
        require_approval_persistence=True,
    )
    result = registry.run(request)
    replay_scope = live_replay_scope_for_request(request)
    expected_approval = live_approval_decision_record_for_request(
        request,
        scope_canonical=replay_scope,
    )
    saved_approval = repositories.approval_repository.get_approval(expected_approval.approval_id)
    return _approval_projection(
        admission_kind="live_runner",
        status=result.status,
        result_metrics=result.verification_report.metrics,
        checks=result.verification_report.checks,
        errors=result.verification_report.errors,
        expected_approval=expected_approval,
        saved_approval=saved_approval,
        replay_record_count=len(repositories.replay_nonce_repository.list_records()),
    )

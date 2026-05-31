"""LLM provider boundary skeleton for future Solar Pro 3 integration.

This module defines the provider contract and a fake Solar Pro 3 provider. It
does not read environment values, import provider SDKs, open network sockets, or
call live APIs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Protocol

from packages.core.exposure import sanitize_public_payload
from packages.core.repositories import (
    ApprovalDecisionRecord,
    ApprovalSubjectSnapshotRecord,
    approval_decision_record,
    approval_subject_snapshot_record,
    canonical_replay_scope,
)
from packages.core.schemas import JsonDict, stable_contract_hash

from .approval_security import (
    ApprovalPolicyResolver,
    ApprovalVerifier,
    ApprovalVerifierPolicy,
    KeyIdentityRegistry,
    PersistentReplayStore,
    claim_approval_replay,
    default_approval_replay_guard,
    enforce_resolved_approval_contract_policy,
    merge_verifier_metrics,
)
from .runner_provider import is_safe_run_id, safe_public_run_id


SOLAR_PRO_3_PROVIDER = "solar-pro-3"
SOLAR_PRO_3_MODEL = "solar-pro-3"
SOLAR_PRO_3_ENV_KEY_NAME = "UPSTAGE_API_KEY"
FAKE_PROVIDER_MODE = "fake"
PROVIDER_APPROVAL_SCOPE = "provider_boundary"
ENV_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,80}$")
CONTRACT_HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(slots=True)
class ProviderApprovalRecord:
    """Approval required before a provider boundary can be admitted."""

    approved_by: str
    approved_at: str
    run_id: str
    provider_name: str
    model_name: str
    mode: str
    env_key_name: str
    max_live_api_calls: int
    max_live_llm_calls: int
    expires_at: str
    audit_log_id: str
    signature_id: str = ""
    signed_contract_hash: str = ""
    nonce: str = ""
    verifier_id: str = ""
    key_id: str = ""
    verifier_scope: str = ""
    verifier_policy_id: str = ""
    key_identity_id: str = ""


@dataclass(slots=True)
class ProviderRequest:
    """Provider invocation envelope that carries contract hashes only."""

    run_id: str
    prompt_contract_hash: str
    provider_name: str = SOLAR_PRO_3_PROVIDER
    model_name: str = SOLAR_PRO_3_MODEL
    mode: str = FAKE_PROVIDER_MODE
    env_key_name: str = SOLAR_PRO_3_ENV_KEY_NAME
    approval: ProviderApprovalRecord | None = None
    metadata: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class ProviderResult:
    """Sanitized provider boundary result."""

    run_id: str
    provider_name: str
    model_name: str
    status: str
    checks: list[JsonDict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    output_contract: JsonDict = field(default_factory=dict)
    metrics: JsonDict = field(default_factory=dict)
    audit_events: list[JsonDict] = field(default_factory=list)

    def to_dict(self) -> JsonDict:
        return sanitize_public_payload(asdict(self))


class LLMProvider(Protocol):
    """Minimal provider contract used by live-capable future boundaries."""

    provider_name: str

    def invoke(self, request: ProviderRequest) -> ProviderResult:
        """Return a provider result or a blocked boundary result."""


def zero_provider_side_effect_metrics() -> dict[str, int]:
    return {
        "live_llm_calls": 0,
        "live_api_calls": 0,
        "provider_calls": 0,
        "provider_imports": 0,
        "provider_secret_value_reads": 0,
        "network_calls": 0,
        "fake_provider_invocations": 0,
        "provider_boundary_block_count": 0,
        "approval_bypass_count": 0,
        "approval_signature_valid_count": 0,
        "approval_replay_mark_count": 0,
        "approval_replay_block_count": 0,
        "approval_replay_store_claim_count": 0,
        "approval_replay_store_hit_count": 0,
        "approval_replay_store_persisted_record_count": 0,
        "approval_verifier_missing_block_count": 0,
        "approval_verifier_fake_count": 0,
        "approval_verifier_secret_value_reads": 0,
        "approval_verifier_key_file_reads": 0,
        "approval_verifier_network_calls": 0,
        "approval_verifier_policy_check_count": 0,
        "approval_verifier_policy_valid_count": 0,
        "approval_verifier_policy_block_count": 0,
        "approval_verifier_identity_block_count": 0,
        "approval_verifier_key_block_count": 0,
        "approval_verifier_scope_block_count": 0,
        "approval_verifier_skew_block_count": 0,
        "approval_policy_resolver_check_count": 0,
        "approval_policy_resolver_valid_count": 0,
        "approval_policy_resolver_block_count": 0,
        "approval_policy_resolver_missing_block_count": 0,
        "approval_policy_unknown_block_count": 0,
        "key_identity_registry_check_count": 0,
        "key_identity_registry_valid_count": 0,
        "key_identity_registry_block_count": 0,
        "key_identity_registry_missing_block_count": 0,
        "key_identity_revoked_block_count": 0,
        "policy_key_mismatch_block_count": 0,
    }


def _metrics(extra: dict[str, Any] | None = None) -> JsonDict:
    return {
        **zero_provider_side_effect_metrics(),
        "provider_boundary_mode": FAKE_PROVIDER_MODE,
        "env_key_name_reference_count": 0,
        **(extra or {}),
    }


def _parse_aware_timestamp(
    value: str,
    *,
    field_name: str,
    failures: list[tuple[str, str]],
) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        failures.append(("provider_approval_valid", f"{field_name} is required."))
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        failures.append(("provider_approval_valid", f"{field_name} must be ISO-8601."))
        return None
    if parsed.tzinfo is None:
        failures.append(("provider_approval_valid", f"{field_name} must include timezone."))
        return None
    return parsed.astimezone(timezone.utc)


def _env_key_name_valid(env_key_name: str) -> bool:
    return isinstance(env_key_name, str) and ENV_KEY_PATTERN.fullmatch(env_key_name) is not None


def _request_shape_failures(request: ProviderRequest) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    if not is_safe_run_id(request.run_id):
        failures.append(("provider_run_id_valid", "run_id contains unsupported characters."))
    if request.provider_name != SOLAR_PRO_3_PROVIDER:
        failures.append(("provider_name_supported", "provider_name must be solar-pro-3."))
    if request.model_name != SOLAR_PRO_3_MODEL:
        failures.append(("provider_model_supported", "model_name must be solar-pro-3."))
    if request.mode != FAKE_PROVIDER_MODE:
        failures.append(("provider_mode_fake", "provider mode must remain fake."))
    if request.env_key_name != SOLAR_PRO_3_ENV_KEY_NAME or not _env_key_name_valid(
        request.env_key_name
    ):
        failures.append(("provider_env_key_name_valid", "env_key_name must be UPSTAGE_API_KEY."))
    if not isinstance(request.prompt_contract_hash, str) or not CONTRACT_HASH_PATTERN.fullmatch(
        request.prompt_contract_hash
    ):
        failures.append(("provider_prompt_contract_hash_valid", "prompt_contract_hash must be a contract hash."))
    return failures


def validate_provider_request(request: ProviderRequest) -> list[tuple[str, str]]:
    """Return sanitized provider gate failures."""
    failures = _request_shape_failures(request)
    approval = request.approval
    if approval is None:
        failures.append(("provider_approval_present", "provider boundary requires approval."))
        return failures
    if not isinstance(approval, ProviderApprovalRecord):
        failures.append(("provider_approval_valid", "provider approval must be ProviderApprovalRecord."))
        return failures

    if not isinstance(approval.approved_by, str) or not approval.approved_by.strip():
        failures.append(("provider_approval_valid", "approved_by is required."))
    if approval.run_id != request.run_id:
        failures.append(("provider_approval_valid", "approval run_id must match request run_id."))
    if approval.provider_name != request.provider_name:
        failures.append(("provider_approval_valid", "approval provider_name must match request provider_name."))
    if approval.model_name != request.model_name:
        failures.append(("provider_approval_valid", "approval model_name must match request model_name."))
    if approval.mode != FAKE_PROVIDER_MODE:
        failures.append(("provider_approval_valid", "approval mode must remain fake."))
    if approval.env_key_name != request.env_key_name:
        failures.append(("provider_approval_valid", "approval env_key_name must match request env_key_name."))
    if type(approval.max_live_api_calls) is not int or approval.max_live_api_calls != 0:
        failures.append(("provider_approval_valid", "max_live_api_calls must be explicit zero."))
    if type(approval.max_live_llm_calls) is not int or approval.max_live_llm_calls != 0:
        failures.append(("provider_approval_valid", "max_live_llm_calls must be explicit zero."))

    approved_at = _parse_aware_timestamp(
        approval.approved_at,
        field_name="approved_at",
        failures=failures,
    )
    expires_at = _parse_aware_timestamp(
        approval.expires_at,
        field_name="expires_at",
        failures=failures,
    )
    if approved_at is not None and expires_at is not None:
        if expires_at <= approved_at:
            failures.append(("provider_approval_valid", "expires_at must be after approved_at."))
        if expires_at <= datetime.now(timezone.utc):
            failures.append(("provider_approval_valid", "provider approval is expired."))

    if not isinstance(approval.audit_log_id, str) or not approval.audit_log_id.strip():
        failures.append(("provider_audit_configured", "audit_log_id is required."))
    return failures


def provider_approval_subject_for_request(request: ProviderRequest) -> JsonDict:
    """Return the provider approval subject without authorization material."""
    if request.approval is None:
        raise ValueError("provider approval is required")
    return {
        "run_id": request.run_id,
        "prompt_contract_hash": request.prompt_contract_hash,
        "provider_name": request.provider_name,
        "model_name": request.model_name,
        "mode": request.mode,
        "env_key_name": request.env_key_name,
        "max_live_api_calls": request.approval.max_live_api_calls,
        "max_live_llm_calls": request.approval.max_live_llm_calls,
    }


def provider_subject_hash_for_request(request: ProviderRequest) -> str:
    """Hash the provider approval subject without authorization material."""
    return stable_contract_hash(provider_approval_subject_for_request(request))


def provider_replay_scope_for_request(request: ProviderRequest) -> str:
    """Return the canonical provider replay scope for signature and nonce gates."""
    return canonical_replay_scope(
        approval_type="provider_approval",
        run_id=request.run_id,
        subject_hash=provider_subject_hash_for_request(request),
    )


def provider_approval_decision_hash(request: ProviderRequest, *, scope_canonical: str) -> str:
    """Hash the approval decision without nonce/signature/key material."""
    return provider_approval_decision_record_for_request(
        request,
        scope_canonical=scope_canonical,
    ).approval_hash


def provider_approval_subject_snapshot_for_request(
    request: ProviderRequest,
    *,
    scope_canonical: str,
) -> ApprovalSubjectSnapshotRecord:
    """Build the canonical provider approval snapshot row."""
    if request.approval is None:
        raise ValueError("provider approval is required")
    return approval_subject_snapshot_record(
        approval_type="provider_approval",
        run_id=request.run_id,
        subject_kind="provider_request",
        subject=provider_approval_subject_for_request(request),
        subject_schema_version="provider-approval-subject-v1",
        lifecycle_class="durable",
        scope_canonical=scope_canonical,
        sanitized_summary="provider approval subject hash-only snapshot",
        created_at=request.approval.approved_at,
    )


def provider_approval_decision_record_for_request(
    request: ProviderRequest,
    *,
    scope_canonical: str,
) -> ApprovalDecisionRecord:
    """Build the canonical provider approval decision row."""
    if request.approval is None:
        raise ValueError("provider approval is required")
    snapshot = provider_approval_subject_snapshot_for_request(
        request,
        scope_canonical=scope_canonical,
    )
    approval_id = stable_contract_hash(
        {
            "approval_type": "provider_approval",
            "run_id": request.run_id,
            "scope_canonical": scope_canonical,
            "audit_log_id": request.approval.audit_log_id,
            "approved_at": request.approval.approved_at,
        }
    )
    return approval_decision_record(
        approval_id=f"approval-{approval_id[:24]}",
        snapshot=snapshot,
        decision="approved",
        approved_by_ref=request.approval.approved_by,
        approver_role="provider_boundary",
        approved_at=request.approval.approved_at,
        expires_at=request.approval.expires_at,
        policy_id_ref=request.approval.verifier_policy_id,
        key_identity_ref=request.approval.key_identity_id,
        audit_log_id=request.approval.audit_log_id,
        lifecycle_class="durable",
        created_at=request.approval.approved_at,
    )


def _blocked_result(request: ProviderRequest, failures: list[tuple[str, str]]) -> ProviderResult:
    result_run_id = safe_public_run_id(request.run_id)
    check_name = failures[0][0] if failures else "provider_boundary_blocked"
    errors = [message for _, message in failures] or ["provider boundary blocked."]
    return ProviderResult(
        run_id=result_run_id,
        provider_name=request.provider_name,
        model_name=request.model_name,
        status="blocked",
        checks=[{"name": check_name, "passed": False}],
        errors=errors,
        output_contract={},
        metrics=_metrics(
            {
                "provider_boundary_block_count": 1,
                "approval_bypass_count": 1,
            }
        ),
        audit_events=[
            {
                "event": "provider_boundary_blocked",
                "run_id": result_run_id,
                "provider_name": request.provider_name,
                "failed_gate": check_name,
            }
        ],
    )


class FakeSolarProProvider:
    """Solar Pro 3 provider skeleton that never performs a live call."""

    provider_name = SOLAR_PRO_3_PROVIDER

    def __init__(
        self,
        *,
        approval_verifier: ApprovalVerifier | None = None,
        approval_verifier_policy: ApprovalVerifierPolicy | None = None,
        approval_policy_resolver: ApprovalPolicyResolver | None = None,
        key_identity_registry: KeyIdentityRegistry | None = None,
        replay_store: PersistentReplayStore | None = None,
        replay_guard: PersistentReplayStore | None = None,
        approval_persistence_service: Any | None = None,
        require_approval_persistence: bool = False,
    ) -> None:
        self.approval_verifier = approval_verifier
        self.approval_verifier_policy = approval_verifier_policy
        if approval_policy_resolver is not None:
            self.approval_policy_resolver = approval_policy_resolver
        elif approval_verifier_policy is not None:
            self.approval_policy_resolver = ApprovalPolicyResolver([approval_verifier_policy])
        else:
            self.approval_policy_resolver = None
        self.key_identity_registry = key_identity_registry
        self.replay_store = replay_store or replay_guard or default_approval_replay_guard()
        self.approval_persistence_service = approval_persistence_service
        self.require_approval_persistence = require_approval_persistence

    def invoke(self, request: ProviderRequest) -> ProviderResult:
        failures = validate_provider_request(request)
        if failures:
            return _blocked_result(request, failures)

        if self.approval_verifier is None:
            result = _blocked_result(
                request,
                [("provider_approval_verifier_present", "approval verifier is required.")],
            )
            result.metrics["approval_verifier_missing_block_count"] = 1
            return result

        replay_scope = provider_replay_scope_for_request(request)
        approval_hash = provider_approval_decision_hash(
            request,
            scope_canonical=replay_scope,
        )

        try:
            verification = self.approval_verifier.verify(
                request.approval,
                scope=replay_scope,
                gate_prefix="provider_approval",
            )
        except Exception:
            result = _blocked_result(
                request,
                [("provider_approval_verifier_available", "approval verifier is unavailable.")],
            )
            result.metrics["approval_verifier_missing_block_count"] = 1
            return result
        if verification.failures:
            result = _blocked_result(request, verification.failures)
            result.metrics.update(verification.metrics)
            return result

        if self.approval_policy_resolver is None:
            result = _blocked_result(
                request,
                [("provider_approval_policy_resolver_present", "approval policy resolver is required.")],
            )
            result.metrics.update(verification.metrics)
            result.metrics["approval_policy_resolver_missing_block_count"] = 1
            return result

        if self.key_identity_registry is None:
            result = _blocked_result(
                request,
                [("provider_approval_key_identity_registry_present", "key identity registry is required.")],
            )
            result.metrics.update(verification.metrics)
            result.metrics["key_identity_registry_missing_block_count"] = 1
            return result

        policy_verification = enforce_resolved_approval_contract_policy(
            request.approval,
            scope=replay_scope,
            gate_prefix="provider_approval",
            policy_resolver=self.approval_policy_resolver,
            key_identity_registry=self.key_identity_registry,
        )
        verification_metrics = merge_verifier_metrics(
            verification.metrics,
            policy_verification.metrics,
        )
        if policy_verification.failures:
            result = _blocked_result(request, policy_verification.failures)
            result.metrics.update(verification_metrics)
            return result

        persistence_metrics: dict[str, int] = {}
        if self.approval_persistence_service is not None:
            try:
                persistence_result = self.approval_persistence_service.persist_provider_approval(
                    request
                )
            except Exception:
                result = _blocked_result(
                    request,
                    [
                        (
                            "provider_approval_persistence_available",
                            "approval persistence service is unavailable.",
                        )
                    ],
                )
                result.metrics.update(verification_metrics)
                result.metrics["approval_persistence_block_count"] = 1
                return result
            persistence_metrics = dict(getattr(persistence_result, "metrics", {}))
            if getattr(persistence_result, "approval_hash", "") != approval_hash:
                result = _blocked_result(
                    request,
                    [
                        (
                            "provider_approval_persistence_hash_match",
                            "persisted approval hash does not match the canonical provider approval.",
                        )
                    ],
                )
                result.metrics.update(verification_metrics)
                result.metrics.update(persistence_metrics)
                result.metrics["approval_persistence_block_count"] = 1
                return result
        elif self.require_approval_persistence:
            result = _blocked_result(
                request,
                [
                    (
                        "provider_approval_persistence_service_present",
                        "approval persistence service is required.",
                    )
                ],
            )
            result.metrics.update(verification_metrics)
            result.metrics["approval_persistence_missing_block_count"] = 1
            return result

        replay_failures = claim_approval_replay(
            request.approval,
            scope=replay_scope,
            gate_prefix="provider_approval",
            replay_store=self.replay_store,
            approval_hash=approval_hash,
            run_id=request.run_id,
            approval_type="provider_approval",
            expires_at=request.approval.expires_at,
        )
        if replay_failures:
            result = _blocked_result(request, replay_failures)
            result.metrics.update(verification_metrics)
            result.metrics.update(persistence_metrics)
            result.metrics["approval_replay_block_count"] = 1
            result.metrics["approval_replay_store_hit_count"] = 1
            return result

        output_contract = {
            "provider_name": request.provider_name,
            "model_name": request.model_name,
            "mode": request.mode,
            "env_key_name": request.env_key_name,
            "prompt_contract_hash": request.prompt_contract_hash,
            "response_kind": "fake_provider_contract",
            "content_hash": stable_contract_hash(
                {
                    "provider_name": request.provider_name,
                    "model_name": request.model_name,
                    "prompt_contract_hash": request.prompt_contract_hash,
                    "mode": request.mode,
                }
            ),
        }
        result = ProviderResult(
            run_id=request.run_id,
            provider_name=request.provider_name,
            model_name=request.model_name,
            status="passed",
            checks=[
                {"name": "provider_approval_present", "passed": True},
                {"name": "provider_approval_valid", "passed": True},
                {"name": "provider_mode_fake", "passed": True},
                {"name": "provider_env_key_name_only", "passed": True},
                {"name": "provider_live_calls_zero", "passed": True},
                {"name": "provider_approval_signature_valid", "passed": True},
                {"name": "provider_approval_replay_fresh", "passed": True},
            ],
            errors=[],
            output_contract=output_contract,
            metrics=_metrics(
                {
                    "fake_provider_invocations": 1,
                    "env_key_name_reference_count": 1,
                    "approval_signature_valid_count": 1,
                    "approval_replay_mark_count": 1,
                    "approval_replay_store_claim_count": 1,
                    "approval_replay_store_persisted_record_count": len(
                        self.replay_store.export_records()
                    ),
                    **persistence_metrics,
                    **verification_metrics,
                }
            ),
            audit_events=[
                {
                    "event": "fake_solar_provider_contract_verified",
                    "run_id": request.run_id,
                    "provider_name": request.provider_name,
                    "model_name": request.model_name,
                    "approval_hash": approval_hash,
                    "prompt_contract_hash": request.prompt_contract_hash,
                    "env_key_name": request.env_key_name,
                }
            ],
        )
        return result

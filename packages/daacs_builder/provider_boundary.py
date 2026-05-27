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
from packages.core.schemas import JsonDict, stable_contract_hash

from .runner_provider import is_safe_run_id, safe_public_run_id


SOLAR_PRO_3_PROVIDER = "solar-pro-3"
SOLAR_PRO_3_MODEL = "solar-pro-3"
SOLAR_PRO_3_ENV_KEY_NAME = "UPSTAGE_API_KEY"
FAKE_PROVIDER_MODE = "fake"
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

    def invoke(self, request: ProviderRequest) -> ProviderResult:
        failures = validate_provider_request(request)
        if failures:
            return _blocked_result(request, failures)

        approval_payload = asdict(request.approval)
        approval_hash = stable_contract_hash(approval_payload)
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
        return ProviderResult(
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
            ],
            errors=[],
            output_contract=output_contract,
            metrics=_metrics(
                {
                    "fake_provider_invocations": 1,
                    "env_key_name_reference_count": 1,
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

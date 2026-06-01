"""Disabled-by-default Solar Pro 3 live adapter skeleton.

This adapter defines the shape of a future Solar Pro 3 live provider path while
keeping execution closed. It never reads environment values, imports provider
SDKs, opens network sockets, or performs a live API call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.core.live_open_policy import (
    SOLAR_PROVIDER_SURFACE,
    LiveOpenDecision,
)
from packages.core.schemas import JsonDict

from .provider_boundary import (
    CONTRACT_HASH_PATTERN,
    SOLAR_PRO_3_ENV_KEY_NAME,
    SOLAR_PRO_3_MODEL,
    SOLAR_PRO_3_PROVIDER,
    ProviderApprovalRecord,
    ProviderRequest,
    ProviderResult,
    zero_provider_side_effect_metrics,
)
from .runner_provider import is_safe_run_id, safe_public_run_id


SOLAR_LIVE_ADAPTER_MODE = "live"
SOLAR_LIVE_ADAPTER_ID = "solar-pro-3-live-disabled-v1"


@dataclass(frozen=True, slots=True)
class SolarPro3LiveAdapterConfig:
    """Configuration required before the real provider path can be proposed."""

    enabled: bool = False
    env_key_name: str = SOLAR_PRO_3_ENV_KEY_NAME
    request_timeout_seconds: int | None = None
    max_cost_units: int | None = None
    max_output_tokens: int | None = None
    max_live_api_calls: int | None = None
    allow_network: bool = False
    adapter_id: str = SOLAR_LIVE_ADAPTER_ID


@dataclass(frozen=True, slots=True)
class ProviderAdapterRegistry:
    """Small registry for disabled/fake provider adapter selection tests."""

    adapters: dict[tuple[str, str], Any] = field(default_factory=dict)

    def register(self, provider_name: str, mode: str, adapter: Any) -> "ProviderAdapterRegistry":
        if not provider_name or not mode:
            raise ValueError("provider_name and mode are required")
        self.adapters[(provider_name, mode)] = adapter
        return self

    def resolve(self, provider_name: str, mode: str) -> Any | None:
        return self.adapters.get((provider_name, mode))


def _metrics(extra: dict[str, Any] | None = None) -> JsonDict:
    return {
        **zero_provider_side_effect_metrics(),
        "adapter_id": SOLAR_LIVE_ADAPTER_ID,
        "adapter_mode": SOLAR_LIVE_ADAPTER_MODE,
        "solar_live_adapter_registered_count": 0,
        "solar_live_adapter_block_count": 0,
        "solar_live_adapter_enabled": False,
        "solar_live_policy_checked": False,
        "solar_live_execution_permission": False,
        "solar_live_sdk_imports": 0,
        "solar_live_env_value_reads": 0,
        "solar_live_api_calls": 0,
        **(extra or {}),
    }


def _check(
    checks: list[JsonDict],
    failures: list[tuple[str, str]],
    *,
    name: str,
    passed: bool,
    message: str,
) -> None:
    checks.append({"name": name, "passed": bool(passed)})
    if not passed:
        failures.append((name, message))


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def _blocked_result(
    request: ProviderRequest,
    *,
    checks: list[JsonDict],
    failures: list[tuple[str, str]],
    config: SolarPro3LiveAdapterConfig,
) -> ProviderResult:
    reason = failures[0][0] if failures else "solar_live_adapter_blocked"
    return ProviderResult(
        run_id=safe_public_run_id(request.run_id),
        provider_name=request.provider_name,
        model_name=request.model_name,
        status="blocked",
        checks=checks or [{"name": reason, "passed": False}],
        errors=[message for _, message in failures] or ["solar live adapter blocked."],
        output_contract={},
        metrics=_metrics(
            {
                "solar_live_adapter_registered_count": 1,
                "solar_live_adapter_block_count": 1,
                "solar_live_adapter_enabled": bool(config.enabled),
                "env_key_name_reference_count": 1 if config.env_key_name == SOLAR_PRO_3_ENV_KEY_NAME else 0,
            }
        ),
        audit_events=[
            {
                "event": "solar_live_adapter_blocked",
                "run_id": safe_public_run_id(request.run_id),
                "provider_name": request.provider_name,
                "adapter_id": config.adapter_id,
                "failed_gate": reason,
            }
        ],
    )


class DisabledSolarPro3LiveAdapter:
    """Real-path adapter skeleton that remains closed until a later unit."""

    provider_name = SOLAR_PRO_3_PROVIDER

    def __init__(
        self,
        *,
        config: SolarPro3LiveAdapterConfig | None = None,
        live_open_decision: LiveOpenDecision | None = None,
    ) -> None:
        self.config = config or SolarPro3LiveAdapterConfig()
        self.live_open_decision = live_open_decision

    def invoke(self, request: ProviderRequest) -> ProviderResult:
        checks: list[JsonDict] = []
        failures: list[tuple[str, str]] = []

        _check(
            checks,
            failures,
            name="solar_live_adapter_enabled",
            passed=self.config.enabled is True,
            message="Solar live adapter is disabled by default.",
        )
        _check(
            checks,
            failures,
            name="solar_live_mode_live",
            passed=request.mode == SOLAR_LIVE_ADAPTER_MODE,
            message="Solar live adapter accepts only live mode; fake mode must use FakeSolarProProvider.",
        )
        _check(
            checks,
            failures,
            name="solar_live_run_id_safe",
            passed=is_safe_run_id(request.run_id),
            message="run_id contains unsupported characters.",
        )
        _check(
            checks,
            failures,
            name="solar_live_provider_supported",
            passed=request.provider_name == SOLAR_PRO_3_PROVIDER,
            message="provider_name must be solar-pro-3.",
        )
        _check(
            checks,
            failures,
            name="solar_live_model_supported",
            passed=request.model_name == SOLAR_PRO_3_MODEL,
            message="model_name must be solar-pro-3.",
        )
        _check(
            checks,
            failures,
            name="solar_live_prompt_contract_hash_valid",
            passed=isinstance(request.prompt_contract_hash, str)
            and CONTRACT_HASH_PATTERN.fullmatch(request.prompt_contract_hash) is not None,
            message="prompt_contract_hash must be a contract hash.",
        )
        _check(
            checks,
            failures,
            name="solar_live_env_key_name_only",
            passed=request.env_key_name == SOLAR_PRO_3_ENV_KEY_NAME
            and self.config.env_key_name == SOLAR_PRO_3_ENV_KEY_NAME,
            message="Solar live adapter may reference only the UPSTAGE_API_KEY name.",
        )
        _check(
            checks,
            failures,
            name="solar_live_approval_present",
            passed=isinstance(request.approval, ProviderApprovalRecord),
            message="provider approval is required before Solar live adapter admission.",
        )
        if isinstance(request.approval, ProviderApprovalRecord):
            _check(
                checks,
                failures,
                name="solar_live_approval_mode_live",
                passed=request.approval.mode == SOLAR_LIVE_ADAPTER_MODE,
                message="provider approval mode must be live for the real adapter path.",
            )
        _check(
            checks,
            failures,
            name="solar_live_timeout_configured",
            passed=_positive_int(self.config.request_timeout_seconds),
            message="request timeout must be configured before live provider work.",
        )
        _check(
            checks,
            failures,
            name="solar_live_cost_quota_configured",
            passed=_positive_int(self.config.max_cost_units)
            and _positive_int(self.config.max_live_api_calls),
            message="cost and live API quota must be configured before live provider work.",
        )
        _check(
            checks,
            failures,
            name="solar_live_token_quota_configured",
            passed=_positive_int(self.config.max_output_tokens),
            message="token quota must be configured before live provider work.",
        )
        _check(
            checks,
            failures,
            name="solar_live_network_not_opened",
            passed=self.config.allow_network is False,
            message="network remains closed in AW-LIVE-01.",
        )

        decision = self.live_open_decision
        _check(
            checks,
            failures,
            name="solar_live_open_policy_present",
            passed=isinstance(decision, LiveOpenDecision),
            message="live-open policy decision is required.",
        )
        if isinstance(decision, LiveOpenDecision):
            _check(
                checks,
                failures,
                name="solar_live_open_policy_surface",
                passed=decision.surface == SOLAR_PROVIDER_SURFACE,
                message="live-open policy decision must target solar_provider.",
            )
            _check(
                checks,
                failures,
                name="solar_live_open_policy_eligible",
                passed=decision.eligible_for_live_open is True,
                message="live-open policy decision must be eligible.",
            )
            _check(
                checks,
                failures,
                name="solar_live_execution_permission_closed",
                passed=decision.allowed_to_execute is True,
                message="AW-LIVE-01 does not grant provider execution permission.",
            )

        _check(
            checks,
            failures,
            name="solar_live_provider_call_not_implemented",
            passed=False,
            message="Solar Pro 3 live API invocation is not implemented in AW-LIVE-01.",
        )
        return _blocked_result(request, checks=checks, failures=failures, config=self.config)


def default_solar_provider_adapter_registry() -> ProviderAdapterRegistry:
    """Return a registry with the disabled live adapter registered."""
    return ProviderAdapterRegistry().register(
        SOLAR_PRO_3_PROVIDER,
        SOLAR_LIVE_ADAPTER_MODE,
        DisabledSolarPro3LiveAdapter(),
    )


__all__ = [
    "DisabledSolarPro3LiveAdapter",
    "ProviderAdapterRegistry",
    "SOLAR_LIVE_ADAPTER_ID",
    "SOLAR_LIVE_ADAPTER_MODE",
    "SolarPro3LiveAdapterConfig",
    "default_solar_provider_adapter_registry",
]

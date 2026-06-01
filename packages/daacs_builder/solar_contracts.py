"""Solar Pro 3 no-call request/response contract fixtures.

These helpers define the sanitized request and response projections required
before a future Solar Pro 3 adapter can be opened. They never read environment
values, import provider SDKs, open network sockets, or call external APIs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from packages.core.exposure import sanitize_public_payload
from packages.core.schemas import JsonDict, stable_contract_hash

from .provider_boundary import (
    CONTRACT_HASH_PATTERN,
    SOLAR_PRO_3_ENV_KEY_NAME,
    SOLAR_PRO_3_MODEL,
    SOLAR_PRO_3_PROVIDER,
    ProviderRequest,
)
from .runner_provider import is_safe_run_id, safe_public_run_id
from .solar_live_adapter import SOLAR_LIVE_ADAPTER_MODE


SOLAR_CONTRACT_VERSION = "solar-pro-3-contract-fixture-v1"


@dataclass(frozen=True, slots=True)
class SolarCostTimeoutPolicy:
    """No-call policy values required before request contracts are admitted."""

    request_timeout_seconds: int | None = None
    max_cost_units: int | None = None
    max_live_api_calls: int | None = None
    max_output_tokens: int | None = None
    retry_count: int = 0


@dataclass(frozen=True, slots=True)
class SolarRequestContractFixture:
    """Sanitized request projection based on prompt contract hash only."""

    version: str
    run_id: str
    provider_name: str
    model_name: str
    mode: str
    env_key_name: str
    prompt_contract_hash: str
    request_contract_hash: str
    request_body_kind: str
    timeout_seconds: int
    cost_unit_budget: int
    live_api_call_budget: int
    output_token_budget: int
    retry_count: int
    input_text_included: bool = False
    provider_body_included: bool = False

    def to_dict(self) -> JsonDict:
        return sanitize_public_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class SolarResponseProjectionFixture:
    """Sanitized response projection fixture with no provider body."""

    version: str
    run_id: str
    provider_name: str
    model_name: str
    status: str
    response_kind: str
    response_summary: str
    response_contract_hash: str
    content_hash: str
    source_body_included: bool = False
    provider_body_included: bool = False

    def to_dict(self) -> JsonDict:
        return sanitize_public_payload(asdict(self))


@dataclass(frozen=True, slots=True)
class SolarContractFixtureResult:
    """Blocked or admitted contract fixture result."""

    status: str
    checks: list[JsonDict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    request_contract: JsonDict = field(default_factory=dict)
    response_projection: JsonDict = field(default_factory=dict)
    metrics: JsonDict = field(default_factory=dict)

    def to_dict(self) -> JsonDict:
        return sanitize_public_payload(asdict(self))


def zero_solar_contract_metrics(extra: dict[str, Any] | None = None) -> JsonDict:
    return {
        "solar_contract_policy_check_count": 0,
        "solar_contract_policy_block_count": 0,
        "solar_request_contract_created_count": 0,
        "solar_response_projection_created_count": 0,
        "solar_contract_input_text_count": 0,
        "solar_contract_source_body_count": 0,
        "solar_contract_provider_body_count": 0,
        "solar_contract_env_value_reads": 0,
        "solar_contract_sdk_imports": 0,
        "solar_contract_api_calls": 0,
        "solar_contract_network_calls": 0,
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


def validate_solar_cost_timeout_policy(
    policy: SolarCostTimeoutPolicy,
) -> tuple[list[JsonDict], list[tuple[str, str]]]:
    """Return checks and failures for the no-call cost/timeout policy."""
    checks: list[JsonDict] = []
    failures: list[tuple[str, str]] = []
    _check(
        checks,
        failures,
        name="solar_contract_timeout_configured",
        passed=_positive_int(policy.request_timeout_seconds),
        message="request timeout must be configured.",
    )
    _check(
        checks,
        failures,
        name="solar_contract_cost_budget_configured",
        passed=_positive_int(policy.max_cost_units),
        message="cost budget must be configured.",
    )
    _check(
        checks,
        failures,
        name="solar_contract_api_quota_configured",
        passed=_positive_int(policy.max_live_api_calls),
        message="live API call quota must be configured.",
    )
    _check(
        checks,
        failures,
        name="solar_contract_output_token_quota_configured",
        passed=_positive_int(policy.max_output_tokens),
        message="output token quota must be configured.",
    )
    _check(
        checks,
        failures,
        name="solar_contract_retry_policy_non_negative",
        passed=type(policy.retry_count) is int and policy.retry_count >= 0,
        message="retry_count must be a non-negative integer.",
    )
    return checks, failures


def _validate_request_shape(
    request: ProviderRequest,
    checks: list[JsonDict],
    failures: list[tuple[str, str]],
) -> None:
    _check(
        checks,
        failures,
        name="solar_contract_run_id_safe",
        passed=is_safe_run_id(request.run_id),
        message="run_id contains unsupported characters.",
    )
    _check(
        checks,
        failures,
        name="solar_contract_provider_supported",
        passed=request.provider_name == SOLAR_PRO_3_PROVIDER,
        message="provider_name must be solar-pro-3.",
    )
    _check(
        checks,
        failures,
        name="solar_contract_model_supported",
        passed=request.model_name == SOLAR_PRO_3_MODEL,
        message="model_name must be solar-pro-3.",
    )
    _check(
        checks,
        failures,
        name="solar_contract_mode_live",
        passed=request.mode == SOLAR_LIVE_ADAPTER_MODE,
        message="request contract fixtures are only for the live adapter path.",
    )
    _check(
        checks,
        failures,
        name="solar_contract_env_key_name_only",
        passed=request.env_key_name == SOLAR_PRO_3_ENV_KEY_NAME,
        message="request contract may reference only the UPSTAGE_API_KEY name.",
    )
    _check(
        checks,
        failures,
        name="solar_contract_prompt_hash_valid",
        passed=isinstance(request.prompt_contract_hash, str)
        and CONTRACT_HASH_PATTERN.fullmatch(request.prompt_contract_hash) is not None,
        message="prompt_contract_hash must be a contract hash.",
    )


def _blocked_result(checks: list[JsonDict], failures: list[tuple[str, str]]) -> SolarContractFixtureResult:
    return SolarContractFixtureResult(
        status="blocked",
        checks=checks,
        errors=[message for _, message in failures],
        request_contract={},
        response_projection={},
        metrics=zero_solar_contract_metrics(
            {
                "solar_contract_policy_check_count": len(checks),
                "solar_contract_policy_block_count": 1,
            }
        ),
    )


def build_solar_request_contract_fixture(
    request: ProviderRequest,
    policy: SolarCostTimeoutPolicy,
) -> SolarContractFixtureResult:
    """Build a sanitized request fixture or return a blocked result."""
    checks, failures = validate_solar_cost_timeout_policy(policy)
    _validate_request_shape(request, checks, failures)
    if failures:
        return _blocked_result(checks, failures)

    request_contract_hash = stable_contract_hash(
        {
            "version": SOLAR_CONTRACT_VERSION,
            "run_id": request.run_id,
            "provider_name": request.provider_name,
            "model_name": request.model_name,
            "mode": request.mode,
            "prompt_contract_hash": request.prompt_contract_hash,
            "timeout_seconds": policy.request_timeout_seconds,
            "cost_unit_budget": policy.max_cost_units,
            "live_api_call_budget": policy.max_live_api_calls,
            "output_token_budget": policy.max_output_tokens,
            "retry_count": policy.retry_count,
        }
    )
    contract = SolarRequestContractFixture(
        version=SOLAR_CONTRACT_VERSION,
        run_id=safe_public_run_id(request.run_id),
        provider_name=request.provider_name,
        model_name=request.model_name,
        mode=request.mode,
        env_key_name=request.env_key_name,
        prompt_contract_hash=request.prompt_contract_hash,
        request_contract_hash=request_contract_hash,
        request_body_kind="prompt_contract_hash_fixture",
        timeout_seconds=int(policy.request_timeout_seconds or 0),
        cost_unit_budget=int(policy.max_cost_units or 0),
        live_api_call_budget=int(policy.max_live_api_calls or 0),
        output_token_budget=int(policy.max_output_tokens or 0),
        retry_count=int(policy.retry_count),
    )
    return SolarContractFixtureResult(
        status="admitted_fixture",
        checks=checks,
        errors=[],
        request_contract=contract.to_dict(),
        response_projection={},
        metrics=zero_solar_contract_metrics(
            {
                "solar_contract_policy_check_count": len(checks),
                "solar_request_contract_created_count": 1,
            }
        ),
    )


def build_solar_response_projection_fixture(
    *,
    request_contract: SolarRequestContractFixture | JsonDict,
    response_summary: str,
    raw_response_body: str | None = None,
) -> SolarResponseProjectionFixture:
    """Build a sanitized response projection fixture without raw provider body."""
    contract_dict = request_contract.to_dict() if isinstance(
        request_contract, SolarRequestContractFixture
    ) else dict(request_contract)
    response_summary_value = response_summary.strip() if response_summary.strip() else "sanitized response summary"
    content_hash = stable_contract_hash(
        {
            "request_contract_hash": contract_dict.get("request_contract_hash", ""),
            "response_summary": response_summary_value,
            "raw_response_ignored": bool(raw_response_body),
        }
    )
    response_contract_hash = stable_contract_hash(
        {
            "version": SOLAR_CONTRACT_VERSION,
            "run_id": contract_dict.get("run_id", ""),
            "provider_name": contract_dict.get("provider_name", SOLAR_PRO_3_PROVIDER),
            "model_name": contract_dict.get("model_name", SOLAR_PRO_3_MODEL),
            "content_hash": content_hash,
        }
    )
    return SolarResponseProjectionFixture(
        version=SOLAR_CONTRACT_VERSION,
        run_id=str(contract_dict.get("run_id", "run-redacted")),
        provider_name=str(contract_dict.get("provider_name", SOLAR_PRO_3_PROVIDER)),
        model_name=str(contract_dict.get("model_name", SOLAR_PRO_3_MODEL)),
        status="projected_fixture",
        response_kind="sanitized_summary_hash_fixture",
        response_summary=response_summary_value,
        response_contract_hash=response_contract_hash,
        content_hash=content_hash,
    )


def attach_solar_response_projection_fixture(
    request_result: SolarContractFixtureResult,
    *,
    response_summary: str,
    raw_response_body: str | None = None,
) -> SolarContractFixtureResult:
    """Attach a sanitized response projection to an admitted request fixture."""
    if request_result.status != "admitted_fixture" or not request_result.request_contract:
        return request_result
    response = build_solar_response_projection_fixture(
        request_contract=request_result.request_contract,
        response_summary=response_summary,
        raw_response_body=raw_response_body,
    )
    metrics = dict(request_result.metrics)
    metrics["solar_response_projection_created_count"] = 1
    return SolarContractFixtureResult(
        status="projected_fixture",
        checks=list(request_result.checks),
        errors=[],
        request_contract=dict(request_result.request_contract),
        response_projection=response.to_dict(),
        metrics=metrics,
    )


__all__ = [
    "SOLAR_CONTRACT_VERSION",
    "SolarContractFixtureResult",
    "SolarCostTimeoutPolicy",
    "SolarRequestContractFixture",
    "SolarResponseProjectionFixture",
    "attach_solar_response_projection_fixture",
    "build_solar_request_contract_fixture",
    "build_solar_response_projection_fixture",
    "validate_solar_cost_timeout_policy",
    "zero_solar_contract_metrics",
]

import builtins
import json
import os
import socket
import urllib.request

from packages.core.exposure import find_forbidden_public_keys
from packages.core.live_open_policy import (
    LIVE_OPEN_REQUIRED_CONTROLS,
    SOLAR_PRO_3_ENV_KEY_NAME,
    SOLAR_PROVIDER_SURFACE,
    LiveOpenRequest,
    evaluate_live_open_request,
)
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.provider_boundary import (
    SOLAR_PRO_3_MODEL,
    SOLAR_PRO_3_PROVIDER,
    ProviderApprovalRecord,
    ProviderRequest,
)
from packages.daacs_builder.solar_live_adapter import (
    SOLAR_LIVE_ADAPTER_MODE,
    DisabledSolarPro3LiveAdapter,
    ProviderAdapterRegistry,
    SolarPro3LiveAdapterConfig,
    default_solar_provider_adapter_registry,
)


def _prompt_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "disabled solar live adapter",
            "prompt_contract": "hash only",
        }
    )


def _approval(**overrides) -> ProviderApprovalRecord:
    fields = {
        "approved_by": "local-user",
        "approved_at": "2026-06-01T00:00:00Z",
        "run_id": "run-solar-live",
        "provider_name": SOLAR_PRO_3_PROVIDER,
        "model_name": SOLAR_PRO_3_MODEL,
        "mode": SOLAR_LIVE_ADAPTER_MODE,
        "env_key_name": SOLAR_PRO_3_ENV_KEY_NAME,
        "max_live_api_calls": 1,
        "max_live_llm_calls": 1,
        "expires_at": "2099-01-01T00:00:00Z",
        "audit_log_id": "audit-solar-live",
    }
    fields.update(overrides)
    return ProviderApprovalRecord(**fields)


def _request(**overrides) -> ProviderRequest:
    fields = {
        "run_id": "run-solar-live",
        "prompt_contract_hash": _prompt_hash(),
        "provider_name": SOLAR_PRO_3_PROVIDER,
        "model_name": SOLAR_PRO_3_MODEL,
        "mode": SOLAR_LIVE_ADAPTER_MODE,
        "env_key_name": SOLAR_PRO_3_ENV_KEY_NAME,
        "approval": _approval(),
    }
    fields.update(overrides)
    return ProviderRequest(**fields)


def _ready_live_open_decision():
    readiness = {field_name: True for field_name in LIVE_OPEN_REQUIRED_CONTROLS}
    return evaluate_live_open_request(
        LiveOpenRequest(
            run_id="run-solar-live",
            surface=SOLAR_PROVIDER_SURFACE,
            env_key_name=SOLAR_PRO_3_ENV_KEY_NAME,
            **readiness,
        )
    )


def _ready_config(**overrides) -> SolarPro3LiveAdapterConfig:
    fields = {
        "enabled": True,
        "request_timeout_seconds": 30,
        "max_cost_units": 1,
        "max_output_tokens": 512,
        "max_live_api_calls": 1,
    }
    fields.update(overrides)
    return SolarPro3LiveAdapterConfig(**fields)


def _checks(result):
    return {check["name"]: check["passed"] for check in result.to_dict()["checks"]}


def _serialized(result) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=True, sort_keys=True)


def test_solar_live_adapter_can_be_registered_but_default_invocation_blocks():
    registry = default_solar_provider_adapter_registry()
    adapter = registry.resolve(SOLAR_PRO_3_PROVIDER, SOLAR_LIVE_ADAPTER_MODE)

    result = adapter.invoke(_request())
    checks = _checks(result)

    assert isinstance(adapter, DisabledSolarPro3LiveAdapter)
    assert result.status == "blocked"
    assert checks["solar_live_adapter_enabled"] is False
    assert result.metrics["solar_live_adapter_registered_count"] == 1
    assert result.metrics["solar_live_api_calls"] == 0
    assert result.metrics["live_api_calls"] == 0
    assert result.metrics["provider_calls"] == 0


def test_solar_live_adapter_blocks_without_live_open_policy():
    adapter = DisabledSolarPro3LiveAdapter(config=_ready_config())

    result = adapter.invoke(_request())
    checks = _checks(result)

    assert result.status == "blocked"
    assert checks["solar_live_open_policy_present"] is False
    assert result.metrics["solar_live_api_calls"] == 0
    assert result.metrics["network_calls"] == 0


def test_solar_live_adapter_blocks_missing_timeout_cost_and_quota_config():
    adapter = DisabledSolarPro3LiveAdapter(
        config=SolarPro3LiveAdapterConfig(enabled=True),
        live_open_decision=_ready_live_open_decision(),
    )

    result = adapter.invoke(_request())
    checks = _checks(result)

    assert result.status == "blocked"
    assert checks["solar_live_timeout_configured"] is False
    assert checks["solar_live_cost_quota_configured"] is False
    assert checks["solar_live_token_quota_configured"] is False
    assert result.metrics["solar_live_api_calls"] == 0


def test_solar_live_adapter_keeps_fake_provider_path_separate():
    adapter = DisabledSolarPro3LiveAdapter(
        config=_ready_config(),
        live_open_decision=_ready_live_open_decision(),
    )
    request = _request(mode="fake", approval=_approval(mode="fake"))

    result = adapter.invoke(request)
    checks = _checks(result)

    assert result.status == "blocked"
    assert checks["solar_live_mode_live"] is False
    assert "FakeSolarProProvider" in _serialized(result)
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["solar_live_api_calls"] == 0


def test_solar_live_adapter_blocks_even_when_policy_is_eligible():
    adapter = DisabledSolarPro3LiveAdapter(
        config=_ready_config(),
        live_open_decision=_ready_live_open_decision(),
    )

    result = adapter.invoke(_request())
    checks = _checks(result)
    public = result.to_dict()

    assert result.status == "blocked"
    assert checks["solar_live_open_policy_eligible"] is True
    assert checks["solar_live_execution_permission_closed"] is False
    assert checks["solar_live_provider_call_not_implemented"] is False
    assert public["metrics"]["solar_live_api_calls"] == 0
    assert result.metrics["provider_secret_value_reads"] == 0
    assert find_forbidden_public_keys(public) == []
    assert_public_projection_safe(public)


def test_solar_live_adapter_does_not_read_env_import_sdk_or_open_network(monkeypatch):
    def blocked_getenv(*args, **kwargs):
        raise AssertionError("env value read attempted")

    def blocked_socket(*args, **kwargs):
        raise AssertionError("network socket attempted")

    def blocked_urlopen(*args, **kwargs):
        raise AssertionError("network urlopen attempted")

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".", 1)[0] in {"upstage", "openai", "requests", "httpx"}:
            raise AssertionError(f"provider SDK import attempted: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(os, "getenv", blocked_getenv)
    monkeypatch.setattr(socket, "socket", blocked_socket)
    monkeypatch.setattr(urllib.request, "urlopen", blocked_urlopen)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    adapter = DisabledSolarPro3LiveAdapter(
        config=_ready_config(),
        live_open_decision=_ready_live_open_decision(),
    )
    result = adapter.invoke(
        _request(
            metadata={
                "note": "api_key=secret-value",
                "raw_prompt": "SOLAR_LIVE_RAW_PROMPT_SENTINEL",
            }
        )
    )
    serialized = _serialized(result)

    assert result.status == "blocked"
    assert result.metrics["solar_live_env_value_reads"] == 0
    assert result.metrics["solar_live_sdk_imports"] == 0
    assert result.metrics["solar_live_api_calls"] == 0
    assert "secret-value" not in serialized
    assert "SOLAR_LIVE_RAW_PROMPT_SENTINEL" not in serialized


def test_solar_provider_adapter_registry_resolves_explicit_modes():
    registry = ProviderAdapterRegistry()
    live_adapter = DisabledSolarPro3LiveAdapter()
    fake_marker = object()

    registry.register(SOLAR_PRO_3_PROVIDER, SOLAR_LIVE_ADAPTER_MODE, live_adapter)
    registry.register(SOLAR_PRO_3_PROVIDER, "fake", fake_marker)

    assert registry.resolve(SOLAR_PRO_3_PROVIDER, SOLAR_LIVE_ADAPTER_MODE) is live_adapter
    assert registry.resolve(SOLAR_PRO_3_PROVIDER, "fake") is fake_marker
    assert registry.resolve(SOLAR_PRO_3_PROVIDER, "unknown") is None

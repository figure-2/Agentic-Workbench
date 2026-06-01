import builtins
import json
import os
import socket
import urllib.request

from packages.core.exposure import find_forbidden_public_keys
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.provider_boundary import (
    SOLAR_PRO_3_ENV_KEY_NAME,
    SOLAR_PRO_3_MODEL,
    SOLAR_PRO_3_PROVIDER,
    ProviderRequest,
)
from packages.daacs_builder.solar_contracts import (
    SolarCostTimeoutPolicy,
    attach_solar_response_projection_fixture,
    build_solar_request_contract_fixture,
    build_solar_response_projection_fixture,
    validate_solar_cost_timeout_policy,
)
from packages.daacs_builder.solar_live_adapter import SOLAR_LIVE_ADAPTER_MODE


def _prompt_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "solar request contract fixture",
            "input": "hash only",
        }
    )


def _request(**overrides) -> ProviderRequest:
    fields = {
        "run_id": "run-solar-contract",
        "prompt_contract_hash": _prompt_hash(),
        "provider_name": SOLAR_PRO_3_PROVIDER,
        "model_name": SOLAR_PRO_3_MODEL,
        "mode": SOLAR_LIVE_ADAPTER_MODE,
        "env_key_name": SOLAR_PRO_3_ENV_KEY_NAME,
        "metadata": {
            "raw_prompt": "SOLAR_CONTRACT_RAW_PROMPT_SENTINEL",
            "provider_payload": {"body": "PROVIDER_PAYLOAD_SENTINEL"},
        },
    }
    fields.update(overrides)
    return ProviderRequest(**fields)


def _policy(**overrides) -> SolarCostTimeoutPolicy:
    fields = {
        "request_timeout_seconds": 30,
        "max_cost_units": 1,
        "max_live_api_calls": 1,
        "max_output_tokens": 512,
        "retry_count": 0,
    }
    fields.update(overrides)
    return SolarCostTimeoutPolicy(**fields)


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_cost_timeout_policy_blocks_missing_required_values():
    checks, failures = validate_solar_cost_timeout_policy(SolarCostTimeoutPolicy())

    failure_names = [name for name, _ in failures]
    assert "solar_contract_timeout_configured" in failure_names
    assert "solar_contract_cost_budget_configured" in failure_names
    assert "solar_contract_api_quota_configured" in failure_names
    assert "solar_contract_output_token_quota_configured" in failure_names
    assert len(checks) == 5


def test_request_contract_uses_prompt_contract_hash_fixture_only():
    result = build_solar_request_contract_fixture(_request(), _policy())
    public = result.to_dict()
    serialized = _serialized(public)
    request_contract = public["request_contract"]

    assert public["status"] == "admitted_fixture"
    assert request_contract["request_body_kind"] == "prompt_contract_hash_fixture"
    assert request_contract["prompt_contract_hash"] == _prompt_hash()
    assert request_contract["input_text_included"] is False
    assert request_contract["provider_body_included"] is False
    assert public["metrics"]["solar_request_contract_created_count"] == 1
    assert public["metrics"]["solar_contract_api_calls"] == 0
    assert "SOLAR_CONTRACT_RAW_PROMPT_SENTINEL" not in serialized
    assert "PROVIDER_PAYLOAD_SENTINEL" not in serialized
    assert "raw_prompt" not in serialized
    assert "provider_payload" not in serialized
    assert find_forbidden_public_keys(public) == []
    assert_public_projection_safe(public)


def test_request_contract_blocks_invalid_policy_or_shape_before_fixture_creation():
    result = build_solar_request_contract_fixture(
        _request(prompt_contract_hash="not-a-hash", mode="fake"),
        SolarCostTimeoutPolicy(request_timeout_seconds=30),
    )
    public = result.to_dict()
    checks = {check["name"]: check["passed"] for check in public["checks"]}

    assert public["status"] == "blocked"
    assert public["request_contract"] == {}
    assert checks["solar_contract_cost_budget_configured"] is False
    assert checks["solar_contract_api_quota_configured"] is False
    assert checks["solar_contract_mode_live"] is False
    assert checks["solar_contract_prompt_hash_valid"] is False
    assert public["metrics"]["solar_contract_policy_block_count"] == 1
    assert public["metrics"]["solar_request_contract_created_count"] == 0


def test_response_projection_contains_summary_and_hashes_only():
    request_result = build_solar_request_contract_fixture(_request(), _policy())
    result = attach_solar_response_projection_fixture(
        request_result,
        response_summary="sanitized planner expansion",
        raw_response_body="RAW_SOLAR_RESPONSE_BODY_SENTINEL api_key=secret-value",
    )
    public = result.to_dict()
    serialized = _serialized(public)
    projection = public["response_projection"]

    assert public["status"] == "projected_fixture"
    assert projection["response_kind"] == "sanitized_summary_hash_fixture"
    assert projection["response_summary"] == "sanitized planner expansion"
    assert len(projection["response_contract_hash"]) == 64
    assert len(projection["content_hash"]) == 64
    assert projection["source_body_included"] is False
    assert projection["provider_body_included"] is False
    assert public["metrics"]["solar_response_projection_created_count"] == 1
    assert "RAW_SOLAR_RESPONSE_BODY_SENTINEL" not in serialized
    assert "secret-value" not in serialized
    assert "provider_response" not in serialized
    assert find_forbidden_public_keys(public) == []
    assert_public_projection_safe(public)


def test_response_projection_can_be_built_from_request_contract_mapping():
    request_result = build_solar_request_contract_fixture(_request(), _policy())
    projection = build_solar_response_projection_fixture(
        request_contract=request_result.to_dict()["request_contract"],
        response_summary="",
        raw_response_body="ignored raw body",
    ).to_dict()

    assert projection["status"] == "projected_fixture"
    assert projection["response_summary"] == "sanitized response summary"
    assert len(projection["response_contract_hash"]) == 64
    assert len(projection["content_hash"]) == 64
    assert find_forbidden_public_keys(projection) == []


def test_blocked_request_result_does_not_attach_response_projection():
    blocked = build_solar_request_contract_fixture(
        _request(prompt_contract_hash="bad"),
        _policy(),
    )
    result = attach_solar_response_projection_fixture(
        blocked,
        response_summary="should not attach",
        raw_response_body="RAW_SOLAR_RESPONSE_BODY_SENTINEL",
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["request_contract"] == {}
    assert result["response_projection"] == {}
    assert "RAW_SOLAR_RESPONSE_BODY_SENTINEL" not in _serialized(result)


def test_solar_contract_fixtures_do_not_read_env_import_sdk_or_call_network(monkeypatch):
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

    result = attach_solar_response_projection_fixture(
        build_solar_request_contract_fixture(_request(), _policy()),
        response_summary="sanitized",
        raw_response_body="RAW_SOLAR_RESPONSE_BODY_SENTINEL",
    ).to_dict()

    assert result["metrics"]["solar_contract_env_value_reads"] == 0
    assert result["metrics"]["solar_contract_sdk_imports"] == 0
    assert result["metrics"]["solar_contract_api_calls"] == 0
    assert result["metrics"]["solar_contract_network_calls"] == 0

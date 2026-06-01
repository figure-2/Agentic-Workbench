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
    ProviderResult,
)
from packages.daacs_builder.provider_envelope_admission import (
    ProviderEnvelopeAdmissionService,
    invoke_adapter_after_provider_envelope_admission,
)
from packages.daacs_builder.provider_envelope_store import (
    InMemoryProviderEnvelopeRepository,
    SQLiteProviderEnvelopeStore,
)
from packages.daacs_builder.solar_contracts import (
    SolarContractFixtureResult,
    SolarCostTimeoutPolicy,
    attach_solar_response_projection_fixture,
    build_solar_request_contract_fixture,
)
from packages.daacs_builder.solar_live_adapter import (
    SOLAR_LIVE_ADAPTER_MODE,
    DisabledSolarPro3LiveAdapter,
    SolarPro3LiveAdapterConfig,
)


def _serialized(value) -> str:
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


def _prompt_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "provider envelope admission fixture",
            "input": "hash only",
        }
    )


def _approval(**overrides) -> ProviderApprovalRecord:
    fields = {
        "approved_by": "local-user",
        "approved_at": "2026-06-01T00:00:00Z",
        "run_id": "run-live-04",
        "provider_name": SOLAR_PRO_3_PROVIDER,
        "model_name": SOLAR_PRO_3_MODEL,
        "mode": SOLAR_LIVE_ADAPTER_MODE,
        "env_key_name": SOLAR_PRO_3_ENV_KEY_NAME,
        "max_live_api_calls": 1,
        "max_live_llm_calls": 1,
        "expires_at": "2099-01-01T00:00:00Z",
        "audit_log_id": "audit-live-04",
    }
    fields.update(overrides)
    return ProviderApprovalRecord(**fields)


def _request(**overrides) -> ProviderRequest:
    fields = {
        "run_id": "run-live-04",
        "prompt_contract_hash": _prompt_hash(),
        "provider_name": SOLAR_PRO_3_PROVIDER,
        "model_name": SOLAR_PRO_3_MODEL,
        "mode": SOLAR_LIVE_ADAPTER_MODE,
        "env_key_name": SOLAR_PRO_3_ENV_KEY_NAME,
        "approval": _approval(),
        "metadata": {
            "raw_prompt": "LIVE04_RAW_PROMPT_SENTINEL",
            "provider_payload": {"body": "LIVE04_PROVIDER_PAYLOAD_SENTINEL"},
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


def _contract_result(request: ProviderRequest | None = None) -> SolarContractFixtureResult:
    request_result = build_solar_request_contract_fixture(
        request or _request(),
        _policy(),
    )
    return attach_solar_response_projection_fixture(
        request_result,
        response_summary="sanitized live adapter admission projection",
        raw_response_body="LIVE04_PROVIDER_BODY_SENTINEL api_key=secret-value",
    )


def _ready_live_open_decision():
    readiness = {field_name: True for field_name in LIVE_OPEN_REQUIRED_CONTROLS}
    return evaluate_live_open_request(
        LiveOpenRequest(
            run_id="run-live-04",
            surface=SOLAR_PROVIDER_SURFACE,
            env_key_name=SOLAR_PRO_3_ENV_KEY_NAME,
            **readiness,
        )
    )


def _ready_config() -> SolarPro3LiveAdapterConfig:
    return SolarPro3LiveAdapterConfig(
        enabled=True,
        request_timeout_seconds=30,
        max_cost_units=1,
        max_output_tokens=512,
        max_live_api_calls=1,
    )


def _checks(result):
    payload = result.to_dict() if hasattr(result, "to_dict") else result
    return {check["name"]: check["passed"] for check in payload["checks"]}


class SpyAdapter:
    def __init__(self, result: ProviderResult | None = None) -> None:
        self.invocation_count = 0
        self.result = result

    def invoke(self, request: ProviderRequest) -> ProviderResult:
        self.invocation_count += 1
        if self.result is not None:
            return self.result
        return DisabledSolarPro3LiveAdapter(
            config=_ready_config(),
            live_open_decision=_ready_live_open_decision(),
        ).invoke(request)


def test_provider_envelope_admission_persists_and_reads_before_disabled_adapter_invocation(tmp_path):
    request = _request()
    contract_result = _contract_result(request)
    store = SQLiteProviderEnvelopeStore(root=tmp_path)
    service = ProviderEnvelopeAdmissionService(store.repository())
    adapter = SpyAdapter()

    result = invoke_adapter_after_provider_envelope_admission(
        adapter=adapter,
        request=request,
        contract_result=contract_result,
        admission_service=service,
    )
    checks = _checks(result)
    rows = store.repository().list_for_run(request.run_id)

    assert adapter.invocation_count == 1
    assert result.status == "blocked"
    assert checks["provider_envelope_admission_passed"] is True
    assert checks["provider_envelope_hashes_visible_in_read_model"] is True
    assert checks["solar_live_provider_call_not_implemented"] is False
    assert result.metrics["provider_envelope_admission_persist_count"] == 1
    assert result.metrics["provider_envelope_adapter_invocation_count"] == 1
    assert result.metrics["solar_live_api_calls"] == 0
    assert rows[0].request_contract_hash == contract_result.request_contract["request_contract_hash"]
    assert rows[0].response_contract_hash == contract_result.response_projection["response_contract_hash"]


def test_provider_envelope_admission_blocks_missing_service_before_adapter_invocation():
    adapter = SpyAdapter()
    result = invoke_adapter_after_provider_envelope_admission(
        adapter=adapter,
        request=_request(),
        contract_result=_contract_result(),
        admission_service=None,
    )
    checks = _checks(result)

    assert result.status == "blocked"
    assert adapter.invocation_count == 0
    assert checks["provider_envelope_admission_service_present"] is False
    assert result.metrics["provider_envelope_adapter_invocation_count"] == 0
    assert result.metrics["provider_calls"] == 0


def test_provider_envelope_admission_blocks_request_contract_hash_mismatch_before_adapter():
    adapter = SpyAdapter()
    request = _request()
    contract_result = _contract_result(request)
    request.metadata["expected_request_contract_hash"] = contract_result.request_contract[
        "request_contract_hash"
    ]
    tampered = SolarContractFixtureResult(
        status=contract_result.status,
        checks=contract_result.checks,
        errors=contract_result.errors,
        request_contract={
            **contract_result.request_contract,
            "request_contract_hash": "a" * 64,
        },
        response_projection=contract_result.response_projection,
        metrics=contract_result.metrics,
    )
    service = ProviderEnvelopeAdmissionService(InMemoryProviderEnvelopeRepository())

    result = invoke_adapter_after_provider_envelope_admission(
        adapter=adapter,
        request=request,
        contract_result=tampered,
        admission_service=service,
    )
    checks = _checks(result)

    assert result.status == "blocked"
    assert adapter.invocation_count == 0
    assert checks["provider_envelope_request_contract_hash_valid"] is False
    assert result.metrics["provider_envelope_adapter_invocation_count"] == 0


def test_provider_envelope_admission_blocks_response_contract_hash_mismatch_before_adapter():
    adapter = SpyAdapter()
    request = _request()
    contract_result = _contract_result(request)
    tampered = SolarContractFixtureResult(
        status=contract_result.status,
        checks=contract_result.checks,
        errors=contract_result.errors,
        request_contract=contract_result.request_contract,
        response_projection={
            **contract_result.response_projection,
            "response_contract_hash": "b" * 64,
        },
        metrics=contract_result.metrics,
    )
    service = ProviderEnvelopeAdmissionService(InMemoryProviderEnvelopeRepository())

    result = invoke_adapter_after_provider_envelope_admission(
        adapter=adapter,
        request=request,
        contract_result=tampered,
        admission_service=service,
    )
    checks = _checks(result)

    assert result.status == "blocked"
    assert adapter.invocation_count == 0
    assert checks["provider_envelope_response_contract_hash_valid"] is False
    assert result.metrics["provider_envelope_adapter_invocation_count"] == 0


def test_provider_envelope_admission_blocks_corrupted_store_before_adapter_invocation(tmp_path):
    request = _request()
    contract_result = _contract_result(request)
    store = SQLiteProviderEnvelopeStore(root=tmp_path)
    repository = store.repository()
    store.path.write_text("not a sqlite database", encoding="utf-8")
    service = ProviderEnvelopeAdmissionService(repository)
    adapter = SpyAdapter()

    result = invoke_adapter_after_provider_envelope_admission(
        adapter=adapter,
        request=request,
        contract_result=contract_result,
        admission_service=service,
    )
    checks = _checks(result)

    assert result.status == "blocked"
    assert adapter.invocation_count == 0
    assert checks["provider_envelope_persistence_available"] is False
    assert result.metrics["provider_envelope_adapter_invocation_count"] == 0
    assert result.metrics["provider_envelope_admission_block_count"] == 1


def test_provider_envelope_admission_public_result_exposes_no_raw_values(tmp_path):
    request = _request()
    contract_result = _contract_result(request)
    service = ProviderEnvelopeAdmissionService(SQLiteProviderEnvelopeStore(root=tmp_path).repository())

    admission = service.admit(request, contract_result)
    serialized = _serialized(admission)

    assert admission.status == "admitted"
    for sentinel in (
        "LIVE04_RAW_PROMPT_SENTINEL",
        "LIVE04_PROVIDER_PAYLOAD_SENTINEL",
        "LIVE04_PROVIDER_BODY_SENTINEL",
        "secret-value",
        "raw_prompt",
        "provider_payload",
        "provider_response",
    ):
        assert sentinel not in serialized
    assert find_forbidden_public_keys(admission.to_dict()) == []
    assert_public_projection_safe(admission.to_dict())


def test_provider_envelope_admission_does_not_read_env_import_sdk_or_call_network(tmp_path, monkeypatch):
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

    request = _request()
    result = invoke_adapter_after_provider_envelope_admission(
        adapter=SpyAdapter(),
        request=request,
        contract_result=_contract_result(request),
        admission_service=ProviderEnvelopeAdmissionService(
            SQLiteProviderEnvelopeStore(root=tmp_path).repository()
        ),
    )

    assert result.metrics["provider_envelope_env_value_reads"] == 0
    assert result.metrics["provider_envelope_sdk_imports"] == 0
    assert result.metrics["provider_envelope_api_calls"] == 0
    assert result.metrics["provider_envelope_network_calls"] == 0
    assert result.metrics["solar_live_env_value_reads"] == 0
    assert result.metrics["solar_live_sdk_imports"] == 0
    assert result.metrics["solar_live_api_calls"] == 0


def test_provider_envelope_admission_allows_duplicate_matching_evidence_without_raw_rewrite(tmp_path):
    request = _request()
    contract_result = _contract_result(request)
    service = ProviderEnvelopeAdmissionService(SQLiteProviderEnvelopeStore(root=tmp_path).repository())

    first = service.admit(request, contract_result)
    second = service.admit(request, contract_result)

    assert first.status == "admitted"
    assert second.status == "admitted"
    assert second.metrics["provider_envelope_admission_duplicate_count"] == 1
    assert second.metrics["provider_envelope_admission_persist_count"] == 0

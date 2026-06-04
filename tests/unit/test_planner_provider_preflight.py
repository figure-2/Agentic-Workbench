import builtins
import json
import os
import socket
import urllib.request

from packages.core.exposure import find_forbidden_public_keys
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.div_planner.provider_boundary import (
    PLANNER_PROVIDER_MODE_FIXTURE,
    PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
    PlannerProviderPreflightRequest,
    PlannerProviderSelector,
    ready_planner_provider_policy,
)
from apps.api.agentic_workbench_api.services.planner_provider_preflight import (
    run_planner_provider_preflight,
)


def _prompt_contract_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "planner provider preflight",
            "source": "hash-only fixture",
        }
    )


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _checks(public: dict) -> dict[str, bool]:
    return {check["name"]: check["passed"] for check in public["checks"]}


def test_fixture_planner_mode_remains_default_and_no_call():
    selector = PlannerProviderSelector()
    result = selector.preflight(
        PlannerProviderPreflightRequest(
            run_id="run-planner-fixture",
            prompt_contract_hash=_prompt_contract_hash(),
            planner_provider_mode=PLANNER_PROVIDER_MODE_FIXTURE,
        )
    )
    public = result.to_dict()
    checks = _checks(public)

    assert public["status"] == "fixture_default"
    assert public["reason"] == "fixture_planner_selected"
    assert checks["fixture_planner_remains_default"] is True
    assert public["counts"]["planner_provider_success_count"] == 0
    assert public["execution_boundary"]["provider_calls"] == 0
    assert public["execution_boundary"]["solar_provider_calls"] == 0
    assert public["claim_boundary"]["provider_generated_blueprint"] is False
    assert find_forbidden_public_keys(public) == []
    assert_public_projection_safe(public)


def test_solar_planner_preflight_blocks_without_ready_policy():
    selector = PlannerProviderSelector()
    result = selector.preflight(
        PlannerProviderPreflightRequest(
            run_id="run-planner-blocked",
            prompt_contract_hash=_prompt_contract_hash(),
            planner_provider_mode=PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
        )
    )
    public = result.to_dict()
    checks = _checks(public)

    assert public["status"] == "blocked"
    assert public["reason"] in {
        "timeout_missing",
        "cost_quota_missing",
        "output_token_quota_missing",
        "live_open_policy_not_eligible",
    }
    assert checks["live_open_policy_eligible"] is False
    assert public["counts"]["status_blocked_count"] == 1
    assert public["execution_boundary"]["provider_calls"] == 0
    assert public["execution_boundary"]["network_calls"] == 0


def test_solar_planner_preflight_is_preflight_only_with_ready_policy():
    selector = PlannerProviderSelector()
    result = selector.preflight(
        PlannerProviderPreflightRequest(
            run_id="run-planner-ready",
            prompt_contract_hash=_prompt_contract_hash(),
            planner_provider_mode=PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
            policy=ready_planner_provider_policy(),
        )
    )
    public = result.to_dict()
    checks = _checks(public)

    assert public["status"] == "preflight_only"
    assert public["reason"] == "provider_call_disabled_by_design"
    assert checks["live_open_policy_eligible"] is True
    assert checks["planner_provider_call_disabled_by_design"] is True
    assert public["counts"]["comparison_variant_count"] == 1
    assert public["counts"]["status_preflight_only_count"] == 1
    assert public["counts"]["planner_provider_success_count"] == 0
    assert public["counts"]["provider_call_count"] == 0
    assert public["counts"]["sdk_import_count"] == 0
    assert public["counts"]["env_value_read_count"] == 0
    assert public["execution_boundary"]["env_key_value_reads"] == 0
    assert public["execution_boundary"]["sdk_imports"] == 0
    assert public["execution_boundary"]["network_calls"] == 0


def test_api_policy_requires_literal_true_not_truthy_strings():
    policy = {
        "approval_policy_ready": "true",
        "replay_persistence_ready": "true",
        "cost_quota_guard_ready": "true",
        "timeout_guard_ready": "true",
        "workspace_sandbox_ready": "true",
        "write_allowlist_ready": "true",
        "rollback_plan_ready": "true",
        "secret_redaction_ready": "true",
        "artifact_sanitizer_ready": "true",
        "audit_projection_ready": "true",
        "request_timeout_seconds": 30,
        "max_cost_units": 1,
        "max_output_tokens": 512,
        "max_live_api_calls": 1,
        "retry_count": 0,
    }

    public = run_planner_provider_preflight(
        {
            "run_id": "run-planner-string-policy",
            "prompt_contract_hash": _prompt_contract_hash(),
            "planner_provider_mode": PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
            "policy": policy,
        }
    )
    checks = _checks(public)

    assert public["status"] == "blocked"
    assert checks["live_open_policy_eligible"] is False
    assert public["execution_boundary"]["provider_calls"] == 0
    assert public["claim_boundary"]["external_provider_outcome"] is False


def test_solar_planner_preflight_blocks_missing_timeout_cost_and_quota():
    selector = PlannerProviderSelector()
    result = selector.preflight(
        PlannerProviderPreflightRequest(
            run_id="run-planner-policy-gap",
            prompt_contract_hash=_prompt_contract_hash(),
            planner_provider_mode=PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
            policy=ready_planner_provider_policy(
                request_timeout_seconds=None,
                max_cost_units=None,
                max_output_tokens=None,
                max_live_api_calls=None,
            ),
        )
    )
    public = result.to_dict()
    checks = _checks(public)

    assert public["status"] == "blocked"
    assert checks["timeout_configured"] is False
    assert checks["cost_quota_configured"] is False
    assert checks["output_token_quota_configured"] is False
    assert public["execution_boundary"]["provider_calls"] == 0


def test_solar_planner_preflight_sanitizes_metadata_and_public_projection():
    selector = PlannerProviderSelector()
    result = selector.preflight(
        PlannerProviderPreflightRequest(
            run_id="run-planner-sanitize",
            prompt_contract_hash=_prompt_contract_hash(),
            planner_provider_mode=PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
            policy=ready_planner_provider_policy(),
            metadata={
                "raw_prompt": "SOLAR_PLANNER_RAW_PROMPT_SENTINEL",
                "secret_note": "api_key=secret-value",
            },
        )
    )
    public = result.to_dict()
    serialized = _serialized(public)

    assert "SOLAR_PLANNER_RAW_PROMPT_SENTINEL" not in serialized
    assert "secret-value" not in serialized
    assert find_forbidden_public_keys(public) == []
    assert_public_projection_safe(public)


def test_solar_planner_preflight_does_not_read_env_import_sdk_or_open_network(monkeypatch):
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

    selector = PlannerProviderSelector()
    result = selector.preflight(
        PlannerProviderPreflightRequest(
            run_id="run-planner-no-call",
            prompt_contract_hash=_prompt_contract_hash(),
            planner_provider_mode=PLANNER_PROVIDER_MODE_SOLAR_DISABLED,
            policy=ready_planner_provider_policy(),
        )
    )
    public = result.to_dict()

    assert public["status"] == "preflight_only"
    assert public["execution_boundary"]["provider_calls"] == 0
    assert public["execution_boundary"]["solar_provider_calls"] == 0
    assert public["execution_boundary"]["env_key_value_reads"] == 0
    assert public["execution_boundary"]["sdk_imports"] == 0
    assert public["execution_boundary"]["network_calls"] == 0

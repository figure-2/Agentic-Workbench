import json

from packages.core.exposure import find_forbidden_public_keys
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.div_planner.solar_live_spike import (
    SOLAR_PLANNER_LIVE_SPIKE_VERSION,
    SolarPlannerHTTPResponse,
    SolarPlannerLiveProviderError,
    SolarPlannerLiveSpikeRequest,
    run_solar_planner_live_spike,
)


def _prompt_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "solar planner live spike",
            "prompt_contract": "hash only",
        }
    )


def _request(**overrides) -> SolarPlannerLiveSpikeRequest:
    fields = {
        "run_id": "run-solar-live-spike",
        "prompt_contract_hash": _prompt_hash(),
        "operator_live_opt_in": True,
        "request_timeout_seconds": 20,
        "max_input_chars": 1800,
        "max_output_tokens": 384,
        "max_live_api_calls": 1,
        "cost_limit_label": "one-shot-bounded",
        "sanitized_idea_summary": "study group task collaboration app",
    }
    fields.update(overrides)
    return SolarPlannerLiveSpikeRequest(**fields)


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_live_spike_blocks_without_explicit_operator_opt_in():
    runner_calls: list[dict] = []

    def runner(**kwargs):
        runner_calls.append(kwargs)
        raise AssertionError("runner should not be called")

    result = run_solar_planner_live_spike(
        _request(operator_live_opt_in=False),
        credential_reader=lambda _: "up_test_key",
        live_runner=runner,
    ).to_dict()

    assert result["projection_version"] == SOLAR_PLANNER_LIVE_SPIKE_VERSION
    assert result["status"] == "blocked"
    assert result["reason"] == "operator_live_opt_in_missing"
    assert result["counts"]["provider_call_count"] == 0
    assert result["counts"]["env_value_read_count"] == 0
    assert result["counts"]["credential_value_exposure_count"] == 0
    assert result["counts"]["input_text_exposure_count"] == 0
    assert runner_calls == []
    assert find_forbidden_public_keys(result) == []
    assert_public_projection_safe(result)


def test_live_spike_blocks_missing_credential_before_request_creation():
    runner_calls: list[dict] = []

    def runner(**kwargs):
        runner_calls.append(kwargs)
        raise AssertionError("runner should not be called")

    result = run_solar_planner_live_spike(
        _request(),
        credential_reader=lambda _: None,
        live_runner=runner,
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "credential_unavailable"
    assert result["counts"]["env_value_read_count"] == 1
    assert result["counts"]["request_body_created_count"] == 0
    assert result["counts"]["provider_call_count"] == 0
    assert runner_calls == []
    assert_public_projection_safe(result)


def test_live_spike_projects_fake_runner_response_hashes_only():
    runner_calls: list[dict] = []

    def runner(**kwargs):
        runner_calls.append(kwargs)
        request_body = kwargs["request_body"]
        assert "Build a small task collaboration app" not in _serialized(request_body)
        assert "raw_prompt" not in _serialized(request_body)
        return SolarPlannerHTTPResponse(
            status_code=200,
            body=json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "planning_blueprint": "Define a compact collaboration workflow.",
                                        "prd_package": "Capture task, assignee, due date, and dashboard requirements.",
                                        "implementation_brief": "Build a local React fixture with task cards.",
                                        "acceptance_criteria": "Verify visible task state and no live runtime execution.",
                                    }
                                )
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
            elapsed_ms=123,
        )

    result = run_solar_planner_live_spike(
        _request(),
        credential_reader=lambda _: "up_test_key",
        live_runner=runner,
    ).to_dict()
    serialized = _serialized(result)
    projection = result["response_projection"]

    assert result["status"] == "projected"
    assert result["reason"] == "solar_live_spike_projected"
    assert result["counts"]["provider_call_count"] == 1
    assert result["counts"]["network_call_count"] == 1
    assert result["counts"]["env_value_read_count"] == 1
    assert result["counts"]["credential_value_exposure_count"] == 0
    assert result["counts"]["input_text_exposure_count"] == 0
    assert result["counts"]["raw_provider_body_stored_count"] == 0
    assert result["counts"]["raw_provider_body_returned_count"] == 0
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert result["execution_boundary"]["server_start_calls"] == 0
    assert len(projection["response_contract_hash"]) == 64
    assert len(projection["summary_hash"]) == 64
    assert projection["summary_section_count"] == 4
    assert projection["provider_body_included"] is False
    assert len(runner_calls) == 1
    assert "up_test_key" not in serialized
    assert "planning_blueprint" not in serialized
    assert "raw_prompt" not in serialized
    assert find_forbidden_public_keys(result) == []
    assert_public_projection_safe(result)


def test_live_spike_provider_error_is_sanitized():
    def runner(**kwargs):
        raise SolarPlannerLiveProviderError(
            "provider_timeout",
            status_code=0,
            body_byte_count=0,
        )

    result = run_solar_planner_live_spike(
        _request(),
        credential_reader=lambda _: "up_test_key",
        live_runner=runner,
    ).to_dict()
    serialized = _serialized(result)

    assert result["status"] == "failed"
    assert result["reason"] == "provider_timeout"
    assert result["response_projection"] == {}
    assert result["counts"]["provider_call_count"] == 1
    assert result["counts"]["raw_provider_body_returned_count"] == 0
    assert "up_test_key" not in serialized
    assert_public_projection_safe(result)

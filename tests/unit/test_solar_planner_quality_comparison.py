import json

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.div_planner.solar_live_spike import (
    SolarPlannerHTTPResponse,
    SolarPlannerLiveSpikeRequest,
    run_solar_planner_live_spike,
)
from packages.div_planner.solar_quality_comparison import (
    SOLAR_PLANNER_QUALITY_COMPARISON_VERSION,
    SolarPlannerQualityComparisonRequest,
    compare_solar_planner_quality,
)


def _prompt_hash() -> str:
    return stable_contract_hash({"purpose": "solar quality comparison"})


def _projected_solar_spike() -> dict:
    def runner(**kwargs):
        return SolarPlannerHTTPResponse(
            status_code=200,
            body=json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "planning_blueprint": "workflow",
                                        "prd_package": "requirements",
                                        "implementation_brief": "build plan",
                                        "acceptance_criteria": "checks",
                                    }
                                )
                            }
                        }
                    ]
                }
            ).encode("utf-8"),
        )

    return run_solar_planner_live_spike(
        SolarPlannerLiveSpikeRequest(
            run_id="run-solar-quality",
            prompt_contract_hash=_prompt_hash(),
            operator_live_opt_in=True,
            request_timeout_seconds=20,
            max_input_chars=1800,
            max_output_tokens=384,
            max_live_api_calls=1,
            cost_limit_label="one-shot-bounded",
        ),
        credential_reader=lambda _: "up_test_key",
        live_runner=runner,
    ).to_dict()


def _request(**overrides) -> SolarPlannerQualityComparisonRequest:
    fields = {
        "run_id": "run-solar-quality",
        "prompt_contract_hash": _prompt_hash(),
        "fixture_required_stage_count": 7,
        "fixture_covered_stage_count": 7,
        "fixture_artifact_count": 6,
        "solar_live_spike_projection": _projected_solar_spike(),
    }
    fields.update(overrides)
    return SolarPlannerQualityComparisonRequest(**fields)


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_quality_comparison_blocks_artifact_binding_without_reviewer_approval():
    result = compare_solar_planner_quality(_request()).to_dict()

    assert result["projection_version"] == SOLAR_PLANNER_QUALITY_COMPARISON_VERSION
    assert result["status"] == "review_blocked"
    assert result["reason"] == "reviewer_approval_missing"
    assert result["fixture_summary"]["stage_coverage"] == "7/7"
    assert result["solar_summary"]["summary_section_count"] == 4
    assert result["solar_summary"]["artifact_hint_count"] >= 3
    assert result["solar_summary"]["missing_required_stage_count"] == 0
    assert result["review_gate"]["status"] == "blocked"
    assert result["review_gate"]["artifact_binding_permission"] is False
    assert result["counts"]["reviewer_approval_count"] == 0
    assert result["counts"]["artifact_binding_performed_count"] == 0
    assert result["counts"]["additional_live_call_count"] == 0
    assert result["execution_boundary"]["comparison_provider_calls"] == 0
    assert result["execution_boundary"]["observed_solar_provider_calls"] == 1
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert "up_test_key" not in _serialized(result)
    assert_public_projection_safe(result)


def test_quality_comparison_can_mark_review_ready_with_hash_only_approval():
    approval_hash = stable_contract_hash(
        {"reviewer": "local", "decision": "quality-comparison-only"}
    )

    result = compare_solar_planner_quality(
        _request(reviewer_approval_hash=approval_hash)
    ).to_dict()

    assert result["status"] == "review_ready"
    assert result["reason"] == "solar_quality_comparison_ready_for_reviewer_bound_draft"
    assert result["review_gate"]["status"] == "ready"
    assert result["review_gate"]["artifact_binding_permission"] is True
    assert result["review_gate"]["artifact_binding_performed"] is False
    assert result["counts"]["reviewer_approval_count"] == 1
    assert result["counts"]["artifact_binding_permission_count"] == 1
    assert result["counts"]["artifact_binding_performed_count"] == 0
    assert_public_projection_safe(result)


def test_quality_comparison_blocks_missing_solar_projection_without_side_effects():
    result = compare_solar_planner_quality(
        _request(solar_live_spike_projection={})
    ).to_dict()
    serialized = _serialized(result)

    assert result["status"] == "review_blocked"
    assert result["reason"] == "solar_projection_version_invalid"
    assert result["counts"]["solar_response_projection_count"] == 0
    assert result["counts"]["missing_required_stage_count"] == 4
    assert result["execution_boundary"]["comparison_provider_calls"] == 0
    assert result["execution_boundary"]["comparison_env_key_value_reads"] == 0
    assert result["execution_boundary"]["comparison_network_calls"] == 0
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert "raw_prompt" not in serialized
    assert "provider_payload" not in serialized
    assert_public_projection_safe(result)

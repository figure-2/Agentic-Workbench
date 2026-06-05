import json

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.div_planner.solar_draft_projection import (
    SOLAR_PLANNER_DRAFT_PROJECTION_VERSION,
    SolarPlannerDraftProjectionRequest,
    project_solar_planner_drafts,
)
from packages.div_planner.solar_live_spike import (
    SolarPlannerHTTPResponse,
    SolarPlannerLiveSpikeRequest,
    run_solar_planner_live_spike,
)
from packages.div_planner.solar_quality_comparison import (
    SolarPlannerQualityComparisonRequest,
    compare_solar_planner_quality,
)


def _prompt_hash() -> str:
    return stable_contract_hash({"purpose": "solar draft projection"})


def _reviewer_hash() -> str:
    return stable_contract_hash(
        {"reviewer": "local", "decision": "draft-projection-only"}
    )


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
            run_id="run-solar-draft",
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


def _quality_ready() -> dict:
    return compare_solar_planner_quality(
        SolarPlannerQualityComparisonRequest(
            run_id="run-solar-draft",
            prompt_contract_hash=_prompt_hash(),
            fixture_required_stage_count=7,
            fixture_covered_stage_count=7,
            fixture_artifact_count=6,
            solar_live_spike_projection=_projected_solar_spike(),
            reviewer_approval_hash=_reviewer_hash(),
        )
    ).to_dict()


def _request(**overrides) -> SolarPlannerDraftProjectionRequest:
    quality = _quality_ready()
    fields = {
        "run_id": "run-solar-draft",
        "prompt_contract_hash": _prompt_hash(),
        "solar_quality_comparison_hash": quality["comparison_hash"],
        "solar_quality_comparison_projection": quality,
        "reviewer_approval_hash": _reviewer_hash(),
    }
    fields.update(overrides)
    return SolarPlannerDraftProjectionRequest(**fields)


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_draft_projection_blocks_without_reviewer_approval_hash():
    result = project_solar_planner_drafts(
        _request(reviewer_approval_hash="")
    ).to_dict()

    assert result["projection_version"] == SOLAR_PLANNER_DRAFT_PROJECTION_VERSION
    assert result["status"] == "blocked"
    assert result["reason"] == "reviewer_approval_missing"
    assert result["counts"]["draft_artifact_projection_count"] == 0
    assert result["counts"]["canonical_artifact_write_count"] == 0
    assert result["counts"]["additional_live_call_count"] == 0
    assert result["execution_boundary"]["draft_projection_provider_calls"] == 0
    assert result["execution_boundary"]["target_runtime_calls"] == 0
    assert_public_projection_safe(result)


def test_draft_projection_blocks_quality_hash_mismatch():
    wrong_hash = stable_contract_hash({"wrong": "quality"})

    result = project_solar_planner_drafts(
        _request(solar_quality_comparison_hash=wrong_hash)
    ).to_dict()

    assert result["status"] == "blocked"
    assert result["reason"] == "quality_comparison_hash_mismatch"
    assert result["counts"]["quality_comparison_hash_match_count"] == 0
    assert result["counts"]["draft_projection_count"] == 0
    assert result["counts"]["canonical_artifact_write_count"] == 0
    assert_public_projection_safe(result)


def test_draft_projection_creates_hash_only_planning_and_prd_drafts():
    result = project_solar_planner_drafts(_request()).to_dict()
    serialized = _serialized(result)

    assert result["status"] == "draft_projected"
    assert result["reason"] == "solar_draft_projection_ready_for_review"
    assert len(result["draft_projection_hash"]) == 64
    assert result["counts"]["draft_projection_count"] == 1
    assert result["counts"]["draft_artifact_projection_count"] == 2
    assert result["counts"]["draft_planning_blueprint_projection_count"] == 1
    assert result["counts"]["draft_prd_package_projection_count"] == 1
    assert result["review_gate"]["canonical_artifact_write_permission"] is False
    assert result["review_gate"]["canonical_artifact_write_performed"] is False
    assert result["counts"]["canonical_artifact_write_count"] == 0
    assert result["counts"]["provider_call_count"] == 0
    assert result["counts"]["env_value_read_count"] == 0
    assert result["counts"]["network_call_count"] == 0
    assert result["counts"]["target_runtime_call_count"] == 0
    assert {artifact["artifact_label"] for artifact in result["draft_artifacts"]} == {
        "PlanningBlueprint",
        "PRDPackage",
    }
    assert all(
        artifact["provider_body_included"] is False
        and artifact["section_body_included"] is False
        and artifact["canonical_artifact_written"] is False
        for artifact in result["draft_artifacts"]
    )
    for forbidden in (
        "up_test_key",
        "provider_payload",
        "runtime_payload",
        "raw_prompt",
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(result)

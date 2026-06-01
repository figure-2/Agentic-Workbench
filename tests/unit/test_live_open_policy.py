import json

from packages.core.exposure import find_forbidden_public_keys
from packages.core.live_open_policy import (
    DAACS_TARGET_RUNTIME_SURFACE,
    LIVE_OPEN_REQUIRED_CONTROLS,
    SOLAR_PRO_3_ENV_KEY_NAME,
    SOLAR_PROVIDER_SURFACE,
    LiveOpenRequest,
    evaluate_live_open_request,
)


def _ready_request(**overrides):
    fields = {field_name: True for field_name in LIVE_OPEN_REQUIRED_CONTROLS}
    fields.update(
        {
            "run_id": "run-live-open-001",
            "surface": SOLAR_PROVIDER_SURFACE,
            "env_key_name": SOLAR_PRO_3_ENV_KEY_NAME,
        }
    )
    fields.update(overrides)
    return LiveOpenRequest(**fields)


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_live_open_policy_blocks_by_default_and_keeps_zero_calls():
    decision = evaluate_live_open_request(
        LiveOpenRequest(
            run_id="run-live-open-default",
            surface=SOLAR_PROVIDER_SURFACE,
            env_key_name=SOLAR_PRO_3_ENV_KEY_NAME,
        )
    )

    public = decision.to_dict()

    assert public["status"] == "blocked"
    assert public["eligible_for_live_open"] is False
    assert public["allowed_to_execute"] is False
    assert "approval_policy_ready_missing" in public["reason_codes"]
    assert public["execution_boundary"]["solar_provider_calls"] == 0
    assert public["execution_boundary"]["target_runtime_calls"] == 0
    assert public["execution_boundary"]["network_calls"] == 0
    assert public["execution_boundary"]["env_key_value_loaded"] is False
    assert find_forbidden_public_keys(public) == []


def test_live_open_policy_blocks_unknown_surface_before_any_call():
    decision = evaluate_live_open_request(_ready_request(surface="unknown", env_key_name=""))

    public = decision.to_dict()

    assert public["status"] == "blocked"
    assert public["surface"] == "unknown"
    assert "surface_unknown" in public["reason_codes"]
    assert public["execution_boundary"]["solar_provider_calls"] == 0
    assert public["execution_boundary"]["target_runtime_calls"] == 0


def test_solar_live_open_policy_references_env_key_name_without_loading_value():
    decision = evaluate_live_open_request(
        _ready_request(
            metadata={
                "note": "api_key=secret-value",
                "raw_prompt": "LIVE_OPEN_RAW_PROMPT_SENTINEL",
            }
        )
    )

    public = decision.to_dict()
    serialized = _serialized(public)

    assert public["status"] == "eligible_for_separate_live_implementation"
    assert public["eligible_for_live_open"] is True
    assert public["allowed_to_execute"] is False
    assert public["reason_codes"] == ["separate_live_implementation_required"]
    assert public["execution_boundary"]["env_key_value_loaded"] is False
    assert SOLAR_PRO_3_ENV_KEY_NAME in serialized
    assert "secret-value" not in serialized
    assert "LIVE_OPEN_RAW_PROMPT_SENTINEL" not in serialized
    assert find_forbidden_public_keys(public) == []


def test_ready_policy_still_does_not_grant_execution_permission():
    decision = evaluate_live_open_request(_ready_request())

    public = decision.to_dict()

    assert public["status"] == "eligible_for_separate_live_implementation"
    assert public["eligible_for_live_open"] is True
    assert public["allowed_to_execute"] is False
    assert public["claim_boundary"]["requires_separate_implementation_unit"] is True
    assert public["execution_boundary"]["live_execution_opened"] is False
    assert public["execution_boundary"]["solar_provider_calls"] == 0
    assert public["execution_boundary"]["target_runtime_calls"] == 0


def test_requested_call_or_write_attempt_blocks_even_when_controls_are_ready():
    decision = evaluate_live_open_request(
        _ready_request(
            requested_live_call_count=1,
            requested_runtime_write_count=1,
            requested_network_call_count=1,
        )
    )

    public = decision.to_dict()

    assert public["status"] == "blocked"
    assert "requested_live_call_count_not_zero" in public["reason_codes"]
    assert "requested_runtime_write_count_not_zero" in public["reason_codes"]
    assert "requested_network_call_count_not_zero" in public["reason_codes"]
    assert public["execution_boundary"]["solar_provider_calls"] == 0
    assert public["execution_boundary"]["filesystem_writes"] == 0
    assert public["execution_boundary"]["network_calls"] == 0


def test_daacs_target_runtime_policy_requires_no_provider_env_key_name():
    blocked = evaluate_live_open_request(
        _ready_request(
            surface=DAACS_TARGET_RUNTIME_SURFACE,
            env_key_name=SOLAR_PRO_3_ENV_KEY_NAME,
        )
    ).to_dict()
    eligible = evaluate_live_open_request(
        _ready_request(surface=DAACS_TARGET_RUNTIME_SURFACE, env_key_name="")
    ).to_dict()

    assert blocked["status"] == "blocked"
    assert "runtime_env_key_not_expected" in blocked["reason_codes"]
    assert blocked["execution_boundary"]["target_runtime_calls"] == 0
    assert eligible["status"] == "eligible_for_separate_live_implementation"
    assert eligible["allowed_to_execute"] is False

"""Solar planner quality comparison over public-safe projections.

This module compares the fixture planner evidence against a sanitized Solar
live spike projection. It does not call a provider, read credentials, parse raw
provider bodies, or bind Solar output into artifacts without reviewer approval.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from packages.core.exposure import sanitize_public_payload
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash

from .provider_boundary import CONTRACT_HASH_PATTERN, SAFE_RUN_ID_PATTERN
from .solar_live_spike import SOLAR_PLANNER_LIVE_SPIKE_VERSION


SOLAR_PLANNER_QUALITY_COMPARISON_VERSION = (
    "solar-planner-quality-comparison-public-v1"
)
SOLAR_PLANNER_QUALITY_COMPARISON_MODE = "solar_quality_compare_public_projection"
REQUIRED_SOLAR_QUALITY_SECTION_COUNT = 4


@dataclass(frozen=True, slots=True)
class SolarPlannerQualityComparisonRequest:
    """Public-safe request for fixture-vs-Solar quality comparison."""

    run_id: str
    prompt_contract_hash: str
    fixture_required_stage_count: int
    fixture_covered_stage_count: int
    fixture_artifact_count: int
    solar_live_spike_projection: JsonDict = field(default_factory=dict)
    reviewer_approval_hash: str = ""
    required_solar_section_count: int = REQUIRED_SOLAR_QUALITY_SECTION_COUNT
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SolarPlannerQualityComparisonResult:
    """Hash/count-only quality comparison projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    prompt_contract_hash: str
    comparison_hash: str
    fixture_summary: JsonDict
    solar_summary: JsonDict
    review_gate: JsonDict
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("solar quality comparison projection must be a mapping")
        assert_public_projection_safe(payload)
        return payload


def _safe_run_id(run_id: str) -> str:
    if isinstance(run_id, str) and SAFE_RUN_ID_PATTERN.fullmatch(run_id):
        return run_id
    return "run-redacted"


def _positive_or_zero_int(value: object) -> bool:
    return type(value) is int and value >= 0


def _valid_contract_hash(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


def _check(
    checks: list[JsonDict],
    failures: list[str],
    *,
    name: str,
    passed: bool,
    reason: str,
) -> None:
    checks.append({"name": name, "passed": bool(passed)})
    if not passed:
        failures.append(reason)


def _fixture_summary(request: SolarPlannerQualityComparisonRequest) -> JsonDict:
    required = max(int(request.fixture_required_stage_count), 0)
    covered = max(min(int(request.fixture_covered_stage_count), required), 0)
    coverage_percent = round((covered / required) * 100, 1) if required else 0.0
    return {
        "stage_coverage": f"{covered}/{required}",
        "required_stage_count": required,
        "covered_stage_count": covered,
        "coverage_percent": coverage_percent,
        "artifact_count": max(int(request.fixture_artifact_count), 0),
    }


def _solar_response_projection(public_projection: JsonDict) -> JsonDict:
    response_projection = public_projection.get("response_projection", {})
    if isinstance(response_projection, dict):
        return response_projection
    return {}


def _solar_summary(
    request: SolarPlannerQualityComparisonRequest,
) -> JsonDict:
    public_projection = request.solar_live_spike_projection
    if not isinstance(public_projection, dict):
        public_projection = {}
    response_projection = _solar_response_projection(public_projection)
    section_count = max(int(response_projection.get("summary_section_count", 0) or 0), 0)
    artifact_hint_count = max(
        int(response_projection.get("artifact_hint_count", 0) or 0), 0
    )
    required = max(int(request.required_solar_section_count), 0)
    missing_required_stage_count = max(required - section_count, 0)
    return {
        "solar_live_spike_status": str(public_projection.get("status", "missing")),
        "solar_projection_version": str(public_projection.get("projection_version", "")),
        "response_contract_hash": str(
            response_projection.get("response_contract_hash", "")
        ),
        "summary_hash": str(response_projection.get("summary_hash", "")),
        "summary_section_count": section_count,
        "artifact_hint_count": artifact_hint_count,
        "required_section_count": required,
        "missing_required_stage_count": missing_required_stage_count,
        "provider_body_included": response_projection.get("provider_body_included")
        is True,
        "source_body_included": response_projection.get("source_body_included") is True,
    }


def _execution_boundary(public_projection: JsonDict) -> JsonDict:
    execution = public_projection.get("execution_boundary", {})
    if not isinstance(execution, dict):
        execution = {}
    return {
        "comparison_provider_calls": 0,
        "comparison_live_api_calls": 0,
        "comparison_network_calls": 0,
        "comparison_env_key_value_reads": 0,
        "observed_solar_provider_calls": int(execution.get("provider_calls", 0) or 0),
        "observed_solar_network_calls": int(execution.get("network_calls", 0) or 0),
        "observed_solar_env_key_value_reads": int(
            execution.get("env_key_value_reads", 0) or 0
        ),
        "sdk_imports": 0,
        "target_runtime_calls": 0,
        "server_start_calls": 0,
        "artifact_binding_calls": 0,
        "additional_live_call_count": 0,
    }


def _claim_boundary(status: str) -> JsonDict:
    return {
        "scope": "solar planner quality comparison over public projection",
        "status": status,
        "fixture_planner_default": True,
        "solar_output_auto_applied": False,
        "quality_proof_claim": False,
        "provider_generated_artifact": False,
        "target_runtime_outcome": False,
        "hosted_behavior_claim": False,
        "production_trust_claim": False,
    }


def _comparison_hash(
    *,
    request: SolarPlannerQualityComparisonRequest,
    fixture_summary: JsonDict,
    solar_summary: JsonDict,
) -> str:
    return stable_contract_hash(
        {
            "projection_version": SOLAR_PLANNER_QUALITY_COMPARISON_VERSION,
            "run_id": _safe_run_id(request.run_id),
            "prompt_contract_hash": request.prompt_contract_hash,
            "fixture_summary": fixture_summary,
            "solar_summary": solar_summary,
            "reviewer_approval_hash_present": _valid_contract_hash(
                request.reviewer_approval_hash
            ),
        }
    )


def compare_solar_planner_quality(
    request: SolarPlannerQualityComparisonRequest,
) -> SolarPlannerQualityComparisonResult:
    """Compare fixture and Solar public projections without side effects."""
    checks: list[JsonDict] = []
    failures: list[str] = []
    public_projection = (
        request.solar_live_spike_projection
        if isinstance(request.solar_live_spike_projection, dict)
        else {}
    )
    response_projection = _solar_response_projection(public_projection)
    fixture = _fixture_summary(request)
    solar = _solar_summary(request)

    _check(
        checks,
        failures,
        name="run_id_safe",
        passed=isinstance(request.run_id, str)
        and SAFE_RUN_ID_PATTERN.fullmatch(request.run_id) is not None,
        reason="run_id_invalid",
    )
    _check(
        checks,
        failures,
        name="prompt_contract_hash_valid",
        passed=_valid_contract_hash(request.prompt_contract_hash),
        reason="prompt_contract_hash_invalid",
    )
    _check(
        checks,
        failures,
        name="fixture_stage_coverage_complete",
        passed=fixture["required_stage_count"] == fixture["covered_stage_count"]
        and fixture["required_stage_count"] > 0,
        reason="fixture_stage_coverage_incomplete",
    )
    _check(
        checks,
        failures,
        name="fixture_artifact_count_present",
        passed=request.fixture_artifact_count >= 3,
        reason="fixture_artifact_count_insufficient",
    )
    _check(
        checks,
        failures,
        name="solar_live_projection_version_valid",
        passed=public_projection.get("projection_version")
        == SOLAR_PLANNER_LIVE_SPIKE_VERSION,
        reason="solar_projection_version_invalid",
    )
    _check(
        checks,
        failures,
        name="solar_live_projection_projected",
        passed=public_projection.get("status") == "projected",
        reason="solar_projection_not_projected",
    )
    _check(
        checks,
        failures,
        name="solar_response_hash_only",
        passed=_valid_contract_hash(response_projection.get("response_contract_hash"))
        and _valid_contract_hash(response_projection.get("summary_hash"))
        and response_projection.get("provider_body_included") is False
        and response_projection.get("source_body_included") is False,
        reason="solar_response_projection_not_hash_only",
    )
    _check(
        checks,
        failures,
        name="solar_required_sections_present",
        passed=solar["missing_required_stage_count"] == 0,
        reason="solar_required_sections_missing",
    )
    reviewer_hash_valid = _valid_contract_hash(request.reviewer_approval_hash)
    _check(
        checks,
        failures,
        name="reviewer_approval_hash_present",
        passed=reviewer_hash_valid,
        reason="reviewer_approval_missing",
    )
    _check(
        checks,
        failures,
        name="comparison_no_extra_live_call",
        passed=True,
        reason="comparison_extra_live_call_detected",
    )
    _check(
        checks,
        failures,
        name="target_runtime_closed",
        passed=True,
        reason="target_runtime_opened",
    )

    comparison_hash = _comparison_hash(
        request=request,
        fixture_summary=fixture,
        solar_summary=solar,
    )
    if failures:
        status = "review_blocked"
        reason = failures[0]
    else:
        status = "review_ready"
        reason = "solar_quality_comparison_ready_for_reviewer_bound_draft"
    failed_count = sum(1 for check in checks if not check["passed"])
    review_gate = {
        "status": "ready" if status == "review_ready" else "blocked",
        "reason": reason,
        "reviewer_approval_hash": request.reviewer_approval_hash
        if reviewer_hash_valid
        else "",
        "artifact_binding_permission": status == "review_ready",
        "artifact_binding_performed": False,
        "draft_artifact_creation_count": 0,
    }
    counts = {
        "comparison_count": 1,
        "check_count": len(checks),
        "failed_check_count": failed_count,
        "fixture_required_stage_count": fixture["required_stage_count"],
        "fixture_covered_stage_count": fixture["covered_stage_count"],
        "fixture_artifact_count": fixture["artifact_count"],
        "solar_response_projection_count": 1
        if public_projection.get("status") == "projected"
        else 0,
        "solar_summary_section_count": solar["summary_section_count"],
        "solar_artifact_hint_count": solar["artifact_hint_count"],
        "missing_required_stage_count": solar["missing_required_stage_count"],
        "reviewer_approval_count": 1 if reviewer_hash_valid else 0,
        "artifact_binding_permission_count": 1 if status == "review_ready" else 0,
        "artifact_binding_performed_count": 0,
        "additional_live_call_count": 0,
        "raw_provider_body_stored_count": 0,
        "raw_provider_body_returned_count": 0,
        "credential_value_exposure_count": 0,
        "input_text_exposure_count": 0,
        "target_runtime_call_count": 0,
        "server_start_count": 0,
        "status_review_ready_count": 1 if status == "review_ready" else 0,
        "status_review_blocked_count": 1 if status == "review_blocked" else 0,
    }
    return SolarPlannerQualityComparisonResult(
        projection_version=SOLAR_PLANNER_QUALITY_COMPARISON_VERSION,
        run_id=_safe_run_id(request.run_id),
        mode=SOLAR_PLANNER_QUALITY_COMPARISON_MODE,
        status=status,
        reason=reason,
        prompt_contract_hash=request.prompt_contract_hash,
        comparison_hash=comparison_hash,
        fixture_summary=fixture,
        solar_summary=solar,
        review_gate=review_gate,
        checks=checks,
        counts=counts,
        execution_boundary=_execution_boundary(public_projection),
        claim_boundary=_claim_boundary(status),
    )


def solar_quality_comparison_request_from_payload(
    payload: dict[str, Any],
) -> SolarPlannerQualityComparisonRequest:
    """Build a comparison request from API/demo payload."""
    return SolarPlannerQualityComparisonRequest(
        run_id=str(payload["run_id"]),
        prompt_contract_hash=str(payload["prompt_contract_hash"]),
        fixture_required_stage_count=int(payload.get("fixture_required_stage_count", 0)),
        fixture_covered_stage_count=int(payload.get("fixture_covered_stage_count", 0)),
        fixture_artifact_count=int(payload.get("fixture_artifact_count", 0)),
        solar_live_spike_projection=dict(payload.get("solar_live_spike_projection", {})),
        reviewer_approval_hash=str(payload.get("reviewer_approval_hash", "")),
        required_solar_section_count=int(
            payload.get(
                "required_solar_section_count",
                REQUIRED_SOLAR_QUALITY_SECTION_COUNT,
            )
        ),
        metadata={},
    )


__all__ = [
    "REQUIRED_SOLAR_QUALITY_SECTION_COUNT",
    "SOLAR_PLANNER_QUALITY_COMPARISON_MODE",
    "SOLAR_PLANNER_QUALITY_COMPARISON_VERSION",
    "SolarPlannerQualityComparisonRequest",
    "SolarPlannerQualityComparisonResult",
    "compare_solar_planner_quality",
    "solar_quality_comparison_request_from_payload",
]

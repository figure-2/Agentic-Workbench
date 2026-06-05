"""Solar planner draft artifact projections.

This module turns reviewer-approved Solar quality comparison evidence into
hash/count-only draft PlanningBlueprint and PRDPackage projections. It does not
perform another provider call and does not write canonical artifacts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from packages.core.exposure import sanitize_public_payload
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash

from .provider_boundary import CONTRACT_HASH_PATTERN, SAFE_RUN_ID_PATTERN
from .solar_quality_comparison import SOLAR_PLANNER_QUALITY_COMPARISON_VERSION


SOLAR_PLANNER_DRAFT_PROJECTION_VERSION = "solar-planner-draft-projection-public-v1"
SOLAR_PLANNER_DRAFT_PROJECTION_MODE = (
    "solar_draft_projection_from_quality_comparison"
)
DRAFT_PLANNING_BLUEPRINT_LABEL = "PlanningBlueprint"
DRAFT_PRD_PACKAGE_LABEL = "PRDPackage"
DRAFT_ARTIFACT_LABELS = (
    DRAFT_PLANNING_BLUEPRINT_LABEL,
    DRAFT_PRD_PACKAGE_LABEL,
)


@dataclass(frozen=True, slots=True)
class SolarPlannerDraftProjectionRequest:
    """Public-safe request for Solar-derived draft projections."""

    run_id: str
    prompt_contract_hash: str
    solar_quality_comparison_hash: str
    solar_quality_comparison_projection: JsonDict = field(default_factory=dict)
    reviewer_approval_hash: str = ""
    requested_draft_labels: tuple[str, ...] = DRAFT_ARTIFACT_LABELS
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SolarPlannerDraftProjectionResult:
    """Hash/count-only Solar draft projection result."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    prompt_contract_hash: str
    source_quality_comparison_hash: str
    draft_projection_hash: str
    draft_artifacts: list[JsonDict]
    review_gate: JsonDict
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("solar draft projection must be a mapping")
        assert_public_projection_safe(payload)
        return payload


def _safe_run_id(run_id: str) -> str:
    if isinstance(run_id, str) and SAFE_RUN_ID_PATTERN.fullmatch(run_id):
        return run_id
    return "run-redacted"


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


def _quality_projection(request: SolarPlannerDraftProjectionRequest) -> JsonDict:
    if isinstance(request.solar_quality_comparison_projection, dict):
        return request.solar_quality_comparison_projection
    return {}


def _quality_review_gate(quality_projection: JsonDict) -> JsonDict:
    review_gate = quality_projection.get("review_gate", {})
    if isinstance(review_gate, dict):
        return review_gate
    return {}


def _quality_solar_summary(quality_projection: JsonDict) -> JsonDict:
    solar_summary = quality_projection.get("solar_summary", {})
    if isinstance(solar_summary, dict):
        return solar_summary
    return {}


def _quality_counts(quality_projection: JsonDict) -> JsonDict:
    counts = quality_projection.get("counts", {})
    if isinstance(counts, dict):
        return counts
    return {}


def _quality_comparison_hash(quality_projection: JsonDict) -> str:
    value = quality_projection.get("comparison_hash", "")
    return value if isinstance(value, str) else ""


def _draft_artifact_hash(
    *,
    request: SolarPlannerDraftProjectionRequest,
    artifact_label: str,
    source_quality_comparison_hash: str,
) -> str:
    return stable_contract_hash(
        {
            "projection_version": SOLAR_PLANNER_DRAFT_PROJECTION_VERSION,
            "run_id": _safe_run_id(request.run_id),
            "prompt_contract_hash": request.prompt_contract_hash,
            "source_quality_comparison_hash": source_quality_comparison_hash,
            "artifact_label": artifact_label,
            "canonical_artifact_written": False,
        }
    )


def _draft_projection_hash(
    *,
    request: SolarPlannerDraftProjectionRequest,
    source_quality_comparison_hash: str,
    draft_artifacts: list[JsonDict],
) -> str:
    return stable_contract_hash(
        {
            "projection_version": SOLAR_PLANNER_DRAFT_PROJECTION_VERSION,
            "run_id": _safe_run_id(request.run_id),
            "prompt_contract_hash": request.prompt_contract_hash,
            "source_quality_comparison_hash": source_quality_comparison_hash,
            "draft_artifacts": draft_artifacts,
            "canonical_artifact_written": False,
        }
    )


def _draft_artifacts(
    *,
    request: SolarPlannerDraftProjectionRequest,
    source_quality_comparison_hash: str,
    quality_projection: JsonDict,
) -> list[JsonDict]:
    solar_summary = _quality_solar_summary(quality_projection)
    section_count = int(solar_summary.get("summary_section_count", 0) or 0)
    artifact_hint_count = int(solar_summary.get("artifact_hint_count", 0) or 0)
    artifacts: list[JsonDict] = []
    for artifact_label in request.requested_draft_labels:
        artifacts.append(
            {
                "artifact_label": artifact_label,
                "draft_artifact_hash": _draft_artifact_hash(
                    request=request,
                    artifact_label=artifact_label,
                    source_quality_comparison_hash=source_quality_comparison_hash,
                ),
                "source_quality_comparison_hash": source_quality_comparison_hash,
                "source_section_label_count": section_count,
                "source_artifact_hint_count": artifact_hint_count,
                "section_body_included": False,
                "provider_body_included": False,
                "canonical_artifact_written": False,
            }
        )
    return artifacts


def _execution_boundary() -> JsonDict:
    return {
        "draft_projection_provider_calls": 0,
        "draft_projection_live_api_calls": 0,
        "draft_projection_network_calls": 0,
        "draft_projection_env_key_value_reads": 0,
        "sdk_imports": 0,
        "target_runtime_calls": 0,
        "server_start_calls": 0,
        "canonical_artifact_write_calls": 0,
        "additional_live_call_count": 0,
    }


def _claim_boundary(status: str) -> JsonDict:
    return {
        "scope": "solar planner draft projection over reviewer-approved quality evidence",
        "status": status,
        "fixture_planner_default": True,
        "solar_output_auto_applied": False,
        "canonical_artifact_mutated": False,
        "provider_generated_artifact": False,
        "target_runtime_outcome": False,
        "hosted_behavior_claim": False,
        "production_trust_claim": False,
    }


def project_solar_planner_drafts(
    request: SolarPlannerDraftProjectionRequest,
) -> SolarPlannerDraftProjectionResult:
    """Project draft PlanningBlueprint/PRDPackage evidence without side effects."""
    checks: list[JsonDict] = []
    failures: list[str] = []
    quality_projection = _quality_projection(request)
    review_gate = _quality_review_gate(quality_projection)
    solar_summary = _quality_solar_summary(quality_projection)
    quality_counts = _quality_counts(quality_projection)
    projected_quality_hash = _quality_comparison_hash(quality_projection)
    reviewer_hash_valid = _valid_contract_hash(request.reviewer_approval_hash)

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
        name="quality_projection_version_valid",
        passed=quality_projection.get("projection_version")
        == SOLAR_PLANNER_QUALITY_COMPARISON_VERSION,
        reason="quality_projection_version_invalid",
    )
    _check(
        checks,
        failures,
        name="quality_comparison_hash_valid",
        passed=_valid_contract_hash(request.solar_quality_comparison_hash),
        reason="quality_comparison_hash_invalid",
    )
    _check(
        checks,
        failures,
        name="quality_comparison_hash_matches",
        passed=request.solar_quality_comparison_hash == projected_quality_hash
        and _valid_contract_hash(projected_quality_hash),
        reason="quality_comparison_hash_mismatch",
    )
    _check(
        checks,
        failures,
        name="quality_review_ready",
        passed=quality_projection.get("status") == "review_ready",
        reason="quality_projection_not_review_ready",
    )
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
        name="reviewer_approval_hash_matches_quality_gate",
        passed=reviewer_hash_valid
        and review_gate.get("reviewer_approval_hash") == request.reviewer_approval_hash,
        reason="reviewer_approval_hash_mismatch",
    )
    _check(
        checks,
        failures,
        name="artifact_binding_permission_ready",
        passed=review_gate.get("artifact_binding_permission") is True
        and review_gate.get("artifact_binding_performed") is False,
        reason="artifact_binding_permission_not_ready",
    )
    _check(
        checks,
        failures,
        name="quality_stage_requirements_met",
        passed=int(quality_counts.get("missing_required_stage_count", -1)) == 0
        and int(solar_summary.get("missing_required_stage_count", -1)) == 0,
        reason="quality_required_stage_missing",
    )
    _check(
        checks,
        failures,
        name="quality_projection_hash_only",
        passed=solar_summary.get("provider_body_included") is False
        and solar_summary.get("source_body_included") is False,
        reason="quality_projection_not_hash_only",
    )
    _check(
        checks,
        failures,
        name="canonical_artifact_write_closed",
        passed=True,
        reason="canonical_artifact_write_opened",
    )
    _check(
        checks,
        failures,
        name="additional_live_call_closed",
        passed=True,
        reason="additional_live_call_detected",
    )
    _check(
        checks,
        failures,
        name="target_runtime_closed",
        passed=True,
        reason="target_runtime_opened",
    )

    status = "blocked" if failures else "draft_projected"
    reason = failures[0] if failures else "solar_draft_projection_ready_for_review"
    draft_artifacts = (
        []
        if failures
        else _draft_artifacts(
            request=request,
            source_quality_comparison_hash=request.solar_quality_comparison_hash,
            quality_projection=quality_projection,
        )
    )
    draft_projection_hash = _draft_projection_hash(
        request=request,
        source_quality_comparison_hash=(
            request.solar_quality_comparison_hash
            if _valid_contract_hash(request.solar_quality_comparison_hash)
            else ""
        ),
        draft_artifacts=draft_artifacts,
    )
    failed_count = sum(1 for check in checks if not check["passed"])
    counts = {
        "draft_projection_count": 1 if status == "draft_projected" else 0,
        "draft_artifact_projection_count": len(draft_artifacts),
        "draft_planning_blueprint_projection_count": sum(
            1
            for artifact in draft_artifacts
            if artifact.get("artifact_label") == DRAFT_PLANNING_BLUEPRINT_LABEL
        ),
        "draft_prd_package_projection_count": sum(
            1
            for artifact in draft_artifacts
            if artifact.get("artifact_label") == DRAFT_PRD_PACKAGE_LABEL
        ),
        "source_quality_comparison_count": 1
        if quality_projection.get("projection_version")
        == SOLAR_PLANNER_QUALITY_COMPARISON_VERSION
        else 0,
        "quality_comparison_hash_match_count": 1
        if request.solar_quality_comparison_hash == projected_quality_hash
        and _valid_contract_hash(projected_quality_hash)
        else 0,
        "reviewer_approval_count": 1 if reviewer_hash_valid else 0,
        "canonical_artifact_write_count": 0,
        "additional_live_call_count": 0,
        "provider_call_count": 0,
        "env_value_read_count": 0,
        "network_call_count": 0,
        "sdk_import_count": 0,
        "raw_provider_body_stored_count": 0,
        "raw_provider_body_returned_count": 0,
        "credential_value_exposure_count": 0,
        "input_text_exposure_count": 0,
        "target_runtime_call_count": 0,
        "server_start_count": 0,
        "check_count": len(checks),
        "failed_check_count": failed_count,
        "status_draft_projected_count": 1 if status == "draft_projected" else 0,
        "status_blocked_count": 1 if status == "blocked" else 0,
    }
    draft_review_gate = {
        "status": "ready" if status == "draft_projected" else "blocked",
        "reason": reason,
        "reviewer_approval_hash": request.reviewer_approval_hash
        if reviewer_hash_valid
        else "",
        "source_quality_comparison_hash": request.solar_quality_comparison_hash
        if _valid_contract_hash(request.solar_quality_comparison_hash)
        else "",
        "canonical_artifact_write_permission": False,
        "canonical_artifact_write_performed": False,
        "draft_artifact_creation_count": len(draft_artifacts),
    }
    return SolarPlannerDraftProjectionResult(
        projection_version=SOLAR_PLANNER_DRAFT_PROJECTION_VERSION,
        run_id=_safe_run_id(request.run_id),
        mode=SOLAR_PLANNER_DRAFT_PROJECTION_MODE,
        status=status,
        reason=reason,
        prompt_contract_hash=request.prompt_contract_hash,
        source_quality_comparison_hash=request.solar_quality_comparison_hash
        if _valid_contract_hash(request.solar_quality_comparison_hash)
        else "",
        draft_projection_hash=draft_projection_hash,
        draft_artifacts=draft_artifacts,
        review_gate=draft_review_gate,
        checks=checks,
        counts=counts,
        execution_boundary=_execution_boundary(),
        claim_boundary=_claim_boundary(status),
    )


def solar_draft_projection_request_from_payload(
    payload: dict[str, Any],
) -> SolarPlannerDraftProjectionRequest:
    """Build a draft projection request from API/demo payload."""
    requested_labels = payload.get("requested_draft_labels", DRAFT_ARTIFACT_LABELS)
    if not isinstance(requested_labels, list | tuple):
        requested_labels = DRAFT_ARTIFACT_LABELS
    safe_labels = tuple(
        str(label)
        for label in requested_labels
        if str(label) in DRAFT_ARTIFACT_LABELS
    )
    return SolarPlannerDraftProjectionRequest(
        run_id=str(payload["run_id"]),
        prompt_contract_hash=str(payload["prompt_contract_hash"]),
        solar_quality_comparison_hash=str(
            payload.get("solar_quality_comparison_hash", "")
        ),
        solar_quality_comparison_projection=dict(
            payload.get("solar_quality_comparison_projection", {})
        ),
        reviewer_approval_hash=str(payload.get("reviewer_approval_hash", "")),
        requested_draft_labels=safe_labels or DRAFT_ARTIFACT_LABELS,
        metadata={},
    )


__all__ = [
    "DRAFT_ARTIFACT_LABELS",
    "DRAFT_PLANNING_BLUEPRINT_LABEL",
    "DRAFT_PRD_PACKAGE_LABEL",
    "SOLAR_PLANNER_DRAFT_PROJECTION_MODE",
    "SOLAR_PLANNER_DRAFT_PROJECTION_VERSION",
    "SolarPlannerDraftProjectionRequest",
    "SolarPlannerDraftProjectionResult",
    "project_solar_planner_drafts",
    "solar_draft_projection_request_from_payload",
]

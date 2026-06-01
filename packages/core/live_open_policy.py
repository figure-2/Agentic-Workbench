"""Fail-closed live-open policy gate.

This module decides whether a future Solar Pro 3 provider or DAACS target
runtime integration is ready for a separate implementation unit. It never
reads environment values, imports provider SDKs, opens network sockets, invokes
runtime code, or grants execution permission by itself.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

from .exposure import sanitize_public_payload


SOLAR_PROVIDER_SURFACE = "solar_provider"
DAACS_TARGET_RUNTIME_SURFACE = "daacs_target_runtime"
LIVE_OPEN_SURFACES = (SOLAR_PROVIDER_SURFACE, DAACS_TARGET_RUNTIME_SURFACE)
SOLAR_PRO_3_ENV_KEY_NAME = "UPSTAGE_API_KEY"

LIVE_OPEN_REQUIRED_CONTROLS = (
    "approval_policy_ready",
    "replay_persistence_ready",
    "cost_quota_guard_ready",
    "timeout_guard_ready",
    "workspace_sandbox_ready",
    "write_allowlist_ready",
    "rollback_plan_ready",
    "secret_redaction_ready",
    "artifact_sanitizer_ready",
    "audit_projection_ready",
)

_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


@dataclass(frozen=True, slots=True)
class LiveOpenRequest:
    """Readiness envelope for a future live/provider implementation unit."""

    run_id: str
    surface: str
    env_key_name: str = ""
    approval_policy_ready: bool = False
    replay_persistence_ready: bool = False
    cost_quota_guard_ready: bool = False
    timeout_guard_ready: bool = False
    workspace_sandbox_ready: bool = False
    write_allowlist_ready: bool = False
    rollback_plan_ready: bool = False
    secret_redaction_ready: bool = False
    artifact_sanitizer_ready: bool = False
    audit_projection_ready: bool = False
    requested_live_call_count: int = 0
    requested_runtime_write_count: int = 0
    requested_network_call_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LiveOpenDecision:
    """Sanitized policy decision.

    `allowed_to_execute` intentionally remains false in AW-LIVE-00. A passing
    decision means only that a separate live integration task may be proposed.
    """

    run_id: str
    surface: str
    status: str
    eligible_for_live_open: bool
    allowed_to_execute: bool
    reason_codes: list[str]
    checks: list[dict[str, Any]]
    execution_boundary: dict[str, Any]
    claim_boundary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return sanitize_public_payload(asdict(self))


def _check(
    checks: list[dict[str, Any]],
    *,
    name: str,
    passed: bool,
    reason_code: str,
    message: str,
) -> None:
    checks.append(
        {
            "name": name,
            "passed": bool(passed),
            "reason_code": "" if passed else reason_code,
            "message": "ready" if passed else message,
        }
    )


def _safe_run_id(run_id: str) -> str:
    if isinstance(run_id, str) and _RUN_ID_PATTERN.fullmatch(run_id):
        return run_id
    return "run-redacted"


def _zero_execution_boundary(surface: str, env_key_name: str) -> dict[str, Any]:
    public_env_key_name = (
        env_key_name
        if surface == SOLAR_PROVIDER_SURFACE and env_key_name == SOLAR_PRO_3_ENV_KEY_NAME
        else ""
    )
    return {
        "policy_gate": "aw-live-00",
        "surface": surface if surface in LIVE_OPEN_SURFACES else "unknown",
        "env_key_name": public_env_key_name,
        "live_execution_opened": False,
        "allowed_to_execute": False,
        "solar_provider_calls": 0,
        "target_runtime_calls": 0,
        "provider_imports": 0,
        "network_calls": 0,
        "subprocess_calls": 0,
        "filesystem_writes": 0,
        "env_key_value_loaded": False,
    }


def _claim_boundary() -> dict[str, Any]:
    return {
        "claim_scope": "local policy gate only",
        "public_wording": "live-open readiness policy, zero provider/runtime calls",
        "requires_separate_implementation_unit": True,
        "hosted_or_production_claim": False,
    }


def _shape_checks(request: LiveOpenRequest, checks: list[dict[str, Any]]) -> None:
    _check(
        checks,
        name="run_id_safe",
        passed=isinstance(request.run_id, str) and _RUN_ID_PATTERN.fullmatch(request.run_id) is not None,
        reason_code="run_id_invalid",
        message="run_id must be a safe correlation id.",
    )
    _check(
        checks,
        name="surface_supported",
        passed=request.surface in LIVE_OPEN_SURFACES,
        reason_code="surface_unknown",
        message="surface must be solar_provider or daacs_target_runtime.",
    )
    if request.surface == SOLAR_PROVIDER_SURFACE:
        _check(
            checks,
            name="env_key_name_reference_only",
            passed=request.env_key_name == SOLAR_PRO_3_ENV_KEY_NAME,
            reason_code="env_key_name_invalid",
            message="Solar provider readiness may reference only the UPSTAGE_API_KEY name.",
        )
    elif request.surface == DAACS_TARGET_RUNTIME_SURFACE:
        _check(
            checks,
            name="runtime_env_key_absent",
            passed=request.env_key_name == "",
            reason_code="runtime_env_key_not_expected",
            message="DAACS target runtime readiness must not carry provider env key names.",
        )

    for field_name in (
        "requested_live_call_count",
        "requested_runtime_write_count",
        "requested_network_call_count",
    ):
        value = getattr(request, field_name)
        _check(
            checks,
            name=f"{field_name}_zero",
            passed=type(value) is int and value == 0,
            reason_code=f"{field_name}_not_zero",
            message=f"{field_name} must stay explicit zero in AW-LIVE-00.",
        )


def _readiness_checks(request: LiveOpenRequest, checks: list[dict[str, Any]]) -> None:
    for field_name in LIVE_OPEN_REQUIRED_CONTROLS:
        value = getattr(request, field_name)
        _check(
            checks,
            name=field_name,
            passed=type(value) is bool and value is True,
            reason_code=f"{field_name}_missing",
            message=f"{field_name} must be true before live-open can be eligible.",
        )


def evaluate_live_open_request(request: LiveOpenRequest) -> LiveOpenDecision:
    """Return a sanitized fail-closed live-open readiness decision."""
    checks: list[dict[str, Any]] = []
    _shape_checks(request, checks)
    _readiness_checks(request, checks)

    failing_reason_codes = [
        str(check["reason_code"]) for check in checks if not check["passed"] and check["reason_code"]
    ]
    if failing_reason_codes:
        status = "blocked"
        eligible = False
        reason_codes = failing_reason_codes
    else:
        status = "eligible_for_separate_live_implementation"
        eligible = True
        reason_codes = ["separate_live_implementation_required"]

    return LiveOpenDecision(
        run_id=_safe_run_id(request.run_id),
        surface=request.surface if request.surface in LIVE_OPEN_SURFACES else "unknown",
        status=status,
        eligible_for_live_open=eligible,
        allowed_to_execute=False,
        reason_codes=reason_codes,
        checks=checks,
        execution_boundary=_zero_execution_boundary(request.surface, request.env_key_name),
        claim_boundary=_claim_boundary(),
    )


__all__ = [
    "DAACS_TARGET_RUNTIME_SURFACE",
    "LIVE_OPEN_REQUIRED_CONTROLS",
    "LIVE_OPEN_SURFACES",
    "LiveOpenDecision",
    "LiveOpenRequest",
    "SOLAR_PRO_3_ENV_KEY_NAME",
    "SOLAR_PROVIDER_SURFACE",
    "evaluate_live_open_request",
]

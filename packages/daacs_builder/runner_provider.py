"""Runner provider skeleton and registry for DAACS execution boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Protocol

from packages.core.pathing import normalize_public_relative_path
from packages.core.exposure import sanitize_public_payload
from packages.core.schemas import (
    ImplementationBrief,
    JsonDict,
    SpecApproval,
    VerificationReport,
    stable_contract_hash,
    utc_now,
)

from .offline_runner import DAACSOfflineRunner


RUNNER_MODES = {"offline", "dry_run", "live"}
LIVE_MODE = "live"
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,80}$")


@dataclass(slots=True)
class ApprovalRecord:
    """Structured approval required before any future live execution."""

    approved_by: str
    approved_at: str
    run_id: str
    mode: str
    allowed_operations: list[str]
    max_provider_calls: int
    max_subprocess_calls: int
    max_package_installs: int
    max_server_starts: int
    max_files_written: int
    workspace_root: str
    expires_at: str
    rollback_plan_id: str
    audit_log_id: str


@dataclass(slots=True)
class RunnerPolicy:
    """Explicit execution permissions. Defaults are fail-closed."""

    allow_provider_calls: bool = False
    allow_cli_agent: bool = False
    allow_subprocess: bool = False
    allow_package_install: bool = False
    allow_server_start: bool = False
    allow_filesystem_write: bool = False
    allow_network: bool = False
    timeout_seconds: int = 0
    workspace_root: str = ""


@dataclass(slots=True)
class RunnerRequest:
    """Request envelope consumed by runner providers."""

    run_id: str
    mode: str
    state: dict[str, Any]
    policy: RunnerPolicy = field(default_factory=RunnerPolicy)
    implementation_brief: ImplementationBrief | None = None
    spec_approval: SpecApproval | None = None
    approval: ApprovalRecord | None = None
    plan: RunnerPlan | None = None


@dataclass(slots=True)
class RunnerPlan:
    """Side-effect-free execution plan emitted by the dry-run runner boundary."""

    run_id: str
    mode: str
    implementation_brief_hash: str
    build_spec_hash: str
    planned_actions: list[JsonDict] = field(default_factory=list)
    artifact_manifest: list[JsonDict] = field(default_factory=list)
    required_approvals: list[JsonDict] = field(default_factory=list)
    side_effects: JsonDict = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id is required")
        if self.mode != "dry_run":
            raise ValueError("RunnerPlan mode must be dry_run")
        if not self.implementation_brief_hash.strip():
            raise ValueError("implementation_brief_hash is required")
        if not self.build_spec_hash.strip():
            raise ValueError("build_spec_hash is required")
        if not self.planned_actions:
            raise ValueError("planned_actions are required")
        for key, value in self.side_effects.items():
            if value != 0:
                raise ValueError(f"dry-run side effect must be zero: {key}")

    def to_dict(self) -> JsonDict:
        self.validate()
        normalized_manifest: list[JsonDict] = []
        for item in self.artifact_manifest:
            if not isinstance(item, dict):
                continue
            normalized = dict(item)
            if normalized.get("path"):
                normalized["path"] = normalize_public_relative_path(str(normalized["path"]))
            normalized_manifest.append(normalized)
        payload = {
            "run_id": self.run_id,
            "mode": self.mode,
            "implementation_brief_hash": self.implementation_brief_hash,
            "build_spec_hash": self.build_spec_hash,
            "planned_actions": self.planned_actions,
            "artifact_manifest": normalized_manifest,
            "required_approvals": self.required_approvals,
            "side_effects": self.side_effects,
            "created_at": self.created_at,
        }
        payload["plan_hash"] = stable_contract_hash(
            {
                "run_id": self.run_id,
                "mode": self.mode,
                "implementation_brief_hash": self.implementation_brief_hash,
                "build_spec_hash": self.build_spec_hash,
                "planned_actions": self.planned_actions,
                "artifact_manifest": normalized_manifest,
                "required_approvals": self.required_approvals,
                "side_effects": self.side_effects,
            }
        )
        return sanitize_public_payload(payload)


@dataclass(slots=True)
class RunnerResult:
    """Mode-aware result wrapper around VerificationReport."""

    run_id: str
    mode: str
    status: str
    verification_report: VerificationReport
    plan: RunnerPlan | None = None
    artifact_manifest: list[dict[str, Any]] = field(default_factory=list)
    audit_events: list[dict[str, Any]] = field(default_factory=list)


class RunnerProvider(Protocol):
    """Minimal provider contract for runner mode dispatch."""

    mode: str

    def run(self, request: RunnerRequest) -> RunnerResult:
        """Run or block a runner request."""


def _zero_side_effect_metrics() -> dict[str, int]:
    return {
        "live_llm_calls": 0,
        "live_api_calls": 0,
        "provider_calls": 0,
        "cli_agent_invocations": 0,
        "subprocess_calls": 0,
        "package_install_calls": 0,
        "server_start_calls": 0,
        "filesystem_writes": 0,
        "provider_imports": 0,
        "network_calls": 0,
        "approval_bypass_count": 0,
    }


def is_safe_run_id(run_id: str) -> bool:
    return (
        isinstance(run_id, str)
        and RUN_ID_PATTERN.fullmatch(run_id) is not None
        and ".." not in run_id
        and "/" not in run_id
        and "\\" not in run_id
    )


def safe_public_run_id(run_id: str) -> str:
    return run_id if is_safe_run_id(run_id) else "invalid-run-id"


def _blocked_result(
    *,
    request: RunnerRequest,
    check_name: str,
    error: str,
    metrics: dict[str, int] | None = None,
) -> RunnerResult:
    merged_metrics = {
        **_zero_side_effect_metrics(),
        "boundary_mode": request.mode,
        "runner_admission_block_count": 1,
        **(metrics or {}),
    }
    report_run_id = safe_public_run_id(request.run_id)
    report = VerificationReport(
        run_id=report_run_id,
        passed=False,
        checks=[{"name": check_name, "passed": False}],
        errors=[error],
        generated_files=[],
        metrics=merged_metrics,
    )
    return RunnerResult(
        run_id=report_run_id,
        mode=request.mode,
        status="blocked",
        verification_report=report,
    )


class OfflineRunnerProvider:
    """Provider that delegates to the existing DAACSOfflineRunner."""

    mode = "offline"

    def __init__(self, runner: DAACSOfflineRunner | None = None) -> None:
        self.runner = runner or DAACSOfflineRunner()

    def run(self, request: RunnerRequest) -> RunnerResult:
        report = self.runner.run(request.state)
        report.metrics["boundary_mode"] = "offline"
        report.metrics.setdefault("approval_bypass_count", 0)
        status = "passed" if report.passed else "failed"
        return RunnerResult(
            run_id=request.run_id,
            mode="offline",
            status=status,
            verification_report=report,
            artifact_manifest=[],
            audit_events=[],
        )


class RunnerProviderRegistry:
    """Fail-closed registry for runner providers."""

    def __init__(self) -> None:
        self._providers: dict[str, RunnerProvider] = {}

    def register(self, provider: RunnerProvider) -> None:
        self._providers[provider.mode] = provider

    def registered_modes(self) -> list[str]:
        return sorted(self._providers)

    def run(self, request: RunnerRequest) -> RunnerResult:
        if request.mode not in RUNNER_MODES:
            return _blocked_result(
                request=request,
                check_name="runner_mode_known",
                error=f"unknown runner mode: {request.mode}",
                metrics={"runner_registry_unknown_mode_block_count": 1},
            )

        if request.mode == LIVE_MODE and request.approval is None:
            return _blocked_result(
                request=request,
                check_name="live_approval_present",
                error="live runner mode requires a structured approval record.",
                metrics={
                    "approval_bypass_count": 1,
                    "live_mode_without_approval_block_count": 1,
                },
            )

        if request.mode == LIVE_MODE and not isinstance(request.approval, ApprovalRecord):
            return _blocked_result(
                request=request,
                check_name="live_approval_valid",
                error="live runner mode requires structured ApprovalRecord approval.",
                metrics={
                    "approval_bypass_count": 1,
                    "live_mode_malformed_approval_block_count": 1,
                },
            )

        provider = self._providers.get(request.mode)
        if provider is None:
            return _blocked_result(
                request=request,
                check_name=f"{request.mode}_runner_registered",
                error=f"runner provider is not registered for mode: {request.mode}",
                metrics={"runner_registry_missing_provider_block_count": 1},
            )

        return provider.run(request)


def default_runner_provider_registry() -> RunnerProviderRegistry:
    """Create the default registry with fail-closed mode providers."""
    from .dry_run_runner import DryRunRunnerProvider
    from .live_runner import LiveRunnerProvider

    registry = RunnerProviderRegistry()
    registry.register(OfflineRunnerProvider())
    registry.register(DryRunRunnerProvider())
    registry.register(LiveRunnerProvider())
    return registry

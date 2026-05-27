"""Runner provider skeleton and registry for DAACS execution boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from packages.core.schemas import VerificationReport

from .offline_runner import DAACSOfflineRunner


RUNNER_MODES = {"offline", "dry_run", "live"}
LIVE_MODE = "live"


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
    approval: ApprovalRecord | None = None


@dataclass(slots=True)
class RunnerResult:
    """Mode-aware result wrapper around VerificationReport."""

    run_id: str
    mode: str
    status: str
    verification_report: VerificationReport
    plan: dict[str, Any] | None = None
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
        "approval_bypass_count": 0,
    }


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
    report = VerificationReport(
        run_id=request.run_id,
        passed=False,
        checks=[{"name": check_name, "passed": False}],
        errors=[error],
        generated_files=[],
        metrics=merged_metrics,
    )
    return RunnerResult(
        run_id=request.run_id,
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
    """Create the default registry. Only offline is executable in AW-NEXT-06."""
    registry = RunnerProviderRegistry()
    registry.register(OfflineRunnerProvider())
    return registry

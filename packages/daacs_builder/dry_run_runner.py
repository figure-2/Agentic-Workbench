"""Side-effect-free DAACS dry-run runner.

The dry-run runner converts an approved ImplementationBrief into a RunnerPlan.
It does not import DAACS runtime modules, call providers, spawn subprocesses,
install packages, start servers, or write files.
"""

from __future__ import annotations

from typing import Any

from packages.core.schemas import (
    ImplementationBrief,
    SpecApproval,
    VerificationReport,
)

from .adapters import ensure_implementation_approved
from .offline_runner import DAACSOfflineRunner, find_blocked_operation_attempts
from .runner_provider import RunnerPlan, RunnerRequest, RunnerResult


ZERO_DRY_RUN_SIDE_EFFECTS: dict[str, int] = {
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
}


def _blocked_report(
    *,
    run_id: str,
    check_name: str,
    error: str,
    metrics: dict[str, int] | None = None,
) -> VerificationReport:
    return VerificationReport(
        run_id=run_id,
        passed=False,
        checks=[{"name": check_name, "passed": False}],
        errors=[error],
        generated_files=[],
        metrics={
            **ZERO_DRY_RUN_SIDE_EFFECTS,
            "boundary_mode": "dry_run",
            "approval_bypass_count": 1,
            "runner_admission_block_count": 1,
            "executed_action_count": 0,
            "simulated_action_count": 0,
            "plan_sanitization_failure_count": 0,
            "generated_payload_in_dry_run_count": 0,
            **(metrics or {}),
        },
    )


def _expected_artifacts(run_id: str, build_spec: dict[str, Any]) -> list[dict[str, Any]]:
    app_name = str(build_spec.get("app_name") or "agentic-app")
    return [
        {
            "kind": "backend_source",
            "path": f"runs/{run_id}/{app_name}/backend",
            "status": "planned_only",
        },
        {
            "kind": "frontend_source",
            "path": f"runs/{run_id}/{app_name}/frontend",
            "status": "planned_only",
        },
        {
            "kind": "verification_report",
            "path": f"runs/{run_id}/{app_name}/verification-report.json",
            "status": "planned_only",
        },
    ]


def _planned_actions(brief: ImplementationBrief) -> list[dict[str, Any]]:
    build_spec = brief.build_spec
    actions: list[dict[str, Any]] = []
    for task in brief.daacs_tasks:
        role = str(task.get("role", "task"))
        if role == "backend":
            actions.append(
                {
                    "id": "plan-backend-generation",
                    "role": "backend",
                    "action_type": "simulate_code_generation",
                    "summary": "Plan backend files from BuildSpec endpoints and data models.",
                    "endpoint_count": len(build_spec.get("api_spec", {}).get("endpoints", [])),
                    "will_write_files": False,
                    "will_call_provider": False,
                    "will_spawn_subprocess": False,
                }
            )
        elif role == "frontend":
            actions.append(
                {
                    "id": "plan-frontend-generation",
                    "role": "frontend",
                    "action_type": "simulate_code_generation",
                    "summary": "Plan frontend files from BuildSpec pages, components, and API calls.",
                    "api_call_count": len(build_spec.get("frontend_spec", {}).get("api_calls", [])),
                    "will_write_files": False,
                    "will_call_provider": False,
                    "will_spawn_subprocess": False,
                }
            )
        elif role == "verifier":
            actions.append(
                {
                    "id": "plan-verification",
                    "role": "verifier",
                    "action_type": "simulate_verification",
                    "summary": "Plan verification checks from acceptance criteria and path boundaries.",
                    "acceptance_criteria_count": len(build_spec.get("acceptance_criteria", [])),
                    "will_write_files": False,
                    "will_call_provider": False,
                    "will_spawn_subprocess": False,
                }
            )
    return actions or [
        {
            "id": "plan-build-contract",
            "role": "orchestrator",
            "action_type": "simulate_planning",
            "summary": "Plan DAACS build from approved ImplementationBrief.",
            "will_write_files": False,
            "will_call_provider": False,
            "will_spawn_subprocess": False,
        }
    ]


class DAACSDryRunRunner:
    """Create a RunnerPlan from approved contracts without side effects."""

    def __init__(self, offline_runner: DAACSOfflineRunner | None = None) -> None:
        self.offline_runner = offline_runner or DAACSOfflineRunner()

    def run(
        self,
        *,
        run_id: str,
        state: dict[str, Any],
        implementation_brief: ImplementationBrief | None,
        approval: SpecApproval | None,
    ) -> tuple[RunnerPlan | None, VerificationReport]:
        if implementation_brief is None:
            return None, _blocked_report(
                run_id=run_id,
                check_name="implementation_brief_present",
                error="dry-run requires an approved ImplementationBrief.",
                metrics={"implementation_brief_missing_block_count": 1},
            )
        if approval is None:
            return None, _blocked_report(
                run_id=run_id,
                check_name="spec_approval_present",
                error="dry-run requires a SpecApproval matching the ImplementationBrief.",
                metrics={"spec_approval_missing_block_count": 1},
            )

        try:
            ensure_implementation_approved(implementation_brief, approval)
        except ValueError as exc:
            return None, _blocked_report(
                run_id=run_id,
                check_name="spec_approval_matches_brief",
                error=str(exc),
                metrics={"spec_approval_mismatch_block_count": 1},
            )

        offline_report = self.offline_runner.run(state)
        if not offline_report.passed:
            offline_report.metrics.update(
                {
                    **ZERO_DRY_RUN_SIDE_EFFECTS,
                    "boundary_mode": "dry_run",
                    "dry_run_state_rejection_count": 1,
                    "executed_action_count": 0,
                }
            )
            return None, offline_report

        blocked_findings = find_blocked_operation_attempts(implementation_brief.to_dict())
        if blocked_findings:
            return None, _blocked_report(
                run_id=run_id,
                check_name="implementation_brief_side_effect_free",
                error="ImplementationBrief contains blocked operation payloads.",
                metrics={
                    "blocked_operation_attempt_count": len(blocked_findings),
                    "approval_bypass_count": 0,
                },
            )

        brief_payload = implementation_brief.to_dict()
        brief_hash = str(brief_payload["brief_hash"])
        actions = _planned_actions(implementation_brief)
        plan = RunnerPlan(
            run_id=run_id,
            mode="dry_run",
            implementation_brief_hash=brief_hash,
            build_spec_hash=implementation_brief.build_spec_hash,
            planned_actions=actions,
            artifact_manifest=_expected_artifacts(run_id, implementation_brief.build_spec),
            required_approvals=[
                {
                    "approval_type": "live_runner",
                    "reason": "Live DAACS execution still requires ApprovalRecord after dry-run review.",
                    "status": "required_before_live",
                }
            ],
            side_effects=ZERO_DRY_RUN_SIDE_EFFECTS,
        )
        plan_payload = plan.to_dict()
        simulated_action_count = len(actions)
        report = VerificationReport(
            run_id=run_id,
            passed=True,
            checks=[
                {"name": "dry_run_runner_admission", "passed": True},
                {"name": "implementation_brief_present", "passed": True},
                {"name": "spec_approval_matches_brief", "passed": True},
                {"name": "offline_state_contract_passed", "passed": True},
                {"name": "dry_run_side_effects_zero", "passed": True},
                {"name": "runner_plan_created", "passed": True},
            ],
            errors=[],
            generated_files=[],
            metrics={
                **ZERO_DRY_RUN_SIDE_EFFECTS,
                "boundary_mode": "dry_run",
                "approval_bypass_count": 0,
                "executed_action_count": 0,
                "simulated_action_count": simulated_action_count,
                "planned_backend_actions": sum(1 for item in actions if item.get("role") == "backend"),
                "planned_frontend_actions": sum(1 for item in actions if item.get("role") == "frontend"),
                "planned_verification_actions": sum(1 for item in actions if item.get("role") == "verifier"),
                "artifact_manifest_count": len(plan_payload["artifact_manifest"]),
                "required_live_approval_count": len(plan.required_approvals),
                "next_action_placeholder_count": len(plan.required_approvals),
                "next_action_required_before_live_count": sum(
                    1
                    for item in plan.required_approvals
                    if item.get("status") == "required_before_live"
                ),
                "plan_sanitization_failure_count": 0,
                "generated_payload_in_dry_run_count": 0,
                "raw_secret_log_count": 0,
            },
        )
        return plan, report


class DryRunRunnerProvider:
    """Provider wrapper for DAACSDryRunRunner."""

    mode = "dry_run"

    def __init__(self, runner: DAACSDryRunRunner | None = None) -> None:
        self.runner = runner or DAACSDryRunRunner()

    def run(self, request: RunnerRequest) -> RunnerResult:
        plan, report = self.runner.run(
            run_id=request.run_id,
            state=request.state,
            implementation_brief=request.implementation_brief,
            approval=request.spec_approval,
        )
        status = "approval_required" if report.passed else "blocked"
        plan_payload = plan.to_dict() if plan is not None else None
        return RunnerResult(
            run_id=request.run_id,
            mode="dry_run",
            status=status,
            verification_report=report,
            plan=plan,
            artifact_manifest=plan_payload["artifact_manifest"] if plan_payload else [],
            audit_events=[
                {
                    "event": "dry_run_planned" if report.passed else "dry_run_blocked",
                    "run_id": request.run_id,
                    "side_effects": ZERO_DRY_RUN_SIDE_EFFECTS,
                }
            ],
        )

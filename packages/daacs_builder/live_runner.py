"""Gated fake live runner boundary.

This module intentionally connects only a fake runtime. It does not import
DAACS runtime modules, LLM providers, subprocess helpers, package installers,
servers, or filesystem writers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from packages.core.pathing import PathBoundaryError, normalize_public_relative_path
from packages.core.repositories import canonical_replay_scope
from packages.core.schemas import VerificationReport, stable_contract_hash

from .approval_security import (
    ApprovalPolicyResolver,
    ApprovalVerifier,
    ApprovalVerifierPolicy,
    KeyIdentityRegistry,
    PersistentReplayStore,
    claim_approval_replay,
    default_approval_replay_guard,
    enforce_resolved_approval_contract_policy,
    merge_verifier_metrics,
)
from .offline_runner import DAACSOfflineRunner
from .runner_provider import (
    ApprovalRecord,
    RunnerRequest,
    RunnerResult,
    is_safe_run_id,
    safe_public_run_id,
)


FAKE_LIVE_OPERATION = "fake_runtime"
LIVE_APPROVAL_SCOPE = "live_runner"

LIVE_LIMIT_FIELDS = (
    "max_provider_calls",
    "max_subprocess_calls",
    "max_package_installs",
    "max_server_starts",
    "max_files_written",
)

LIVE_POLICY_FLAGS = (
    "allow_provider_calls",
    "allow_cli_agent",
    "allow_subprocess",
    "allow_package_install",
    "allow_server_start",
    "allow_filesystem_write",
    "allow_network",
)

ZERO_FAKE_LIVE_SIDE_EFFECTS: dict[str, int] = {
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

ZERO_FAKE_LIVE_RUNTIME_METRICS: dict[str, int] = {
    "fake_live_runtime_invocations": 0,
    "real_daacs_invocations": 0,
    "solar_provider_calls": 0,
    "executed_action_count": 0,
    "approval_signature_valid_count": 0,
    "approval_replay_mark_count": 0,
    "approval_replay_block_count": 0,
    "approval_replay_store_claim_count": 0,
    "approval_replay_store_hit_count": 0,
    "approval_replay_store_persisted_record_count": 0,
    "approval_verifier_missing_block_count": 0,
    "approval_verifier_fake_count": 0,
    "approval_verifier_secret_value_reads": 0,
    "approval_verifier_key_file_reads": 0,
    "approval_verifier_network_calls": 0,
    "approval_verifier_policy_check_count": 0,
    "approval_verifier_policy_valid_count": 0,
    "approval_verifier_policy_block_count": 0,
    "approval_verifier_identity_block_count": 0,
    "approval_verifier_key_block_count": 0,
    "approval_verifier_scope_block_count": 0,
    "approval_verifier_skew_block_count": 0,
    "approval_policy_resolver_check_count": 0,
    "approval_policy_resolver_valid_count": 0,
    "approval_policy_resolver_block_count": 0,
    "approval_policy_resolver_missing_block_count": 0,
    "approval_policy_unknown_block_count": 0,
    "key_identity_registry_check_count": 0,
    "key_identity_registry_valid_count": 0,
    "key_identity_registry_block_count": 0,
    "key_identity_registry_missing_block_count": 0,
    "key_identity_revoked_block_count": 0,
    "policy_key_mismatch_block_count": 0,
}


def _metrics(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        **ZERO_FAKE_LIVE_SIDE_EFFECTS,
        **ZERO_FAKE_LIVE_RUNTIME_METRICS,
        "boundary_mode": "live",
        **(extra or {}),
    }


def _parse_aware_timestamp(
    value: str,
    *,
    field_name: str,
    failures: list[tuple[str, str]],
) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        failures.append(("live_approval_valid", f"{field_name} is required."))
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        failures.append(("live_approval_valid", f"{field_name} must be ISO-8601."))
        return None
    if parsed.tzinfo is None:
        failures.append(("live_approval_valid", f"{field_name} must include timezone."))
        return None
    return parsed.astimezone(timezone.utc)


def _validate_workspace(
    approval: ApprovalRecord,
    request: RunnerRequest,
    failures: list[tuple[str, str]],
) -> None:
    if not is_safe_run_id(request.run_id):
        return
    expected_prefix = f"runs/{request.run_id}"
    try:
        approval_workspace = normalize_public_relative_path(approval.workspace_root)
    except (PathBoundaryError, ValueError):
        failures.append(("live_workspace_valid", "approval workspace_root must be a safe relative path."))
        return

    if approval_workspace != expected_prefix and not approval_workspace.startswith(
        f"{expected_prefix}/"
    ):
        failures.append(("live_workspace_valid", "approval workspace_root must stay inside the run workspace."))

    if not isinstance(request.policy.workspace_root, str) or not request.policy.workspace_root.strip():
        failures.append(("live_workspace_valid", "runner policy workspace_root is required for live mode."))
        return
    try:
        policy_workspace = normalize_public_relative_path(request.policy.workspace_root)
    except (PathBoundaryError, ValueError):
        failures.append(("live_workspace_valid", "runner policy workspace_root must be a safe relative path."))
        return

    if policy_workspace != approval_workspace:
        failures.append(("live_workspace_valid", "approval and policy workspace roots must match."))


def _validate_approval(
    request: RunnerRequest,
    failures: list[tuple[str, str]],
) -> None:
    approval = request.approval
    if not isinstance(approval, ApprovalRecord):
        failures.append(("live_approval_valid", "live runner requires ApprovalRecord approval."))
        return

    if not isinstance(approval.approved_by, str) or not approval.approved_by.strip():
        failures.append(("live_approval_valid", "approved_by is required."))
    if approval.run_id != request.run_id:
        failures.append(("live_approval_valid", "approval run_id must match the request run_id."))
    if approval.mode != "live":
        failures.append(("live_approval_valid", "approval mode must be live."))

    allowed_operations_valid = (
        isinstance(approval.allowed_operations, list)
        and all(isinstance(item, str) for item in approval.allowed_operations)
        and set(approval.allowed_operations) == {FAKE_LIVE_OPERATION}
    )
    if not allowed_operations_valid:
        failures.append(("live_approval_valid", "allowed_operations must allow only fake_runtime."))

    for field_name in LIVE_LIMIT_FIELDS:
        value = getattr(approval, field_name)
        if type(value) is not int or value != 0:
            failures.append(("live_approval_valid", f"{field_name} must be explicit zero."))

    approved_at = _parse_aware_timestamp(
        approval.approved_at,
        field_name="approved_at",
        failures=failures,
    )
    expires_at = _parse_aware_timestamp(
        approval.expires_at,
        field_name="expires_at",
        failures=failures,
    )
    if approved_at is not None and expires_at is not None:
        if expires_at <= approved_at:
            failures.append(("live_approval_valid", "expires_at must be after approved_at."))
        if expires_at <= datetime.now(timezone.utc):
            failures.append(("live_approval_valid", "approval is expired."))

    if not isinstance(approval.rollback_plan_id, str) or not approval.rollback_plan_id.strip():
        failures.append(("live_rollback_configured", "rollback_plan_id is required."))
    if not isinstance(approval.audit_log_id, str) or not approval.audit_log_id.strip():
        failures.append(("live_audit_configured", "audit_log_id is required."))

    _validate_workspace(approval, request, failures)


def _validate_policy(request: RunnerRequest, failures: list[tuple[str, str]]) -> None:
    for flag in LIVE_POLICY_FLAGS:
        if bool(getattr(request.policy, flag)):
            failures.append(("live_policy_fake_only", f"{flag} must stay disabled for fake live mode."))


def _validate_dry_run_plan(request: RunnerRequest, failures: list[tuple[str, str]]) -> None:
    plan = request.plan
    if plan is None:
        failures.append(("dry_run_plan_present", "dry-run RunnerPlan is required before fake live mode."))
        return

    try:
        plan.validate()
    except ValueError as exc:
        failures.append(("dry_run_plan_valid", str(exc)))
        return

    if plan.run_id != request.run_id:
        failures.append(("dry_run_plan_valid", "RunnerPlan run_id must match the request run_id."))
    if not any(item.get("approval_type") == "live_runner" for item in plan.required_approvals):
        failures.append(("dry_run_plan_valid", "RunnerPlan must request live_runner approval."))
    if request.state.get("spec_approval_status") != "approved":
        failures.append(("dry_run_plan_valid", "approved BuildSpec state is required before live mode."))
    if request.state.get("implementation_brief_hash") != plan.implementation_brief_hash:
        failures.append(("dry_run_plan_valid", "RunnerPlan implementation brief hash must match state."))
    if request.state.get("approved_build_spec_hash") != plan.build_spec_hash:
        failures.append(("dry_run_plan_valid", "RunnerPlan BuildSpec hash must match approved state."))


def validate_fake_live_request(request: RunnerRequest) -> list[tuple[str, str]]:
    """Return sanitized gate failures for fake live admission."""
    failures: list[tuple[str, str]] = []
    if not is_safe_run_id(request.run_id):
        failures.append(("live_run_id_valid", "run_id contains unsupported characters."))
    _validate_approval(request, failures)
    _validate_policy(request, failures)
    _validate_dry_run_plan(request, failures)
    return failures


def live_hashes_for_request(request: RunnerRequest) -> tuple[str, str]:
    """Return state and plan hashes for a validated fake-live request."""
    plan_payload = request.plan.to_dict() if request.plan is not None else {}
    state_hash = stable_contract_hash(
        {
            "run_id": request.run_id,
            "state": request.state,
        }
    )
    plan_hash = str(plan_payload["plan_hash"])
    return state_hash, plan_hash


def live_subject_hash_for_request(request: RunnerRequest) -> str:
    """Hash the live approval subject without authorization material."""
    state_hash, plan_hash = live_hashes_for_request(request)
    return stable_contract_hash(
        {
            "run_id": request.run_id,
            "plan_hash": plan_hash,
            "state_hash": state_hash,
            "workspace_root": request.approval.workspace_root,
            "allowed_operations": request.approval.allowed_operations,
            "side_effect_limits": {
                field_name: getattr(request.approval, field_name)
                for field_name in LIVE_LIMIT_FIELDS
            },
        }
    )


def live_replay_scope_for_request(request: RunnerRequest) -> str:
    """Return the canonical live replay scope for signature and nonce gates."""
    return canonical_replay_scope(
        approval_type="live_runner_approval",
        run_id=request.run_id,
        subject_hash=live_subject_hash_for_request(request),
    )


def live_approval_decision_hash(request: RunnerRequest, *, scope_canonical: str) -> str:
    """Hash the live approval decision without nonce/signature/key material."""
    return stable_contract_hash(
        {
            "approval_type": "live_runner_approval",
            "run_id": request.run_id,
            "subject_hash": live_subject_hash_for_request(request),
            "scope_canonical": scope_canonical,
            "decision": "approved",
            "approved_at": request.approval.approved_at,
            "expires_at": request.approval.expires_at,
            "rollback_plan_id": request.approval.rollback_plan_id,
            "audit_log_id": request.approval.audit_log_id,
        }
    )


def _blocked_result(
    *,
    request: RunnerRequest,
    failures: list[tuple[str, str]],
    extra_metrics: dict[str, Any] | None = None,
) -> RunnerResult:
    check_name = failures[0][0] if failures else "fake_live_runner_blocked"
    errors = [message for _, message in failures] or ["fake live runner blocked."]
    report_run_id = safe_public_run_id(request.run_id)
    report = VerificationReport(
        run_id=report_run_id,
        passed=False,
        checks=[{"name": check_name, "passed": False}],
        errors=errors,
        generated_files=[],
        metrics=_metrics(
            {
                "runner_admission_block_count": 1,
                "approval_validation_failure_count": 1,
                **(extra_metrics or {}),
            }
        ),
    )
    return RunnerResult(
        run_id=report_run_id,
        mode="live",
        status="blocked",
        verification_report=report,
        artifact_manifest=[],
        audit_events=[
            {
                "event": "fake_live_blocked",
                "run_id": report_run_id,
                "failed_gate": check_name,
                "side_effects": ZERO_FAKE_LIVE_SIDE_EFFECTS,
            }
        ],
    )


class FakeLiveRuntime:
    """Runtime stub that records admission evidence without external effects."""

    name = "fake_live_runtime"

    def run(
        self,
        *,
        request: RunnerRequest,
        approval_hash: str,
        state_hash: str,
        plan_hash: str,
    ) -> dict[str, Any]:
        return {
            "runtime": self.name,
            "run_id": request.run_id,
            "approval_hash": approval_hash,
            "state_hash": state_hash,
            "plan_hash": plan_hash,
            "real_daacs_invocations": 0,
            "solar_provider_calls": 0,
            "executed_action_count": 0,
            "generated_file_count": 0,
        }


class LiveRunnerProvider:
    """Live provider skeleton that admits only a fake runtime."""

    mode = "live"

    def __init__(
        self,
        *,
        runtime: FakeLiveRuntime | None = None,
        offline_runner: DAACSOfflineRunner | None = None,
        approval_verifier: ApprovalVerifier | None = None,
        approval_verifier_policy: ApprovalVerifierPolicy | None = None,
        approval_policy_resolver: ApprovalPolicyResolver | None = None,
        key_identity_registry: KeyIdentityRegistry | None = None,
        replay_store: PersistentReplayStore | None = None,
        replay_guard: PersistentReplayStore | None = None,
    ) -> None:
        self.runtime = runtime or FakeLiveRuntime()
        self.offline_runner = offline_runner or DAACSOfflineRunner()
        self.approval_verifier = approval_verifier
        self.approval_verifier_policy = approval_verifier_policy
        if approval_policy_resolver is not None:
            self.approval_policy_resolver = approval_policy_resolver
        elif approval_verifier_policy is not None:
            self.approval_policy_resolver = ApprovalPolicyResolver([approval_verifier_policy])
        else:
            self.approval_policy_resolver = None
        self.key_identity_registry = key_identity_registry
        self.replay_store = replay_store or replay_guard or default_approval_replay_guard()

    def run(self, request: RunnerRequest) -> RunnerResult:
        failures = validate_fake_live_request(request)
        if failures:
            return _blocked_result(
                request=request,
                failures=failures,
                extra_metrics={"approval_bypass_count": 1},
            )

        if self.approval_verifier is None:
            return _blocked_result(
                request=request,
                failures=[("live_approval_verifier_present", "approval verifier is required.")],
                extra_metrics={
                    "approval_bypass_count": 1,
                    "approval_verifier_missing_block_count": 1,
                },
            )

        replay_scope = live_replay_scope_for_request(request)
        approval_hash = live_approval_decision_hash(
            request,
            scope_canonical=replay_scope,
        )

        try:
            verification = self.approval_verifier.verify(
                request.approval,
                scope=replay_scope,
                gate_prefix="live_approval",
            )
        except Exception:
            return _blocked_result(
                request=request,
                failures=[("live_approval_verifier_available", "approval verifier is unavailable.")],
                extra_metrics={
                    "approval_bypass_count": 1,
                    "approval_verifier_missing_block_count": 1,
                },
            )
        if verification.failures:
            return _blocked_result(
                request=request,
                failures=verification.failures,
                extra_metrics={
                    "approval_bypass_count": 1,
                    **verification.metrics,
                },
            )

        if self.approval_policy_resolver is None:
            return _blocked_result(
                request=request,
                failures=[("live_approval_policy_resolver_present", "approval policy resolver is required.")],
                extra_metrics={
                    "approval_bypass_count": 1,
                    **verification.metrics,
                    "approval_policy_resolver_missing_block_count": 1,
                },
            )

        if self.key_identity_registry is None:
            return _blocked_result(
                request=request,
                failures=[("live_approval_key_identity_registry_present", "key identity registry is required.")],
                extra_metrics={
                    "approval_bypass_count": 1,
                    **verification.metrics,
                    "key_identity_registry_missing_block_count": 1,
                },
            )

        policy_verification = enforce_resolved_approval_contract_policy(
            request.approval,
            scope=replay_scope,
            gate_prefix="live_approval",
            policy_resolver=self.approval_policy_resolver,
            key_identity_registry=self.key_identity_registry,
        )
        verification_metrics = merge_verifier_metrics(
            verification.metrics,
            policy_verification.metrics,
        )
        if policy_verification.failures:
            return _blocked_result(
                request=request,
                failures=policy_verification.failures,
                extra_metrics={
                    "approval_bypass_count": 1,
                    **verification_metrics,
                },
            )

        offline_report = self.offline_runner.run(request.state)
        if not offline_report.passed:
            return _blocked_result(
                request=request,
                failures=[
                    (
                        "offline_state_contract_passed",
                        "approved state must pass offline contract checks before fake live mode.",
                    )
                ],
                extra_metrics={
                    "offline_state_rejection_count": 1,
                    "approval_bypass_count": 0,
                },
            )

        state_hash, plan_hash = live_hashes_for_request(request)
        replay_failures = claim_approval_replay(
            request.approval,
            scope=replay_scope,
            gate_prefix="live_approval",
            replay_store=self.replay_store,
            approval_hash=approval_hash,
            run_id=request.run_id,
            approval_type="live_runner_approval",
            expires_at=request.approval.expires_at,
        )
        if replay_failures:
            return _blocked_result(
                request=request,
                failures=replay_failures,
                extra_metrics={
                    "approval_bypass_count": 1,
                    "approval_replay_block_count": 1,
                    "approval_replay_store_hit_count": 1,
                    **verification_metrics,
                },
            )

        runtime_evidence = self.runtime.run(
            request=request,
            approval_hash=approval_hash,
            state_hash=state_hash,
            plan_hash=plan_hash,
        )
        metrics = _metrics(
            {
                "fake_live_runtime_invocations": 1,
                "dry_run_plan_verified_count": 1,
                "rollback_plan_configured_count": 1,
                "audit_log_configured_count": 1,
                "fake_runtime_evidence_count": 1,
                "approval_signature_valid_count": 1,
                "approval_replay_mark_count": 1,
                "approval_replay_store_claim_count": 1,
                "approval_replay_store_persisted_record_count": len(
                    self.replay_store.export_records()
                ),
                "planned_action_count": len(request.plan.planned_actions)
                if request.plan is not None
                else 0,
                **verification_metrics,
            }
        )
        report = VerificationReport(
            run_id=request.run_id,
            passed=True,
            checks=[
                {"name": "live_approval_valid", "passed": True},
                {"name": "live_approval_signature_valid", "passed": True},
                {"name": "live_approval_replay_fresh", "passed": True},
                {"name": "live_workspace_valid", "passed": True},
                {"name": "live_policy_fake_only", "passed": True},
                {"name": "dry_run_plan_present", "passed": True},
                {"name": "dry_run_plan_valid", "passed": True},
                {"name": "offline_state_contract_passed", "passed": True},
                {"name": "fake_runtime_only", "passed": True},
                {"name": "side_effects_zero", "passed": True},
            ],
            errors=[],
            generated_files=[],
            metrics=metrics,
        )
        return RunnerResult(
            run_id=request.run_id,
            mode="live",
            status="passed",
            verification_report=report,
            plan=request.plan,
            artifact_manifest=[],
            audit_events=[
                {
                    "event": "fake_live_runtime_verified",
                    "run_id": request.run_id,
                    "approval_hash": approval_hash,
                    "state_hash": state_hash,
                    "plan_hash": plan_hash,
                    "runtime": runtime_evidence["runtime"],
                    "side_effects": ZERO_FAKE_LIVE_SIDE_EFFECTS,
                }
            ],
        )

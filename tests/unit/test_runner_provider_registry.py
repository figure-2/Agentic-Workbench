import builtins
from itertools import count
import os
import subprocess
import sys
import socket
import urllib.request
from pathlib import Path

import pytest

from packages.daacs_builder.adapters import (
    build_spec_to_daacs_initial_state,
    create_spec_approval,
    implementation_brief_from_prd_package,
    planning_to_build_spec,
)
from packages.daacs_builder.approval_security import (
    ApprovalPolicyResolver,
    DurableReplayStore,
    ApprovalVerificationResult,
    ApprovalVerifierPolicy,
    FakeApprovalVerifier,
    InMemoryReplayRecordAdapter,
    KeyIdentityRecord,
    KeyIdentityRegistry,
    PersistentReplayStore,
    UnavailableReplayRecordAdapter,
    sign_approval_for_tests,
)
from packages.daacs_builder.live_runner import LIVE_APPROVAL_SCOPE, LiveRunnerProvider
from packages.daacs_builder.runner_provider import (
    ApprovalRecord,
    RunnerPolicy,
    RunnerRequest,
    default_runner_provider_registry,
)
from packages.div_planner.adapters import planning_blueprint_from_div_state, planning_to_prd_package


_live_approval_counter = count(1)


class RaisingApprovalVerifier:
    def verify(self, approval, *, scope, gate_prefix):
        raise RuntimeError("sig-live-leaked nonce-live-leaked signed_contract_hash C:\\secret\\.env")


class PermissiveApprovalVerifier:
    def verify(self, approval, *, scope, gate_prefix):
        return ApprovalVerificationResult(failures=[], metrics={})


class RaisingReplayStore(PersistentReplayStore):
    def claim(self, *, scope: str, nonce: str) -> bool:
        raise RuntimeError("nonce-live-leaked signed_contract_hash postgres://secret")


def _state():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {
                "toc": ["Agentic Workbench"],
                "rationale": "Need a provider registry boundary.",
                "blueprint": [
                    {"title": "Runner Registry", "guideline": "route runner modes"},
                    {"title": "Approval Gate", "guideline": "block live execution"},
                ],
            }
        }
    )
    spec = planning_to_build_spec(blueprint)
    return build_spec_to_daacs_initial_state(spec, run_id="run-provider")


def _approved_dry_run_parts():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {
                "toc": ["Agentic Workbench"],
                "rationale": "Need a dry-run runner plan.",
                "blueprint": [
                    {"title": "Runner Plan", "guideline": "plan DAACS actions"},
                    {"title": "Approval Gate", "guideline": "require content approval"},
                ],
            }
        }
    )
    spec = planning_to_build_spec(blueprint)
    prd_package = planning_to_prd_package(blueprint, build_spec=spec)
    brief = implementation_brief_from_prd_package(prd_package, spec)
    approval = create_spec_approval(brief, approval_id="approval-run-provider", approved=True)
    state = build_spec_to_daacs_initial_state(
        spec,
        run_id="run-provider",
        implementation_brief=brief,
        approval=approval,
        require_approval=True,
    )
    return state, brief, approval


def _approved_dry_run_result():
    state, brief, approval = _approved_dry_run_parts()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )
    assert result.plan is not None
    return state, result.plan


def _valid_live_approval(**overrides):
    approval_index = next(_live_approval_counter)
    signed = overrides.pop("signed", True)
    signature_id = overrides.pop("signature_id", f"sig-live-run-provider-{approval_index:04d}")
    nonce = overrides.pop("nonce", f"nonce-live-run-provider-{approval_index:04d}")
    fields = {
        "approved_by": "local-user",
        "approved_at": "2026-05-27T00:00:00Z",
        "run_id": "run-provider",
        "mode": "live",
        "allowed_operations": ["fake_runtime"],
        "max_provider_calls": 0,
        "max_subprocess_calls": 0,
        "max_package_installs": 0,
        "max_server_starts": 0,
        "max_files_written": 0,
        "workspace_root": "runs/run-provider",
        "expires_at": "2099-01-01T00:00:00Z",
        "rollback_plan_id": "rollback-run-provider",
        "audit_log_id": "audit-run-provider",
    }
    fields.update(overrides)
    approval = ApprovalRecord(**fields)
    if signed:
        sign_approval_for_tests(
            approval,
            scope=LIVE_APPROVAL_SCOPE,
            signature_id=signature_id,
            nonce=nonce,
        )
    return approval


def _valid_live_policy(**overrides):
    fields = {"workspace_root": "runs/run-provider"}
    fields.update(overrides)
    return RunnerPolicy(**fields)


def _live_provider(**overrides):
    fields = {
        "approval_verifier": FakeApprovalVerifier(),
        "approval_verifier_policy": ApprovalVerifierPolicy(),
        "key_identity_registry": KeyIdentityRegistry(),
        "replay_store": PersistentReplayStore(),
    }
    fields.update(overrides)
    return LiveRunnerProvider(**fields)


def test_default_registry_routes_offline_provider_without_live_execution():
    result = default_runner_provider_registry().run(
        RunnerRequest(run_id="run-provider", mode="offline", state=_state())
    )

    assert result.status == "passed"
    assert result.mode == "offline"
    assert result.verification_report.passed is True
    assert result.verification_report.metrics["boundary_mode"] == "offline"
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["subprocess_calls"] == 0
    assert result.verification_report.metrics["filesystem_writes"] == 0
    assert result.artifact_manifest == []


def test_default_registry_registers_offline_dry_run_and_fake_live():
    assert default_runner_provider_registry().registered_modes() == ["dry_run", "live", "offline"]


def test_default_registry_routes_dry_run_provider_without_side_effects():
    state, brief, approval = _approved_dry_run_parts()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
            policy=RunnerPolicy(
                allow_provider_calls=True,
                allow_subprocess=True,
                allow_package_install=True,
                allow_server_start=True,
                allow_filesystem_write=True,
                allow_network=True,
            ),
        )
    )
    plan_payload = result.plan.to_dict()

    assert result.status == "approval_required"
    assert result.mode == "dry_run"
    assert result.verification_report.passed is True
    assert result.verification_report.generated_files == []
    assert result.verification_report.metrics["boundary_mode"] == "dry_run"
    assert result.verification_report.metrics["executed_action_count"] == 0
    assert result.verification_report.metrics["simulated_action_count"] > 0
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["subprocess_calls"] == 0
    assert result.verification_report.metrics["package_install_calls"] == 0
    assert result.verification_report.metrics["server_start_calls"] == 0
    assert result.verification_report.metrics["filesystem_writes"] == 0
    assert result.plan is not None
    assert plan_payload["mode"] == "dry_run"
    assert plan_payload["implementation_brief_hash"] == brief.to_dict()["brief_hash"]
    assert plan_payload["build_spec_hash"] == brief.build_spec_hash
    assert plan_payload["side_effects"]["provider_calls"] == 0
    assert "backend_files" not in str(plan_payload)
    assert "frontend_files" not in str(plan_payload)


def test_dry_run_blocks_without_spec_approval():
    state, brief, _approval = _approved_dry_run_parts()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
        )
    )

    assert result.status == "blocked"
    assert result.plan is None
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["subprocess_calls"] == 0
    assert result.verification_report.metrics["filesystem_writes"] == 0
    assert result.verification_report.metrics["spec_approval_missing_block_count"] == 1


def test_dry_run_blocks_mismatched_spec_approval():
    state, brief, approval = _approved_dry_run_parts()
    approval.approved_build_spec_hash = "not-current"
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "blocked"
    assert result.plan is None
    assert result.verification_report.metrics["spec_approval_mismatch_block_count"] == 1
    assert result.verification_report.metrics["provider_calls"] == 0


def test_dry_run_blocks_mutated_implementation_brief_after_approval():
    state, brief, approval = _approved_dry_run_parts()
    brief.daacs_tasks.append(
        {
            "id": "mutated-live-task",
            "role": "backend",
            "summary": "backend_llm.invoke(prompt)",
        }
    )

    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "blocked"
    assert result.plan is None
    assert result.verification_report.metrics["spec_approval_mismatch_block_count"] == 1
    assert result.verification_report.metrics["provider_calls"] == 0


def test_dry_run_rejects_unsafe_state_before_planning():
    state, brief, approval = _approved_dry_run_parts()
    state["backend_files"] = {"main.py": "print('should not exist in dry-run')"}

    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "blocked"
    assert result.plan is None
    assert result.verification_report.metrics["dry_run_state_rejection_count"] == 1
    assert result.verification_report.metrics["filesystem_writes"] == 0


def test_dry_run_does_not_call_process_network_or_file_write(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("dry-run attempted a blocked side effect")

    monkeypatch.setattr(subprocess, "run", fail_if_called)
    monkeypatch.setattr(subprocess, "Popen", fail_if_called)
    monkeypatch.setattr(os, "system", fail_if_called)
    monkeypatch.setattr(builtins, "open", fail_if_called)
    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "mkdir", fail_if_called)
    monkeypatch.setattr(socket, "create_connection", fail_if_called)
    monkeypatch.setattr(urllib.request, "urlopen", fail_if_called)

    state, brief, approval = _approved_dry_run_parts()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "approval_required"
    assert result.verification_report.metrics["executed_action_count"] == 0
    assert result.verification_report.metrics["network_calls"] == 0


def test_dry_run_does_not_import_provider_or_daacs_runtime_even_with_tripwire(monkeypatch):
    real_import = builtins.__import__

    def fail_blocked_import(name, *args, **kwargs):
        blocked_prefixes = (
            "daacs",
            "langchain_upstage",
            "langchain_tavily",
            "qdrant_client",
            "openai",
            "anthropic",
        )
        if name.startswith(blocked_prefixes):
            raise AssertionError(f"dry-run attempted blocked import: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_blocked_import)
    state, brief, approval = _approved_dry_run_parts()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "approval_required"
    assert result.verification_report.metrics["provider_imports"] == 0


def test_dry_run_plan_redacts_public_payloads():
    state, brief, approval = _approved_dry_run_parts()
    brief.constraints.append("Authorization: Bearer live-secret-token")
    approval = create_spec_approval(brief, approval_id="approval-redacted", approved=True)

    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )
    serialized = str(
        {
            "plan": result.plan.to_dict(),
            "audit_events": result.audit_events,
            "report": result.verification_report.to_dict(),
        }
    )

    assert result.status == "approval_required"
    assert "live-secret-token" not in serialized
    assert "Authorization" not in serialized
    assert "raw_content" not in serialized


def test_dry_run_does_not_import_daacs_or_provider_runtime_modules():
    blocked_modules = {
        "daacs.llm.cli_executor",
        "daacs.graph.backend_subgraph",
        "daacs.graph.frontend_subgraph",
        "langchain_upstage",
        "langchain_tavily",
        "qdrant_client",
    }

    state, brief, approval = _approved_dry_run_parts()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="dry_run",
            state=state,
            implementation_brief=brief,
            spec_approval=approval,
        )
    )

    assert result.status == "approval_required"
    assert not (blocked_modules & set(sys.modules))


def test_registry_rejects_unknown_mode_as_blocked_result():
    result = default_runner_provider_registry().run(
        RunnerRequest(run_id="run-provider", mode="experimental", state=_state())
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert result.mode == "experimental"
    assert result.verification_report.passed is False
    assert checks["runner_mode_known"] is False
    assert "unknown runner mode" in result.verification_report.errors[0]
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["approval_bypass_count"] == 0


def test_registry_blocks_live_mode_without_approval():
    result = default_runner_provider_registry().run(
        RunnerRequest(run_id="run-provider", mode="live", state=_state())
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert result.verification_report.passed is False
    assert checks["live_approval_present"] is False
    assert result.verification_report.metrics["approval_bypass_count"] == 1
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["cli_agent_invocations"] == 0


def test_registry_blocks_live_mode_with_malformed_approval():
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=_state(),
            approval="approved in chat",
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_approval_valid"] is False
    assert result.verification_report.metrics["approval_bypass_count"] == 1
    assert result.verification_report.metrics["provider_calls"] == 0


def test_live_blocks_unsafe_run_id_without_public_exposure():
    unsafe_run_id = "john@example.com/demo"
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id=unsafe_run_id,
            mode="live",
            state=_state(),
            approval=_valid_live_approval(run_id=unsafe_run_id),
            policy=_valid_live_policy(),
        )
    )
    serialized = str(
        {
            "result_run_id": result.run_id,
            "report": result.verification_report.to_dict(),
            "audit_events": result.audit_events,
        }
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert result.run_id == "invalid-run-id"
    assert result.verification_report.run_id == "invalid-run-id"
    assert checks["live_run_id_valid"] is False
    assert unsafe_run_id not in serialized
    assert "john@example.com" not in serialized
    assert result.verification_report.metrics["provider_calls"] == 0


def test_live_blocks_without_dry_run_plan_even_with_valid_approval():
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=_state(),
            approval=_valid_live_approval(),
            policy=_valid_live_policy(),
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["dry_run_plan_present"] is False
    assert result.verification_report.metrics["approval_bypass_count"] == 1
    assert result.verification_report.metrics["provider_calls"] == 0


def test_live_blocks_without_approval_verifier():
    state, plan = _approved_dry_run_result()
    result = LiveRunnerProvider(replay_store=PersistentReplayStore()).run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_approval_verifier_present"] is False
    assert result.verification_report.metrics["approval_verifier_missing_block_count"] == 1
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert result.verification_report.metrics["provider_calls"] == 0


def test_live_blocks_verifier_exception_without_public_exposure():
    state, plan = _approved_dry_run_result()
    result = _live_provider(approval_verifier=RaisingApprovalVerifier()).run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    serialized = str(
        {
            "report": result.verification_report.to_dict(),
            "audit_events": result.audit_events,
        }
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_approval_verifier_available"] is False
    assert result.verification_report.metrics["approval_verifier_missing_block_count"] == 1
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert "sig-live-leaked" not in serialized
    assert "nonce" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "C:\\\\" not in serialized


@pytest.mark.parametrize(
    ("approval_overrides", "verifier_policy", "expected_gate", "expected_metric"),
    [
        (
            {"verifier_id": "verifier-unknown-local"},
            ApprovalVerifierPolicy(),
            "live_approval_verifier_trusted",
            "approval_verifier_identity_block_count",
        ),
        (
            {},
            ApprovalVerifierPolicy(revoked_verifier_ids=("verifier-local-fake",)),
            "live_approval_verifier_trusted",
            "approval_verifier_identity_block_count",
        ),
        (
            {"key_id": "key-unknown-local"},
            ApprovalVerifierPolicy(),
            "live_approval_key_trusted",
            "approval_verifier_key_block_count",
        ),
        (
            {},
            ApprovalVerifierPolicy(revoked_key_ids=("key-local-fake",)),
            "live_approval_key_trusted",
            "approval_verifier_key_block_count",
        ),
        (
            {"key_id": "-----BEGIN PRIVATE KEY-----"},
            ApprovalVerifierPolicy(),
            "live_approval_key_trusted",
            "approval_verifier_key_block_count",
        ),
        (
            {"verifier_scope": "provider_boundary"},
            ApprovalVerifierPolicy(),
            "live_approval_scope_matches",
            "approval_verifier_scope_block_count",
        ),
        (
            {"approved_at": "2099-01-01T00:00:00Z", "expires_at": "2099-01-02T00:00:00Z"},
            ApprovalVerifierPolicy(),
            "live_approval_approved_at_skew_valid",
            "approval_verifier_skew_block_count",
        ),
    ],
)
def test_live_blocks_untrusted_verifier_policy(
    approval_overrides,
    verifier_policy,
    expected_gate,
    expected_metric,
):
    state, plan = _approved_dry_run_result()
    approval = _valid_live_approval(**approval_overrides)
    result = _live_provider(approval_verifier=FakeApprovalVerifier(verifier_policy)).run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=approval,
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    serialized = str(
        {
            "report": result.verification_report.to_dict(),
            "audit_events": result.audit_events,
        }
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks[expected_gate] is False
    assert result.verification_report.metrics[expected_metric] == 1
    assert result.verification_report.metrics["approval_verifier_policy_block_count"] == 1
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["solar_provider_calls"] == 0
    assert result.verification_report.metrics["real_daacs_invocations"] == 0
    assert result.verification_report.metrics["network_calls"] == 0
    assert str(approval.verifier_id) not in serialized
    assert str(approval.key_id) not in serialized
    assert approval.signature_id not in serialized
    assert approval.nonce not in serialized
    assert approval.signed_contract_hash not in serialized


@pytest.mark.parametrize(
    ("approval_overrides", "verifier_policy", "expected_gate", "expected_metric"),
    [
        (
            {"verifier_id": "verifier-unknown-local"},
            ApprovalVerifierPolicy(),
            "live_approval_verifier_trusted",
            "approval_verifier_identity_block_count",
        ),
        (
            {},
            ApprovalVerifierPolicy(revoked_verifier_ids=("verifier-local-fake",)),
            "live_approval_verifier_trusted",
            "approval_verifier_identity_block_count",
        ),
        (
            {"key_id": "key-unknown-local"},
            ApprovalVerifierPolicy(),
            "live_approval_key_trusted",
            "approval_verifier_key_block_count",
        ),
        (
            {},
            ApprovalVerifierPolicy(revoked_key_ids=("key-local-fake",)),
            "live_approval_key_trusted",
            "approval_verifier_key_block_count",
        ),
        (
            {"verifier_scope": "provider_boundary"},
            ApprovalVerifierPolicy(),
            "live_approval_scope_matches",
            "approval_verifier_scope_block_count",
        ),
        (
            {"approved_at": "2099-01-01T00:00:00Z", "expires_at": "2099-01-02T00:00:00Z"},
            ApprovalVerifierPolicy(),
            "live_approval_approved_at_skew_valid",
            "approval_verifier_skew_block_count",
        ),
    ],
)
def test_live_enforces_policy_contract_after_custom_verifier(
    approval_overrides,
    verifier_policy,
    expected_gate,
    expected_metric,
):
    state, plan = _approved_dry_run_result()
    approval = _valid_live_approval(**approval_overrides)
    result = _live_provider(
        approval_verifier=PermissiveApprovalVerifier(),
        approval_verifier_policy=verifier_policy,
        key_identity_registry=KeyIdentityRegistry(
            [KeyIdentityRecord(verifier_id=approval.verifier_id, key_id=approval.key_id)]
        ),
    ).run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=approval,
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks[expected_gate] is False
    assert result.verification_report.metrics[expected_metric] == 1
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["solar_provider_calls"] == 0
    assert result.verification_report.metrics["real_daacs_invocations"] == 0
    assert result.verification_report.metrics["network_calls"] == 0


@pytest.mark.parametrize(
    ("provider_overrides", "expected_gate", "expected_metric"),
    [
        (
            {"approval_verifier_policy": None, "approval_policy_resolver": None},
            "live_approval_policy_resolver_present",
            "approval_policy_resolver_missing_block_count",
        ),
        (
            {"key_identity_registry": None},
            "live_approval_key_identity_registry_present",
            "key_identity_registry_missing_block_count",
        ),
    ],
)
def test_live_blocks_missing_resolver_or_registry(
    provider_overrides,
    expected_gate,
    expected_metric,
):
    state, plan = _approved_dry_run_result()
    result = _live_provider(**provider_overrides).run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks[expected_gate] is False
    assert result.verification_report.metrics[expected_metric] == 1
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["solar_provider_calls"] == 0
    assert result.verification_report.metrics["real_daacs_invocations"] == 0
    assert result.verification_report.metrics["network_calls"] == 0


@pytest.mark.parametrize(
    ("approval_overrides", "provider_overrides", "expected_gate", "expected_metric"),
    [
        (
            {"verifier_policy_id": "policy-unknown-local"},
            {},
            "live_approval_policy_resolved",
            "approval_policy_unknown_block_count",
        ),
        (
            {},
            {"approval_policy_resolver": ApprovalPolicyResolver([])},
            "live_approval_policy_resolved",
            "approval_policy_unknown_block_count",
        ),
        (
            {},
            {"key_identity_registry": KeyIdentityRegistry([])},
            "live_approval_key_identity_trusted",
            "key_identity_registry_block_count",
        ),
        (
            {"key_identity_id": "key-identity-revoked"},
            {
                "key_identity_registry": KeyIdentityRegistry(
                    [KeyIdentityRecord(identity_id="key-identity-revoked", revoked=True)]
                )
            },
            "live_approval_key_identity_trusted",
            "key_identity_revoked_block_count",
        ),
        (
            {},
            {
                "key_identity_registry": KeyIdentityRegistry(
                    [KeyIdentityRecord(key_id="key-other-local")]
                )
            },
            "live_approval_policy_key_matches",
            "policy_key_mismatch_block_count",
        ),
    ],
)
def test_live_blocks_policy_resolver_and_key_identity_failures(
    approval_overrides,
    provider_overrides,
    expected_gate,
    expected_metric,
):
    state, plan = _approved_dry_run_result()
    approval = _valid_live_approval(**approval_overrides)
    result = _live_provider(**provider_overrides).run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=approval,
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    serialized = str(
        {
            "report": result.verification_report.to_dict(),
            "audit_events": result.audit_events,
        }
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks[expected_gate] is False
    assert result.verification_report.metrics[expected_metric] == 1
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["solar_provider_calls"] == 0
    assert result.verification_report.metrics["real_daacs_invocations"] == 0
    assert result.verification_report.metrics["network_calls"] == 0
    assert approval.signature_id not in serialized
    assert approval.nonce not in serialized
    assert approval.signed_contract_hash not in serialized
    assert approval.verifier_policy_id not in serialized
    assert approval.key_identity_id not in serialized


def test_live_blocks_unsigned_approval():
    state, plan = _approved_dry_run_result()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(signed=False),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    serialized = str(
        {
            "report": result.verification_report.to_dict(),
            "audit_events": result.audit_events,
        }
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_approval_signature_valid"] is False
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["network_calls"] == 0
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "nonce" not in serialized


def test_live_blocks_tampered_signed_approval_payload():
    state, plan = _approved_dry_run_result()
    approval = _valid_live_approval()
    approval.rollback_plan_id = "rollback-run-provider-tampered"

    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=approval,
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_approval_signature_valid"] is False
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert result.verification_report.metrics["real_daacs_invocations"] == 0


def test_live_blocks_provider_scope_signed_approval_reuse():
    state, plan = _approved_dry_run_result()
    approval = _valid_live_approval(signed=False)
    sign_approval_for_tests(
        approval,
        scope="provider_boundary",
        signature_id="sig-live-cross-scope",
        nonce="nonce-live-cross-scope",
    )

    result = _live_provider().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=approval,
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_approval_signature_valid"] is False
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["solar_provider_calls"] == 0
    assert result.verification_report.metrics["real_daacs_invocations"] == 0
    assert result.verification_report.metrics["network_calls"] == 0


def test_live_blocks_reused_nonce_after_first_fake_runtime_pass():
    state, plan = _approved_dry_run_result()
    provider = _live_provider()
    request = RunnerRequest(
        run_id="run-provider",
        mode="live",
        state=state,
        approval=_valid_live_approval(),
        plan=plan,
        policy=_valid_live_policy(),
    )

    first = provider.run(request)
    second = provider.run(request)
    checks = {check["name"]: check["passed"] for check in second.verification_report.checks}

    assert first.status == "passed"
    assert second.status == "blocked"
    assert checks["live_approval_replay_fresh"] is False
    assert second.verification_report.metrics["approval_replay_block_count"] == 1
    assert second.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert second.verification_report.metrics["real_daacs_invocations"] == 0


def test_live_blocks_reused_nonce_across_fresh_default_registries():
    state, plan = _approved_dry_run_result()
    request = RunnerRequest(
        run_id="run-provider",
        mode="live",
        state=state,
        approval=_valid_live_approval(
            signature_id="sig-live-cross-registry",
            nonce="nonce-live-cross-registry",
        ),
        plan=plan,
        policy=_valid_live_policy(),
    )

    first = default_runner_provider_registry().run(request)
    second = default_runner_provider_registry().run(request)
    checks = {check["name"]: check["passed"] for check in second.verification_report.checks}

    assert first.status == "passed"
    assert second.status == "blocked"
    assert checks["live_approval_replay_fresh"] is False
    assert second.verification_report.metrics["approval_replay_block_count"] == 1
    assert second.verification_report.metrics["fake_live_runtime_invocations"] == 0


def test_live_blocks_reused_nonce_after_restart_simulation():
    state, plan = _approved_dry_run_result()
    replay_store = PersistentReplayStore()
    request = RunnerRequest(
        run_id="run-provider",
        mode="live",
        state=state,
        approval=_valid_live_approval(
            signature_id="sig-live-restart-simulation",
            nonce="nonce-live-restart-simulation",
        ),
        plan=plan,
        policy=_valid_live_policy(),
    )

    first = _live_provider(replay_store=replay_store).run(request)
    restarted_store = PersistentReplayStore.from_records(replay_store.export_records())
    second = _live_provider(replay_store=restarted_store).run(request)
    checks = {check["name"]: check["passed"] for check in second.verification_report.checks}

    assert first.status == "passed"
    assert second.status == "blocked"
    assert checks["live_approval_replay_fresh"] is False
    assert second.verification_report.metrics["approval_replay_store_hit_count"] == 1
    assert second.verification_report.metrics["fake_live_runtime_invocations"] == 0


def test_live_blocks_replay_store_exception_without_consuming_runtime():
    state, plan = _approved_dry_run_result()
    result = _live_provider(replay_store=RaisingReplayStore()).run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    serialized = str(
        {
            "report": result.verification_report.to_dict(),
            "audit_events": result.audit_events,
        }
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_approval_replay_store_available"] is False
    assert result.verification_report.metrics["approval_replay_store_hit_count"] == 1
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert result.verification_report.metrics["real_daacs_invocations"] == 0
    assert "nonce" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "postgres://secret" not in serialized


def test_live_blocks_unavailable_durable_replay_adapter():
    state, plan = _approved_dry_run_result()
    result = _live_provider(replay_store=DurableReplayStore(UnavailableReplayRecordAdapter())).run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_approval_replay_store_available"] is False
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["solar_provider_calls"] == 0
    assert result.verification_report.metrics["real_daacs_invocations"] == 0
    assert result.verification_report.metrics["network_calls"] == 0


def test_live_blocks_reused_nonce_after_durable_restart_simulation():
    state, plan = _approved_dry_run_result()
    adapter = InMemoryReplayRecordAdapter()
    request = RunnerRequest(
        run_id="run-provider",
        mode="live",
        state=state,
        approval=_valid_live_approval(
            signature_id="sig-live-durable-restart",
            nonce="nonce-live-durable-restart",
        ),
        plan=plan,
        policy=_valid_live_policy(),
    )

    first = _live_provider(replay_store=DurableReplayStore(adapter)).run(request)
    second = _live_provider(replay_store=DurableReplayStore(adapter)).run(request)
    checks = {check["name"]: check["passed"] for check in second.verification_report.checks}

    assert first.status == "passed"
    assert second.status == "blocked"
    assert checks["live_approval_replay_fresh"] is False
    assert second.verification_report.metrics["approval_replay_store_hit_count"] == 1
    assert second.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert second.verification_report.metrics["real_daacs_invocations"] == 0


@pytest.mark.parametrize(
    "approval_overrides",
    [
        {
            "signed": False,
            "signature_id": "bad",
            "nonce": "nonce-live-malformed-sig",
            "signed_contract_hash": "a" * 64,
        },
        {
            "signed": False,
            "signature_id": "sig-live-malformed-nonce",
            "nonce": "bad",
            "signed_contract_hash": "a" * 64,
        },
        {
            "signed": False,
            "signature_id": "sig-live-malformed-hash",
            "nonce": "nonce-live-malformed-hash",
            "signed_contract_hash": "bad",
        },
    ],
)
def test_live_blocks_malformed_signature_envelope(approval_overrides):
    state, plan = _approved_dry_run_result()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(**approval_overrides),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    serialized = str(
        {
            "report": result.verification_report.to_dict(),
            "audit_events": result.audit_events,
        }
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_approval_signature_valid"] is False
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 0
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "nonce" not in serialized


@pytest.mark.parametrize(
    ("overrides", "expected_gate"),
    [
        ({"run_id": "other-run"}, "live_approval_valid"),
        ({"mode": "dry_run"}, "live_approval_valid"),
        ({"allowed_operations": []}, "live_approval_valid"),
        ({"allowed_operations": ["fake_runtime", "provider_call"]}, "live_approval_valid"),
        ({"max_provider_calls": 1}, "live_approval_valid"),
        ({"max_subprocess_calls": 1}, "live_approval_valid"),
        ({"max_package_installs": 1}, "live_approval_valid"),
        ({"max_server_starts": 1}, "live_approval_valid"),
        ({"max_files_written": 1}, "live_approval_valid"),
        (
            {"approved_at": "2026-05-27T00:00:00Z", "expires_at": "2026-05-27T00:00:00Z"},
            "live_approval_valid",
        ),
        ({"expires_at": "2000-01-01T00:00:00Z", "approved_at": "1999-01-01T00:00:00Z"}, "live_approval_valid"),
        ({"rollback_plan_id": ""}, "live_rollback_configured"),
        ({"audit_log_id": ""}, "live_audit_configured"),
    ],
)
def test_live_blocks_invalid_approval_fields(overrides, expected_gate):
    state, plan = _approved_dry_run_result()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(**overrides),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks[expected_gate] is False
    assert result.verification_report.metrics["provider_calls"] == 0
    assert result.verification_report.metrics["real_daacs_invocations"] == 0


@pytest.mark.parametrize(
    "workspace_root",
    [
        "",
        "../escape",
        "..%2Fescape",
        "C:/tmp/run-provider",
        "runs/other-run",
        "runs/run-provider\x00bad",
    ],
)
def test_live_blocks_unsafe_workspace_roots(workspace_root):
    state, plan = _approved_dry_run_result()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(workspace_root=workspace_root),
            plan=plan,
            policy=_valid_live_policy(workspace_root=workspace_root or "runs/run-provider"),
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_workspace_valid"] is False
    assert result.verification_report.metrics["filesystem_writes"] == 0


def test_live_blocks_policy_escalation_for_fake_runtime():
    state, plan = _approved_dry_run_result()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(),
            plan=plan,
            policy=_valid_live_policy(allow_provider_calls=True),
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["live_policy_fake_only"] is False
    assert result.verification_report.metrics["provider_calls"] == 0


def test_live_blocks_tampered_dry_run_plan_reference():
    state, plan = _approved_dry_run_result()
    state["implementation_brief_hash"] = "tampered"

    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "blocked"
    assert checks["dry_run_plan_valid"] is False
    assert result.verification_report.metrics["provider_calls"] == 0


def test_live_fake_runtime_passes_with_zero_side_effects_after_dry_run_plan():
    state, plan = _approved_dry_run_result()
    approval = _valid_live_approval()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=approval,
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    metrics = result.verification_report.metrics
    checks = {check["name"]: check["passed"] for check in result.verification_report.checks}

    assert result.status == "passed"
    assert result.mode == "live"
    assert result.verification_report.passed is True
    assert result.verification_report.generated_files == []
    assert result.artifact_manifest == []
    assert checks["fake_runtime_only"] is True
    assert metrics["fake_live_runtime_invocations"] == 1
    assert metrics["real_daacs_invocations"] == 0
    assert metrics["solar_provider_calls"] == 0
    assert metrics["executed_action_count"] == 0
    assert metrics["provider_calls"] == 0
    assert metrics["subprocess_calls"] == 0
    assert metrics["package_install_calls"] == 0
    assert metrics["server_start_calls"] == 0
    assert metrics["filesystem_writes"] == 0
    assert metrics["network_calls"] == 0
    assert metrics["approval_bypass_count"] == 0
    assert metrics["approval_verifier_fake_count"] == 1
    assert metrics["approval_verifier_policy_check_count"] == 1
    assert metrics["approval_verifier_policy_valid_count"] == 1


def test_live_fake_runtime_does_not_call_host_commands(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("fake live runner attempted a blocked side effect")

    monkeypatch.setattr(subprocess, "run", fail_if_called)
    monkeypatch.setattr(subprocess, "Popen", fail_if_called)
    monkeypatch.setattr(os, "system", fail_if_called)

    state, plan = _approved_dry_run_result()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )

    assert result.status == "passed"
    assert result.verification_report.metrics["subprocess_calls"] == 0
    assert result.verification_report.metrics["package_install_calls"] == 0
    assert result.verification_report.metrics["server_start_calls"] == 0


def test_live_fake_runtime_does_not_write_files_or_call_network(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("fake live runner attempted a blocked side effect")

    monkeypatch.setattr(builtins, "open", fail_if_called)
    monkeypatch.setattr(Path, "write_text", fail_if_called)
    monkeypatch.setattr(Path, "write_bytes", fail_if_called)
    monkeypatch.setattr(Path, "mkdir", fail_if_called)
    monkeypatch.setattr(socket, "create_connection", fail_if_called)
    monkeypatch.setattr(urllib.request, "urlopen", fail_if_called)

    state, plan = _approved_dry_run_result()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )

    assert result.status == "passed"
    assert result.verification_report.metrics["fake_live_runtime_invocations"] == 1
    assert result.verification_report.metrics["network_calls"] == 0


def test_live_fake_runtime_does_not_import_daacs_or_provider_modules(monkeypatch):
    real_import = builtins.__import__

    def fail_blocked_import(name, *args, **kwargs):
        blocked_prefixes = (
            "daacs",
            "langchain_upstage",
            "langchain_tavily",
            "qdrant_client",
            "openai",
            "anthropic",
        )
        if name.startswith(blocked_prefixes):
            raise AssertionError(f"fake live runner attempted blocked import: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_blocked_import)
    state, plan = _approved_dry_run_result()
    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=_valid_live_approval(),
            plan=plan,
            policy=_valid_live_policy(),
        )
    )

    assert result.status == "passed"
    assert result.verification_report.metrics["provider_imports"] == 0


def test_live_fake_runtime_public_payloads_are_sanitized():
    state, plan = _approved_dry_run_result()
    state["safe_note"] = "Bearer live-secret-token"
    approval = _valid_live_approval(approved_by="local-user@example.com")

    result = default_runner_provider_registry().run(
        RunnerRequest(
            run_id="run-provider",
            mode="live",
            state=state,
            approval=approval,
            plan=plan,
            policy=_valid_live_policy(),
        )
    )
    serialized = str(
        {
            "report": result.verification_report.to_dict(),
            "audit_events": result.audit_events,
            "artifact_manifest": result.artifact_manifest,
        }
    )

    assert result.status == "passed"
    assert "live-secret-token" not in serialized
    assert "local-user@example.com" not in serialized
    assert "raw_content" not in serialized
    assert "C:\\\\" not in serialized
    assert approval.signature_id not in serialized
    assert approval.nonce not in serialized
    assert approval.signed_contract_hash not in serialized
    assert approval.verifier_id not in serialized
    assert approval.key_id not in serialized
    assert approval.verifier_policy_id not in serialized
    assert approval.key_identity_id not in serialized
    assert "signed_contract_hash" not in serialized

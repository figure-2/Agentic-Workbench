import builtins
from itertools import count
import os
import socket
import urllib.request
from pathlib import Path

import pytest

from packages.core.repositories import FileBackedReplayNonceRepository
from packages.core.approval_replay_factory import (
    ApprovalReplayRepositoryConfig,
    build_approval_replay_repositories,
)
from packages.core.sqlite_repositories import SQLiteReplayNonceRepository
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.adapters import (
    build_spec_to_daacs_initial_state,
    create_spec_approval,
    implementation_brief_from_prd_package,
    planning_to_build_spec,
)
from packages.daacs_builder.provider_boundary import (
    FakeSolarProProvider,
    PROVIDER_APPROVAL_SCOPE,
    ProviderApprovalRecord,
    ProviderRequest,
    SOLAR_PRO_3_ENV_KEY_NAME,
    provider_approval_decision_hash,
    provider_approval_decision_record_for_request,
    provider_approval_subject_snapshot_for_request,
    provider_replay_scope_for_request,
)
from packages.daacs_builder.approval_persistence import CanonicalApprovalPersistenceService
from packages.daacs_builder.approval_security import (
    ApprovalPolicyResolver,
    ApprovalVerificationResult,
    ApprovalVerifierPolicy,
    DurableReplayStore,
    FakeApprovalVerifier,
    InMemoryReplayRecordAdapter,
    KeyIdentityRecord,
    KeyIdentityRegistry,
    PersistentReplayStore,
    UnavailableReplayRecordAdapter,
    replay_store_from_approval_replay_repositories,
    sign_approval_for_tests,
)
from packages.daacs_builder.runner_provider import RunnerRequest, default_runner_provider_registry
from packages.div_planner.adapters import planning_blueprint_from_div_state, planning_to_prd_package


_provider_approval_counter = count(1)


class RaisingApprovalVerifier:
    def verify(self, approval, *, scope, gate_prefix):
        raise RuntimeError("sig-provider-leaked nonce-provider-leaked signed_contract_hash C:\\secret\\.env")


class PermissiveApprovalVerifier:
    def verify(self, approval, *, scope, gate_prefix):
        return ApprovalVerificationResult(failures=[], metrics={})


class RaisingReplayStore(PersistentReplayStore):
    def claim(self, *, scope: str, nonce: str) -> bool:
        raise RuntimeError("nonce-provider-leaked signed_contract_hash postgres://secret")


def _prompt_contract_hash():
    return stable_contract_hash(
        {
            "purpose": "fake solar provider boundary",
            "input_contract": "sanitized prompt hash only",
        }
    )


def _provider_approval(**overrides):
    approval_index = next(_provider_approval_counter)
    signed = overrides.pop("signed", True)
    signature_id = overrides.pop(
        "signature_id",
        f"sig-provider-run-provider-{approval_index:04d}",
    )
    nonce = overrides.pop("nonce", f"nonce-provider-run-provider-{approval_index:04d}")
    fields = {
        "approved_by": "local-user",
        "approved_at": "2026-05-27T00:00:00Z",
        "run_id": "run-provider",
        "provider_name": "solar-pro-3",
        "model_name": "solar-pro-3",
        "mode": "fake",
        "env_key_name": SOLAR_PRO_3_ENV_KEY_NAME,
        "max_live_api_calls": 0,
        "max_live_llm_calls": 0,
        "expires_at": "2099-01-01T00:00:00Z",
        "audit_log_id": "provider-audit-run-provider",
    }
    fields.update(overrides)
    approval = ProviderApprovalRecord(**fields)
    if signed:
        try:
            signature_scope = provider_replay_scope_for_request(
                ProviderRequest(
                    run_id=fields["run_id"],
                    prompt_contract_hash=_prompt_contract_hash(),
                    provider_name=fields["provider_name"],
                    model_name=fields["model_name"],
                    mode=fields["mode"],
                    env_key_name=fields["env_key_name"],
                    approval=approval,
                )
            )
        except ValueError:
            signature_scope = PROVIDER_APPROVAL_SCOPE
        sign_approval_for_tests(
            approval,
            scope=signature_scope,
            signature_id=signature_id,
            nonce=nonce,
        )
    return approval


def _provider_request(**overrides):
    fields = {
        "run_id": "run-provider",
        "prompt_contract_hash": _prompt_contract_hash(),
        "approval": _provider_approval(),
    }
    fields.update(overrides)
    return ProviderRequest(**fields)


def _fake_provider(**overrides):
    fields = {
        "approval_verifier": FakeApprovalVerifier(),
        "approval_verifier_policy": ApprovalVerifierPolicy(),
        "key_identity_registry": KeyIdentityRegistry(),
        "replay_store": PersistentReplayStore(),
    }
    fields.update(overrides)
    return FakeSolarProProvider(**fields)


def _persist_provider_approval(repositories, request):
    replay_scope = provider_replay_scope_for_request(request)
    snapshot = provider_approval_subject_snapshot_for_request(
        request,
        scope_canonical=replay_scope,
    )
    expected_approval = provider_approval_decision_record_for_request(
        request,
        scope_canonical=replay_scope,
    )
    saved_approval = repositories.approval_repository.save_approval(
        approval_id=expected_approval.approval_id,
        snapshot=snapshot,
        decision=expected_approval.decision,
        approved_by_ref=expected_approval.approved_by_ref,
        approver_role=expected_approval.approver_role,
        approved_at=expected_approval.approved_at,
        expires_at=expected_approval.expires_at,
        policy_id_ref=expected_approval.policy_id_ref,
        key_identity_ref=expected_approval.key_identity_ref,
        audit_log_id=expected_approval.audit_log_id,
        lifecycle_class=expected_approval.lifecycle_class,
        created_at=expected_approval.created_at,
    )
    assert saved_approval.approval_hash == provider_approval_decision_hash(
        request,
        scope_canonical=replay_scope,
    )
    return saved_approval


def _approved_dry_run_request():
    blueprint = planning_blueprint_from_div_state(
        {
            "idea": {
                "toc": ["Agentic Workbench"],
                "rationale": "Need provider boundary isolation.",
                "blueprint": [
                    {"title": "Provider Boundary", "guideline": "plan provider usage only"},
                    {"title": "Approval Gate", "guideline": "block live provider calls"},
                ],
            }
        }
    )
    spec = planning_to_build_spec(blueprint)
    prd_package = planning_to_prd_package(blueprint, build_spec=spec)
    brief = implementation_brief_from_prd_package(prd_package, spec)
    approval = create_spec_approval(brief, approval_id="approval-provider-boundary", approved=True)
    state = build_spec_to_daacs_initial_state(
        spec,
        run_id="run-provider",
        implementation_brief=brief,
        approval=approval,
        require_approval=True,
    )
    return RunnerRequest(
        run_id="run-provider",
        mode="dry_run",
        state=state,
        implementation_brief=brief,
        spec_approval=approval,
    )


def test_provider_boundary_blocks_without_approval():
    result = FakeSolarProProvider().invoke(
        ProviderRequest(run_id="run-provider", prompt_contract_hash=_prompt_contract_hash())
    )
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_present"] is False
    assert result.metrics["approval_bypass_count"] == 1
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["live_api_calls"] == 0
    assert result.metrics["live_llm_calls"] == 0


def test_provider_boundary_blocks_malformed_approval():
    result = FakeSolarProProvider().invoke(
        ProviderRequest(
            run_id="run-provider",
            prompt_contract_hash=_prompt_contract_hash(),
            approval="approved in chat",
        )
    )
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_valid"] is False
    assert result.metrics["provider_imports"] == 0


def test_provider_boundary_blocks_without_approval_verifier():
    result = FakeSolarProProvider(replay_store=PersistentReplayStore()).invoke(_provider_request())
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_verifier_present"] is False
    assert result.metrics["approval_verifier_missing_block_count"] == 1
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["live_api_calls"] == 0


def test_provider_boundary_blocks_verifier_exception_without_public_exposure():
    result = _fake_provider(approval_verifier=RaisingApprovalVerifier()).invoke(_provider_request())
    serialized = str(result.to_dict())
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_verifier_available"] is False
    assert result.metrics["approval_verifier_missing_block_count"] == 1
    assert result.metrics["fake_provider_invocations"] == 0
    assert "sig-provider-leaked" not in serialized
    assert "nonce" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "C:\\\\" not in serialized


@pytest.mark.parametrize(
    ("approval_overrides", "verifier_policy", "expected_gate", "expected_metric"),
    [
        (
            {"verifier_id": "verifier-unknown-local"},
            ApprovalVerifierPolicy(),
            "provider_approval_verifier_trusted",
            "approval_verifier_identity_block_count",
        ),
        (
            {},
            ApprovalVerifierPolicy(revoked_verifier_ids=("verifier-local-fake",)),
            "provider_approval_verifier_trusted",
            "approval_verifier_identity_block_count",
        ),
        (
            {"key_id": "key-unknown-local"},
            ApprovalVerifierPolicy(),
            "provider_approval_key_trusted",
            "approval_verifier_key_block_count",
        ),
        (
            {},
            ApprovalVerifierPolicy(revoked_key_ids=("key-local-fake",)),
            "provider_approval_key_trusted",
            "approval_verifier_key_block_count",
        ),
        (
            {"key_id": "-----BEGIN PRIVATE KEY-----"},
            ApprovalVerifierPolicy(),
            "provider_approval_key_trusted",
            "approval_verifier_key_block_count",
        ),
        (
            {"verifier_scope": "live_runner"},
            ApprovalVerifierPolicy(),
            "provider_approval_scope_matches",
            "approval_verifier_scope_block_count",
        ),
        (
            {"approved_at": "2099-01-01T00:00:00Z", "expires_at": "2099-01-02T00:00:00Z"},
            ApprovalVerifierPolicy(),
            "provider_approval_approved_at_skew_valid",
            "approval_verifier_skew_block_count",
        ),
    ],
)
def test_provider_boundary_blocks_untrusted_verifier_policy(
    approval_overrides,
    verifier_policy,
    expected_gate,
    expected_metric,
):
    approval = _provider_approval(**approval_overrides)
    result = _fake_provider(approval_verifier=FakeApprovalVerifier(verifier_policy)).invoke(
        _provider_request(approval=approval)
    )
    serialized = str(result.to_dict())
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks[expected_gate] is False
    assert result.metrics[expected_metric] == 1
    assert result.metrics["approval_verifier_policy_block_count"] == 1
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["live_api_calls"] == 0
    assert result.metrics["live_llm_calls"] == 0
    assert result.metrics["network_calls"] == 0
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
            "provider_approval_verifier_trusted",
            "approval_verifier_identity_block_count",
        ),
        (
            {},
            ApprovalVerifierPolicy(revoked_verifier_ids=("verifier-local-fake",)),
            "provider_approval_verifier_trusted",
            "approval_verifier_identity_block_count",
        ),
        (
            {"key_id": "key-unknown-local"},
            ApprovalVerifierPolicy(),
            "provider_approval_key_trusted",
            "approval_verifier_key_block_count",
        ),
        (
            {},
            ApprovalVerifierPolicy(revoked_key_ids=("key-local-fake",)),
            "provider_approval_key_trusted",
            "approval_verifier_key_block_count",
        ),
        (
            {"verifier_scope": "live_runner"},
            ApprovalVerifierPolicy(),
            "provider_approval_scope_matches",
            "approval_verifier_scope_block_count",
        ),
        (
            {"approved_at": "2099-01-01T00:00:00Z", "expires_at": "2099-01-02T00:00:00Z"},
            ApprovalVerifierPolicy(),
            "provider_approval_approved_at_skew_valid",
            "approval_verifier_skew_block_count",
        ),
    ],
)
def test_provider_boundary_enforces_policy_contract_after_custom_verifier(
    approval_overrides,
    verifier_policy,
    expected_gate,
    expected_metric,
):
    approval = _provider_approval(**approval_overrides)
    result = _fake_provider(
        approval_verifier=PermissiveApprovalVerifier(),
        approval_verifier_policy=verifier_policy,
        key_identity_registry=KeyIdentityRegistry(
            [KeyIdentityRecord(verifier_id=approval.verifier_id, key_id=approval.key_id)]
        ),
    ).invoke(_provider_request(approval=approval))
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks[expected_gate] is False
    assert result.metrics[expected_metric] == 1
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["live_api_calls"] == 0
    assert result.metrics["live_llm_calls"] == 0
    assert result.metrics["network_calls"] == 0


@pytest.mark.parametrize(
    ("provider_overrides", "expected_gate", "expected_metric"),
    [
        (
            {"approval_verifier_policy": None, "approval_policy_resolver": None},
            "provider_approval_policy_resolver_present",
            "approval_policy_resolver_missing_block_count",
        ),
        (
            {"key_identity_registry": None},
            "provider_approval_key_identity_registry_present",
            "key_identity_registry_missing_block_count",
        ),
    ],
)
def test_provider_boundary_blocks_missing_resolver_or_registry(
    provider_overrides,
    expected_gate,
    expected_metric,
):
    result = _fake_provider(**provider_overrides).invoke(_provider_request())
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks[expected_gate] is False
    assert result.metrics[expected_metric] == 1
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["live_api_calls"] == 0
    assert result.metrics["live_llm_calls"] == 0
    assert result.metrics["network_calls"] == 0


@pytest.mark.parametrize(
    ("approval_overrides", "provider_overrides", "expected_gate", "expected_metric"),
    [
        (
            {"verifier_policy_id": "policy-unknown-local"},
            {},
            "provider_approval_policy_resolved",
            "approval_policy_unknown_block_count",
        ),
        (
            {},
            {"approval_policy_resolver": ApprovalPolicyResolver([])},
            "provider_approval_policy_resolved",
            "approval_policy_unknown_block_count",
        ),
        (
            {},
            {"key_identity_registry": KeyIdentityRegistry([])},
            "provider_approval_key_identity_trusted",
            "key_identity_registry_block_count",
        ),
        (
            {"key_identity_id": "key-identity-revoked"},
            {
                "key_identity_registry": KeyIdentityRegistry(
                    [KeyIdentityRecord(identity_id="key-identity-revoked", revoked=True)]
                )
            },
            "provider_approval_key_identity_trusted",
            "key_identity_revoked_block_count",
        ),
        (
            {},
            {
                "key_identity_registry": KeyIdentityRegistry(
                    [KeyIdentityRecord(key_id="key-other-local")]
                )
            },
            "provider_approval_policy_key_matches",
            "policy_key_mismatch_block_count",
        ),
    ],
)
def test_provider_boundary_blocks_policy_resolver_and_key_identity_failures(
    approval_overrides,
    provider_overrides,
    expected_gate,
    expected_metric,
):
    approval = _provider_approval(**approval_overrides)
    result = _fake_provider(**provider_overrides).invoke(_provider_request(approval=approval))
    serialized = str(result.to_dict())
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks[expected_gate] is False
    assert result.metrics[expected_metric] == 1
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["live_api_calls"] == 0
    assert result.metrics["live_llm_calls"] == 0
    assert result.metrics["network_calls"] == 0
    assert approval.signature_id not in serialized
    assert approval.nonce not in serialized
    assert approval.signed_contract_hash not in serialized
    assert approval.verifier_policy_id not in serialized
    assert approval.key_identity_id not in serialized


def test_provider_boundary_blocks_unsigned_approval():
    result = _fake_provider().invoke(
        _provider_request(approval=_provider_approval(signed=False))
    )
    serialized = str(result.to_dict())
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_signature_valid"] is False
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["network_calls"] == 0
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "nonce" not in serialized


def test_provider_boundary_blocks_tampered_signed_approval_payload():
    approval = _provider_approval()
    approval.audit_log_id = "provider-audit-run-provider-tampered"

    result = _fake_provider().invoke(_provider_request(approval=approval))
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_signature_valid"] is False
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0


def test_provider_boundary_blocks_live_scope_signed_approval_reuse():
    approval = _provider_approval(signed=False)
    sign_approval_for_tests(
        approval,
        scope="live_runner",
        signature_id="sig-provider-cross-scope",
        nonce="nonce-provider-cross-scope",
    )

    result = _fake_provider().invoke(_provider_request(approval=approval))
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_signature_valid"] is False
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["live_api_calls"] == 0
    assert result.metrics["live_llm_calls"] == 0
    assert result.metrics["network_calls"] == 0


def test_provider_boundary_blocks_signed_approval_reuse_for_different_prompt_subject():
    approval = _provider_approval(
        signature_id="sig-provider-subject-reuse",
        nonce="nonce-provider-subject-reuse",
    )
    request = _provider_request(
        approval=approval,
        prompt_contract_hash=stable_contract_hash({"different": "prompt-subject"}),
    )

    result = _fake_provider().invoke(request)
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_signature_valid"] is False
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["live_api_calls"] == 0
    assert result.metrics["live_llm_calls"] == 0


def test_provider_boundary_blocks_reused_nonce():
    provider = _fake_provider()
    request = _provider_request()

    first = provider.invoke(request)
    second = provider.invoke(request)
    checks = {check["name"]: check["passed"] for check in second.checks}

    assert first.status == "passed"
    assert second.status == "blocked"
    assert checks["provider_approval_replay_fresh"] is False
    assert second.metrics["approval_replay_block_count"] == 1
    assert second.metrics["fake_provider_invocations"] == 0
    assert second.metrics["provider_calls"] == 0


def test_provider_boundary_blocks_reused_nonce_across_fresh_provider_instances():
    replay_store = PersistentReplayStore()
    request = _provider_request(
        approval=_provider_approval(
            signature_id="sig-provider-cross-instance",
            nonce="nonce-provider-cross-instance",
        )
    )

    first = _fake_provider(replay_store=replay_store).invoke(request)
    second = _fake_provider(replay_store=replay_store).invoke(request)
    checks = {check["name"]: check["passed"] for check in second.checks}

    assert first.status == "passed"
    assert second.status == "blocked"
    assert checks["provider_approval_replay_fresh"] is False
    assert second.metrics["approval_replay_block_count"] == 1
    assert second.metrics["fake_provider_invocations"] == 0


def test_provider_boundary_blocks_reused_nonce_after_restart_simulation():
    replay_store = PersistentReplayStore()
    request = _provider_request(
        approval=_provider_approval(
            signature_id="sig-provider-restart-simulation",
            nonce="nonce-provider-restart-simulation",
        )
    )

    first = _fake_provider(replay_store=replay_store).invoke(request)
    restarted_store = PersistentReplayStore.from_records(replay_store.export_records())
    second = _fake_provider(replay_store=restarted_store).invoke(request)
    checks = {check["name"]: check["passed"] for check in second.checks}

    assert first.status == "passed"
    assert second.status == "blocked"
    assert checks["provider_approval_replay_fresh"] is False
    assert second.metrics["approval_replay_store_hit_count"] == 1
    assert second.metrics["fake_provider_invocations"] == 0


def test_provider_boundary_blocks_replay_store_exception_without_consuming_runtime():
    result = _fake_provider(replay_store=RaisingReplayStore()).invoke(_provider_request())
    serialized = str(result.to_dict())
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_replay_store_available"] is False
    assert result.metrics["approval_replay_store_hit_count"] == 1
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert "nonce" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "postgres://secret" not in serialized


def test_provider_boundary_blocks_unavailable_durable_replay_adapter():
    result = _fake_provider(replay_store=DurableReplayStore(UnavailableReplayRecordAdapter())).invoke(
        _provider_request()
    )
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_replay_store_available"] is False
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["live_api_calls"] == 0
    assert result.metrics["live_llm_calls"] == 0
    assert result.metrics["network_calls"] == 0


def test_provider_boundary_blocks_reused_nonce_after_durable_restart_simulation():
    adapter = InMemoryReplayRecordAdapter()
    request = _provider_request(
        approval=_provider_approval(
            signature_id="sig-provider-durable-restart",
            nonce="nonce-provider-durable-restart",
        )
    )

    first = _fake_provider(replay_store=DurableReplayStore(adapter)).invoke(request)
    second = _fake_provider(replay_store=DurableReplayStore(adapter)).invoke(request)
    checks = {check["name"]: check["passed"] for check in second.checks}

    assert first.status == "passed"
    assert second.status == "blocked"
    assert checks["provider_approval_replay_fresh"] is False
    assert second.metrics["approval_replay_store_hit_count"] == 1
    assert second.metrics["fake_provider_invocations"] == 0
    assert second.metrics["provider_calls"] == 0


def test_provider_boundary_blocks_reused_nonce_with_file_backed_replay_repository(tmp_path):
    request = _provider_request(
        approval=_provider_approval(
            signature_id="sig-provider-file-backed",
            nonce="nonce-provider-file-backed",
        )
    )

    first = _fake_provider(
        replay_store=DurableReplayStore(FileBackedReplayNonceRepository(root=tmp_path))
    ).invoke(request)
    second = _fake_provider(
        replay_store=DurableReplayStore(FileBackedReplayNonceRepository(root=tmp_path))
    ).invoke(request)
    checks = {check["name"]: check["passed"] for check in second.checks}

    assert first.status == "passed"
    assert second.status == "blocked"
    assert checks["provider_approval_replay_fresh"] is False
    assert second.metrics["approval_replay_store_hit_count"] == 1
    assert second.metrics["fake_provider_invocations"] == 0
    assert second.metrics["provider_calls"] == 0
    assert second.metrics["live_api_calls"] == 0
    assert second.metrics["live_llm_calls"] == 0
    assert "aw.approval.v1/provider_approval/" in (tmp_path / "replay_nonces.json").read_text(
        encoding="utf-8"
    )


def test_provider_boundary_uses_sqlite_replay_repository_and_blocks_reused_nonce_after_restart(tmp_path):
    request = _provider_request(
        approval=_provider_approval(
            signature_id="sig-provider-sqlite-backed",
            nonce="nonce-provider-sqlite-backed",
        )
    )
    first_repositories = build_approval_replay_repositories(
        ApprovalReplayRepositoryConfig(backend="sqlite", root=tmp_path)
    )
    second_repositories = build_approval_replay_repositories(
        ApprovalReplayRepositoryConfig(backend="sqlite", root=tmp_path)
    )

    assert isinstance(first_repositories.replay_nonce_repository, SQLiteReplayNonceRepository)
    saved_approval = _persist_provider_approval(first_repositories, request)
    first = _fake_provider(
        replay_store=replay_store_from_approval_replay_repositories(first_repositories)
    ).invoke(request)
    second = _fake_provider(
        replay_store=replay_store_from_approval_replay_repositories(second_repositories)
    ).invoke(request)
    checks = {check["name"]: check["passed"] for check in second.checks}
    serialized = str(second.to_dict())

    assert first.status == "passed"
    assert second.status == "blocked"
    assert checks["provider_approval_replay_fresh"] is False
    assert second.metrics["approval_replay_store_hit_count"] == 1
    assert second.metrics["fake_provider_invocations"] == 0
    assert second.metrics["provider_calls"] == 0
    assert second.metrics["live_api_calls"] == 0
    assert second.metrics["live_llm_calls"] == 0
    assert request.approval.nonce not in serialized
    assert request.approval.signature_id not in serialized
    assert request.approval.signed_contract_hash not in serialized
    sqlite_rows = str(
        {
            "approval": first_repositories.approval_repository.get_approval(
                saved_approval.approval_id
            ).to_dict(),
            "replay": [
                record.to_dict()
                for record in first_repositories.replay_nonce_repository.list_records()
            ],
        }
    )
    assert request.approval.nonce not in sqlite_rows
    assert request.approval.signature_id not in sqlite_rows
    assert request.approval.signed_contract_hash not in sqlite_rows
    assert "signed_contract_hash" not in sqlite_rows


def test_provider_boundary_persists_canonical_approval_before_sqlite_replay_claim(tmp_path):
    request = _provider_request(
        approval=_provider_approval(
            signature_id="sig-provider-persist-service",
            nonce="nonce-provider-persist-service",
        )
    )
    first_repositories = build_approval_replay_repositories(
        ApprovalReplayRepositoryConfig(backend="sqlite", root=tmp_path)
    )
    second_repositories = build_approval_replay_repositories(
        ApprovalReplayRepositoryConfig(backend="sqlite", root=tmp_path)
    )
    service = CanonicalApprovalPersistenceService(first_repositories.approval_repository)
    replay_store = replay_store_from_approval_replay_repositories(first_repositories)

    first = _fake_provider(
        replay_store=replay_store,
        approval_persistence_service=service,
        require_approval_persistence=True,
    ).invoke(request)
    replay_scope = provider_replay_scope_for_request(request)
    expected_approval = provider_approval_decision_record_for_request(
        request,
        scope_canonical=replay_scope,
    )
    saved_approval = first_repositories.approval_repository.get_approval(
        expected_approval.approval_id
    )
    assert saved_approval is not None
    second = _fake_provider(
        replay_store=replay_store_from_approval_replay_repositories(second_repositories),
        approval_persistence_service=CanonicalApprovalPersistenceService(
            second_repositories.approval_repository
        ),
        require_approval_persistence=True,
    ).invoke(request)
    checks = {check["name"]: check["passed"] for check in second.checks}
    serialized_rows = str(
        {
            "approval": saved_approval.to_dict(),
            "replay": [
                record.to_dict()
                for record in first_repositories.replay_nonce_repository.list_records()
            ],
        }
    )

    assert first.status == "passed"
    assert saved_approval.approval_hash == expected_approval.approval_hash
    assert saved_approval.approval_hash == provider_approval_decision_hash(
        request,
        scope_canonical=replay_scope,
    )
    assert first.metrics["approval_persistence_persist_count"] == 1
    assert first.metrics["fake_provider_invocations"] == 1
    assert second.status == "blocked"
    assert checks["provider_approval_replay_fresh"] is False
    assert second.metrics["approval_persistence_duplicate_count"] == 1
    assert second.metrics["fake_provider_invocations"] == 0
    assert request.approval.nonce not in serialized_rows
    assert request.approval.signature_id not in serialized_rows
    assert request.approval.signed_contract_hash not in serialized_rows
    assert "signed_contract_hash" not in serialized_rows


def test_provider_boundary_blocks_missing_approval_persistence_service_before_fake_invocation(tmp_path):
    repositories = build_approval_replay_repositories(
        ApprovalReplayRepositoryConfig(backend="sqlite", root=tmp_path)
    )
    request = _provider_request(
        approval=_provider_approval(
            signature_id="sig-provider-missing-persist-service",
            nonce="nonce-provider-missing-persist-service",
        )
    )
    result = _fake_provider(
        replay_store=replay_store_from_approval_replay_repositories(repositories),
        require_approval_persistence=True,
    ).invoke(request)
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_persistence_service_present"] is False
    assert result.metrics["approval_persistence_missing_block_count"] == 1
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0


def test_provider_boundary_blocks_sqlite_replay_without_persisted_canonical_approval(tmp_path):
    repositories = build_approval_replay_repositories(
        ApprovalReplayRepositoryConfig(backend="sqlite", root=tmp_path)
    )
    result = _fake_provider(
        replay_store=replay_store_from_approval_replay_repositories(repositories)
    ).invoke(
        _provider_request(
            approval=_provider_approval(
                signature_id="sig-provider-sqlite-no-approval",
                nonce="nonce-provider-sqlite-no-approval",
            )
        )
    )
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_replay_store_available"] is False
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0


def test_provider_boundary_blocks_corrupted_sqlite_replay_repository_before_fake_invocation(tmp_path):
    repositories = build_approval_replay_repositories(
        ApprovalReplayRepositoryConfig(backend="sqlite", root=tmp_path)
    )
    request = _provider_request(
        approval=_provider_approval(
            signature_id="sig-provider-sqlite-corrupt",
            nonce="nonce-provider-sqlite-corrupt",
        )
    )
    _persist_provider_approval(repositories, request)
    replay_store = replay_store_from_approval_replay_repositories(repositories)
    repositories.sqlite_store.path.write_text("not a sqlite database", encoding="utf-8")

    result = _fake_provider(replay_store=replay_store).invoke(request)
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_replay_store_available"] is False
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["live_api_calls"] == 0
    assert result.metrics["live_llm_calls"] == 0


@pytest.mark.parametrize(
    "approval_overrides",
    [
        {
            "signed": False,
            "signature_id": "bad",
            "nonce": "nonce-provider-malformed-sig",
            "signed_contract_hash": "a" * 64,
        },
        {
            "signed": False,
            "signature_id": "sig-provider-malformed-nonce",
            "nonce": "bad",
            "signed_contract_hash": "a" * 64,
        },
        {
            "signed": False,
            "signature_id": "sig-provider-malformed-hash",
            "nonce": "nonce-provider-malformed-hash",
            "signed_contract_hash": "bad",
        },
    ],
)
def test_provider_boundary_blocks_malformed_signature_envelope(approval_overrides):
    approval = _provider_approval(**approval_overrides)
    result = _fake_provider().invoke(_provider_request(approval=approval))
    serialized = str(result.to_dict())
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks["provider_approval_signature_valid"] is False
    assert result.metrics["fake_provider_invocations"] == 0
    assert "signature_id" not in serialized
    assert "signed_contract_hash" not in serialized
    assert "nonce" not in serialized


@pytest.mark.parametrize(
    ("approval_overrides", "request_overrides", "expected_gate"),
    [
        ({"run_id": "other-run"}, {}, "provider_approval_valid"),
        ({"provider_name": "other-provider"}, {}, "provider_approval_valid"),
        ({"model_name": "other-model"}, {}, "provider_approval_valid"),
        ({"mode": "live"}, {}, "provider_approval_valid"),
        ({"env_key_name": "OTHER_API_KEY"}, {}, "provider_approval_valid"),
        ({"max_live_api_calls": 1}, {}, "provider_approval_valid"),
        ({"max_live_llm_calls": 1}, {}, "provider_approval_valid"),
        ({"audit_log_id": ""}, {}, "provider_audit_configured"),
        (
            {"approved_at": "2026-05-27T00:00:00Z", "expires_at": "2026-05-27T00:00:00Z"},
            {},
            "provider_approval_valid",
        ),
        ({"expires_at": "2000-01-01T00:00:00Z", "approved_at": "1999-01-01T00:00:00Z"}, {}, "provider_approval_valid"),
        ({}, {"provider_name": "other-provider"}, "provider_name_supported"),
        ({}, {"model_name": "other-model"}, "provider_model_supported"),
        ({}, {"mode": "live"}, "provider_mode_fake"),
        ({}, {"env_key_name": "upstage_api_key"}, "provider_env_key_name_valid"),
        ({}, {"env_key_name": "UPSTAGE_API_KEY "}, "provider_env_key_name_valid"),
        ({}, {"env_key_name": "API_KEY"}, "provider_env_key_name_valid"),
        ({}, {"env_key_name": "UPSTAGE_API_KEY=secret"}, "provider_env_key_name_valid"),
        ({}, {"env_key_name": "SECRET_VALUE"}, "provider_env_key_name_valid"),
        ({}, {"prompt_contract_hash": "raw prompt"}, "provider_prompt_contract_hash_valid"),
    ],
)
def test_provider_boundary_blocks_invalid_contracts(
    approval_overrides,
    request_overrides,
    expected_gate,
):
    approval = _provider_approval(**approval_overrides)
    request = _provider_request(approval=approval, **request_overrides)

    result = _fake_provider().invoke(request)
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert checks[expected_gate] is False
    assert result.metrics["fake_provider_invocations"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["network_calls"] == 0


def test_provider_boundary_blocks_unsafe_run_id_without_public_exposure():
    unsafe_run_id = "owner@example.com/demo"
    result = _fake_provider().invoke(
        _provider_request(
            run_id=unsafe_run_id,
            approval=_provider_approval(run_id=unsafe_run_id),
        )
    )
    serialized = str(result.to_dict())
    checks = {check["name"]: check["passed"] for check in result.checks}

    assert result.status == "blocked"
    assert result.run_id == "invalid-run-id"
    assert checks["provider_run_id_valid"] is False
    assert unsafe_run_id not in serialized
    assert "owner@example.com" not in serialized
    assert result.metrics["provider_secret_value_reads"] == 0


def test_fake_solar_provider_passes_without_reading_env_secret_or_calling_live_provider(
    monkeypatch,
):
    dummy_secret = "upstage-test-secret-value"
    monkeypatch.setenv(SOLAR_PRO_3_ENV_KEY_NAME, dummy_secret)

    def fail_if_env_value_read(*args, **kwargs):
        raise AssertionError("provider boundary attempted to read an env secret value")

    monkeypatch.setattr(os, "getenv", fail_if_env_value_read)
    monkeypatch.setattr(os.environ, "get", fail_if_env_value_read)

    result = _fake_provider().invoke(_provider_request())
    serialized = str(result.to_dict())

    assert result.status == "passed"
    assert result.output_contract["env_key_name"] == SOLAR_PRO_3_ENV_KEY_NAME
    assert dummy_secret not in serialized
    assert result.metrics["fake_provider_invocations"] == 1
    assert result.metrics["env_key_name_reference_count"] == 1
    assert result.metrics["provider_secret_value_reads"] == 0
    assert result.metrics["provider_calls"] == 0
    assert result.metrics["live_api_calls"] == 0
    assert result.metrics["live_llm_calls"] == 0
    assert result.metrics["network_calls"] == 0
    assert result.metrics["approval_verifier_fake_count"] == 1
    assert result.metrics["approval_verifier_policy_check_count"] == 1
    assert result.metrics["approval_verifier_policy_valid_count"] == 1
    assert result.metrics["approval_verifier_secret_value_reads"] == 0
    assert result.metrics["approval_verifier_key_file_reads"] == 0


def test_fake_solar_provider_and_verifier_do_not_read_dotenv_or_call_network(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("provider boundary attempted a blocked side effect")

    monkeypatch.setattr(builtins, "open", fail_if_called)
    monkeypatch.setattr(Path, "read_text", fail_if_called)
    monkeypatch.setattr(socket, "create_connection", fail_if_called)
    monkeypatch.setattr(urllib.request, "urlopen", fail_if_called)

    result = _fake_provider().invoke(_provider_request())

    assert result.status == "passed"
    assert result.metrics["network_calls"] == 0
    assert result.metrics["provider_secret_value_reads"] == 0
    assert result.metrics["approval_verifier_secret_value_reads"] == 0
    assert result.metrics["approval_verifier_key_file_reads"] == 0


def test_fake_solar_provider_does_not_import_upstage_or_provider_runtime(monkeypatch):
    real_import = builtins.__import__

    def fail_blocked_import(name, *args, **kwargs):
        blocked_prefixes = (
            "upstage",
            "langchain_upstage",
            "openai",
            "anthropic",
            "httpx",
            "requests",
        )
        if name.startswith(blocked_prefixes):
            raise AssertionError(f"provider boundary attempted blocked import: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_blocked_import)
    result = _fake_provider().invoke(_provider_request())

    assert result.status == "passed"
    assert result.metrics["provider_imports"] == 0


def test_provider_boundary_public_payload_contains_env_key_name_only():
    approval = _provider_approval(approved_by="local-user@example.com")
    result = _fake_provider().invoke(_provider_request(approval=approval))
    serialized = str(result.to_dict())

    assert result.status == "passed"
    assert SOLAR_PRO_3_ENV_KEY_NAME in serialized
    assert "local-user@example.com" not in serialized
    assert "raw_prompt" not in serialized
    assert "raw_content" not in serialized
    assert "Authorization" not in serialized
    assert approval.signature_id not in serialized
    assert approval.nonce not in serialized
    assert approval.signed_contract_hash not in serialized
    assert approval.verifier_id not in serialized
    assert approval.key_id not in serialized
    assert approval.verifier_policy_id not in serialized
    assert approval.key_identity_id not in serialized
    assert "signed_contract_hash" not in serialized


def test_offline_and_dry_run_do_not_import_solar_or_upstage_modules(monkeypatch):
    real_import = builtins.__import__

    def fail_blocked_import(name, *args, **kwargs):
        blocked_prefixes = (
            "upstage",
            "langchain_upstage",
            "openai",
            "anthropic",
            "httpx",
            "requests",
        )
        if name.startswith(blocked_prefixes):
            raise AssertionError(f"offline/dry-run attempted blocked provider import: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_blocked_import)

    offline_result = default_runner_provider_registry().run(
        RunnerRequest(run_id="run-provider", mode="offline", state=_approved_dry_run_request().state)
    )
    dry_run_result = default_runner_provider_registry().run(_approved_dry_run_request())

    assert offline_result.status == "passed"
    assert dry_run_result.status == "approval_required"
    assert offline_result.verification_report.metrics["provider_imports"] == 0
    assert dry_run_result.verification_report.metrics["provider_imports"] == 0

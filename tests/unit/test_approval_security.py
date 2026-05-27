from packages.daacs_builder.approval_security import (
    ApprovalPolicyResolver,
    ApprovalVerifierPolicy,
    DurableReplayStore,
    FakeApprovalVerifier,
    InMemoryReplayRecordAdapter,
    KeyIdentityRecord,
    KeyIdentityRegistry,
    PersistentReplayStore,
    UnavailableReplayRecordAdapter,
    enforce_resolved_approval_contract_policy,
    sign_approval_for_tests,
)
from packages.daacs_builder.runner_provider import ApprovalRecord


def test_persistent_replay_store_claims_are_scope_isolated_and_export_sanitized():
    store = PersistentReplayStore()

    assert store.claim(scope="live_runner", nonce="nonce-shared-scope-test") is True
    assert store.claim(scope="live_runner", nonce="nonce-shared-scope-test") is False
    assert store.claim(scope="provider_boundary", nonce="nonce-shared-scope-test") is True

    serialized = str(store.export_records())
    assert "nonce-shared-scope-test" not in serialized
    assert "live_runner" in serialized
    assert "provider_boundary" in serialized


def test_persistent_replay_store_restart_simulation_keeps_claimed_authorization():
    store = PersistentReplayStore()

    assert store.claim(scope="provider_boundary", nonce="nonce-restart-store-test") is True
    restarted = PersistentReplayStore.from_records(store.export_records())

    assert restarted.claim(scope="provider_boundary", nonce="nonce-restart-store-test") is False
    assert restarted.claim(scope="provider_boundary", nonce="nonce-new-store-test") is True


def test_fake_approval_verifier_preserves_identity_policy_metrics():
    approval = ApprovalRecord(
        approved_by="local-user",
        approved_at="2026-05-27T00:00:00Z",
        run_id="run-provider",
        mode="live",
        allowed_operations=["fake_runtime"],
        max_provider_calls=0,
        max_subprocess_calls=0,
        max_package_installs=0,
        max_server_starts=0,
        max_files_written=0,
        workspace_root="runs/run-provider",
        expires_at="2099-01-01T00:00:00Z",
        rollback_plan_id="rollback-run-provider",
        audit_log_id="audit-run-provider",
    )
    sign_approval_for_tests(
        approval,
        scope="live_runner",
        signature_id="sig-approval-security-metrics",
        nonce="nonce-approval-security-metrics",
    )

    result = FakeApprovalVerifier().verify(
        approval,
        scope="live_runner",
        gate_prefix="live_approval",
    )

    assert result.failures == []
    assert result.metrics["approval_verifier_fake_count"] == 1
    assert result.metrics["approval_verifier_policy_check_count"] == 1
    assert result.metrics["approval_verifier_policy_valid_count"] == 1


def test_policy_resolver_blocks_unknown_policy_id():
    approval = ApprovalRecord(
        approved_by="local-user",
        approved_at="2026-05-27T00:00:00Z",
        run_id="run-provider",
        mode="live",
        allowed_operations=["fake_runtime"],
        max_provider_calls=0,
        max_subprocess_calls=0,
        max_package_installs=0,
        max_server_starts=0,
        max_files_written=0,
        workspace_root="runs/run-provider",
        expires_at="2099-01-01T00:00:00Z",
        rollback_plan_id="rollback-run-provider",
        audit_log_id="audit-run-provider",
        verifier_policy_id="policy-unknown-local",
    )
    sign_approval_for_tests(
        approval,
        scope="live_runner",
        signature_id="sig-approval-policy-unknown",
        nonce="nonce-approval-policy-unknown",
    )

    result = enforce_resolved_approval_contract_policy(
        approval,
        scope="live_runner",
        gate_prefix="live_approval",
        policy_resolver=ApprovalPolicyResolver(),
        key_identity_registry=KeyIdentityRegistry(),
    )

    assert result.failures[0][0] == "live_approval_policy_resolved"
    assert result.metrics["approval_policy_unknown_block_count"] == 1


def test_key_identity_registry_blocks_policy_key_mismatch():
    approval = ApprovalRecord(
        approved_by="local-user",
        approved_at="2026-05-27T00:00:00Z",
        run_id="run-provider",
        mode="live",
        allowed_operations=["fake_runtime"],
        max_provider_calls=0,
        max_subprocess_calls=0,
        max_package_installs=0,
        max_server_starts=0,
        max_files_written=0,
        workspace_root="runs/run-provider",
        expires_at="2099-01-01T00:00:00Z",
        rollback_plan_id="rollback-run-provider",
        audit_log_id="audit-run-provider",
        key_identity_id="key-identity-mismatch",
    )
    sign_approval_for_tests(
        approval,
        scope="live_runner",
        signature_id="sig-approval-key-mismatch",
        nonce="nonce-approval-key-mismatch",
    )
    registry = KeyIdentityRegistry(
        [KeyIdentityRecord(identity_id="key-identity-mismatch", key_id="key-other-local")]
    )

    result = enforce_resolved_approval_contract_policy(
        approval,
        scope="live_runner",
        gate_prefix="live_approval",
        policy_resolver=ApprovalPolicyResolver(),
        key_identity_registry=registry,
    )

    assert result.failures[0][0] == "live_approval_policy_key_matches"
    assert result.metrics["policy_key_mismatch_block_count"] == 1


def test_durable_replay_store_restart_simulation_keeps_claimed_authorization():
    adapter = InMemoryReplayRecordAdapter()
    first_store = DurableReplayStore(adapter)

    assert first_store.claim(scope="provider_boundary", nonce="nonce-durable-replay") is True
    restarted_store = DurableReplayStore(adapter)

    assert restarted_store.claim(scope="provider_boundary", nonce="nonce-durable-replay") is False
    assert "nonce-durable-replay" not in str(restarted_store.export_records())


def test_durable_replay_store_adapter_unavailable_blocks_claim():
    store = DurableReplayStore(UnavailableReplayRecordAdapter())

    try:
        store.claim(scope="provider_boundary", nonce="nonce-unavailable-replay")
    except RuntimeError:
        blocked = True
    else:
        blocked = False

    assert blocked is True

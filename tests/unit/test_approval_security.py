from packages.daacs_builder.approval_security import (
    FakeApprovalVerifier,
    PersistentReplayStore,
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

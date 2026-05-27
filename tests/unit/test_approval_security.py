from packages.daacs_builder.approval_security import PersistentReplayStore


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

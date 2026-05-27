"""Approval signature and replay guard skeletons.

This module performs structural approval checks only. It does not read signing
secrets, environment values, key files, or external identity providers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from typing import Any, Protocol


APPROVAL_SIGNATURE_ID_PATTERN = re.compile(r"^sig-[A-Za-z0-9_.-]{8,80}$")
APPROVAL_NONCE_PATTERN = re.compile(r"^nonce-[A-Za-z0-9_.-]{8,80}$")
APPROVAL_VERIFIER_ID_PATTERN = re.compile(r"^verifier-[A-Za-z0-9_.-]{4,80}$")
APPROVAL_KEY_ID_PATTERN = re.compile(r"^key-[A-Za-z0-9_.-]{4,80}$")
APPROVAL_POLICY_ID_PATTERN = re.compile(r"^policy-[A-Za-z0-9_.-]{4,80}$")
APPROVAL_KEY_IDENTITY_ID_PATTERN = re.compile(r"^key-identity-[A-Za-z0-9_.-]{4,80}$")
APPROVAL_SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{4,80}$")
CONTRACT_HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")
DEFAULT_VERIFIER_ID = "verifier-local-fake"
DEFAULT_KEY_ID = "key-local-fake"
DEFAULT_POLICY_ID = "policy-local-fake"
DEFAULT_KEY_IDENTITY_ID = "key-identity-local-fake"


@dataclass(frozen=True, slots=True)
class ApprovalVerificationResult:
    """Verifier result with sanitized gate failures and metrics."""

    failures: list[tuple[str, str]]
    metrics: dict[str, int]


@dataclass(frozen=True, slots=True)
class ApprovalVerifierPolicy:
    """Static verifier/key policy for local skeleton tests."""

    policy_id: str = DEFAULT_POLICY_ID
    trusted_verifier_ids: tuple[str, ...] = (DEFAULT_VERIFIER_ID,)
    trusted_key_ids: tuple[str, ...] = (DEFAULT_KEY_ID,)
    trusted_key_identity_ids: tuple[str, ...] = (DEFAULT_KEY_IDENTITY_ID,)
    revoked_verifier_ids: tuple[str, ...] = ()
    revoked_key_ids: tuple[str, ...] = ()
    allowed_scopes: tuple[str, ...] = ("live_runner", "provider_boundary")
    max_future_skew_seconds: int = 300


@dataclass(frozen=True, slots=True)
class KeyIdentityRecord:
    """Resolved key identity reference used by local policy tests."""

    identity_id: str = DEFAULT_KEY_IDENTITY_ID
    key_id: str = DEFAULT_KEY_ID
    verifier_id: str = DEFAULT_VERIFIER_ID
    allowed_policy_ids: tuple[str, ...] = (DEFAULT_POLICY_ID,)
    revoked: bool = False


class ApprovalVerifier(Protocol):
    """Minimal approval verifier contract."""

    def verify(self, approval: Any, *, scope: str, gate_prefix: str) -> ApprovalVerificationResult:
        """Verify an approval envelope without reading secrets or external systems."""


class ApprovalPolicyResolver:
    """Local policy resolver skeleton with explicit unknown-id failure."""

    def __init__(self, policies: list[ApprovalVerifierPolicy] | None = None) -> None:
        policy_source = [ApprovalVerifierPolicy()] if policies is None else policies
        self._policies = {policy.policy_id: policy for policy in policy_source}

    def resolve(self, policy_id: str) -> ApprovalVerifierPolicy | None:
        if not isinstance(policy_id, str) or APPROVAL_POLICY_ID_PATTERN.fullmatch(policy_id) is None:
            return None
        return self._policies.get(policy_id)


class KeyIdentityRegistry:
    """Local key identity registry skeleton with revocation support."""

    def __init__(self, identities: list[KeyIdentityRecord] | None = None) -> None:
        identity_source = [KeyIdentityRecord()] if identities is None else identities
        self._identities = {
            identity.identity_id: identity
            for identity in identity_source
        }

    def resolve(self, identity_id: str) -> KeyIdentityRecord | None:
        if (
            not isinstance(identity_id, str)
            or APPROVAL_KEY_IDENTITY_ID_PATTERN.fullmatch(identity_id) is None
        ):
            return None
        return self._identities.get(identity_id)


class ReplayRecordAdapter(Protocol):
    """Durable replay adapter contract for file/DB-backed future stores."""

    def load_records(self) -> list[dict[str, str]]:
        """Load sanitized replay records."""

    def save_records(self, records: list[dict[str, str]]) -> None:
        """Persist sanitized replay records."""


class InMemoryReplayRecordAdapter:
    """Shared in-memory adapter used to simulate durable process restart."""

    def __init__(self, records: list[dict[str, str]] | None = None) -> None:
        self._records = list(records or [])

    def load_records(self) -> list[dict[str, str]]:
        return [dict(record) for record in self._records]

    def save_records(self, records: list[dict[str, str]]) -> None:
        self._records = [dict(record) for record in records]


class UnavailableReplayRecordAdapter:
    """Adapter stub that simulates unavailable file/DB persistence."""

    def load_records(self) -> list[dict[str, str]]:
        raise RuntimeError("replay record adapter is unavailable")

    def save_records(self, records: list[dict[str, str]]) -> None:
        raise RuntimeError("replay record adapter is unavailable")


def merge_verifier_metrics(*metric_sets: dict[str, int]) -> dict[str, int]:
    """Merge verifier metrics without letting zero defaults erase evidence."""
    merged: dict[str, int] = {}
    for metrics in metric_sets:
        for key, value in metrics.items():
            if key not in merged or value:
                merged[key] = value
    return merged


class PersistentReplayStore:
    """Process-local persistent replay store skeleton.

    The store exports hashed replay records so tests can simulate process
    restart without exposing raw authorization values.
    """

    def __init__(self, used_records: list[dict[str, str]] | None = None) -> None:
        self._used_keys: set[tuple[str, str]] = set()
        for record in used_records or []:
            scope = str(record.get("scope", ""))
            nonce_hash = str(record.get("nonce_hash", ""))
            if scope and CONTRACT_HASH_PATTERN.fullmatch(nonce_hash):
                self._used_keys.add((scope, nonce_hash))

    @staticmethod
    def _nonce_hash(*, scope: str, nonce: str) -> str:
        return approval_contract_hash({"scope": scope, "authorization": nonce})

    def is_used(self, *, scope: str, nonce: str) -> bool:
        return (scope, self._nonce_hash(scope=scope, nonce=nonce)) in self._used_keys

    def mark_used(self, *, scope: str, nonce: str) -> None:
        self._used_keys.add((scope, self._nonce_hash(scope=scope, nonce=nonce)))

    def claim(self, *, scope: str, nonce: str) -> bool:
        key = (scope, self._nonce_hash(scope=scope, nonce=nonce))
        if key in self._used_keys:
            return False
        self._used_keys.add(key)
        return True

    def export_records(self) -> list[dict[str, str]]:
        return [
            {"scope": scope, "nonce_hash": nonce_hash}
            for scope, nonce_hash in sorted(self._used_keys)
        ]

    @classmethod
    def from_records(cls, records: list[dict[str, str]]) -> "PersistentReplayStore":
        return cls(records)


class ApprovalReplayGuard(PersistentReplayStore):
    """Backward-compatible name for the replay store skeleton."""


class DurableReplayStore(PersistentReplayStore):
    """Replay store skeleton backed by a sanitized record adapter."""

    def __init__(self, adapter: ReplayRecordAdapter) -> None:
        super().__init__([])
        self._adapter = adapter
        self._loaded = False

    def _load_once(self) -> None:
        if self._loaded:
            return
        records = self._adapter.load_records()
        self._used_keys.clear()
        for record in records:
            scope = str(record.get("scope", ""))
            nonce_hash = str(record.get("nonce_hash", ""))
            if scope and CONTRACT_HASH_PATTERN.fullmatch(nonce_hash):
                self._used_keys.add((scope, nonce_hash))
        self._loaded = True

    def claim(self, *, scope: str, nonce: str) -> bool:
        self._load_once()
        key = (scope, self._nonce_hash(scope=scope, nonce=nonce))
        if key in self._used_keys:
            return False
        self._used_keys.add(key)
        try:
            self._adapter.save_records(self.export_records())
        except Exception:
            self._used_keys.discard(key)
            raise
        return True

    def export_records(self) -> list[dict[str, str]]:
        self._load_once()
        return super().export_records()


_PROCESS_REPLAY_GUARD = ApprovalReplayGuard()


def default_approval_replay_guard() -> PersistentReplayStore:
    """Return the process-local default replay store."""
    return _PROCESS_REPLAY_GUARD


def approval_signature_payload(approval: Any, *, scope: str) -> dict[str, Any]:
    payload = asdict(approval)
    payload.pop("signature_id", None)
    payload.pop("signed_contract_hash", None)
    return {
        "approval_scope": scope,
        "approval_payload": payload,
    }


def approval_contract_hash(payload: dict[str, Any]) -> str:
    """Return an internal canonical hash for approval signature binding."""
    serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def expected_signed_contract_hash(approval: Any, *, scope: str) -> str:
    return approval_contract_hash(approval_signature_payload(approval, scope=scope))


def sign_approval_for_tests(
    approval: Any,
    *,
    scope: str,
    signature_id: str,
    nonce: str,
    verifier_id: str = DEFAULT_VERIFIER_ID,
    key_id: str = DEFAULT_KEY_ID,
    verifier_policy_id: str = DEFAULT_POLICY_ID,
    key_identity_id: str = DEFAULT_KEY_IDENTITY_ID,
) -> Any:
    """Populate deterministic signature fields for fixture approvals."""
    approval.signature_id = signature_id
    approval.nonce = nonce
    if not getattr(approval, "verifier_id", ""):
        approval.verifier_id = verifier_id
    if not getattr(approval, "key_id", ""):
        approval.key_id = key_id
    if not getattr(approval, "verifier_scope", ""):
        approval.verifier_scope = scope
    if not getattr(approval, "verifier_policy_id", ""):
        approval.verifier_policy_id = verifier_policy_id
    if not getattr(approval, "key_identity_id", ""):
        approval.key_identity_id = key_identity_id
    approval.signed_contract_hash = expected_signed_contract_hash(approval, scope=scope)
    return approval


def validate_approval_signature(
    approval: Any,
    *,
    scope: str,
    gate_prefix: str,
) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    signature_id = getattr(approval, "signature_id", "")
    nonce = getattr(approval, "nonce", "")
    signed_contract_hash = getattr(approval, "signed_contract_hash", "")

    if not isinstance(signature_id, str) or not APPROVAL_SIGNATURE_ID_PATTERN.fullmatch(
        signature_id
    ):
        failures.append((f"{gate_prefix}_signature_valid", "approval signature envelope is required."))
    if not isinstance(nonce, str) or not APPROVAL_NONCE_PATTERN.fullmatch(nonce):
        failures.append((f"{gate_prefix}_signature_valid", "approval signature envelope is required."))
    if not isinstance(
        signed_contract_hash, str
    ) or not CONTRACT_HASH_PATTERN.fullmatch(signed_contract_hash):
        failures.append(
            (
                f"{gate_prefix}_signature_valid",
                "approval signature envelope is required.",
            )
        )

    if failures:
        return failures

    if signed_contract_hash != expected_signed_contract_hash(approval, scope=scope):
        failures.append(
            (
                f"{gate_prefix}_signature_valid",
                "approval signature envelope does not match approval payload.",
            )
        )
    return failures


class FakeApprovalVerifier:
    """Deterministic verifier skeleton that never reads secrets or key files."""

    def __init__(self, policy: ApprovalVerifierPolicy | None = None) -> None:
        self.policy = policy or ApprovalVerifierPolicy()

    def verify(self, approval: Any, *, scope: str, gate_prefix: str) -> ApprovalVerificationResult:
        metrics = _zero_verifier_metrics()
        metrics["approval_verifier_fake_count"] = 1
        metrics["approval_verifier_policy_check_count"] = 1

        failures = validate_approval_signature(
            approval,
            scope=scope,
            gate_prefix=gate_prefix,
        )
        if failures:
            metrics["approval_verifier_policy_block_count"] = 1
            return ApprovalVerificationResult(failures=failures, metrics=metrics)

        policy_failures, policy_metrics = validate_approval_verifier_policy(
            approval,
            scope=scope,
            gate_prefix=gate_prefix,
            policy=self.policy,
        )
        metrics = merge_verifier_metrics(metrics, policy_metrics)
        if policy_failures:
            metrics["approval_verifier_policy_block_count"] = 1
        else:
            metrics["approval_verifier_policy_valid_count"] = 1
        return ApprovalVerificationResult(
            failures=policy_failures,
            metrics=metrics,
        )


def _zero_verifier_metrics() -> dict[str, int]:
    return {
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


def _parse_approval_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def validate_approval_verifier_policy(
    approval: Any,
    *,
    scope: str,
    gate_prefix: str,
    policy: ApprovalVerifierPolicy,
) -> tuple[list[tuple[str, str]], dict[str, int]]:
    failures: list[tuple[str, str]] = []
    metrics = _zero_verifier_metrics()
    verifier_id = getattr(approval, "verifier_id", "")
    key_id = getattr(approval, "key_id", "")
    verifier_scope = getattr(approval, "verifier_scope", "")

    if (
        not isinstance(verifier_id, str)
        or APPROVAL_VERIFIER_ID_PATTERN.fullmatch(verifier_id) is None
        or verifier_id not in policy.trusted_verifier_ids
        or verifier_id in policy.revoked_verifier_ids
    ):
        failures.append((f"{gate_prefix}_verifier_trusted", "approval verifier is not trusted."))
        metrics["approval_verifier_identity_block_count"] = 1

    if (
        not isinstance(key_id, str)
        or APPROVAL_KEY_ID_PATTERN.fullmatch(key_id) is None
        or key_id not in policy.trusted_key_ids
        or key_id in policy.revoked_key_ids
    ):
        failures.append((f"{gate_prefix}_key_trusted", "approval signing key is not trusted."))
        metrics["approval_verifier_key_block_count"] = 1

    if (
        not isinstance(verifier_scope, str)
        or APPROVAL_SCOPE_PATTERN.fullmatch(verifier_scope) is None
        or verifier_scope != scope
        or scope not in policy.allowed_scopes
    ):
        failures.append((f"{gate_prefix}_scope_matches", "approval verifier scope is not allowed."))
        metrics["approval_verifier_scope_block_count"] = 1

    approved_at = _parse_approval_timestamp(getattr(approval, "approved_at", ""))
    max_skew = max(0, int(policy.max_future_skew_seconds))
    if approved_at is not None and approved_at > datetime.now(timezone.utc) + timedelta(
        seconds=max_skew
    ):
        failures.append((f"{gate_prefix}_approved_at_skew_valid", "approval timestamp is not valid."))
        metrics["approval_verifier_skew_block_count"] = 1

    return failures, metrics


def enforce_approval_contract_policy(
    approval: Any,
    *,
    scope: str,
    gate_prefix: str,
    policy: ApprovalVerifierPolicy,
) -> ApprovalVerificationResult:
    """Run the local minimum approval contract after an injected verifier returns."""
    metrics = _zero_verifier_metrics()
    metrics["approval_verifier_policy_check_count"] = 1

    failures = validate_approval_signature(
        approval,
        scope=scope,
        gate_prefix=gate_prefix,
    )
    if failures:
        metrics["approval_verifier_policy_block_count"] = 1
        return ApprovalVerificationResult(failures=failures, metrics=metrics)

    policy_failures, policy_metrics = validate_approval_verifier_policy(
        approval,
        scope=scope,
        gate_prefix=gate_prefix,
        policy=policy,
    )
    metrics = merge_verifier_metrics(metrics, policy_metrics)
    if policy_failures:
        metrics["approval_verifier_policy_block_count"] = 1
    else:
        metrics["approval_verifier_policy_valid_count"] = 1
    return ApprovalVerificationResult(failures=policy_failures, metrics=metrics)


def enforce_resolved_approval_contract_policy(
    approval: Any,
    *,
    scope: str,
    gate_prefix: str,
    policy_resolver: ApprovalPolicyResolver,
    key_identity_registry: KeyIdentityRegistry,
) -> ApprovalVerificationResult:
    """Resolve policy/key identity, then enforce the minimum approval contract."""
    metrics = _zero_verifier_metrics()
    metrics["approval_verifier_policy_check_count"] = 1
    metrics["approval_policy_resolver_check_count"] = 1
    metrics["key_identity_registry_check_count"] = 1

    failures = validate_approval_signature(
        approval,
        scope=scope,
        gate_prefix=gate_prefix,
    )
    if failures:
        metrics["approval_verifier_policy_block_count"] = 1
        return ApprovalVerificationResult(failures=failures, metrics=metrics)

    policy_id = getattr(approval, "verifier_policy_id", "")
    key_identity_id = getattr(approval, "key_identity_id", "")
    policy = policy_resolver.resolve(policy_id)
    key_identity = key_identity_registry.resolve(key_identity_id)

    if policy is None:
        failures.append((f"{gate_prefix}_policy_resolved", "approval policy is not trusted."))
        metrics["approval_policy_resolver_block_count"] = 1
        metrics["approval_policy_unknown_block_count"] = 1
    else:
        metrics["approval_policy_resolver_valid_count"] = 1

    if key_identity is None:
        failures.append((f"{gate_prefix}_key_identity_trusted", "approval key identity is not trusted."))
        metrics["key_identity_registry_block_count"] = 1
    elif key_identity.revoked:
        failures.append((f"{gate_prefix}_key_identity_trusted", "approval key identity is revoked."))
        metrics["key_identity_registry_block_count"] = 1
        metrics["key_identity_revoked_block_count"] = 1
    else:
        metrics["key_identity_registry_valid_count"] = 1

    if policy is not None and key_identity is not None and not key_identity.revoked:
        key_matches = (
            key_identity.key_id == getattr(approval, "key_id", "")
            and key_identity.verifier_id == getattr(approval, "verifier_id", "")
            and policy.policy_id in key_identity.allowed_policy_ids
            and key_identity.identity_id in policy.trusted_key_identity_ids
        )
        if not key_matches:
            failures.append((f"{gate_prefix}_policy_key_matches", "approval policy and key identity do not match."))
            metrics["approval_policy_resolver_block_count"] = 1
            metrics["key_identity_registry_block_count"] = 1
            metrics["policy_key_mismatch_block_count"] = 1

    if failures:
        metrics["approval_verifier_policy_block_count"] = 1
        return ApprovalVerificationResult(failures=failures, metrics=metrics)

    policy_failures, policy_metrics = validate_approval_verifier_policy(
        approval,
        scope=scope,
        gate_prefix=gate_prefix,
        policy=policy,
    )
    metrics = merge_verifier_metrics(metrics, policy_metrics)
    if policy_failures:
        metrics["approval_verifier_policy_block_count"] = 1
    else:
        metrics["approval_verifier_policy_valid_count"] = 1
    return ApprovalVerificationResult(failures=policy_failures, metrics=metrics)


def validate_approval_nonce_fresh(
    approval: Any,
    *,
    scope: str,
    gate_prefix: str,
    replay_guard: ApprovalReplayGuard,
) -> list[tuple[str, str]]:
    nonce = getattr(approval, "nonce", "")
    if replay_guard.is_used(scope=scope, nonce=nonce):
        return [(f"{gate_prefix}_replay_fresh", "approval authorization has already been used.")]
    return []


def claim_approval_replay(
    approval: Any,
    *,
    scope: str,
    gate_prefix: str,
    replay_store: PersistentReplayStore,
) -> list[tuple[str, str]]:
    nonce = getattr(approval, "nonce", "")
    try:
        claimed = replay_store.claim(scope=scope, nonce=nonce)
    except Exception:
        return [(f"{gate_prefix}_replay_store_available", "approval replay store is unavailable.")]
    if not claimed:
        return [(f"{gate_prefix}_replay_fresh", "approval authorization has already been used.")]
    return []


def mark_approval_nonce_used(
    approval: Any,
    *,
    scope: str,
    replay_guard: ApprovalReplayGuard,
) -> None:
    replay_guard.mark_used(scope=scope, nonce=getattr(approval, "nonce", ""))

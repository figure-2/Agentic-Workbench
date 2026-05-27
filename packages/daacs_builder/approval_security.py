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
APPROVAL_SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{4,80}$")
CONTRACT_HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")
DEFAULT_VERIFIER_ID = "verifier-local-fake"
DEFAULT_KEY_ID = "key-local-fake"


@dataclass(frozen=True, slots=True)
class ApprovalVerificationResult:
    """Verifier result with sanitized gate failures and metrics."""

    failures: list[tuple[str, str]]
    metrics: dict[str, int]


@dataclass(frozen=True, slots=True)
class ApprovalVerifierPolicy:
    """Static verifier/key policy for local skeleton tests."""

    trusted_verifier_ids: tuple[str, ...] = (DEFAULT_VERIFIER_ID,)
    trusted_key_ids: tuple[str, ...] = (DEFAULT_KEY_ID,)
    revoked_verifier_ids: tuple[str, ...] = ()
    revoked_key_ids: tuple[str, ...] = ()
    allowed_scopes: tuple[str, ...] = ("live_runner", "provider_boundary")
    max_future_skew_seconds: int = 300


class ApprovalVerifier(Protocol):
    """Minimal approval verifier contract."""

    def verify(self, approval: Any, *, scope: str, gate_prefix: str) -> ApprovalVerificationResult:
        """Verify an approval envelope without reading secrets or external systems."""


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

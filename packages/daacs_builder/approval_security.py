"""Approval signature and replay guard skeletons.

This module performs structural approval checks only. It does not read signing
secrets, environment values, key files, or external identity providers.
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import re
from typing import Any


APPROVAL_SIGNATURE_ID_PATTERN = re.compile(r"^sig-[A-Za-z0-9_.-]{8,80}$")
APPROVAL_NONCE_PATTERN = re.compile(r"^nonce-[A-Za-z0-9_.-]{8,80}$")
CONTRACT_HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class ApprovalReplayGuard:
    """In-memory nonce guard for local skeleton tests."""

    def __init__(self, used_nonces: set[tuple[str, str]] | None = None) -> None:
        self._used_nonces: set[tuple[str, str]] = set(used_nonces or set())

    def is_used(self, *, scope: str, nonce: str) -> bool:
        return (scope, nonce) in self._used_nonces

    def mark_used(self, *, scope: str, nonce: str) -> None:
        self._used_nonces.add((scope, nonce))


_PROCESS_REPLAY_GUARD = ApprovalReplayGuard()


def default_approval_replay_guard() -> ApprovalReplayGuard:
    """Return the process-local default replay guard."""
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
) -> Any:
    """Populate deterministic signature fields for fixture approvals."""
    approval.signature_id = signature_id
    approval.nonce = nonce
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


def mark_approval_nonce_used(
    approval: Any,
    *,
    scope: str,
    replay_guard: ApprovalReplayGuard,
) -> None:
    replay_guard.mark_used(scope=scope, nonce=getattr(approval, "nonce", ""))

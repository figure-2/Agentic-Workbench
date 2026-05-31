"""Canonical approval persistence service for live/provider admission.

The service stores only the canonical approval subject snapshot and decision
row required by the durable replay repository. It never stores raw nonce,
signature, signed contract hash, provider payload, prompt body, or runtime
output.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from packages.core.repositories import (
    ApprovalDecisionRecord,
    ApprovalRepository,
    ApprovalSubjectSnapshotRecord,
)

from .live_runner import (
    live_approval_decision_hash,
    live_approval_decision_record_for_request,
    live_approval_subject_snapshot_for_request,
    live_replay_scope_for_request,
)
from .provider_boundary import (
    provider_approval_decision_hash,
    provider_approval_decision_record_for_request,
    provider_approval_subject_snapshot_for_request,
    provider_replay_scope_for_request,
)


AUTHORIZATION_MATERIAL_KEYS = {"signature_id", "signed_contract_hash", "nonce"}
AUTHORIZATION_MATERIAL_VALUE_MARKERS = (
    "signature_id",
    "signed_contract_hash",
    "sig-provider",
    "nonce-provider",
    "sig-live",
    "nonce-live",
)


class CanonicalApprovalPersistenceError(RuntimeError):
    """Raised when canonical approval persistence cannot be trusted."""


@dataclass(frozen=True, slots=True)
class CanonicalApprovalPersistenceResult:
    """Public-safe result for a canonical approval persistence attempt."""

    approval_type: str
    run_id: str
    approval_id: str
    approval_hash: str
    subject_snapshot_id: str
    subject_hash: str
    scope_canonical: str
    status: str
    duplicate: bool = False

    @property
    def metrics(self) -> dict[str, int]:
        return {
            "approval_persistence_service_present_count": 1,
            "approval_persistence_persist_count": 0 if self.duplicate else 1,
            "approval_persistence_duplicate_count": 1 if self.duplicate else 0,
            "approval_persistence_hash_match_count": 1,
        }

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class CanonicalApprovalPersistenceService:
    """Persist provider/live canonical approval rows before replay admission."""

    def __init__(self, approval_repository: ApprovalRepository) -> None:
        self.approval_repository = approval_repository

    def persist_provider_approval(self, request: Any) -> CanonicalApprovalPersistenceResult:
        """Persist the canonical provider approval row for an approved request."""
        scope = provider_replay_scope_for_request(request)
        snapshot = provider_approval_subject_snapshot_for_request(
            request,
            scope_canonical=scope,
        )
        expected = provider_approval_decision_record_for_request(
            request,
            scope_canonical=scope,
        )
        expected_hash = provider_approval_decision_hash(request, scope_canonical=scope)
        return self._persist_canonical_approval(
            expected=expected,
            snapshot=snapshot,
            expected_approval_hash=expected_hash,
        )

    def persist_live_approval(self, request: Any) -> CanonicalApprovalPersistenceResult:
        """Persist the canonical live-runner approval row for an approved request."""
        scope = live_replay_scope_for_request(request)
        snapshot = live_approval_subject_snapshot_for_request(
            request,
            scope_canonical=scope,
        )
        expected = live_approval_decision_record_for_request(
            request,
            scope_canonical=scope,
        )
        expected_hash = live_approval_decision_hash(request, scope_canonical=scope)
        return self._persist_canonical_approval(
            expected=expected,
            snapshot=snapshot,
            expected_approval_hash=expected_hash,
        )

    def _persist_canonical_approval(
        self,
        *,
        expected: ApprovalDecisionRecord,
        snapshot: ApprovalSubjectSnapshotRecord,
        expected_approval_hash: str,
    ) -> CanonicalApprovalPersistenceResult:
        self._assert_expected_rows_match(expected=expected, snapshot=snapshot)
        self._assert_no_authorization_material(snapshot=snapshot, approval=expected)
        if expected.approval_hash != expected_approval_hash:
            raise CanonicalApprovalPersistenceError("canonical approval hash mismatch")

        existing = self.approval_repository.get_approval(expected.approval_id)
        if existing is not None:
            self._assert_existing_matches(expected=expected, snapshot=snapshot, existing=existing)
            return self._result(expected, duplicate=True)

        try:
            saved = self.approval_repository.save_approval(
                approval_id=expected.approval_id,
                snapshot=snapshot,
                decision=expected.decision,
                approved_by_ref=expected.approved_by_ref,
                approver_role=expected.approver_role,
                approved_at=expected.approved_at,
                expires_at=expected.expires_at,
                policy_id_ref=expected.policy_id_ref,
                key_identity_ref=expected.key_identity_ref,
                audit_log_id=expected.audit_log_id,
                lifecycle_class=expected.lifecycle_class,
                created_at=expected.created_at,
            )
        except Exception as exc:
            race_existing = self.approval_repository.get_approval(expected.approval_id)
            if race_existing is not None:
                self._assert_existing_matches(
                    expected=expected,
                    snapshot=snapshot,
                    existing=race_existing,
                )
                return self._result(expected, duplicate=True)
            raise CanonicalApprovalPersistenceError("canonical approval persistence failed") from exc

        if saved.approval_hash != expected.approval_hash:
            raise CanonicalApprovalPersistenceError("persisted approval hash mismatch")
        saved_snapshot = self.approval_repository.get_snapshot(snapshot.subject_snapshot_id)
        if saved_snapshot is None or saved_snapshot.snapshot_hash != snapshot.snapshot_hash:
            raise CanonicalApprovalPersistenceError("persisted approval snapshot mismatch")
        self._assert_no_authorization_material(snapshot=saved_snapshot, approval=saved)
        return self._result(saved, duplicate=False)

    def _assert_existing_matches(
        self,
        *,
        expected: ApprovalDecisionRecord,
        snapshot: ApprovalSubjectSnapshotRecord,
        existing: ApprovalDecisionRecord,
    ) -> None:
        if existing.to_dict() != expected.to_dict():
            raise CanonicalApprovalPersistenceError("existing approval row does not match canonical row")
        existing_snapshot = self.approval_repository.get_snapshot(snapshot.subject_snapshot_id)
        if existing_snapshot is None or existing_snapshot.to_dict() != snapshot.to_dict():
            raise CanonicalApprovalPersistenceError("existing approval snapshot does not match canonical row")
        self._assert_no_authorization_material(snapshot=existing_snapshot, approval=existing)

    def _assert_expected_rows_match(
        self,
        *,
        expected: ApprovalDecisionRecord,
        snapshot: ApprovalSubjectSnapshotRecord,
    ) -> None:
        if expected.subject_snapshot_id != snapshot.subject_snapshot_id:
            raise CanonicalApprovalPersistenceError("approval snapshot id mismatch")
        if expected.subject_hash != snapshot.subject_hash:
            raise CanonicalApprovalPersistenceError("approval subject hash mismatch")
        if expected.scope_canonical != snapshot.scope_canonical:
            raise CanonicalApprovalPersistenceError("approval replay scope mismatch")
        if expected.lifecycle_class != "durable" or snapshot.lifecycle_class != "durable":
            raise CanonicalApprovalPersistenceError("canonical live/provider approvals must be durable")

    def _assert_no_authorization_material(
        self,
        *,
        snapshot: ApprovalSubjectSnapshotRecord,
        approval: ApprovalDecisionRecord,
    ) -> None:
        self._assert_no_authorization_material_value(snapshot.to_dict())
        self._assert_no_authorization_material_value(approval.to_dict())

    def _assert_no_authorization_material_value(self, value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() in AUTHORIZATION_MATERIAL_KEYS:
                    raise CanonicalApprovalPersistenceError(
                        "approval persistence contains authorization material"
                    )
                self._assert_no_authorization_material_value(item)
            return
        if isinstance(value, list | tuple):
            for item in value:
                self._assert_no_authorization_material_value(item)
            return
        if isinstance(value, str):
            lowered = value.lower()
            for marker in AUTHORIZATION_MATERIAL_VALUE_MARKERS:
                if marker in lowered:
                    raise CanonicalApprovalPersistenceError(
                        "approval persistence contains authorization material"
                    )

    def _result(
        self,
        approval: ApprovalDecisionRecord,
        *,
        duplicate: bool,
    ) -> CanonicalApprovalPersistenceResult:
        return CanonicalApprovalPersistenceResult(
            approval_type=approval.approval_type,
            run_id=approval.run_id,
            approval_id=approval.approval_id,
            approval_hash=approval.approval_hash,
            subject_snapshot_id=approval.subject_snapshot_id,
            subject_hash=approval.subject_hash,
            scope_canonical=approval.scope_canonical,
            status="already_persisted" if duplicate else "persisted",
            duplicate=duplicate,
        )

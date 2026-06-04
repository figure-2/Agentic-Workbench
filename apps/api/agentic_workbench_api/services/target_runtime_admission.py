"""API service for disabled DAACS target runtime adapter admission."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_admission import (
    TARGET_RUNTIME_ADAPTER_ADMISSION_VERSION,
    TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION,
    DisabledTargetRuntimeAdapter,
    TargetRuntimeAdapterAdmissionRequest,
    default_target_runtime_adapter_admission_service,
    invoke_disabled_target_runtime_adapter_after_preflight_admission,
)
from packages.daacs_builder.target_runtime_admission_store import (
    TARGET_RUNTIME_ADMISSION_DB_NAME,
    SQLiteTargetRuntimeAdmissionStore,
    target_runtime_adapter_admission_public_read_model,
    target_runtime_adapter_admission_record_from_result,
)
from packages.daacs_builder.runner_provider import safe_public_run_id


@dataclass(slots=True)
class TargetRuntimeAdmissionRepositoryConfig:
    """Server-side target runtime adapter admission evidence store selector."""

    root: str | Path | None = None
    filename: str = TARGET_RUNTIME_ADMISSION_DB_NAME


@dataclass(slots=True)
class TargetRuntimeAdmissionRepositoryProvider:
    """Cached SQLite target runtime admission repository provider."""

    config: TargetRuntimeAdmissionRepositoryConfig | None = None
    _cached_store: SQLiteTargetRuntimeAdmissionStore | None = None

    @property
    def configured(self) -> bool:
        return self.config is not None and self.config.root is not None

    @property
    def backend(self) -> str:
        return "sqlite" if self.configured else "unconfigured"

    def store(self) -> SQLiteTargetRuntimeAdmissionStore:
        if not self.configured or self.config is None or self.config.root is None:
            raise ValueError("target runtime admission repository is not configured")
        if self._cached_store is None:
            self._cached_store = SQLiteTargetRuntimeAdmissionStore(
                root=self.config.root,
                filename=self.config.filename,
            )
        return self._cached_store

    def repository(self):
        return self.store().repository()


def _mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _zero_execution_boundary() -> dict[str, int]:
    return {
        "target_runtime_calls": 0,
        "filesystem_writes": 0,
        "subprocess_calls": 0,
        "network_calls": 0,
        "execution_permission_count": 0,
    }


def _persistence_summary(
    *,
    status: str,
    backend: str,
    persisted_count: int = 0,
    duplicate_count: int = 0,
    blocked_count: int = 0,
) -> dict[str, Any]:
    payload = {
        "projection_version": "target-runtime-adapter-admission-persistence-public-v1",
        "status": status,
        "repository_boundary": {
            "target_runtime_adapter_admission_backend": backend,
            "raw_row_returned": False,
            "root_path_returned": False,
        },
        "counts": {
            "adapter_admission_persisted_count": persisted_count,
            "adapter_admission_duplicate_count": duplicate_count,
            "adapter_admission_persistence_block_count": blocked_count,
            "local_evidence_repository_write_count": persisted_count,
        },
        "execution_boundary": _zero_execution_boundary(),
        "claim_boundary": {
            "target_runtime_outcome": False,
            "generated_artifact_body": False,
            "production_trust_claim": False,
        },
    }
    assert_public_projection_safe(payload)
    return payload


def _blocked_projection(
    *,
    request: TargetRuntimeAdapterAdmissionRequest,
    reason: str,
    backend: str,
) -> dict[str, Any]:
    public_run_id = safe_public_run_id(request.run_id)
    adapter_admission_hash = stable_contract_hash(
        {
            "projection_version": TARGET_RUNTIME_ADAPTER_ADMISSION_VERSION,
            "run_id": public_run_id,
            "mode": request.mode,
            "runner_plan_hash": request.runner_plan_hash,
            "expected_preflight_hash": request.expected_preflight_hash,
            "status": "blocked",
            "reason": reason,
        }
    )
    projection = {
        "projection_version": TARGET_RUNTIME_ADAPTER_ADMISSION_VERSION,
        "run_id": public_run_id,
        "mode": request.mode,
        "status": "blocked",
        "reason": reason,
        "runner_plan_hash": request.runner_plan_hash,
        "expected_preflight_hash": request.expected_preflight_hash,
        "preflight_hash": "",
        "adapter_admission_hash": adapter_admission_hash,
        "checks": [{"name": reason, "passed": False, "reason": reason}],
        "counts": {
            "adapter_admission_count": 0,
            "check_count": 1,
            "failed_check_count": 1,
            "preflight_hash_required_count": 1,
            "preflight_hash_match_count": 0,
            "adapter_reach_count": 0,
            "adapter_disabled_block_count": 0,
            "target_runtime_call_count": 0,
            "filesystem_write_count": 0,
            "subprocess_call_count": 0,
            "network_call_count": 0,
            "execution_permission_count": 0,
        },
        "execution_boundary": _zero_execution_boundary(),
        "claim_boundary": {
            "scope": "disabled target runtime adapter admission evidence only",
            "preflight_required": True,
            "target_runtime_outcome": False,
            "generated_artifact_body": False,
            "hosted_behavior": False,
            "production_trust_claim": False,
        },
        "adapter_admission_persistence": _persistence_summary(
            status="blocked",
            backend=backend,
            blocked_count=1,
        ),
        "adapter_admission_read_model": {
            "projection_version": "target-runtime-adapter-admission-read-model-public-v1",
            "status": "blocked",
            "run_id": public_run_id,
            "counts": {
                "adapter_admission_record_count": 0,
                "adapter_admission_hash_count": 0,
                "preflight_hash_count": 0,
                "adapter_reach_count": 0,
                "adapter_disabled_block_count": 0,
                "execution_permission_count": 0,
                "target_runtime_call_count": 0,
                "filesystem_write_count": 0,
                "subprocess_call_count": 0,
                "network_call_count": 0,
            },
            "adapter_admissions": [],
            "repository_boundary": {
                "target_runtime_adapter_admission_store": "blocked",
                "raw_row_returned": False,
                "root_path_returned": False,
            },
            "execution_boundary": _zero_execution_boundary(),
        },
    }
    assert_public_projection_safe(projection)
    return projection


def run_target_runtime_adapter_admission(
    payload: dict[str, Any],
    *,
    repository_provider: TargetRuntimeAdmissionRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Return a disabled adapter admission projection after preflight hash checks."""
    selected_provider = repository_provider or TargetRuntimeAdmissionRepositoryProvider()
    request = TargetRuntimeAdapterAdmissionRequest(
        run_id=str(payload["run_id"]),
        runner_plan_hash=str(payload["runner_plan_hash"]),
        expected_preflight_hash=str(payload["expected_preflight_hash"]),
        preflight_projection=_mapping(
            payload.get("preflight_projection", {}),
            field_name="preflight_projection",
        ),
        mode=str(payload.get("mode", TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION)),
        metadata={},
    )
    repository = None
    if selected_provider.configured:
        try:
            repository = selected_provider.repository()
        except Exception:
            return _blocked_projection(
                request=request,
                reason="target_runtime_adapter_admission_store_unavailable",
                backend=selected_provider.backend,
            )

    result = invoke_disabled_target_runtime_adapter_after_preflight_admission(
        adapter=DisabledTargetRuntimeAdapter(),
        request=request,
        admission_service=default_target_runtime_adapter_admission_service(),
    ).to_dict()
    result["adapter_admission_persistence"] = _persistence_summary(
        status="skipped",
        backend=selected_provider.backend,
    )
    if repository is None:
        result["adapter_admission_read_model"] = {}
        assert_public_projection_safe(result)
        return result

    if result.get("status") == "blocked" and result.get("reason") == "target_runtime_adapter_disabled":
        try:
            record = target_runtime_adapter_admission_record_from_result(result)
            repository.save(record)
            persistence = _persistence_summary(
                status="persisted",
                backend=selected_provider.backend,
                persisted_count=1,
            )
        except ValueError as exc:
            if "duplicate" not in str(exc).lower():
                return _blocked_projection(
                    request=request,
                    reason="target_runtime_adapter_admission_persistence_failed",
                    backend=selected_provider.backend,
                )
            persistence = _persistence_summary(
                status="duplicate",
                backend=selected_provider.backend,
                duplicate_count=1,
            )
        except Exception:
            return _blocked_projection(
                request=request,
                reason="target_runtime_adapter_admission_persistence_failed",
                backend=selected_provider.backend,
            )
        result["adapter_admission_persistence"] = persistence
        result["adapter_admission_read_model"] = target_runtime_adapter_admission_public_read_model(
            repository,
            run_id=request.run_id,
        )
    else:
        result["adapter_admission_read_model"] = target_runtime_adapter_admission_public_read_model(
            repository,
            run_id=request.run_id,
        )

    assert_public_projection_safe(result)
    return result


def read_target_runtime_adapter_admissions(
    run_id: str,
    *,
    repository_provider: TargetRuntimeAdmissionRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Read sanitized disabled target runtime adapter admission evidence."""
    selected_provider = repository_provider or TargetRuntimeAdmissionRepositoryProvider()
    if not selected_provider.configured:
        return _blocked_projection(
            request=TargetRuntimeAdapterAdmissionRequest(
                run_id=run_id,
                runner_plan_hash="",
                expected_preflight_hash="",
                preflight_projection={},
            ),
            reason="target_runtime_adapter_admission_store_unconfigured",
            backend=selected_provider.backend,
        )["adapter_admission_read_model"]
    try:
        read_model = target_runtime_adapter_admission_public_read_model(
            selected_provider.repository(),
            run_id=run_id,
        )
    except Exception:
        return _blocked_projection(
            request=TargetRuntimeAdapterAdmissionRequest(
                run_id=run_id,
                runner_plan_hash="",
                expected_preflight_hash="",
                preflight_projection={},
            ),
            reason="target_runtime_adapter_admission_store_unavailable",
            backend=selected_provider.backend,
        )["adapter_admission_read_model"]
    assert_public_projection_safe(read_model)
    return read_model

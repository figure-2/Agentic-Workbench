"""API service for disabled DAACS target runtime output manifest contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.runner_provider import safe_public_run_id
from packages.daacs_builder.target_runtime_output_manifest import (
    TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
    TARGET_RUNTIME_OUTPUT_MANIFEST_VERSION,
    TargetRuntimeOutputManifestRequest,
    build_disabled_target_runtime_output_manifest,
)
from packages.daacs_builder.target_runtime_output_manifest_store import (
    TARGET_RUNTIME_OUTPUT_MANIFEST_DB_NAME,
    SQLiteTargetRuntimeOutputManifestStore,
    target_runtime_output_manifest_public_read_model,
    target_runtime_output_manifest_record_from_result,
)


@dataclass(slots=True)
class TargetRuntimeOutputManifestRepositoryConfig:
    """Server-side output manifest evidence store selector."""

    root: str | Path | None = None
    filename: str = TARGET_RUNTIME_OUTPUT_MANIFEST_DB_NAME


@dataclass(slots=True)
class TargetRuntimeOutputManifestRepositoryProvider:
    """Cached SQLite output manifest repository provider."""

    config: TargetRuntimeOutputManifestRepositoryConfig | None = None
    _cached_store: SQLiteTargetRuntimeOutputManifestStore | None = None

    @property
    def configured(self) -> bool:
        return self.config is not None and self.config.root is not None

    @property
    def backend(self) -> str:
        return "sqlite" if self.configured else "unconfigured"

    def store(self) -> SQLiteTargetRuntimeOutputManifestStore:
        if not self.configured or self.config is None or self.config.root is None:
            raise ValueError("target runtime output manifest repository is not configured")
        if self._cached_store is None:
            self._cached_store = SQLiteTargetRuntimeOutputManifestStore(
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


def _list_of_mappings(value: Any, *, field_name: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    output: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} items must be mappings")
        output.append(item)
    return output


def _zero_execution_boundary() -> dict[str, int]:
    return {
        "target_runtime_calls": 0,
        "filesystem_writes": 0,
        "subprocess_calls": 0,
        "network_calls": 0,
        "generated_artifact_body_write_count": 0,
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
        "projection_version": "target-runtime-output-manifest-persistence-public-v1",
        "status": status,
        "repository_boundary": {
            "target_runtime_output_manifest_backend": backend,
            "raw_row_returned": False,
            "root_path_returned": False,
        },
        "counts": {
            "output_manifest_persisted_count": persisted_count,
            "output_manifest_duplicate_count": duplicate_count,
            "output_manifest_persistence_block_count": blocked_count,
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
    request: TargetRuntimeOutputManifestRequest,
    reason: str,
    backend: str,
) -> dict[str, Any]:
    public_run_id = safe_public_run_id(request.run_id)
    read_model_hash = stable_contract_hash(
        request.adapter_admission_read_model
        if isinstance(request.adapter_admission_read_model, dict)
        else {}
    )
    output_manifest_hash = stable_contract_hash(
        {
            "projection_version": TARGET_RUNTIME_OUTPUT_MANIFEST_VERSION,
            "run_id": public_run_id,
            "mode": request.mode,
            "runner_plan_hash": request.runner_plan_hash,
            "adapter_admission_hash": request.adapter_admission_hash,
            "adapter_admission_read_model_hash": read_model_hash,
            "status": "blocked",
            "reason": reason,
        }
    )
    projection = {
        "projection_version": TARGET_RUNTIME_OUTPUT_MANIFEST_VERSION,
        "run_id": public_run_id,
        "mode": request.mode,
        "status": "blocked",
        "reason": reason,
        "runner_plan_hash": request.runner_plan_hash,
        "adapter_admission_hash": request.adapter_admission_hash,
        "adapter_admission_read_model_hash": read_model_hash,
        "output_manifest_hash": output_manifest_hash,
        "output_groups": [],
        "checks": [{"name": reason, "passed": False, "reason": reason}],
        "counts": {
            "output_manifest_count": 0,
            "comparison_variant_count": 1,
            "check_count": 1,
            "failed_check_count": 1,
            "adapter_admission_read_model_count": 0,
            "adapter_admission_record_count": 0,
            "adapter_admission_hash_count": 0,
            "adapter_admission_hash_match_count": 0,
            "output_group_count": 0,
            "output_group_hash_count": 0,
            "generated_artifact_body_write_count": 0,
            "target_runtime_call_count": 0,
            "filesystem_write_count": 0,
            "subprocess_call_count": 0,
            "network_call_count": 0,
            "execution_permission_count": 0,
        },
        "execution_boundary": _zero_execution_boundary(),
        "claim_boundary": {
            "scope": "disabled target runtime output manifest evidence only",
            "adapter_admission_read_model_required": True,
            "target_runtime_outcome": False,
            "generated_artifact_body": False,
            "generated_file_content": False,
            "hosted_behavior": False,
            "production_trust_claim": False,
        },
        "output_manifest_persistence": _persistence_summary(
            status="blocked",
            backend=backend,
            blocked_count=1,
        ),
        "output_manifest_read_model": {
            "projection_version": "target-runtime-output-manifest-read-model-public-v1",
            "status": "blocked",
            "run_id": public_run_id,
            "counts": {
                "output_manifest_record_count": 0,
                "output_manifest_hash_count": 0,
                "adapter_admission_hash_count": 0,
                "adapter_admission_read_model_hash_count": 0,
                "output_group_count": 0,
                "output_group_hash_count": 0,
                "generated_artifact_body_write_count": 0,
                "execution_permission_count": 0,
                "target_runtime_call_count": 0,
                "filesystem_write_count": 0,
                "subprocess_call_count": 0,
                "network_call_count": 0,
            },
            "output_manifests": [],
            "repository_boundary": {
                "target_runtime_output_manifest_store": "blocked",
                "raw_row_returned": False,
                "root_path_returned": False,
            },
            "execution_boundary": _zero_execution_boundary(),
        },
    }
    assert_public_projection_safe(projection)
    return projection


def run_target_runtime_output_manifest(
    payload: dict[str, Any],
    *,
    repository_provider: TargetRuntimeOutputManifestRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Return the disabled output manifest projection."""
    selected_provider = repository_provider or TargetRuntimeOutputManifestRepositoryProvider()
    request = TargetRuntimeOutputManifestRequest(
        run_id=str(payload["run_id"]),
        runner_plan_hash=str(payload["runner_plan_hash"]),
        adapter_admission_hash=str(payload["adapter_admission_hash"]),
        adapter_admission_read_model=_mapping(
            payload.get("adapter_admission_read_model", {}),
            field_name="adapter_admission_read_model",
        ),
        output_groups=_list_of_mappings(
            payload.get("output_groups", []),
            field_name="output_groups",
        ),
        mode=str(
            payload.get("mode", TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED)
        ),
        metadata={},
    )
    repository = None
    if selected_provider.configured:
        try:
            repository = selected_provider.repository()
        except Exception:
            return _blocked_projection(
                request=request,
                reason="target_runtime_output_manifest_store_unavailable",
                backend=selected_provider.backend,
            )

    result = build_disabled_target_runtime_output_manifest(request=request).to_dict()
    result["output_manifest_persistence"] = _persistence_summary(
        status="skipped",
        backend=selected_provider.backend,
    )
    if repository is None:
        result["output_manifest_read_model"] = {}
        assert_public_projection_safe(result)
        return result

    if (
        result.get("status") == "blocked"
        and result.get("reason") == "target_runtime_output_manifest_execution_closed"
    ):
        try:
            record = target_runtime_output_manifest_record_from_result(result)
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
                    reason="target_runtime_output_manifest_persistence_failed",
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
                reason="target_runtime_output_manifest_persistence_failed",
                backend=selected_provider.backend,
            )
        result["output_manifest_persistence"] = persistence
        result["output_manifest_read_model"] = target_runtime_output_manifest_public_read_model(
            repository,
            run_id=request.run_id,
        )
    else:
        result["output_manifest_read_model"] = (
            target_runtime_output_manifest_public_read_model(
                repository,
                run_id=request.run_id,
            )
        )

    assert_public_projection_safe(result)
    return result


def read_target_runtime_output_manifests(
    run_id: str,
    *,
    repository_provider: TargetRuntimeOutputManifestRepositoryProvider | None = None,
) -> dict[str, Any]:
    """Read sanitized disabled target runtime output manifest evidence."""
    selected_provider = repository_provider or TargetRuntimeOutputManifestRepositoryProvider()
    if not selected_provider.configured:
        return _blocked_projection(
            request=TargetRuntimeOutputManifestRequest(
                run_id=run_id,
                runner_plan_hash="",
                adapter_admission_hash="",
                adapter_admission_read_model={},
            ),
            reason="target_runtime_output_manifest_store_unconfigured",
            backend=selected_provider.backend,
        )["output_manifest_read_model"]
    try:
        read_model = target_runtime_output_manifest_public_read_model(
            selected_provider.repository(),
            run_id=run_id,
        )
    except Exception:
        return _blocked_projection(
            request=TargetRuntimeOutputManifestRequest(
                run_id=run_id,
                runner_plan_hash="",
                adapter_admission_hash="",
                adapter_admission_read_model={},
            ),
            reason="target_runtime_output_manifest_store_unavailable",
            backend=selected_provider.backend,
        )["output_manifest_read_model"]
    assert_public_projection_safe(read_model)
    return read_model


__all__ = [
    "TargetRuntimeOutputManifestRepositoryConfig",
    "TargetRuntimeOutputManifestRepositoryProvider",
    "read_target_runtime_output_manifests",
    "run_target_runtime_output_manifest",
]

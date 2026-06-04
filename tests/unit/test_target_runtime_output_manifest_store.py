import builtins
import json
import os
import sqlite3
import urllib.request

import pytest

from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_admission import (
    DisabledTargetRuntimeAdapter,
    TargetRuntimeAdapterAdmissionRequest,
    TargetRuntimeAdapterAdmissionService,
    invoke_disabled_target_runtime_adapter_after_preflight_admission,
)
from packages.daacs_builder.target_runtime_admission_store import (
    InMemoryTargetRuntimeAdapterAdmissionRepository,
    target_runtime_adapter_admission_public_read_model,
    target_runtime_adapter_admission_record_from_result,
)
from packages.daacs_builder.target_runtime_output_manifest import (
    TargetRuntimeOutputManifestRequest,
    build_disabled_target_runtime_output_manifest,
)
from packages.daacs_builder.target_runtime_output_manifest_store import (
    TARGET_RUNTIME_OUTPUT_MANIFEST_DB_NAME,
    TARGET_RUNTIME_OUTPUT_MANIFEST_EXPECTED_COLUMNS,
    SQLiteTargetRuntimeOutputManifestStore,
    target_runtime_output_manifest_public_read_model,
    target_runtime_output_manifest_public_read_model_from_sqlite,
    target_runtime_output_manifest_record_from_result,
)
from packages.daacs_builder.target_runtime_sandbox import (
    TargetRuntimePreflightRequest,
    TargetRuntimePreflightService,
    ready_target_runtime_command_policy,
    ready_target_runtime_rollback_policy,
    ready_target_runtime_sandbox_policy,
    ready_target_runtime_workspace_intent,
)


RUN_ID = "run-daacs-runtime-04"


def _runner_plan_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "target runtime output manifest persistence",
            "runner_plan": "hash-only",
        }
    )


def _preflight(run_id: str = RUN_ID) -> dict:
    request = TargetRuntimePreflightRequest(
        run_id=run_id,
        runner_plan_hash=_runner_plan_hash(),
        sandbox_policy=ready_target_runtime_sandbox_policy(),
        workspace_intent=ready_target_runtime_workspace_intent(run_id),
        command_policy=ready_target_runtime_command_policy(),
        rollback_policy=ready_target_runtime_rollback_policy(),
        metadata={
            "raw_prompt": "DAACS_OUTPUT_MANIFEST_STORE_RAW_PROMPT_SENTINEL",
            "runtime_payload": "DAACS_OUTPUT_MANIFEST_STORE_RUNTIME_SENTINEL",
        },
    )
    return TargetRuntimePreflightService().preflight(request).to_dict()


def _admission_result(run_id: str = RUN_ID) -> dict:
    preflight = _preflight(run_id)
    request = TargetRuntimeAdapterAdmissionRequest(
        run_id=run_id,
        runner_plan_hash=_runner_plan_hash(),
        expected_preflight_hash=preflight["preflight_hash"],
        preflight_projection=preflight,
        metadata={
            "raw_file_body": "DAACS_OUTPUT_MANIFEST_STORE_RAW_FILE_SENTINEL",
        },
    )
    return invoke_disabled_target_runtime_adapter_after_preflight_admission(
        adapter=DisabledTargetRuntimeAdapter(),
        request=request,
        admission_service=TargetRuntimeAdapterAdmissionService(),
    ).to_dict()


def _adapter_read_model(run_id: str = RUN_ID) -> tuple[str, dict]:
    repository = InMemoryTargetRuntimeAdapterAdmissionRepository()
    admission_record = target_runtime_adapter_admission_record_from_result(
        _admission_result(run_id)
    )
    repository.save(admission_record)
    read_model = target_runtime_adapter_admission_public_read_model(
        repository,
        run_id=run_id,
    )
    return admission_record.adapter_admission_hash, read_model


def _manifest_result(run_id: str = RUN_ID) -> dict:
    adapter_admission_hash, read_model = _adapter_read_model(run_id)
    request = TargetRuntimeOutputManifestRequest(
        run_id=run_id,
        runner_plan_hash=_runner_plan_hash(),
        adapter_admission_hash=adapter_admission_hash,
        adapter_admission_read_model=read_model,
        output_groups=[
            {"label": "backend", "expected_artifact_kind": "backend"},
            {"label": "frontend", "expected_artifact_kind": "frontend"},
            {
                "label": "verification_report",
                "expected_artifact_kind": "verification_report",
            },
        ],
        metadata={
            "raw_file_body": "DAACS_OUTPUT_MANIFEST_STORE_REQUEST_RAW_SENTINEL",
            "generated_artifact_body": (
                "DAACS_OUTPUT_MANIFEST_STORE_GENERATED_BODY_SENTINEL"
            ),
        },
    )
    return build_disabled_target_runtime_output_manifest(request=request).to_dict()


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def test_target_runtime_output_manifest_record_is_hash_status_count_only():
    record = target_runtime_output_manifest_record_from_result(_manifest_result())
    serialized = _serialized(record.to_dict())

    assert record.status == "blocked"
    assert record.reason == "target_runtime_output_manifest_execution_closed"
    assert record.output_manifest_count == 1
    assert record.adapter_admission_read_model_count == 1
    assert record.adapter_admission_hash_match_count == 1
    assert record.output_group_count == 3
    assert record.output_group_hash_count == 3
    assert record.generated_artifact_body_write_count == 0
    assert record.execution_permission_count == 0
    assert record.target_runtime_call_count == 0
    assert record.filesystem_write_count == 0
    assert record.subprocess_call_count == 0
    assert record.network_call_count == 0
    for forbidden in (
        "DAACS_OUTPUT_MANIFEST_STORE_RAW_PROMPT_SENTINEL",
        "DAACS_OUTPUT_MANIFEST_STORE_RUNTIME_SENTINEL",
        "DAACS_OUTPUT_MANIFEST_STORE_RAW_FILE_SENTINEL",
        "DAACS_OUTPUT_MANIFEST_STORE_REQUEST_RAW_SENTINEL",
        "DAACS_OUTPUT_MANIFEST_STORE_GENERATED_BODY_SENTINEL",
        "raw_prompt",
        "runtime_payload",
        "raw_file_body",
        "provider_payload",
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(record.to_dict())


def test_target_runtime_output_manifest_sqlite_persists_only_hash_status_count_rows(
    tmp_path,
):
    store = SQLiteTargetRuntimeOutputManifestStore(tmp_path / "manifest-store")
    repository = store.repository()
    record = target_runtime_output_manifest_record_from_result(_manifest_result())

    repository.save(record)

    with sqlite3.connect(store.path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM target_runtime_output_manifests"
        ).fetchall()
    row = dict(rows[0])
    serialized_row = _serialized(row)
    read_model = target_runtime_output_manifest_public_read_model(
        repository,
        run_id=RUN_ID,
    )

    assert len(rows) == 1
    assert set(row) == TARGET_RUNTIME_OUTPUT_MANIFEST_EXPECTED_COLUMNS[
        "target_runtime_output_manifests"
    ]
    assert row["output_manifest_hash"] == record.output_manifest_hash
    assert row["adapter_admission_hash"] == record.adapter_admission_hash
    assert "DAACS_OUTPUT_MANIFEST_STORE_RAW_PROMPT_SENTINEL" not in serialized_row
    assert "DAACS_OUTPUT_MANIFEST_STORE_RUNTIME_SENTINEL" not in serialized_row
    assert "DAACS_OUTPUT_MANIFEST_STORE_RAW_FILE_SENTINEL" not in serialized_row
    assert "DAACS_OUTPUT_MANIFEST_STORE_REQUEST_RAW_SENTINEL" not in serialized_row
    assert "DAACS_OUTPUT_MANIFEST_STORE_GENERATED_BODY_SENTINEL" not in serialized_row
    assert "raw_prompt" not in serialized_row
    assert "runtime_payload" not in serialized_row
    assert "raw_file_body" not in serialized_row
    assert read_model["status"] == "available"
    assert read_model["counts"]["output_manifest_record_count"] == 1
    assert read_model["counts"]["output_manifest_hash_count"] == 1
    assert read_model["counts"]["output_group_count"] == 3
    assert read_model["counts"]["output_group_hash_count"] == 3
    assert read_model["counts"]["generated_artifact_body_write_count"] == 0
    assert read_model["counts"]["target_runtime_call_count"] == 0
    assert set(read_model["output_manifests"][0]) == {
        "status",
        "reason",
        "runner_plan_hash",
        "adapter_admission_hash",
        "adapter_admission_read_model_hash",
        "output_manifest_hash",
        "output_groups_hash",
        "check_count",
        "failed_check_count",
        "adapter_admission_read_model_count",
        "adapter_admission_hash_match_count",
        "output_group_count",
        "output_group_hash_count",
        "generated_artifact_body_write_count",
        "execution_permission_count",
        "target_runtime_call_count",
        "filesystem_write_count",
        "subprocess_call_count",
        "network_call_count",
    }
    assert_public_projection_safe(read_model)


def test_target_runtime_output_manifest_sqlite_duplicate_rolls_back_partial_row(
    tmp_path,
):
    store = SQLiteTargetRuntimeOutputManifestStore(tmp_path / "manifest-store")
    repository = store.repository()
    record = target_runtime_output_manifest_record_from_result(_manifest_result())

    repository.save(record)

    with pytest.raises(ValueError, match="duplicate"):
        repository.save(record)

    read_model = target_runtime_output_manifest_public_read_model(
        repository,
        run_id=RUN_ID,
    )
    assert read_model["counts"]["output_manifest_record_count"] == 1
    assert read_model["counts"]["output_manifest_hash_count"] == 1


def test_target_runtime_output_manifest_read_model_blocks_bad_sqlite_stores(tmp_path):
    unavailable_root = tmp_path / "not-a-directory"
    unavailable_root.write_text("not a directory", encoding="utf-8")
    corrupted_root = tmp_path / "corrupted"
    corrupted_root.mkdir()
    (corrupted_root / TARGET_RUNTIME_OUTPUT_MANIFEST_DB_NAME).write_text(
        "not sqlite",
        encoding="utf-8",
    )
    wrong_schema_root = tmp_path / "wrong-schema"
    wrong_schema_root.mkdir()
    with sqlite3.connect(wrong_schema_root / TARGET_RUNTIME_OUTPUT_MANIFEST_DB_NAME) as conn:
        conn.execute("CREATE TABLE target_runtime_output_manifests (run_id TEXT)")
        conn.commit()

    unavailable = target_runtime_output_manifest_public_read_model_from_sqlite(
        unavailable_root,
        run_id=RUN_ID,
    )
    corrupted = target_runtime_output_manifest_public_read_model_from_sqlite(
        corrupted_root,
        run_id=RUN_ID,
    )
    wrong_schema = target_runtime_output_manifest_public_read_model_from_sqlite(
        wrong_schema_root,
        run_id=RUN_ID,
    )

    assert unavailable["status"] == "blocked"
    assert corrupted["status"] == "blocked"
    assert wrong_schema["status"] == "blocked"
    assert unavailable["counts"]["output_manifest_record_count"] == 0
    assert corrupted["counts"]["output_manifest_record_count"] == 0
    assert wrong_schema["counts"]["output_manifest_record_count"] == 0


def test_target_runtime_output_manifest_store_does_not_read_env_or_call_network(
    monkeypatch,
    tmp_path,
):
    def blocked_getenv(*args, **kwargs):
        raise AssertionError("env value read attempted")

    def blocked_urlopen(*args, **kwargs):
        raise AssertionError("network urlopen attempted")

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".", 1)[0] in {"upstage", "openai", "requests", "httpx"}:
            raise AssertionError(f"runtime/provider SDK import attempted: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(os, "getenv", blocked_getenv)
    monkeypatch.setattr(urllib.request, "urlopen", blocked_urlopen)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    store = SQLiteTargetRuntimeOutputManifestStore(tmp_path / "manifest-store")
    repository = store.repository()
    record = target_runtime_output_manifest_record_from_result(_manifest_result())
    repository.save(record)
    read_model = target_runtime_output_manifest_public_read_model(
        repository,
        run_id=RUN_ID,
    )

    assert read_model["status"] == "available"
    assert read_model["execution_boundary"]["target_runtime_calls"] == 0
    assert read_model["execution_boundary"]["network_calls"] == 0

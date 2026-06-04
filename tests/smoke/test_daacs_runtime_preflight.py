import importlib.util
import json
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.agentic_workbench_api.main import create_app
from apps.api.agentic_workbench_api.services.target_runtime_admission import (
    TargetRuntimeAdmissionRepositoryConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_output_manifest import (
    TargetRuntimeOutputManifestRepositoryConfig,
)
from packages.core.live_open_policy import LIVE_OPEN_REQUIRED_CONTROLS
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.target_runtime_admission import (
    TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION,
)
from packages.daacs_builder.target_runtime_output_manifest import (
    TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
)
from packages.daacs_builder.target_runtime_sandbox import (
    TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT,
)


DEMO_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "demo-service-flow"
    / "run_local_demo.py"
)


def _load_demo_module():
    spec = importlib.util.spec_from_file_location("aw_daacs_runtime_00_demo", DEMO_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _runner_plan_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "daacs runtime smoke",
            "runner_plan": "hash-only",
        }
    )


def _payload(run_id: str = "run-daacs-runtime-api") -> dict:
    readiness = {field_name: True for field_name in LIVE_OPEN_REQUIRED_CONTROLS}
    workspace_root = f"runs/{run_id}/workspace"
    return {
        "run_id": run_id,
        "runner_plan_hash": _runner_plan_hash(),
        "mode": TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT,
        "sandbox_policy": {
            **readiness,
            "timeout_seconds": 60,
            "max_planned_files": 20,
            "max_subprocess_calls": 0,
            "max_package_installs": 0,
            "max_server_starts": 0,
            "max_network_calls": 0,
            "max_target_runtime_calls": 0,
        },
        "workspace_intent": {
            "workspace_root": workspace_root,
            "allowed_write_paths": [
                f"{workspace_root}/backend",
                f"{workspace_root}/frontend",
                f"{workspace_root}/reports",
            ],
            "requested_write_paths": [
                f"{workspace_root}/backend/main.py",
                f"{workspace_root}/frontend/App.tsx",
                f"{workspace_root}/reports/verification.json",
            ],
            "expected_output_paths": [
                f"{workspace_root}/backend",
                f"{workspace_root}/frontend",
                f"{workspace_root}/reports",
            ],
        },
        "command_policy": {
            "requested_operations": [
                "render backend files",
                "render frontend files",
                "render report",
            ],
            "allowed_operation_labels": [
                "render_backend",
                "render_frontend",
                "render_report",
            ],
        },
        "rollback_policy": {
            "rollback_plan_id": "rollback-local-target-runtime-preflight",
            "abort_criteria": [
                "any path boundary finding",
                "any non-zero side-effect counter",
            ],
            "cleanup_steps": [
                "discard run-scoped workspace",
                "keep sanitized audit projection only",
            ],
        },
        "raw_file_body": "DAACS_RUNTIME_RAW_FILE_BODY_SENTINEL",
    }


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def test_daacs_runtime_preflight_api_is_no_call_and_public_safe():
    client = TestClient(create_app())

    response = client.post("/api/v1/daacs/runtime/preflight", json=_payload())

    assert response.status_code == 200
    data = response.json()["data"]
    serialized = _serialized(data)

    assert data["projection_version"] == "target-runtime-preflight-public-v1"
    assert data["status"] == "blocked"
    assert data["reason"] == "target_runtime_execution_closed"
    assert data["mode"] == TARGET_RUNTIME_MODE_DISABLED_PREFLIGHT
    assert data["counts"]["denied_path_count"] == 0
    assert data["counts"]["blocked_operation_count"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["filesystem_writes"] == 0
    assert data["execution_boundary"]["subprocess_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["execution_permission_count"] == 0
    assert "DAACS_RUNTIME_RAW_FILE_BODY_SENTINEL" not in serialized
    assert "raw_file_body" not in serialized
    assert_public_projection_safe(data)


def test_daacs_runtime_adapter_admission_api_requires_preflight_hash_and_stays_disabled():
    client = TestClient(create_app())
    preflight_response = client.post("/api/v1/daacs/runtime/preflight", json=_payload())
    preflight_response.raise_for_status()
    preflight = preflight_response.json()["data"]

    response = client.post(
        "/api/v1/daacs/runtime/adapter/admission",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "expected_preflight_hash": preflight["preflight_hash"],
            "mode": TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION,
            "preflight_projection": preflight,
            "raw_runtime_payload": "DAACS_RUNTIME_ADAPTER_RAW_SENTINEL",
        },
    )
    mismatch_response = client.post(
        "/api/v1/daacs/runtime/adapter/admission",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "expected_preflight_hash": "a" * 64,
            "mode": TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION,
            "preflight_projection": preflight,
        },
    )

    assert response.status_code == 200
    assert mismatch_response.status_code == 200
    data = response.json()["data"]
    mismatch = mismatch_response.json()["data"]
    serialized = _serialized(data)

    assert data["projection_version"] == "target-runtime-adapter-admission-public-v1"
    assert data["status"] == "blocked"
    assert data["reason"] == "target_runtime_adapter_disabled"
    assert data["counts"]["preflight_hash_match_count"] == 1
    assert data["counts"]["adapter_reach_count"] == 1
    assert data["counts"]["adapter_disabled_block_count"] == 1
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["filesystem_writes"] == 0
    assert data["execution_boundary"]["subprocess_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["execution_permission_count"] == 0
    assert mismatch["status"] == "blocked"
    assert mismatch["reason"] == "preflight_hash_mismatch"
    assert mismatch["counts"]["adapter_reach_count"] == 0
    assert "DAACS_RUNTIME_ADAPTER_RAW_SENTINEL" not in serialized
    assert "raw_runtime_payload" not in serialized
    assert_public_projection_safe(data)


def test_daacs_runtime_adapter_admission_api_persists_and_reads_hash_only_evidence(
    tmp_path,
):
    client = TestClient(
        create_app(
            target_runtime_admission_repository_config=(
                TargetRuntimeAdmissionRepositoryConfig(
                    root=tmp_path / "target-runtime-admission-evidence"
                )
            )
        )
    )
    preflight_response = client.post(
        "/api/v1/daacs/runtime/preflight",
        json=_payload("run-daacs-runtime-admission-store-api"),
    )
    preflight_response.raise_for_status()
    preflight = preflight_response.json()["data"]

    response = client.post(
        "/api/v1/daacs/runtime/adapter/admission",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "expected_preflight_hash": preflight["preflight_hash"],
            "mode": TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION,
            "preflight_projection": preflight,
            "raw_runtime_payload": "DAACS_RUNTIME_ADAPTER_STORE_RAW_SENTINEL",
        },
    )
    read_response = client.get(
        f"/api/v1/daacs/runtime/adapter/admissions/{preflight['run_id']}"
    )

    assert response.status_code == 200
    assert read_response.status_code == 200
    data = response.json()["data"]
    read_model = read_response.json()["data"]
    serialized = _serialized({"admission": data, "read_model": read_model})

    assert data["adapter_admission_persistence"]["status"] == "persisted"
    assert data["adapter_admission_persistence"]["counts"][
        "adapter_admission_persisted_count"
    ] == 1
    assert data["adapter_admission_read_model"]["status"] == "available"
    assert read_model["projection_version"] == (
        "target-runtime-adapter-admission-read-model-public-v1"
    )
    assert read_model["status"] == "available"
    assert read_model["counts"]["adapter_admission_record_count"] == 1
    assert read_model["counts"]["adapter_admission_hash_count"] == 1
    assert read_model["counts"]["adapter_reach_count"] == 1
    assert read_model["counts"]["adapter_disabled_block_count"] == 1
    assert read_model["counts"]["target_runtime_call_count"] == 0
    assert read_model["repository_boundary"]["raw_row_returned"] is False
    assert read_model["repository_boundary"]["root_path_returned"] is False
    assert "DAACS_RUNTIME_ADAPTER_STORE_RAW_SENTINEL" not in serialized
    assert "raw_runtime_payload" not in serialized
    assert_public_projection_safe(data)
    assert_public_projection_safe(read_model)


def test_daacs_runtime_output_manifest_api_requires_adapter_read_model_and_stays_no_call(
    tmp_path,
):
    client = TestClient(
        create_app(
            target_runtime_admission_repository_config=(
                TargetRuntimeAdmissionRepositoryConfig(
                    root=tmp_path / "target-runtime-admission-evidence"
                )
            ),
            target_runtime_output_manifest_repository_config=(
                TargetRuntimeOutputManifestRepositoryConfig(
                    root=tmp_path / "target-runtime-output-manifest-evidence"
                )
            )
        )
    )
    preflight_response = client.post(
        "/api/v1/daacs/runtime/preflight",
        json=_payload("run-daacs-runtime-output-manifest-api"),
    )
    preflight_response.raise_for_status()
    preflight = preflight_response.json()["data"]
    admission_response = client.post(
        "/api/v1/daacs/runtime/adapter/admission",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "expected_preflight_hash": preflight["preflight_hash"],
            "mode": TARGET_RUNTIME_MODE_DISABLED_ADAPTER_ADMISSION,
            "preflight_projection": preflight,
        },
    )
    read_response = client.get(
        f"/api/v1/daacs/runtime/adapter/admissions/{preflight['run_id']}"
    )
    admission = admission_response.json()["data"]
    read_model = read_response.json()["data"]

    response = client.post(
        "/api/v1/daacs/runtime/output-manifest",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "adapter_admission_hash": admission["adapter_admission_hash"],
            "adapter_admission_read_model": read_model,
            "mode": TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
            "raw_file_body": "DAACS_RUNTIME_OUTPUT_MANIFEST_RAW_SENTINEL",
        },
    )
    mismatch_response = client.post(
        "/api/v1/daacs/runtime/output-manifest",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "adapter_admission_hash": "a" * 64,
            "adapter_admission_read_model": read_model,
            "mode": TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
        },
    )
    output_manifest_read_response = client.get(
        f"/api/v1/daacs/runtime/output-manifests/{preflight['run_id']}"
    )

    assert response.status_code == 200
    assert mismatch_response.status_code == 200
    assert output_manifest_read_response.status_code == 200
    data = response.json()["data"]
    mismatch = mismatch_response.json()["data"]
    output_manifest_read_model = output_manifest_read_response.json()["data"]
    serialized = _serialized(
        {"output_manifest": data, "read_model": output_manifest_read_model}
    )

    assert data["projection_version"] == "target-runtime-output-manifest-public-v1"
    assert data["status"] == "blocked"
    assert data["reason"] == "target_runtime_output_manifest_execution_closed"
    assert data["counts"]["adapter_admission_read_model_count"] == 1
    assert data["counts"]["adapter_admission_hash_match_count"] == 1
    assert data["counts"]["output_group_count"] == 3
    assert data["counts"]["output_group_hash_count"] == 3
    assert data["output_manifest_persistence"]["status"] == "persisted"
    assert data["output_manifest_persistence"]["counts"][
        "output_manifest_persisted_count"
    ] == 1
    assert data["output_manifest_read_model"]["status"] == "available"
    assert data["output_manifest_read_model"]["counts"][
        "output_manifest_record_count"
    ] == 1
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["filesystem_writes"] == 0
    assert data["execution_boundary"]["subprocess_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["generated_artifact_body_write_count"] == 0
    assert output_manifest_read_model["projection_version"] == (
        "target-runtime-output-manifest-read-model-public-v1"
    )
    assert output_manifest_read_model["status"] == "available"
    assert output_manifest_read_model["counts"]["output_manifest_record_count"] == 1
    assert output_manifest_read_model["counts"]["output_manifest_hash_count"] == 1
    assert output_manifest_read_model["counts"]["output_group_count"] == 3
    assert output_manifest_read_model["counts"][
        "generated_artifact_body_write_count"
    ] == 0
    assert output_manifest_read_model["counts"]["target_runtime_call_count"] == 0
    assert output_manifest_read_model["repository_boundary"]["raw_row_returned"] is False
    assert output_manifest_read_model["repository_boundary"]["root_path_returned"] is False
    assert mismatch["status"] == "blocked"
    assert mismatch["reason"] == "adapter_admission_hash_mismatch"
    assert mismatch["counts"]["adapter_admission_hash_match_count"] == 0
    assert "DAACS_RUNTIME_OUTPUT_MANIFEST_RAW_SENTINEL" not in serialized
    assert "raw_file_body" not in serialized
    assert_public_projection_safe(data)
    assert_public_projection_safe(output_manifest_read_model)


def test_local_service_demo_compares_dry_run_and_target_runtime_preflight(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "daacs-runtime-store",
        include_daacs_runtime_output_manifest=True,
    )
    serialized = _serialized(summary)
    comparison = summary["daacs_runtime_comparison"]
    preflight = summary["daacs_runtime_preflight"]
    adapter_admission = summary["daacs_runtime_adapter_admission"]
    output_manifest = summary["daacs_runtime_output_manifest"]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert comparison["comparison_variant_count"] == 4
    assert comparison["dry_run_stage_coverage"] == "7/7"
    assert comparison["target_runtime_preflight_status"] == "blocked"
    assert comparison["target_runtime_calls"] == 0
    assert comparison["filesystem_writes"] == 0
    assert comparison["subprocess_calls"] == 0
    assert comparison["network_calls"] == 0
    assert comparison["adapter_admission_status"] == "blocked"
    assert comparison["adapter_admission_reason"] == "target_runtime_adapter_disabled"
    assert comparison["adapter_preflight_hash_match_count"] == 1
    assert comparison["adapter_reach_count"] == 1
    assert comparison["adapter_disabled_block_count"] == 1
    assert comparison["adapter_persisted_count"] == 1
    assert comparison["adapter_read_model_record_count"] == 1
    assert comparison["output_manifest_status"] == "blocked"
    assert comparison["output_manifest_reason"] == (
        "target_runtime_output_manifest_execution_closed"
    )
    assert comparison["output_manifest_hash_count"] == 1
    assert comparison["output_manifest_group_count"] == 3
    assert comparison["output_manifest_prerequisite_count"] == 1
    assert comparison["output_manifest_persisted_count"] == 1
    assert comparison["output_manifest_read_model_record_count"] == 1
    assert comparison["output_manifest_read_model_hash_count"] == 1
    assert comparison["output_manifest_generated_body_writes"] == 0
    assert comparison["output_manifest_target_runtime_calls"] == 0
    assert comparison["output_manifest_filesystem_writes"] == 0
    assert comparison["output_manifest_subprocess_calls"] == 0
    assert comparison["output_manifest_network_calls"] == 0
    assert comparison["adapter_target_runtime_calls"] == 0
    assert comparison["adapter_filesystem_writes"] == 0
    assert comparison["adapter_subprocess_calls"] == 0
    assert comparison["adapter_network_calls"] == 0
    assert comparison["raw_exposure_findings"] == 0
    assert comparison["public_claim_drift_findings"] == 0
    assert preflight["status"] == "blocked"
    assert preflight["reason"] == "target_runtime_execution_closed"
    assert preflight["counts"]["denied_path_count"] == 0
    assert preflight["counts"]["blocked_operation_count"] == 0
    assert adapter_admission["status"] == "blocked"
    assert adapter_admission["reason"] == "target_runtime_adapter_disabled"
    assert adapter_admission["counts"]["preflight_hash_match_count"] == 1
    assert adapter_admission["counts"]["adapter_reach_count"] == 1
    assert adapter_admission["counts"]["target_runtime_call_count"] == 0
    assert adapter_admission["persistence"]["status"] == "persisted"
    assert adapter_admission["read_model"]["status"] == "available"
    assert adapter_admission["read_model"]["counts"][
        "adapter_admission_record_count"
    ] == 1
    assert output_manifest["status"] == "blocked"
    assert output_manifest["reason"] == "target_runtime_output_manifest_execution_closed"
    assert output_manifest["counts"]["adapter_admission_read_model_count"] == 1
    assert output_manifest["counts"]["adapter_admission_hash_match_count"] == 1
    assert output_manifest["counts"]["output_group_count"] == 3
    assert output_manifest["counts"]["generated_artifact_body_write_count"] == 0
    assert output_manifest["persistence"]["status"] == "persisted"
    assert output_manifest["read_model"]["status"] == "available"
    assert output_manifest["read_model"]["counts"]["output_manifest_record_count"] == 1
    assert output_manifest["read_model"]["counts"]["output_manifest_hash_count"] == 1
    assert checks["daacs_runtime_preflight_projection"] is True
    assert checks["daacs_runtime_preflight_blocked"] is True
    assert checks["daacs_runtime_preflight_execution_zero"] is True
    assert checks["daacs_runtime_preflight_boundary_clean"] is True
    assert checks["daacs_runtime_adapter_admission_projection"] is True
    assert checks["daacs_runtime_adapter_admission_blocked"] is True
    assert checks["daacs_runtime_adapter_admission_hash_match"] is True
    assert checks["daacs_runtime_adapter_disabled_reached"] is True
    assert checks["daacs_runtime_adapter_execution_zero"] is True
    assert checks["daacs_runtime_adapter_admission_persisted"] is True
    assert checks["daacs_runtime_adapter_admission_read_model"] is True
    assert checks["daacs_runtime_adapter_read_model_execution_zero"] is True
    assert checks["daacs_runtime_output_manifest_projection"] is True
    assert checks["daacs_runtime_output_manifest_blocked"] is True
    assert checks["daacs_runtime_output_manifest_prerequisite"] is True
    assert checks["daacs_runtime_output_manifest_groups"] is True
    assert checks["daacs_runtime_output_manifest_execution_zero"] is True
    assert checks["daacs_runtime_output_manifest_persisted"] is True
    assert checks["daacs_runtime_output_manifest_read_model"] is True
    assert checks["daacs_runtime_output_manifest_read_model_execution_zero"] is True

    for forbidden in (
        "raw_prompt",
        "raw_log",
        "raw_file_body",
        "Build a small task collaboration app",
        "runtime_payload",
        "provider_payload",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(summary)

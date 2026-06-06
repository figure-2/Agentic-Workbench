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
from apps.api.agentic_workbench_api.services.target_runtime_fixture_materialization import (
    TargetRuntimeFixtureMaterializationConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_restricted_workspace_generation import (
    TargetRuntimeRestrictedWorkspaceGenerationConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_generated_artifact_verification import (
    TargetRuntimeGeneratedArtifactVerificationConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_generated_workspace_static_validation import (
    TargetRuntimeGeneratedWorkspaceStaticValidationConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_buildable_fixture_manifest import (
    TargetRuntimeBuildableFixtureManifestConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_local_build_attempt import (
    TargetRuntimeLocalBuildAttemptConfig,
)
from apps.api.agentic_workbench_api.services.target_runtime_local_preview_attempt import (
    TargetRuntimeLocalPreviewAttemptConfig,
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
from packages.daacs_builder.target_runtime_generated_artifact_bundle import (
    TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED,
    TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
)
from packages.daacs_builder.target_runtime_fixture_materialization import (
    TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE,
    TARGET_RUNTIME_FIXTURE_MATERIALIZATION_VERSION,
)
from packages.daacs_builder.target_runtime_restricted_workspace_generation import (
    TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE,
    TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION,
)
from packages.daacs_builder.target_runtime_generated_artifact_verification import (
    TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE,
    TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION,
)
from packages.daacs_builder.target_runtime_generated_workspace_static_validation import (
    TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE,
    TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION,
)
from packages.daacs_builder.target_runtime_buildable_fixture_manifest import (
    TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE,
    TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION,
)
from packages.daacs_builder.target_runtime_local_build_preflight import (
    TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE,
    TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION,
)
from packages.daacs_builder.target_runtime_local_build_attempt import (
    TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE,
    TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION,
)
from packages.daacs_builder.target_runtime_local_preview_attempt import (
    BROWSER_RUNTIME_PREFLIGHT_VERSION,
    BrowserRuntimePreflightResult,
    TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE,
    TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_VERSION,
)
from packages.daacs_builder.target_runtime_browser_setup_attempt import (
    TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE,
    TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_VERSION,
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
    serialized = _serialized({"admission": data, "mismatch": mismatch})

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


def test_daacs_runtime_generated_artifact_bundle_api_requires_output_manifest_read_model(
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
        json=_payload("run-daacs-runtime-generated-bundle-api"),
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
    adapter_read_response = client.get(
        f"/api/v1/daacs/runtime/adapter/admissions/{preflight['run_id']}"
    )
    admission = admission_response.json()["data"]
    adapter_read_model = adapter_read_response.json()["data"]
    manifest_response = client.post(
        "/api/v1/daacs/runtime/output-manifest",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "adapter_admission_hash": admission["adapter_admission_hash"],
            "adapter_admission_read_model": adapter_read_model,
            "mode": TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
        },
    )
    output_manifest = manifest_response.json()["data"]
    output_manifest_read_response = client.get(
        f"/api/v1/daacs/runtime/output-manifests/{preflight['run_id']}"
    )
    output_manifest_read_model = output_manifest_read_response.json()["data"]

    response = client.post(
        "/api/v1/daacs/runtime/generated-artifact-bundle",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "output_manifest_hash": output_manifest["output_manifest_hash"],
            "output_manifest_read_model": output_manifest_read_model,
            "mode": TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED,
            "raw_file_body": "DAACS_RUNTIME_GENERATED_BUNDLE_RAW_SENTINEL",
        },
    )
    mismatch_response = client.post(
        "/api/v1/daacs/runtime/generated-artifact-bundle",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "output_manifest_hash": "a" * 64,
            "output_manifest_read_model": output_manifest_read_model,
            "mode": TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED,
        },
    )

    assert response.status_code == 200
    assert mismatch_response.status_code == 200
    data = response.json()["data"]
    mismatch = mismatch_response.json()["data"]
    serialized = _serialized(data)

    assert data["projection_version"] == TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION
    assert data["status"] == "blocked"
    assert data["reason"] == (
        "target_runtime_generated_artifact_bundle_execution_closed"
    )
    assert data["counts"]["output_manifest_read_model_count"] == 1
    assert data["counts"]["output_manifest_hash_match_count"] == 1
    assert data["counts"]["output_manifest_record_count"] == 1
    assert data["counts"]["artifact_unit_count"] == 3
    assert data["counts"]["artifact_unit_hash_count"] == 3
    assert data["counts"]["generated_artifact_body_write_count"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["filesystem_writes"] == 0
    assert data["execution_boundary"]["subprocess_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["generated_artifact_body_write_count"] == 0
    assert mismatch["status"] == "blocked"
    assert mismatch["reason"] == "output_manifest_hash_mismatch"
    assert mismatch["counts"]["output_manifest_hash_match_count"] == 0
    assert "DAACS_RUNTIME_GENERATED_BUNDLE_RAW_SENTINEL" not in serialized
    assert "raw_file_body" not in serialized
    assert_public_projection_safe(data)


def test_daacs_runtime_fixture_materialization_api_writes_sanitized_workspace_records(
    tmp_path,
):
    workspace_root = tmp_path / "target-runtime-fixture-workspace"
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
            ),
            target_runtime_fixture_materialization_config=(
                TargetRuntimeFixtureMaterializationConfig(root=workspace_root)
            ),
        )
    )
    preflight_response = client.post(
        "/api/v1/daacs/runtime/preflight",
        json=_payload("run-daacs-runtime-fixture-materialization-api"),
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
    adapter_read_response = client.get(
        f"/api/v1/daacs/runtime/adapter/admissions/{preflight['run_id']}"
    )
    admission = admission_response.json()["data"]
    adapter_read_model = adapter_read_response.json()["data"]
    manifest_response = client.post(
        "/api/v1/daacs/runtime/output-manifest",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "adapter_admission_hash": admission["adapter_admission_hash"],
            "adapter_admission_read_model": adapter_read_model,
            "mode": TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
        },
    )
    output_manifest = manifest_response.json()["data"]
    output_manifest_read_response = client.get(
        f"/api/v1/daacs/runtime/output-manifests/{preflight['run_id']}"
    )
    output_manifest_read_model = output_manifest_read_response.json()["data"]
    bundle_response = client.post(
        "/api/v1/daacs/runtime/generated-artifact-bundle",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "output_manifest_hash": output_manifest["output_manifest_hash"],
            "output_manifest_read_model": output_manifest_read_model,
            "mode": TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED,
        },
    )
    bundle = bundle_response.json()["data"]

    response = client.post(
        "/api/v1/daacs/runtime/fixture-materialization",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "generated_artifact_bundle_hash": bundle[
                "generated_artifact_bundle_hash"
            ],
            "generated_artifact_bundle_projection": bundle,
            "mode": TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE,
            "raw_file_body": "DAACS_RUNTIME_FIXTURE_MATERIALIZATION_RAW_SENTINEL",
        },
    )
    mismatch_response = client.post(
        "/api/v1/daacs/runtime/fixture-materialization",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "generated_artifact_bundle_hash": "a" * 64,
            "generated_artifact_bundle_projection": bundle,
            "mode": TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE,
        },
    )

    assert response.status_code == 200
    assert mismatch_response.status_code == 200
    data = response.json()["data"]
    mismatch = mismatch_response.json()["data"]
    serialized = _serialized(data)

    assert data["projection_version"] == TARGET_RUNTIME_FIXTURE_MATERIALIZATION_VERSION
    assert data["status"] == "passed"
    assert data["reason"] == "target_runtime_fixture_artifacts_materialized"
    assert data["mode"] == TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE
    assert data["counts"]["generated_artifact_bundle_hash_match_count"] == 1
    assert data["counts"]["fixture_artifact_record_count"] == 3
    assert data["counts"]["fixture_artifact_content_hash_count"] == 3
    assert data["execution_boundary"]["fixture_workspace_file_write_count"] == 3
    assert data["execution_boundary"]["filesystem_writes_outside_workspace"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["subprocess_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["repository_boundary"]["root_path_returned"] is False
    assert data["repository_boundary"]["artifact_content_returned"] is False
    assert mismatch["status"] == "blocked"
    assert mismatch["reason"] == "generated_artifact_bundle_hash_mismatch"
    assert mismatch["counts"]["fixture_workspace_file_write_count"] == 0

    for record in data["artifact_records"]:
        assert record["body_included"] is False
        assert record["root_path_returned"] is False
        assert (workspace_root / record["workspace_relative_path"]).exists()
    assert "DAACS_RUNTIME_FIXTURE_MATERIALIZATION_RAW_SENTINEL" not in serialized
    assert "raw_file_body" not in serialized
    assert str(tmp_path) not in serialized
    assert_public_projection_safe(data)


def test_daacs_runtime_restricted_workspace_generation_api_writes_app_skeleton(
    tmp_path,
):
    fixture_workspace_root = tmp_path / "target-runtime-fixture-workspace"
    restricted_workspace_root = tmp_path / "target-runtime-restricted-workspace"
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
            ),
            target_runtime_fixture_materialization_config=(
                TargetRuntimeFixtureMaterializationConfig(root=fixture_workspace_root)
            ),
            target_runtime_restricted_workspace_generation_config=(
                TargetRuntimeRestrictedWorkspaceGenerationConfig(
                    root=restricted_workspace_root
                )
            ),
            target_runtime_generated_artifact_verification_config=(
                TargetRuntimeGeneratedArtifactVerificationConfig(
                    root=restricted_workspace_root
                )
            ),
            target_runtime_generated_workspace_static_validation_config=(
                TargetRuntimeGeneratedWorkspaceStaticValidationConfig(
                    root=restricted_workspace_root
                )
            ),
            target_runtime_buildable_fixture_manifest_config=(
                TargetRuntimeBuildableFixtureManifestConfig(
                    root=restricted_workspace_root
                )
            ),
        )
    )
    preflight_response = client.post(
        "/api/v1/daacs/runtime/preflight",
        json=_payload("run-daacs-runtime-mvp-01-api"),
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
    admission = admission_response.json()["data"]
    adapter_read_response = client.get(
        f"/api/v1/daacs/runtime/adapter/admissions/{preflight['run_id']}"
    )
    adapter_read_model = adapter_read_response.json()["data"]
    manifest_response = client.post(
        "/api/v1/daacs/runtime/output-manifest",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "adapter_admission_hash": admission["adapter_admission_hash"],
            "adapter_admission_read_model": adapter_read_model,
            "mode": TARGET_RUNTIME_OUTPUT_MANIFEST_MODE_DISABLED,
        },
    )
    output_manifest = manifest_response.json()["data"]
    output_manifest_read_response = client.get(
        f"/api/v1/daacs/runtime/output-manifests/{preflight['run_id']}"
    )
    output_manifest_read_model = output_manifest_read_response.json()["data"]
    bundle_response = client.post(
        "/api/v1/daacs/runtime/generated-artifact-bundle",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "output_manifest_hash": output_manifest["output_manifest_hash"],
            "output_manifest_read_model": output_manifest_read_model,
            "mode": TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_MODE_DISABLED,
        },
    )
    bundle = bundle_response.json()["data"]
    fixture_response = client.post(
        "/api/v1/daacs/runtime/fixture-materialization",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "generated_artifact_bundle_hash": bundle[
                "generated_artifact_bundle_hash"
            ],
            "generated_artifact_bundle_projection": bundle,
            "mode": TARGET_RUNTIME_FIXTURE_MATERIALIZATION_MODE,
        },
    )
    fixture_response.raise_for_status()

    response = client.post(
        "/api/v1/daacs/runtime/restricted-workspace-generation",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "implementation_brief_hash": stable_contract_hash(
                {"artifact": "implementation_brief", "run_id": preflight["run_id"]}
            ),
            "generated_artifact_bundle_hash": bundle[
                "generated_artifact_bundle_hash"
            ],
            "generated_artifact_bundle_projection": bundle,
            "mode": TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE,
            "raw_file_body": "DAACS_RUNTIME_MVP_01_RAW_SENTINEL",
        },
    )
    mismatch_response = client.post(
        "/api/v1/daacs/runtime/restricted-workspace-generation",
        json={
            "run_id": preflight["run_id"],
            "runner_plan_hash": preflight["runner_plan_hash"],
            "implementation_brief_hash": stable_contract_hash(
                {"artifact": "implementation_brief", "run_id": preflight["run_id"]}
            ),
            "generated_artifact_bundle_hash": "a" * 64,
            "generated_artifact_bundle_projection": bundle,
            "mode": TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE,
        },
    )

    assert response.status_code == 200
    assert mismatch_response.status_code == 200
    data = response.json()["data"]
    mismatch = mismatch_response.json()["data"]
    verification_response = client.post(
        "/api/v1/daacs/runtime/generated-artifact-verification",
        json={
            "run_id": preflight["run_id"],
            "generated_workspace_hash": data["generated_workspace_hash"],
            "generated_workspace_projection": data,
            "mode": TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE,
        },
    )
    verification_response.raise_for_status()
    generated_verification = verification_response.json()["data"]
    static_validation_response = client.post(
        "/api/v1/daacs/runtime/generated-workspace-static-validation",
        json={
            "run_id": preflight["run_id"],
            "generated_artifact_verification_hash": generated_verification[
                "generated_artifact_verification_hash"
            ],
            "generated_artifact_verification_projection": generated_verification,
            "mode": TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE,
        },
    )
    static_validation_response.raise_for_status()
    static_validation = static_validation_response.json()["data"]
    buildable_manifest_response = client.post(
        "/api/v1/daacs/runtime/buildable-fixture-manifest",
        json={
            "run_id": preflight["run_id"],
            "generated_workspace_static_validation_hash": static_validation[
                "generated_workspace_static_validation_hash"
            ],
            "generated_workspace_static_validation_projection": static_validation,
            "mode": TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_MODE,
        },
    )
    buildable_manifest_response.raise_for_status()
    buildable_manifest = buildable_manifest_response.json()["data"]
    serialized = _serialized(data)

    assert data["projection_version"] == (
        TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION
    )
    assert data["status"] == "passed"
    assert data["reason"] == "target_runtime_restricted_workspace_generated"
    assert data["mode"] == TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE
    assert data["counts"]["generated_artifact_bundle_hash_match_count"] == 1
    assert data["counts"]["generated_workspace_file_record_count"] == 9
    assert data["counts"]["generated_workspace_file_hash_count"] == 9
    assert data["counts"]["restricted_workspace_file_write_count"] == 9
    assert data["counts"]["file_content_public_return_count"] == 0
    assert data["counts"]["local_root_path_return_count"] == 0
    assert data["execution_boundary"]["restricted_workspace_file_write_count"] == 9
    assert data["execution_boundary"]["filesystem_writes_outside_workspace"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["sdk_imports"] == 0
    assert data["execution_boundary"]["env_key_value_reads"] == 0
    assert data["execution_boundary"]["subprocess_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["package_install_calls"] == 0
    assert data["execution_boundary"]["build_calls"] == 0
    assert data["execution_boundary"]["server_start_calls"] == 0
    assert data["repository_boundary"]["root_path_returned"] is False
    assert data["repository_boundary"]["file_content_returned"] is False
    assert mismatch["status"] == "blocked"
    assert mismatch["reason"] == "generated_artifact_bundle_hash_mismatch"
    assert mismatch["counts"]["restricted_workspace_file_write_count"] == 0
    assert generated_verification["status"] == "passed"
    assert generated_verification["counts"]["file_check_record_count"] == 9
    assert static_validation["projection_version"] == (
        TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION
    )
    assert static_validation["status"] == "passed"
    assert static_validation["counts"]["static_file_checked_count"] == 9
    assert static_validation["counts"]["required_script_present_count"] == 4
    assert static_validation["counts"]["app_component_marker_present_count"] == 13
    assert static_validation["counts"]["api_marker_present_count"] == 8
    assert (
        static_validation["counts"]["verification_boundary_marker_present_count"]
        == 4
    )
    assert static_validation["execution_boundary"]["package_install_calls"] == 0
    assert static_validation["execution_boundary"]["build_calls"] == 0
    assert static_validation["execution_boundary"]["server_start_calls"] == 0
    assert static_validation["repository_boundary"]["file_content_returned"] is False
    assert buildable_manifest["projection_version"] == (
        TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION
    )
    assert buildable_manifest["status"] == "passed"
    assert buildable_manifest["build_ready_candidate"] is True
    assert buildable_manifest["counts"]["required_file_read_count"] == 5
    assert buildable_manifest["counts"]["required_script_present_count"] == 4
    assert buildable_manifest["counts"]["total_dependency_label_count"] >= 4
    assert buildable_manifest["counts"]["placeholder_dependency_value_count"] == 0
    assert buildable_manifest["execution_boundary"]["package_install_calls"] == 0
    assert buildable_manifest["execution_boundary"]["build_calls"] == 0
    assert buildable_manifest["execution_boundary"]["server_start_calls"] == 0
    assert buildable_manifest["repository_boundary"]["file_content_returned"] is False

    for record in data["file_records"]:
        assert record["content_included"] is False
        assert record["root_path_returned"] is False
        assert (restricted_workspace_root / record["workspace_relative_path"]).exists()
    assert "DAACS_RUNTIME_MVP_01_RAW_SENTINEL" not in serialized
    assert "raw_file_body" not in serialized
    assert str(tmp_path) not in serialized
    assert_public_projection_safe(data)
    assert_public_projection_safe(generated_verification)
    assert_public_projection_safe(static_validation)


def test_local_service_demo_compares_dry_run_and_target_runtime_preflight(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "daacs-runtime-store",
        include_daacs_runtime_fixture_materialization=True,
    )
    serialized = _serialized(summary)
    comparison = summary["daacs_runtime_comparison"]
    preflight = summary["daacs_runtime_preflight"]
    adapter_admission = summary["daacs_runtime_adapter_admission"]
    output_manifest = summary["daacs_runtime_output_manifest"]
    generated_bundle = summary["daacs_runtime_generated_artifact_bundle"]
    fixture_materialization = summary["daacs_runtime_fixture_materialization"]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert comparison["comparison_variant_count"] == 6
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
    assert comparison["generated_artifact_bundle_status"] == "blocked"
    assert comparison["generated_artifact_bundle_reason"] == (
        "target_runtime_generated_artifact_bundle_execution_closed"
    )
    assert comparison["generated_artifact_bundle_hash_count"] == 1
    assert comparison["generated_artifact_bundle_unit_count"] == 3
    assert comparison["generated_artifact_bundle_prerequisite_count"] == 1
    assert comparison["generated_artifact_bundle_body_writes"] == 0
    assert comparison["generated_artifact_bundle_target_runtime_calls"] == 0
    assert comparison["generated_artifact_bundle_filesystem_writes"] == 0
    assert comparison["generated_artifact_bundle_subprocess_calls"] == 0
    assert comparison["generated_artifact_bundle_network_calls"] == 0
    assert comparison["fixture_materialization_status"] == "passed"
    assert comparison["fixture_materialization_reason"] == (
        "target_runtime_fixture_artifacts_materialized"
    )
    assert comparison["fixture_materialization_record_count"] == 3
    assert comparison["fixture_materialization_content_hash_count"] == 3
    assert comparison["fixture_materialization_workspace_writes"] == 3
    assert comparison["fixture_materialization_outside_workspace_writes"] == 0
    assert comparison["fixture_materialization_body_public_returns"] == 0
    assert comparison["fixture_materialization_target_runtime_calls"] == 0
    assert comparison["fixture_materialization_provider_calls"] == 0
    assert comparison["fixture_materialization_subprocess_calls"] == 0
    assert comparison["fixture_materialization_network_calls"] == 0
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
    assert generated_bundle["status"] == "blocked"
    assert generated_bundle["reason"] == (
        "target_runtime_generated_artifact_bundle_execution_closed"
    )
    assert generated_bundle["counts"]["output_manifest_read_model_count"] == 1
    assert generated_bundle["counts"]["output_manifest_hash_match_count"] == 1
    assert generated_bundle["counts"]["artifact_unit_count"] == 3
    assert generated_bundle["counts"]["generated_artifact_body_write_count"] == 0
    assert fixture_materialization["projection_version"] == (
        TARGET_RUNTIME_FIXTURE_MATERIALIZATION_VERSION
    )
    assert fixture_materialization["status"] == "passed"
    assert fixture_materialization["reason"] == (
        "target_runtime_fixture_artifacts_materialized"
    )
    assert fixture_materialization["counts"]["generated_artifact_bundle_hash_match_count"] == 1
    assert fixture_materialization["counts"]["fixture_artifact_record_count"] == 3
    assert fixture_materialization["counts"]["fixture_artifact_content_hash_count"] == 3
    assert fixture_materialization["execution_boundary"][
        "fixture_workspace_file_write_count"
    ] == 3
    assert fixture_materialization["execution_boundary"][
        "filesystem_writes_outside_workspace"
    ] == 0
    assert fixture_materialization["execution_boundary"]["target_runtime_calls"] == 0
    assert fixture_materialization["repository_boundary"]["root_path_returned"] is False
    assert fixture_materialization["repository_boundary"][
        "artifact_content_returned"
    ] is False
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
    assert checks["daacs_runtime_generated_artifact_bundle_projection"] is True
    assert checks["daacs_runtime_generated_artifact_bundle_blocked"] is True
    assert checks["daacs_runtime_generated_artifact_bundle_prerequisite"] is True
    assert checks["daacs_runtime_generated_artifact_bundle_units"] is True
    assert checks["daacs_runtime_generated_artifact_bundle_execution_zero"] is True
    assert checks["daacs_runtime_fixture_materialization_projection"] is True
    assert checks["daacs_runtime_fixture_materialization_passed"] is True
    assert checks["daacs_runtime_fixture_materialization_prerequisite"] is True
    assert checks["daacs_runtime_fixture_materialization_records"] is True
    assert checks["daacs_runtime_fixture_materialization_workspace_writes"] is True
    assert checks["daacs_runtime_fixture_materialization_live_zero"] is True

    for forbidden in (
        "raw_prompt",
        "raw_log",
        "raw_file_body",
        "Build a small task collaboration app",
        "runtime_payload",
        "provider_payload",
        str(tmp_path),
        "target-runtime-fixture-workspace",
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(summary)


def test_local_service_demo_retries_preview_when_browser_setup_makes_runtime_available():
    module = _load_demo_module()

    should_retry = module._should_retry_local_preview_after_browser_setup(
        local_preview_attempt={
            "status": "environment_blocked",
            "reason": "playwright_python_package_missing",
        },
        browser_setup_attempt={
            "status": "passed",
            "post_setup_browser_runtime_preflight": {"available": True},
        },
        allow_local_preview_attempt=True,
    )
    blocked_without_opt_in = module._should_retry_local_preview_after_browser_setup(
        local_preview_attempt={"status": "environment_blocked"},
        browser_setup_attempt={
            "status": "passed",
            "post_setup_browser_runtime_preflight": {"available": True},
        },
        allow_local_preview_attempt=False,
    )
    blocked_when_already_passed = module._should_retry_local_preview_after_browser_setup(
        local_preview_attempt={"status": "passed"},
        browser_setup_attempt={
            "status": "passed",
            "post_setup_browser_runtime_preflight": {"available": True},
        },
        allow_local_preview_attempt=True,
    )

    assert should_retry is True
    assert blocked_without_opt_in is False
    assert blocked_when_already_passed is False


def test_local_service_demo_generates_restricted_workspace_skeleton(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "daacs-runtime-mvp-01-store",
        include_daacs_runtime_restricted_workspace_generation=True,
    )
    serialized = _serialized(summary)
    comparison = summary["daacs_runtime_comparison"]
    restricted_workspace = summary[
        "daacs_runtime_restricted_workspace_generation"
    ]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert comparison["comparison_variant_count"] == 7
    assert comparison["restricted_workspace_generation_status"] == "passed"
    assert comparison["restricted_workspace_generation_reason"] == (
        "target_runtime_restricted_workspace_generated"
    )
    assert comparison["restricted_workspace_file_record_count"] == 9
    assert comparison["restricted_workspace_file_hash_count"] == 9
    assert comparison["restricted_workspace_file_byte_count"] > 0
    assert comparison["restricted_workspace_codegen_input_hash_count"] == 1
    assert comparison["restricted_workspace_codegen_document_hash_count"] == 3
    assert comparison["restricted_workspace_planning_hash_present_count"] == 1
    assert comparison["restricted_workspace_prd_hash_present_count"] == 1
    assert comparison["restricted_workspace_solar_draft_hash_present_count"] == 0
    assert comparison["restricted_workspace_writes"] == 9
    assert comparison["restricted_workspace_outside_writes"] == 0
    assert comparison["restricted_workspace_file_content_public_returns"] == 0
    assert comparison["restricted_workspace_target_runtime_calls"] == 0
    assert comparison["restricted_workspace_provider_calls"] == 0
    assert comparison["restricted_workspace_sdk_imports"] == 0
    assert comparison["restricted_workspace_env_value_reads"] == 0
    assert comparison["restricted_workspace_subprocess_calls"] == 0
    assert comparison["restricted_workspace_network_calls"] == 0
    assert comparison["restricted_workspace_package_install_calls"] == 0
    assert comparison["restricted_workspace_build_calls"] == 0
    assert comparison["restricted_workspace_server_start_calls"] == 0
    assert restricted_workspace["projection_version"] == (
        TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION
    )
    assert restricted_workspace["status"] == "passed"
    assert restricted_workspace["counts"]["generated_workspace_file_record_count"] == 9
    assert restricted_workspace["counts"]["generated_workspace_file_hash_count"] == 9
    assert restricted_workspace["counts"]["codegen_input_hash_count"] == 1
    assert restricted_workspace["counts"]["codegen_input_document_hash_count"] == 3
    assert restricted_workspace["document_input_summary"]["document_hash_count"] == 3
    assert restricted_workspace["document_input_summary"]["source"] == (
        "fixture_planning_documents"
    )
    assert len(restricted_workspace["codegen_input_hash"]) == 64
    assert restricted_workspace["repository_boundary"]["root_path_returned"] is False
    assert restricted_workspace["repository_boundary"]["file_content_returned"] is False
    assert checks["daacs_runtime_restricted_workspace_generation_projection"] is True
    assert checks["daacs_runtime_restricted_workspace_generation_passed"] is True
    assert checks["daacs_runtime_restricted_workspace_generation_prerequisite"] is True
    assert checks["daacs_runtime_restricted_workspace_generation_records"] is True
    assert checks["daacs_runtime_restricted_workspace_generation_writes"] is True
    assert checks["daacs_runtime_restricted_workspace_generation_codegen_input"] is True
    assert checks["daacs_runtime_restricted_workspace_generation_public_safe"] is True
    assert checks["daacs_runtime_restricted_workspace_generation_live_zero"] is True

    file_paths = {
        record["workspace_relative_path"]
        for record in restricted_workspace["file_records"]
    }
    for expected in {
        "README.md",
        "package.json",
        "src/App.tsx",
        "src/api.ts",
        "tests/verification.md",
    }:
        assert any(path.endswith(f"generated-app/{expected}") for path in file_paths)
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


def test_local_service_demo_verifies_generated_artifact_files(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "aw-verify-01-store",
        include_daacs_runtime_generated_artifact_verification=True,
    )
    serialized = _serialized(summary)
    comparison = summary["daacs_runtime_comparison"]
    generated_verification = summary[
        "daacs_runtime_generated_artifact_verification"
    ]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert comparison["comparison_variant_count"] == 8
    assert comparison["generated_artifact_verification_status"] == "passed"
    assert comparison["generated_artifact_verification_reason"] == (
        "generated_artifact_files_verified"
    )
    assert comparison["generated_artifact_verification_expected_file_count"] == 9
    assert comparison["generated_artifact_verification_file_check_count"] == 9
    assert comparison["generated_artifact_verification_content_hash_matches"] == 9
    assert comparison["generated_artifact_verification_byte_count_matches"] == 9
    assert comparison["generated_artifact_verification_file_reads"] == 9
    assert comparison[
        "generated_artifact_verification_file_content_public_returns"
    ] == 0
    assert comparison[
        "generated_artifact_verification_local_root_public_returns"
    ] == 0
    assert comparison["generated_artifact_verification_target_runtime_calls"] == 0
    assert comparison["generated_artifact_verification_provider_calls"] == 0
    assert comparison["generated_artifact_verification_sdk_imports"] == 0
    assert comparison["generated_artifact_verification_env_value_reads"] == 0
    assert comparison["generated_artifact_verification_subprocess_calls"] == 0
    assert comparison["generated_artifact_verification_network_calls"] == 0
    assert comparison["generated_artifact_verification_package_install_calls"] == 0
    assert comparison["generated_artifact_verification_build_calls"] == 0
    assert comparison["generated_artifact_verification_server_start_calls"] == 0
    assert generated_verification["projection_version"] == (
        TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_VERSION
    )
    assert generated_verification["status"] == "passed"
    assert generated_verification["mode"] == (
        TARGET_RUNTIME_GENERATED_ARTIFACT_VERIFICATION_MODE
    )
    assert generated_verification["counts"]["expected_file_count"] == 9
    assert generated_verification["counts"]["file_check_record_count"] == 9
    assert generated_verification["counts"]["content_hash_match_count"] == 9
    assert generated_verification["counts"]["byte_count_match_count"] == 9
    assert generated_verification["repository_boundary"]["root_path_returned"] is False
    assert generated_verification["repository_boundary"]["file_content_returned"] is False
    assert checks["daacs_runtime_generated_artifact_verification_projection"] is True
    assert checks["daacs_runtime_generated_artifact_verification_passed"] is True
    assert checks["daacs_runtime_generated_artifact_verification_prerequisite"] is True
    assert checks["daacs_runtime_generated_artifact_verification_records"] is True
    assert checks["daacs_runtime_generated_artifact_verification_public_safe"] is True
    assert checks["daacs_runtime_generated_artifact_verification_live_zero"] is True

    for record in generated_verification["file_check_records"]:
        assert record["content_included"] is False
        assert record["root_path_returned"] is False
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


def test_local_service_demo_statically_validates_generated_workspace(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "aw-build-01-store",
        include_daacs_runtime_generated_workspace_static_validation=True,
    )
    serialized = _serialized(summary)
    comparison = summary["daacs_runtime_comparison"]
    static_validation = summary[
        "daacs_runtime_generated_workspace_static_validation"
    ]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert comparison["comparison_variant_count"] == 9
    assert comparison["generated_workspace_static_validation_status"] == "passed"
    assert comparison["generated_workspace_static_validation_reason"] == (
        "generated_workspace_static_validation_passed"
    )
    assert comparison["generated_workspace_static_validation_file_checked_count"] == 9
    assert comparison["generated_workspace_static_validation_file_reads"] == 9
    assert comparison[
        "generated_workspace_static_validation_package_json_parse_pass"
    ] == 1
    assert comparison[
        "generated_workspace_static_validation_required_script_present_count"
    ] == 4
    assert comparison["generated_workspace_static_validation_app_marker_count"] == 13
    assert comparison["generated_workspace_static_validation_api_marker_count"] == 8
    assert (
        comparison[
            "generated_workspace_static_validation_verification_boundary_marker_count"
        ]
        == 4
    )
    assert comparison[
        "generated_workspace_static_validation_zero_call_marker_count"
    ] == 5
    assert comparison[
        "generated_workspace_static_validation_file_content_public_returns"
    ] == 0
    assert comparison[
        "generated_workspace_static_validation_local_root_public_returns"
    ] == 0
    assert comparison["generated_workspace_static_validation_target_runtime_calls"] == 0
    assert comparison["generated_workspace_static_validation_provider_calls"] == 0
    assert comparison["generated_workspace_static_validation_sdk_imports"] == 0
    assert comparison["generated_workspace_static_validation_env_value_reads"] == 0
    assert comparison["generated_workspace_static_validation_subprocess_calls"] == 0
    assert comparison["generated_workspace_static_validation_network_calls"] == 0
    assert comparison["generated_workspace_static_validation_package_install_calls"] == 0
    assert comparison["generated_workspace_static_validation_build_calls"] == 0
    assert comparison["generated_workspace_static_validation_server_start_calls"] == 0
    assert static_validation["projection_version"] == (
        TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_VERSION
    )
    assert static_validation["status"] == "passed"
    assert static_validation["mode"] == (
        TARGET_RUNTIME_GENERATED_WORKSPACE_STATIC_VALIDATION_MODE
    )
    assert static_validation["counts"]["static_file_checked_count"] == 9
    assert static_validation["counts"]["file_read_count"] == 9
    assert static_validation["counts"]["required_script_present_count"] == 4
    assert static_validation["repository_boundary"]["root_path_returned"] is False
    assert static_validation["repository_boundary"]["file_content_returned"] is False
    assert checks["daacs_runtime_generated_workspace_static_validation_projection"] is True
    assert checks["daacs_runtime_generated_workspace_static_validation_passed"] is True
    assert checks["daacs_runtime_generated_workspace_static_validation_prerequisite"] is True
    assert checks["daacs_runtime_generated_workspace_static_validation_records"] is True
    assert checks["daacs_runtime_generated_workspace_static_validation_public_safe"] is True
    assert checks["daacs_runtime_generated_workspace_static_validation_live_zero"] is True

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


def test_local_service_demo_projects_buildable_fixture_manifest(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "aw-build-02-store",
        include_daacs_runtime_buildable_fixture_manifest=True,
    )
    serialized = _serialized(summary)
    comparison = summary["daacs_runtime_comparison"]
    buildable_manifest = summary["daacs_runtime_buildable_fixture_manifest"]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert comparison["comparison_variant_count"] == 10
    assert comparison["buildable_fixture_manifest_status"] == "passed"
    assert comparison["buildable_fixture_manifest_reason"] == (
        "buildable_fixture_manifest_ready"
    )
    assert comparison["buildable_fixture_manifest_candidate"] is True
    assert comparison["buildable_fixture_manifest_file_reads"] == 5
    assert comparison["buildable_fixture_manifest_required_file_read_count"] == 5
    assert comparison["buildable_fixture_manifest_required_script_present_count"] == 4
    assert comparison["buildable_fixture_manifest_dependency_label_count"] >= 4
    assert comparison["buildable_fixture_manifest_placeholder_dependency_values"] == 0
    assert comparison["buildable_fixture_manifest_package_manifest_value_returns"] == 0
    assert comparison["buildable_fixture_manifest_file_content_public_returns"] == 0
    assert comparison["buildable_fixture_manifest_local_root_public_returns"] == 0
    assert comparison["buildable_fixture_manifest_target_runtime_calls"] == 0
    assert comparison["buildable_fixture_manifest_provider_calls"] == 0
    assert comparison["buildable_fixture_manifest_sdk_imports"] == 0
    assert comparison["buildable_fixture_manifest_env_value_reads"] == 0
    assert comparison["buildable_fixture_manifest_subprocess_calls"] == 0
    assert comparison["buildable_fixture_manifest_network_calls"] == 0
    assert comparison["buildable_fixture_manifest_package_install_calls"] == 0
    assert comparison["buildable_fixture_manifest_build_calls"] == 0
    assert comparison["buildable_fixture_manifest_server_start_calls"] == 0
    assert buildable_manifest["projection_version"] == (
        TARGET_RUNTIME_BUILDABLE_FIXTURE_MANIFEST_VERSION
    )
    assert buildable_manifest["status"] == "passed"
    assert buildable_manifest["build_ready_candidate"] is True
    assert buildable_manifest["counts"]["required_file_read_count"] == 5
    assert buildable_manifest["counts"]["required_script_present_count"] == 4
    assert buildable_manifest["counts"]["total_dependency_label_count"] >= 4
    assert buildable_manifest["counts"]["placeholder_dependency_value_count"] == 0
    assert buildable_manifest["package_manifest"]["dependency_value_returned"] is False
    assert checks["daacs_runtime_buildable_fixture_manifest_projection"] is True
    assert checks["daacs_runtime_buildable_fixture_manifest_passed"] is True
    assert checks["daacs_runtime_buildable_fixture_manifest_package"] is True
    assert checks["daacs_runtime_buildable_fixture_manifest_source_shape"] is True
    assert checks["daacs_runtime_buildable_fixture_manifest_public_safe"] is True
    assert checks["daacs_runtime_buildable_fixture_manifest_live_zero"] is True

    for forbidden in (
        "raw_prompt",
        "raw_log",
        "raw_file_body",
        "Build a small task collaboration app",
        "runtime_payload",
        "provider_payload",
        "fixture-reference",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(summary)


def test_daacs_runtime_local_build_preflight_api_uses_buildable_manifest_only(
    tmp_path,
):
    client = TestClient(
        create_app(
            target_runtime_restricted_workspace_generation_config=(
                TargetRuntimeRestrictedWorkspaceGenerationConfig(
                    root=tmp_path / "target-runtime-restricted-workspace"
                )
            ),
            target_runtime_generated_artifact_verification_config=(
                TargetRuntimeGeneratedArtifactVerificationConfig(
                    root=tmp_path / "target-runtime-restricted-workspace"
                )
            ),
            target_runtime_generated_workspace_static_validation_config=(
                TargetRuntimeGeneratedWorkspaceStaticValidationConfig(
                    root=tmp_path / "target-runtime-restricted-workspace"
                )
            ),
            target_runtime_buildable_fixture_manifest_config=(
                TargetRuntimeBuildableFixtureManifestConfig(
                    root=tmp_path / "target-runtime-restricted-workspace"
                )
            ),
        )
    )
    module = _load_demo_module()
    summary = module.run_demo(
        tmp_path / "aw-build-03-api-source",
        include_daacs_runtime_buildable_fixture_manifest=True,
    )
    buildable_manifest = summary["daacs_runtime_buildable_fixture_manifest"]

    response = client.post(
        "/api/v1/daacs/runtime/local-build-preflight",
        json={
            "run_id": buildable_manifest["run_id"]
            if "run_id" in buildable_manifest
            else summary["run_id"],
            "buildable_fixture_manifest_hash": buildable_manifest[
                "buildable_fixture_manifest_hash"
            ],
            "buildable_fixture_manifest_projection": buildable_manifest,
            "mode": TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE,
            "operator_opt_in": False,
            "raw_file_body": "AW_BUILD_03_API_RAW_SENTINEL",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    serialized = _serialized(data)
    assert data["projection_version"] == TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION
    assert data["status"] == "passed"
    assert data["reason"] == "local_build_preflight_ready"
    assert data["local_build_eligible"] is True
    assert data["local_build_opt_in_required"] is True
    assert data["operator_opt_in_present"] is False
    assert data["counts"]["command_plan_label_count"] == 4
    assert data["counts"]["command_plan_hash_count"] == 4
    assert data["counts"]["default_execution_permission_count"] == 0
    assert data["execution_boundary"]["package_install_calls"] == 0
    assert data["execution_boundary"]["build_calls"] == 0
    assert data["execution_boundary"]["server_start_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert "AW_BUILD_03_API_RAW_SENTINEL" not in serialized
    assert "raw_file_body" not in serialized
    assert str(tmp_path) not in serialized
    assert_public_projection_safe(data)


def test_local_service_demo_projects_local_build_preflight(tmp_path):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "aw-build-03-store",
        include_daacs_runtime_local_build_preflight=True,
    )
    serialized = _serialized(summary)
    comparison = summary["daacs_runtime_comparison"]
    local_build_preflight = summary["daacs_runtime_local_build_preflight"]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert comparison["comparison_variant_count"] == 11
    assert comparison["local_build_preflight_status"] == "passed"
    assert comparison["local_build_preflight_reason"] == "local_build_preflight_ready"
    assert comparison["local_build_preflight_eligible"] is True
    assert comparison["local_build_preflight_opt_in_required"] is True
    assert comparison["local_build_preflight_operator_opt_in_present"] is False
    assert comparison["local_build_preflight_command_label_count"] == 4
    assert comparison["local_build_preflight_command_hash_count"] == 4
    assert comparison["local_build_preflight_default_execution_permission_count"] == 0
    assert comparison["local_build_preflight_target_runtime_calls"] == 0
    assert comparison["local_build_preflight_provider_calls"] == 0
    assert comparison["local_build_preflight_sdk_imports"] == 0
    assert comparison["local_build_preflight_env_value_reads"] == 0
    assert comparison["local_build_preflight_subprocess_calls"] == 0
    assert comparison["local_build_preflight_network_calls"] == 0
    assert comparison["local_build_preflight_package_install_calls"] == 0
    assert comparison["local_build_preflight_build_calls"] == 0
    assert comparison["local_build_preflight_server_start_calls"] == 0
    assert local_build_preflight["projection_version"] == (
        TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION
    )
    assert local_build_preflight["status"] == "passed"
    assert local_build_preflight["mode"] == TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_MODE
    assert local_build_preflight["local_build_eligible"] is True
    assert local_build_preflight["local_build_opt_in_required"] is True
    assert local_build_preflight["counts"]["command_plan_label_count"] == 4
    assert local_build_preflight["counts"]["command_plan_hash_count"] == 4
    assert local_build_preflight["repository_boundary"]["root_path_returned"] is False
    assert local_build_preflight["repository_boundary"]["file_content_returned"] is False
    assert checks["daacs_runtime_local_build_preflight_projection"] is True
    assert checks["daacs_runtime_local_build_preflight_passed"] is True
    assert checks["daacs_runtime_local_build_preflight_policy"] is True
    assert checks["daacs_runtime_local_build_preflight_commands"] is True
    assert checks["daacs_runtime_local_build_preflight_public_safe"] is True
    assert checks["daacs_runtime_local_build_preflight_live_zero"] is True

    for forbidden in (
        "raw_prompt",
        "raw_log",
        "raw_file_body",
        "Build a small task collaboration app",
        "runtime_payload",
        "provider_payload",
        "fixture-reference",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(summary)


def test_daacs_runtime_local_build_attempt_api_requires_explicit_opt_in(
    tmp_path,
):
    source_root = tmp_path / "aw-build-04-api-source"
    client = TestClient(
        create_app(
            target_runtime_local_build_attempt_config=(
                TargetRuntimeLocalBuildAttemptConfig(
                    root=source_root / "target-runtime-restricted-workspace"
                )
            ),
        )
    )
    module = _load_demo_module()
    summary = module.run_demo(
        source_root,
        include_daacs_runtime_local_build_preflight=True,
    )
    preflight = summary["daacs_runtime_local_build_preflight"]

    response = client.post(
        "/api/v1/daacs/runtime/local-build-attempt",
        json={
            "run_id": preflight["run_id"],
            "local_build_preflight_hash": preflight["local_build_preflight_hash"],
            "local_build_preflight_projection": preflight,
            "mode": TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE,
            "operator_opt_in": False,
            "allow_local_command_execution": False,
            "raw_file_body": "AW_BUILD_04_API_RAW_SENTINEL",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    serialized = _serialized(data)
    assert data["projection_version"] == TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION
    assert data["status"] == "blocked"
    assert data["reason"] == "local_build_attempt_opt_in_required"
    assert data["local_build_attempted"] is False
    assert data["local_build_opt_in_present"] is False
    assert data["local_command_execution_allowed"] is False
    assert data["counts"]["package_install_attempt_count"] == 0
    assert data["counts"]["build_attempt_count"] == 0
    assert data["execution_boundary"]["subprocess_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["server_start_calls"] == 0
    assert data["execution_boundary"]["target_runtime_calls"] == 0
    assert data["repository_boundary"]["root_path_returned"] is False
    assert data["repository_boundary"]["command_output_returned"] is False
    assert "AW_BUILD_04_API_RAW_SENTINEL" not in serialized
    assert "raw_file_body" not in serialized
    assert str(tmp_path) not in serialized
    assert_public_projection_safe(data)


def test_local_service_demo_records_local_build_attempt_as_blocked_without_allow(
    tmp_path,
):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "aw-build-04-store",
        include_daacs_runtime_local_build_attempt=True,
        allow_local_build_attempt=False,
    )
    serialized = _serialized(summary)
    comparison = summary["daacs_runtime_comparison"]
    local_build_attempt = summary["daacs_runtime_local_build_attempt"]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert comparison["comparison_variant_count"] == 12
    assert comparison["local_build_attempt_status"] == "blocked"
    assert comparison["local_build_attempt_reason"] == (
        "local_build_attempt_opt_in_required"
    )
    assert comparison["local_build_attempt_attempted"] is False
    assert comparison["local_build_attempt_opt_in_present"] is False
    assert comparison["local_build_attempt_command_allowed"] is False
    assert comparison["local_build_attempt_command_result_count"] == 0
    assert comparison["local_build_attempt_package_install_attempts"] == 0
    assert comparison["local_build_attempt_build_attempts"] == 0
    assert comparison["local_build_attempt_server_start_attempts"] == 0
    assert comparison["local_build_attempt_raw_output_returns"] == 0
    assert comparison["local_build_attempt_target_runtime_calls"] == 0
    assert comparison["local_build_attempt_provider_calls"] == 0
    assert comparison["local_build_attempt_sdk_imports"] == 0
    assert comparison["local_build_attempt_env_value_reads"] == 0
    assert comparison["local_build_attempt_subprocess_calls"] == 0
    assert comparison["local_build_attempt_network_calls"] == 0
    assert comparison["local_build_attempt_package_install_calls"] == 0
    assert comparison["local_build_attempt_build_calls"] == 0
    assert comparison["local_build_attempt_server_start_calls"] == 0
    assert local_build_attempt["projection_version"] == (
        TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION
    )
    assert local_build_attempt["status"] == "blocked"
    assert local_build_attempt["mode"] == TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE
    assert local_build_attempt["local_build_attempted"] is False
    assert local_build_attempt["repository_boundary"]["root_path_returned"] is False
    assert local_build_attempt["repository_boundary"]["command_output_returned"] is False
    assert checks["daacs_runtime_local_build_attempt_projection"] is True
    assert checks["daacs_runtime_local_build_attempt_status_recorded"] is True
    assert checks["daacs_runtime_local_build_attempt_policy"] is True
    assert checks["daacs_runtime_local_build_attempt_results_hash_only"] is True
    assert checks["daacs_runtime_local_build_attempt_public_safe"] is True
    assert checks["daacs_runtime_local_build_attempt_provider_runtime_zero"] is True

    for forbidden in (
        "raw_prompt",
        "raw_log",
        "raw_file_body",
        "Build a small task collaboration app",
        "runtime_payload",
        "provider_payload",
        "fixture-reference",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(summary)


def test_daacs_runtime_local_preview_attempt_api_requires_explicit_opt_in(
    tmp_path,
):
    source_root = tmp_path / "aw-preview-01-api-source"
    client = TestClient(
        create_app(
            target_runtime_local_preview_attempt_config=(
                TargetRuntimeLocalPreviewAttemptConfig(
                    root=source_root / "target-runtime-restricted-workspace"
                )
            ),
        )
    )
    module = _load_demo_module()
    summary = module.run_demo(
        source_root,
        include_daacs_runtime_local_build_attempt=True,
        allow_local_build_attempt=True,
    )
    local_build_attempt = summary["daacs_runtime_local_build_attempt"]

    response = client.post(
        "/api/v1/daacs/runtime/local-preview-attempt",
        json={
            "run_id": local_build_attempt["run_id"],
            "local_build_attempt_hash": local_build_attempt[
                "local_build_attempt_hash"
            ],
            "local_build_attempt_projection": local_build_attempt,
            "mode": TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE,
            "operator_opt_in": False,
            "allow_local_preview_server": False,
            "allow_browser_verification": False,
            "raw_file_body": "AW_PREVIEW_01_API_RAW_SENTINEL",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    serialized = _serialized(data)
    assert data["projection_version"] == TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_VERSION
    assert data["status"] == "blocked"
    assert data["reason"] == "local_preview_opt_in_required"
    assert data["mode"] == TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE
    assert data["local_preview_attempted"] is False
    assert data["local_preview_opt_in_present"] is False
    assert data["local_preview_server_allowed"] is False
    assert data["browser_verification_allowed"] is False
    assert data["counts"]["preview_server_start_attempt_count"] == 0
    assert data["counts"]["server_start_count"] == 0
    assert data["execution_boundary"]["subprocess_calls"] == 0
    assert data["execution_boundary"]["server_start_calls"] == 0
    assert data["execution_boundary"]["network_calls"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["repository_boundary"]["root_path_returned"] is False
    assert data["repository_boundary"]["screenshot_path_returned"] is False
    assert "AW_PREVIEW_01_API_RAW_SENTINEL" not in serialized
    assert "raw_file_body" not in serialized
    assert str(tmp_path) not in serialized
    assert_public_projection_safe(data)


def test_daacs_runtime_browser_setup_attempt_api_requires_explicit_opt_in():
    client = TestClient(create_app())
    preflight = BrowserRuntimePreflightResult(
        available=False,
        status="environment_blocked",
        reason="playwright_python_package_missing",
        import_checked=True,
        launch_checked=False,
        browser_engine="chromium",
        duration_ms=1,
    ).to_public_record()

    response = client.post(
        "/api/v1/daacs/runtime/browser-setup-attempt",
        json={
            "run_id": "preview-03-api-run",
            "browser_runtime_preflight_hash": stable_contract_hash(preflight),
            "browser_runtime_preflight_projection": preflight,
            "mode": TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE,
            "operator_opt_in": False,
            "allow_browser_runtime_setup": False,
            "raw_file_body": "AW_PREVIEW_03_API_RAW_SENTINEL",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    serialized = _serialized(data)
    assert data["projection_version"] == TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_VERSION
    assert data["status"] == "blocked"
    assert data["reason"] == "browser_runtime_setup_opt_in_required"
    assert data["mode"] == TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE
    assert data["setup_attempted"] is False
    assert data["operator_opt_in_present"] is False
    assert data["browser_runtime_setup_allowed"] is False
    assert data["browser_runtime_preflight"]["projection_version"] == (
        BROWSER_RUNTIME_PREFLIGHT_VERSION
    )
    assert data["counts"]["default_setup_command_execution_count"] == 0
    assert data["counts"]["setup_command_attempt_count"] == 0
    assert data["counts"]["browser_runtime_available_after_setup_count"] == 0
    assert data["execution_boundary"]["local_process_calls"] == 0
    assert data["execution_boundary"]["provider_calls"] == 0
    assert data["execution_boundary"]["solar_live_calls"] == 0
    assert data["execution_boundary"]["daacs_target_runtime_calls"] == 0
    assert data["repository_boundary"]["raw_command_output_stored"] is False
    assert data["repository_boundary"]["local_root_path_returned"] is False
    assert "AW_PREVIEW_03_API_RAW_SENTINEL" not in serialized
    assert "raw_file_body" not in serialized
    assert "pip install playwright" not in serialized
    assert "playwright install chromium" not in serialized
    assert_public_projection_safe(data)


def test_local_service_demo_records_local_preview_attempt_as_blocked_without_allow(
    tmp_path,
):
    module = _load_demo_module()

    summary = module.run_demo(
        tmp_path / "aw-preview-01-store",
        include_daacs_runtime_local_preview_attempt=True,
        allow_local_preview_attempt=False,
    )
    serialized = _serialized(summary)
    comparison = summary["daacs_runtime_comparison"]
    local_build_attempt = summary["daacs_runtime_local_build_attempt"]
    local_preview_attempt = summary["daacs_runtime_local_preview_attempt"]
    checks = summary["checks"]

    assert summary["status"] == "passed"
    assert comparison["comparison_variant_count"] == 13
    assert comparison["local_build_attempt_status"] == "blocked"
    assert comparison["local_build_attempt_attempted"] is False
    assert comparison["local_preview_attempt_status"] == "blocked"
    assert comparison["local_preview_attempt_reason"] == (
        "local_preview_opt_in_required"
    )
    assert comparison["local_preview_attempt_attempted"] is False
    assert comparison["local_preview_attempt_opt_in_present"] is False
    assert comparison["local_preview_attempt_server_allowed"] is False
    assert comparison["local_preview_attempt_browser_allowed"] is False
    assert comparison["local_preview_attempt_server_start_attempts"] == 0
    assert comparison["local_preview_attempt_server_starts"] == 0
    assert comparison["local_preview_attempt_server_stops"] == 0
    assert comparison["local_preview_attempt_browser_verification_attempts"] == 0
    assert comparison["local_preview_attempt_screenshot_evidence_count"] == 0
    assert comparison["local_preview_attempt_raw_output_returns"] == 0
    assert comparison["local_preview_attempt_target_runtime_calls"] == 0
    assert comparison["local_preview_attempt_provider_calls"] == 0
    assert comparison["local_preview_attempt_sdk_imports"] == 0
    assert comparison["local_preview_attempt_env_value_reads"] == 0
    assert comparison["local_preview_attempt_subprocess_calls"] == 0
    assert comparison["local_preview_attempt_network_calls"] == 0
    assert comparison["local_preview_attempt_external_network_calls"] == 0
    assert comparison["local_preview_attempt_package_install_calls"] == 0
    assert comparison["local_preview_attempt_build_calls"] == 0
    assert comparison["local_preview_attempt_server_start_calls"] == 0
    assert comparison["local_preview_attempt_server_stop_calls"] == 0
    assert local_build_attempt["local_build_attempted"] is False
    assert local_preview_attempt["projection_version"] == (
        TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_VERSION
    )
    assert local_preview_attempt["status"] == "blocked"
    assert local_preview_attempt["mode"] == TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE
    assert local_preview_attempt["local_preview_attempted"] is False
    assert local_preview_attempt["repository_boundary"]["root_path_returned"] is False
    assert (
        local_preview_attempt["repository_boundary"]["screenshot_path_returned"]
        is False
    )
    assert checks["daacs_runtime_local_preview_attempt_projection"] is True
    assert checks["daacs_runtime_local_preview_attempt_status_recorded"] is True
    assert checks["daacs_runtime_local_preview_attempt_policy"] is True
    assert checks["daacs_runtime_local_preview_attempt_evidence_hash_only"] is True
    assert checks["daacs_runtime_local_preview_attempt_public_safe"] is True
    assert checks["daacs_runtime_local_preview_attempt_provider_runtime_zero"] is True

    for forbidden in (
        "raw_prompt",
        "raw_log",
        "raw_file_body",
        "Build a small task collaboration app",
        "runtime_payload",
        "provider_payload",
        "fixture-reference",
        str(tmp_path),
    ):
        assert forbidden not in serialized
    assert_public_projection_safe(summary)

"""Restricted fixture workspace generation for portfolio-visible output.

This module writes a small, sanitized app skeleton into a run-scoped local
workspace. It is deliberately template-backed: it does not execute the DAACS
target runtime, install packages, run builds, start servers, import provider
SDKs, read environment values, or open network connections.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Callable

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys, sanitize_public_payload
from packages.core.pathing import PathBoundaryError, resolve_within_root
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash, utc_now

from .runner_provider import is_safe_run_id, safe_public_run_id
from .target_runtime_generated_artifact_bundle import (
    TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION = (
    "target-runtime-restricted-workspace-generation-public-v1"
)
TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE = (
    "target_runtime_restricted_workspace_fixture_generation"
)
RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS = (
    "readme",
    "package_json",
    "index_html",
    "main_entrypoint",
    "app_component",
    "api_client",
    "vite_config",
    "tsconfig_json",
    "verification_notes",
)


@dataclass(frozen=True, slots=True)
class RestrictedWorkspaceTemplate:
    """Allowlisted generated workspace file template."""

    template_id: str
    label: str
    artifact_kind: str
    relative_path: str
    render: Callable[["TargetRuntimeRestrictedWorkspaceGenerationRequest"], str]


@dataclass(frozen=True, slots=True)
class TargetRuntimeRestrictedWorkspaceGenerationRequest:
    """Request to write a sanitized fixture app skeleton under a run workspace."""

    run_id: str
    runner_plan_hash: str
    implementation_brief_hash: str
    generated_artifact_bundle_hash: str
    generated_artifact_bundle_projection: JsonDict = field(default_factory=dict)
    workspace_root: str | Path | None = None
    template_ids: tuple[str, ...] = RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS
    mode: str = TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TargetRuntimeRestrictedWorkspaceFileRecord:
    """Public-safe record for one generated fixture workspace file."""

    file_id: str
    run_id: str
    label: str
    artifact_kind: str
    workspace_relative_path: str
    content_hash: str
    byte_count: int
    content_included: bool
    root_path_returned: bool
    created_at: str

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("restricted workspace file record must be a mapping")
        _assert_projection_safe(payload)
        return payload


@dataclass(frozen=True, slots=True)
class TargetRuntimeRestrictedWorkspaceGenerationResult:
    """Public-safe restricted workspace generation projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    runner_plan_hash: str
    implementation_brief_hash: str
    generated_artifact_bundle_hash: str
    generated_artifact_bundle_projection_hash: str
    generated_workspace_hash: str
    file_records: list[JsonDict]
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    repository_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("restricted workspace generation result must be a mapping")
        _assert_projection_safe(payload)
        return payload


def _is_contract_hash(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


def _as_int(value: object) -> int:
    if type(value) is int and value >= 0:
        return value
    return 0


def _assert_projection_safe(value: JsonDict) -> None:
    public = sanitize_public_payload(value)
    if not isinstance(public, dict):
        raise ValueError("restricted workspace projection must be a mapping")
    if find_forbidden_public_keys(public):
        raise ValueError("restricted workspace projection contains forbidden keys")
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError("restricted workspace projection contains forbidden claims")
    assert_public_projection_safe(public)


def _zero_execution_boundary(*, file_write_count: int = 0) -> JsonDict:
    return {
        "target_runtime_calls": 0,
        "provider_calls": 0,
        "live_api_calls": 0,
        "sdk_imports": 0,
        "env_key_value_reads": 0,
        "subprocess_calls": 0,
        "network_calls": 0,
        "package_install_calls": 0,
        "build_calls": 0,
        "server_start_calls": 0,
        "execution_permission_count": 0,
        "restricted_workspace_file_write_count": file_write_count,
        "filesystem_writes_outside_workspace": 0,
        "generated_file_content_public_return_count": 0,
    }


def _repository_boundary(*, configured: bool) -> JsonDict:
    return {
        "restricted_workspace_backend": "local" if configured else "unconfigured",
        "root_path_returned": False,
        "raw_row_returned": False,
        "file_content_returned": False,
    }


def _claim_boundary() -> JsonDict:
    return {
        "scope": "restricted local fixture workspace generation only",
        "fixture_generation": True,
        "target_runtime_outcome": False,
        "external_provider_outcome": False,
        "generated_file_content_public": False,
        "source_body_public": False,
        "build_executed": False,
        "server_started": False,
        "hosted_behavior": False,
        "production_trust_claim": False,
    }


def _check(
    checks: list[JsonDict],
    failures: list[str],
    *,
    name: str,
    passed: bool,
    reason: str,
) -> None:
    checks.append({"name": name, "passed": bool(passed), "reason": "" if passed else reason})
    if not passed:
        failures.append(reason)


def _bundle_counts(bundle: JsonDict) -> JsonDict:
    counts = bundle.get("counts", {})
    return counts if isinstance(counts, dict) else {}


def _bundle_execution(bundle: JsonDict) -> JsonDict:
    execution = bundle.get("execution_boundary", {})
    return execution if isinstance(execution, dict) else {}


def _bundle_projection_hash(bundle: JsonDict) -> str:
    sanitized = sanitize_public_payload(bundle)
    if not isinstance(sanitized, dict):
        return ""
    _assert_projection_safe(sanitized)
    return stable_contract_hash(sanitized)


def _render_readme(request: TargetRuntimeRestrictedWorkspaceGenerationRequest) -> str:
    return (
        "# Agentic Workbench Fixture App Skeleton\n\n"
        "This folder is a sanitized, template-backed local fixture generated for "
        "portfolio preview.\n\n"
        "## Evidence\n\n"
        f"- run_id: {safe_public_run_id(request.run_id)}\n"
        f"- runner_plan_hash: {request.runner_plan_hash}\n"
        f"- implementation_brief_hash: {request.implementation_brief_hash}\n"
        f"- generated_artifact_bundle_hash: {request.generated_artifact_bundle_hash}\n\n"
        "## Execution Boundary\n\n"
        "- DAACS target runtime calls: 0\n"
        "- Provider calls: 0\n"
        "- Package installs: 0\n"
        "- Builds: 0\n"
        "- Server starts: 0\n"
    )


def _render_package_json(request: TargetRuntimeRestrictedWorkspaceGenerationRequest) -> str:
    package = {
        "name": f"agentic-workbench-fixture-{safe_public_run_id(request.run_id)}",
        "private": True,
        "version": "0.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview",
            "verify": "tsc --noEmit",
        },
        "dependencies": {
            "react": "^19.2.7",
            "react-dom": "^19.2.7",
        },
        "devDependencies": {
            "@types/react": "^19.2.16",
            "@types/react-dom": "^19.2.3",
            "@vitejs/plugin-react": "^6.0.2",
            "typescript": "^6.0.3",
            "vite": "^8.0.16",
        },
        "agenticWorkbench": {
            "mode": TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE,
            "runId": safe_public_run_id(request.run_id),
            "targetRuntimeCalls": 0,
            "packageInstallCalls": 0,
            "buildCalls": 0,
        },
    }
    return json.dumps(package, ensure_ascii=True, sort_keys=True, indent=2) + "\n"


def _render_index_html(request: TargetRuntimeRestrictedWorkspaceGenerationRequest) -> str:
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "  <head>\n"
        "    <meta charset=\"UTF-8\" />\n"
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />\n"
        "    <title>Agentic Workbench Fixture App</title>\n"
        "  </head>\n"
        "  <body>\n"
        "    <div id=\"root\"></div>\n"
        "    <script type=\"module\" src=\"/src/main.tsx\"></script>\n"
        "  </body>\n"
        "</html>\n"
    )


def _render_main_entrypoint(
    request: TargetRuntimeRestrictedWorkspaceGenerationRequest,
) -> str:
    return (
        "import React from 'react';\n"
        "import { createRoot } from 'react-dom/client';\n"
        "import App from './App';\n\n"
        "createRoot(document.getElementById('root')!).render(\n"
        "  <React.StrictMode>\n"
        "    <App />\n"
        "  </React.StrictMode>,\n"
        ");\n"
    )


def _render_app_component(
    request: TargetRuntimeRestrictedWorkspaceGenerationRequest,
) -> str:
    run_id = json.dumps(safe_public_run_id(request.run_id))
    return (
        "import { getFixtureRunSummary } from './api';\n\n"
        "export default function App() {\n"
        "  const summary = getFixtureRunSummary();\n"
        "  const cards = [\n"
        "    { label: 'Planning', value: 'PRDPackage ready' },\n"
        "    { label: 'Build', value: 'RunnerPlan ready' },\n"
        "    { label: 'Verify', value: 'VerificationReport ready' },\n"
        "  ];\n\n"
        "  return (\n"
        "    <main aria-label=\"Agentic Workbench fixture app\">\n"
        "      <h1>Agentic Workbench Fixture App</h1>\n"
        f"      <p>Run {{ {run_id} }}</p>\n"
        "      <section>\n"
        "        <h2>Workflow</h2>\n"
        "        <ol>\n"
        "          {summary.stages.map((stage) => <li key={stage}>{stage}</li>)}\n"
        "        </ol>\n"
        "      </section>\n"
        "      <section>\n"
        "        <h2>Artifact Cards</h2>\n"
        "        {cards.map((card) => (\n"
        "          <article key={card.label}>\n"
        "            <h3>{card.label}</h3>\n"
        "            <p>{card.value}</p>\n"
        "          </article>\n"
        "        ))}\n"
        "      </section>\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    )


def _render_api_client(request: TargetRuntimeRestrictedWorkspaceGenerationRequest) -> str:
    return (
        "export type FixtureRunSummary = {\n"
        "  runId: string;\n"
        "  stages: string[];\n"
        "  providerCalls: number;\n"
        "  targetRuntimeCalls: number;\n"
        "};\n\n"
        "export function getFixtureRunSummary(): FixtureRunSummary {\n"
        "  return {\n"
        f"    runId: {json.dumps(safe_public_run_id(request.run_id))},\n"
        "    stages: ['Idea', 'PlanningBlueprint', 'PRDPackage', 'ImplementationBrief', 'Approval', 'RunnerPlan', 'VerificationReport'],\n"
        "    providerCalls: 0,\n"
        "    targetRuntimeCalls: 0,\n"
        "  };\n"
        "}\n"
    )


def _render_vite_config(request: TargetRuntimeRestrictedWorkspaceGenerationRequest) -> str:
    return (
        "import { defineConfig } from 'vite';\n"
        "import react from '@vitejs/plugin-react';\n\n"
        "export default defineConfig({\n"
        "  plugins: [react()],\n"
        "});\n"
    )


def _render_tsconfig_json(
    request: TargetRuntimeRestrictedWorkspaceGenerationRequest,
) -> str:
    config = {
        "compilerOptions": {
            "target": "ES2020",
            "useDefineForClassFields": True,
            "lib": ["DOM", "DOM.Iterable", "ES2020"],
            "allowJs": False,
            "skipLibCheck": True,
            "esModuleInterop": True,
            "allowSyntheticDefaultImports": True,
            "strict": True,
            "forceConsistentCasingInFileNames": True,
            "module": "ESNext",
            "moduleResolution": "Node",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx",
        },
        "include": ["src"],
        "references": [],
    }
    return json.dumps(config, ensure_ascii=True, sort_keys=True, indent=2) + "\n"


def _render_verification_notes(
    request: TargetRuntimeRestrictedWorkspaceGenerationRequest,
) -> str:
    return (
        "# Fixture Verification Notes\n\n"
        "| Check | Result |\n"
        "|---|---:|\n"
        "| Generated files | 9 |\n"
        "| Provider calls | 0 |\n"
        "| DAACS target runtime calls | 0 |\n"
        "| Package installs | 0 |\n"
        "| Builds | 0 |\n"
        "| Server starts | 0 |\n\n"
        f"generation_request_hash: {stable_contract_hash({'run_id': safe_public_run_id(request.run_id), 'runner_plan_hash': request.runner_plan_hash})}\n"
    )


RESTRICTED_WORKSPACE_TEMPLATES: dict[str, RestrictedWorkspaceTemplate] = {
    "readme": RestrictedWorkspaceTemplate(
        template_id="readme",
        label="readme",
        artifact_kind="documentation",
        relative_path="README.md",
        render=_render_readme,
    ),
    "package_json": RestrictedWorkspaceTemplate(
        template_id="package_json",
        label="package_json",
        artifact_kind="package_manifest",
        relative_path="package.json",
        render=_render_package_json,
    ),
    "index_html": RestrictedWorkspaceTemplate(
        template_id="index_html",
        label="index_html",
        artifact_kind="frontend_entry_html",
        relative_path="index.html",
        render=_render_index_html,
    ),
    "main_entrypoint": RestrictedWorkspaceTemplate(
        template_id="main_entrypoint",
        label="main_entrypoint",
        artifact_kind="frontend_entrypoint",
        relative_path="src/main.tsx",
        render=_render_main_entrypoint,
    ),
    "app_component": RestrictedWorkspaceTemplate(
        template_id="app_component",
        label="app_component",
        artifact_kind="frontend_component",
        relative_path="src/App.tsx",
        render=_render_app_component,
    ),
    "api_client": RestrictedWorkspaceTemplate(
        template_id="api_client",
        label="api_client",
        artifact_kind="frontend_api_client",
        relative_path="src/api.ts",
        render=_render_api_client,
    ),
    "vite_config": RestrictedWorkspaceTemplate(
        template_id="vite_config",
        label="vite_config",
        artifact_kind="build_config",
        relative_path="vite.config.ts",
        render=_render_vite_config,
    ),
    "tsconfig_json": RestrictedWorkspaceTemplate(
        template_id="tsconfig_json",
        label="tsconfig_json",
        artifact_kind="typescript_config",
        relative_path="tsconfig.json",
        render=_render_tsconfig_json,
    ),
    "verification_notes": RestrictedWorkspaceTemplate(
        template_id="verification_notes",
        label="verification_notes",
        artifact_kind="verification_notes",
        relative_path="tests/verification.md",
        render=_render_verification_notes,
    ),
}


def _selected_templates(template_ids: tuple[str, ...]) -> list[RestrictedWorkspaceTemplate]:
    templates: list[RestrictedWorkspaceTemplate] = []
    seen: set[str] = set()
    for template_id in template_ids:
        normalized = str(template_id).strip()
        if not normalized:
            raise ValueError("restricted_workspace_template_id_missing")
        if "/" in normalized or "\\" in normalized or ":" in normalized or normalized.startswith("."):
            raise ValueError("restricted_workspace_template_id_unsafe")
        if normalized not in RESTRICTED_WORKSPACE_TEMPLATES:
            raise ValueError("restricted_workspace_template_not_allowlisted")
        if normalized in seen:
            raise ValueError("restricted_workspace_template_duplicate")
        seen.add(normalized)
        templates.append(RESTRICTED_WORKSPACE_TEMPLATES[normalized])
    return templates


def _relative_workspace_path(*, run_id: str, template: RestrictedWorkspaceTemplate) -> str:
    return (
        f"runs/{safe_public_run_id(run_id)}/generated-app/"
        f"{template.relative_path}"
    )


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{stable_contract_hash(content)[:12]}.tmp")
    try:
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(path)
    except OSError:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass
        raise


def _file_record(
    *,
    request: TargetRuntimeRestrictedWorkspaceGenerationRequest,
    template: RestrictedWorkspaceTemplate,
    relative_path: str,
    content: str,
    created_at: str,
) -> TargetRuntimeRestrictedWorkspaceFileRecord:
    content_hash = stable_contract_hash(
        {
            "template_id": template.template_id,
            "relative_path": relative_path,
            "content": content,
        }
    )
    return TargetRuntimeRestrictedWorkspaceFileRecord(
        file_id=f"generated-file-{content_hash[:16]}",
        run_id=safe_public_run_id(request.run_id),
        label=template.label,
        artifact_kind=template.artifact_kind,
        workspace_relative_path=relative_path,
        content_hash=content_hash,
        byte_count=len(content.encode("utf-8")),
        content_included=False,
        root_path_returned=False,
        created_at=created_at,
    )


def _counts(
    *,
    checks: list[JsonDict],
    file_records: list[JsonDict],
    bundle: JsonDict,
    bundle_hash_match_count: int,
    write_count: int,
) -> JsonDict:
    bundle_counts = _bundle_counts(bundle)
    failed_check_count = sum(1 for check in checks if not check["passed"])
    return {
        "restricted_workspace_generation_count": 1 if write_count else 0,
        "comparison_variant_count": 1,
        "check_count": len(checks),
        "failed_check_count": failed_check_count,
        "generated_artifact_bundle_projection_count": 1 if bundle else 0,
        "generated_artifact_bundle_hash_match_count": bundle_hash_match_count,
        "generated_artifact_bundle_artifact_unit_count": _as_int(
            bundle_counts.get("artifact_unit_count")
        ),
        "generated_workspace_file_record_count": len(file_records),
        "generated_workspace_file_hash_count": len(
            {record["content_hash"] for record in file_records}
        ),
        "generated_workspace_file_byte_count": sum(
            _as_int(record.get("byte_count")) for record in file_records
        ),
        "restricted_workspace_file_write_count": write_count,
        "write_allowlist_violation_count": 0,
        "path_traversal_block_count": 0,
        "absolute_path_block_count": 0,
        "file_content_public_return_count": 0,
        "local_root_path_return_count": 0,
        "target_runtime_call_count": 0,
        "provider_call_count": 0,
        "sdk_import_count": 0,
        "env_value_read_count": 0,
        "subprocess_call_count": 0,
        "network_call_count": 0,
        "package_install_call_count": 0,
        "build_call_count": 0,
        "server_start_call_count": 0,
        "execution_permission_count": 0,
    }


def _hash_for_workspace(
    *,
    request: TargetRuntimeRestrictedWorkspaceGenerationRequest,
    bundle_projection_hash: str,
    file_records: list[JsonDict],
    status: str,
    reason: str,
    failed_check_count: int,
) -> str:
    return stable_contract_hash(
        {
            "projection_version": TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION,
            "run_id": safe_public_run_id(request.run_id),
            "mode": request.mode,
            "runner_plan_hash": request.runner_plan_hash,
            "implementation_brief_hash": request.implementation_brief_hash,
            "generated_artifact_bundle_hash": request.generated_artifact_bundle_hash,
            "generated_artifact_bundle_projection_hash": bundle_projection_hash,
            "file_hashes": [record["content_hash"] for record in file_records],
            "status": status,
            "reason": reason,
            "failed_check_count": failed_check_count,
        }
    )


def _result(
    *,
    request: TargetRuntimeRestrictedWorkspaceGenerationRequest,
    status: str,
    reason: str,
    checks: list[JsonDict],
    file_records: list[JsonDict],
    bundle_projection_hash: str,
    bundle_hash_match_count: int,
    write_count: int,
    configured: bool,
) -> TargetRuntimeRestrictedWorkspaceGenerationResult:
    failed_check_count = sum(1 for check in checks if not check["passed"])
    generated_workspace_hash = _hash_for_workspace(
        request=request,
        bundle_projection_hash=bundle_projection_hash,
        file_records=file_records,
        status=status,
        reason=reason,
        failed_check_count=failed_check_count,
    )
    return TargetRuntimeRestrictedWorkspaceGenerationResult(
        projection_version=TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION,
        run_id=safe_public_run_id(request.run_id),
        mode=request.mode,
        status=status,
        reason=reason,
        runner_plan_hash=request.runner_plan_hash
        if _is_contract_hash(request.runner_plan_hash)
        else "",
        implementation_brief_hash=request.implementation_brief_hash
        if _is_contract_hash(request.implementation_brief_hash)
        else "",
        generated_artifact_bundle_hash=request.generated_artifact_bundle_hash
        if _is_contract_hash(request.generated_artifact_bundle_hash)
        else "",
        generated_artifact_bundle_projection_hash=bundle_projection_hash
        if _is_contract_hash(bundle_projection_hash)
        else "",
        generated_workspace_hash=generated_workspace_hash,
        file_records=file_records,
        checks=checks,
        counts=_counts(
            checks=checks,
            file_records=file_records,
            bundle=request.generated_artifact_bundle_projection,
            bundle_hash_match_count=bundle_hash_match_count,
            write_count=write_count,
        ),
        execution_boundary=_zero_execution_boundary(file_write_count=write_count),
        repository_boundary=_repository_boundary(configured=configured),
        claim_boundary=_claim_boundary(),
    )


class TargetRuntimeRestrictedWorkspaceGenerationService:
    """Generate a sanitized fixture app skeleton in a restricted workspace."""

    def generate(
        self,
        request: TargetRuntimeRestrictedWorkspaceGenerationRequest,
    ) -> TargetRuntimeRestrictedWorkspaceGenerationResult:
        bundle = (
            request.generated_artifact_bundle_projection
            if isinstance(request.generated_artifact_bundle_projection, dict)
            else {}
        )
        bundle_counts = _bundle_counts(bundle)
        bundle_execution = _bundle_execution(bundle)
        bundle_projection_hash = _bundle_projection_hash(bundle) if bundle else ""
        bundle_hash_match = (
            _is_contract_hash(request.generated_artifact_bundle_hash)
            and request.generated_artifact_bundle_hash
            == bundle.get("generated_artifact_bundle_hash")
        )
        workspace_root = Path(request.workspace_root) if request.workspace_root else None
        configured = workspace_root is not None
        checks: list[JsonDict] = []
        failures: list[str] = []

        try:
            templates = _selected_templates(tuple(request.template_ids))
            template_selection_valid = True
            template_failure_reason = ""
        except ValueError as exc:
            templates = []
            template_selection_valid = False
            template_failure_reason = str(exc)

        _check(
            checks,
            failures,
            name="restricted_workspace_mode_valid",
            passed=request.mode == TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE,
            reason="target_runtime_restricted_workspace_generation_mode_invalid",
        )
        _check(
            checks,
            failures,
            name="run_id_safe",
            passed=is_safe_run_id(request.run_id),
            reason="run_id_invalid",
        )
        _check(
            checks,
            failures,
            name="runner_plan_hash_valid",
            passed=_is_contract_hash(request.runner_plan_hash),
            reason="runner_plan_hash_invalid",
        )
        _check(
            checks,
            failures,
            name="implementation_brief_hash_valid",
            passed=_is_contract_hash(request.implementation_brief_hash),
            reason="implementation_brief_hash_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_hash_valid",
            passed=_is_contract_hash(request.generated_artifact_bundle_hash),
            reason="generated_artifact_bundle_hash_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_projection_present",
            passed=bool(bundle),
            reason="generated_artifact_bundle_projection_missing",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_projection_version",
            passed=bundle.get("projection_version")
            == TARGET_RUNTIME_GENERATED_ARTIFACT_BUNDLE_VERSION,
            reason="generated_artifact_bundle_projection_version_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_projection_blocked",
            passed=bundle.get("status") == "blocked",
            reason="generated_artifact_bundle_projection_status_invalid",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_run_matches",
            passed=bundle.get("run_id") == safe_public_run_id(request.run_id),
            reason="generated_artifact_bundle_run_mismatch",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_hash_matches_projection",
            passed=bundle_hash_match,
            reason="generated_artifact_bundle_hash_mismatch",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_prerequisite_complete",
            passed=_as_int(bundle_counts.get("output_manifest_hash_match_count")) == 1
            and _as_int(bundle_counts.get("artifact_unit_count")) >= 3
            and _as_int(bundle_counts.get("generated_artifact_body_write_count")) == 0,
            reason="generated_artifact_bundle_prerequisite_incomplete",
        )
        _check(
            checks,
            failures,
            name="generated_artifact_bundle_zero_call_boundary",
            passed=_as_int(bundle_execution.get("target_runtime_calls")) == 0
            and _as_int(bundle_execution.get("filesystem_writes")) == 0
            and _as_int(bundle_execution.get("subprocess_calls")) == 0
            and _as_int(bundle_execution.get("network_calls")) == 0
            and _as_int(bundle_execution.get("execution_permission_count")) == 0
            and _as_int(bundle_execution.get("generated_artifact_body_write_count")) == 0,
            reason="generated_artifact_bundle_zero_call_boundary_invalid",
        )
        _check(
            checks,
            failures,
            name="template_ids_allowlisted",
            passed=template_selection_valid,
            reason=template_failure_reason or "restricted_workspace_template_invalid",
        )
        _check(
            checks,
            failures,
            name="required_templates_present",
            passed=set(request.template_ids) == set(RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS),
            reason="restricted_workspace_required_templates_missing",
        )
        _check(
            checks,
            failures,
            name="restricted_workspace_root_configured",
            passed=configured,
            reason="restricted_workspace_root_unconfigured",
        )

        file_records: list[JsonDict] = []
        write_count = 0
        if failures:
            return _result(
                request=request,
                status="blocked",
                reason=failures[0],
                checks=checks,
                file_records=file_records,
                bundle_projection_hash=bundle_projection_hash,
                bundle_hash_match_count=1 if bundle_hash_match else 0,
                write_count=write_count,
                configured=configured,
            )

        assert workspace_root is not None
        created_at = utc_now()
        try:
            for template in templates:
                content = template.render(request)
                relative_path = _relative_workspace_path(
                    run_id=request.run_id,
                    template=template,
                )
                target_path = resolve_within_root(workspace_root, relative_path)
                _write_text_atomic(target_path, content)
                record = _file_record(
                    request=request,
                    template=template,
                    relative_path=relative_path,
                    content=content,
                    created_at=created_at,
                ).to_dict()
                file_records.append(record)
                write_count += 1
        except (OSError, PathBoundaryError, ValueError):
            return _result(
                request=request,
                status="blocked",
                reason="restricted_workspace_generation_failed",
                checks=[
                    *checks,
                    {
                        "name": "restricted_workspace_generated",
                        "passed": False,
                        "reason": "restricted_workspace_generation_failed",
                    },
                ],
                file_records=[],
                bundle_projection_hash=bundle_projection_hash,
                bundle_hash_match_count=1 if bundle_hash_match else 0,
                write_count=0,
                configured=configured,
            )

        generated = len(file_records) >= len(RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS)
        final_checks = [
            *checks,
            {
                "name": "restricted_workspace_generated",
                "passed": generated,
                "reason": "" if generated else "restricted_workspace_generation_incomplete",
            },
        ]
        status = "passed" if generated else "blocked"
        reason = (
            "target_runtime_restricted_workspace_generated"
            if generated
            else "restricted_workspace_generation_incomplete"
        )
        return _result(
            request=request,
            status=status,
            reason=reason,
            checks=final_checks,
            file_records=file_records,
            bundle_projection_hash=bundle_projection_hash,
            bundle_hash_match_count=1 if bundle_hash_match else 0,
            write_count=write_count,
            configured=configured,
        )


def default_target_runtime_restricted_workspace_generation_service() -> (
    TargetRuntimeRestrictedWorkspaceGenerationService
):
    return TargetRuntimeRestrictedWorkspaceGenerationService()


def generate_target_runtime_restricted_workspace(
    *,
    request: TargetRuntimeRestrictedWorkspaceGenerationRequest,
    service: TargetRuntimeRestrictedWorkspaceGenerationService | None = None,
) -> TargetRuntimeRestrictedWorkspaceGenerationResult:
    selected_service = (
        service or default_target_runtime_restricted_workspace_generation_service()
    )
    return selected_service.generate(request)


__all__ = [
    "RESTRICTED_WORKSPACE_REQUIRED_TEMPLATE_IDS",
    "TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_MODE",
    "TARGET_RUNTIME_RESTRICTED_WORKSPACE_GENERATION_VERSION",
    "TargetRuntimeRestrictedWorkspaceFileRecord",
    "TargetRuntimeRestrictedWorkspaceGenerationRequest",
    "TargetRuntimeRestrictedWorkspaceGenerationResult",
    "TargetRuntimeRestrictedWorkspaceGenerationService",
    "default_target_runtime_restricted_workspace_generation_service",
    "generate_target_runtime_restricted_workspace",
]

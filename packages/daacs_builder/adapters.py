"""Adapters between Workbench contracts and DAACS-style inputs."""

from __future__ import annotations

import re
from typing import Any
from pathlib import Path
from urllib.parse import unquote

from packages.core.pathing import PathBoundaryError, normalize_public_relative_path
from packages.core.schemas import (
    BuildSpec,
    ImplementationBrief,
    PlanningBlueprint,
    PRDPackage,
    SpecApproval,
    VerificationReport,
    stable_contract_hash,
)


RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,80}$")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return slug or "agentic-app"


def _validate_run_id(run_id: str) -> str:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id contains unsupported characters")
    if ".." in run_id or "/" in run_id or "\\" in run_id:
        raise ValueError("run_id must not contain path traversal segments")
    return run_id


def _pascal_case(value: str) -> str:
    words = [word for word in re.split(r"[^A-Za-z0-9]+", value) if word]
    return "".join(word[:1].upper() + word[1:].lower() for word in words) or "WorkItem"


def _pluralize(resource: str) -> str:
    if resource.endswith("s"):
        return resource
    if resource.endswith("y") and len(resource) > 1:
        return f"{resource[:-1]}ies"
    return f"{resource}s"


def _resource_specs(blueprint: PlanningBlueprint, *, max_resources: int = 4) -> list[dict[str, str]]:
    source_features = [feature for feature in blueprint.features if str(feature).strip()]
    if not source_features:
        source_features = ["work item"]

    specs: list[dict[str, str]] = []
    seen: set[str] = set()
    for feature in source_features:
        raw_name = str(feature).strip()
        resource = _pluralize(_slugify(raw_name))
        if resource in seen:
            continue
        seen.add(resource)
        specs.append(
            {
                "feature": raw_name,
                "resource": resource,
                "model": _pascal_case(resource[:-1] if resource.endswith("s") else resource),
            }
        )
        if len(specs) >= max_resources:
            break
    return specs


def _build_api_spec(blueprint: PlanningBlueprint) -> dict[str, Any]:
    endpoints: list[dict[str, Any]] = [
        {
            "method": "GET",
            "path": "/api/v1/health",
            "description": "Health check endpoint for generated backend readiness.",
            "request_body": {},
            "response": {"status": "ok", "service": "string"},
        }
    ]
    data_models: list[dict[str, Any]] = []

    for spec in _resource_specs(blueprint):
        resource = spec["resource"]
        model = spec["model"]
        feature = spec["feature"]
        endpoints.extend(
            [
                {
                    "method": "GET",
                    "path": f"/api/v1/{resource}",
                    "description": f"List records supporting the planned feature: {feature}",
                    "request_body": {},
                    "response": {"items": [model], "count": "integer"},
                },
                {
                    "method": "POST",
                    "path": f"/api/v1/{resource}",
                    "description": f"Create a record for the planned feature: {feature}",
                    "request_body": {
                        "title": "string",
                        "description": "string",
                        "status": "string",
                    },
                    "response": {"id": "string", "status": "created"},
                },
            ]
        )
        data_models.append(
            {
                "name": model,
                "source_feature": feature,
                "fields": {
                    "id": "string",
                    "title": "string",
                    "description": "string",
                    "status": "string",
                    "created_at": "datetime",
                },
            }
        )

    return {
        "version": "v1",
        "base_url": "http://localhost:8080",
        "endpoints": endpoints,
        "data_models": data_models,
        "evidence_summary": [
            {
                "title": item.get("title", "Evidence"),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
            }
            for item in blueprint.evidence[:5]
        ],
    }


def _build_frontend_spec(blueprint: PlanningBlueprint, api_spec: dict[str, Any]) -> dict[str, Any]:
    api_calls = [
        f"{endpoint.get('method', 'GET')} {endpoint.get('path', '')}"
        for endpoint in api_spec.get("endpoints", [])
    ]
    components = ["AppShell", "VerificationStatus", "EvidencePanel"]
    components.extend(
        f"{_pascal_case(spec['resource'])}Panel" for spec in _resource_specs(blueprint)
    )
    visual_requirements = [
        {
            "section_number": artifact.get("section_number"),
            "visual_type": (artifact.get("meta") or {}).get("visual_type") or artifact.get("visual_type"),
            "purpose": (artifact.get("meta") or {}).get("purpose") or artifact.get("purpose"),
        }
        for artifact in blueprint.visual_artifacts
        if isinstance(artifact, dict)
    ]
    return {
        "pages": ["Dashboard", "Evidence", "Verification"],
        "components": list(dict.fromkeys(components)),
        "api_calls": api_calls,
        "state_management": "React local state with explicit loading and error states",
        "visual_requirements": visual_requirements,
        "content_sections": blueprint.features[:8],
    }


def _acceptance_criteria(api_spec: dict[str, Any], frontend_spec: dict[str, Any]) -> list[str]:
    endpoint_criteria = [
        f"Backend implements {endpoint['method']} {endpoint['path']}."
        for endpoint in api_spec.get("endpoints", [])
    ]
    frontend_criteria = [
        f"Frontend calls {api_call}."
        for api_call in frontend_spec.get("api_calls", [])
    ]
    return endpoint_criteria + frontend_criteria + [
        "Generated files stay inside the run workspace.",
        "VerificationReport records generated backend and frontend file counts.",
    ]


def _verification_contract(build_spec: BuildSpec) -> dict[str, Any]:
    endpoints = build_spec.api_spec.get("endpoints", [])
    api_calls = build_spec.frontend_spec.get("api_calls", [])
    return {
        "source_blueprint_title": build_spec.source_blueprint_title,
        "constraints": build_spec.constraints,
        "acceptance_criteria": build_spec.acceptance_criteria,
        "api_endpoint_count": len(endpoints),
        "frontend_api_call_count": len(api_calls),
        "data_model_count": len(build_spec.api_spec.get("data_models", [])),
        "required_backend_endpoints": [
            f"{endpoint.get('method', 'GET')} {endpoint.get('path', '')}" for endpoint in endpoints
        ],
        "required_frontend_calls": api_calls,
    }


def _daacs_tasks(build_spec: BuildSpec) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    if build_spec.backend_required:
        tasks.append(
            {
                "id": "backend-contract",
                "role": "backend",
                "summary": "Implement API endpoints and data models from BuildSpec.",
                "endpoint_count": len(build_spec.api_spec.get("endpoints", [])),
                "data_model_count": len(build_spec.api_spec.get("data_models", [])),
            }
        )
    if build_spec.frontend_required:
        tasks.append(
            {
                "id": "frontend-contract",
                "role": "frontend",
                "summary": "Implement UI components and API calls from BuildSpec.",
                "component_count": len(build_spec.frontend_spec.get("components", [])),
                "api_call_count": len(build_spec.frontend_spec.get("api_calls", [])),
            }
        )
    tasks.append(
        {
            "id": "verification-contract",
            "role": "verifier",
            "summary": "Verify generated files against acceptance criteria and path boundaries.",
            "acceptance_criteria_count": len(build_spec.acceptance_criteria),
        }
    )
    return tasks


def implementation_brief_from_prd_package(
    prd_package: PRDPackage,
    build_spec: BuildSpec,
) -> ImplementationBrief:
    """Create the DAACS-readable handoff brief after PRD and BuildSpec creation."""
    prd_package.validate()
    build_spec.validate()
    build_spec_payload = build_spec.to_dict()
    build_spec_hash = stable_contract_hash(build_spec_payload)
    brief = ImplementationBrief(
        app_name=build_spec.app_name,
        build_spec_hash=build_spec_hash,
        prd_package=prd_package,
        build_spec=build_spec_payload,
        daacs_tasks=_daacs_tasks(build_spec),
        handoff_summary=(
            f"DAACS may plan implementation for {build_spec.app_name} only after "
            f"user approval of BuildSpec hash {build_spec_hash}."
        ),
        constraints=build_spec.constraints
        + [
            "Do not start DAACS live execution before dry-run plan approval.",
            "Keep PRD approval separate from live runner ApprovalRecord.",
        ],
    )
    brief.validate()
    return brief


def create_spec_approval(
    implementation_brief: ImplementationBrief,
    *,
    approval_id: str,
    approved: bool,
    requested_changes: list[str] | None = None,
    approver_role: str = "user",
) -> SpecApproval:
    """Create a sanitized approval or requested-change record for the brief."""
    implementation_brief.validate()
    approval = SpecApproval(
        approval_id=approval_id,
        approved=approved,
        approved_build_spec_hash=implementation_brief.build_spec_hash if approved else "",
        approval_scope=["prd_package", "implementation_brief", "build_spec", "daacs_build"]
        if approved
        else ["prd_package", "implementation_brief", "build_spec"],
        requested_changes=requested_changes or [],
        approver_role=approver_role,
    )
    approval.validate()
    return approval


def ensure_implementation_approved(
    implementation_brief: ImplementationBrief | None,
    approval: SpecApproval | None,
) -> None:
    """Fail closed unless the approval matches the current brief hash."""
    if implementation_brief is None:
        raise ValueError("implementation_brief is required before DAACS handoff")
    implementation_brief.validate()
    if approval is None:
        raise ValueError("spec approval is required before DAACS handoff")
    approval.validate()
    if not approval.approved:
        raise ValueError("spec approval is not approved")
    if approval.approved_build_spec_hash != implementation_brief.build_spec_hash:
        raise ValueError("approval hash does not match implementation brief")


def _normalize_generated_file_path(namespace: str, filename: str) -> str:
    decoded = unquote(str(filename).strip())
    if not decoded:
        raise PathBoundaryError("generated filename is required")
    if "\x00" in decoded:
        raise PathBoundaryError("null byte is not allowed in generated filename")
    candidate = Path(decoded)
    if candidate.is_absolute() or candidate.drive:
        raise PathBoundaryError("generated filename must be relative")
    if any(part == ".." for part in re.split(r"[\\/]+", decoded)):
        raise PathBoundaryError("generated filename must not contain parent traversal")
    normalized = normalize_public_relative_path(f"{namespace}/{decoded}")
    if not normalized.startswith(f"{namespace}/"):
        raise PathBoundaryError("generated filename escapes its namespace")
    return normalized


def planning_to_build_spec(blueprint: PlanningBlueprint) -> BuildSpec:
    """Create a deterministic DAACS BuildSpec from a planning blueprint."""
    blueprint.validate()
    app_name = _slugify(blueprint.title)
    feature_lines = "\n".join(f"- {feature}" for feature in blueprint.features)
    evidence_lines = "\n".join(
        f"- {item.get('title', 'Evidence')}: {item.get('snippet') or item.get('url', 'no-url')}"
        for item in blueprint.evidence[:5]
    )
    visual_lines = "\n".join(
        f"- {(item.get('meta') or {}).get('visual_type') or item.get('visual_type', 'visual')}: "
        f"{(item.get('meta') or {}).get('purpose') or item.get('purpose', 'No purpose provided')}"
        for item in blueprint.visual_artifacts[:5]
        if isinstance(item, dict)
    )
    goal = (
        f"Build an application for: {blueprint.problem}\n\n"
        f"Core features:\n{feature_lines or '- Define a minimal usable workflow'}\n\n"
        f"Research evidence:\n{evidence_lines or '- No external evidence attached'}\n\n"
        f"Visual requirements:\n{visual_lines or '- No visual artifact requirements attached'}"
    )
    api_spec = _build_api_spec(blueprint)
    frontend_spec = _build_frontend_spec(blueprint, api_spec)

    spec = BuildSpec(
        app_name=app_name,
        goal=goal,
        backend_required=True,
        frontend_required=True,
        api_spec=api_spec,
        frontend_spec=frontend_spec,
        constraints=[
            "Generate code only inside the run workspace.",
            "Do not include secrets in generated files or logs.",
            "Keep generated API routes aligned with the BuildSpec contract.",
            "Do not make live provider calls during fixture/offline verification.",
        ],
        acceptance_criteria=_acceptance_criteria(api_spec, frontend_spec),
        source_blueprint_title=blueprint.title,
    )
    spec.validate()
    return spec


def build_spec_to_daacs_initial_state(
    build_spec: BuildSpec,
    *,
    run_id: str,
    project_dir: str | None = None,
    config: dict[str, Any] | None = None,
    implementation_brief: ImplementationBrief | None = None,
    approval: SpecApproval | None = None,
    require_approval: bool = False,
) -> dict[str, Any]:
    """Map a BuildSpec to a DAACS-compatible initial state without importing DAACS."""
    build_spec.validate()
    if require_approval:
        ensure_implementation_approved(implementation_brief, approval)
    exec_config = (config or {}).get("execution", {})
    cli_config = (config or {}).get("cli_assistant", {})
    now = "offline-fixture"
    safe_run_id = _validate_run_id(run_id)
    safe_project_dir = normalize_public_relative_path(project_dir or f"examples/demo-projects/{safe_run_id}")
    orchestrator_plan = (
        f"Implement {build_spec.app_name} from BuildSpec. "
        f"Backend endpoints: {len(build_spec.api_spec.get('endpoints', []))}. "
        f"Frontend API calls: {len(build_spec.frontend_spec.get('api_calls', []))}."
    )
    return {
        "session_id": safe_run_id,
        "initial_goal": build_spec.goal,
        "current_goal": build_spec.goal,
        "project_dir": safe_project_dir,
        "llm_sources": {},
        "mode": exec_config.get("mode", "test"),
        "parallel_execution": exec_config.get("parallel_execution", False),
        "cli_assistant": cli_config.get("type", "codex"),
        "cli_assistant_available": False,
        "iteration_count": 0,
        "max_iterations": exec_config.get("max_iterations", 10),
        "max_subgraph_iterations": exec_config.get("max_subgraph_iterations", 2),
        "consecutive_failures": 0,
        "max_failures": exec_config.get("max_failures", 5),
        "orchestrator_plan": orchestrator_plan,
        "needs_backend": build_spec.backend_required,
        "needs_frontend": build_spec.frontend_required,
        "api_spec": build_spec.api_spec,
        "frontend_spec": build_spec.frontend_spec,
        "constraints": build_spec.constraints,
        "acceptance_criteria": build_spec.acceptance_criteria,
        "source_blueprint_title": build_spec.source_blueprint_title,
        "implementation_brief_hash": implementation_brief.to_dict()["brief_hash"]
        if implementation_brief is not None
        else "",
        "approved_build_spec_hash": approval.approved_build_spec_hash if approval is not None else "",
        "spec_approval_id": approval.approval_id if approval is not None else "",
        "spec_approval_status": "approved" if approval is not None and approval.approved else "missing",
        "build_contract": _verification_contract(build_spec),
        "backend_files": {},
        "backend_status": "pending",
        "backend_needs_rework": False,
        "backend_subgraph_iterations": 0,
        "backend_logs": [],
        "backend_action_type": None,
        "backend_test_result": "",
        "frontend_files": {},
        "frontend_status": "pending",
        "frontend_needs_rework": False,
        "frontend_subgraph_iterations": 0,
        "frontend_logs": [],
        "frontend_action_type": None,
        "frontend_test_result": "",
        "orchestrator_judgment": "",
        "compatibility_verified": False,
        "compatibility_issues": [],
        "endpoint_analysis": {},
        "recommendations": [],
        "needs_rework": False,
        "next_actions": [],
        "failure_type": None,
        "failure_summary": [],
        "turn_history": [
            {
                "event": "build_spec_mapped",
                "source_blueprint_title": build_spec.source_blueprint_title,
                "acceptance_criteria_count": len(build_spec.acceptance_criteria),
                "approval_required": require_approval,
                "spec_approval_status": "approved" if approval is not None and approval.approved else "missing",
            }
        ],
        "rework_history": [],
        "final_status": "partial",
        "stop_reason": "",
        "all_files": {},
        "current_phase": "spec_ready",
        "completed_phases": ["build_spec_created"],
        "created_at": now,
        "updated_at": now,
        "total_duration_seconds": 0.0,
    }


def verification_report_from_daacs_output(
    *,
    run_id: str,
    daacs_output: dict[str, Any],
) -> VerificationReport:
    """Create a neutral verification report from DAACS-style output."""
    backend_files = list((daacs_output.get("backend_files") or {}).keys())
    frontend_files = list((daacs_output.get("frontend_files") or {}).keys())
    issues = daacs_output.get("compatibility_issues") or []
    generated_files = [
        _normalize_generated_file_path("backend", name) for name in backend_files
    ] + [_normalize_generated_file_path("frontend", name) for name in frontend_files]
    passed = bool(daacs_output.get("compatibility_verified")) and not issues
    return VerificationReport(
        run_id=run_id,
        passed=passed,
        checks=[
            {"name": "compatibility_verified", "passed": bool(daacs_output.get("compatibility_verified"))},
            {"name": "backend_files_generated", "passed": bool(backend_files), "count": len(backend_files)},
            {"name": "frontend_files_generated", "passed": bool(frontend_files), "count": len(frontend_files)},
        ],
        errors=[str(issue) for issue in issues],
        generated_files=generated_files,
        metrics={
            "backend_file_count": len(backend_files),
            "frontend_file_count": len(frontend_files),
            "issue_count": len(issues),
        },
    )

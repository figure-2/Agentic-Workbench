# BuildSpec to DAACSState Contract

## Conclusion

`PlanningBlueprint -> PRDPackage -> ImplementationBrief -> SpecApproval -> BuildSpec -> DAACSState` is now a deterministic offline contract. It still does not execute DAACS, spawn CLI agents, call LLMs, install packages, or start local servers.

## Contract Flow

```text
PlanningBlueprint
  -> feature/resource extraction
  -> PRDPackage for human review
  -> versioned REST API contract
  -> frontend API call contract
  -> acceptance criteria
  -> ImplementationBrief for DAACS handoff
  -> SpecApproval gate
  -> DAACS-compatible initial state
```

## Mapping Rules

| Source | Target | Rule |
|---|---|---|
| `PlanningBlueprint.title` | `BuildSpec.app_name` | slugified ASCII app name |
| `PlanningBlueprint.problem` | `BuildSpec.goal` | primary build goal |
| `PlanningBlueprint.features` | `api_spec.endpoints` | each feature becomes a resource up to 4 resources |
| `PlanningBlueprint.features` | `api_spec.data_models` | each resource gets a data model |
| `PlanningBlueprint.evidence` | `api_spec.evidence_summary` | sanitized title/url/snippet only |
| `PlanningBlueprint.visual_artifacts` | `frontend_spec.visual_requirements` | structured visual requirements |
| `PlanningBlueprint` + `BuildSpec` | `PRDPackage` | PRD markdown, features, API requirements, entities, visual requirements, acceptance criteria |
| `PRDPackage` + `BuildSpec` | `ImplementationBrief` | DAACS task manifest plus stable `build_spec_hash` |
| `ImplementationBrief` + `SpecApproval` | DAACS handoff gate | build state is admitted only when approval hash matches |
| `api_spec.endpoints` | `frontend_spec.api_calls` | all endpoints become frontend call obligations |
| `BuildSpec.acceptance_criteria` | `DAACSState.acceptance_criteria` | preserved as additive state field |
| `BuildSpec` summary | `DAACSState.build_contract` | counts and required endpoint/call lists |

## Generated API Shape

- Version prefix: `/api/v1`
- Health endpoint: `GET /api/v1/health`
- Feature resources: `GET /api/v1/{resources}`, `POST /api/v1/{resources}`
- Resource naming: lowercase kebab-case plural

## DAACSState Boundary

The adapter fills DAACS-compatible runtime keys without importing DAACS modules. It sets generated work status to pending and marks `cli_assistant_available=false` for offline fixture mode.

Key mapped groups:

- project/session: `session_id`, `initial_goal`, `current_goal`, `project_dir`
- execution: `mode`, `parallel_execution`, iteration/failure limits
- planning: `orchestrator_plan`, `needs_backend`, `needs_frontend`, `api_spec`, `frontend_spec`
- build status: backend/frontend pending fields
- verification context: `constraints`, `acceptance_criteria`, `source_blueprint_title`, `build_contract`
- approval context: `implementation_brief_hash`, `approved_build_spec_hash`, `spec_approval_id`, `spec_approval_status`
- lifecycle: `current_phase`, `completed_phases`, `turn_history`

## Safety Rules

- `run_id` must be a simple identifier and cannot contain path traversal, separators, absolute paths, or null bytes.
- `project_dir` is normalized as a public relative path.
- Generated file paths in `VerificationReport` are normalized through the shared path boundary.
- Generated file names must remain inside their backend/frontend namespace. Parent traversal and URL-encoded traversal are rejected, not silently normalized.
- This contract does not perform file writes, network calls, subprocess calls, package installation, or live LLM calls.
- When `require_approval=true`, `build_spec_to_daacs_initial_state` fails closed unless the `SpecApproval` matches the current `ImplementationBrief.build_spec_hash`.
- `SpecApproval` is only content approval for PRD/brief/BuildSpec. It is not live runner execution approval.

## Known Limits

- This does not prove generated code quality.
- This does not run DAACS subgraphs.
- This does not verify Solar Pro 3 or any provider output.
- This does not implement live DAACS execution.
- The dry-run runner creates a `RunnerPlan` only; it does not execute DAACS or generate files.
- DAACS itself still has risky execution surfaces that must stay behind explicit offline/live boundaries.

# AW-PARITY-00 Public API / Fixture Boundary

## Scope

Block raw public exposure in the fixture API and make fixture/synthetic mode
machine-readable before source identity parity fixtures are added.

This is not a live DAACS, Solar Pro 3, or source-runtime integration step.

## Current Implementation

- `POST /api/v1/runs` no longer returns `WorkflowSession.to_dict()` directly.
- `packages.core.public_projection` projects sessions into sanitized read models:
  run metadata, prompt contract hash, artifact metadata, fixture boundary flags,
  and side-effect counters only.
- Fixture API responses include:
  - `runtime_mode=fixture`
  - `approval_lifecycle=synthetic`
  - `approval_mode=fixture`
  - `fixture_mode=true`
  - `durable_user_approval=false`
- Fixture planner no longer copies `IdeaBrief.raw_prompt` into
  `PlanningBlueprint.problem`.
- Public denylist now includes raw prompt, raw log, file body, provider payload,
  request/response payload, and approval authorization material field names.
- Public claim scanner now blocks unsupported external-provider,
  DAACS source-runtime, Solar live-outcome, direct source-runtime, and generated
  app production-outcome claim patterns.

## Acceptance Results

| Gate | Result |
|---|---|
| `python -m pytest tests -q` | 255 passed |
| API/public response `raw_prompt` exposure | 0 in covered fixtures |
| raw log/file body/provider payload/approval auth material exposure | 0 in covered fixtures |
| `WorkflowSession.to_dict()` direct public API return | blocked by API projection test |
| fixture/synthetic mode marker in API response | covered |
| fixture planner raw prompt propagation | blocked |
| external provider outcome claim scan | covered |
| DAACS/source-runtime outcome claim scan | covered |
| Solar Pro 3 live call | 0 |
| DAACS live call | 0 |

## Test Commands

```powershell
python -m compileall packages apps tests
python -m pytest tests/unit/test_public_projection.py tests/integration/test_api_public_projection.py tests/unit/test_claims_and_evidence.py -q
python -m pytest tests -q
```

## Non-Current Claims

- Public API projection does not prove live provider integration.
- Public API projection does not prove DAACS source-runtime outcome.
- Fixture approval is not durable user approval.
- Sanitized artifact metadata is not generated source delivery.
- This is not production API hardening or a security certification.

## Next Step

`AW-PARITY-01` should add source identity golden path fixtures after this public
boundary. It should prove identity preservation through sanitized artifact
chains, not source runtime reproduction.

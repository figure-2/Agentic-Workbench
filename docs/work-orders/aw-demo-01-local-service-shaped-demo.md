# AW-DEMO-01 Work Order: Local Service-Shaped Demo

## Conclusion

`AW-DEMO-01` is the recommended work order after `AW-API-06` is implemented.
Its purpose is to prove one local service-shaped Idea-to-App workflow without
opening Solar Pro 3, DAACS target runtime execution, provider calls, CLI agent
execution, package installation, server start, or unrestricted file writes.

This work order is a demo integration step, not a live execution step.

## Implementation Unit

```text
id: AW-DEMO-01
depends_on: AW-API-06
scope: local service-shaped demo flow over composed run read model
risk_level: medium
rollback_plan: demo route/script/docs 제거, AW-API-06 composed read model 유지
```

## Senior Review Decision

Product lens:

- The demo should show the product's identity in one understandable path:
  idea, planning artifacts, approval boundary, dry-run runner plan,
  verification report, and run/evidence read model.
- The demo should feel like a future service flow, but must not claim generated
  app delivery or live execution.

Architecture lens:

- The demo must consume `AW-API-06` composed run read model instead of directly
  reading individual repositories from demo code.
- The demo may configure local SQLite stores server-side, but request payloads
  must not choose repository roots or local paths.

Security lens:

- The demo must keep the same raw exposure boundary as the API:
  no raw prompt in public output, no raw artifact body, no raw logs, no provider
  payloads, no runtime payloads, no raw approval authorization material.
- Solar Pro 3 and DAACS target runtime remain blocked.

Data lens:

- The demo should persist sanitized canonical run/artifact rows and sanitized
  evidence rows to local configured repositories.
- The demo should verify that the composed read model links these rows by
  `run_id`, hashes, and counts only.

Test lens:

- The demo should be covered by integration or smoke tests using temporary local
  stores.
- The test should prove that the read model is sufficient for a user-facing demo
  without inspecting private repository internals.

Audit lens:

- Public wording must call this a local fixture/dry-run demo.
- Do not describe it as live provider integration, DAACS runtime execution,
  generated app success, production monitoring, or hosted service behavior.

## Scope

Build one repeatable local demo path around the composed run read model:

```text
User Idea
-> POST /api/v1/runs
-> sanitized PlanningBlueprint / PRDPackage / BuildSpec / ImplementationBrief
-> synthetic or fixture approval boundary
-> dry-run RunnerPlan
-> VerificationReport
-> persisted canonical run/artifact rows
-> persisted sanitized evidence rows
-> GET /api/v1/runs/{run_id}
-> composed public run/evidence response
```

The demo may be implemented as one or more of:

- a test fixture scenario
- a local script under `examples/`
- a demo-specific API test helper
- a README/demo note with exact local commands

The recommended first implementation is a test-backed local script or fixture,
not a UI. UI should wait until the API read model is stable.

## Non-Scope

- No Solar Pro 3 API call.
- No Upstage SDK import requirement.
- No DAACS target runtime execution.
- No original DIV live graph execution.
- No CLI agent execution.
- No `npm install`, package install, server start, or generated app build.
- No unrestricted filesystem write.
- No production database or hosted persistence claim.
- No UI migration from source projects.

## Recommended Demo Scenario

Use one representative idea that exercises both source identities:

```text
Build a small task collaboration app for a study group.
It needs task creation, assignee tracking, status changes, due dates,
and a simple dashboard for incomplete work.
```

Expected preserved identity:

- DIV identity:
  - idea structure
  - PRD sections
  - user flow intent
  - acceptance criteria
  - evidence/assumption summary
- DAACS identity:
  - backend/frontend/API split
  - execution plan projection
  - verification criteria
  - replanning/next-action placeholder
  - runner/provider boundary markers

## Acceptance Tests

- Demo path creates one run through `POST /api/v1/runs`.
- Demo path persists sanitized canonical run/artifact rows when configured.
- Demo path persists sanitized runner/report/audit evidence rows when
  configured.
- `GET /api/v1/runs/{run_id}` returns composed canonical run state and evidence
  summary.
- `GET /api/v1/runs/{run_id}/artifacts` returns artifact metadata only.
- Artifact count is at least 3.
- Same `run_id` links canonical run, artifacts, runner plan, verification
  report, and audit event evidence.
- DIV identity signals are visible as sanitized planning/document/evidence
  summaries.
- DAACS identity signals are visible as sanitized backend/frontend/API,
  runner-plan, verifier, and next-action summaries.
- Raw prompt leakage count is 0.
- Raw artifact body leakage count is 0.
- Raw log/file/provider/runtime payload leakage count is 0.
- Raw approval authorization material leakage count is 0.
- Solar Pro 3 call count is 0.
- DAACS target runtime call count is 0.
- Re-running the demo with a fresh temporary store is deterministic for
  structural counts and hash presence.
- Existing regression suite remains green.

## Suggested Files

- `examples/demo-service-flow/README.md`
- `examples/demo-service-flow/demo_input.json`
- `examples/demo-service-flow/run_local_demo.py`
- `tests/smoke/test_local_service_demo.py`
- `docs/evals/aw-demo-01-local-service-shaped-demo.md`
- `docs/metrics.md`
- `README.md`

If the implementation can be completed without adding a script, prefer a smoke
test plus a short example README first.

## Public Response Requirements

The demo response should include:

- `projection_version`
- `run_id`
- `runtime_mode`
- `fixture_mode`
- `run.stage`
- `run.status`
- `run.prompt_contract_hash`
- `run.idea_summary`
- artifact metadata and counts
- evidence summary counts
- linkage checks
- zero-call execution boundary
- claim boundary markers

The demo response must not include:

- `.env` values
- API key values
- internal absolute paths
- local DB root paths
- raw prompts
- raw provider payloads
- raw logs
- raw file bodies
- raw generated source bodies
- raw approval signatures
- raw nonces

## Implementation Notes

- Use configured local repositories through server-side app construction.
- Use temporary stores in tests.
- Prefer deterministic fixture data.
- Reuse existing public projection and sanitizer assertions.
- Keep demo output small enough to inspect manually.
- Keep source-project parity references in internal SoT only.
- Public demo docs should describe current behavior as local fixture/dry-run.

## Verification Commands

```powershell
python -m compileall packages apps tests
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Follow-Up Work

```text
AW-DEMO-02
depends_on: AW-DEMO-01
scope: minimal user-facing run status surface over the composed read model
risk_level: medium
rollback_plan: UI/demo surface 제거, AW-DEMO-01 API/script demo 유지
```

```text
AW-LIVE-00
depends_on: AW-DEMO-01
scope: live-open checklist and policy ADR before Solar Pro 3 or DAACS runtime calls
risk_level: high
rollback_plan: live-open policy 문서 제거, all live calls remain blocked
```

## External Audit Checklist

- The demo does not imply real provider output.
- The demo does not imply DAACS target runtime success.
- The demo does not imply generated app delivery.
- The demo does not expose raw prompt or raw evidence.
- The demo proves the value proposition through artifact chain visibility.
- The demo remains consistent with ADR 0001 and the public claim boundary.

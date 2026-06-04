# AW-MVP-01 Work Order: Service-Shaped Vertical Slice

## Conclusion

`AW-MVP-01` shifts the project from adding more no-call gates to proving one
reviewable service path:

```text
Idea
-> SoT/PRD/ImplementationBrief-style artifacts
-> synthetic approval
-> dry-run RunnerPlan
-> VerificationReport
-> public read-model summary
```

This is still a local dry-run service baseline. It does not call Solar Pro 3,
load provider secrets, import provider SDKs, run the DAACS target runtime, or
claim delivered application output.

## Implementation Unit

```text
id: AW-MVP-01
depends_on:
  - AW-PARITY-01C
  - AW-PERSIST-08
  - AW-LIVE-CHAIN-04
scope: service-shaped local end-to-end demo baseline
risk_level: high
rollback_plan: remove AW-MVP-01 API/demo/test/docs additions and keep AW-DEMO-03/AW-LIVE-CHAIN-04
```

## Senior Review Decision

Product lens:

- The next useful milestone is a first-time-reviewable path, not another
  hidden safety boundary.
- The user-facing story is: rough idea becomes implementation-ready artifacts,
  then a dry-run execution plan and verification summary.

Architecture lens:

- Keep canonical run state and evidence rows separate.
- Add the missing verification-specific read model rather than returning raw
  repository rows or overloading the composed run endpoint.

Security lens:

- Preserve the existing no-call boundary.
- Public output must expose only hashes, counts, status, reasons, and summaries.

QA lens:

- One representative golden path must cover all seven stages.
- The demo must fail if verification evidence or run linkage disappears.

Audit lens:

- Public wording must say local dry-run service baseline.
- Do not describe this as hosted behavior, provider outcome, source-runtime
  recreation, or generated application delivery.

## Acceptance Tests

- `POST /api/v1/runs` creates one sanitized run.
- `GET /api/v1/runs/{run_id}` returns composed canonical run/evidence summary.
- `GET /api/v1/runs/{run_id}/artifacts` returns artifact metadata only.
- `GET /api/v1/runs/{run_id}/verification` returns verification evidence as a
  sanitized public read model.
- Stage coverage is `7/7`: Idea, PlanningBlueprint, PRDPackage,
  ImplementationBrief, Approval, RunnerPlan, VerificationReport.
- Artifact linkage by `run_id` is `100%`.
- Raw prompt, raw log, raw file body, provider body, runtime body, and raw
  authorization material exposure findings remain `0`.
- Solar Pro 3 calls remain `0`.
- DAACS target runtime calls remain `0`.
- Unavailable evidence store returns a blocked public projection.

## Suggested Files

- `apps/api/agentic_workbench_api/services/evidence_read_model.py`
- `apps/api/agentic_workbench_api/main.py`
- `examples/demo-service-flow/run_local_demo.py`
- `examples/demo-service-flow/render_status_surface.py`
- `examples/demo-service-flow/render_static_ui_shell.py`
- `tests/smoke/test_mvp_service_flow.py`
- `docs/evals/aw-mvp-01-service-shaped-vertical-slice.md`
- `docs/metrics.md`

## Quantitative Targets

| Metric | Target |
|---|---:|
| Golden path scenario count | 1 |
| Stage coverage | 7/7 |
| Artifact linkage by `run_id` | 100% |
| Forbidden public exposure findings | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |
| Public claim drift findings | 0 |

## Follow-Up

After this closes, the next practical choices are:

- `AW-SOLAR-01`: provider-backed planner spike, still behind explicit policy
  and cost controls.
- `AW-DAACS-RUNTIME-00`: DAACS target runtime sandbox design before any target
  workspace execution.

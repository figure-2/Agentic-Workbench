# AW-DEMO-02 Work Order: Minimal Run Status Surface

## Conclusion

`AW-DEMO-02` is the recommended implementation unit after `AW-DEMO-01`.
Its purpose is to turn the composed run read model into a human-readable
status surface so a first-time reviewer can understand the workflow without
reading raw API JSON.

This is a local demo surface, not a live runtime or production UI.

## Implementation Unit

```text
id: AW-DEMO-02
depends_on: AW-DEMO-01, AW-API-06
scope: minimal user-facing run status surface over the composed read model
risk_level: medium
rollback_plan: status surface script/docs/tests 제거, AW-DEMO-01 API/script demo 유지
```

## Senior Review Decision

Product lens:

- The project now proves the artifact chain through API JSON, but a new reader
  still has to interpret nested response fields.
- The next step should show the product story in one readable status report:
  run state, artifact chain, DIV identity, DAACS identity, evidence, and
  blocked live boundaries.

Architecture lens:

- The status surface must consume `AW-DEMO-01` / `AW-API-06` public projections.
- It must not read SQLite tables directly.
- It must not become a separate source of truth.

Security lens:

- The status surface must not print raw prompt, raw artifact bodies, raw logs,
  provider payloads, runtime payloads, raw approval signatures, raw nonces,
  `.env` values, or local database paths.

Data lens:

- The surface should display only counts, safe labels, artifact kinds, boolean
  identity signals, zero-call metrics, and claim boundary markers.

Test lens:

- A smoke test should verify that the rendered surface is understandable and
  does not leak forbidden raw fields.

Audit lens:

- The wording must describe the result as local fixture/dry-run output.
- It must not imply Solar Pro 3 integration, DAACS target runtime execution,
  generated app delivery, hosted deployment, or production monitoring.

## Scope

Build a minimal local status surface for the current demo:

```text
run_local_demo.py
-> sanitized summary dict
-> render_status_surface(summary)
-> Markdown/CLI report
```

The report should include:

- run id
- projection version
- runtime mode
- artifact count and artifact kinds
- DIV identity signals
- DAACS identity signals
- evidence summary counts
- repository boundary status
- execution boundary zero-call metrics
- claim boundary statement
- recommended next action

## Non-Scope

- No React, Next.js, or web dashboard yet.
- No browser automation.
- No live provider call.
- No Upstage/Solar Pro 3 SDK import.
- No DAACS target runtime execution.
- No original DIV live graph execution.
- No local server start.
- No generated app build.
- No raw artifact body rendering.
- No persistent report file unless a later explicit task asks for exports.

## Acceptance Tests

- `render_status_surface(summary)` returns a Markdown/text report.
- Report contains `Agentic Workbench Run Status`.
- Report contains run id, artifact count, DIV identity, DAACS identity, evidence
  summary, execution boundary, claim boundary, and next action sections.
- Report marks Solar Pro 3 calls as `0`.
- Report marks DAACS target runtime calls as `0`.
- Report does not include raw prompt text.
- Report does not include raw artifact bodies.
- Report does not include provider/runtime payload keys.
- Report does not include local temp/store paths.
- Report does not include raw approval signature or raw nonce values.
- Existing demo smoke tests remain green.
- Full regression suite remains green.

## Suggested Files

- `examples/demo-service-flow/render_status_surface.py`
- `examples/demo-service-flow/README.md`
- `tests/smoke/test_run_status_surface.py`
- `docs/evals/aw-demo-02-minimal-run-status-surface.md`
- `docs/metrics.md`
- `README.md`

## Recommended Command

```powershell
python examples/demo-service-flow/render_status_surface.py
```

Expected behavior:

- prints a concise Markdown/text report to stdout
- uses local configured projection stores
- does not write files by default
- keeps provider/runtime call counts at 0

## Follow-Up Work

```text
AW-DEMO-03
depends_on: AW-DEMO-02
scope: optional static HTML or lightweight UI shell over the same public run status projection
risk_level: medium
rollback_plan: UI shell 제거, AW-DEMO-02 CLI/Markdown surface 유지
```

```text
AW-LIVE-00
depends_on: AW-DEMO-02
scope: live-open checklist and policy ADR before Solar Pro 3 or DAACS runtime calls
risk_level: high
rollback_plan: live-open policy 문서 제거, all live calls remain blocked
```

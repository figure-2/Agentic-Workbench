# AW-DEMO-03 Work Order: Static UI Shell

## Conclusion

`AW-DEMO-03` is the implementation unit after `AW-DEMO-02` and `AW-LIVE-00`.
Its purpose is to make the local service-shaped demo understandable through a
minimal static HTML shell while reusing the same sanitized public summary.

This is a local static shell, not a hosted dashboard and not live execution.

## Implementation Unit

```text
id: AW-DEMO-03
depends_on: AW-DEMO-02, AW-LIVE-00
scope: optional static UI shell over the public demo summary
risk_level: medium
rollback_plan: static UI script/docs/tests 제거, AW-DEMO-02 CLI/Markdown surface 유지
```

## Senior Review Decision

Product lens:

- `AW-DEMO-02` gives a readable CLI/Markdown summary, but a first-time reviewer
  still benefits from a screen-shaped view.
- The UI should show the product story: idea-to-artifact flow, DIV identity,
  DAACS identity, evidence, zero-call boundary, and live policy state.

Architecture lens:

- The shell must consume the same public summary returned by the local demo.
- It must not query SQLite tables, repository internals, env values, provider
  SDKs, or runtime modules.

Security lens:

- HTML must not include raw prompts, raw artifact bodies, raw logs, provider
  payloads, runtime payloads, raw authorization fields, local store paths, or
  secret values.
- Live policy must be displayed as `closed / eligible only`, and execution
  permission must stay closed.

Data lens:

- The UI model may include counts, artifact kind labels, boolean identity
  signals, zero-call counters, and live-open policy status.
- It must not become a second source of truth.

Test lens:

- Smoke tests should render HTML from the public summary and verify no raw
  leakage, no path echo, and zero provider/runtime calls.

Audit lens:

- The public claim is static local UI over sanitized fixture/dry-run
  projections only.
- It must not claim hosted UI, production monitoring, provider integration, or
  DAACS target runtime outcome.

## Scope

```text
run_local_demo.py
-> sanitized summary dict
-> render_static_ui_shell(summary)
-> static HTML string or explicit output file
```

The shell should include:

- run overview
- artifact count and artifact kinds
- workflow stage rail
- DIV identity signals
- DAACS identity signals
- evidence counts
- execution boundary counters
- live-open policy state
- claim-safe projection marker

## Non-Scope

- No React/Next.js application.
- No local server start.
- No browser-based API calls.
- No provider SDK import.
- No `.env` value read.
- No Solar Pro 3 call.
- No DAACS target runtime call.
- No generated app build.
- No raw artifact rendering.
- No hosted dashboard claim.

## Acceptance Tests

- Static UI uses public summary only.
- HTML contains `AW-DEMO-03` and `public-summary-only` markers.
- HTML shows `closed / eligible only`.
- HTML shows Solar Pro 3 calls as `0`.
- HTML shows DAACS target runtime calls as `0`.
- HTML shows execution permission as closed.
- HTML includes DIV and DAACS identity sections.
- HTML includes artifact and evidence sections.
- HTML has raw prompt/log/body/provider/runtime payload findings `0`.
- HTML has raw approval authorization findings `0`.
- HTML has local path findings `0`.
- Full regression suite remains green.

## Suggested Files

- `examples/demo-service-flow/render_static_ui_shell.py`
- `examples/demo-service-flow/README.md`
- `tests/smoke/test_static_ui_shell.py`
- `docs/evals/aw-demo-03-static-ui-shell.md`
- `docs/metrics.md`
- `README.md`

## Recommended Command

```powershell
python examples/demo-service-flow/render_static_ui_shell.py --output .local/aw-demo-03-static-ui.html
```

## Follow-Up Work

```text
AW-LIVE-01
depends_on: AW-LIVE-00, AW-DEMO-03
scope: disabled-by-default Solar Pro 3 provider adapter design and test harness
risk_level: high
rollback_plan: provider adapter design/test 제거, AW-LIVE-00 policy gate 유지
```

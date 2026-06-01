# AW-LIVE-00 Work Order: Live-Open Policy Gate

## Conclusion

`AW-LIVE-00` is the implementation unit after `AW-DEMO-02`. Its purpose is to
freeze the policy controls required before Solar Pro 3 or DAACS target runtime
work can be proposed.

This is not a provider integration and not a target runtime integration.

## Implementation Unit

```text
id: AW-LIVE-00
depends_on: AW-DEMO-02
scope: fail-closed live-open policy gate before any Solar Pro 3 or DAACS target runtime call
risk_level: high
rollback_plan: live-open policy module/docs/tests 제거, all live/provider/runtime calls remain blocked
```

## Senior Review Decision

Product lens:

- The local demo is understandable enough to show the artifact chain.
- The next risk is claim drift: a reviewer may assume live provider/runtime
  capability exists because the project has fake admission APIs and a local
  status surface.
- Therefore the next unit must define what "ready to open live" means before
  any integration work starts.

Architecture lens:

- Live readiness must be a standalone policy module, not embedded in provider
  or runner execution code.
- A passing decision may mark a surface eligible for a later implementation
  unit, but it must not grant execution permission.

Security lens:

- Env key names may be referenced. Env values must never be read, returned, or
  logged.
- Cost, timeout, sandbox, write allowlist, rollback, redaction, sanitizer, and
  audit controls must be explicit.

Data lens:

- Public output should contain only readiness check names, reason codes, zero
  counters, and claim-boundary markers.
- No raw prompt, raw log, provider payload, runtime payload, signature, nonce,
  approval authorization material, local path, or secret value may appear.

Test lens:

- The policy gate must fail closed on unknown surfaces, missing controls, and
  attempted calls or writes.
- The happy path must still return `allowed_to_execute=false`.

Audit lens:

- Public wording must say readiness policy, not provider/runtime outcome.
- A stored API key is not sufficient to open provider calls.

## Scope

Add a side-effect-free policy evaluator:

```text
LiveOpenRequest
-> evaluate_live_open_request()
-> LiveOpenDecision
```

Required live-open controls:

- approval policy
- replay persistence
- cost/quota guard
- timeout guard
- workspace sandbox
- write allowlist
- rollback plan
- secret redaction
- artifact sanitizer
- audit projection

Supported readiness surfaces:

- `solar_provider`
- `daacs_target_runtime`

## Non-Scope

- No Solar Pro 3 API call.
- No Upstage SDK import.
- No `.env` value read.
- No DAACS target runtime invocation.
- No CLI agent execution.
- No package install.
- No server start.
- No filesystem write as runtime output.
- No live approval UX.
- No production trust root.
- No production key registry.
- No multi-host replay guarantee.

## Acceptance Tests

- Unknown surface is blocked.
- Default request with missing controls is blocked.
- Complete readiness for `solar_provider` references only `UPSTAGE_API_KEY`
  as an env key name.
- Complete readiness for `solar_provider` never reads an env value.
- Complete readiness returns `eligible_for_separate_live_implementation`.
- Complete readiness keeps `allowed_to_execute=false`.
- DAACS target runtime readiness rejects provider env key names.
- Requested provider/runtime/network/write counters greater than zero are
  blocked.
- Public decision output has forbidden public key findings 0.
- Solar Pro 3 call count remains 0.
- DAACS target runtime call count remains 0.
- Existing regression suite remains green.

## Suggested Files

- `packages/core/live_open_policy.py`
- `tests/unit/test_live_open_policy.py`
- `docs/adr/0002-live-open-policy-gate.md`
- `docs/evals/aw-live-00-live-open-policy-gate.md`
- `docs/metrics.md`
- `docs/claim-boundary.md`
- `README.md`

## Follow-Up Work

```text
AW-DEMO-03
depends_on: AW-DEMO-02, AW-LIVE-00
scope: optional static UI shell over the same public projection and live-closed status markers
risk_level: medium
rollback_plan: UI shell 제거, AW-DEMO-02 CLI/Markdown surface 유지
```

```text
AW-LIVE-01
depends_on: AW-LIVE-00
scope: Solar Pro 3 provider adapter design with explicit live approval envelope, still disabled by default
risk_level: high
rollback_plan: provider adapter design 제거, AW-LIVE-00 policy gate 유지
```

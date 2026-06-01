# AW-LIVE-01 Work Order: Disabled Solar Pro 3 Provider Adapter

## Conclusion

`AW-LIVE-01` is the implementation unit after `AW-LIVE-00` and `AW-DEMO-03`.
Its purpose is to define the future Solar Pro 3 provider adapter path while
keeping the adapter disabled and blocked by default.

This is not a Solar Pro 3 API integration.

## Implementation Unit

```text
id: AW-LIVE-01
depends_on: AW-LIVE-00, AW-DEMO-03
scope: disabled-by-default Solar Pro 3 provider adapter design + test harness
risk_level: high
rollback_plan: provider adapter design/test 제거, AW-LIVE-00 policy gate 유지
```

## Senior Review Decision

Product lens:

- The project now has a local static demo surface and a live-open policy gate.
- The next useful step is to show where Solar Pro 3 will enter the system
  without implying that provider execution is available.

Architecture lens:

- The real-path adapter must be separate from `FakeSolarProProvider`.
- The adapter must be registered by provider and mode, so `fake` and `live`
  paths cannot be confused.
- The adapter may return blocked `ProviderResult` objects only.

Security lens:

- The adapter must never read the `UPSTAGE_API_KEY` value.
- The adapter must never import provider SDKs, open network sockets, or perform
  API calls.
- Approval, live-open policy, timeout, cost, and quota controls must be explicit
  before the adapter can move beyond the earliest blocked gates.

Data lens:

- Public output may include adapter id, check names, reason messages, zero-call
  counters, and env key name references only.
- Public output must not include raw prompt, raw provider payload, raw runtime
  payload, signature, nonce, local path, or secret values.

Test lens:

- Tests must prove registration is possible but invocation remains blocked.
- Tests must prove missing approval/live-open policy/config blocks before any
  provider action.

Audit lens:

- Public wording must describe the adapter as disabled and blocked.
- It must not claim model quality, external provider outcome, hosted execution,
  or production readiness.

## Scope

Add:

- `SolarPro3LiveAdapterConfig`
- `DisabledSolarPro3LiveAdapter`
- `ProviderAdapterRegistry`
- unit tests for disabled, missing policy, missing config, fake/live split, and
  no side effects

## Non-Scope

- No Solar Pro 3 API call.
- No Upstage SDK import.
- No `.env` value read.
- No network call.
- No provider response parsing.
- No token/cost metering implementation.
- No production approval UX.
- No production key registry.
- No runtime write.

## Acceptance Tests

- Adapter registration is possible.
- Default invocation is blocked.
- Missing live-open policy is blocked.
- Missing timeout/cost/quota config is blocked.
- Fake provider mode is rejected by the real-path adapter.
- Eligible live-open policy still keeps execution permission closed.
- Env value read count remains `0`.
- Provider SDK import count remains `0`.
- Solar Pro 3 API call count remains `0`.
- Public output forbidden key findings remain `0`.
- Full regression suite remains green.

## Suggested Files

- `packages/daacs_builder/solar_live_adapter.py`
- `tests/unit/test_solar_live_adapter.py`
- `docs/evals/aw-live-01-disabled-solar-provider-adapter.md`
- `docs/metrics.md`
- `README.md`
- `docs/architecture.md`
- `docs/claim-boundary.md`

## Follow-Up Work

```text
AW-LIVE-02
depends_on: AW-LIVE-01
scope: Solar Pro 3 request/response contract fixtures and cost/timeout policy contract, still no API call
risk_level: high
rollback_plan: request/response contract fixtures 제거, AW-LIVE-01 disabled adapter 유지
```

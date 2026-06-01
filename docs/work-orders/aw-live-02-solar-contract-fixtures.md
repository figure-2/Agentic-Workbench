# AW-LIVE-02 Work Order: Solar Pro 3 Contract Fixtures

## Conclusion

`AW-LIVE-02` is the implementation unit after `AW-LIVE-01`. Its purpose is to
define the no-call request/response contracts and cost/timeout policy that a
future Solar Pro 3 adapter must satisfy before provider execution can be
considered.

This is not a Solar Pro 3 API call.

## Implementation Unit

```text
id: AW-LIVE-02
depends_on: AW-LIVE-01
scope: Solar Pro 3 request/response contract fixture + cost/timeout policy contract
risk_level: high
rollback_plan: request/response contract fixture와 policy contract 제거, AW-LIVE-01 유지
```

## Senior Review Decision

Product lens:

- The project now has a disabled provider adapter. The next gap is explaining
  what a future provider request and response are allowed to contain.
- The answer must be a contract fixture, not a provider invocation.

Architecture lens:

- Request contracts must be based on `prompt_contract_hash`, not raw prompt
  text.
- Response projections must contain sanitized summary and hashes only.
- Contract fixture logic should be separate from adapter invocation so tests can
  verify no-call behavior in isolation.

Security lens:

- No `.env` value read.
- No SDK import.
- No network call.
- No raw prompt, source body, provider body, authorization field, or local path
  in public output.

Data lens:

- Public fields may include run id, provider/model names, mode, env key name,
  prompt contract hash, request contract hash, response contract hash, content
  hash, counts, and policy check names.

Test lens:

- Missing timeout, cost, API quota, or token quota must block fixture creation.
- Raw input/body values passed into tests must not appear in serialized public
  output.

Audit lens:

- Public wording must say no-call contract fixture.
- It must not claim response quality, provider success, hosted execution, or
  production provider readiness.

## Scope

Add:

- `SolarCostTimeoutPolicy`
- `SolarRequestContractFixture`
- `SolarResponseProjectionFixture`
- `SolarContractFixtureResult`
- helpers to validate policy, build request fixture, and attach response
  projection fixture

## Non-Scope

- No Solar Pro 3 API call.
- No Upstage SDK import.
- No `.env` value read.
- No network call.
- No provider response parsing.
- No retry execution.
- No cost metering against a real provider.
- No production credential or approval UX.

## Acceptance Tests

- Request fixture uses `prompt_contract_hash` only.
- Missing timeout/cost/API quota/token quota blocks.
- Invalid prompt contract hash blocks.
- Fake mode blocks in the Solar request contract fixture.
- Response projection contains sanitized summary and hashes only.
- Raw prompt/body/provider values do not appear in public output.
- SDK import/env value/API/network calls remain `0`.
- Full regression suite remains green.

## Suggested Files

- `packages/daacs_builder/solar_contracts.py`
- `tests/unit/test_solar_contracts.py`
- `docs/evals/aw-live-02-solar-contract-fixtures.md`
- `docs/metrics.md`
- `README.md`
- `docs/architecture.md`
- `docs/claim-boundary.md`

## Follow-Up Work

```text
AW-LIVE-03
depends_on: AW-LIVE-02
scope: provider request envelope persistence/read-model projection, still no external call
risk_level: high
rollback_plan: provider envelope persistence/read-model 제거, AW-LIVE-02 유지
```

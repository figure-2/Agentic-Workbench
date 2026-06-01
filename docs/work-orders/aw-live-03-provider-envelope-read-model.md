# AW-LIVE-03 Work Order: Provider Envelope Persistence and Read Model

## Conclusion

`AW-LIVE-03` is the implementation unit after `AW-LIVE-02`. Its purpose is to
persist and read sanitized provider request/response envelope evidence as
hashes, counts, and status only.

This is still a no-call boundary. It does not import a provider SDK, read env
values, open network connections, or call Solar Pro 3.

## Implementation Unit

```text
id: AW-LIVE-03
depends_on: AW-LIVE-02
scope: provider request envelope persistence/read-model projection, still no external call
risk_level: high
rollback_plan: provider envelope persistence/read-model 제거, AW-LIVE-02 유지
```

## Senior Review Decision

Product lens:

- The project needs evidence that a future provider request/response envelope
  can be tracked without exposing sensitive material.
- Public wording must say `no-call provider envelope evidence`, not provider
  outcome.

Architecture lens:

- The envelope store should sit after the Solar contract fixture and before any
  future provider adapter execution.
- The stored record may keep provider/model labels internally, but the public
  read model should return only hashes, counts, and status.
- The store should be isolated from approval/replay and runner/report/audit
  repositories so evidence boundaries remain explicit.

Security lens:

- Raw prompt, provider body, provider payload, authorization material, env
  value, SDK import, API call, and network call must remain at 0.
- A corrupted, unavailable, or wrong-schema store must return a blocked public
  read model or fail closed before any provider path can proceed.

Data lens:

- Persist allowed fields only:
  `envelope_id`, `run_id`, provider/model labels, `mode`, `status`,
  `request_contract_hash`, `response_contract_hash`,
  `prompt_contract_hash`, `content_hash`, field counts, policy check count,
  sanitized summary, and timestamp.
- Public read model allowed fields are narrower: envelope id, status, hashes,
  counts, repository boundary status, and zero-call counters.

Test lens:

- Unit tests must prove DB rows contain no raw input/body/provider values.
- Public read model tests must prove the returned shape is hash/count/status
  only.
- Store corruption/unavailability must be tested.

Audit lens:

- Public documents must not say this validates model output, provider quality,
  hosted execution, or production provider readiness.
- The safe claim is that the local harness can persist and read sanitized
  provider envelope evidence.

## Scope

Add:

- `ProviderEnvelopeRecord`
- in-memory provider envelope repository
- SQLite provider envelope store/repository skeleton
- provider envelope public read model
- helper to convert `SolarContractFixtureResult` into an envelope record
- helper to return blocked read model when SQLite store is unavailable

## Non-Scope

- No Solar Pro 3 API call.
- No Upstage SDK import.
- No `.env` value read.
- No network call.
- No provider response parsing.
- No provider execution result claim.
- No production provider readiness claim.
- No approval/replay repository merge.

## Acceptance Tests

- `request_contract_hash` and `response_contract_hash` are stored.
- DB rows do not contain raw prompt, provider body, provider payload, or secret
  sentinel values.
- Public read model returns hash/count/status fields only.
- Corrupted, unavailable, wrong-schema, or escaping-path store is blocked.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Suggested Files

- `packages/daacs_builder/provider_envelope_store.py`
- `tests/unit/test_provider_envelope_store.py`
- `docs/evals/aw-live-03-provider-envelope-read-model.md`
- `docs/metrics.md`
- `README.md`
- `docs/architecture.md`
- `docs/claim-boundary.md`

## Follow-Up Work

```text
AW-LIVE-04
depends_on: AW-LIVE-03
scope: provider envelope admission service wiring before disabled live adapter invocation
risk_level: high
rollback_plan: admission service wiring 제거, AW-LIVE-03 유지
```

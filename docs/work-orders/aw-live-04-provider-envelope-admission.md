# AW-LIVE-04 Work Order: Provider Envelope Admission Service

## Conclusion

`AW-LIVE-04` is the implementation unit after `AW-LIVE-03`. Its purpose is to
require provider envelope evidence before a disabled Solar live adapter can be
invoked.

This is still a no-call boundary. The service proves ordering and evidence
linkage only: Solar contract fixture -> provider envelope persistence -> public
read model -> disabled adapter admission.

## Implementation Unit

```text
id: AW-LIVE-04
depends_on: AW-LIVE-03
scope: provider envelope admission service wiring before disabled live adapter invocation
risk_level: high
rollback_plan: admission service wiring 제거, AW-LIVE-03 provider envelope read model 유지
```

## Senior Review Decision

Product lens:

- The next user-visible value is not provider execution. It is proving that a
  future provider path cannot skip evidence persistence and read-model checks.
- Public wording must say local no-call admission ordering, not provider result.

Architecture lens:

- Implement an explicit service boundary instead of adding hidden side effects
  to the adapter.
- The wrapper must block when the service is missing or when envelope evidence
  is unavailable.
- The disabled adapter may be invoked only after envelope evidence is persisted
  and visible through the public read model.

Security lens:

- Raw prompt, provider body, provider payload, authorization material, env
  value, SDK import, API call, and network call remain outside this path.
- Corrupted or unavailable envelope store must block before adapter invocation.

Data lens:

- Admission evidence is hash-bound:
  `request_contract_hash`, `response_contract_hash`, `prompt_contract_hash`,
  `content_hash`, counts, status, and envelope id.
- Public results expose sanitized checks, hashes, counts, and zero-call metrics
  only.

Test lens:

- Missing service must block before adapter invocation.
- Contract hash mismatch must block before adapter invocation.
- Store failure must block before adapter invocation.
- A valid no-call contract fixture should persist evidence, read it back, and
  then reach the disabled adapter, which still blocks.

Audit lens:

- This is a sequencing and evidence-control improvement.
- It must not claim model quality, external provider behavior, hosted service,
  production provider readiness, or generated app output.

## Scope

Add:

- `ProviderEnvelopeAdmissionService`
- `ProviderEnvelopeAdmissionResult`
- wrapper function to invoke an adapter only after envelope admission
- unit tests for successful evidence admission, missing service, hash mismatch,
  corrupted store, raw leakage, no-call guards, and duplicate matching evidence

## Non-Scope

- No Solar Pro 3 API call.
- No Upstage SDK import.
- No `.env` value read.
- No network call.
- No provider response parser.
- No production provider readiness.
- No adapter execution permission.

## Acceptance Tests

- Disabled live adapter invocation occurs only after provider envelope row
  save/read succeeds.
- Missing provider envelope persistence service is blocked.
- Request or response contract hash mismatch is blocked.
- Corrupted envelope store is blocked before adapter invocation.
- Raw prompt/provider body/provider payload storage and public exposure remain
  `0`.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Suggested Files

- `packages/daacs_builder/provider_envelope_admission.py`
- `tests/unit/test_provider_envelope_admission.py`
- `docs/evals/aw-live-04-provider-envelope-admission.md`
- `docs/metrics.md`
- `README.md`
- `docs/architecture.md`
- `docs/claim-boundary.md`

## Follow-Up Work

```text
AW-LIVE-05
depends_on: AW-LIVE-04
scope: provider admission service API/read-model projection hook, still no external call
risk_level: high
rollback_plan: API/read-model hook 제거, AW-LIVE-04 service boundary 유지
```

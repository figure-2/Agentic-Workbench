# AW-LIVE-44 Work Order: Execution Capsule Authz Release Attestation Boundary

## Conclusion

`AW-LIVE-44` adds a disabled first-call final no-call execution capsule
authorization release attestation after the execution capsule authz operator
decision. It binds authz operator-decision, release-attestation,
claim-boundary, and no-call counter hashes while keeping execution disabled.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-44
depends_on: AW-LIVE-43
scope: disabled first-call final no-call execution capsule authorization release attestation boundary, still no provider call
risk_level: high
rollback_plan: authorization release attestation boundary 제거, AW-LIVE-43 유지
```

## Background

`AW-LIVE-43` created a disabled execution capsule authorization operator
decision. The next safe step is still not a provider call. The next step is a
disabled authz release attestation that proves future authorization decision
evidence can be attested without granting execution permission. Public output
still contains only hashes and counts.

## Specialist Review

Product lens:
- The authz release attestation should make the future first-call sequence
  easier to inspect without implying a provider response or a live execution
  exists.

Architecture lens:
- Keep authz release attestation as a projection over authz operator-decision
  hash, release-attestation hash, claim-boundary evidence, and no-call
  counters. Do not turn it into a runtime result.

Security lens:
- Return only status, reason, hashes, and counts. Do not return prompt text,
  provider body, provider payload, authorization material, signature, nonce,
  env value, local paths, raw attestation flags, or operator references.

Testing lens:
- Cover missing expected execution capsule authz operator decision hash.
- Cover missing execution capsule authz release attestation payload.
- Cover complete authz release attestation with execution still disabled.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is local no-call capsule authz release attestation evidence. It is not
  provider behavior evidence, model-quality evidence, or execution permission.

## Implementation Scope

Add:

- execution capsule authz release attestation projection helper
- API response execution capsule authz release attestation field
- demo summary execution capsule authz release attestation fields
- expected authz operator decision hash and authz release attestation payload test cases
- metrics and claim docs

## Non-Scope

- No Solar Pro 3 API call.
- No Upstage SDK import.
- No `.env` value read.
- No network call.
- No provider response parser.
- No provider quality evaluation.
- No DAACS target runtime call.
- No production operator identity system.

## Acceptance Tests

- Execution capsule authz operator decision hash exists and matches the expected hash.
- Execution capsule authz release attestation payload is required.
- Release attestation is represented as a local hash only.
- Claim boundary is represented as a local hash only.
- No-call counter hash is present only when tracked counters are `0`.
- Authz release attestation keeps execution permission count `0`.
- Public output exposes only status, reason, hashes, and counts.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the execution capsule authz release attestation projection, API/demo
fields, related tests/docs, and return to the `AW-LIVE-43` execution capsule
authz operator decision boundary.

## Next Candidate

```text
AW-LIVE-45
scope: disabled first-call final no-call execution capsule authorization release seal boundary, still no provider call
```

The later release seal must remain separate from actual provider execution
until a dedicated call-opening task is explicitly approved.

# AW-LIVE-37 Work Order: Execution Capsule Release Attestation Boundary

## Conclusion

`AW-LIVE-37` adds a disabled first-call final no-call execution capsule release
attestation after the execution capsule operator decision. It binds execution
capsule operator decision, release-attestation, claim-boundary, and no-call
counter hashes while keeping execution disabled.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-37
depends_on: AW-LIVE-36
scope: disabled first-call final no-call execution capsule release attestation boundary, still no provider call
risk_level: high
rollback_plan: execution capsule release attestation boundary 제거, AW-LIVE-36 유지
```

## Background

`AW-LIVE-36` created a disabled execution capsule operator decision for a
future manual provider test candidate. The next safe step is still not a
provider call. The next step is a disabled release attestation that proves a
future human release attestation can be checked against execution capsule
operator decision, claim-boundary, and no-call evidence without granting
execution permission. Public output still contains only hashes and counts.

## Specialist Review

Product lens:
- The attestation should make the future first-call sequence easier to inspect
  without implying a provider response or a live execution exists.

Architecture lens:
- Keep the attestation as a projection over execution capsule operator
  decision evidence, release-attestation hash, claim-boundary evidence, and
  no-call counters. Do not turn it into a runtime result.

Security lens:
- Return only status, reason, hashes, and counts. Do not return prompt text,
  provider body, provider payload, authorization material, signature, nonce,
  env value, local paths, raw attestation flags, or operator references.

Testing lens:
- Cover missing expected execution capsule operator decision hash.
- Cover missing execution capsule release attestation payload.
- Cover complete release attestation with execution still disabled.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is local no-call capsule release attestation evidence. It is not
  provider behavior evidence, model-quality evidence, or execution permission.

## Implementation Scope

Add:

- execution capsule release attestation projection helper
- API response execution capsule release attestation field
- demo summary execution capsule release attestation fields
- expected operator decision hash and attestation payload test cases
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

- Execution capsule operator decision hash exists and matches the expected
  hash.
- Execution capsule release attestation payload is required.
- Release attestation is represented as a local hash only.
- Claim boundary is represented as a local hash only.
- No-call counter hash is present only when tracked counters are `0`.
- Attestation keeps execution permission count `0`.
- Public attestation exposes only status, reason, hashes, and counts.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the execution capsule release attestation projection, API/demo fields,
related tests/docs, and return to the `AW-LIVE-36` execution capsule operator
decision boundary.

## Next Candidate

```text
AW-LIVE-38
scope: disabled first-call final no-call execution capsule release seal boundary, still no provider call
```

The later release seal must remain separate from actual provider execution
until a dedicated call-opening task is explicitly approved.

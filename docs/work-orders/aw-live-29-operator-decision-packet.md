# AW-LIVE-29 Work Order: Operator Decision Packet Boundary

## Conclusion

`AW-LIVE-29` adds a disabled first-call operator decision packet after the
operator handback. It binds handback, operator-decision, claim-boundary, and
no-call counter hashes while keeping execution disabled.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-29
depends_on: AW-LIVE-28
scope: disabled first-call operator decision packet boundary, still no provider call
risk_level: high
rollback_plan: operator decision packet boundary 제거, AW-LIVE-28 유지
```

## Background

`AW-LIVE-28` created a disabled operator handback for a future manual provider
test candidate. The next safe step is still not a provider call. The next step
is a disabled operator decision packet that proves a future human decision can
be checked against handback, claim-boundary, and no-call evidence without
granting execution permission. Public output still contains only hashes and
counts.

## Specialist Review

Product lens:
- The packet should make the future first-call sequence understandable without
  implying a provider response or a live operator-approved execution exists.

Architecture lens:
- Keep the packet as a projection over operator handback evidence,
  operator-decision hash, claim-boundary evidence, and no-call counters. Do
  not turn it into a runtime result.

Security lens:
- Return only status, reason, hashes, and counts. Do not return prompt text,
  provider body, provider payload, authorization material, signature, nonce,
  env value, local paths, raw decision flags, or operator references.

Testing lens:
- Cover missing expected operator handback hash.
- Cover missing operator decision packet payload.
- Cover complete packet with execution still disabled.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is local no-call decision packet evidence. It is not provider behavior
  evidence, model-quality evidence, or execution permission.

## Implementation Scope

Add:

- operator decision packet projection helper
- API response operator decision packet field
- demo summary operator decision packet fields
- expected operator handback hash and packet payload test cases
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

- Operator handback hash exists and matches the expected hash.
- Operator decision packet payload is required.
- Operator decision is represented as a local hash only.
- Claim boundary is represented as a local hash only.
- No-call counter hash is present only when tracked counters are `0`.
- Packet keeps execution permission count `0`.
- Public packet exposes only status, reason, hashes, and counts.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the operator decision packet projection, API/demo fields, related
tests/docs, and return to the `AW-LIVE-28` operator handback boundary.

## Next Candidate

```text
AW-LIVE-30
scope: disabled first-call operator release attestation boundary, still no provider call
```

The later operator release attestation must remain separate from actual
provider execution until a dedicated call-opening task is explicitly approved.

# AW-LIVE-18 Work Order: Live Execution Arming Record Boundary

## Conclusion

`AW-LIVE-18` adds an explicit no-call live execution arming record after the
sealed pre-execution packet. It binds operator, sealed packet, expiry,
rollback, and abort policy hashes while keeping execution disabled.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-18
depends_on: AW-LIVE-17
scope: explicit no-call live execution arming record, still execution blocked
risk_level: high
rollback_plan: arming record 제거, AW-LIVE-17 유지
```

## Background

`AW-LIVE-17` sealed the pre-call evidence into one hash/count-only packet. The
next safe step is not a provider call. The next step is an arming record that
states who armed the future test candidate, which sealed packet it refers to,
when it expires, and which rollback/abort hashes apply. Public output still
contains only hashes and counts.

## Specialist Review

Product lens:
- The arming record should make the future manual provider test process clear
  without implying live capability.

Architecture lens:
- Keep the arming record as a projection over the sealed packet and a local
  arming payload. Do not turn it into a runtime command.

Security lens:
- Return only status, reason, hashes, and counts. Do not return prompt text,
  provider body, provider payload, authorization material, signature, nonce,
  env value, local paths, operator reference, expiry value, rollback body, or
  abort criteria text.

Testing lens:
- Cover missing expected sealed hash.
- Cover complete arming record.
- Cover arming sealed hash mismatch.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is local no-call arming evidence. It is not provider behavior evidence,
  model-quality evidence, or execution permission.

## Implementation Scope

Add:

- arming record projection helper
- API response arming record field
- demo summary arming record fields
- expected sealed packet hash mismatch test cases
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

- Sealed packet hash exists and matches the expected hash.
- Arming record includes operator, sealed packet, expiry, rollback, and abort
  policy hashes.
- Arming record keeps execution permission count `0`.
- Public arming projection exposes only status, reason, hashes, and counts.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the arming record projection, API/demo fields, related tests/docs, and
return to the `AW-LIVE-17` sealed pre-execution packet boundary.

## Next Candidate

```text
AW-LIVE-19
scope: no-call execution authorization release proposal, still execution blocked
```

The later release proposal must remain separate from actual provider execution
until a dedicated call-opening task is explicitly approved.

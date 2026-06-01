# AW-LIVE-17 Work Order: Sealed Pre-Execution Packet Boundary

## Conclusion

`AW-LIVE-17` adds a sealed pre-execution packet boundary after operator opt-in.
It binds handoff, opt-in, cost/timeout/quota, and rollback/abort hashes while
keeping execution disabled by default.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-17
depends_on: AW-LIVE-16
scope: live-call sealed pre-execution packet boundary, still no provider call
risk_level: high
rollback_plan: sealed pre-execution packet 제거, AW-LIVE-16 유지
```

## Background

`AW-LIVE-16` added an operator opt-in checklist bound to the final handoff
packet hash. The next safe step is to seal the pre-call evidence into one
hash/count-only packet. This packet is still not a provider invocation and is
not execution permission.

## Specialist Review

Product lens:
- The sealed packet should make the future manual provider test candidate easy
  to review without implying live capability.

Architecture lens:
- Keep the packet as a projection over already sanitized policy, proposal,
  handoff, and opt-in components.

Security lens:
- Return only status, reason, hashes, and counts. Do not return prompt text,
  provider body, provider payload, authorization material, signature, nonce,
  env value, local paths, rollback body, or abort criteria text.

Testing lens:
- Cover missing expected operator opt-in hash.
- Cover complete sealed packet.
- Cover operator opt-in hash mismatch.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is local no-call pre-execution evidence. It is not provider behavior
  evidence, model-quality evidence, or execution permission.

## Implementation Scope

Add:

- sealed pre-execution packet projection helper
- API response sealed packet field
- demo summary sealed packet fields
- expected operator opt-in hash mismatch test cases
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

- Operator opt-in hash exists and matches the expected hash.
- Sealed packet includes handoff, opt-in, cost/timeout/quota, and
  rollback/abort hashes.
- Default execution remains blocked.
- Public sealed packet projection exposes only status, reason, hashes, and
  counts.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the sealed packet projection, API/demo fields, related tests/docs, and
return to the `AW-LIVE-16` operator opt-in checklist boundary.

## Next Candidate

```text
AW-LIVE-18
scope: explicit no-call live execution arming record, still execution blocked
```

The later arming record must remain separate from actual provider execution
until a dedicated call-opening task is explicitly approved.

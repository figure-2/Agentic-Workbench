# AW-LIVE-20 Work Order: Final Release Packet Boundary

## Conclusion

`AW-LIVE-20` adds a no-call final release packet after the release proposal.
It binds release proposal, arming record, operator, release window, and
rollback/abort hashes while keeping execution disabled.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-20
depends_on: AW-LIVE-19
scope: no-call final release packet boundary, still execution blocked
risk_level: high
rollback_plan: final release packet 제거, AW-LIVE-19 유지
```

## Background

`AW-LIVE-19` created a release proposal for a future manual provider test
candidate. The next safe step is still not a provider call. The next step is a
final packet that states which release proposal it refers to and binds the
proposal's arming, operator, release window, and rollback hashes. Public output
still contains only hashes and counts.

## Specialist Review

Product lens:
- The final packet should make the future manual provider test process clear
  without implying live capability.

Architecture lens:
- Keep the final packet as a projection over the release proposal and a local
  final-packet payload. Do not turn it into a runtime command.

Security lens:
- Return only status, reason, hashes, and counts. Do not return prompt text,
  provider body, provider payload, authorization material, signature, nonce,
  env value, local paths, operator reference, release window values, rollback
  body, or abort criteria text.

Testing lens:
- Cover missing expected release proposal hash.
- Cover complete final release packet.
- Cover final packet proposal hash mismatch.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is local no-call final release evidence. It is not provider behavior
  evidence, model-quality evidence, or execution permission.

## Implementation Scope

Add:

- final release packet projection helper
- API response final release packet field
- demo summary final release packet fields
- expected release proposal hash mismatch test cases
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

- Release proposal hash exists and matches the expected hash.
- Final release packet includes release proposal, arming record, operator,
  release window, and rollback/abort hashes.
- Final release packet keeps execution permission count `0`.
- Public final packet exposes only status, reason, hashes, and counts.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the final release packet projection, API/demo fields, related
tests/docs, and return to the `AW-LIVE-19` release proposal boundary.

## Next Candidate

```text
AW-LIVE-21
scope: disabled first-call execution switch boundary, still no provider call
```

The later switch must remain separate from actual provider execution until a
dedicated call-opening task is explicitly approved.

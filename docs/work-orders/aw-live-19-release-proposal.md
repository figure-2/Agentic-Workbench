# AW-LIVE-19 Work Order: Execution Authorization Release Proposal Boundary

## Conclusion

`AW-LIVE-19` adds a no-call execution authorization release proposal after the
arming record. It binds operator, arming record, release window, and
rollback/abort hashes while keeping execution disabled.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-19
depends_on: AW-LIVE-18
scope: no-call execution authorization release proposal, still execution blocked
risk_level: high
rollback_plan: release proposal 제거, AW-LIVE-18 유지
```

## Background

`AW-LIVE-18` created an arming record for a future manual provider test
candidate. The next safe step is still not a provider call. The next step is a
release proposal that states which arming record it refers to, who proposed the
release, what release window applies, and which rollback/abort hash applies.
Public output still contains only hashes and counts.

## Specialist Review

Product lens:
- The release proposal should make the future manual provider test process
  clear without implying live capability.

Architecture lens:
- Keep the release proposal as a projection over the arming record and a local
  release payload. Do not turn it into a runtime command.

Security lens:
- Return only status, reason, hashes, and counts. Do not return prompt text,
  provider body, provider payload, authorization material, signature, nonce,
  env value, local paths, operator reference, release window values, rollback
  body, or abort criteria text.

Testing lens:
- Cover missing expected arming record hash.
- Cover complete release proposal.
- Cover release proposal arming hash mismatch.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is local no-call release evidence. It is not provider behavior evidence,
  model-quality evidence, or execution permission.

## Implementation Scope

Add:

- release proposal projection helper
- API response release proposal field
- demo summary release proposal fields
- expected arming record hash mismatch test cases
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

- Arming record hash exists and matches the expected hash.
- Release proposal includes operator, arming record, release window, and
  rollback/abort hashes.
- Release proposal keeps execution permission count `0`.
- Public release proposal exposes only status, reason, hashes, and counts.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the release proposal projection, API/demo fields, related tests/docs,
and return to the `AW-LIVE-18` arming record boundary.

## Next Candidate

```text
AW-LIVE-20
scope: no-call final release packet boundary, still execution blocked
```

The later final release packet must remain separate from actual provider
execution until a dedicated call-opening task is explicitly approved.

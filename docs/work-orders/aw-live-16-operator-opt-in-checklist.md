# AW-LIVE-16 Work Order: Operator Opt-In Checklist Boundary

## Conclusion

`AW-LIVE-16` adds a first live-call operator opt-in checklist boundary after
the no-call handoff packet. It binds a local operator opt-in to the expected
handoff packet hash while keeping execution disabled by default.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-16
depends_on: AW-LIVE-15
scope: first live-call operator opt-in checklist boundary, still disabled by default
risk_level: high
rollback_plan: opt-in checklist boundary 제거, AW-LIVE-15 handoff packet 유지
```

## Background

`AW-LIVE-15` created a final no-call handoff packet over policy, preflight,
readiness, review, and export evidence. The next safe step is not a provider
call. The next step is a separate opt-in projection that proves a person
explicitly opted in to the exact handoff packet hash while execution remains
closed.

## Specialist Review

Product lens:
- The opt-in should make the future manual provider test process clearer
  without implying that the provider path is open.

Architecture lens:
- Keep opt-in as a projection over sanitized handoff evidence. Do not turn it
  into a runtime command or permission token.

Security lens:
- Return only status, reason, hashes, and counts. Do not return prompt text,
  provider body, provider payload, authorization material, signature, nonce,
  env value, or local paths.

Testing lens:
- Cover missing opt-in.
- Cover complete opt-in.
- Cover handoff hash mismatch.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is local no-call opt-in evidence. It is not provider behavior evidence,
  model-quality evidence, or execution permission.

## Implementation Scope

Add:

- operator opt-in projection helper
- API response operator opt-in field
- demo summary operator opt-in fields
- handoff hash binding test cases
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

- Handoff packet hash exists and matches the expected hash.
- Missing operator opt-in is blocked.
- Complete opt-in still leaves execution permission count `0`.
- Opt-in handoff hash mismatch is blocked.
- Public opt-in projection exposes only status, reason, hashes, and counts.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the operator opt-in projection, API/demo fields, related tests/docs, and
return to the `AW-LIVE-15` handoff packet boundary.

## Next Candidate

```text
AW-LIVE-17
scope: live-call sealed pre-execution packet boundary, still no provider call
```

The later sealed packet must remain separate from actual provider execution
until a dedicated call-opening task is explicitly approved.

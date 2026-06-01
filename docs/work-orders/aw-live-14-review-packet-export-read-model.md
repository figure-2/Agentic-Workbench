# AW-LIVE-14 Work Order: Review Packet Export Read Model

## Conclusion

`AW-LIVE-14` adds a no-call export/read-model for the manual provider test
review packet. It stores and returns only hash/status/reason/count fields.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-14
depends_on: AW-LIVE-13
scope: manual provider test review packet export/read-model, still no external call
risk_level: high
rollback_plan: review packet export/read-model 제거, AW-LIVE-13 projection 유지
```

## Background

`AW-LIVE-13` creates the blocked review packet in the POST precheck response.
The next safe step is to persist a sanitized export row and expose it through a
read model so API/demo paths can retrieve the packet evidence without raw
material.

## Specialist Review

Product lens:
- The export/read-model should let a first-time reviewer see that the manual
  provider test candidate has a stored review packet, without implying
  execution.

Architecture lens:
- Keep the export as a repository/read-model projection over an existing packet
  hash. Do not attach it to adapter invocation or provider execution.

Security lens:
- Persist only status, reason, hashes, and counts. Do not persist prompt text,
  provider body, provider payload, authorization material, signature, nonce,
  env value, or local paths.

Testing lens:
- Cover normal export/read-model retrieval.
- Cover expected packet hash mismatch.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is local no-call evidence. It is not provider behavior evidence,
  model-quality evidence, or an execution permission.

## Implementation Scope

Add:

- review packet export repository row
- review packet export public read model
- API/demo export summary
- expected review packet hash mismatch gate
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

- Review packet export can be read by API/demo as hash/status/reason/count
  fields only.
- Packet export stores no raw prompt/provider body/provider payload.
- Packet hash mismatch is blocked before adapter admission.
- Approve decision still leaves execution permission count `0`.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the review packet export row/read-model, API/demo fields, related
tests/docs, and return to the `AW-LIVE-13` review packet projection.

## Next Candidate

```text
AW-LIVE-15
scope: manual provider test final no-call audit handoff packet, still no external call
```

The later handoff packet should remain separate from any execution permission
and continue to expose only sanitized hashes and counts.

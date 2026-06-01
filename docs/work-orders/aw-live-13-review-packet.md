# AW-LIVE-13 Work Order: Review Packet

## Conclusion

`AW-LIVE-13` adds a no-call review packet for the manual provider test track.
It packages the policy summary, preflight audit, and readiness decision into a
single public-safe projection while execution stays blocked.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-13
depends_on: AW-LIVE-12
scope: no-call manual provider test review packet, still no external call
risk_level: high
rollback_plan: review packet 제거, AW-LIVE-12 상태 유지
```

## Background

`AW-LIVE-12` records a blocked readiness decision against a preflight audit
hash. The next safe step is a single review packet that an operator can inspect
without seeing raw prompt, provider body, provider payload, or authorization
material.

## Specialist Review

Product lens:
- The packet should make the manual provider test track understandable as one
  local review artifact.

Architecture lens:
- Keep the packet as a pure projection over existing component hashes. It must
  not call an adapter or mutate provider/runtime state.

Security lens:
- The public packet must expose only status, reason, hash, and counts. Operator
  identity, auth material, provider payloads, raw prompt, signature, nonce, env
  value, and local paths must remain absent.

Testing lens:
- Cover the valid no-call packet path.
- Cover mismatched component blocking.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is a local no-call review artifact. It is not provider behavior evidence,
  model-quality evidence, or a launch claim.

## Implementation Scope

Add:

- `manual_provider_test_review_packet` public projection
- review packet hash bound to policy/preflight/readiness hashes
- missing/mismatched component reasons
- API/demo assertions
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

- Policy summary, preflight audit, and readiness decision are packaged.
- Public projection exposes only status, reason, hash, and counts.
- Approve decision still grants execution permission count `0`.
- Missing or mismatched packet component remains blocked.
- Raw prompt/provider body/provider payload exposure remains `0`.
- Raw approval authorization material exposure remains `0`.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the review packet projection, remove API/demo fields, remove related
tests/docs, and return to the `AW-LIVE-12` readiness decision record.

## Next Candidate

```text
AW-LIVE-14
scope: manual provider test review packet export/read-model, still no external call
```

The later export/read-model should keep the same hash/count/status/reason
boundary and remain separate from any execution permission.

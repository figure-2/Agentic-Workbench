# AW-LIVE-12 Work Order: Readiness Decision Record

## Conclusion

`AW-LIVE-12` adds a blocked readiness decision record for the manual provider
test track. It lets an operator record `approve`, `reject`, or `defer` against
the preflight audit hash, but it still does not grant execution permission.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-12
depends_on: AW-LIVE-11
scope: manual provider test execution readiness decision record, still no external call
risk_level: high
rollback_plan: readiness decision record 제거, AW-LIVE-11 상태 유지
```

## Background

`AW-LIVE-11` produces a blocked preflight audit bundle. The next safe step is a
decision record that says what a human operator decided after reviewing that
bundle. The decision must remain hash-only in public output and must not create
an execution path.

## Specialist Review

Product lens:
- The decision record should clarify whether the local candidate was approved,
  rejected, or deferred for later work.

Architecture lens:
- Keep the record as a projection over the preflight hash. It should not call an
  adapter or mutate provider/runtime state.

Security lens:
- The public record must expose only status, reason, hash, and counts. Operator
  identity, auth material, provider payloads, raw prompt, signature, nonce, env
  value, and local paths must remain absent.

Testing lens:
- Cover approve, reject, and defer.
- Cover preflight hash mismatch.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is a local no-call decision record. It is not provider behavior evidence,
  model-quality evidence, or a service launch claim.

## Implementation Scope

Add:

- `manual_provider_test_readiness_decision` public projection
- readiness decision hash bound to the preflight audit hash
- approve/reject/defer count fields
- blocked reason for missing/mismatched preflight hash
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

- Readiness decision is created from a preflight audit hash.
- Approve/reject/defer are represented by decision count fields.
- Decision status remains `blocked`.
- Execution permission count remains `0`.
- Missing or mismatched preflight hash remains blocked.
- Public projection exposes only status, reason, hash, and counts.
- Raw prompt/provider body/provider payload exposure remains `0`.
- Raw approval authorization material exposure remains `0`.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the readiness decision projection, remove API/demo fields, remove
related tests/docs, and return to the `AW-LIVE-11` preflight audit bundle.

## Next Candidate

```text
AW-LIVE-13
scope: no-call manual provider test review packet, still no external call
```

The later review packet should package the policy summary, preflight audit, and
readiness decision into a single operator-facing artifact while keeping
execution closed.

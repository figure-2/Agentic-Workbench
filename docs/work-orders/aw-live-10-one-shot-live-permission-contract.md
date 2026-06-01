# AW-LIVE-10 Work Order: One-Shot Live Permission Contract

## Conclusion

`AW-LIVE-10` adds an explicit one-shot permission contract projection above the
disabled manual provider test executor. The contract can be fingerprinted for a
specific run, proposal, planned call, cost, timeout, quota, rollback, and abort
criteria, but the public state remains `blocked`.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-10
depends_on: AW-LIVE-09
scope: explicit one-shot live call permission contract, still no call by default
risk_level: high
rollback_plan: one-shot permission contract 제거, AW-LIVE-09 disabled executor boundary 유지
```

## Background

`AW-LIVE-09` proves that a manual provider test proposal and executor flag do
not create execution permission. The next safe step is a narrow permission
contract that records the shape of a later one-shot call request without
creating an execution path.

## Specialist Review

Product lens:
- The reviewer should see the difference between a proposed one-shot test and
  any provider outcome.

Architecture lens:
- Keep the permission contract attached to the provider envelope API output.
  It should not become a new runner or adapter path.

Security lens:
- The public permission projection must expose only status, reason, hash,
  expiry, and count. Raw prompt, provider body, provider payload, auth
  material, signature, nonce, env value, and local paths must remain absent.

Testing lens:
- Test that executor blocked state keeps the permission state blocked.
- Test that a valid one-shot permission candidate is represented by a hash
  only.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is a contract boundary for a later manual test proposal. It is not
  provider execution, provider quality evidence, or a service launch claim.

## Implementation Scope

Add:

- `one_shot_live_permission` public projection
- permission contract hash derived from required one-shot fields
- blocked reason when permission is missing
- blocked reason when executor remains blocked
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

- Executor blocked state keeps permission state blocked.
- One-shot permission contract includes run id, proposal hash, planned call
  hash, cost, timeout, quota, rollback, abort criteria hash/count, and expiry.
- Permission public projection exposes only `status`, `reason`,
  `permission_contract_hash`, `expires_at`, and `permission_field_count`.
- Permission presence does not alter default blocked execution.
- Raw prompt/provider body/provider payload exposure remains `0`.
- Raw approval authorization material exposure remains `0`.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the one-shot permission projection, remove API/demo fields, remove
related tests/docs, and return to the `AW-LIVE-09` disabled executor boundary.

## Next Candidate

```text
AW-LIVE-11
scope: first manual provider test preflight audit bundle, still no external call
```

The later preflight bundle should aggregate proposal, executor, permission,
operator checklist, and no-call counters before any separate live-test request
is considered.

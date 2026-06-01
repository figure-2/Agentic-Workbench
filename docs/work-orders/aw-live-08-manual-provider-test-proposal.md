# AW-LIVE-08 Work Order: Manual Provider Test Proposal Gate

## Conclusion

`AW-LIVE-08` adds a first manual provider test proposal gate. A separate
operator approval must reference the exact proposal hash before the proposal
can be accepted by the local API projection.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls. Even an accepted proposal remains
disabled by default.

## Task Definition

```text
id: AW-LIVE-08
depends_on: AW-LIVE-07
scope: first manual provider test proposal gate skeleton
risk_level: high
rollback_plan: manual test proposal gate 제거, AW-LIVE-07 dry-admission 상태 유지
```

## Background

`AW-LIVE-07` made dry-admission visible through a manual checklist. The next
gap is deciding what a first narrow provider test would mean before any later
task considers opening an external call. `AW-LIVE-08` closes that gap by
requiring a proposal object and a separate proposal approval hash.

## Specialist Review

Product lens:
- The reviewer should see that a test proposal exists, but also see that it is
  not executable.

Architecture lens:
- Keep the proposal gate inside the provider envelope API projection. It has
  access to run id, prompt contract hash, policy limits, operator approval, and
  no-call counters.

Security lens:
- The proposal must not expose raw prompt, provider body, auth material,
  signature, nonce, env value, local path, or provider payload.

Testing lens:
- Test both missing proposal approval and approved-but-disabled states.

Audit lens:
- This is a proposal gate. It is not external provider behavior, model quality
  evidence, or production approval.

## Implementation Scope

Add:

- `manual_provider_test_proposal` public projection
- proposal hash over run id, prompt contract hash, cost, timeout, quota,
  rollback id, and abort criteria hash/count
- separate manual proposal operator approval
- API/demo fields showing `allowed_to_execute=false` and
  `disabled_by_default=true`
- tests and metrics

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

- Missing manual provider test proposal approval is blocked.
- Proposal includes run id, prompt contract hash, cost, timeout, quota,
  rollback id, and abort criteria hash/count.
- Accepted proposal still has `allowed_to_execute=false`.
- Accepted proposal still has `disabled_by_default=true`.
- Raw prompt/provider body/provider payload exposure remains `0`.
- Raw approval authorization material exposure remains `0`.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the manual provider test proposal projection, remove API/demo fields,
remove related tests/docs, and return to the `AW-LIVE-07` dry-admission
checklist state.

## Next Candidate

```text
AW-LIVE-09
scope: disabled manual provider test executor boundary
```

Still no external call unless a later task explicitly creates a narrow,
operator-approved executor and then separately enables it.

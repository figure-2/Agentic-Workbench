# AW-LIVE-09 Work Order: Disabled Manual Provider Test Executor

## Conclusion

`AW-LIVE-09` adds a disabled manual provider test executor boundary. Even when
the manual provider test proposal gate is accepted, the executor projection
returns `blocked`. It exposes only `status`, `reason`, and `planned_call_hash`.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-09
depends_on: AW-LIVE-08
scope: disabled manual provider test executor boundary
risk_level: high
rollback_plan: disabled executor boundary 제거, AW-LIVE-08 proposal gate 유지
```

## Background

`AW-LIVE-08` can accept a manual provider test proposal as
`approved_disabled`, but that still should not imply any executor exists. The
next safe step is to add an executor boundary that proves execution remains
blocked even when a proposal and executor flag are present.

## Specialist Review

Product lens:
- The reviewer should see that the next live-track object is an executor
  boundary, not provider behavior.

Architecture lens:
- Keep executor projection small and local to provider envelope API output.
  The executor should not create a new execution path.

Security lens:
- The executor projection must not expose raw prompt, provider body, auth
  material, signature, nonce, env value, local path, or provider payload.

Testing lens:
- Test approved proposal without executor flag.
- Test approved proposal with executor flag.
- Both states must remain blocked with provider/runtime counters at 0.

Audit lens:
- This is not external provider execution. It is a disabled boundary for a
  later, separately approved implementation unit.

## Implementation Scope

Add:

- `manual_provider_test_executor` public projection
- `planned_call_hash` derived from proposal hash and request identifiers
- blocked reason when executor flag is missing
- blocked reason when executor flag is present
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

- Proposal gate `approved_disabled` still leaves executor blocked.
- Missing `manual_test_executor_enable` blocks executor with
  `executor_enable_required`.
- Present `manual_test_executor_enable=true` still blocks executor with
  `executor_disabled_by_default`.
- Executor public projection exposes only `status`, `reason`, and
  `planned_call_hash`.
- Raw prompt/provider body/provider payload exposure remains `0`.
- Raw approval authorization material exposure remains `0`.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the manual provider test executor projection, remove API/demo fields,
remove related tests/docs, and return to the `AW-LIVE-08` proposal gate.

## Next Candidate

```text
AW-LIVE-10
scope: explicit one-shot live call permission contract, still no call by default
```

The later permission contract must still require a separate operator decision
and must preserve no-call defaults until an explicit test task changes them.

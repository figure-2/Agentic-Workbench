# AW-LIVE-06 Work Order: Provider Precheck Operator Approval Envelope

## Conclusion

`AW-LIVE-06` makes provider envelope precheck require an explicit operator
approval envelope. The operator approves a sanitized policy summary containing
cost, timeout, quota, readiness, and zero-call boundaries before provider
envelope admission can proceed.

This remains a no-call local precheck. It does not open Solar Pro 3, provider
SDKs, network calls, or DAACS target runtime.

## Task Definition

```text
id: AW-LIVE-06
depends_on: AW-LIVE-05
scope: provider precheck policy UX + explicit operator approval envelope
risk_level: high
rollback_plan: operator approval envelope/API hook 제거, AW-LIVE-05 상태 유지
```

## Background

`AW-LIVE-05` made provider envelope admission visible through API/demo
projections. The remaining gap was that precheck could run without clearly
showing what a human operator had reviewed. `AW-LIVE-06` closes that gap by
making the operator approval subject explicit and hash-bound.

## Specialist Review

Product lens:
- The user-facing story should be: "an operator approved this local no-call
  precheck summary", not "the provider ran".

Architecture lens:
- Keep operator approval in the API service layer, before provider envelope
  repository access and before disabled adapter reachability.

Security lens:
- Operator approval must not expose signature, nonce, provider body, raw prompt,
  or env values.

Testing lens:
- Missing operator approval must block before provider envelope rows are
  written.
- The approved policy summary hash must match the exact public summary.

Audit lens:
- This is still a readiness/evidence gate. It is not provider execution,
  hosted provider behavior, or production provider readiness.

## Implementation Scope

Add:

- provider precheck operator policy summary projection
- operator approval envelope projection
- policy summary hash binding
- missing/mismatched operator approval blocking before store/admission
- API/demo projection updates
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

- Provider precheck requires explicit `operator_approval`.
- Public response includes cost/timeout/quota/readiness summary.
- Public response includes operator approval status and policy summary hash.
- Missing operator approval blocks before provider envelope store write.
- Raw prompt/provider body/provider payload exposure remains `0`.
- Raw approval authorization material exposure remains `0`.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove operator policy summary and approval envelope checks from the provider
envelope API service, remove related tests/docs, and return to `AW-LIVE-05`
behavior.

## Next Candidate

```text
AW-LIVE-07
scope: live provider dry-admission runbook and manual operator checklist
```

Still no external call unless a later task explicitly opens a narrowly scoped
manual live test.

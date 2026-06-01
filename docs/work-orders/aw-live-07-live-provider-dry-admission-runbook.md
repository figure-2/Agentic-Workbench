# AW-LIVE-07 Work Order: Live Provider Dry-Admission Runbook

## Conclusion

`AW-LIVE-07` documents and projects the manual checklist required before a
future provider test can even be proposed. It does not open Solar Pro 3, does
not import provider SDKs, does not read `.env` values, does not make network
calls, and does not call the DAACS target runtime.

## Task Definition

```text
id: AW-LIVE-07
depends_on: AW-LIVE-06
scope: live provider dry-admission runbook + manual operator checklist
risk_level: high
rollback_plan: runbook/checklist 문서와 projection 제거, AW-LIVE-06 유지
```

## Background

`AW-LIVE-06` added an operator approval envelope bound to a sanitized policy
summary hash. That proves that a local operator approved the precheck subject,
but it still does not define the manual checklist for the first narrow provider
test proposal. `AW-LIVE-07` closes that gap by making the API/demo response say
`dry_admission_only` and by documenting the manual runbook.

## Specialist Review

Product lens:
- The status must be understandable to a first-time reviewer: evidence is
  visible, but execution permission is still closed.

Architecture lens:
- The dry-admission checklist belongs in the provider envelope API projection
  layer because it combines policy summary, operator approval, and zero-call
  boundaries.

Security lens:
- The checklist must not include raw prompt, provider body, auth material,
  signature, nonce, env value, or local filesystem path.

Testing lens:
- Existing API and demo tests should prove the response is not executable and
  still keeps all provider/runtime counters at zero.

Audit lens:
- This is a manual readiness checklist, not provider behavior evidence and not
  production approval.

## Implementation Scope

Add:

- `live_provider_dry_admission` public projection
- dry-admission checklist ids for operator approval, policy hash binding,
  cost, timeout, API quota, output budget, rollback, final review, and closed
  execution permission
- API/demo assertions that `live_ready=false` and `allowed_to_execute=false`
- runbook and eval documentation
- metrics and public claim docs update

## Non-Scope

- No Solar Pro 3 API call.
- No Upstage SDK import.
- No `.env` value read.
- No network call.
- No provider response parser.
- No provider quality evaluation.
- No DAACS target runtime call.
- No production identity or signing system.

## Acceptance Tests

- Live call preconditions are documented in a manual checklist.
- Cost, timeout, quota, rollback, and operator approval conditions are explicit.
- API/demo shows dry-admission status, not execution permission.
- Public responses expose only status, hash, count, boolean, and checklist
  metadata.
- Raw prompt/provider body/provider payload exposure remains `0`.
- Raw approval authorization material exposure remains `0`.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the dry-admission checklist projection, remove API/demo assertions and
docs, and return to the `AW-LIVE-06` operator approval envelope behavior.

## Next Candidate

```text
AW-LIVE-08
scope: first manual provider test proposal gate with explicit operator opt-in
```

Still no external call unless a later task explicitly opens a narrow manual
test path with cost, timeout, quota, rollback, and operator approval evidence.

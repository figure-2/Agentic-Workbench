# AW-LIVE-11 Work Order: Manual Provider Test Preflight Audit Bundle

## Conclusion

`AW-LIVE-11` adds a blocked preflight audit bundle for the first manual provider
test track. It combines the manual proposal, disabled executor, one-shot
permission, operator checklist, and no-call counters into one public-safe
projection.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-11
depends_on: AW-LIVE-10
scope: first manual provider test preflight audit bundle, still no external call
risk_level: high
rollback_plan: preflight audit bundle 제거, AW-LIVE-10 상태 유지
```

## Background

`AW-LIVE-10` can produce a blocked one-shot permission contract hash. A reviewer
still needs one compact preflight view that says whether the proposal, executor,
permission, checklist, and no-call counters are mutually consistent.

## Specialist Review

Product lens:
- The bundle should make the live-track readiness story easier to understand
  without implying provider behavior.

Architecture lens:
- Keep the bundle as a projection over existing components. It must not create
  a new adapter, provider, or runtime path.

Security lens:
- The bundle must expose only status, reason, hash, and counts. It must not
  expose raw prompt, provider body, provider payload, auth material, signature,
  nonce, env value, or local paths.

Testing lens:
- Cover a complete local preflight candidate.
- Cover a mismatched permission candidate.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is a local no-call preflight bundle. It is not external provider
  execution, model-quality evidence, or a service launch claim.

## Implementation Scope

Add:

- `manual_provider_test_preflight_audit` public projection
- component checks for proposal, executor, permission, operator checklist, and
  no-call counters
- preflight hash for fully consistent local candidates
- blocked reason for missing/mismatched components
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

- Proposal, executor, one-shot permission, operator checklist, and no-call
  counters are represented by one preflight bundle.
- Bundle status remains `blocked`.
- Missing proposal component reports a blocked reason.
- Mismatched permission component reports a blocked reason.
- Public projection exposes only status, reason, hash, and counts.
- Raw prompt/provider body/provider payload exposure remains `0`.
- Raw approval authorization material exposure remains `0`.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the preflight audit bundle projection, remove API/demo fields, remove
related tests/docs, and return to the `AW-LIVE-10` one-shot permission contract.

## Next Candidate

```text
AW-LIVE-12
scope: manual provider test execution readiness decision record, still no external call
```

The later readiness decision should remain separate from any provider adapter
invocation and should still default to blocked.

# AW-LIVE-40 Work Order: Execution Capsule Authz Export Read Model Boundary

## Conclusion

`AW-LIVE-40` adds a disabled first-call final no-call execution capsule
authorization export/read-model after the execution capsule final
authorization. It binds final-authz, export metadata, claim-boundary, and
no-call counter hashes while keeping execution disabled.

This still does not open Solar Pro 3, provider SDKs, `.env` value reads,
network calls, or DAACS target runtime calls.

## Task Definition

```text
id: AW-LIVE-40
depends_on: AW-LIVE-39
scope: disabled first-call final no-call execution capsule authorization export/read-model boundary, still no provider call
risk_level: high
rollback_plan: authorization export/read-model boundary 제거, AW-LIVE-39 유지
```

## Background

`AW-LIVE-39` created a disabled execution capsule final authorization for a
future manual provider test candidate. The next safe step is still not a
provider call. The next step is a disabled authz export/read-model that proves
future final authorization evidence can be summarized for operators without
granting execution permission. Public output still contains only hashes and
counts.

## Specialist Review

Product lens:
- The authz export/read-model should make the future first-call sequence easier
  to inspect without implying a provider response or a live execution exists.

Architecture lens:
- Keep authz export/read-model as a projection over execution capsule final
  authz evidence, export metadata hash, claim-boundary evidence, and no-call
  counters. Do not turn it into a runtime result.

Security lens:
- Return only status, reason, hashes, and counts. Do not return prompt text,
  provider body, provider payload, authorization material, signature, nonce,
  env value, local paths, raw export flags, or operator references.

Testing lens:
- Cover missing expected execution capsule final authz hash.
- Cover missing execution capsule authz export payload.
- Cover complete authz export/read-model with execution still disabled.
- Keep provider/runtime counters at `0`.

Audit lens:
- This is local no-call capsule authz export/read-model evidence. It is not
  provider behavior evidence, model-quality evidence, or execution permission.

## Implementation Scope

Add:

- execution capsule authz export projection helper
- execution capsule authz export read-model helper
- API response execution capsule authz export/read-model fields
- demo summary execution capsule authz export/read-model fields
- expected final authz hash and authz export payload test cases
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

- Execution capsule final authz hash exists and matches the expected hash.
- Execution capsule authz export payload is required.
- Export metadata is represented as a local hash only.
- Claim boundary is represented as a local hash only.
- No-call counter hash is present only when tracked counters are `0`.
- Authz export/read-model keeps execution permission count `0`.
- Public output exposes only status, reason, hashes, and counts.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Rollback

Remove the execution capsule authz export/read-model projection, API/demo
fields, related tests/docs, and return to the `AW-LIVE-39` execution capsule
final authorization boundary.

## Next Candidate

```text
AW-LIVE-41
scope: disabled first-call final no-call execution capsule authorization handoff packet boundary, still no provider call
```

The later handoff packet must remain separate from actual provider execution
until a dedicated call-opening task is explicitly approved.

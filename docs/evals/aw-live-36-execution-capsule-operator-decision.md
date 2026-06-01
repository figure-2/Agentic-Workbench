# AW-LIVE-36 Execution Capsule Operator Decision Boundary

## Conclusion

`AW-LIVE-36` adds a disabled first-call execution capsule operator decision
boundary after the execution capsule operator review. The decision binds the
execution capsule operator review hash, operator decision hash,
claim-boundary hash, and no-call counter hash into a public hash/count
projection.

Execution permission remains closed.

## Scope

- disabled execution capsule operator decision public projection
- expected execution capsule operator review hash match gate
- execution capsule operator decision payload presence gate
- operator decision hash projection
- claim-boundary hash projection
- no-call counter hash projection
- API/demo summary fields

## Non-Scope

- Solar Pro 3 API call
- Upstage SDK import
- `.env` value read
- network call
- provider response parser
- provider quality evaluation
- DAACS target runtime call
- execution permission grant

## Acceptance Evidence

| Gate | Result |
|---|---|
| execution capsule operator review hash exists | covered |
| expected execution capsule operator review hash must match | covered |
| execution capsule operator decision payload is required | covered |
| operator decision is represented as a local hash | covered |
| claim boundary is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| decision still keeps execution permission `0` | covered |
| public decision returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_operator_decision_without_expected_review_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_operator_decision_without_decision_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_execution_capsule_operator_decision_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-36 adds a local disabled execution capsule operator decision that binds
execution capsule operator review, operator decision, claim-boundary, and
no-call counter hashes while keeping execution permission closed.
```

Forbidden:

```text
AW-LIVE-36 invokes a provider call, records a provider response, grants
execution permission, validates a model result, or proves deployment readiness.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The execution capsule operator decision is a public projection over
  sanitized no-call evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, local path, and raw
  operator identity.
- Missing expected execution capsule operator review hash or missing decision
  payload blocks the decision.
- A complete decision still reports
  `execution_capsule_operator_decision_execution_closed` and keeps
  `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The execution capsule operator decision is not provider-result evidence. A
  later implementation must not treat it as proof that a provider or target
  runtime was invoked.

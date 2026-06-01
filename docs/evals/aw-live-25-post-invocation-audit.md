# AW-LIVE-25 Post-Invocation Audit Boundary

## Conclusion

`AW-LIVE-25` adds a disabled first-call post-invocation audit after the
invocation receipt. The audit binds the invocation receipt hash, local
claim-boundary hash, and no-call counter hash into one public projection.

Execution permission remains closed.

## Scope

- disabled post-invocation audit public projection
- expected invocation receipt hash match gate
- post-invocation audit payload presence gate
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
| invocation receipt hash exists | covered |
| expected invocation receipt hash must match | covered |
| post-invocation audit payload is required | covered |
| claim boundary is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| audit still keeps execution permission `0` | covered |
| public audit returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_post_invocation_audit_without_expected_receipt_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_post_invocation_audit_without_audit_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_post_invocation_audit_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-25 adds a local disabled post-invocation audit that binds invocation
receipt, claim-boundary, and no-call counter hashes while keeping execution
permission closed.
```

Forbidden:

```text
AW-LIVE-25 invokes a provider call, records a provider response, grants
execution permission, or validates model quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The post-invocation audit is a public projection over sanitized no-call
  evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Missing expected invocation receipt hash or missing audit payload blocks the
  audit.
- A complete audit still reports `post_invocation_audit_execution_closed` and
  keeps `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The audit is not provider-result evidence. A later implementation must not
  treat it as proof that a provider or target runtime was invoked.

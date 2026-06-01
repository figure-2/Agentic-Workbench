# AW-LIVE-24 Invocation Receipt Boundary

## Conclusion

`AW-LIVE-24` adds a disabled first-call executor invocation receipt after the
executor dispatch record. The receipt binds the dispatch record hash, result
placeholder hash, and no-call counter hash into one public projection.

Execution permission remains closed.

## Scope

- disabled invocation receipt public projection
- expected dispatch record hash match gate
- invocation receipt payload presence gate
- result placeholder hash projection
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
| dispatch record hash exists | covered |
| expected dispatch record hash must match | covered |
| invocation receipt payload is required | covered |
| result placeholder is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| receipt still keeps execution permission `0` | covered |
| public receipt returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_invocation_receipt_without_expected_dispatch_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_invocation_receipt_without_receipt_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_invocation_receipt_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-24 adds a local disabled invocation receipt that binds dispatch,
result-placeholder, and no-call counter hashes while keeping execution
permission closed.
```

Forbidden:

```text
AW-LIVE-24 invokes a provider call, records a real provider response, grants
execution permission, or validates model quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The invocation receipt is a public projection over sanitized no-call
  evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Missing expected dispatch record hash or missing receipt payload blocks the
  receipt.
- A complete receipt still reports `invocation_receipt_execution_closed` and
  keeps `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The receipt is not provider-result evidence. A later implementation must not
  treat it as proof that a provider or target runtime was invoked.

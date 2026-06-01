# AW-LIVE-28 Operator Handback Boundary

## Conclusion

`AW-LIVE-28` adds a disabled first-call operator handback after the closeout
record. The handback binds the closeout record hash, operator-review hash,
claim-boundary hash, and no-call counter hash into one public projection.

Execution permission remains closed.

## Scope

- disabled operator handback public projection
- expected closeout record hash match gate
- operator handback payload presence gate
- operator review hash projection
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
| closeout record hash exists | covered |
| expected closeout record hash must match | covered |
| operator handback payload is required | covered |
| operator review is represented as a local hash | covered |
| claim boundary is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| handback still keeps execution permission `0` | covered |
| public handback returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_operator_handback_without_expected_closeout_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_operator_handback_without_handback_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_operator_handback_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-28 adds a local disabled operator handback that binds closeout,
operator-review, claim-boundary, and no-call counter hashes while keeping
execution permission closed.
```

Forbidden:

```text
AW-LIVE-28 invokes a provider call, records a provider response, grants
execution permission, verifies a live operator action, or validates model
quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The operator handback is a public projection over sanitized no-call evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, local path, and raw
  operator identity.
- Missing expected closeout record hash or missing operator handback payload
  blocks the record.
- A complete handback still reports `operator_handback_execution_closed` and
  keeps `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The operator handback is not provider-result evidence. A later
  implementation must not treat it as proof that a provider or target runtime
  was invoked.

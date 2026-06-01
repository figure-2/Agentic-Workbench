# AW-LIVE-30 Operator Release Attestation Boundary

## Conclusion

`AW-LIVE-30` adds a disabled first-call operator release attestation after the
operator decision packet. The attestation binds the operator decision packet
hash, operator-attestation hash, claim-boundary hash, and no-call counter hash
into one public projection.

Execution permission remains closed.

## Scope

- disabled operator release attestation public projection
- expected operator decision packet hash match gate
- operator release attestation payload presence gate
- operator attestation hash projection
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
| operator decision packet hash exists | covered |
| expected operator decision packet hash must match | covered |
| operator release attestation payload is required | covered |
| operator attestation is represented as a local hash | covered |
| claim boundary is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| attestation still keeps execution permission `0` | covered |
| public attestation returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_operator_release_attestation_without_expected_decision_packet_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_operator_release_attestation_without_attestation_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_operator_release_attestation_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-30 adds a local disabled operator release attestation that binds
decision packet, operator-attestation, claim-boundary, and no-call counter
hashes while keeping execution permission closed.
```

Forbidden:

```text
AW-LIVE-30 invokes a provider call, records a provider response, grants
execution permission, verifies a live operator release, or validates model
quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The operator release attestation is a public projection over sanitized
  no-call evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, local path, and raw
  operator identity.
- Missing expected operator decision packet hash or missing operator release
  attestation payload blocks the attestation.
- A complete attestation still reports
  `operator_release_attestation_execution_closed` and keeps
  `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The operator release attestation is not provider-result evidence. A later
  implementation must not treat it as proof that a provider or target runtime
  was invoked.

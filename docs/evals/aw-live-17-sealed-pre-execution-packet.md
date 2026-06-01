# AW-LIVE-17 Sealed Pre-Execution Packet Boundary

## Conclusion

`AW-LIVE-17` adds a sealed pre-execution packet boundary after the operator
opt-in checklist. The packet binds the handoff hash, operator opt-in hash,
cost/timeout/quota hash, and rollback/abort hash into one no-call public
projection.

Execution permission remains closed.

## Scope

- sealed pre-execution packet public projection
- expected operator opt-in hash match gate
- cost/timeout/quota hash projection
- rollback/abort hash projection
- API/demo summary fields

## Non-Scope

- Solar Pro 3 API call
- Upstage SDK import
- `.env` value read
- network call
- provider response parser
- provider quality evaluation
- DAACS target runtime call
- production operator identity system

## Acceptance Evidence

| Gate | Result |
|---|---|
| operator opt-in hash exists | covered |
| expected operator opt-in hash must match | covered |
| cost/timeout/quota hash is included | covered |
| rollback/abort criteria hash is included | covered |
| default execution remains blocked | covered |
| public packet returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_sealed_packet_without_expected_operator_opt_in_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_sealed_packet_but_keeps_execution_disabled tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_sealed_packet_operator_hash_mismatch tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-17 adds a local no-call sealed pre-execution packet that binds handoff,
operator opt-in, cost/timeout/quota, and rollback/abort hashes.
```

Forbidden:

```text
AW-LIVE-17 grants provider execution permission, performs a provider call, or
validates model quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The sealed packet is a public projection over sanitized no-call evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Missing or mismatched expected operator opt-in hash blocks packet sealing.
- A complete packet still reports `sealed_pre_execution_packet_execution_closed`
  and keeps `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The sealed packet is not an execution token. A later implementation must not
  treat it as sufficient authority to call a provider.

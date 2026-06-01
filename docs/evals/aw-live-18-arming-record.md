# AW-LIVE-18 Live Execution Arming Record Boundary

## Conclusion

`AW-LIVE-18` adds an explicit no-call live execution arming record after the
sealed pre-execution packet. The record binds a sealed packet hash, operator
hash, expiry hash, rollback/abort hash, and abort policy hash into one public
projection.

Execution permission remains closed.

## Scope

- arming record public projection
- expected sealed packet hash match gate
- operator hash projection
- expiry hash projection
- rollback/abort and abort policy hash projection
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
| sealed packet hash exists | covered |
| expected sealed packet hash must match | covered |
| arming record includes operator hash | covered |
| arming record includes expiry hash | covered |
| arming record includes rollback/abort and abort policy hashes | covered |
| execution permission remains `0` | covered |
| public record returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_arming_record_without_expected_sealed_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_arming_record_but_keeps_execution_disabled tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_arming_record_sealed_hash_mismatch tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-18 adds a local no-call arming record that binds sealed packet,
operator, expiry, rollback, and abort policy hashes.
```

Forbidden:

```text
AW-LIVE-18 grants provider execution permission, performs a provider call, or
validates model quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The arming record is a public projection over sanitized no-call evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Missing or mismatched expected sealed packet hash blocks arming.
- A complete arming record still reports `arming_record_execution_closed` and
  keeps `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The arming record is not an execution token. A later implementation must not
  treat it as sufficient authority to call a provider.

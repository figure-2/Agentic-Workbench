# AW-LIVE-19 Execution Authorization Release Proposal Boundary

## Conclusion

`AW-LIVE-19` adds a no-call execution authorization release proposal after the
arming record. The proposal binds the arming record hash, operator hash,
release window hash, and rollback/abort hash into one public projection.

Execution permission remains closed.

## Scope

- release proposal public projection
- expected arming record hash match gate
- release operator hash projection
- release window hash projection
- rollback/abort hash match projection
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
| arming record hash exists | covered |
| expected arming record hash must match | covered |
| release proposal includes operator hash | covered |
| release proposal includes release window hash | covered |
| rollback/abort hash matches arming record | covered |
| execution permission remains `0` | covered |
| public proposal returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_release_proposal_without_expected_arming_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_release_proposal_but_keeps_execution_disabled tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_release_proposal_arming_hash_mismatch tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-19 adds a local no-call release proposal that binds arming record,
operator, release window, and rollback/abort hashes.
```

Forbidden:

```text
AW-LIVE-19 grants provider execution permission, performs a provider call, or
validates model quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The release proposal is a public projection over sanitized no-call evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Missing or mismatched expected arming record hash blocks release proposal
  completion.
- A complete release proposal still reports `release_proposal_execution_closed`
  and keeps `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The release proposal is not an execution token. A later implementation must
  not treat it as sufficient authority to call a provider.

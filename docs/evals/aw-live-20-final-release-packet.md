# AW-LIVE-20 Final Release Packet Boundary

## Conclusion

`AW-LIVE-20` adds a no-call final release packet after the release proposal.
The packet binds the release proposal hash, arming record hash, operator hash,
release window hash, and rollback/abort hash into one public projection.

Execution permission remains closed.

## Scope

- final release packet public projection
- expected release proposal hash match gate
- release proposal hash projection
- arming record hash projection
- operator, release window, and rollback/abort hash projection
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
| release proposal hash exists | covered |
| expected release proposal hash must match | covered |
| final packet includes arming record hash | covered |
| final packet includes operator hash | covered |
| final packet includes release window hash | covered |
| final packet includes rollback/abort hash | covered |
| execution permission remains `0` | covered |
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
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_final_release_packet_without_expected_release_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_final_release_packet_but_keeps_execution_disabled tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_final_release_packet_proposal_hash_mismatch tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-20 adds a local no-call final release packet that binds release
proposal, arming record, operator, release window, and rollback/abort hashes.
```

Forbidden:

```text
AW-LIVE-20 grants provider execution permission, performs a provider call, or
validates model quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The final release packet is a public projection over sanitized no-call
  evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Missing or mismatched expected release proposal hash blocks final packet
  completion.
- A complete final release packet still reports
  `final_release_packet_execution_closed` and keeps
  `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The final release packet is not an execution token. A later implementation
  must not treat it as sufficient authority to call a provider.

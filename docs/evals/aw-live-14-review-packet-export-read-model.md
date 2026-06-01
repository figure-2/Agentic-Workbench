# AW-LIVE-14 Review Packet Export Read Model

## Conclusion

`AW-LIVE-14` adds a no-call review packet export and read model. The export
stores only the review packet hash, export hash, status, reason, and counts.

Execution permission remains closed.

## Scope

- review packet export row
- review packet export public read model
- API/demo read-model projection updates
- mismatch gate for expected review packet hash

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
| review packet export row uses hash/status/reason/count fields | covered |
| API read-model returns stored packet export | covered |
| demo summary reads stored packet export | covered |
| packet hash mismatch blocked before adapter admission | covered |
| approve decision grants execution permission | 0 |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\unit\test_provider_envelope_store.py tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_reads_review_packet_export_model_without_execution tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_review_packet_export_hash_mismatch tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-14 adds a local no-call review packet export/read-model with sanitized
hash and count fields.
```

Forbidden:

```text
AW-LIVE-14 proves provider behavior, validates model quality, or grants
provider execution permission.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The export row stores only sanitized hash/status/reason/count fields.
- Public read-model output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Mismatched expected packet hash blocks before adapter admission.
- Approve readiness decision still leaves execution permission count at `0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The export/read-model is still local evidence only. A later implementation
  must not treat it as an execution token.

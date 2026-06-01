# AW-LIVE-26 Completion Summary Boundary

## Conclusion

`AW-LIVE-26` adds a disabled first-call completion summary after the
post-invocation audit. The summary binds the post-invocation audit hash,
claim-boundary hash, and no-call counter hash into one public projection.

Execution permission remains closed.

## Scope

- disabled completion summary public projection
- expected post-invocation audit hash match gate
- completion summary payload presence gate
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
| post-invocation audit hash exists | covered |
| expected post-invocation audit hash must match | covered |
| completion summary payload is required | covered |
| claim boundary is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| summary still keeps execution permission `0` | covered |
| public summary returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_completion_summary_without_expected_audit_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_completion_summary_without_summary_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_completion_summary_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-26 adds a local disabled completion summary that binds
post-invocation audit, claim-boundary, and no-call counter hashes while
keeping execution permission closed.
```

Forbidden:

```text
AW-LIVE-26 invokes a provider call, records a provider response, grants
execution permission, or validates model quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The completion summary is a public projection over sanitized no-call
  evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Missing expected post-invocation audit hash or missing completion payload
  blocks the summary.
- A complete summary still reports `completion_summary_execution_closed` and
  keeps `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The completion summary is not provider-result evidence. A later
  implementation must not treat it as proof that a provider or target runtime
  was invoked.

# AW-LIVE-33 Execution Capsule Export Read Model Boundary

## Conclusion

`AW-LIVE-33` adds a disabled first-call execution capsule export/read-model
boundary after the execution authorization capsule. The export binds the
execution capsule hash, export metadata hash, claim-boundary hash, and no-call
counter hash into a public hash/count projection.

Execution permission remains closed.

## Scope

- disabled execution capsule export public projection
- expected execution capsule hash match gate
- execution capsule export payload presence gate
- export metadata hash projection
- export read-model projection
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
| execution capsule hash exists | covered |
| expected execution capsule hash must match | covered |
| execution capsule export payload is required | covered |
| export metadata is represented as a local hash | covered |
| claim boundary is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| export still keeps execution permission `0` | covered |
| public export returns only status, reason, hashes, and counts | covered |
| public read model returns only latest hash and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_export_without_expected_capsule_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_export_without_export_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_execution_capsule_export_read_model_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-33 adds a local disabled execution capsule export/read-model that
binds execution capsule, export metadata, claim-boundary, and no-call counter
hashes while keeping execution permission closed.
```

Forbidden:

```text
AW-LIVE-33 invokes a provider call, records a provider response, grants
execution permission, validates a model result, or proves deployment readiness.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The execution capsule export is a public projection over sanitized no-call
  evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, local path, and raw
  operator identity.
- Missing expected execution capsule hash or missing export payload blocks the
  export.
- A complete export still reports `execution_capsule_export_execution_closed`
  and keeps `execution_permission_count=0`.
- The read model exposes only the latest export hash and count fields.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The execution capsule export is not provider-result evidence. A later
  implementation must not treat it as proof that a provider or target runtime
  was invoked.

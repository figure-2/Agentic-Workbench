# AW-LIVE-47 Execution Capsule Authz Final Authz Export Boundary

## Conclusion

`AW-LIVE-47` adds a disabled first-call execution capsule authorization final
authorization export/read-model boundary after `AW-LIVE-46`. The export binds
the execution capsule authz final-authorization hash, export metadata hash,
claim-boundary hash, and no-call counter hash into a public hash/count
projection.

Execution permission remains closed.

## Scope

- disabled execution capsule authz final-authorization export projection
- expected execution capsule authz final-authorization hash match gate
- export payload presence gate
- export metadata hash projection
- export/read-model public projection
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
| execution capsule authz final-authorization hash exists | covered |
| expected execution capsule authz final-authorization hash must match | covered |
| execution capsule authz final-authorization export payload is required | covered |
| export metadata is represented as a local hash | covered |
| export request is represented as a count only | covered |
| claim boundary is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| export still keeps execution permission `0` | covered |
| read-model returns latest export hash and counts only | covered |
| public export returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_export_without_expected_final_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_authz_final_authz_export_without_export_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_execution_capsule_authz_final_authz_export_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-47 adds a local disabled execution capsule authorization final
authorization export/read-model that binds authz final-authorization, export
metadata, claim-boundary, and no-call counter hashes while keeping execution
permission closed.
```

Forbidden:

```text
AW-LIVE-47 invokes a provider call, records a provider response, grants
execution permission, validates a model result, or proves deployment readiness.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The execution capsule authz final-authorization export/read-model is a
  public projection over sanitized no-call evidence.
- The export exposes only hashes, status, reason, and counts.
- The read-model exposes only status, reason, latest export hash, and counts.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, local path, and raw
  operator identity.
- Missing expected execution capsule authz final-authorization hash or missing
  export payload blocks the boundary.
- A complete export still reports
  `execution_capsule_authz_final_authz_export_execution_closed` and keeps
  `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The export/read-model is not provider-result evidence. A later
  implementation must not treat it as proof that a provider or target runtime
  was invoked.

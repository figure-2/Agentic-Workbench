# AW-LIVE-32 Execution Authorization Capsule Boundary

## Conclusion

`AW-LIVE-32` adds a disabled first-call execution authorization capsule after
the release authorization seal. The capsule binds the release seal hash, final
authorization hash, claim-boundary hash, and no-call counter hash into one
public projection.

Execution permission remains closed.

## Scope

- disabled execution capsule public projection
- expected release seal hash match gate
- execution authorization capsule payload presence gate
- final authorization hash projection
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
| release seal hash exists | covered |
| expected release seal hash must match | covered |
| execution authorization capsule payload is required | covered |
| final authorization is represented as a local hash | covered |
| claim boundary is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| capsule still keeps execution permission `0` | covered |
| public capsule returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_without_expected_release_seal_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_without_capsule_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_execution_capsule_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-32 adds a local disabled execution authorization capsule that binds
release seal, final authorization, claim-boundary, and no-call counter hashes
while keeping execution permission closed.
```

Forbidden:

```text
AW-LIVE-32 invokes a provider call, records a provider response, grants
execution permission, validates a model result, or proves deployment readiness.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The execution authorization capsule is a public projection over sanitized
  no-call evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, local path, and raw
  operator identity.
- Missing expected release seal hash or missing execution authorization capsule
  payload blocks the capsule.
- A complete capsule still reports
  `execution_authorization_capsule_execution_closed` and keeps
  `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The execution authorization capsule is not provider-result evidence. A later
  implementation must not treat it as proof that a provider or target runtime
  was invoked.

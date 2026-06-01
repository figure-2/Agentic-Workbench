# AW-LIVE-41 Execution Capsule Authz Handoff Packet Boundary

## Conclusion

`AW-LIVE-41` adds a disabled first-call execution capsule authorization
handoff packet after the execution capsule authz export/read-model. The
handoff packet binds the authz export hash, authz export read-model hash,
claim-boundary hash, and no-call counter hash into a public hash/count
projection.

Execution permission remains closed.

## Scope

- disabled execution capsule authz handoff packet public projection
- expected execution capsule authz export hash match gate
- execution capsule authz handoff packet payload presence gate
- authz export read-model availability gate
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
| execution capsule authz export hash exists | covered |
| expected execution capsule authz export hash must match | covered |
| execution capsule authz handoff packet payload is required | covered |
| authz export read-model latest hash must match export hash | covered |
| handoff request is represented as a count only | covered |
| claim boundary is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| handoff packet still keeps execution permission `0` | covered |
| public handoff returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_authz_handoff_without_expected_export_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_authz_handoff_without_packet_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_execution_capsule_authz_handoff_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-41 adds a local disabled execution capsule authorization handoff
packet that binds authz export, read-model, claim-boundary, and no-call
counter hashes while keeping execution permission closed.
```

Forbidden:

```text
AW-LIVE-41 invokes a provider call, records a provider response, grants
execution permission, validates a model result, or proves deployment readiness.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The execution capsule authz handoff packet is a public projection over
  sanitized no-call evidence.
- The handoff packet exposes only hashes, status, reason, and counts.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, local path, and raw
  operator identity.
- Missing expected execution capsule authz export hash or missing handoff
  payload blocks the boundary.
- A complete handoff still reports
  `execution_capsule_authz_handoff_packet_execution_closed` and keeps
  `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The execution capsule authz handoff packet is not provider-result evidence.
  A later implementation must not treat it as proof that a provider or target
  runtime was invoked.

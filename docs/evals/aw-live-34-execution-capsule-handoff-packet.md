# AW-LIVE-34 Execution Capsule Handoff Packet Boundary

## Conclusion

`AW-LIVE-34` adds a disabled first-call execution capsule handoff packet after
the execution capsule export/read-model. The packet binds the execution capsule
export hash, export read-model hash, claim-boundary hash, and no-call counter
hash into a public hash/count projection.

Execution permission remains closed.

## Scope

- disabled execution capsule handoff packet public projection
- expected execution capsule export hash match gate
- execution capsule handoff packet payload presence gate
- export read-model hash projection
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
| execution capsule export hash exists | covered |
| expected execution capsule export hash must match | covered |
| execution capsule handoff packet payload is required | covered |
| export read model is represented as a local hash | covered |
| claim boundary is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| packet still keeps execution permission `0` | covered |
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
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_handoff_without_expected_export_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_capsule_handoff_without_packet_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_execution_capsule_handoff_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-34 adds a local disabled execution capsule handoff packet that binds
execution capsule export, export read model, claim-boundary, and no-call
counter hashes while keeping execution permission closed.
```

Forbidden:

```text
AW-LIVE-34 invokes a provider call, records a provider response, grants
execution permission, validates a model result, or proves deployment readiness.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The execution capsule handoff packet is a public projection over sanitized
  no-call evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, local path, and raw
  operator identity.
- Missing expected execution capsule export hash or missing handoff packet
  payload blocks the packet.
- A complete packet still reports
  `execution_capsule_handoff_packet_execution_closed` and keeps
  `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The execution capsule handoff packet is not provider-result evidence. A
  later implementation must not treat it as proof that a provider or target
  runtime was invoked.

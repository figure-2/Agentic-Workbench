# AW-LIVE-23 Executor Dispatch Record Boundary

## Conclusion

`AW-LIVE-23` adds a disabled first-call executor dispatch record after the
executor preflight. The record binds the executor preflight hash, planned
dispatch hash, and no-call counter hash into one public projection.

Execution permission remains closed.

## Scope

- disabled executor dispatch record public projection
- expected executor preflight hash match gate
- dispatch record payload presence gate
- planned dispatch hash projection
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
| executor preflight hash exists | covered |
| expected executor preflight hash must match | covered |
| dispatch record payload is required | covered |
| planned dispatch is represented as a local hash | covered |
| no-call counters are hashed as a closed local bundle | covered |
| dispatch record still keeps execution permission `0` | covered |
| public dispatch record returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_dispatch_record_without_expected_preflight_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_dispatch_record_without_record_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_dispatch_record_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-23 adds a local disabled executor dispatch record that binds executor
preflight, planned dispatch, and no-call counter hashes while keeping execution
permission closed.
```

Forbidden:

```text
AW-LIVE-23 dispatches a provider call, grants execution permission, or validates
model quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The executor dispatch record is a public projection over sanitized no-call
  evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Missing expected executor preflight hash or missing dispatch record payload
  blocks the record.
- A complete dispatch record still reports
  `executor_dispatch_record_execution_closed` and keeps
  `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The dispatch record is not an execution command. A later implementation must
  not treat it as sufficient authority to call a provider.

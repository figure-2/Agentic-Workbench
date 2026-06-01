# AW-LIVE-22 Executor Preflight Boundary

## Conclusion

`AW-LIVE-22` adds a disabled first-call executor preflight after the execution
switch. The preflight binds the execution switch hash, final release packet
hash, and no-call counter hash into one public projection.

Execution permission remains closed.

## Scope

- disabled executor preflight public projection
- expected execution switch hash match gate
- executor preflight payload presence gate
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
| execution switch hash exists | covered |
| expected execution switch hash must match | covered |
| executor preflight payload is required | covered |
| no-call counters are hashed as a closed local bundle | covered |
| preflight still keeps execution permission `0` | covered |
| public preflight returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_executor_preflight_without_expected_switch_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_executor_preflight_without_preflight_payload tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_executor_preflight_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-22 adds a local disabled executor preflight that binds execution
switch, final release packet, and no-call counter hashes while keeping
execution permission closed.
```

Forbidden:

```text
AW-LIVE-22 grants provider execution permission, performs a provider call, or
validates model quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The executor preflight is a public projection over sanitized no-call
  evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Missing expected execution switch hash or missing executor preflight payload
  blocks the preflight.
- A complete preflight still reports `executor_preflight_execution_closed` and
  keeps `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The preflight is not an execution token. A later implementation must not treat
  it as sufficient authority to call a provider.

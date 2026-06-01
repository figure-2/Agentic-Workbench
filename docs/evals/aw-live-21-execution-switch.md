# AW-LIVE-21 Disabled Execution Switch Boundary

## Conclusion

`AW-LIVE-21` adds a disabled first-call execution switch after the final
release packet. The switch binds the final release packet hash and a switch
enable hash into one public projection.

Execution permission remains closed.

## Scope

- disabled execution switch public projection
- expected final release packet hash match gate
- explicit switch enable flag gate
- switch enable hash projection
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
| final release packet hash exists | covered |
| expected final release packet hash must match | covered |
| execution switch requires a separate enable flag | covered |
| enable flag still keeps execution permission `0` | covered |
| public switch returns only status, reason, hashes, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_switch_without_expected_final_hash tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_execution_switch_without_enable_flag tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_builds_execution_switch_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-21 adds a local disabled execution switch that binds final release
packet and switch-enable hashes while keeping execution permission closed.
```

Forbidden:

```text
AW-LIVE-21 grants provider execution permission, performs a provider call, or
validates model quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The execution switch is a public projection over sanitized no-call evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Missing expected final release packet hash or missing enable flag blocks the
  switch.
- A complete switch still reports `execution_switch_disabled_by_default` and
  keeps `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The switch is not an execution token. A later implementation must not treat
  it as sufficient authority to call a provider.

# AW-LIVE-09 Disabled Manual Provider Test Executor

## Conclusion

`AW-LIVE-09` adds a disabled manual provider test executor projection. The
projection remains blocked even when the proposal gate is accepted and even
when the executor flag is present.

Provider and runtime execution remain closed.

## Scope

- disabled executor public projection
- planned call hash
- blocked reason for missing executor flag
- blocked reason for enabled-but-disabled executor
- API/demo projection updates

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
| accepted proposal still leaves executor blocked | covered |
| missing executor flag blocked | covered |
| executor flag present still blocked | covered |
| executor public projection fields | status / reason / planned_call_hash |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_persists_hash_read_model_without_external_calls tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_accepts_manual_test_proposal_but_keeps_execution_disabled tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_manual_executor_even_when_enable_requested tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-09 adds a disabled local executor boundary for manual provider test
proposals.
```

Forbidden:

```text
AW-LIVE-09 opens a provider, proves provider behavior, validates provider
quality, or establishes production provider readiness.
```

## External Audit

Finding: no blocker.

- Accepted proposal does not grant executor permission.
- Executor flag does not grant executor permission.
- Executor public projection is narrowed to status, reason, and planned call
  hash.
- No raw prompt, provider body, authorization material, signature, nonce, env
  value, or local path is exposed.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The executor is intentionally disabled. A later permission contract would
  still need separate operator approval and a narrow no-default execution plan.

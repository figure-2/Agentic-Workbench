# AW-LIVE-08 Manual Provider Test Proposal Gate

## Conclusion

`AW-LIVE-08` adds a local manual provider test proposal gate. The proposal must
include run id, prompt contract hash, cost, timeout, quota, rollback id, and
abort criteria hash/count. A separate operator approval must reference the
exact proposal hash.

Provider and runtime execution remain closed.

## Scope

- manual provider test proposal public projection
- proposal hash binding
- separate proposal operator approval
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
| missing proposal approval blocked | covered |
| proposal includes run id and prompt contract hash | covered |
| proposal includes cost/timeout/quota | covered |
| proposal includes rollback id | covered |
| proposal includes abort criteria hash/count | covered |
| accepted proposal status | `approved_disabled` |
| accepted proposal `allowed_to_execute` | false |
| accepted proposal `disabled_by_default` | true |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_persists_hash_read_model_without_external_calls tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_accepts_manual_test_proposal_but_keeps_execution_disabled tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-08 adds a local manual provider test proposal gate that remains disabled
by default.
```

Forbidden:

```text
AW-LIVE-08 opens a provider, proves provider behavior, validates provider
quality, or establishes production provider readiness.
```

## External Audit

Finding: no blocker.

- Missing proposal approval is represented as blocked.
- Accepted proposal remains disabled by default.
- Proposal fields are exposed as hash/count/status/booleans and policy limits,
  not raw prompt or provider payload.
- Execution permission remains closed.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The proposal gate is a local review contract, not an executor. A later task
  must still define and test a disabled executor boundary before any external
  call can be considered.

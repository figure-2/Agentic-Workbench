# AW-LIVE-06 Operator Approval Envelope

## Conclusion

`AW-LIVE-06` requires a local operator approval envelope before provider
envelope precheck can proceed. The approval is bound to a sanitized policy
summary hash that covers cost, timeout, quota, live-open readiness, and
zero-call boundaries.

Provider and runtime execution remain closed.

## Scope

- provider precheck operator policy summary projection
- operator approval envelope projection
- policy summary hash binding
- missing operator approval block before provider envelope store write
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
| provider precheck requires operator approval envelope | covered |
| cost/timeout/quota/readiness public summary | covered |
| operator approval references exact policy summary hash | covered |
| missing operator approval blocks before store write | covered |
| fixture `/api/v1/runs` path provider envelope writes | 0 |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-06 adds a local no-call operator approval envelope for provider
precheck policy summaries.
```

Forbidden:

```text
AW-LIVE-06 opens Solar Pro 3, proves provider behavior, validates provider
quality, or establishes production provider readiness.
```

## External Audit

Finding: no blocker.

- Operator approval is required before repository access and adapter reachability.
- The approval subject is a sanitized summary hash, not raw prompt or provider
  payload.
- Missing operator approval blocks without creating provider envelope rows.
- Public responses include status, summary hash, counts, and zero-call metrics.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The operator envelope is a local projection contract, not a production
  identity or signing system. Any external call must still be opened by a later
  task with explicit cost, quota, timeout, and rollback constraints.

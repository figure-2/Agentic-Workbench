# AW-LIVE-10 One-Shot Live Permission Contract

## Conclusion

`AW-LIVE-10` adds a one-shot permission contract projection. A valid candidate
produces a public-safe hash, expiry, and field count, but the status remains
`blocked` because the executor boundary is still disabled.

Provider and runtime execution remain closed.

## Scope

- one-shot permission public projection
- permission contract hash
- expiry and field count
- blocked reason for missing permission
- blocked reason for blocked executor
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
| executor blocked state keeps permission blocked | covered |
| permission candidate has required contract fields | covered |
| permission public projection fields | status / reason / hash / expiry / count |
| permission presence does not enable execution | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_persists_hash_read_model_without_external_calls tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_one_shot_permission_when_executor_blocked tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-10 adds a blocked one-shot permission contract projection for a local
manual provider test candidate.
```

Forbidden:

```text
AW-LIVE-10 proves provider behavior, validates model quality, or establishes
service launch readiness.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- Executor blocked state remains the controlling condition.
- Permission public projection is narrowed to status, reason, hash, expiry, and
  count.
- No raw prompt, provider body, authorization material, signature, nonce, env
  value, or local path is exposed.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The permission contract is intentionally not an execution token. A later
  preflight audit bundle should still require an explicit manual decision.

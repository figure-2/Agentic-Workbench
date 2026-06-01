# AW-LIVE-12 Readiness Decision Record

## Conclusion

`AW-LIVE-12` adds a blocked readiness decision record. A valid decision produces
a public-safe hash and counts, but the status remains `blocked` and execution
permission count remains `0`.

Provider and runtime execution remain closed.

## Scope

- readiness decision public projection
- preflight audit hash binding
- approve/reject/defer count fields
- blocked reason for preflight hash mismatch
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
| decision record created from preflight hash | covered |
| approve decision represented by counts | covered |
| reject decision represented by counts | covered |
| defer decision represented by counts | covered |
| preflight hash mismatch blocked | covered |
| decision projection fields | status / reason / hash / counts |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_records_readiness_decision_without_execution tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_readiness_decision_hash_mismatch tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_represents_reject_and_defer_decisions tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-12 adds a blocked local readiness decision record for a manual provider
test candidate.
```

Forbidden:

```text
AW-LIVE-12 proves provider behavior, validates model quality, or establishes
service launch readiness.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- Decision record is bound to the current preflight audit hash.
- Public output is limited to status, reason, hash, and counts.
- Approve/reject/defer do not grant execution permission.
- Missing or mismatched preflight hash remains blocked.
- No raw prompt, provider body, authorization material, signature, nonce, env
  value, or local path is exposed.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The record is intentionally not a live-call approval. A later review packet
  should still remain separate from any adapter invocation.

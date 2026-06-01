# AW-LIVE-16 Operator Opt-In Checklist Boundary

## Conclusion

`AW-LIVE-16` adds a first live-call operator opt-in checklist boundary after
the no-call handoff packet. The checklist binds the operator opt-in to the
expected handoff packet hash and still keeps execution permission closed.

This boundary does not call Solar Pro 3, import provider SDKs, read `.env`
values, open network paths, or run target runtime code.

## Scope

- operator opt-in public projection
- API/demo summary fields
- handoff packet hash binding
- missing opt-in and mismatched opt-in gates
- execution permission count fixed at `0`

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
| handoff packet hash is required | covered |
| opt-in handoff hash must match expected handoff hash | covered |
| missing operator opt-in remains blocked | covered |
| complete opt-in still keeps execution permission closed | covered |
| public projection returns only status, reason, hash, and counts | covered |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization material exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_missing_operator_opt_in_without_execution tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_accepts_operator_opt_in_but_keeps_execution_disabled tests\integration\test_api_public_projection.py::test_provider_envelope_precheck_api_blocks_operator_opt_in_handoff_mismatch tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q
python -m pytest tests\integration\test_api_public_projection.py tests\smoke\test_local_service_demo.py tests\unit\test_public_claim_projection_docs.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-16 adds a local no-call operator opt-in checklist that binds a manual
provider test candidate to the expected handoff packet hash.
```

Forbidden:

```text
AW-LIVE-16 grants provider execution permission, proves provider behavior, or
validates model quality.
```

## External Audit

Finding: no blocker expected if the listed tests pass.

- The opt-in checklist is a public projection over sanitized handoff evidence.
- Public output excludes raw prompt, provider body, provider payload,
  authorization material, signature, nonce, env value, and local path.
- Missing or mismatched handoff hash blocks the opt-in projection.
- A complete opt-in still reports `operator_opt_in_execution_closed` and keeps
  `execution_permission_count=0`.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- The opt-in checklist is not an execution token. A later implementation must
  keep it separate from any provider invocation mechanism.

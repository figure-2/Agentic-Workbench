# AW-LIVE-04 Provider Envelope Admission Service

## Conclusion

`AW-LIVE-04` adds a provider envelope admission service that must pass before a
disabled Solar live adapter can be invoked. The service persists no-call
contract evidence, reads it back through the public provider envelope read
model, verifies matching request/response hashes, and only then reaches the
disabled adapter.

Provider and runtime calls remain closed.

## Scope

- `ProviderEnvelopeAdmissionService`
- `ProviderEnvelopeAdmissionResult`
- `invoke_adapter_after_provider_envelope_admission`
- unit tests for ordering, missing service, contract mismatch, corrupted store,
  sanitized public output, no-call guards, and duplicate matching evidence

## Non-Scope

- Solar Pro 3 API call
- Upstage SDK import
- `.env` value read
- network call
- provider response parser
- provider quality evaluation
- hosted execution
- production provider readiness

## Acceptance Evidence

| Gate | Result |
|---|---|
| provider envelope row saved before disabled adapter invocation | covered |
| provider envelope read model checked before disabled adapter invocation | covered |
| missing admission service | blocked |
| request contract hash mismatch | blocked |
| response contract hash mismatch | blocked |
| corrupted SQLite envelope store | blocked |
| duplicate matching evidence | admitted as duplicate |
| raw prompt/provider body/provider payload storage or public exposure | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |
| forbidden public key findings | 0 |

## Measured Commands

```powershell
python -m pytest tests\unit\test_provider_envelope_admission.py -q
python -m pytest tests\unit\test_provider_envelope_admission.py tests\unit\test_provider_envelope_store.py tests\unit\test_solar_live_adapter.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-04 adds a local no-call provider envelope admission service that checks
hash-bound evidence before a disabled Solar adapter path can be reached.
```

Forbidden:

```text
AW-LIVE-04 calls Solar Pro 3, validates model output, proves provider quality,
parses provider responses, or opens production provider execution.
```

## External Audit

Finding: no blocker.

- The service is explicit and testable instead of hidden inside adapter logic.
- Missing service, hash mismatch, and store corruption block before adapter
  invocation.
- Valid no-call envelope evidence reaches the disabled adapter, which still
  blocks because provider execution is not implemented.
- Raw prompt/body/provider values remain absent from stored rows and public
  results.
- No SDK import, env value read, network call, or external API call is present.

Residual risk:

- This is still a service boundary for local evidence ordering. Future work
  must decide whether to expose this through API/demo read models before any
  provider adapter path is opened.

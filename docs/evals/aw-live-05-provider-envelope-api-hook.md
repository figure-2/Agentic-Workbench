# AW-LIVE-05 Provider Envelope API Hook

## Conclusion

`AW-LIVE-05` connects the no-call provider envelope admission service to local
API and demo read-model paths. The API can persist and read provider envelope
evidence as status, hashes, and counts only. The disabled adapter can be reached
only after that evidence passes, and it still blocks before any external call.

## Scope

- `ProviderEnvelopeRepositoryConfig`
- `ProviderEnvelopeRepositoryProvider`
- `run_provider_envelope_precheck`
- `read_provider_envelope_precheck`
- `POST /api/v1/admissions/provider/envelope/precheck`
- `GET /api/v1/admissions/provider/envelopes/{run_id}`
- optional local demo provider envelope precheck

## Non-Scope

- Solar Pro 3 API call
- Upstage SDK import
- `.env` value read
- network call
- provider response parser
- provider quality evaluation
- DAACS target runtime call
- hosted or production provider readiness

## Acceptance Evidence

| Gate | Result |
|---|---|
| API path optionally uses `ProviderEnvelopeAdmissionService` | covered |
| Demo path optionally uses provider envelope precheck | covered |
| public response exposes status/hash/count only | covered |
| missing provider envelope store | blocked |
| corrupted provider envelope store | blocked |
| fixture `/api/v1/runs` path provider envelope writes | 0 |
| raw prompt/provider body/provider payload exposure | 0 |
| raw approval authorization field exposure | 0 |
| SDK imports | 0 |
| env value reads | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\integration\test_api_public_projection.py -q
python -m pytest tests\smoke\test_local_service_demo.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-05 adds a local no-call provider envelope admission API/read-model hook
that exposes sanitized status, hashes, and counts.
```

Forbidden:

```text
AW-LIVE-05 proves external provider behavior, provider quality, hosted provider
service behavior, or production provider readiness.
```

## External Audit

Finding: no blocker.

- The API hook is optional and server-side configured.
- Missing or corrupted provider envelope storage blocks before adapter
  admission.
- Fixture/dry-run run creation remains separate from provider envelope precheck.
- Public responses include hash/count/status projections only.
- Raw prompt/body/provider values and approval authorization fields are not
  present in tested public output.
- No SDK import, env value read, network call, external API call, or target
  runtime call is present.

Residual risk:

- This still proves local evidence ordering, not provider execution. Future
  work must add explicit operator approval and cost/timeout envelopes before
  any external provider implementation unit.

# AW-LIVE-05 Work Order: Provider Envelope API Hook

## Conclusion

`AW-LIVE-05` exposes the existing provider envelope admission boundary through
local API and demo read-model projections. It is still a no-call precheck. The
goal is to make provider envelope admission visible without turning it into a
provider outcome or runtime claim.

## Task Definition

```text
id: AW-LIVE-05
depends_on: AW-LIVE-04
scope: provider admission service API/read-model projection hook, still no external call
risk_level: high
rollback_plan: API/read-model hook 제거, AW-LIVE-04 service boundary 유지
```

## Background

`AW-LIVE-04` already proves this internal chain:

```text
Solar no-call contract fixture
-> ProviderEnvelopeAdmissionService
-> Provider envelope row save
-> Provider envelope public read model
-> disabled Solar adapter reached
-> blocked, no external call
```

Before a future provider adapter can be opened, API/demo users need a safe way
to see whether that evidence chain passed. That requires a public projection
over status, hashes, and counts only.

## Specialist Review

Product lens:
- The feature must be presented as a local readiness/evidence precheck.
- It must not imply provider output quality, hosted execution, or app
  generation.

Architecture lens:
- Add a thin API/service hook rather than moving admission logic into
  `main.py`.
- Keep `/api/v1/runs` fixture/dry-run separate from provider envelope
  precheck.

Security lens:
- Public responses may expose request/response contract hashes and counts.
- Public responses must not expose raw prompt, provider body, provider payload,
  SDK payloads, env values, or approval authorization fields.

Testing lens:
- Test missing/corrupted provider envelope store before adapter admission.
- Test that default fixture run paths do not create provider envelope rows.

Audit lens:
- Allowed claim: local no-call provider envelope admission can be viewed
  through sanitized API/demo projections.
- Forbidden claim: this proves external provider behavior or production
  provider readiness.

## Implementation Scope

Add:

- `ProviderEnvelopeRepositoryConfig`
- `ProviderEnvelopeRepositoryProvider`
- `run_provider_envelope_precheck`
- `read_provider_envelope_precheck`
- `POST /api/v1/admissions/provider/envelope/precheck`
- `GET /api/v1/admissions/provider/envelopes/{run_id}`
- optional demo flag for provider envelope precheck
- integration/smoke tests

## Non-Scope

- No Solar Pro 3 API call.
- No Upstage SDK import.
- No `.env` value read.
- No network call.
- No provider response parser.
- No provider quality evaluation.
- No DAACS target runtime call.
- No execution permission grant.

## Acceptance Tests

- API/demo path can optionally use `ProviderEnvelopeAdmissionService`.
- Public response exposes provider envelope admission status, request/response
  contract hashes, and counts only.
- Missing or corrupted provider envelope store blocks before adapter admission.
- Fixture/dry-run `/api/v1/runs` path does not touch provider envelope store.
- Raw prompt/provider body/provider payload exposure remains `0`.
- SDK import, env value read, API call, and network call remain `0`.
- Full regression suite remains green.

## Suggested Files

- `apps/api/agentic_workbench_api/services/provider_envelope_api.py`
- `apps/api/agentic_workbench_api/main.py`
- `examples/demo-service-flow/run_local_demo.py`
- `tests/integration/test_api_public_projection.py`
- `tests/smoke/test_local_service_demo.py`
- `docs/evals/aw-live-05-provider-envelope-api-hook.md`
- `docs/metrics.md`
- `README.md`
- `docs/architecture.md`
- `docs/claim-boundary.md`

## Rollback

Remove the provider envelope API service file, remove the two API routes, remove
demo precheck option/tests, and keep the `AW-LIVE-04` service boundary intact.

## Next Candidate

```text
AW-LIVE-06
scope: provider precheck policy UX and explicit operator approval envelope
```

This should still avoid external calls until cost, timeout, audit, and operator
approval rules are fully closed.

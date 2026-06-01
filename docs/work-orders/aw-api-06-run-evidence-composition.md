# AW-API-06 Work Order: Canonical Run and Evidence Composition

## Conclusion

The next implementation unit is `AW-API-06`. Its purpose is to make
`GET /api/v1/runs/{run_id}` useful as the main local service read endpoint
without opening live provider or target runtime execution.

## Senior Review Decision

Product lens:

- A first-time user needs one run page/API that explains status, artifacts,
  dry-run evidence, and verification evidence.
- The demo should be shaped like a future service path, but current claims must
  stay fixture/dry-run/fake-boundary.

Architecture lens:

- Canonical run state remains primary.
- Evidence is attached as a separate optional summary.
- The composition layer must not merge persistence responsibilities.

Security lens:

- Raw prompt, raw logs, raw file bodies, provider payloads, runtime payloads,
  and approval authorization material stay out of public responses.
- Missing or corrupted evidence must not cause fallback to raw rows.

Data lens:

- Canonical run/artifact store, runner/report/audit evidence store, and
  approval/replay store remain separate.
- API output may contain counts, hashes, linkage status, safe labels, and
  blocked markers.

Test lens:

- This is an integration test first change because the risk is boundary drift
  between stores.

Audit lens:

- The feature must be described as local read-model composition, not generated
  app delivery, provider outcome, or production observability.

## Implementation Unit

```text
id: AW-API-06
depends_on: AW-PERSIST-08
scope: canonical run state + evidence summary composition
risk_level: high
rollback_plan: evidence summary composition 제거, AW-PERSIST-08 canonical read API로 복귀
```

## Scope

Implement a public-safe composed read model for `GET /api/v1/runs/{run_id}`.

The endpoint should return:

- canonical run state
- canonical artifact metadata
- optional runner/report/audit evidence summary
- optional approval/replay evidence summary if repository configuration exists
- repository boundary metadata
- zero-call execution boundary metrics
- claim boundary markers

The endpoint must not return:

- raw prompt
- raw artifact payload body
- raw planned action body
- raw log or stack trace
- raw file body
- provider request/response payload
- runtime payload
- raw approval authorization material
- local DB root path
- raw repository row

## Recommended API Shape

```json
{
  "projection_version": "canonical-run-composed-read-model-public-v1",
  "run_id": "run-example",
  "status": "passed",
  "runtime_mode": "read_model",
  "run": {
    "run_id": "run-example",
    "stage": "verified",
    "status": "completed",
    "prompt_contract_hash": "hash...",
    "idea_summary": "safe summary"
  },
  "artifacts": [],
  "evidence_summary": {
    "status": "available",
    "runner_plan_count": 1,
    "verification_report_count": 1,
    "audit_event_count": 2,
    "approval_count": 0,
    "replay_nonce_count": 0,
    "linkage": {
      "run_id_matched": true,
      "artifact_linkage_checked": true
    },
    "checks": []
  },
  "repository_boundary": {
    "canonical_run_artifact_backend": "sqlite",
    "runner_report_audit_backend": "sqlite",
    "approval_replay_backend": "not_queried_or_unconfigured",
    "raw_row_returned": false,
    "root_path_returned": false
  },
  "execution_boundary": {
    "solar_provider_calls": 0,
    "target_runtime_calls": 0
  },
  "claim_boundary": {
    "local_read_model_only": true,
    "external_provider_outcome": false,
    "target_runtime_outcome": false
  }
}
```

This shape is a target for implementation, not current behavior.

## Acceptance Tests

- `GET /api/v1/runs/{run_id}` returns canonical run state and safe evidence
  summary when both stores are configured.
- Missing evidence repository keeps canonical run lookup `passed` and returns
  evidence status `unconfigured`.
- Corrupted evidence repository returns canonical run state with evidence
  status `blocked`.
- Corrupted canonical run store blocks canonical run lookup.
- Cross-run evidence leakage is 0.
- Artifact payload body leakage is 0.
- Raw prompt, raw log, raw file body, provider payload, runtime payload, and raw
  approval authorization material leakage is 0.
- Repository boundary says which stores were queried.
- Solar Pro 3 call count remains 0.
- DAACS target runtime call count remains 0.
- Existing test suite remains green.

## Suggested Files

- `apps/api/agentic_workbench_api/main.py`
- `apps/api/agentic_workbench_api/services/canonical_run_store.py`
- `apps/api/agentic_workbench_api/services/evidence_read_model.py`
- `tests/integration/test_api_public_projection.py`
- `docs/evals/aw-api-06-run-evidence-composition.md`
- `docs/metrics.md`
- `docs/architecture.md`
- `docs/claim-boundary.md`

## Implementation Notes

- Prefer adding a small composition helper instead of expanding endpoint logic
  inline.
- Reuse existing sanitizers and public projection assertions.
- Do not make request bodies select local repository paths.
- Do not introduce provider SDK imports.
- Do not read `.env` values.
- Do not call Solar Pro 3.
- Do not call DAACS target runtime.

## Follow-Up Work

```text
AW-DEMO-01
depends_on: AW-API-06
scope: local service-shaped demo flow over composed read model
risk_level: medium
rollback_plan: demo route/script/docs 제거, AW-API-06 유지
```

```text
AW-LIVE-00
depends_on: AW-DEMO-01
scope: live-open checklist and policy ADR before Solar Pro 3 or DAACS runtime calls
risk_level: high
rollback_plan: live-open policy 문서 제거, all live calls remain blocked
```

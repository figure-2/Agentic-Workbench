# AW-MVP-01 Service-Shaped Vertical Slice Eval

## Scope

This eval records the first local service-shaped vertical slice over the
existing public API and read-model boundary.

```text
Idea
-> POST /api/v1/runs
-> PlanningBlueprint / PRDPackage / ImplementationBrief
-> SpecApproval
-> dry-run RunnerPlan
-> VerificationReport
-> GET /api/v1/runs/{run_id}
-> GET /api/v1/runs/{run_id}/artifacts
-> GET /api/v1/runs/{run_id}/verification
```

The slice is local and dry-run only. It does not call providers, read provider
secret values, execute target runtime code, install packages, start generated
apps, or return raw artifact bodies.

## Implemented Public Surfaces

| Surface | Purpose | Public fields |
|---|---|---|
| `POST /api/v1/runs` | Create one fixture-backed run | run hash, stage, status, artifact summaries |
| `GET /api/v1/runs/{run_id}` | Read composed canonical run/evidence summary | counts, linkage, boundaries |
| `GET /api/v1/runs/{run_id}/artifacts` | Read artifact metadata | kind, name, content hash, summary |
| `GET /api/v1/runs/{run_id}/verification` | Read verification evidence | status, counts, report hashes, zero-call counters |
| local demo summary | Human-reviewable service slice | MVP coverage, evidence counts, claim boundary |

## Acceptance Results

| Gate | Result |
|---|---|
| representative golden path scenario | covered, 1 scenario |
| stage coverage | covered, 7/7 |
| `POST /api/v1/runs` creates sanitized run | covered |
| composed run read model available | covered |
| artifact read model available | covered |
| verification read model available | covered |
| unavailable verification store blocked | covered |
| artifact linkage by `run_id` | covered, 100% |
| raw prompt/log/file/provider/runtime exposure | 0 findings |
| raw approval authorization exposure | 0 findings |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |
| public claim drift | 0 findings |

## Quantitative Result

| Metric | Value |
|---|---:|
| Golden path scenario count | 1 |
| Required stage count | 7 |
| Covered stage count | 7 |
| Stage coverage | 100.0% |
| Artifact count in current fixture | 6 |
| Runner plan count | 1 |
| Verification report count | 1 |
| Runner plan hash count in verification read model | 1 |
| Failed report count | 0 |
| Artifact linkage by `run_id` | 100% |
| Forbidden public exposure findings | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |
| Public claim drift findings | 0 |

## Tests

```powershell
python -m compileall apps examples tests
python -m pytest tests\smoke\test_mvp_service_flow.py -q --color=no
python -m pytest tests -q --color=no
.\scripts\verify.ps1
```

Observed result:

```text
compileall: passed
test_mvp_service_flow.py: 2 passed
full regression: 578 passed
verify.ps1: 578 passed
```

## Limitations

- Planning content is still fixture-generated, not provider-generated.
- RunnerPlan and VerificationReport are dry-run evidence, not target workspace
  execution results.
- Static UI remains a shell over public summary data.
- Solar Pro 3 and DAACS target runtime are still closed by default.

## Next Recommended Work

`AW-SOLAR-01` should prepare a provider-backed planner spike behind explicit
policy, cost, timeout, quota, and operator approval controls. `AW-DAACS-RUNTIME-00`
should separately define the target runtime sandbox and file allowlist before
any target workspace execution is considered.

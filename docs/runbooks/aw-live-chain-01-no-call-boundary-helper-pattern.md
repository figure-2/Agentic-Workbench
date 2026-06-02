# AW-LIVE-CHAIN-01 Runbook: No-Call Boundary Helper Pattern

## Purpose

Use this runbook to verify that repeated no-call boundary logic was consolidated
without changing the public projection contract.

This runbook does not authorize live provider execution.

## What Changed

`AW-LIVE-CHAIN-01` introduces a private helper that evaluates:

- upstream projection status and reason
- expected upstream hash
- payload presence
- supplied upstream hash
- local evidence hash
- request flag
- claim-boundary closure
- no-call counter closure

The first adoption covers:

- `AW-LIVE-67` final authorization projection
- `AW-LIVE-68` final authorization export projection

## Expected Public Projection Invariants

The public response must still expose only:

- status
- reason
- hashes
- counts

Required invariant counts:

| Counter | Required |
|---|---:|
| `component_count` | 8 |
| `component_hash_count` on complete path | 4 |
| `no_call_counter_count` | 13 |
| `claim_boundary_check_count` | 3 |
| `execution_permission_count` | 0 |

## Verification Commands

```powershell
python -m compileall apps tests examples
python -m pytest tests\integration\test_api_public_projection.py -q --color=no
python -m pytest tests\smoke\test_local_service_demo.py::test_local_service_demo_can_include_provider_envelope_precheck_without_calls -q --color=no
python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no
python -m pytest tests -q --color=no
.\scripts\verify.ps1
git diff --check
```

## Failure Conditions

Treat the refactor as failed if any of these occur:

- any `AW-LIVE-60` through `AW-LIVE-68` regression test fails
- public field names change
- complete-path public component count changes from `8`
- complete-path public component hash count changes from `4`
- execution permission count becomes non-zero
- raw prompt, provider body, provider payload, approval authorization material,
  env value, SDK import, network call, or target runtime call appears

## Rollback

Revert the helper extraction and restore the explicit `AW-LIVE-67` and
`AW-LIVE-68` implementation blocks. Keep the `AW-LIVE-68` explicit boundary as
the fallback baseline.

## Operator Decision

This runbook allows only local helper-pattern verification. It does not permit
Solar Pro 3 calls, Upstage SDK import, `.env` value reads, network calls, or
DAACS target runtime calls.

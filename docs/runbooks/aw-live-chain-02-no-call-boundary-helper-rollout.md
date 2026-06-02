# AW-LIVE-CHAIN-02 Runbook: No-Call Boundary Helper Rollout

## Purpose

Use this runbook to verify helper adoption across `AW-LIVE-60` through
`AW-LIVE-66`.

This runbook does not authorize live provider execution.

## What Changed

The private no-call boundary helper now evaluates these projections:

- `AW-LIVE-60`
- `AW-LIVE-61`
- `AW-LIVE-62`
- `AW-LIVE-63`
- `AW-LIVE-64`
- `AW-LIVE-65`
- `AW-LIVE-66`
- `AW-LIVE-67`
- `AW-LIVE-68`

`AW-LIVE-62` uses the helper's `local_evidence_present` override so the export
read-model availability check remains stricter than simple hash presence.

## Required Invariants

| Counter | Required |
|---|---:|
| public field name changes | 0 |
| complete-path `component_count` | 8 |
| complete-path `component_hash_count` | 4 |
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

Treat the rollout as failed if any of these occur:

- any provider envelope integration test fails
- any public field name changes
- complete-path component count changes from `8`
- complete-path component hash count changes from `4`
- execution permission count becomes non-zero
- helper adoption changes reason strings
- raw prompt, provider body, provider payload, approval authorization material,
  env value, SDK import, network call, or target runtime call appears

## Rollback

Revert the `AW-LIVE-60` through `AW-LIVE-66` helper adoption and keep the
`AW-LIVE-CHAIN-01` helper usage in `AW-LIVE-67` and `AW-LIVE-68`.

## Operator Decision

This runbook allows only local helper-pattern verification. It does not permit
Solar Pro 3 calls, Upstage SDK import, `.env` value reads, network calls, or
DAACS target runtime calls.

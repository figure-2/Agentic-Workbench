# AW-LIVE-68 Runbook: Execution Capsule Authz Final Authz Final Authorization Final Authorization Final Authorization Export Boundary

## Purpose

Use this runbook to verify the local no-call export/read-model boundary added
after `AW-LIVE-67`.

This runbook does not authorize live provider execution.

## Expected Public Projection

```json
{
  "status": "blocked",
  "reason": "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_execution_closed",
  "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash": "<hash>",
  "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash": "<hash>",
  "export_metadata_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "export_count": 1,
  "component_count": 8,
  "passed_component_count": 8,
  "mismatch_count": 0,
  "component_hash_count": 4,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "export_metadata_count": 1,
  "export_request_count": 1,
  "execution_permission_count": 0
}
```

Expected read-model:

```json
{
  "status": "available",
  "reason": "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model_available",
  "latest_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash": "<hash>",
  "counts": {
    "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_count": 1,
    "component_count": 8,
    "execution_permission_count": 0
  }
}
```

## Manual Check

1. Build a local provider envelope precheck payload with all prerequisite
   no-call stages through `AW-LIVE-67`.
2. Add `expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash`.
3. Add `manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_export`.
4. POST to `/api/v1/admissions/provider/envelope/precheck`.
5. Confirm the export projection is `blocked` with execution permission `0`.
6. Confirm the export read-model is `available` with execution permission `0`.

## Failure Conditions

The boundary must remain blocked when:

- expected final authorization hash is missing
- expected final authorization hash mismatches
- export payload is missing
- supplied final authorization hash mismatches
- export metadata is missing
- export request flag is missing
- claim-boundary hash cannot be closed
- no-call counters are not all `0`

## No-Call Requirements

Required counts:

| Counter | Required |
|---|---:|
| `provider_calls` | 0 |
| `network_calls` | 0 |
| `solar_live_api_calls` | 0 |
| `provider_envelope_env_value_reads` | 0 |
| `provider_envelope_sdk_imports` | 0 |
| `execution_permission_count` | 0 |

## Operator Decision

This runbook allows only a local no-call export/read-model check. It does not
permit Solar Pro 3 calls, Upstage SDK import, `.env` value reads, network calls,
or DAACS target runtime calls.

## Next Step

After AW-LIVE-68, the recommended next work is `AW-LIVE-CHAIN-01`: consolidate
the repeated no-call boundary pattern into helper functions while preserving all
public field names and tests.

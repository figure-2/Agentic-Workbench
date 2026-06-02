# AW-LIVE-69 Runbook: Execution Capsule Authz Final Authz Final Authorization Final Authorization Final Authorization Handoff Boundary

## Purpose

Use this runbook to verify the local no-call handoff packet boundary added
after `AW-LIVE-68`.

This runbook does not authorize live provider execution.

## Expected Public Projection

```json
{
  "status": "blocked",
  "reason": "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_packet_execution_closed",
  "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_handoff_packet_hash": "<hash>",
  "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash": "<hash>",
  "execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_read_model_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "packet_count": 1,
  "component_count": 8,
  "passed_component_count": 8,
  "mismatch_count": 0,
  "component_hash_count": 4,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "export_read_model_count": 1,
  "handoff_request_count": 1,
  "execution_permission_count": 0
}
```

## Manual Check

1. Build a local provider envelope precheck payload with all prerequisite
   no-call stages through `AW-LIVE-68`.
2. Add `expected_execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_export_hash`.
3. Add `manual_test_execution_capsule_authz_final_authz_final_authorization_final_authorization_final_authorization_handoff_packet`.
4. POST to `/api/v1/admissions/provider/envelope/precheck`.
5. Confirm the handoff packet projection is `blocked` with execution permission
   `0`.
6. Confirm no raw prompt, provider payload, authorization material, nonce,
   signature, env value, or local path appears in the response.

## Failure Conditions

The boundary must remain blocked when:

- expected export hash is missing
- expected export hash mismatches
- handoff payload is missing
- supplied export hash mismatches
- export read-model is missing or mismatched
- handoff request flag is missing
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

This runbook allows only a local no-call handoff packet check. It does not
permit Solar Pro 3 calls, Upstage SDK import, `.env` value reads, network calls,
or DAACS target runtime calls.

## Next Step

After AW-LIVE-69, continue to `AW-LIVE-70` only if the disabled evidence chain
still needs another boundary. Otherwise prioritize `AW-LIVE-CHAIN-04` to reduce
older no-call boundary duplication.

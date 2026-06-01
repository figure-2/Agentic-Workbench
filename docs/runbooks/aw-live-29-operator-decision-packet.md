# AW-LIVE-29 Runbook: Operator Decision Packet Boundary

## Conclusion

The operator decision packet is a blocked no-call record after the operator
handback. It proves that a future first-call decision step can be represented
as hashes and counts without opening the provider path.

## Operator Decision Packet Projection

The public operator decision packet returns only:

```json
{
  "status": "blocked",
  "reason": "operator_decision_packet_execution_closed",
  "operator_decision_packet_hash": "<hash>",
  "operator_handback_hash": "<hash>",
  "operator_decision_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "component_count": 8,
  "passed_component_count": 8,
  "mismatch_count": 0,
  "component_hash_count": 4,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "operator_decision_count": 1,
  "decision_packet_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| operator handback | hash is present and execution remains closed |
| expected operator handback hash | equals computed operator handback hash |
| operator decision packet payload | present |
| packet handback hash | equals computed operator handback hash |
| operator decision | represented as a local hash only |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Operator handback hash is missing or mismatched.
- Expected operator handback hash is missing.
- Operator decision packet payload is missing.
- Packet handback hash does not match the computed operator handback hash.
- Operator decision hash is missing.
- Decision packet request flag is missing.
- Claim-boundary checks are not closed.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, nonce, or raw operator identity appears in
  public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The operator decision packet is not provider-result evidence. It is only local
no-call evidence that a future operator decision can be represented without
exposing raw operator data or opening a first-call invocation.

## Rollback

Remove the operator decision packet projection, API/demo fields, related
tests/docs, and return to the AW-LIVE-28 operator handback boundary.

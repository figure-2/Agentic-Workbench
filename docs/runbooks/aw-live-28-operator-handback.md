# AW-LIVE-28 Runbook: Operator Handback Boundary

## Conclusion

The operator handback is a blocked no-call record after the closeout record.
It proves that a future first-call handback step can be represented as hashes
and counts without opening the provider path.

## Operator Handback Projection

The public operator handback returns only:

```json
{
  "status": "blocked",
  "reason": "operator_handback_execution_closed",
  "operator_handback_hash": "<hash>",
  "closeout_record_hash": "<hash>",
  "operator_review_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "component_count": 8,
  "passed_component_count": 8,
  "mismatch_count": 0,
  "component_hash_count": 4,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "operator_review_count": 1,
  "handback_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| closeout record | hash is present and execution remains closed |
| expected closeout record hash | equals computed closeout record hash |
| operator handback payload | present |
| handback closeout hash | equals computed closeout record hash |
| operator review | represented as a local hash only |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Closeout record hash is missing or mismatched.
- Expected closeout record hash is missing.
- Operator handback payload is missing.
- Handback closeout hash does not match the computed closeout record hash.
- Operator review hash is missing.
- Handback request flag is missing.
- Claim-boundary checks are not closed.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, nonce, or raw operator identity appears in
  public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The operator handback is not provider-result evidence. It is only local no-call
evidence that a future operator review can be represented without exposing raw
operator data or opening a first-call invocation.

## Rollback

Remove the operator handback projection, API/demo fields, related tests/docs,
and return to the AW-LIVE-27 closeout record boundary.

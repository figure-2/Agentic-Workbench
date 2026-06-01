# AW-LIVE-26 Runbook: Completion Summary Boundary

## Conclusion

The completion summary is a blocked no-call record after the post-invocation
audit. It proves that a future first-call completion step can be represented
as hashes and counts without opening the provider path.

## Completion Summary Projection

The public completion summary returns only:

```json
{
  "status": "blocked",
  "reason": "completion_summary_execution_closed",
  "completion_summary_hash": "<hash>",
  "post_invocation_audit_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "component_count": 7,
  "passed_component_count": 7,
  "mismatch_count": 0,
  "component_hash_count": 3,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "summary_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| post-invocation audit | hash is present and execution remains closed |
| expected post-invocation audit hash | equals computed post-invocation audit hash |
| completion summary payload | present |
| summary audit hash | equals computed post-invocation audit hash |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Post-invocation audit hash is missing or mismatched.
- Expected post-invocation audit hash is missing.
- Completion summary payload is missing.
- Summary audit hash does not match the computed post-invocation audit hash.
- Claim-boundary checks are not closed.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The completion summary is not provider-result evidence. It is only local
no-call evidence that no first-call invocation has occurred.

## Rollback

Remove the completion summary projection, API/demo fields, related tests/docs,
and return to the AW-LIVE-25 post-invocation audit boundary.

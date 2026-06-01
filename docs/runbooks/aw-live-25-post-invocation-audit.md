# AW-LIVE-25 Runbook: Post-Invocation Audit Boundary

## Conclusion

The post-invocation audit is a blocked no-call record after the invocation
receipt. It proves that a future post-call audit step can be represented as
hashes and counts without opening the provider path.

## Post-Invocation Audit Projection

The public audit summary returns only:

```json
{
  "status": "blocked",
  "reason": "post_invocation_audit_execution_closed",
  "post_invocation_audit_hash": "<hash>",
  "invocation_receipt_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "component_count": 7,
  "passed_component_count": 7,
  "mismatch_count": 0,
  "component_hash_count": 3,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "audit_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| invocation receipt | hash is present and execution remains closed |
| expected invocation receipt hash | equals computed invocation receipt hash |
| post-invocation audit payload | present |
| audit receipt hash | equals computed invocation receipt hash |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Invocation receipt hash is missing or mismatched.
- Expected invocation receipt hash is missing.
- Post-invocation audit payload is missing.
- Audit receipt hash does not match the computed invocation receipt hash.
- Claim-boundary checks are not closed.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The post-invocation audit is not provider-result evidence. It is only local
no-call evidence that no first-call invocation has occurred.

## Rollback

Remove the post-invocation audit projection, API/demo fields, related
tests/docs, and return to the AW-LIVE-24 invocation receipt boundary.

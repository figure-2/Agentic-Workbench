# AW-LIVE-24 Runbook: Invocation Receipt Boundary

## Conclusion

The invocation receipt is a blocked no-call record after the executor dispatch
record. It proves that a future receipt step can be represented as hashes and
counts without opening the provider path.

## Invocation Receipt Projection

The public receipt summary returns only:

```json
{
  "status": "blocked",
  "reason": "invocation_receipt_execution_closed",
  "invocation_receipt_hash": "<hash>",
  "dispatch_record_hash": "<hash>",
  "result_placeholder_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "component_count": 6,
  "passed_component_count": 6,
  "mismatch_count": 0,
  "component_hash_count": 3,
  "no_call_counter_count": 13,
  "receipt_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| dispatch record | hash is present and execution remains closed |
| expected dispatch record hash | equals computed dispatch record hash |
| invocation receipt payload | present |
| receipt dispatch hash | equals computed dispatch record hash |
| result placeholder | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Dispatch record hash is missing or mismatched.
- Expected dispatch record hash is missing.
- Invocation receipt payload is missing.
- Receipt dispatch hash does not match the computed dispatch record hash.
- Result placeholder intent is missing.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The invocation receipt is not provider-result evidence. It is only local no-call
evidence that no first-call invocation has occurred.

## Rollback

Remove the invocation receipt projection, API/demo fields, related tests/docs,
and return to the AW-LIVE-23 executor dispatch record boundary.

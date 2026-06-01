# AW-LIVE-18 Runbook: Live Execution Arming Record Boundary

## Conclusion

The arming record is a blocked no-call record after the sealed pre-execution
packet. It proves that operator intent, expiry, rollback, and abort policy
evidence can be summarized as hashes and counts without opening the provider
path.

## Arming Record Projection

The public arming summary returns only:

```json
{
  "status": "blocked",
  "reason": "arming_record_execution_closed",
  "arming_record_hash": "<hash>",
  "sealed_packet_hash": "<hash>",
  "operator_hash": "<hash>",
  "expiry_hash": "<hash>",
  "rollback_abort_hash": "<hash>",
  "abort_policy_hash": "<hash>",
  "component_count": 8,
  "passed_component_count": 8,
  "mismatch_count": 0,
  "component_hash_count": 5,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| sealed packet | hash is present and execution remains closed |
| expected sealed hash | equals computed sealed packet hash |
| arming payload | present |
| arming sealed hash | equals computed sealed packet hash |
| operator | represented as a hash |
| expiry | represented as a hash |
| rollback/abort | hash matches sealed packet rollback/abort hash |
| abort policy | hash is present |

## Stop Conditions

- Sealed packet hash is missing or mismatched.
- Expected sealed packet hash is missing.
- Arming record is missing.
- Arming record sealed hash does not match the computed sealed hash.
- Operator, expiry, rollback, or abort policy evidence is missing.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The arming record is not an execution token. It is only a local no-call record
for a later provider test candidate.

## Rollback

Remove the arming record projection, API/demo fields, related tests/docs, and
return to the AW-LIVE-17 sealed pre-execution packet boundary.

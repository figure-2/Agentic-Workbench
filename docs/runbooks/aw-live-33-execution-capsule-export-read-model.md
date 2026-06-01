# AW-LIVE-33 Runbook: Execution Capsule Export Read Model Boundary

## Conclusion

The execution capsule export/read-model boundary is a blocked no-call record
after the execution authorization capsule. It proves that a future first-call
execution capsule can be exported as hashes and counts without opening the
provider path.

## Execution Capsule Export Projection

The public execution capsule export returns only:

```json
{
  "status": "blocked",
  "reason": "execution_capsule_export_execution_closed",
  "execution_capsule_export_hash": "<hash>",
  "execution_capsule_hash": "<hash>",
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
  "execution_permission_count": 0
}
```

The public read model returns only:

```json
{
  "status": "available",
  "reason": "execution_capsule_export_read_model_available",
  "latest_execution_capsule_export_hash": "<hash>",
  "counts": {
    "execution_capsule_export_count": 1,
    "component_count": 8,
    "execution_permission_count": 0
  }
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| execution capsule | hash is present and execution remains closed |
| expected execution capsule hash | equals computed execution capsule hash |
| execution capsule export payload | present |
| export execution capsule hash | equals computed execution capsule hash |
| export metadata | represented as a local hash only |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Execution capsule hash is missing or mismatched.
- Expected execution capsule hash is missing.
- Execution capsule export payload is missing.
- Export execution capsule hash does not match the computed capsule hash.
- Export metadata hash is missing.
- Export request flag is missing.
- Claim-boundary checks are not closed.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, nonce, or raw operator identity appears in
  public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The execution capsule export/read-model is not provider-result evidence. It is
only local no-call evidence that a future execution capsule export can be
represented without exposing raw operator data or opening a first-call
invocation.

## Rollback

Remove the execution capsule export/read-model projection, API/demo fields,
related tests/docs, and return to the AW-LIVE-32 execution authorization
capsule boundary.

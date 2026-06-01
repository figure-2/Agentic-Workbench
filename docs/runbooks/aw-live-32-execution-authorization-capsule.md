# AW-LIVE-32 Runbook: Execution Authorization Capsule Boundary

## Conclusion

The execution authorization capsule is a blocked no-call record after the
release authorization seal. It proves that a future first-call execution
capsule step can be represented as hashes and counts without opening the
provider path.

## Execution Capsule Projection

The public execution capsule returns only:

```json
{
  "status": "blocked",
  "reason": "execution_authorization_capsule_execution_closed",
  "execution_capsule_hash": "<hash>",
  "release_seal_hash": "<hash>",
  "final_authz_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "component_count": 8,
  "passed_component_count": 8,
  "mismatch_count": 0,
  "component_hash_count": 4,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "final_authz_count": 1,
  "capsule_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| release seal | hash is present and execution remains closed |
| expected release seal hash | equals computed release seal hash |
| execution authorization capsule payload | present |
| capsule release seal hash | equals computed release seal hash |
| final authorization | represented as a local hash only |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Release seal hash is missing or mismatched.
- Expected release seal hash is missing.
- Execution authorization capsule payload is missing.
- Capsule release seal hash does not match the computed release seal hash.
- Final authorization hash is missing.
- Capsule request flag is missing.
- Claim-boundary checks are not closed.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, nonce, or raw operator identity appears in
  public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The execution authorization capsule is not provider-result evidence. It is
only local no-call evidence that a future execution capsule can be represented
without exposing raw operator data or opening a first-call invocation.

## Rollback

Remove the execution capsule projection, API/demo fields, related tests/docs,
and return to the AW-LIVE-31 release authorization seal boundary.

# AW-LIVE-39 Runbook: Execution Capsule Final Authorization Boundary

## Conclusion

The execution capsule final authorization is a blocked no-call record after the
execution capsule release seal. It proves that a future first-call execution
capsule release seal can be followed by final authorization as hashes and
counts without opening the provider path.

## Execution Capsule Final Authorization Projection

The public execution capsule final authorization returns only:

```json
{
  "status": "blocked",
  "reason": "execution_capsule_final_authz_execution_closed",
  "execution_capsule_final_authz_hash": "<hash>",
  "execution_capsule_release_seal_hash": "<hash>",
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
  "authz_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| execution capsule release seal | hash is present and execution remains closed |
| expected execution capsule release seal hash | equals computed release seal hash |
| execution capsule final authorization payload | present |
| final authorization release seal hash | equals computed release seal hash |
| final authorization material | represented as a local hash only |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Execution capsule release seal hash is missing or mismatched.
- Expected execution capsule release seal hash is missing.
- Execution capsule final authorization payload is missing.
- Final authorization release seal hash does not match the computed seal hash.
- Final authorization material hash is missing.
- Authorization request flag is missing.
- Claim-boundary checks are not closed.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, nonce, or raw operator identity appears in
  public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The execution capsule final authorization is not provider-result evidence. It
is only local no-call evidence that a future final authorization can be
represented without exposing raw operator data or opening a first-call
invocation.

## Rollback

Remove the execution capsule final authorization projection, API/demo fields,
related tests/docs, and return to the AW-LIVE-38 execution capsule release seal
boundary.

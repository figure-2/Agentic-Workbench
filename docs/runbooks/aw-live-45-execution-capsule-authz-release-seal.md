# AW-LIVE-45 Runbook: Execution Capsule Authz Release Seal Boundary

## Conclusion

The execution capsule authz release seal is a blocked no-call record after the
execution capsule authz release attestation. It proves that a future
first-call authorization attestation can be sealed as hashes and counts without
opening the provider path.

## Execution Capsule Authz Release Seal Projection

The public execution capsule authz release seal returns only:

```json
{
  "status": "blocked",
  "reason": "execution_capsule_authz_release_seal_execution_closed",
  "execution_capsule_authz_release_seal_hash": "<hash>",
  "execution_capsule_authz_release_attestation_hash": "<hash>",
  "seal_material_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "component_count": 8,
  "passed_component_count": 8,
  "mismatch_count": 0,
  "component_hash_count": 4,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "seal_material_count": 1,
  "seal_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| execution capsule authz release attestation | hash is present and execution remains closed |
| expected execution capsule authz release attestation hash | equals computed authz release attestation hash |
| execution capsule authz release seal payload | present |
| seal attestation hash | equals computed authz release attestation hash |
| seal material | represented as a local hash only |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Execution capsule authz release attestation hash is missing or mismatched.
- Expected execution capsule authz release attestation hash is missing.
- Execution capsule authz release seal payload is missing.
- Seal attestation hash does not match the computed authz release attestation hash.
- Seal material hash is missing.
- Seal request flag is missing.
- Claim-boundary checks are not closed.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, nonce, or raw operator identity appears in
  public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The execution capsule authz release seal is not provider-result evidence. It
is only local no-call evidence that a future authorization attestation can be
sealed without exposing raw operator data or opening a first-call invocation.

## Rollback

Remove the execution capsule authz release seal projection, API/demo fields,
related tests/docs, and return to the AW-LIVE-44 execution capsule authz release
attestation boundary.

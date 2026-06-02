# AW-LIVE-51 Runbook: Execution Capsule Authz Final Authz Release Attestation Boundary

## Conclusion

The execution capsule authz final-authorization release attestation is a
blocked no-call record after the execution capsule authz final-authorization
operator decision. It shows that a future first-call authorization capsule can
represent a release attestation over operator-decision evidence without opening
the provider path.

## Execution Capsule Authz Final Authz Release Attestation Projection

The public execution capsule authz final-authorization release attestation
returns only:

```json
{
  "status": "blocked",
  "reason": "execution_capsule_authz_final_authz_release_attestation_execution_closed",
  "execution_capsule_authz_final_authz_release_attestation_hash": "<hash>",
  "execution_capsule_authz_final_authz_operator_decision_hash": "<hash>",
  "release_attestation_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "component_count": 8,
  "passed_component_count": 8,
  "mismatch_count": 0,
  "component_hash_count": 4,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "release_attestation_count": 1,
  "attestation_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| execution capsule authz final authorization operator decision | hash is present and execution remains closed |
| expected execution capsule authz final authorization operator decision hash | equals computed operator-decision hash |
| execution capsule authz final authorization release attestation payload | present |
| supplied attestation upstream hash | equals computed operator-decision hash |
| release attestation | represented as a local hash only |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Execution capsule authz final authorization operator decision hash is missing
  or mismatched.
- Expected execution capsule authz final authorization operator decision hash is
  missing.
- Release attestation payload is missing.
- Supplied attestation upstream hash does not match the computed
  operator-decision hash.
- Release attestation details are missing.
- Attestation request flag is missing.
- Claim-boundary checks are not closed.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, nonce, or raw operator identity appears in
  public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The execution capsule authz final-authorization release attestation is not
provider-result evidence. It is only local no-call evidence that a future
authorization capsule can represent release attestation over operator-decision
evidence without exposing raw operator data or opening a first-call invocation.

## Rollback

Remove the execution capsule authz final-authorization release attestation
projection, API/demo fields, related tests/docs, and return to the AW-LIVE-50
execution capsule authz final-authorization operator decision boundary.

# AW-LIVE-43 Runbook: Execution Capsule Authz Operator Decision Boundary

## Conclusion

The execution capsule authz operator decision is a blocked no-call record after
the execution capsule authz operator review. It proves that a future
first-call authorization review can be decided as hashes and counts without
opening the provider path.

## Execution Capsule Authz Operator Decision Projection

The public execution capsule authz operator decision returns only:

```json
{
  "status": "blocked",
  "reason": "execution_capsule_authz_operator_decision_execution_closed",
  "execution_capsule_authz_operator_decision_hash": "<hash>",
  "execution_capsule_authz_operator_review_hash": "<hash>",
  "operator_decision_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "component_count": 8,
  "passed_component_count": 8,
  "mismatch_count": 0,
  "component_hash_count": 4,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "operator_decision_count": 1,
  "decision_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| execution capsule authz operator review | hash is present and execution remains closed |
| expected execution capsule authz operator review hash | equals computed authz operator review hash |
| execution capsule authz operator decision payload | present |
| decision review hash | equals computed authz operator review hash |
| operator decision | represented as a local hash only |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Execution capsule authz operator review hash is missing or mismatched.
- Expected execution capsule authz operator review hash is missing.
- Execution capsule authz operator decision payload is missing.
- Decision review hash does not match the computed authz operator review hash.
- Operator decision hash is missing.
- Decision request flag is missing.
- Claim-boundary checks are not closed.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, nonce, or raw operator identity appears in
  public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The execution capsule authz operator decision is not provider-result evidence.
It is only local no-call evidence that a future authorization review can be
decided without exposing raw operator data or opening a first-call invocation.

## Rollback

Remove the execution capsule authz operator decision projection, API/demo
fields, related tests/docs, and return to the AW-LIVE-42 execution capsule
authz operator review boundary.

# AW-LIVE-30 Runbook: Operator Release Attestation Boundary

## Conclusion

The operator release attestation is a blocked no-call record after the operator
decision packet. It proves that a future first-call release attestation step can
be represented as hashes and counts without opening the provider path.

## Operator Release Attestation Projection

The public operator release attestation returns only:

```json
{
  "status": "blocked",
  "reason": "operator_release_attestation_execution_closed",
  "operator_release_attestation_hash": "<hash>",
  "operator_decision_packet_hash": "<hash>",
  "operator_attestation_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "component_count": 8,
  "passed_component_count": 8,
  "mismatch_count": 0,
  "component_hash_count": 4,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "operator_attestation_count": 1,
  "attestation_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| operator decision packet | hash is present and execution remains closed |
| expected operator decision packet hash | equals computed decision packet hash |
| operator release attestation payload | present |
| attestation decision packet hash | equals computed decision packet hash |
| operator attestation | represented as a local hash only |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Operator decision packet hash is missing or mismatched.
- Expected operator decision packet hash is missing.
- Operator release attestation payload is missing.
- Attestation decision packet hash does not match the computed decision packet
  hash.
- Operator attestation hash is missing.
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

The operator release attestation is not provider-result evidence. It is only
local no-call evidence that a future release attestation can be represented
without exposing raw operator data or opening a first-call invocation.

## Rollback

Remove the operator release attestation projection, API/demo fields, related
tests/docs, and return to the AW-LIVE-29 operator decision packet boundary.

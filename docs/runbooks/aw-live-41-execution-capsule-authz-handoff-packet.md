# AW-LIVE-41 Runbook: Execution Capsule Authz Handoff Packet Boundary

## Conclusion

The execution capsule authz handoff packet is a blocked no-call record after
the execution capsule authz export/read-model. It proves that a future
first-call execution authorization export can be handed off as hashes and
counts without opening the provider path.

## Execution Capsule Authz Handoff Projection

The public execution capsule authz handoff packet returns only:

```json
{
  "status": "blocked",
  "reason": "execution_capsule_authz_handoff_packet_execution_closed",
  "execution_capsule_authz_handoff_packet_hash": "<hash>",
  "execution_capsule_authz_export_hash": "<hash>",
  "execution_capsule_authz_export_read_model_hash": "<hash>",
  "claim_boundary_hash": "<hash>",
  "no_call_counters_hash": "<hash>",
  "packet_count": 1,
  "component_count": 8,
  "passed_component_count": 8,
  "mismatch_count": 0,
  "component_hash_count": 4,
  "no_call_counter_count": 13,
  "claim_boundary_check_count": 3,
  "export_read_model_count": 1,
  "handoff_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| execution capsule authz export | hash is present and execution remains closed |
| expected execution capsule authz export hash | equals computed authz export hash |
| execution capsule authz handoff payload | present |
| handoff export hash | equals computed authz export hash |
| authz export read-model | available and latest hash equals export hash |
| claim boundary | represented as a local hash only |
| no-call counters | all tracked call/import/env-read counters are `0` |

## Stop Conditions

- Execution capsule authz export hash is missing or mismatched.
- Expected execution capsule authz export hash is missing.
- Execution capsule authz handoff payload is missing.
- Handoff export hash does not match the computed authz export hash.
- Authz export read-model is missing or mismatched.
- Handoff request flag is missing.
- Claim-boundary checks are not closed.
- Any no-call counter is non-zero.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, nonce, or raw operator identity appears in
  public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The execution capsule authz handoff packet is not provider-result evidence. It
is only local no-call evidence that a future authorization export can be handed
off without exposing raw operator data or opening a first-call invocation.

## Rollback

Remove the execution capsule authz handoff packet projection, API/demo fields,
related tests/docs, and return to the AW-LIVE-40 execution capsule authz
export/read-model boundary.

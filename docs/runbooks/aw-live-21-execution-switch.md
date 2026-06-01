# AW-LIVE-21 Runbook: Disabled Execution Switch Boundary

## Conclusion

The execution switch is a blocked no-call record after the final release
packet. It proves that a future operator-facing switch can be represented as
hashes and counts without opening the provider path.

## Execution Switch Projection

The public switch summary returns only:

```json
{
  "status": "blocked",
  "reason": "execution_switch_disabled_by_default",
  "execution_switch_hash": "<hash>",
  "final_release_packet_hash": "<hash>",
  "switch_enable_hash": "<hash>",
  "component_count": 5,
  "passed_component_count": 5,
  "mismatch_count": 0,
  "component_hash_count": 2,
  "enable_request_count": 1,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| final release packet | hash is present and execution remains closed |
| expected final release packet hash | equals computed final release packet hash |
| switch payload | present |
| switch final packet hash | equals computed final release packet hash |
| switch enable flag | present as a separate local flag |

## Stop Conditions

- Final release packet hash is missing or mismatched.
- Expected final release packet hash is missing.
- Switch payload is missing.
- Switch final packet hash does not match the computed final release packet hash.
- Switch enable flag is missing.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The execution switch is not an execution token. It is only a local no-call
record for a later provider test candidate.

## Rollback

Remove the execution switch projection, API/demo fields, related tests/docs,
and return to the AW-LIVE-20 final release packet boundary.

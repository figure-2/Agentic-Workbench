# AW-LIVE-20 Runbook: Final Release Packet Boundary

## Conclusion

The final release packet is a blocked no-call record after the release
proposal. It proves that release proposal, arming, operator, release window,
and rollback evidence can be summarized as hashes and counts without opening
the provider path.

## Final Release Packet Projection

The public final packet summary returns only:

```json
{
  "status": "blocked",
  "reason": "final_release_packet_execution_closed",
  "final_release_packet_hash": "<hash>",
  "release_proposal_hash": "<hash>",
  "arming_record_hash": "<hash>",
  "operator_hash": "<hash>",
  "release_window_hash": "<hash>",
  "rollback_abort_hash": "<hash>",
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
| release proposal | hash is present and execution remains closed |
| expected release proposal hash | equals computed release proposal hash |
| final packet payload | present |
| final packet release hash | equals computed release proposal hash |
| arming record | represented as a hash |
| operator | represented as a hash |
| release window | represented as a hash |
| rollback/abort | represented as a hash |

## Stop Conditions

- Release proposal hash is missing or mismatched.
- Expected release proposal hash is missing.
- Final release packet payload is missing.
- Final packet release proposal hash does not match the computed proposal hash.
- Arming record, operator, release window, or rollback hash evidence is missing.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The final release packet is not an execution token. It is only a local no-call
record for a later provider test candidate.

## Rollback

Remove the final release packet projection, API/demo fields, related
tests/docs, and return to the AW-LIVE-19 release proposal boundary.

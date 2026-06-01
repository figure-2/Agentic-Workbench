# AW-LIVE-19 Runbook: Execution Authorization Release Proposal Boundary

## Conclusion

The release proposal is a blocked no-call record after the arming record. It
proves that operator intent, release window, and rollback evidence can be
summarized as hashes and counts without opening the provider path.

## Release Proposal Projection

The public release proposal summary returns only:

```json
{
  "status": "blocked",
  "reason": "release_proposal_execution_closed",
  "release_proposal_hash": "<hash>",
  "arming_record_hash": "<hash>",
  "operator_hash": "<hash>",
  "release_window_hash": "<hash>",
  "rollback_abort_hash": "<hash>",
  "component_count": 7,
  "passed_component_count": 7,
  "mismatch_count": 0,
  "component_hash_count": 4,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| arming record | hash is present and execution remains closed |
| expected arming hash | equals computed arming record hash |
| release proposal payload | present |
| release proposal arming hash | equals computed arming record hash |
| operator | represented as a hash |
| release window | represented as a hash |
| rollback/abort | hash matches arming record rollback/abort hash |

## Stop Conditions

- Arming record hash is missing or mismatched.
- Expected arming record hash is missing.
- Release proposal is missing.
- Release proposal arming hash does not match the computed arming hash.
- Operator, release window, or rollback evidence is missing.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The release proposal is not an execution token. It is only a local no-call
record for a later provider test candidate.

## Rollback

Remove the release proposal projection, API/demo fields, related tests/docs,
and return to the AW-LIVE-18 arming record boundary.

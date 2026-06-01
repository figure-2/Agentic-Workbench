# AW-LIVE-16 Runbook: Operator Opt-In Checklist Boundary

## Conclusion

The operator opt-in checklist is a blocked no-call gate after the handoff
packet. It lets an operator state intent against a specific handoff packet hash
without granting execution permission.

## Operator Opt-In Projection

The public opt-in summary returns only:

```json
{
  "status": "blocked",
  "reason": "operator_opt_in_execution_closed",
  "operator_opt_in_hash": "<hash>",
  "handoff_packet_hash": "<hash>",
  "checklist_item_count": 5,
  "passed_check_count": 5,
  "mismatch_count": 0,
  "execution_permission_count": 0
}
```

## Required Conditions

| Condition | Requirement |
|---|---|
| handoff packet | hash is present |
| opt-in payload | present |
| handoff binding | opt-in handoff hash equals computed handoff hash |
| decision | `opt_in` |
| operator fields | operator reference and opt-in time are present |

## Stop Conditions

- Handoff packet hash is missing.
- Operator opt-in payload is missing.
- Operator opt-in handoff hash does not match the computed handoff hash.
- Operator decision is not `opt_in`.
- Operator reference or opt-in time is missing.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The opt-in checklist is not an execution token. It is only a local no-call
statement that the handoff packet was reviewed for a later manual provider
test candidate.

## Rollback

Remove the operator opt-in projection, API/demo fields, related tests/docs, and
return to the AW-LIVE-15 handoff packet boundary.

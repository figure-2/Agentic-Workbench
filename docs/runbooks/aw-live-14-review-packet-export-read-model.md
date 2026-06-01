# AW-LIVE-14 Runbook: Review Packet Export Read Model

## Conclusion

The review packet export/read-model is a blocked no-call evidence surface. It
lets an operator retrieve the stored review packet hash and counts without
seeing raw prompt, provider body, provider payload, or authorization material.

## Export Projection

The public export summary returns only:

```json
{
  "status": "blocked",
  "reason": "review_packet_execution_closed",
  "review_packet_hash": "<hash>",
  "review_packet_export_hash": "<hash>",
  "export_count": 1,
  "component_count": 3,
  "passed_component_count": 3,
  "mismatch_count": 0,
  "component_hash_count": 3,
  "execution_permission_count": 0
}
```

The read model returns the same hash/status/reason/count fields for stored
exports.

## Required Conditions

| Condition | Requirement |
|---|---|
| review packet hash | present and matches optional expected hash |
| export store | available before read-model projection |
| execution permission | count remains `0` |
| raw material | never stored or returned |

## Stop Conditions

- Expected review packet hash does not match the computed packet hash.
- Review packet hash is missing.
- Export store is corrupted or unavailable.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The export is not an execution token. It is only a local read-model for the
manual provider test review packet.

## Rollback

Remove the review packet export row/read-model and keep the AW-LIVE-13 review
packet projection as the highest live-track boundary.

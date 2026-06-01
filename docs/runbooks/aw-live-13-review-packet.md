# AW-LIVE-13 Runbook: Review Packet

## Conclusion

The review packet is a blocked public projection. It packages the policy
summary, preflight audit, and readiness decision for operator review, but it
does not grant execution permission.

## Packet Projection

The public projection returns only:

```json
{
  "status": "blocked",
  "reason": "review_packet_execution_closed",
  "review_packet_hash": "<hash>",
  "component_count": 3,
  "passed_component_count": 3,
  "mismatch_count": 0,
  "component_hash_count": 3,
  "execution_permission_count": 0
}
```

When any component is missing or mismatched, the projection remains blocked and
returns an empty packet hash.

## Required Components

| Component | Requirement |
|---|---|
| policy summary | public policy summary hash exists |
| preflight audit | blocked preflight bundle with hash exists |
| readiness decision | blocked decision record with hash exists |

## Current Execution Boundary

- SDK imports: `0`
- Env value reads: `0`
- API calls: `0`
- Network calls: `0`
- Solar provider calls: `0`
- DAACS target runtime calls: `0`

## Stop Conditions

- Policy summary hash is missing.
- Preflight audit hash is missing or mismatched.
- Readiness decision hash is missing or mismatched.
- Execution permission count is not `0`.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The review packet is not an execution token. It is only a local evidence packet
for deciding whether a later manual test proposal should be considered.

## Rollback

Remove the review packet projection and keep the AW-LIVE-12 readiness decision
record as the highest live-track boundary.

# AW-LIVE-12 Runbook: Readiness Decision Record

## Conclusion

The readiness decision record is a blocked public projection. It records a
human decision against a preflight audit hash, but it does not grant execution
permission.

## Decision Projection

The public projection returns only:

```json
{
  "status": "blocked",
  "reason": "readiness_execution_closed",
  "readiness_decision_hash": "<hash>",
  "decision_count": 1,
  "approve_decision_count": 1,
  "reject_decision_count": 0,
  "defer_decision_count": 0,
  "mismatch_count": 0,
  "execution_permission_count": 0
}
```

Reject and defer decisions are represented by count fields:

```text
readiness_rejected
readiness_deferred
```

When the preflight hash is missing or mismatched, the projection remains
blocked and returns an empty decision hash.

## Required Inputs

| Input | Requirement |
|---|---|
| preflight audit hash | matches the current preflight bundle |
| decision | `approve`, `reject`, or `defer` |
| operator reference | present in the private input, never exposed |
| decided timestamp | present in the private input, never exposed |
| reason code | optional hash input, never exposed |

## Current Execution Boundary

- SDK imports: `0`
- Env value reads: `0`
- API calls: `0`
- Network calls: `0`
- Solar provider calls: `0`
- DAACS target runtime calls: `0`

## Stop Conditions

- Preflight audit hash is missing.
- Supplied preflight hash does not match the current bundle.
- Decision is not one of approve/reject/defer.
- Operator reference or decided timestamp is missing.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

An approve decision only means the local no-call candidate was reviewed. It is
not an execution token.

## Rollback

Remove the readiness decision projection and keep the AW-LIVE-11 preflight
audit bundle as the highest live-track boundary.

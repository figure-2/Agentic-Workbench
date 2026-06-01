# AW-LIVE-10 Runbook: One-Shot Live Permission Contract

## Conclusion

The one-shot permission contract is a blocked public projection. It fingerprints
the exact one-shot test candidate but does not grant execution.

## Permission Projection

The public projection returns only:

```json
{
  "status": "blocked",
  "reason": "executor_blocked",
  "permission_contract_hash": "<hash>",
  "expires_at": "<timestamp>",
  "permission_field_count": 11
}
```

When no permission candidate is supplied, the projection returns:

```json
{
  "status": "blocked",
  "reason": "one_shot_permission_required",
  "permission_contract_hash": "",
  "expires_at": "",
  "permission_field_count": 0
}
```

## Required Contract Fields

| Field | Requirement |
|---|---|
| run id | matches the provider envelope precheck run |
| proposal hash | matches the accepted manual test proposal |
| planned call hash | matches the disabled executor projection |
| timeout | matches the policy timeout |
| cost | matches the policy cost limit |
| API quota | matches the policy API call limit |
| output quota | matches the output unit budget |
| rollback | references a rollback plan id |
| abort criteria | references abort criteria hash and count |
| expiry | present as a timestamp string |

## Current Execution Boundary

- SDK imports: `0`
- Env value reads: `0`
- API calls: `0`
- Network calls: `0`
- Solar provider calls: `0`
- DAACS target runtime calls: `0`

## Stop Conditions

- Manual provider test proposal is missing or blocked.
- Disabled executor projection is missing.
- Permission candidate is missing or does not match proposal/executor/policy.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The one-shot permission hash is not an execution token. It is only a public-safe
fingerprint for a candidate request that remains blocked by default.

## Rollback

Remove the one-shot permission projection and keep the AW-LIVE-09 disabled
manual provider test executor boundary as the highest live-track boundary.

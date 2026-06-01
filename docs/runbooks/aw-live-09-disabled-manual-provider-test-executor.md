# AW-LIVE-09 Runbook: Disabled Manual Provider Test Executor

## Conclusion

The disabled executor boundary proves that an accepted manual provider test
proposal does not create execution permission. Current state remains blocked.

## Executor Projection

The executor public projection returns only:

```json
{
  "status": "blocked",
  "reason": "executor_enable_required",
  "planned_call_hash": "<hash>"
}
```

If `manual_test_executor_enable=true` is present, the projection still returns:

```json
{
  "status": "blocked",
  "reason": "executor_disabled_by_default",
  "planned_call_hash": "<hash>"
}
```

## Required Inputs

| Input | Requirement |
|---|---|
| accepted proposal gate | `manual_provider_test_proposal.status=approved_disabled` |
| executor flag | optional marker only; does not grant execution |
| proposal hash | used for `planned_call_hash` |
| prompt contract hash | used for `planned_call_hash` |
| run id | used for `planned_call_hash` |

## Current Execution Boundary

- SDK imports: `0`
- Env value reads: `0`
- API calls: `0`
- Network calls: `0`
- Solar provider calls: `0`
- DAACS target runtime calls: `0`

## Stop Conditions

- Proposal gate is missing or blocked.
- Executor flag is missing.
- Executor flag is present but boundary is still disabled.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce appears in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call occurs during this boundary.

## Operator Note

The executor flag is not a live permission. It only proves the system can
represent an attempted next step and still fail closed.

## Rollback

Remove the executor projection and keep the AW-LIVE-08 manual provider test
proposal gate as the highest live-track boundary.

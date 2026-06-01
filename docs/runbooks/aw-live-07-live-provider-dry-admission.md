# AW-LIVE-07 Runbook: Live Provider Dry-Admission

## Conclusion

This runbook defines the manual checklist for deciding whether a future narrow
provider test can be proposed. Current status remains `dry_admission_only`.
Execution permission remains closed.

## Current Boundary

- Provider path: no-call local precheck only.
- Operator approval: local envelope bound to sanitized policy summary hash.
- Provider envelope evidence: request/response contract hashes, counts, and
  status only.
- External calls: `0`.
- Provider SDK imports: `0`.
- Env value reads: `0`.
- Network calls: `0`.
- DAACS target runtime calls: `0`.

## Manual Checklist

| Check | Required Evidence | Current AW-LIVE-07 State |
|---|---|---|
| Operator approval envelope | operator status and policy summary hash match | projected |
| Cost limit | max cost units shown in public policy summary | projected |
| Timeout limit | request timeout seconds shown in public policy summary | projected |
| API quota | max API call count shown in public policy summary | projected |
| Output budget | max output unit budget shown in public policy summary | projected |
| Rollback plan | named rollback action for failed first test | manual required |
| Final operator review | human confirms one narrow test proposal | manual required |
| Execution permission | explicit closed state before later task | closed |

## Required Conditions Before a Later Manual Test Proposal

1. A single run id and prompt contract hash are selected.
2. The operator approval envelope is present and hash-bound.
3. Cost, timeout, API quota, and output budget are visible in the public policy
   summary.
4. The rollback action is documented.
5. The operator separately approves moving from dry-admission to a later manual
   test task.
6. The later task defines exactly what value can be read, what endpoint can be
   called, and what network path is allowed.
7. The later task defines abort criteria and expected public projection.

## Stop Conditions

- Missing or mismatched operator approval.
- Missing cost, timeout, API quota, or output budget.
- Missing rollback plan.
- Corrupted or unavailable provider envelope store.
- Any raw prompt, provider body, auth material, env value, local path, or
  provider payload in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call during dry-admission.

## API / Demo Projection Requirement

The public projection must include:

```json
{
  "status": "dry_admission_only",
  "live_ready": false,
  "allowed_to_execute": false
}
```

The projection may expose checklist ids, counts, hashes, booleans, and zero-call
counters. It must not expose raw request or response bodies.

## Rollback

Remove the dry-admission checklist projection and this runbook, then keep the
AW-LIVE-06 operator approval envelope boundary.

# AW-LIVE-08 Runbook: Manual Provider Test Proposal Gate

## Conclusion

The manual provider test proposal gate defines what must be approved before a
future task can consider a first narrow provider test. Current state remains
disabled by default.

## Required Proposal Fields

| Field | Requirement | Public Projection |
|---|---|---|
| `run_id` | must match the precheck request | match boolean |
| `prompt_contract_hash` | must match the precheck request | hash value |
| cost limit | must match policy summary | numeric limit |
| timeout limit | must match policy summary | numeric limit |
| API quota | must match policy summary | numeric limit |
| output budget | must match policy summary | numeric limit |
| rollback id | must be present | id and boolean |
| abort criteria | must be present | count and hash |

## Required Approval

The operator must approve the exact `proposal_hash`.

Required approval fields:

- operator reference
- approval timestamp
- decision of `approved`
- approved proposal hash

The public projection may return the approval status, hash match boolean, and
envelope hash. It must not return raw authorization material.

## Current Execution Boundary

Even when the proposal gate is accepted:

```json
{
  "status": "approved_disabled",
  "live_ready": false,
  "allowed_to_execute": false,
  "disabled_by_default": true
}
```

The projection is evidence for review only. It is not permission to call an
external provider.

## Stop Conditions

- Missing proposal.
- Proposal run id mismatch.
- Proposal prompt contract hash mismatch.
- Cost, timeout, API quota, or output budget mismatch.
- Missing rollback id.
- Missing abort criteria.
- Missing proposal approval.
- Proposal approval hash mismatch.
- Any raw prompt, provider body, provider payload, authorization material, env
  value, local path, signature, or nonce in public output.
- Any SDK import, env value read, API call, network call, or target runtime
  call during this gate.

## Operator Checklist

1. Confirm the selected run id.
2. Confirm the prompt contract hash.
3. Confirm cost, timeout, API quota, and output budget.
4. Confirm rollback id.
5. Confirm abort criteria count/hash.
6. Approve the exact proposal hash.
7. Confirm execution remains disabled by default.

## Rollback

Remove the proposal gate projection and keep the AW-LIVE-07 dry-admission
checklist as the highest live-track boundary.

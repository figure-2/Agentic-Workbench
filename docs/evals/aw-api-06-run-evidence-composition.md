# AW-API-06 Run / Evidence Composition

## Scope

Add a composed public read model for `GET /api/v1/runs/{run_id}`.

The endpoint now treats canonical run-session state as the primary run status
source and attaches runner/report/audit plus optional approval/replay evidence
as a separate sanitized summary. It does not expose raw repository rows, raw
prompts, raw artifact bodies, raw logs, provider payloads, runtime payloads, or
approval authorization material.

## Current Implementation

- `read_composed_canonical_run`
- `canonical-run-composed-read-model-public-v1`
- canonical run/artifact state as primary run state
- optional evidence summary with counts, checks, linkage status, and blocked
  markers
- missing evidence store reported as `unconfigured`
- corrupted evidence store reported as evidence summary `blocked`
- corrupted canonical store still blocks canonical run lookup

## Acceptance Results

| Gate | Result |
|---|---|
| canonical run state plus evidence summary returned by `GET /api/v1/runs/{run_id}` | covered |
| missing evidence repository keeps canonical run lookup available | covered |
| corrupted evidence repository blocks only evidence summary section | covered |
| corrupted canonical run store blocks canonical lookup | covered |
| cross-run evidence leakage | 0 |
| artifact payload body leakage | 0 |
| raw prompt/log/file/provider/runtime body leakage | 0 |
| raw approval authorization material leakage | 0 |
| repository boundary says which stores were queried | covered |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

## Test Commands

```powershell
python -m pytest tests/integration/test_api_public_projection.py -q
python -m pytest tests -q
```

## Claim Boundary

This is local read-model composition for sanitized repository projections. It
is not live observability, production monitoring, external provider outcome,
target runtime outcome, generated app delivery, hosted persistence, or
repository trust certification.

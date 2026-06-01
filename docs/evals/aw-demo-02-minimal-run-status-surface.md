# AW-DEMO-02 Minimal Run Status Surface

## Scope

Add a human-readable Markdown/CLI status surface over the `AW-DEMO-01` local
service-shaped demo summary.

The surface consumes the existing public projection path:

```text
run_local_demo.py
-> sanitized summary
-> render_status_surface(summary)
-> Markdown report to stdout
```

It does not read SQLite tables directly and does not create a separate source
of truth.

## Current Implementation

- `examples/demo-service-flow/render_status_surface.py`
- `tests/smoke/test_run_status_surface.py`
- demo README updated with the reviewer-facing command

The report includes:

- run status and projection version
- artifact chain
- DIV identity signals
- DAACS identity signals
- evidence summary counts
- repository boundary
- execution boundary
- claim boundary
- failed checks and next action

## Acceptance Results

| Gate | Result |
|---|---|
| Markdown/text report returned by `render_status_surface` | covered |
| report contains run id and artifact count | covered |
| report contains DIV identity section | covered |
| report contains DAACS identity section | covered |
| report contains evidence summary section | covered |
| report contains execution boundary section | covered |
| report contains claim boundary section | covered |
| Solar Pro 3 calls shown as 0 | covered |
| DAACS target runtime calls shown as 0 | covered |
| raw prompt leakage | 0 |
| raw artifact body leakage | 0 |
| raw provider/runtime payload leakage | 0 |
| raw approval signature/nonce value leakage | 0 |
| local store path leakage | 0 |

## Test Commands

```powershell
python -m pytest tests/smoke/test_run_status_surface.py -q
python examples/demo-service-flow/render_status_surface.py --store-root <temp-local-store>
python -m pytest tests -q
```

## Claim Boundary

This is a local reviewer-facing status surface over fixture/dry-run public
projections. It is not a web dashboard, hosted service, live provider
integration, DAACS target runtime execution, generated app delivery, production
monitoring, or security certification.

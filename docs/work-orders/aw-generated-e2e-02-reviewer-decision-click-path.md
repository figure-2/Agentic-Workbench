# AW-GENERATED-E2E-02 Reviewer Decision Click-Path

## Summary

```text
id: AW-GENERATED-E2E-02
depends_on:
  - AW-GENERATED-E2E-01
  - AW-GENERATED-QUALITY-02
scope:
  Add a second browser click-path verification for the generated fixture app's
  reviewer decision flow and record public-safe hash/count/status evidence.
risk_level: medium
rollback_plan:
  Remove reviewer decision click-path verification hook/docs and keep
  AW-GENERATED-E2E-01 as the latest generated app interaction baseline.
```

## Goal

Prove the generated app has more than one meaningful interaction. After the
owner filter path, the next candidate is a reviewer decision action that changes
a visible decision state or selected action count.

## Acceptance Tests

- Explicit opt-in is required before starting the local preview server.
- Browser verification clicks one reviewer decision/action control.
- Public evidence records click target label hash, before/after decision state
  hash or count, screenshot hash count, and status only.
- Screenshot path, page text, command output, local root path, provider payload,
  and credential exposure findings remain `0`.
- Provider/Solar additional calls remain `0`.
- DAACS uncontrolled target runtime calls remain `0`.
- Preview server cleanup remains `100%`.

## Out Of Scope

- Hosted deployment
- New Solar live call
- Raw screenshot or DOM text export
- Unrestricted DAACS runtime execution

## Completion Evidence

Measured command:

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --store-root .local\aw-generated-e2e-02-store --output-dir .local\aw-generated-e2e-02 --screenshot-backed
```

Measured result:

- Owner filter click attempts/passes: `1/1`
- Reviewer decision click attempts/passes: `1/1`
- Reviewer decision target label hash count: `1`
- Reviewer decision state hash count: `2`
- Reviewer decision state changed count: `1`
- Screenshot evidence/hash count: `1/1`
- Screenshot byte count: `146487`
- Preview server starts/stops: `1/1`
- Preview server cleanup percent: `100.0`
- Browser setup command attempts: `0`
- Provider calls: `0`
- DAACS target runtime calls: `0`
- Raw/path/page-text exposure findings: `0`

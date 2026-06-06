# AW-GENERATED-E2E-01 Owner Filter Click-Path Verification

## Summary

```text
id: AW-GENERATED-E2E-01
depends_on:
  - AW-GENERATED-QUALITY-02
  - AW-DEMO-FINAL-03
scope:
  Verify the generated fixture app's owner filter interaction in a browser and
  record public-safe click-path evidence.
risk_level: medium
rollback_plan:
  Remove click-path verification hook/docs and keep AW-GENERATED-QUALITY-02 as
  the latest generated app quality baseline.
```

## Goal

Prove the generated app is not only visually deeper but has at least one
working interaction. The first candidate is the owner filter in the generated
task board.

## Acceptance Tests

- Explicit opt-in is required before starting the local preview server.
- Browser verification clicks one owner filter button.
- Public evidence records click target label hash, before/after visible task
  count, screenshot hash count, and status only.
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

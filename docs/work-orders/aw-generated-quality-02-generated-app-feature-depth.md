# AW-GENERATED-QUALITY-02 Generated App Feature Depth

## Summary

```text
id: AW-GENERATED-QUALITY-02
depends_on:
  - AW-DEMO-FINAL-03
  - AW-GENERATED-QUALITY-01
scope:
  Improve the generated fixture app from a good portfolio screen into a more
  convincing app-shaped experience with deeper UI sections, document-linked
  task state, and verification-aware interaction markers.
risk_level: medium
rollback_plan:
  Revert generated app template/content additions and keep
  AW-DEMO-FINAL-03 screenshot-backed package as the latest portfolio package.
```

## Goal

Raise portfolio value by making the generated app look and behave more like an
actual workbench result, while keeping provider calls and uncontrolled target
runtime execution closed.

## Acceptance Tests

- Generated app still includes at least 9 sanitized fixture files.
- App surface includes workflow stages, artifact cards, runner plan,
  verification summary, task board, and at least one interaction-ready section.
- Static validation records increased feature marker count.
- Local build attempt still passes under explicit opt-in.
- Screenshot-backed portfolio package still records screenshot evidence count
  `1` when browser runtime is available.
- Raw prompt, provider body, file body, local root path, screenshot path, page
  text, and credential exposure findings remain `0`.
- Provider/Solar additional calls remain `0`.
- DAACS uncontrolled target runtime calls remain `0`.

## Out Of Scope

- Hosted deployment
- New Solar live call
- Running an unrestricted DAACS target runtime
- Public raw generated file body viewer

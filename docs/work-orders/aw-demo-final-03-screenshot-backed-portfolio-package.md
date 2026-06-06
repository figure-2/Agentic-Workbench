# AW-DEMO-FINAL-03 Screenshot-Backed Portfolio Package

## Summary

```text
id: AW-DEMO-FINAL-03
depends_on:
  - AW-PREVIEW-04
  - AW-DEMO-FINAL-02
scope:
  Package the portfolio demo so a reviewer can run one command and inspect the
  service-shaped workflow summary, static preview, generated app build evidence,
  and screenshot evidence status together.
risk_level: medium
rollback_plan:
  Remove the packaging/readme/docs additions and keep AW-PREVIEW-04 screenshot
  evidence as the latest measured browser verification layer.
```

## Goal

Make the portfolio review flow simpler. A first-time reviewer should understand
the chain:

```text
Idea -> SoT/PRD/ImplementationBrief -> RunnerPlan -> VerificationReport
-> generated fixture app -> local build -> browser screenshot evidence
```

## Acceptance Tests

- One documented command produces sanitized JSON and static HTML output.
- The portfolio report includes screenshot status/hash count/byte count only.
- The report includes build status and generated app file count.
- The report includes provider/Solar/DAACS runtime call counters.
- Screenshot path, page text, raw command output, local root path, provider
  payload, and credential exposure counts remain `0`.
- If browser runtime is unavailable, the report states
  `environment_blocked` instead of claiming screenshot success.
- Metrics record stage coverage, generated app file count, screenshot evidence
  count, server cleanup percent, and zero exposure findings.

## Out Of Scope

- Hosted deployment
- New Solar provider call
- Uncontrolled DAACS target runtime execution
- Raw screenshot path or page text export
- Large SPA rewrite

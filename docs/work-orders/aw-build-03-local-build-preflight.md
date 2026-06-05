# AW-BUILD-03 Local Build Preflight

## Summary

```text
id: AW-BUILD-03
depends_on:
  - AW-BUILD-02
scope:
  Add an explicit local build preflight over the buildable fixture app manifest.
  The preflight should decide whether a later local-only package install/build
  attempt is eligible, but it must not run install, build, server start,
  provider call, network call, or DAACS target runtime execution by default.
risk_level: medium
rollback_plan:
  Remove local build preflight service/API/demo/preview/tests/docs and return
  to AW-BUILD-02 buildable fixture app manifest.
```

## Goal

Move faster toward a portfolio-visible generated app result while preserving a
clear boundary between "build-ready candidate" and "build actually executed".

AW-BUILD-03 should make the next local build attempt reviewable by showing:

- run id and buildable manifest hash
- package manager command labels
- required file coverage
- opt-in requirement
- expected local-only execution scope
- zero default execution counters

## Team Decision

| Lens | Decision |
|---|---|
| Product | The next useful milestone is local build readiness, not another disabled provider chain. |
| Architecture | Keep build preflight separate from actual execution so later build attempts can be enabled explicitly. |
| Security | Do not read secret values or return local root paths. Do not run package manager commands in this step. |
| Frontend | Preview should show "build preflight eligible" separately from "build passed". |
| Test | Targeted tests should verify hash matching, command label projection, opt-in requirement, and zero default side effects. |

## Scope

### A. Build Preflight Contract

Acceptance tests:

- `buildable_fixture_manifest_hash` must exist and match expected hash.
- public projection returns command labels only, such as `npm install` and
  `npm run build`.
- public projection returns `local_build_opt_in_required=true`.
- public projection returns `build_executed=false`.
- public projection returns `package_install_executed=false`.
- public projection returns `server_started=false`.
- public projection returns no dependency values, file bodies, local root
  paths, env values, provider payloads, or raw logs.

### B. API/Demo/Preview Wiring

Acceptance tests:

- API/demo can include build preflight after AW-BUILD-02.
- preview shows build preflight status, reason, command label count, and opt-in
  requirement.
- default demo path still completes without package install, build, server
  start, provider call, network call, subprocess call, or DAACS target runtime
  call.

### C. Quantitative Documentation

Acceptance tests:

- `docs/evals/aw-build-03-local-build-preflight.md` records measured counts.
- `docs/metrics.md` records command label count, opt-in flag, and zero default
  execution counters.
- public wording does not claim build success or hosted success.

## Out Of Scope

- Running `npm install`
- Running `npm run build`
- Starting a dev server
- Opening a browser against the generated app
- Calling Solar Pro 3 or any provider
- Running DAACS target runtime
- Hosting or deployment

## Quantitative Targets

| Metric | Target |
|---|---:|
| Build preflight scenario count | 1 |
| Required manifest hash match | 1/1 |
| Package manager command labels | >= 2 |
| Local build opt-in required | 1 |
| Default package installs | 0 |
| Default builds | 0 |
| Default server starts | 0 |
| Provider/network/subprocess/runtime calls | 0 |
| Public raw body/root path/env value returns | 0 |

## Done Criteria

- Build preflight projection exists and is linked to AW-BUILD-02 hash.
- Demo and preview show build preflight status without claiming build success.
- Targeted unit and smoke tests pass.
- Full regression test passes once.
- Metrics and eval docs record quantitative results.

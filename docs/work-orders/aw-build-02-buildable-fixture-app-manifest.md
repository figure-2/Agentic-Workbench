# AW-BUILD-02 Buildable Fixture App Manifest

## Summary

```text
id: AW-BUILD-02
depends_on:
  - AW-BUILD-01
scope:
  Convert the generated fixture app skeleton from "static shape only" toward a
  buildable local app candidate by hardening package metadata, dependency
  labels, and build-readiness projection. Do not run package install, build,
  server start, provider call, or DAACS target runtime execution in this step.
risk_level: medium
rollback_plan:
  Remove buildable manifest hardening, build-readiness projection, tests, and
  docs. Return to AW-BUILD-01 static validation.
```

## Goal

Increase portfolio-facing completeness quickly by making the generated fixture
workspace look like a realistic local React/Vite app candidate while still
keeping execution closed by default.

This is the bridge before an explicit opt-in local build attempt.

## Team Decision

| Lens | Decision |
|---|---|
| Product | The next visible milestone should be "this generated workspace is build-ready by contract," not another no-call gate. |
| Architecture | Keep generation template-backed, but make the package manifest and readiness projection explicit. |
| Security | Do not run install/build/server in this step. Record `build_executed=false` and all execution counters as `0`. |
| Frontend | Align the fixture app structure with a conventional React/Vite app shape so reviewers understand the output folder. |
| Test | Add targeted tests for manifest values, readiness counts, and public projection safety. |

## Scope

### A. Manifest Hardening

Acceptance tests:

- `package.json` keeps required scripts: `dev`, `build`, `preview`, `verify`.
- dependency values are no longer placeholder text in the build-ready manifest
  path.
- package metadata exposes only safe labels and hashes.
- no secret, env value, raw prompt, local root path, or file body appears in
  public projection.

### B. Build-Readiness Projection

Acceptance tests:

- read-model returns `build_ready_candidate=true`.
- read-model returns package script count and dependency label count.
- read-model returns `package_install_executed=false`.
- read-model returns `build_executed=false`.
- read-model returns `server_started=false`.
- provider/network/subprocess/runtime counters remain `0`.

### C. Demo and Preview Integration

Acceptance tests:

- `run_local_demo.py` can include build-readiness projection after static
  validation.
- preview shows build-ready candidate status and counts.
- public wording does not claim install/build/hosted success.

## Out Of Scope

- Running `npm install`
- Running `npm run build`
- Starting Vite dev server
- Executing DAACS target runtime
- Calling Solar Pro 3 or other providers
- Hosting or deployment

## Quantitative Targets

| Metric | Target |
|---|---:|
| Build-readiness scenario count | 1 |
| Required script labels | 4/4 |
| Dependency label count | >= 4 |
| Placeholder dependency values in build-ready manifest | 0 |
| Package installs | 0 |
| Builds | 0 |
| Server starts | 0 |
| Provider/network/subprocess/runtime calls | 0 |
| Raw file body returns | 0 |
| Local root path returns | 0 |
| Public claim drift findings | 0 |

## Done Criteria

- Generated workspace has a build-readiness projection.
- Demo and preview show build-readiness status/counts.
- Targeted unit and smoke tests pass.
- Full regression test passes once.
- Metrics and eval docs record quantitative results.

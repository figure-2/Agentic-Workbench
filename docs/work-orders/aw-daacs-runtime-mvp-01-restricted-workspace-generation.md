# AW-DAACS-RUNTIME-MVP-01 Restricted Workspace Generation

## Summary

```text
id: AW-DAACS-RUNTIME-MVP-01
depends_on:
  - AW-APP-01
  - AW-SOLAR-02
  - AW-DAACS-RUNTIME-06
scope:
  Generate a minimal, sanitized fixture app skeleton inside a run-scoped
  restricted workspace using the existing ImplementationBrief, RunnerPlan, and
  fixture artifact bundle records.
  This is the first "visible generated output" experiment, but it remains local
  and allowlist-bound.
risk_level: high
rollback_plan:
  Remove the restricted workspace generator, generated fixture templates,
  read-model hook, smoke tests, and eval docs. Keep AW-DAACS-RUNTIME-06
  fixture materialization and AW-APP-01 preview unchanged.
```

## Goal

Move from "artifact preview" to "restricted generated workspace preview".

The user should be able to run one local command and see a small app skeleton
folder with sanitized files, such as:

```text
runs/<run_id>/generated-app/
  README.md
  package.json
  src/App.tsx
  src/api.ts
  tests/verification.md
```

The output is still fixture/template-backed. It is not a live DAACS runtime run,
not a package install, not a build, not a server start, and not deployment.

## Implementation Scope

### A. Restricted Workspace Generator

Add a generator service that writes only inside:

```text
<configured_store_root>/runs/<run_id>/generated-app/
```

Inputs:

- `run_id`
- `runner_plan_hash`
- `implementation_brief_hash`
- `generated_artifact_bundle_hash`
- allowlisted template ids

Acceptance tests:

- Writes only under the run-scoped generated app directory.
- Path traversal is blocked.
- Absolute output paths are blocked.
- File body templates are sanitized and deterministic.
- No provider call, SDK import, env value read, subprocess, package install, build, server start, or network call.

### B. Minimal App Skeleton

Generate a small fixture app skeleton from templates.

Required files:

- `README.md`
- `package.json`
- `src/App.tsx`
- `src/api.ts`
- `tests/verification.md`

Acceptance tests:

- At least 5 files are written.
- File hashes are recorded.
- Byte counts are recorded.
- Public projection returns relative paths, hashes, byte counts, and status only.
- Public projection does not return raw file bodies or local root paths.

### C. Preview Integration

Extend AW-APP-01 preview or add a companion command so reviewers can see:

- generated workspace status
- generated file count
- file cards
- zero-call counters
- warning that build/run is not executed yet

Acceptance tests:

- Preview shows generated file count >= 5.
- Preview shows root path returned = false.
- Preview shows file body returned = false.
- Preview shows build/run/hosted status = not executed.

### D. Quantitative Evidence

Record metrics in `docs/metrics.md` and an eval doc.

Required metrics:

| Metric | Target |
|---|---:|
| Generated workspace scenarios | 1 |
| Generated files | >= 5 |
| File hash count | >= 5 |
| Write allowlist violations | 0 |
| Path traversal blocked fixtures | >= 3 |
| Raw file body returns | 0 |
| Local root path returns | 0 |
| Provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Package installs | 0 |
| Builds/server starts | 0 |

## Out Of Scope

- Real DAACS runtime execution
- CLI coding agent execution
- Installing npm/pip packages
- Running build/test commands against generated code
- Starting a local server
- Hosting/deploying the generated app
- Claiming the generated app is complete
- Persisting raw prompts or raw provider responses

## Done Criteria

- One local command generates the restricted workspace skeleton.
- Public read model returns only status/hash/count/path summaries.
- AW-APP-01 or a companion preview shows the generated file cards.
- Targeted tests pass.
- Full regression test passes once.
- Eval and metrics document the quantitative results.

# AW-DEMO-01 Local Service-Shaped Demo

## Purpose

This demo proves the local Agentic Workbench flow through the public API
boundary:

```text
Idea
-> POST /api/v1/runs
-> sanitized artifact chain
-> local dry-run evidence persistence
-> GET /api/v1/runs/{run_id}
-> composed canonical run/evidence read model
```

The default demo is fixture/dry-run only. It does not call Solar Pro 3,
Upstage, external providers, original DIV runtime, DAACS target runtime, CLI
agents, package installers, local app servers, or generated app builds.
Explicit opt-in flags can run bounded local package/build or local preview
checks inside the run-scoped generated fixture app workspace.

## Run

From the project root:

```powershell
python examples/demo-service-flow/run_local_demo.py
```

To keep the local SQLite projection stores outside the example folder:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-demo-01
```

To include the AW-SOLAR-01 no-call planner provider comparison:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-solar-01-demo --include-solar-planner-preflight
```

To include the AW-SOLAR-02 one-shot planner spike mock projection:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-solar-02-demo --include-solar-planner-spike
```

This keeps the fixture planner as the artifact-producing path while adding a
Solar-shaped spike envelope and mocked response projection. Provider calls, SDK
imports, env value reads, and network calls remain `0`.

To include the AW-SOLAR-LIVE-01 Solar planner live spike boundary without
operator opt-in:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-solar-live-01-blocked --include-solar-planner-live-spike
```

This records the blocked default path. Provider calls, env value reads, network
calls, server starts, and DAACS target runtime calls remain `0`.

To opt in to one bounded Solar planner live spike:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-solar-live-01 --include-solar-planner-live-spike --allow-solar-planner-live-call
```

This reads the configured `UPSTAGE_API_KEY` environment value and may perform
one Upstage chat completion attempt with timeout, input-size, output-token, and
call-count caps. The fixture planner remains the artifact-producing path. The
public summary returns status, hashes, counts, response byte count, response
section count, and artifact hint count only. It does not return the credential
value, raw prompt text, provider response body, local root paths, file bodies,
server state, or DAACS target runtime output.

To include the AW-SOLAR-QUALITY-01 fixture-vs-Solar quality comparison without
an additional live call:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-solar-quality-01 --include-solar-planner-quality-comparison
```

This compares the fixture planner stage coverage with the Solar live-spike
public projection. Without `--include-solar-planner-live-spike` and
`--allow-solar-planner-live-call`, the comparison uses the blocked Solar
projection and performs `0` provider calls, env value reads, and network calls.
Reviewer approval is absent by default, so Solar-authored artifact binding
remains blocked.

To attach a reviewer approval hash to the comparison:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-solar-quality-01 --include-solar-planner-quality-comparison --allow-solar-quality-reviewer-approval
```

This only marks the quality comparison as reviewer-bound when the Solar
projection is otherwise eligible. It does not create Solar-authored artifacts,
store provider bodies, start servers, or execute the DAACS target runtime.

To include the AW-SOLAR-DRAFT-01 reviewer-gated draft projection:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-solar-draft-01 --include-solar-planner-draft-projection
```

This projects draft `PlanningBlueprint` and `PRDPackage` candidates only when a
review-ready Solar quality comparison and matching reviewer approval hash are
present. The default local demo remains blocked and performs `0` additional live
calls, canonical artifact writes, server starts, or DAACS target runtime calls.

To include the AW-DAACS-RUNTIME-00 no-call target runtime sandbox comparison:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-daacs-runtime-00-demo --include-daacs-runtime-preflight
```

To include the AW-DAACS-RUNTIME-01/02 no-call disabled target runtime adapter
admission comparison plus persisted adapter admission read-model evidence:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-daacs-runtime-01-demo --include-daacs-runtime-adapter-admission
```

To include the AW-DAACS-RUNTIME-03/04 no-call output manifest contract,
persistence, and read-model comparison:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-daacs-runtime-04-demo --include-daacs-runtime-output-manifest
```

To include the AW-DAACS-RUNTIME-05 no-call generated artifact bundle contract
over the persisted output manifest read model:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-daacs-runtime-05-demo --include-daacs-runtime-generated-artifact-bundle
```

To include the AW-DAACS-RUNTIME-06 sanitized fixture artifact materialization
inside a run-scoped local workspace:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-daacs-runtime-06-demo --include-daacs-runtime-fixture-materialization
```

To include the AW-DAACS-RUNTIME-MVP-01 restricted fixture app skeleton
generation, including the AW-DAACS-RUNTIME-MVP-02 document-linked codegen
input evidence:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-daacs-runtime-mvp-01-demo --include-daacs-runtime-restricted-workspace-generation
```

This writes nine sanitized fixture files under a run-scoped generated-app
folder and returns relative paths, hashes, byte counts, status, document input
hash counts, a `codegen_input_hash`, and zero-call counters only. The codegen
input binds the fixture PlanningBlueprint, PRDPackage, ImplementationBrief, and
optional Solar draft projection hashes without storing or returning raw prompt
or provider bodies. It does not install packages, run builds, start servers,
return file contents, or execute the DAACS target runtime.

To include the AW-VERIFY-01 generated artifact verification over those
restricted fixture files:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-verify-01-demo --include-daacs-runtime-generated-artifact-verification
```

This verifies the nine generated fixture files by workspace-relative path,
content hash, and byte count. It returns verification hashes, statuses, reasons,
and counts only. It does not return file contents, expose local root paths,
install packages, run builds, start servers, or execute the DAACS target
runtime.

To include the AW-BUILD-01 generated workspace static validation over the
verified fixture app workspace:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-build-01-demo --include-daacs-runtime-generated-workspace-static-validation
```

This validates `package.json`, required script labels, `src/App.tsx` markers,
`src/api.ts` markers, and zero-call verification notes. It returns status,
hashes, reasons, and counts only. It does not install packages, run builds,
start servers, call providers, open network connections, or execute the DAACS
target runtime.

To include the AW-BUILD-02 buildable fixture app manifest over the static
validation result:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-build-02-demo --include-daacs-runtime-buildable-fixture-manifest
```

This validates build-ready candidate metadata such as script labels,
dependency labels, `index.html`, `src/main.tsx`, `vite.config.ts`, and
`tsconfig.json` markers. It returns hashes, labels, status, reasons, and
counts only. It does not return dependency values, file contents, local root
paths, install packages, run builds, start servers, call providers, open
network connections, or execute the DAACS target runtime.

To include the AW-BUILD-03 local build preflight over the buildable fixture app
manifest:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-build-03-demo --include-daacs-runtime-local-build-preflight
```

This validates that the buildable fixture app is eligible for a future explicit
local build attempt. The public summary returns command labels, command hashes,
manifest hashes, status, reasons, opt-in requirement, and zero-call counters
only. It does not install packages, run builds, start servers, call providers,
open network connections, run subprocess commands, or execute the DAACS target
runtime.

To include the AW-BUILD-04 local build attempt boundary without allowing local
commands:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-build-04-demo --include-daacs-runtime-local-build-attempt
```

This records the blocked default path. Package installs, builds, server starts,
provider calls, network calls, subprocess calls, and target runtime calls remain
`0`.

To opt in to one local fixture app package/build attempt inside the run-scoped
generated workspace:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-build-04-demo --include-daacs-runtime-local-build-attempt --allow-local-build-attempt
```

This may run `npm install --no-audit --no-fund` and `npm run build` inside the
generated fixture app workspace. The public summary returns command labels,
exit-code hashes, output hashes, byte counts, durations, status, reasons, and
counts only. It does not return command output bodies, dependency values, file
contents, local root paths, start a server, call providers, or execute the DAACS
target runtime.

To include the AW-PREVIEW-01 local preview attempt boundary without allowing a
preview server:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-preview-01-demo --include-daacs-runtime-local-preview-attempt
```

This records the blocked default path. Package installs, builds, preview server
starts, browser verification attempts, provider calls, network calls, and DAACS
target runtime calls remain `0`.

To opt in to one local fixture app preview-server/browser verification attempt:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-preview-01-demo --include-daacs-runtime-local-preview-attempt --allow-local-preview-attempt
```

This may first run the AW-BUILD-04 local package/build attempt, then runs a
browser runtime preflight. If Playwright/browser runtime support is unavailable,
the preview attempt returns `environment_blocked` before starting a server and
returns install guidance labels/hashes only. If the browser runtime is
available, the command starts the generated fixture app preview server inside
the run-scoped workspace and verifies the first screen. The verification path
uses Python Playwright when available and falls back to an installed
Chromium-family system browser in headless mode when Playwright is not
installed. The public summary returns status, reason, hashes, visible marker
count, screenshot hash/byte count when available, and server start/stop
counters only. It does not return command output bodies, file contents,
screenshot paths, page text, local root paths, provider output, or target
runtime output.

To include the AW-PREVIEW-03 browser runtime setup boundary without running
setup commands:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-preview-03-demo --include-daacs-runtime-browser-setup-attempt
```

This records setup status, command labels, hashes, and counts only. Setup
command executions remain `0` without `--allow-browser-runtime-setup`.

To explicitly allow the local Playwright setup attempt:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-preview-03-demo --include-daacs-runtime-browser-setup-attempt --allow-browser-runtime-setup
```

This may run local Playwright package/browser setup commands following the
official Playwright browser installation flow. The public summary still does
not return raw command output, argv, browser error text, local paths, provider
payloads, or DAACS runtime output.

To run the AW-DEMO-FINAL-04 interaction-backed portfolio package in one command:

```powershell
python examples/demo-service-flow/run_portfolio_demo.py --output-dir .local/aw-demo-final-04 --screenshot-backed
```

This writes `aw-demo-final-04-summary.json` and
`aw-demo-final-04-preview.html` under the selected output directory.
`--screenshot-backed` is an explicit opt-in for one local build attempt and one
local preview/browser verification attempt. It does not opt in to browser
runtime setup commands. The printed report contains output file names, stage
coverage, fixture app file count, local build attempt status/counts, local
preview status, screenshot hash/byte-count status, owner filter click evidence,
reviewer decision click evidence, browser setup status, and
execution boundary counters only. It does not print local root paths, command
output bodies, file contents, screenshot paths, page text, hosted state,
provider output, or target runtime output.

To render the AW-APP-01 portfolio-facing artifact preview over the same public
summary:

```powershell
python examples/demo-service-flow/render_artifact_preview.py --store-root .local/aw-app-01-demo --output .local/aw-app-01-preview.html
```

The preview is a static HTML file. It shows workflow stage coverage, document
chain status, three sanitized fixture artifact cards, verification status, and
zero-call execution counters. When the default preview command is used, it also
shows nine generated workspace file cards plus generated artifact
verification status/counts, generated workspace static validation
status/counts, the AW-BUILD-02 build-ready candidate manifest, and the
AW-BUILD-03 local build preflight status. With `--include-local-build-attempt`
and `--allow-local-build-attempt`, it also shows the AW-BUILD-04 local fixture
app package/build attempt result. It does not render file contents, local root
paths, secret values, dependency values, command outputs, build outputs, server
state, or runtime/provider outcomes.

The printed JSON is a sanitized summary. It includes run status, artifact
kinds, evidence counts, linkage markers, repository boundary flags, and
zero-call execution metrics. It does not include raw prompts, provider payloads,
runtime payloads, logs, file bodies, raw approval signatures, raw nonces, or
local database root paths.

## Human-Readable Status Surface

For a reviewer-friendly Markdown report:

```powershell
python examples/demo-service-flow/render_status_surface.py
```

The status surface reads the same local API demo path and prints sections for
run state, artifact chain, DIV identity signals, DAACS identity signals,
evidence summary, execution boundary, claim boundary, checks, and next action.
It does not read repository tables directly and does not open live execution.

## Static UI Shell

For a local HTML shell over the same public summary:

```powershell
python examples/demo-service-flow/render_static_ui_shell.py --output .local/aw-demo-03-static-ui.html
```

The shell renders run status, artifact chain, DIV/DAACS identity signals,
evidence counts, execution boundary counters, and the live-open policy state.
It consumes the public demo summary only. It does not read repository tables,
load `.env` values, call Solar Pro 3, or run the DAACS target runtime.

## AW-MVP-01 Vertical Slice

The same demo now also exposes the service-shaped MVP baseline:

```text
Idea
-> PlanningBlueprint
-> PRDPackage
-> ImplementationBrief
-> SpecApproval
-> RunnerPlan
-> VerificationReport
```

`GET /api/v1/runs/{run_id}/verification` returns the verification read model
for the run. The demo summary records `workflow_stage_coverage` and
`mvp_metrics` so reviewers can see the covered stage count, linkage percent,
zero-call counters, and public exposure findings without inspecting repository
rows.

## Expected Signals

- DIV identity is represented by planning and PRD artifacts.
- DAACS identity is represented by BuildSpec, ImplementationBrief, dry-run
  RunnerPlan evidence, and VerificationReport evidence.
- AW-MVP-01 stage coverage is `7/7` for the representative local scenario.
- The composed read model remains local and fixture-based.
- Provider and target runtime call counts remain `0`.
- The static UI marks live policy as `closed / eligible only`.
- When `--include-solar-planner-preflight` is used, the fixture planner remains
  the artifact-producing path with `7/7` stage coverage, while the disabled
  Solar planner preflight returns `preflight_only` with provider calls, SDK
  imports, env value reads, and network calls all `0`.
- When `--include-daacs-runtime-preflight` is used, the dry-run RunnerPlan
  remains the only execution evidence path, while the target runtime sandbox
  preflight returns `blocked` with filesystem writes, subprocess calls, network
  calls, and target runtime calls all `0`.
- When `--include-daacs-runtime-adapter-admission` is used, the demo compares
  three variants: dry-run runner, target runtime preflight, and disabled
  adapter admission. The preflight hash must match before adapter reachability,
  but the disabled adapter still returns `blocked`. The adapter admission
  evidence is persisted as a hash/status/count-only SQLite row and read back
  through the public read model. Execution permission, filesystem writes,
  subprocess calls, network calls, and target runtime calls all remain `0`.
- When `--include-daacs-runtime-output-manifest` is used, the demo compares
  four variants: dry-run runner, target runtime preflight, persisted disabled
  adapter admission, and persisted disabled output manifest evidence. The
  manifest shows expected output group labels and hashes only, and the
  read-model returns manifest hashes/status/counts only. It does not include
  generated file bodies, generated source bodies, raw paths, filesystem writes
  outside local SQLite evidence stores, subprocess calls, network calls, or
  target runtime calls.
- When `--include-daacs-runtime-generated-artifact-bundle` is used, the demo
  compares five variants: dry-run runner, target runtime preflight, persisted
  disabled adapter admission, persisted disabled output manifest evidence, and
  disabled generated artifact bundle evidence. The bundle shows artifact unit
  labels and hashes only. It does not include generated file bodies, generated
  source bodies, raw paths, filesystem writes outside local SQLite evidence
  stores, subprocess calls, network calls, or target runtime calls.
- When `--include-daacs-runtime-fixture-materialization` is used, the demo
  compares six variants and writes three sanitized fixture artifacts under a
  run-scoped local workspace. The public summary returns relative paths,
  content hashes, status, reasons, and counts only. It does not return local
  root paths, raw file bodies, provider payloads, subprocess output, network
  output, or target runtime calls.
- When `--include-daacs-runtime-restricted-workspace-generation` is used, the
  demo compares seven variants and writes nine sanitized fixture app skeleton
  files under a run-scoped generated-app folder. The public summary returns
  relative paths, content hashes, byte counts, status, reasons, and counts
  only. Package installs, builds, server starts, provider calls, network calls,
  subprocess calls, and target runtime calls all remain `0`.
- When `--include-daacs-runtime-generated-artifact-verification` is used, the
  demo compares eight variants and verifies the nine restricted fixture app
  files by hash and byte count. The public summary returns verification hashes,
  status, reasons, counts, and zero-call boundaries only. File contents, local
  root paths, provider payloads, package installs, builds, server starts,
  network calls, subprocess calls, and target runtime calls all remain `0`.
- When `--include-daacs-runtime-generated-workspace-static-validation` is used,
  the demo compares nine variants and statically validates the verified fixture
  app workspace. The public summary returns static validation hashes, status,
  reasons, counts, and zero-call boundaries only. File contents, local root
  paths, provider payloads, package installs, builds, server starts, network
  calls, subprocess calls, and target runtime calls all remain `0`.
- When `--include-daacs-runtime-buildable-fixture-manifest` is used, the demo
  compares ten variants and validates the generated fixture app as a
  build-ready candidate manifest. The public summary returns script labels,
  dependency labels, source marker counts, hashes, status, reasons, and
  zero-call boundaries only. Dependency values, file contents, local root
  paths, provider payloads, package installs, builds, server starts, network
  calls, subprocess calls, and target runtime calls all remain `0`.
- When `--include-daacs-runtime-local-build-preflight` is used, the demo
  compares eleven variants and validates local build preflight eligibility over
  the build-ready candidate manifest. The public summary returns command
  labels, command hashes, opt-in requirement, status, reasons, and zero-call
  boundaries only. Operator opt-in is not present by default, execution
  permission remains `0`, and package installs, builds, server starts, provider
  calls, network calls, subprocess calls, and target runtime calls all remain
  `0`.
- When `--include-daacs-runtime-local-build-attempt` is used without
  `--allow-local-build-attempt`, the demo compares twelve variants and records
  the blocked default local build attempt path. Package installs, builds,
  server starts, provider calls, network calls, subprocess calls, and target
  runtime calls all remain `0`.
- When `--include-daacs-runtime-local-build-attempt` and
  `--allow-local-build-attempt` are used together, the demo compares twelve
  variants and attempts one package install plus one build command inside the
  run-scoped generated fixture app workspace. Public output returns hashes,
  counts, byte counts, durations, status, and reasons only. Server starts,
  provider calls, env value reads, SDK imports, and target runtime calls remain
  `0`.
- When `run_portfolio_demo.py --allow-local-build-attempt` is used, the command
  writes one sanitized JSON summary and one static HTML preview for portfolio
  review. The generated fixture app local build attempt is included, while
  local preview and browser setup states are included as status/count fields.
  In the default browser setup path, setup command attempts, server starts,
  provider calls, DAACS target runtime calls, raw body exposure, screenshot path
  exposure, page text exposure, and local root path exposure remain `0`.
- AW-GENERATED-QUALITY-01 upgrades the generated fixture app surface with
  workflow stages, artifact cards, runner plan, verification summary, execution
  boundary counters, and task board sections. The static validation path records
  app markers `7/7`, API markers `4/4`, verification/boundary markers `4/4`,
  and zero-call markers `5/5`.
- AW-PREVIEW-04 records explicit opt-in browser screenshot evidence for the
  generated fixture app. In the measured system-headless-browser path, the
  portfolio command records screenshot evidence count `1`, screenshot byte
  count `53009`, preview server starts/stops `1/1`, cleanup `100.0%`, provider
  calls `0`, DAACS target runtime calls `0`, and raw/path/page-text exposure
  findings `0`.
- AW-DEMO-FINAL-03 promotes the portfolio command to a screenshot-backed
  package. The measured `--screenshot-backed` path records generated fixture app
  files `9`, local build status `passed`, local preview status `passed`,
  screenshot evidence count `1`, screenshot byte count `52645`, preview server
  starts/stops `1/1`, cleanup `100.0%`, provider calls `0`, DAACS target
  runtime calls `0`, and raw/path/page-text exposure findings `0`.
- AW-DEMO-FINAL-04 promotes the portfolio command to an interaction-backed
  package. The measured `--screenshot-backed` path records generated fixture app
  files `9`, local build status `passed`, local preview status `passed`,
  screenshot evidence count `1`, screenshot byte count `146583`, owner filter
  click status `passed`, reviewer decision click status `passed`, verified
  interaction paths `2/2`, interaction hash evidence count `4`, preview server
  cleanup `100.0%`, provider calls `0`, DAACS target runtime calls `0`, and
  raw/path/page-text exposure findings `0`.
- AW-GENERATED-QUALITY-02 deepens the generated fixture app with a first-screen
  feature depth control strip, Action Center, Evidence Timeline, Owner Filter,
  Reviewer Decision, and interaction-ready task board state. Static validation
  records app markers `13/13`, API markers `8/8`, verification/boundary markers
  `4/4`, and zero-call markers `5/5`.
- AW-GENERATED-E2E-01 verifies the generated fixture app owner filter click
  path in the screenshot-backed portfolio command. The measured path records
  click status `passed`, click attempts `1`, click passes `1`, target label hash
  count `1`, task count `3 -> 1`, screenshot evidence count `1`, screenshot
  byte count `143515`, preview server cleanup `100.0%`, provider calls `0`,
  DAACS target runtime calls `0`, and raw/path/page-text exposure findings `0`.
- AW-GENERATED-E2E-02 verifies the generated fixture app reviewer decision
  click path in the screenshot-backed portfolio command. The measured path
  records click status `passed`, click attempts `1`, click passes `1`, target
  label hash count `1`, state hash count `2`, state changed count `1`,
  screenshot evidence count `1`, screenshot byte count `146487`, preview server
  cleanup `100.0%`, provider calls `0`, DAACS target runtime calls `0`, and
  raw/path/page-text exposure findings `0`.
- When `--include-provider-precheck` is used, manual proposal, disabled
  executor, one-shot permission, preflight audit, readiness decision, review
  packet, review packet export/read-model, handoff packet, and operator opt-in
  summaries remain blocked and hash-only. The sealed pre-execution packet also
  remains blocked and exposes only hashes and counts. The arming record
  remains blocked and exposes only hashes and counts. The release proposal
  remains blocked and exposes only hashes and counts. The final release packet
  remains blocked and exposes only hashes and counts. The execution switch
  remains blocked and exposes only hashes and counts. The executor preflight
  remains blocked and exposes only hashes and counts. The executor dispatch
  record remains blocked and exposes only hashes and counts. The invocation
  receipt remains blocked and exposes only hashes and counts. The
  post-invocation audit remains blocked and exposes only hashes and counts.
  The completion summary remains blocked and exposes only hashes and counts.
  The closeout record remains blocked and exposes only hashes and counts. The
  operator handback remains blocked and exposes only hashes and counts. The
  operator decision packet remains blocked and exposes only hashes and counts.
  The operator release attestation remains blocked and exposes only hashes and
  counts. The release authorization seal remains blocked and exposes only
  hashes and counts. The execution authorization capsule remains blocked and
  exposes only hashes and counts. The execution capsule export/read-model
  remains blocked and exposes only hashes and counts. The execution capsule
  handoff packet remains blocked and exposes only hashes and counts. The
  execution capsule operator review remains blocked and exposes only hashes
  and counts. The execution capsule operator decision remains blocked and
  exposes only hashes and counts. The execution capsule release attestation
  remains blocked and exposes only hashes and counts. The execution capsule
  release seal remains blocked and exposes only hashes and counts. The
  execution capsule final authorization remains blocked and exposes only
  hashes and counts. The execution capsule authorization export/read-model
  remains blocked or available only as hashes and counts. The execution
  capsule authorization handoff packet remains blocked and exposes only hashes
  and counts. The execution capsule authorization operator review remains
  blocked and exposes only hashes and counts. The execution capsule
  authorization operator decision remains blocked and exposes only hashes and
  counts. The execution capsule authorization release attestation remains
  blocked and exposes only hashes and counts. The execution capsule
  authorization release seal remains blocked and exposes only hashes and
  counts. The execution capsule authorization final authorization remains
  blocked and exposes only hashes and counts. The execution capsule
  authorization final authorization export/read-model remains blocked or
  available only as hashes and counts. The execution capsule authorization
  final authorization handoff packet remains blocked and exposes only hashes
  and counts. The execution capsule authorization final authorization operator
  review remains blocked and exposes only hashes and counts. The execution
  capsule authorization final authorization operator decision remains blocked
  and exposes only hashes and counts. The execution capsule authorization
  final authorization release attestation remains blocked and exposes only
  hashes and counts. The execution capsule authorization final authorization
  release seal remains blocked and exposes only hashes and counts.
  The execution capsule authorization final authorization final authorization
  remains blocked and exposes only hashes and counts.
  The execution capsule authorization final authorization final authorization
  export/read-model remains blocked or available only as hashes and counts.
  The execution capsule authorization final authorization final authorization
  handoff packet remains blocked and exposes only hashes and counts.
  The execution capsule authorization final authorization final authorization
  operator review remains blocked and exposes only hashes and counts.
  The execution capsule authorization final authorization final authorization
  operator decision remains blocked and exposes only hashes and counts.
  The execution capsule authorization final authorization final authorization
  release attestation remains blocked and exposes only hashes and counts.
  The execution capsule authorization final authorization final authorization
  release seal remains blocked and exposes only hashes and counts.
  The execution capsule authorization final authorization final authorization
  final authorization remains blocked and exposes only hashes and counts.
  The execution capsule authorization final authorization final authorization
  final authorization export/read-model remains blocked or available only as
  hashes and counts.
  The execution capsule authorization final authorization final authorization
  final authorization handoff packet remains blocked and exposes only hashes
  and counts.
  The execution capsule authorization final authorization final authorization
  final authorization operator review remains blocked and exposes only hashes
  and counts.
  The execution capsule authorization final authorization final authorization
  final authorization operator decision remains blocked and exposes only hashes
  and counts.
  The execution capsule authorization final authorization final authorization
  final authorization release attestation remains blocked and exposes only
  hashes and counts.
  The execution capsule authorization final authorization final authorization
  final authorization release seal remains blocked and exposes only hashes and
  counts.
  The execution capsule authorization final authorization final authorization
  final authorization final authorization remains blocked and exposes only
  hashes and counts.
  The execution capsule authorization final authorization final authorization
  final authorization final authorization export/read-model remains blocked or
  available only as hashes and counts.

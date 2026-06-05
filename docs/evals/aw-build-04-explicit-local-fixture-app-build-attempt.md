# AW-BUILD-04 Explicit Local Fixture App Build Attempt Eval

## Summary

AW-BUILD-04 moves the generated fixture app from local build preflight to one
explicit opt-in package install/build attempt inside the run-scoped generated
workspace. The default path remains blocked. The build-attempt path requires
both operator opt-in and local command execution allowance.

This eval supports only a local fixture app package/build attempt result. It
does not claim server start, hosted behavior, Solar Pro 3 output, external LLM
provider output, or DAACS target runtime execution.

## Team Review

| Lens | Finding |
|---|---|
| Product | This increases portfolio value because reviewers can see the generated fixture app reach a measured local build attempt instead of stopping at preflight. |
| Architecture | The executor is isolated behind the AW-BUILD-03 preflight hash, explicit opt-in, run-scoped workspace resolution, and sanitized result projection. |
| Security | Public output exposes command labels, exit-code hashes, output hashes, byte counts, durations, status, reason, and counters only. Command output bodies and local root paths are not returned. |
| Backend | API/demo wiring keeps fixture mode default and adds an optional local build attempt endpoint. |
| Frontend | The preview now distinguishes build preflight, build attempt, package install/build counts, and server-start count. |
| Test | Unit, API smoke, demo smoke, preview smoke, and one local opt-in demo cover blocked and attempted paths. |
| External audit | Official npm/Vite documentation supports the command family. The eval still avoids hosted, provider, runtime, and server-start claims. |

## Official References Checked

| Source | Use |
|---|---|
| [Vite build guide](https://vite.dev/guide/build.html) | Confirms the Vite build command family used by the fixture app build script. |
| [npm install docs](https://docs.npmjs.com/cli/v11/commands/npm-install/) | Confirms package installation behavior and audit/fund flags. |
| [npm run-script docs](https://docs.npmjs.com/cli/v7/commands/npm-run-script/) | Confirms script execution through npm run-script/npm run. |

Local npm registry checks also confirmed the fixture dependency versions used
by the generated app skeleton were resolvable at the time of measurement.

## Quantitative Result

| Metric | Result |
|---|---:|
| Local build attempt scenarios | 1 |
| Demo comparison variants | 12 |
| Stage coverage | 7/7 |
| Generated fixture app files | 9 |
| Required preflight hash match | 1/1 |
| Operator opt-in present | 1 |
| Local command execution allowed | 1 |
| Command result count | 2 |
| Command output hash count | 2 |
| Package install attempts | 1 |
| Package install calls | 1 |
| Build attempts | 1 |
| Build calls | 1 |
| Server start attempts | 0 |
| Server start calls | 0 |
| Subprocess calls | 2 |
| Package-manager network attempts | 1 |
| Provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| DAACS target runtime calls | 0 |
| Raw command output returns | 0 |
| Public file body returns | 0 |
| Public local root path returns | 0 |
| Failed checks | 0 |

## Local Environment Measurement

| Item | Result |
|---|---|
| Node.js | `v24.15.0` |
| npm | `11.12.1` |
| `npm install --no-audit --no-fund` | exit code `0` |
| `npm run build` | exit code `0` |
| Sanitized install output byte count | `25` |
| Sanitized build output byte count | `389` |

The package-manager network attempt count is `1` because dependency resolution
uses the npm registry. It is not a provider call, target runtime call, server
start, or hosted-app claim.

## Verification

| Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_local_build_attempt.py apps\api\agentic_workbench_api\services\target_runtime_local_build_attempt.py apps\api\agentic_workbench_api\main.py` | passed |
| `python -m pytest tests\unit\test_target_runtime_local_build_attempt.py -q --color=no` | 6 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py::test_daacs_runtime_local_build_attempt_api_requires_explicit_opt_in tests\smoke\test_daacs_runtime_preflight.py::test_local_service_demo_records_local_build_attempt_as_blocked_without_allow -q --color=no` | 2 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-build-04-demo --include-daacs-runtime-local-build-attempt --allow-local-build-attempt` | passed |
| `python -m pytest tests\smoke\test_artifact_preview_surface.py -q --color=no` | 3 passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no` | 3 passed |
| `python -m pytest tests -q --color=no` | 710 passed |
| `git diff --check` | passed |

Full regression and whitespace checks are recorded in `docs/metrics.md`.

## Claim Boundary

Allowed:

- Claiming one explicit local fixture app package/build attempt passed in the
  measured local environment.
- Claiming the public summary and preview expose only hashes, labels, counts,
  status, reason, durations, and byte counts for command outcomes.
- Claiming server starts, provider calls, env value reads, SDK imports, and
  DAACS target runtime calls stayed at `0`.

Not allowed:

- Claiming a server was started.
- Claiming hosted or deployed behavior.
- Claiming external provider planner output.
- Claiming DAACS target runtime execution.
- Claiming raw command output, file body, local root path, dependency value, or
  secret exposure.

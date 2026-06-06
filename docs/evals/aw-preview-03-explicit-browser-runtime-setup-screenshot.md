# AW-PREVIEW-03 Explicit Browser Runtime Setup Eval

AW-PREVIEW-03 adds an explicit browser runtime setup attempt boundary for local
preview screenshots. The default path remains no-install and no-server-start.
Setup commands are represented as labels and hashes in public projection, and
they run only when an operator passes the explicit setup opt-in.

This step follows official Playwright guidance that the Python package and
matching browser binaries must be installed before browser automation can run.

Official references:

- [Playwright Python browsers](https://playwright.dev/python/docs/browsers)
- [Playwright screenshots](https://playwright.dev/docs/screenshots)

## Team Review

| Lens | Finding |
|---|---|
| Product | The demo can now tell reviewers the next concrete step to obtain screenshot evidence without pretending screenshots passed. |
| Architecture | Browser setup is separated from preview verification and exposed through its own hash/count-only projection. |
| Backend | API, unit test, and CLI demo paths share the same setup attempt service. |
| Security | Default setup command execution is `0`; raw command output, argv, browser errors, local paths, provider payloads, and env values are not returned. |
| Test | Unit tests cover blocked, fake-success, and hash-mismatch states. Smoke test covers the API blocked path. |
| External audit | No hosted success, screenshot success, Solar call, or DAACS runtime execution claim is made. |

## Quantitative Evidence

| Metric | Value |
|---|---:|
| Browser setup attempt scenarios | 1 |
| Default setup command executions | 0 |
| Explicit setup opt-in count in current CLI run | 0 |
| Setup command attempts in current CLI run | 0 |
| Browser runtime available after setup in current CLI run | 0 |
| Unit fake-success setup command attempts | 2 |
| Unit fake-success browser runtime available after setup | 1 |
| Screenshot evidence count in current environment | 0 |
| Preview server starts in current setup CLI run | 0 |
| Provider calls | 0 |
| Solar additional live calls | 0 |
| DAACS target runtime calls | 0 |
| Raw command output exposure | 0 |
| Raw argv exposure | 0 |
| Browser error exposure | 0 |
| Public local path exposure | 0 |

## Verification Commands

| Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_browser_setup_attempt.py apps\api\agentic_workbench_api\services\target_runtime_browser_setup_attempt.py apps\api\agentic_workbench_api\main.py packages\daacs_builder\__init__.py examples\demo-service-flow\run_local_demo.py tests\unit\test_target_runtime_browser_setup_attempt.py tests\smoke\test_daacs_runtime_preflight.py -q` | passed |
| `python -m pytest tests\unit\test_target_runtime_browser_setup_attempt.py tests\smoke\test_daacs_runtime_preflight.py::test_daacs_runtime_browser_setup_attempt_api_requires_explicit_opt_in tests\unit\test_public_claim_projection_docs.py -q --color=no` | 7 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-preview-03-cli-blocked --include-daacs-runtime-browser-setup-attempt` | passed with setup status `blocked`, reason `browser_runtime_setup_opt_in_required`, setup command attempts `0` |
| `python -m pytest tests -q --color=no` | 740 passed in 243.14s |

## Claim Boundary

Allowed claim:

- "The project now has an explicit browser runtime setup boundary for local
  screenshot verification."

Blocked claims:

- "Browser screenshot verification passed in this environment."
- "Playwright or browser binaries were installed automatically."
- "The generated app is hosted or production-ready."
- "The original DAACS runtime executed the app."

## Next Work

The next implementation should move to `AW-DEMO-FINAL-01`: package the current
JSON summary, static preview, build evidence, browser setup status, and honest
environment-blocked screenshot state into one portfolio-facing demo command.

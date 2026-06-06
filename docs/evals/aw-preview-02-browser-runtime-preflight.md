# AW-PREVIEW-02 Browser Runtime Preflight Eval

AW-PREVIEW-02 adds a repeatable browser runtime preflight in front of the local
fixture app preview attempt. The goal is to avoid ambiguous
`environment_blocked` results by checking whether Python Playwright and its
Chromium runtime can launch before starting the preview server.

This step does not install packages or browsers automatically. It records
install guidance labels and hashes only, based on official Playwright
documentation. It does not return raw install commands through the public API,
does not return raw browser errors, and does not expose local paths.

## Team Review

| Lens | Finding |
|---|---|
| Product | The preview flow now tells reviewers why screenshot evidence is unavailable instead of appearing broken. |
| Architecture | Browser runtime readiness is separated from preview server startup, so missing browser support does not start unnecessary local servers. |
| Backend | The preflight is injectable for tests and public-safe by default. |
| Security | Install guidance is label/hash-only in projection; raw errors, env values, paths, provider payloads, and page text are not returned. |
| Test | Unit tests cover fake available and fake unavailable browser runtime states. Smoke tests keep default API/demo blocked. |
| External audit | No hosted app, browser screenshot success, or DAACS runtime execution claim is made when the browser runtime is unavailable. |

## Official References

- [Playwright Python browsers](https://playwright.dev/python/docs/browsers)
- [Playwright screenshots](https://playwright.dev/docs/screenshots)

The official Playwright browser documentation states that browser binaries must
be installed for the selected Playwright version. The screenshot documentation
supports the hash-only screenshot evidence path used when the runtime is
available.

## Quantitative Evidence

| Metric | Value |
|---|---:|
| Browser runtime preflight scenarios | 1 |
| Browser runtime preflight records | 1 |
| Browser runtime available count in current environment | 0 |
| Browser import check count | 1 |
| Browser launch check count | 0 |
| Install guidance label count | 2 |
| Install guidance hash count | 2 |
| Default preview server starts without opt-in | 0 |
| Opt-in preview server starts when browser runtime unavailable | 0 |
| Opt-in preview server stops when browser runtime unavailable | 0 |
| Screenshot evidence count in current environment | 0 |
| Unit fake-runner screenshot evidence count | 1 |
| Provider calls | 0 |
| Solar additional live calls | 0 |
| DAACS target runtime calls | 0 |
| Raw browser error exposure | 0 |
| Raw command output exposure | 0 |
| Public local path exposure | 0 |

## Verification Commands

| Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_local_preview_attempt.py apps\api\agentic_workbench_api\services\target_runtime_local_preview_attempt.py examples\demo-service-flow\run_local_demo.py packages\daacs_builder\__init__.py tests\unit\test_target_runtime_local_preview_attempt.py -q` | passed |
| `python -m pytest tests\unit\test_target_runtime_local_preview_attempt.py -q --color=no` | 5 passed |
| `python -m pytest tests\unit\test_target_runtime_local_preview_attempt.py tests\smoke\test_daacs_runtime_preflight.py::test_daacs_runtime_local_preview_attempt_api_requires_explicit_opt_in tests\smoke\test_daacs_runtime_preflight.py::test_local_service_demo_records_local_preview_attempt_as_blocked_without_allow tests\unit\test_public_claim_projection_docs.py -q --color=no` | 10 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-preview-02-cli-blocked --include-daacs-runtime-local-preview-attempt` | passed with preview status `blocked`, reason `local_preview_opt_in_required`, browser runtime preflight count `0`, preview server starts/stops `0/0` |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-preview-02-cli-optin --include-daacs-runtime-local-preview-attempt --allow-local-preview-attempt` | passed with preview status `environment_blocked`, reason `playwright_python_package_missing`, browser runtime preflight count `1`, availability count `0`, preview server starts/stops `0/0`, install guidance labels `2` |
| `python -m pytest tests -q --color=no` | 736 passed in 233.10s |

## Claim Boundary

Allowed claim:

- "The preview attempt now checks browser runtime availability before starting
  the local preview server."

Blocked claims:

- "Browser screenshot verification passed in this environment."
- "The app is hosted or production-ready."
- "The original DAACS runtime executed the generated app."
- "The system installed Playwright/browser binaries automatically."

## Next Work

The next implementation should choose one of two speed-focused paths:

1. Add an explicitly approved browser-runtime setup command that follows the
   official Playwright install flow.
2. Package a final portfolio demo that shows `environment_blocked` as an
   honest local-environment state while continuing to improve generated app
   quality.

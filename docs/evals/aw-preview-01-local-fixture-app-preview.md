# AW-PREVIEW-01 Local Fixture App Preview Eval

AW-PREVIEW-01 adds an explicit opt-in local preview-server/browser verification
boundary over the document-linked generated fixture app. It is intended to show
the portfolio flow from document artifacts to generated files to a locally
servable first screen.

This step does not call Solar Pro 3, does not execute the original DAACS target
runtime, does not run uncontrolled CLI agents, and does not expose raw command
output, page text, screenshot paths, file bodies, local root paths, provider
payloads, prompts, or credentials.

## Team Review

| Lens | Finding |
|---|---|
| Product | This is the first generated-app step that can start a local preview server, making the demo more reviewer-visible than file/hash evidence alone. |
| Architecture | The preview attempt depends on the AW-BUILD-04 build-attempt hash and remains a separate public projection. |
| Backend | The API endpoint returns hash/status/count-only evidence and blocks without explicit preview opt-in. |
| Frontend | The first-screen contract checks visible markers for workflow, task board, and verification summary. |
| Security | Default execution is blocked; opt-in output excludes raw command output, raw page body, local paths, and provider payloads. |
| Test | Unit tests use a fake preview runner for success and environment-blocked paths. Smoke tests cover API/demo blocked defaults. |
| External audit | Claims must distinguish local preview-server start from hosted app success or DAACS runtime execution. |

## Official References

- [Vite preview options](https://vite.dev/config/preview-options.html)
- [Playwright screenshots](https://playwright.dev/docs/screenshots)

These references support the selected local preview server and screenshot
verification shape. The implementation still treats missing browser runtime
support as `environment_blocked` rather than a product success.

## Quantitative Evidence

| Metric | Value |
|---|---:|
| Representative preview scenario count | 1 |
| Public projection count | 1 |
| Required visible marker count | 4 |
| Default path preview opt-in present | 0 |
| Default path preview server starts | 0 |
| Default path browser verification attempts | 0 |
| Opt-in path preview server starts | 1 |
| Opt-in path preview server stops | 1 |
| Opt-in path browser verification status | environment_blocked |
| Opt-in path screenshot evidence count in current environment | 0 |
| Unit fake-runner screenshot evidence count | 1 |
| Provider calls | 0 |
| Solar additional live calls | 0 |
| DAACS target runtime calls | 0 |
| Preview boundary external network calls | 0 |
| Raw output/body/path exposure findings | 0 |
| New unit tests | 5 |
| New smoke tests | 2 |

## Verification Commands

| Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_local_preview_attempt.py apps\api\agentic_workbench_api\services\target_runtime_local_preview_attempt.py apps\api\agentic_workbench_api\main.py examples\demo-service-flow\run_local_demo.py packages\daacs_builder\__init__.py tests\unit\test_target_runtime_local_preview_attempt.py tests\smoke\test_daacs_runtime_preflight.py -q` | passed |
| `python -m pytest tests\unit\test_target_runtime_local_preview_attempt.py -q --color=no` | 5 passed |
| `python -m pytest tests\smoke\test_daacs_runtime_preflight.py::test_daacs_runtime_local_preview_attempt_api_requires_explicit_opt_in tests\smoke\test_daacs_runtime_preflight.py::test_local_service_demo_records_local_preview_attempt_as_blocked_without_allow -q --color=no` | 2 passed |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-preview-01-cli-blocked --include-daacs-runtime-local-preview-attempt` | passed with preview status `blocked` and server starts `0` |
| `python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-preview-01-cli-optin --include-daacs-runtime-local-preview-attempt --allow-local-preview-attempt` | passed with preview status `environment_blocked` and server start/stop count `1/1` |
| `python -m pytest tests -q --color=no` | 736 passed |

## Claim Boundary

Allowed claim:

- "The generated fixture app can be started through an explicit local preview
  boundary, and the server cleanup evidence is recorded."

Blocked claims:

- "The app is hosted."
- "The DAACS runtime generated and executed the app."
- "Solar Pro 3 created the generated app."
- "Browser screenshot verification passed in every environment."
- "Raw generated file bodies or command outputs are available through the
  public API."

## Next Work

The next speed-focused step should either install/document a browser runtime for
repeatable screenshot verification or move directly to a portfolio final demo
that labels this preview step as `environment_blocked` when browser runtime
support is absent.

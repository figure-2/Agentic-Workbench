# AW-DAACS-RUNTIME-03 Work Order: Disabled Target Runtime Output Manifest Contract

## Summary

`AW-DAACS-RUNTIME-03` defines a disabled, no-call output manifest contract for
the future DAACS target runtime path. It must consume the persisted adapter
admission read model from `AW-DAACS-RUNTIME-02`, then produce a public-safe
manifest projection that describes expected output groups, counts, hashes, and
claim boundaries.

This work does not write generated application files, execute DAACS runtime
code, spawn subprocesses, start servers, install packages, call providers, or
open network connections.

## Why This Is Next

The project goal is to move from user idea to development-start documents and
then toward an implementation result. The current system already has:

- service-shaped MVP flow from Idea to VerificationReport
- Solar planner preflight boundary
- DAACS target runtime sandbox preflight
- disabled adapter admission
- persisted adapter admission evidence/read-model

The next missing contract is: "if the runtime were later allowed to produce
files, what output evidence shape would be accepted without exposing raw file
bodies?" `AW-DAACS-RUNTIME-03` answers that question before any runtime writes
are opened.

## Work Unit

```text
id: AW-DAACS-RUNTIME-03
depends_on:
  - AW-MVP-01
  - AW-DAACS-RUNTIME-02
scope:
  Add a disabled target runtime output manifest contract over the persisted
  adapter admission read model. The manifest must be public-safe and limited to
  hashes, status, reason, output group labels, counts, and no-call execution
  counters. It must not contain generated file bodies or raw paths.
risk_level: high
rollback_plan:
  Remove output manifest contract module, API/demo hook, tests, eval document,
  metrics updates, and this work order. Return to AW-DAACS-RUNTIME-02 persisted
  adapter admission evidence/read-model.
```

## 담당 관점

제품:
The manifest should make the demo easier to understand: users should see that
the system has reached "planned implementation outputs" without claiming the
outputs were generated.

아키텍처:
The manifest must sit after persisted adapter admission read-model evidence and
before any target runtime executor. It must not merge canonical run/artifact
repositories with runtime output evidence.

보안:
The manifest must not expose raw prompt, raw logs, raw file bodies, provider
payload, runtime payload, local absolute path, secret, environment value, or
generated application code.

백엔드:
Add the contract as a small service/module first. API/demo wiring is allowed
only after the contract is covered by unit tests.

테스트:
Cover positive no-call manifest creation, missing prerequisite read-model,
hash mismatch, raw body leakage, and zero side-effect counters.

문서/감사:
Record comparison experiment results and numeric metrics in eval/metrics docs.
Do not describe the manifest as runtime execution or generated app success.

## Proposed Implementation Units

### AW-DAACS-RUNTIME-03A: Contract Model

Scope:

Define a target runtime output manifest request/result pair.

Suggested files:

- `packages/daacs_builder/target_runtime_output_manifest.py`
- `tests/unit/test_target_runtime_output_manifest.py`

Required public fields:

- `projection_version`
- `run_id`
- `status`
- `reason`
- `runner_plan_hash`
- `adapter_admission_hash`
- `adapter_admission_read_model_hash`
- `output_manifest_hash`
- `output_groups`
- `counts`
- `execution_boundary`
- `claim_boundary`

Acceptance tests:

- valid persisted adapter admission read-model creates a blocked/no-call
  manifest projection
- missing read-model is blocked
- read-model status other than `available` is blocked
- adapter admission hash mismatch is blocked
- output manifest contains no raw file body or generated source code
- public projection is safe

Risk level: high

Rollback plan:

Remove contract model and unit tests.

### AW-DAACS-RUNTIME-03B: API/Demo Hook

Scope:

Expose the manifest contract through the local API/demo path only when
explicitly requested.

Suggested API:

- `POST /api/v1/daacs/runtime/output-manifest`

Suggested demo flag:

- `--include-daacs-runtime-output-manifest`

Acceptance tests:

- API requires `run_id`, `runner_plan_hash`, `adapter_admission_hash`, and
  adapter admission read-model projection
- demo comparison variant count becomes `4`
- output manifest status remains blocked/no-call
- DAACS target runtime calls remain `0`
- filesystem writes outside existing local SQLite evidence stores remain `0`
- subprocess and network calls remain `0`

Risk level: high

Rollback plan:

Remove API/demo hook and smoke test updates.

### AW-DAACS-RUNTIME-03C: Evaluation And Metrics

Scope:

Record comparison experiment and observed numeric results.

Suggested files:

- `docs/evals/aw-daacs-runtime-03-disabled-output-manifest-contract.md`
- `docs/metrics.md`
- `examples/demo-service-flow/README.md`

Acceptance tests:

- comparison variants recorded as `4`
- stage coverage remains `7/7`
- adapter admission read-model prerequisite coverage recorded as `100%`
- output manifest hash coverage recorded as `100%`
- generated artifact body writes recorded as `0`
- DAACS target runtime calls recorded as `0`
- raw exposure findings recorded as `0`
- public claim drift findings recorded as `0`

Risk level: medium

Rollback plan:

Remove eval/metrics/readme updates.

## Output Manifest Contract Rules

Allowed:

- output group labels such as `backend`, `frontend`, `verification_report`
- expected output counts
- output manifest hash
- source artifact hash references
- adapter admission hash references
- status, reason, and check counts
- zero-call execution counters

Forbidden:

- generated file body
- source code body
- raw prompt
- raw logs
- raw runtime payload
- raw provider payload
- local absolute path
- `.env` value
- API key, token, secret, account id
- claim that a runnable app was generated
- claim that DAACS runtime executed successfully

## Comparison Experiment

| Variant | Expected Status | Purpose |
|---|---|---|
| `dry_run_runner` | `passed` | Existing service-shaped fixture path remains the only artifact-producing path. |
| `target_runtime_preflight` | `blocked` | Sandbox/write/operation/rollback readiness is checked with no runtime call. |
| `persisted_disabled_adapter_admission` | `blocked` + read-model `available` | Disabled adapter admission evidence is durable and queryable. |
| `disabled_output_manifest_contract` | `blocked` or `prepared_no_call` | Expected output evidence shape is defined without generated file writes. |

## Target Metrics

| Metric | Target |
|---|---:|
| Comparison variants | 4 |
| Dry-run stage coverage | 7/7 |
| Adapter admission read-model prerequisite coverage | 100% |
| Output manifest hash coverage | 100% |
| Output group count | >= 3 |
| Generated artifact body writes | 0 |
| DAACS target runtime calls | 0 |
| Filesystem writes outside existing local SQLite evidence stores | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |

## Verification Plan

Run in this order:

```powershell
python -m pytest tests\unit\test_target_runtime_output_manifest.py -q --color=no
python -m pytest tests\unit\test_target_runtime_admission_store.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no
python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-03-demo --include-daacs-runtime-adapter-admission --include-daacs-runtime-output-manifest
python -m pytest tests\unit\test_public_claim_projection_docs.py tests\unit\test_target_runtime_output_manifest.py tests\smoke\test_daacs_runtime_preflight.py -q --color=no
python -m compileall apps examples packages tests
python -m pytest tests -q --color=no
git diff --check
```

## Completion Criteria

- Contract unit tests pass.
- API/demo smoke tests pass.
- Demo summary shows four comparison variants.
- Eval and metrics docs contain observed numeric results.
- Public output contains no raw body, raw path, provider payload, runtime
  payload, secret, or generated source body.
- Solar Pro 3 calls remain `0`.
- DAACS target runtime calls remain `0`.
- Worktree is clean after commit if a commit is requested.

## Non-Goals

- Do not execute DAACS runtime.
- Do not write generated app files.
- Do not start generated app servers.
- Do not install packages.
- Do not call Solar Pro 3 or any provider.
- Do not claim generated app success, runtime success, hosted success, or
  production readiness.

# AW-VERIFY-01 Generated Artifact Verification Eval

## Summary

AW-VERIFY-01 adds a local verification boundary over the restricted fixture app
skeleton generated in AW-DAACS-RUNTIME-MVP-01. It verifies that the nine
workspace-relative file records exist under the configured run-scoped workspace
and that each local file matches the public `content_hash` and `byte_count`
record.

This is not a package install, build, server start, DAACS target runtime
execution, Solar Pro 3 call, or hosted app verification.

## Official Reference Position

No new external API surface was added. This work verifies local fixture file
integrity over the already generated skeleton. The skeleton shape remains based
on the official references recorded in
`docs/evals/aw-daacs-runtime-mvp-01-restricted-workspace-generation.md`.

## Team Review

| Lens | Finding |
|---|---|
| Product | This moves the portfolio demo from "files were produced" to "files are present and hash-verified." |
| Architecture | Verification is a separate service/API boundary and reuses the existing workspace-provider pattern. |
| Security | File bodies are read locally for hashing but are never returned in public API, demo, preview, docs, or metrics. |
| Backend | The demo flag composes generation and verification without opening runtime/provider calls. |
| Frontend | The preview now shows generated artifact verification status and counts without rendering source bodies. |
| Test | Unit tests cover success, missing hash, hash mismatch, missing expected record, missing file, tamper mismatch, path traversal, absolute path, exposure, and side-effect guards. |

## Quantitative Results

| Metric | Result |
|---|---:|
| Generated artifact verification scenarios | 1 |
| Expected files checked | 5 |
| File check records | 5 |
| Content hash matches | 5 |
| Byte count matches | 5 |
| Missing file blocked fixtures | 1 |
| Path traversal blocked fixtures | 1 |
| Absolute path blocked fixtures | 1 |
| Workspace hash mismatch blocked fixtures | 1 |
| Raw file content returns | 0 |
| Local root path returns | 0 |
| Provider calls | 0 |
| SDK imports | 0 |
| Env value reads | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Package installs | 0 |
| Builds | 0 |
| Server starts | 0 |
| DAACS target runtime calls | 0 |

## Public Projection

Allowed public fields:

- `status`
- `reason`
- `generated_workspace_hash`
- `generated_workspace_projection_hash`
- `generated_artifact_verification_hash`
- `file_check_records[].workspace_relative_path`
- `file_check_records[].expected_content_hash`
- `file_check_records[].actual_content_hash`
- `file_check_records[].expected_byte_count`
- `file_check_records[].actual_byte_count`
- `counts`
- `execution_boundary`
- `repository_boundary`
- `claim_boundary`

Forbidden public fields:

- file body
- local root path
- raw prompt
- raw log
- provider payload
- subprocess output
- secret or env value

## Verification

```text
python -m compileall packages\daacs_builder\target_runtime_generated_artifact_verification.py apps\api\agentic_workbench_api\services\target_runtime_generated_artifact_verification.py apps\api\agentic_workbench_api\main.py examples\demo-service-flow\run_local_demo.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_generated_artifact_verification.py tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py
passed

python -m pytest tests\unit\test_target_runtime_generated_artifact_verification.py -q
10 passed

python -m pytest tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py -q
12 passed

python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-verify-01-demo --include-daacs-runtime-generated-artifact-verification
status passed, comparison_variant_count 8, verification status passed, file check count 5, content hash matches 5, target runtime calls 0

python examples\demo-service-flow\render_artifact_preview.py --store-root .local\aw-verify-01-preview --output .local\aw-verify-01-preview.html
preview HTML written

python -m pytest tests -q --color=no
670 passed in 213.25s

git diff --check
passed
```

Browser screenshot verification was not run in this session. Static HTML
generation and smoke tests were used as the fallback verification.

## Claim Boundary

Allowed:

- Claiming nine restricted fixture files were verified by hash and byte count.
- Claiming the public preview shows verification counts.

Not allowed:

- Claiming package install success.
- Claiming generated app build success.
- Claiming hosted or production app behavior.
- Claiming DAACS target runtime execution.
- Claiming Solar Pro 3 output.

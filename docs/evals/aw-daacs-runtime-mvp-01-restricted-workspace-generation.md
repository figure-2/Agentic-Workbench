# AW-DAACS-RUNTIME-MVP-01 Restricted Workspace Generation Eval

## Summary

AW-DAACS-RUNTIME-MVP-01 adds a local, template-backed generated workspace
surface. It writes a sanitized fixture app skeleton under a run-scoped
workspace and returns only relative paths, hashes, byte counts, status, and
zero-call counters.

This is not DAACS target runtime execution. It does not install packages, run a
build, start a server, call a provider, read environment values, or make a
network call.

## Official References Checked

| Reference | Use |
|---|---|
| [React first component docs](https://react.dev/learn/your-first-component) | Component file shape and top-level component organization |
| [Vite guide](https://vite.dev/guide/) | React/TypeScript starter direction and template family |
| [Vite create-vite React TS template package](https://raw.githubusercontent.com/vitejs/vite/main/packages/create-vite/template-react-ts/package.json) | Minimal package script names and Vite/React template convention |
| [Vite create-vite React TS App template](https://raw.githubusercontent.com/vitejs/vite/main/packages/create-vite/template-react-ts/src/App.tsx) | App component template reference |

The implementation does not copy official template bodies. It uses a small
sanitized fixture skeleton shaped by those references.

## Team Review

| Lens | Finding |
|---|---|
| Product | This is the first portfolio-visible generated output folder. It improves demo value without waiting for live runtime execution. |
| Architecture | The generator follows the existing RUNTIME-06 workspace-provider pattern and keeps the configured root out of public responses. |
| Security | File writes are scoped to `<store_root>/runs/<run_id>/generated-app/`. Public output excludes file content and local root paths. |
| Backend | API endpoint and local demo flag reuse the existing preflight/admission/output-manifest/bundle chain. |
| Frontend | The preview surface now shows generated workspace file cards without rendering source bodies. |
| Test | Unit tests cover success, missing prerequisite, hash mismatch, unsafe run id, traversal-like template id, absolute-like template id, missing brief hash, exposure, and side-effect guards. |

## Quantitative Results

| Metric | Result |
|---|---:|
| Generated workspace scenarios | 1 |
| Generated files | 9 |
| File hash count | 5 |
| File byte count | > 0 |
| Required generated paths | 5/5 |
| Write allowlist violations | 0 |
| Path traversal-like template fixtures blocked | 1 |
| Absolute-like template fixtures blocked | 1 |
| Unsafe run id fixtures blocked | 1 |
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

## Generated Files

```text
runs/<run_id>/generated-app/
  README.md
  package.json
  src/App.tsx
  src/api.ts
  tests/verification.md
```

Public records expose only:

- `workspace_relative_path`
- `content_hash`
- `byte_count`
- `label`
- `artifact_kind`
- `status`

## Verification

```text
python -m compileall packages\daacs_builder\target_runtime_restricted_workspace_generation.py apps\api\agentic_workbench_api\services\target_runtime_restricted_workspace_generation.py examples\demo-service-flow\run_local_demo.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_restricted_workspace_generation.py tests\smoke\test_daacs_runtime_preflight.py
passed

python -m pytest tests\unit\test_target_runtime_restricted_workspace_generation.py -q
9 passed

python -m pytest tests\smoke\test_daacs_runtime_preflight.py tests\smoke\test_artifact_preview_surface.py -q
11 passed

python -m pytest tests -q
659 passed in 234.11s

python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-daacs-runtime-mvp-01-demo --include-daacs-runtime-restricted-workspace-generation
status passed, comparison_variant_count 7, generated file count 5, build calls 0

python examples\demo-service-flow\render_artifact_preview.py --store-root .local\aw-daacs-runtime-mvp-01-preview --output .local\aw-daacs-runtime-mvp-01-preview.html
preview HTML written
```

Browser screenshot verification was not run because the local Browser/Playwright
tooling was unavailable in this session. HTML generation and smoke tests were
used as the fallback verification.

## Claim Boundary

Allowed:

- Local fixture app skeleton folder generated.
- File records are hash/path/count-only.
- Build/run/hosted status remains not executed.

Not allowed:

- Claiming DAACS target runtime execution.
- Claiming a built or hosted app.
- Claiming Solar Pro 3 output.
- Returning generated file content through public API or preview.

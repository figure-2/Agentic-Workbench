# AW-APP-01 Artifact Preview Surface

## Scope

`AW-APP-01` adds a portfolio-facing static preview over the existing local
service-shaped demo summary. The preview renders the Workbench path from idea
to planning, PRD, implementation brief, approval, dry-run runner plan,
verification report, and sanitized fixture artifact records.

This work intentionally reuses the `AW-MVP-01` public summary and
`AW-DAACS-RUNTIME-06` fixture materialization projection. It does not add a new
persistence layer, start a server, install packages, build a generated app, call
Solar Pro 3, or execute the DAACS target runtime.

## Surface

Command:

```powershell
python examples/demo-service-flow/render_artifact_preview.py --store-root .local/aw-app-01-demo --output .local/aw-app-01-preview.html
```

Output:

```text
.local/aw-app-01-preview.html
```

The CLI prints only the output file name, not the local store root.

## Quantitative Results

Measured on 2026-06-04.

| Metric | Result |
|---|---:|
| Golden path scenario count | 1 |
| Workflow stage coverage | 7/7 |
| Workflow stage coverage percent | 100.0 |
| Demo artifact count | 6 |
| Preview fixture artifact cards | 3 |
| Document chain rows | 5 |
| DAACS runtime comparison variants | 6 |
| Fixture materialization record count | 3 |
| Fixture materialization content hash count | 3 |
| Fixture workspace writes | 3 |
| Fixture writes outside workspace | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| Solar Pro 3 provider calls | 0 |
| DAACS target runtime calls | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Local root path returns | 0 |
| Artifact content returns | 0 |

## Comparison Check

| Surface | Reviewer value | Fixture artifact cards | Stage coverage | Live/provider calls | Target runtime calls |
|---|---|---:|---:|---:|---:|
| JSON demo summary | Machine-readable evidence | 0 | 7/7 | 0 | 0 |
| Static UI shell | Workflow and policy status | 0 | 7/7 | 0 | 0 |
| AW-APP-01 preview | Artifact-oriented portfolio view | 3 | 7/7 | 0 | 0 |

Interpretation: AW-APP-01 improves visible portfolio value by surfacing the
fixture artifact records as cards while preserving the same local dry-run
execution boundary.

## Verification

```powershell
python -m pytest tests\smoke\test_artifact_preview_surface.py -q
```

Result:

```text
2 passed
```

```powershell
python examples\demo-service-flow\render_artifact_preview.py --store-root .local\aw-app-01-demo --output .local\aw-app-01-preview.html
```

Result:

```text
Wrote aw-app-01-preview.html
```

Full regression:

```powershell
python -m pytest tests -q
```

Result:

```text
642 passed in 201.61s
```

## Public Boundary

The preview is limited to labels, status, counts, hashes, byte counts, and
workspace-relative paths. It does not render file contents, local root paths,
secret values, provider request bodies, runtime request bodies, raw logs, or
approval authorization material.

## Remaining Work

The preview is still a local static artifact. The next implementation should
move toward a controlled Solar planner spike or a restricted generated-app
workspace experiment instead of adding more no-call boundary layers.

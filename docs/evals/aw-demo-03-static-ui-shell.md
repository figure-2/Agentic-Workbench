# AW-DEMO-03 Static UI Shell

## Conclusion

`AW-DEMO-03` adds a local static HTML shell over the existing public demo
summary. It improves demo readability without adding a server, live provider,
or target runtime path.

## Scope

- `render_static_ui_shell(summary)`
- `write_static_ui_shell(summary, output_path)`
- CLI entrypoint for optional HTML output
- smoke tests for rendering and output-file behavior

## Non-Scope

- hosted dashboard
- React/Next.js app
- browser-side API calls
- Solar Pro 3 provider integration
- `.env` value read
- DAACS target runtime invocation
- generated app build
- raw artifact body rendering

## Acceptance Evidence

| Gate | Result |
|---|---|
| static UI consumes public demo summary | covered |
| `public-summary-only` marker | covered |
| live policy displays `closed / eligible only` | covered |
| execution permission remains closed | covered |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |
| raw prompt/log/body/provider/runtime findings | 0 |
| raw approval authorization findings | 0 |
| local path findings | 0 |

## Measured Commands

```powershell
python -m pytest tests\smoke\test_static_ui_shell.py -q
python -m compileall examples packages tests
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

Manual visual check:

```powershell
msedge --headless --screenshot=.local\aw-demo-03-static-ui.png --window-size=1280,900 .local\aw-demo-03-static-ui.html
```

Observed result: the first viewport renders the run overview, workflow rail,
DIV/DAACS identity sections, artifact list, and evidence panel without blank
content or overlapping text.

## Public Claim Boundary

Allowed:

```text
AW-DEMO-03 adds a local static UI shell over sanitized fixture/dry-run
projections and shows provider/runtime call counts as 0.
```

Forbidden:

```text
AW-DEMO-03 is a hosted dashboard, live runtime monitor, provider integration,
generated app delivery surface, or production UI.
```

## External Audit

Finding: no blocker.

- The shell uses `run_demo()` public summary output.
- It does not query repository tables directly.
- It does not read env values.
- It does not call provider or runtime code.
- It displays live-open policy as closed / eligible only.

Residual risk:

- This is static HTML. It does not yet provide navigation, user interaction,
  multi-run browsing, or a production UI framework. Those require separate
  implementation units.

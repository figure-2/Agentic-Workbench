# AW-GENERATED-QUALITY-02 Generated App Feature Depth Eval

## Summary

`AW-GENERATED-QUALITY-02` improves the generated fixture app from a static
portfolio dashboard into a deeper app-shaped experience. The generated app now
includes an action center, evidence timeline, owner filter, reviewer decision
section, and a first-screen feature depth control strip.

This remains a sanitized fixture app. It does not claim hosted deployment,
production readiness, external provider success, or uncontrolled DAACS target
runtime execution.

## Team Review

Product lens: the generated app now communicates a clearer product workflow,
not just a static artifact list.

Frontend lens: the first screen now shows feature depth through action,
filtering, and reviewer-decision concepts. The task board includes a stateful
owner filter using local React state.

Architecture lens: the implementation stays template-backed and run-scoped.
No new repository, provider, or runtime execution path was added.

Security lens: public projection remains hash/count/status-only. Generated file
bodies, screenshot paths, page text, local root paths, provider payloads, and
credential material are not returned.

QA lens: static validation now measures expanded app/API markers, and the
screenshot-backed portfolio command still builds and browser-verifies the app.

## Measured Result

Command:

```powershell
python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-generated-quality-02 --screenshot-backed
```

| Metric | Value |
|---|---:|
| Generated fixture app file count | 9 |
| Generated app byte count | 15392 |
| App markers | 13/13 |
| API markers | 8/8 |
| Verification/boundary markers | 4/4 |
| Zero-call markers | 5/5 |
| Local build status | passed |
| Screenshot evidence count | 1 |
| Screenshot byte count | 53820 |
| Preview server starts/stops | 1/1 |
| Provider calls | 0 |
| Solar additional calls | 0 |
| DAACS target runtime calls | 0 |
| Raw/public body exposure | 0 |
| Screenshot path exposure | 0 |
| Page text exposure | 0 |

## Feature Markers Added

- Feature Depth Control Strip
- Action Center
- Evidence Timeline
- Owner Filter
- Reviewer Decision
- Interaction Ready
- FixtureAction API type
- EvidenceEvent API type
- getFixtureActions API fixture
- getEvidenceTimeline API fixture

## Verification

| Command | Result |
|---|---:|
| `python -m compileall packages\daacs_builder\target_runtime_restricted_workspace_generation.py packages\daacs_builder\target_runtime_generated_workspace_static_validation.py examples\demo-service-flow\render_artifact_preview.py tests\unit\test_target_runtime_restricted_workspace_generation.py tests\unit\test_target_runtime_generated_workspace_static_validation.py tests\smoke\test_artifact_preview_surface.py tests\smoke\test_daacs_runtime_preflight.py` | passed |
| `python -m pytest tests\unit\test_target_runtime_restricted_workspace_generation.py tests\unit\test_target_runtime_generated_workspace_static_validation.py tests\smoke\test_artifact_preview_surface.py tests\smoke\test_daacs_runtime_preflight.py::test_local_service_demo_statically_validates_generated_workspace -q --color=no` | 23 passed |
| `python examples\demo-service-flow\run_portfolio_demo.py --output-dir .local\aw-generated-quality-02 --screenshot-backed` | passed |
| `python -m pytest tests\unit\test_public_claim_projection_docs.py -q --color=no` | 3 passed |
| `git diff --check` | passed |
| `python -m pytest tests -q --color=no` | 742 passed in 238.60s |

## Interpretation

The generated app is still fixture-backed, but it now looks more like a
reviewable application surface. The next quality step should verify the
interactive owner-filter click path rather than adding more static sections.

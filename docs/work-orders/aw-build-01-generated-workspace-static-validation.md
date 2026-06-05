# AW-BUILD-01 Generated Workspace Static Validation

## Summary

```text
id: AW-BUILD-01
depends_on:
  - AW-VERIFY-01
scope:
  Add fast static validation over the generated fixture app workspace without
  package install, build, server start, provider call, or DAACS target runtime
  execution.
risk_level: medium
rollback_plan:
  Remove static validation service/API/demo/tests/docs and return to
  AW-VERIFY-01 hash/byte-count verification.
```

## Goal

Increase portfolio-visible confidence quickly by checking the generated app
skeleton shape beyond file existence:

- `package.json` is valid JSON.
- expected scripts are present as labels only.
- `src/App.tsx` and `src/api.ts` are present and non-empty.
- app component and API client contain expected public fixture markers.
- no raw prompt, secret, provider payload, local root path, or file body is
  returned in public projection.

## Scope

### A. Static Validation Contract

Inputs:

- `run_id`
- `generated_artifact_verification_hash`
- `generated_artifact_verification_projection`
- configured restricted workspace root

Acceptance tests:

- Missing verification hash is blocked.
- Verification hash mismatch is blocked.
- Missing checked files are blocked.
- Public projection returns status, hashes, counts, and reasons only.
- File bodies are not returned.

### B. Local Static Checks

Allowed reads:

- Only the nine verified workspace-relative files.
- Only under `<configured_root>/runs/<run_id>/generated-app/`.

Acceptance tests:

- `package.json` parses as JSON.
- required package script labels are present: `dev`, `build`, `preview`, `verify`.
- `src/App.tsx` contains an exported component marker.
- `src/api.ts` contains the fixture API summary marker.
- `tests/verification.md` contains zero-call counter rows.
- raw body/root path/provider/env/subprocess/network exposure count is `0`.

### C. Demo and Preview Integration

Acceptance tests:

- `run_local_demo.py --include-daacs-runtime-generated-artifact-verification`
  can optionally include static validation.
- preview shows static validation status/counts.
- package install, build, server start, subprocess, network, provider, and
  target runtime call counts remain `0`.

## Out Of Scope

- Running `npm install`
- Running TypeScript compiler
- Running Vite build
- Starting a local server
- Executing DAACS target runtime
- Calling Solar Pro 3 or other providers
- Claiming generated app production readiness

## Quantitative Targets

| Metric | Target |
|---|---:|
| Static validation scenario count | 1 |
| Files statically checked | 9 |
| JSON parse checks | 1 |
| Required script labels | 4/4 |
| TSX marker checks | >= 1 |
| API marker checks | >= 1 |
| Zero-call report marker checks | >= 1 |
| Raw file body returns | 0 |
| Local root path returns | 0 |
| Provider calls | 0 |
| Network calls | 0 |
| Subprocess calls | 0 |
| Package installs | 0 |
| Builds | 0 |
| Server starts | 0 |
| DAACS target runtime calls | 0 |

## Done Criteria

- Static validation service and public projection exist.
- Demo and preview can show the validation result.
- Targeted unit and smoke tests pass.
- Full regression test passes once.
- Metrics and eval docs record quantitative results.

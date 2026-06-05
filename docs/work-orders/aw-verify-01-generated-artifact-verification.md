# AW-VERIFY-01 Generated Artifact Verification

## Summary

```text
id: AW-VERIFY-01
depends_on:
  - AW-DAACS-RUNTIME-MVP-01
scope:
  Verify the restricted fixture app skeleton without opening live provider calls
  or unrestricted target runtime execution.
risk_level: high
rollback_plan:
  Remove verification service/API/demo/tests/docs and return to
  AW-DAACS-RUNTIME-MVP-01 generated workspace preview.
```

## Goal

Add a verification boundary over the generated workspace folder.

The system should inspect the generated file records and, where safe, the local
fixture files under the configured run-scoped workspace. It should report
whether the skeleton has the expected files and whether the static content
matches the public hash records.

## Scope

### A. Verification Contract

Inputs:

- `run_id`
- `generated_workspace_hash`
- `file_records`
- configured restricted workspace root

Acceptance tests:

- Missing generated workspace hash is blocked.
- Hash mismatch is blocked.
- Missing expected file is blocked.
- Public projection returns status, hashes, counts, and reasons only.
- File bodies are not returned.

### B. Local File Integrity Check

Allowed reads:

- Only files listed in `file_records`
- Only under `<configured_root>/runs/<run_id>/generated-app/`

Acceptance tests:

- 5/5 expected files are found.
- 5/5 content hashes match the recorded hashes.
- Path traversal in file records is blocked.
- Absolute file record paths are blocked.
- Local root path is not returned.

### C. Demo and Preview Integration

Acceptance tests:

- `run_local_demo.py --include-daacs-runtime-restricted-workspace-generation`
  can optionally include verification.
- Preview shows verification status/counts.
- Package install, build, server start, subprocess, network, provider, and
  target runtime call counts remain `0`.

## Out Of Scope

- Installing dependencies
- Running `npm run build`
- Starting a local server
- Executing DAACS target runtime
- Calling Solar Pro 3 or other providers
- Claiming hosted or fully built app behavior

## Quantitative Targets

| Metric | Target |
|---|---:|
| Generated workspace scenarios | 1 |
| Expected files checked | 5 |
| Content hash matches | 5 |
| Missing file blocked fixtures | >= 1 |
| Path traversal blocked fixtures | >= 1 |
| Absolute path blocked fixtures | >= 1 |
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

- Verification service and public projection exist.
- Targeted unit and smoke tests pass.
- Full regression test passes once.
- Metrics and eval docs record quantitative results.


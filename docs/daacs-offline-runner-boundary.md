# DAACS Offline Runner Boundary

## Conclusion

`DAACSOfflineRunner` is an execution boundary, not a DAACS runtime wrapper. It accepts the mapped DAACS-compatible state, validates the contract, and returns a `VerificationReport` without importing DAACS runtime modules, spawning agents, installing packages, starting servers, writing files, or calling providers.

## Role

```text
BuildSpec
  -> DAACS-compatible initial state
  -> DAACSOfflineRunner
  -> VerificationReport
```

The runner is the last offline gate before any future live DAACS integration. Live execution must enter through a separate runner/provider boundary.

## Blocked Execution Surfaces

| Surface | Boundary decision |
|---|---|
| CLI agent execution | blocked |
| provider/LLM call | blocked |
| subprocess execution | blocked |
| package install | blocked |
| local server start | blocked |
| filesystem write | blocked |

The runner also rejects unsafe state injection: live mode, non-empty `llm_sources`, `cli_assistant_available=true`, prefilled generated files, pre-seeded `compatibility_verified=true`, missing required state keys, and unsafe `project_dir`.

## Required State Checks

- `session_id`
- `project_dir`
- `mode`
- `cli_assistant_available`
- `api_spec`
- `frontend_spec`
- `acceptance_criteria`
- `build_contract`
- `current_phase`
- `turn_history`

## Report Contract

The runner returns a `VerificationReport` with:

- pass/fail checks for state contract, offline mode, project path, CLI block, provider block, subprocess block, package install block, server start block, filesystem write block, and API/frontend alignment
- zero-valued side-effect metrics: `live_llm_calls`, `live_api_calls`, `provider_calls`, `cli_agent_invocations`, `subprocess_calls`, `package_install_calls`, `server_start_calls`, `filesystem_writes`
- explicit `detected_blocked_operation_count` and `unsafe_state_rejection_count`
- empty `generated_files`

## Namespace Rule

`verification_report_from_daacs_output()` now rejects generated file names containing parent traversal, absolute paths, drives, null bytes, or URL-encoded traversal. It must not silently normalize `backend/../secret.txt` into a different namespace.

## Known Limits

This does not run DAACS subgraphs, compile generated code, start a backend, build a frontend, or verify Solar Pro 3 quality. It proves only that the offline runner can admit a mapped state and keep live execution surfaces closed.


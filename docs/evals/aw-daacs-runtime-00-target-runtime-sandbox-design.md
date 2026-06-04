# AW-DAACS-RUNTIME-00 Target Runtime Sandbox Design

## Conclusion

AW-DAACS-RUNTIME-00은 DAACS target runtime 실행이 아니라, dry-run
RunnerPlan 이후에 필요한 sandbox/write allowlist/command/rollback
preflight 계약을 고정한 단계다. 실행 권한은 계속 `0`이다.

## Scope

포함:

- DAACS target runtime sandbox preflight contract
- `POST /api/v1/daacs/runtime/preflight`
- local demo의 dry-run vs target-runtime-preflight 비교 실험
- run-scoped workspace validation
- write allowlist validation
- package install/server/network/subprocess operation block detection
- rollback/abort/cleanup policy validation
- hash/count/status/reason public projection

제외:

- DAACS target runtime call
- source DAACS subprocess
- package installation
- local app server start
- unrestricted file write
- network call
- raw generated file body persistence
- raw log or command output persistence
- provider/planner call

## Boundary Flow

```text
RunnerPlan hash
-> TargetRuntimePreflightRequest
-> sandbox policy validation
-> run-scoped workspace validation
-> write allowlist validation
-> command/network/install policy validation
-> rollback/abort policy validation
-> TargetRuntimePreflightResult
-> blocked public projection
```

## Acceptance Results

| Acceptance | Result |
|---|---|
| Missing sandbox policy blocks before runtime admission | covered |
| Missing run-scoped workspace intent blocks before runtime admission | covered |
| Path traversal is blocked | covered |
| Absolute path outside workspace is blocked | covered |
| File write outside allowlist is blocked | covered |
| Package install command is blocked | covered |
| Server start command is blocked | covered |
| Network command is blocked | covered |
| Missing rollback/abort policy blocks | covered |
| Public projection exposes hash/status/reason/count only | covered |
| Filesystem write count | 0 |
| Subprocess count | 0 |
| Network call count | 0 |
| DAACS target runtime call count | 0 |
| Raw file/log/runtime payload findings | 0 |

## Comparison Experiment

Representative local service demo command:

```powershell
python examples/demo-service-flow/run_local_demo.py --store-root .local/aw-daacs-runtime-00-demo --include-daacs-runtime-preflight
```

| Variant | Status | Stage coverage | Filesystem writes | Subprocess calls | Network calls | Runtime calls |
|---|---|---:|---:|---:|---:|---:|
| `dry_run_runner` | passed | 7/7 | 0 | 0 | 0 | 0 |
| `target_runtime_preflight` | blocked | preflight-only | 0 | 0 | 0 | 0 |

## Quantitative Results

| Metric | Value |
|---|---:|
| Comparison variants | 2 |
| Dry-run fixture stage coverage | 7/7 |
| Target runtime preflight check count | 19 |
| Target runtime preflight failed check count | 1 |
| Intentional execution-closed check count | 1 |
| Allowed write path count | 3 |
| Requested write path count | 3 |
| Expected output path count | 3 |
| Denied path count in clean comparison | 0 |
| Blocked operation count in clean comparison | 0 |
| Rollback plan count | 1 |
| Abort criteria count | 2 |
| Cleanup step count | 2 |
| Path traversal fixtures blocked | 1/1 |
| Absolute path fixtures blocked | 1/1 |
| Disallowed write fixtures blocked | 1/1 |
| Package install fixtures blocked | 1/1 |
| Server start fixtures blocked | 1/1 |
| Network command fixtures blocked | 1/1 |
| Filesystem writes | 0 |
| Subprocess calls | 0 |
| Network calls | 0 |
| DAACS target runtime calls | 0 |
| Raw exposure findings | 0 |
| Public claim drift findings | 0 |
| New unit tests | 9 |
| New smoke tests | 2 |
| Full pytest passed cases | 598 |

## Verification

```powershell
python -m pytest tests/unit/test_target_runtime_sandbox.py -q --color=no
python -m pytest tests/smoke/test_daacs_runtime_preflight.py -q --color=no
python -m compileall apps examples packages tests
python -m pytest tests -q --color=no
```

Observed result:

```text
9 passed
2 passed
compileall passed
598 passed
```

## Claim Boundary

This is sandbox preflight design only. It does not prove generated artifact
quality, hosted behavior, install success, build success, runtime verification,
or target runtime execution.

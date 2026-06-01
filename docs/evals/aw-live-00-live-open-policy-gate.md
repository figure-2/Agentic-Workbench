# AW-LIVE-00 Live-Open Policy Gate

## Conclusion

`AW-LIVE-00` adds a fail-closed policy gate for future Solar Pro 3 and DAACS
target runtime work. It records readiness controls and zero-call boundaries,
but it does not open provider or runtime execution.

## Scope

- `LiveOpenRequest`
- `LiveOpenDecision`
- `evaluate_live_open_request()`
- public sanitized decision output
- unit tests for blocked and eligible readiness states

## Non-Scope

- Solar Pro 3 API call
- Upstage SDK import
- `.env` value read
- DAACS target runtime invocation
- CLI agent execution
- package install
- server start
- generated app delivery
- production approval or key infrastructure

## Acceptance Evidence

| Gate | Result |
|---|---|
| unknown surface blocked | covered |
| missing controls blocked | covered |
| requested provider/runtime/network/write attempts blocked | covered |
| complete readiness stays `allowed_to_execute=false` | covered |
| Solar env key name referenced without value read | covered |
| DAACS runtime rejects provider env key name | covered |
| forbidden public key findings | 0 |
| Solar Pro 3 calls | 0 |
| DAACS target runtime calls | 0 |

## Measured Commands

```powershell
python -m pytest tests\unit\test_live_open_policy.py -q
python -m compileall packages apps tests
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-00 adds a local readiness policy gate for future provider/runtime work.
It keeps provider and target runtime call counts at 0 and does not grant
execution permission.
```

Forbidden:

```text
AW-LIVE-00 integrates Solar Pro 3, opens DAACS runtime execution, proves live
provider quality, or grants production execution permission.
```

## External Audit

Finding: no blocker.

- The gate is side-effect-free.
- It does not read env values.
- It does not import provider/runtime SDKs.
- It keeps the happy path eligible only for a later implementation unit.
- Public projection uses readiness checks, reason codes, and zero-call metrics
  only.

Residual risk:

- `AW-LIVE-00` is a policy skeleton. It does not yet implement cost metering,
  sandbox enforcement, rollback execution, production signing, or runtime
  isolation. Those must remain separate implementation units.

# AW-LIVE-01 Disabled Solar Pro 3 Provider Adapter

## Conclusion

`AW-LIVE-01` adds a disabled-by-default Solar Pro 3 live-path adapter skeleton
and tests. The adapter can be registered and resolved, but every invocation
returns a blocked `ProviderResult`.

## Scope

- `SolarPro3LiveAdapterConfig`
- `DisabledSolarPro3LiveAdapter`
- `ProviderAdapterRegistry`
- unit tests for registration, missing policy, missing config, mode separation,
  closed execution permission, and side-effect guards

## Non-Scope

- Solar Pro 3 API call
- Upstage SDK import
- `.env` value read
- network socket
- provider response parsing
- production cost metering
- production key registry
- hosted execution

## Acceptance Evidence

| Gate | Result |
|---|---|
| adapter registration possible | covered |
| default invocation blocked | covered |
| missing live-open policy blocked | covered |
| missing timeout/cost/quota config blocked | covered |
| fake provider mode rejected by live adapter | covered |
| eligible policy still keeps execution permission closed | covered |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| forbidden public key findings | 0 |

## Measured Commands

```powershell
python -m pytest tests\unit\test_solar_live_adapter.py -q
python -m compileall packages tests
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-01 adds a disabled Solar Pro 3 adapter skeleton and verifies that the
future real-path adapter remains blocked with provider calls at 0.
```

Forbidden:

```text
AW-LIVE-01 calls Solar Pro 3, imports the Upstage SDK, validates model output,
or proves provider quality.
```

## External Audit

Finding: no blocker.

- Fake and live provider paths are separated by mode.
- The adapter is registered but disabled by default.
- A complete live-open readiness decision still does not grant execution.
- Timeout, cost, and quota config are required before later live work can be
  proposed.
- The adapter does not read env values, import SDKs, open network sockets, or
  call external APIs.

Residual risk:

- This adapter is a skeleton. Cost metering, timeout execution, request signing,
  provider response parsing, retry policy, and production runtime controls are
  not implemented.

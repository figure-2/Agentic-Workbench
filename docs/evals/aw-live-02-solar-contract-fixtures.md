# AW-LIVE-02 Solar Pro 3 Contract Fixtures

## Conclusion

`AW-LIVE-02` adds no-call request/response contract fixtures and a
cost/timeout policy contract for a future Solar Pro 3 adapter path. It keeps
provider calls, SDK imports, env value reads, and network calls at 0.

## Scope

- `SolarCostTimeoutPolicy`
- `SolarRequestContractFixture`
- `SolarResponseProjectionFixture`
- `SolarContractFixtureResult`
- contract helpers for request fixture and response projection fixture
- unit tests for policy block, sanitized projection, and side-effect guards

## Non-Scope

- Solar Pro 3 API call
- Upstage SDK import
- `.env` value read
- network call
- provider response parser
- real cost metering
- hosted execution
- production provider readiness

## Acceptance Evidence

| Gate | Result |
|---|---|
| request fixture uses prompt contract hash only | covered |
| missing timeout/cost/API quota/token quota blocked | covered |
| invalid prompt contract hash blocked | covered |
| fake mode blocked in request contract fixture | covered |
| response projection uses sanitized summary and hashes only | covered |
| raw input/body/provider value leakage | 0 |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| forbidden public key findings | 0 |

## Measured Commands

```powershell
python -m pytest tests\unit\test_solar_contracts.py -q
python -m compileall packages tests
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-02 adds no-call Solar Pro 3 request/response contract fixtures and
cost/timeout policy checks.
```

Forbidden:

```text
AW-LIVE-02 calls Solar Pro 3, validates model output, parses live provider
responses, proves provider quality, or opens production provider execution.
```

## External Audit

Finding: no blocker.

- The request fixture is based on `prompt_contract_hash`.
- The response projection contains summary and hashes only.
- Raw input/body/provider values are ignored.
- Policy omissions block before fixture creation.
- No SDK import, env value read, network call, or external API call is present.

Residual risk:

- This is still a contract fixture. Real request serialization, provider
  response parsing, timeout execution, retry execution, and cost accounting are
  not implemented.

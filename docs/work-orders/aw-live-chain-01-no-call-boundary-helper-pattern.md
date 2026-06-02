# AW-LIVE-CHAIN-01 Work Order: No-Call Boundary Helper Pattern

## Summary

`AW-LIVE-CHAIN-01` reduces repeated no-call boundary implementation logic while
preserving the existing public API/read-model contract.

This is a maintenance and safety refactor. It is still not a live provider
call.

## Work Unit

```text
id: AW-LIVE-CHAIN-01
depends_on: AW-LIVE-68
scope: repeated no-call boundary helper/pattern consolidation
risk_level: medium
rollback_plan: helper extraction revert, AW-LIVE-68 explicit implementation 유지
```

## Acceptance Tests

```text
- public field names unchanged
- existing AW-LIVE-60~68 tests remain green
- helper covers expected-hash validation
- helper covers payload-presence validation
- helper covers hash/count projection
- helper covers claim-boundary hashing
- helper covers no-call counter hashing
- raw/provider/env/network exposure 0
- Solar Pro 3 / DAACS target runtime call 0
```

## Implementation Notes

1. Add a private no-call boundary evaluation helper.
2. Keep public output keys unchanged.
3. Adopt the helper in the two latest projections first:
   - `AW-LIVE-67`
   - `AW-LIVE-68`
4. Preserve the existing reason strings.
5. Preserve the existing stable hash payload shape.
6. Run integration regression before broadening helper adoption.

## Quantitative Targets

| Metric | Target |
|---|---:|
| helper-adopted projections | 2 |
| public field name changes | 0 |
| component count on complete path | 8 |
| component hash count on complete path | 4 |
| no-call counter count | 13 |
| claim-boundary check count | 3 |
| execution permission count | 0 |
| provider envelope integration tests passed | 198 |
| full project tests passed | 573 |
| raw/provider/env/network exposure | 0 |

## Specialist Review

- Product lens: this should be presented as maintainability work, not a live
  capability.
- Architecture lens: adopting the helper in the newest two boundaries first is
  safer than rewriting the whole live chain at once.
- Security lens: the helper must continue to produce hash/count-only public
  projections and must not add provider/env/network access.
- Test lens: public projection integration tests are mandatory because public
  field stability is the main risk.
- Audit lens: docs must clearly distinguish no-call helper consolidation from
  live provider readiness.

## Follow-Up Work

```text
id: AW-LIVE-CHAIN-02
depends_on: AW-LIVE-CHAIN-01
scope: extend helper adoption to AW-LIVE-60 through AW-LIVE-66 in small batches
risk_level: medium
rollback_plan: helper adoption batch revert, AW-LIVE-CHAIN-01 latest-boundary helper 유지
```

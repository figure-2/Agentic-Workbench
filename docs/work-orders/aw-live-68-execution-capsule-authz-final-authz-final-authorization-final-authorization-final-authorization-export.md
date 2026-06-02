# AW-LIVE-68 Work Order: Execution Capsule Authz Final Authz Final Authorization Final Authorization Final Authorization Export Boundary

## Summary

`AW-LIVE-68` adds a disabled first-call final no-call execution capsule
authorization final authorization final authorization final authorization final
authorization export/read-model boundary.

This is still not a live provider call.

## Work Unit

```text
id: AW-LIVE-68
depends_on: AW-LIVE-67
scope: disabled first-call final no-call execution capsule authorization final authorization final authorization final authorization final authorization export/read-model boundary, still no provider call
risk_level: high
rollback_plan: export/read-model boundary 제거, AW-LIVE-67 상태 유지
```

## Acceptance Tests

```text
- execution_capsule_authz_final_authz_final_authz_final_authz_final_authz_hash가 expected hash와 일치
- export/read-model은 final-authorization/export metadata/no-call counters/claim-boundary를 hash/count로만 묶음
- export/read-model이 있어도 execution permission은 0
- public projection은 hash/status/reason/count만 반환
- env value read / SDK import / API call / network call 0 유지
```

## Implementation Notes

- Add final authorization export projection.
- Add final authorization export read-model projection.
- Add blocked fallback projections for missing expected hash and missing export
  payload.
- Add API integration tests for:
  - missing expected final authorization hash
  - missing export payload
  - complete export/read-model path
- Add demo/smoke assertions.
- Update eval, runbook, metrics, claim boundary, architecture, and migration docs.

## Quantitative Targets

| Metric | Target |
|---|---:|
| API regression cases added | 3 |
| complete-path component count | 8 |
| complete-path passed count | 8 |
| complete-path mismatch count | 0 |
| component hash count | 4 |
| no-call counter count | 13 |
| claim-boundary check count | 3 |
| export count | 1 |
| execution permission count | 0 |
| raw/provider/env/network exposure | 0 |

## Specialist Review

- Product lens: This improves demo/read-model visibility, not live execution.
- Architecture lens: The new boundary follows the existing no-call evidence
  chain and should be refactored only after this step is stable.
- Security lens: The public surface must not expose raw prompt, provider body,
  provider payload, authorization material, signature, nonce, `.env` values, or
  local paths.
- Test lens: The acceptance tests must prove both blocked and complete no-call
  paths.
- Audit lens: Public docs must not claim provider success, production readiness,
  or live model quality.

## Follow-Up Work

```text
id: AW-LIVE-CHAIN-01
depends_on: AW-LIVE-68
scope: repeated no-call boundary helper/pattern consolidation
acceptance_tests:
  - public field names unchanged
  - existing AW-LIVE-60~68 tests remain green
  - helper covers expected-hash, payload-presence, claim-boundary, no-call counter, and count projection logic
  - raw/provider/env/network exposure 0
  - Solar Pro 3 / DAACS target runtime call 0
risk_level: medium
rollback_plan: helper extraction revert, AW-LIVE-68 explicit implementation 유지
```

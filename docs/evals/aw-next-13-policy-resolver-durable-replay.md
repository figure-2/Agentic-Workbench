# AW-NEXT-13 Policy Resolver / Durable Replay Boundary

## Conclusion

AW-NEXT-13은 real provider/live 실행을 열지 않고, provider/live approval admission 앞에 `ApprovalPolicyResolver`, `KeyIdentityRegistry`, adapter-backed `DurableReplayStore` skeleton을 추가한 단계다. Solar Pro 3 API 호출과 DAACS live 실행은 계속 0으로 고정한다.

## Scope

Implemented:

- `ApprovalPolicyResolver` for explicit policy ID resolution
- `KeyIdentityRegistry` for key identity lookup, revocation, and policy/key matching
- `DurableReplayStore` backed by a sanitized replay record adapter
- unavailable replay adapter blocked result
- process restart simulation with shared replay adapter
- provider/live fail-closed blocks when resolver or registry is missing
- public sanitizer denylist coverage for signature, nonce, verifier, policy, and key identity fields

Safe contract hashes such as `approval_hash`, `state_hash`, `plan_hash`, `prompt_contract_hash`, and `content_hash` remain allowed as sanitized correlation evidence. Raw approval authorization fields and `signed_contract_hash` are not public output.

Not implemented:

- production cryptographic approval signing
- external identity provider lookup
- key rotation or production revocation service
- atomic disk/DB replay storage
- Solar Pro 3 live provider call
- DAACS live runtime execution

## Quantitative Result

| Metric | Value |
|---|---:|
| Pytest collected cases | 223 |
| Pytest passed cases | 223 |
| Regression delta vs AW-NEXT-12 baseline | +22 |
| Approval security unit tests | 7 |
| Provider boundary test cases | 61 |
| Runner provider registry tests | 76 |
| New resolver/registry/durable replay test cases | 22 |
| Direct approval security fixtures | 4 |
| Provider resolver/registry/durable fixtures | 9 |
| Live resolver/registry/durable fixtures | 9 |
| Policy resolver block fixtures | 5 |
| Empty resolver/registry fixtures | 4 |
| Revoked key identity fixtures | 2 |
| Policy/key mismatch fixtures | 3 |
| Missing resolver/registry fixtures | 4 |
| Durable replay adapter unavailable fixtures | 3 |
| Durable restart replay fixtures | 3 |
| Public sanitizer sensitive approval key coverage | 7 fields |
| Live LLM calls during eval | 0 |
| Live API calls during eval | 0 |
| Provider calls during eval | 0 |
| Provider imports during eval | 0 |
| Network calls during eval | 0 |
| Verifier secret value reads | 0 |
| Verifier key file reads | 0 |
| Solar Pro 3/DAACS live calls | 0 |

## Gates

| Gate | Result |
|---|---|
| unknown `policy_id` blocked | covered |
| missing policy resolver blocked | covered |
| missing key identity registry blocked | covered |
| revoked key identity blocked | covered |
| policy/key identity mismatch blocked | covered |
| durable replay adapter unavailable blocked | covered |
| durable replay survives process restart simulation | covered |
| fake provider/runtime not invoked on boundary failure | covered |
| public output excludes signature_id, signed_contract_hash, nonce, verifier/key/policy/key identity IDs | covered |
| Solar Pro 3/DAACS live call 0 유지 | covered |

## External Audit

Findings addressed:

- resolver/registry are fail-closed for provider/live admission when not explicitly wired
- empty resolver/registry configurations remain empty and block instead of falling back to fake local trust roots
- permissive custom verifier cannot bypass static policy and key identity checks
- durable replay adapter unavailability blocks before fake provider/runtime invocation
- public payload sanitizer now drops approval signature, nonce, verifier, policy, and key identity fields if they appear in public output

Residual risk:

- `DurableReplayStore` is a boundary skeleton. The in-memory adapter only simulates restart durability and is not atomic production storage.
- policy and key identity registries are local fixtures, not production trust roots.
- real Solar Pro 3 and DAACS live execution remain intentionally disabled.

## Claim Boundary

Allowed claim:

`AW-NEXT-13 added fail-closed resolver/registry/durable replay boundary skeletons and verified them with 223 local tests while keeping Solar Pro 3 and DAACS live calls at 0.`

Forbidden claim:

`AW-NEXT-13 implemented production approval infrastructure, production durable replay storage, real Solar Pro 3 approval, or real DAACS live execution.`

## Next Recommended Unit

```text
id: AW-NEXT-14
depends_on: AW-NEXT-13
scope: file-backed durable replay adapter fixture + atomic write contract skeleton
acceptance_tests:
  - replay adapter writes only sanitized nonce hashes
  - corrupted replay file blocks admission
  - partial write simulation blocks admission
  - path traversal replay store path blocked
  - Solar Pro 3/DAACS live call 0 유지
risk_level: high
rollback_plan: file-backed adapter 제거, AW-NEXT-13 in-memory adapter skeleton으로 복귀
```

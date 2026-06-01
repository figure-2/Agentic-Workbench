# ADR 0002: Live-Open Policy Gate

## Status

Accepted

## Date

2026-06-01

## Context

Agentic Workbench already has local fixture, dry-run, fake provider, fake live
runner, approval/replay, and read-model boundaries. The next risk is opening a
real provider or target runtime path just because a credential or a fake
admission path exists.

Credential availability is not an execution policy. Before Solar Pro 3 or the
DAACS target runtime can be connected, the project needs one explicit readiness
gate that records the controls required for a later live implementation unit.

## Decision

Add `AW-LIVE-00` as a fail-closed live-open policy gate.

The gate evaluates readiness for two future surfaces:

- `solar_provider`
- `daacs_target_runtime`

The gate requires all of these controls to be ready:

- approval policy
- replay persistence
- cost/quota guard
- timeout guard
- workspace sandbox
- write allowlist
- rollback plan
- secret redaction
- artifact sanitizer
- audit projection

The gate also requires all requested call/write/network counters to be explicit
zero. A passing result means only `eligible_for_separate_live_implementation`.
It does not grant execution permission and does not call provider or runtime
code.

## Rationale

The project is moving from local fixture/dry-run proof toward service-shaped
demo behavior. Without a live-open policy gate, later Solar Pro 3 or DAACS
runtime work could bypass cost, sandbox, rollback, and audit controls.

Keeping `allowed_to_execute=false` in `AW-LIVE-00` prevents this readiness
check from becoming an accidental runtime switch.

## Consequences

- Solar Pro 3 API key presence is represented only by the env key name
  `UPSTAGE_API_KEY`; the value is not read.
- DAACS target runtime readiness must not carry provider env key names.
- Unknown live surfaces are blocked.
- Any requested provider/runtime/network/write call count greater than zero is
  blocked.
- Later work may propose a separate implementation unit only after this gate
  reports eligibility.

## Rejected Alternatives

### Open the provider path because the env key exists

Rejected. A stored env key does not prove approval policy, replay durability,
cost guard, timeout guard, redaction, or audit readiness.

### Let fake admission APIs decide live readiness

Rejected. Fake admission proves approval/replay plumbing for local demo paths.
It is not a live-open control plane.

### Combine policy evaluation and execution in one module

Rejected. `AW-LIVE-00` must stay side-effect-free so it can be tested and
audited without opening external calls or runtime writes.

## Acceptance Criteria

- Unknown surface is blocked.
- Missing readiness controls are blocked.
- Solar provider readiness references only `UPSTAGE_API_KEY` as an env key
  name and never reads its value.
- DAACS target runtime readiness rejects provider env key names.
- Requested provider/runtime/network/write attempts are blocked.
- Complete readiness returns `eligible_for_separate_live_implementation` but
  `allowed_to_execute=false`.
- Public output has no raw authorization material, raw prompt, raw log, raw
  provider payload, raw runtime payload, or secret value.
- Solar Pro 3 calls remain 0.
- DAACS target runtime calls remain 0.

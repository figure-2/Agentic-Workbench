# Claim Boundary

## Conclusion

Agentic Workbench is a local/dev AI agent workflow harness prototype. It may claim contract, approval, dry-run, fake-boundary, and sanitizer work. It must not claim external-provider outcome, source-runtime outcome, hosted success, or production-grade security.

## Public Allowed

- Local/dev workflow harness prototype
- Idea-to-artifact contract pipeline
- Planning package, build spec, approval gate, dry-run plan, and verification report
- Side-effect-free dry-run planning
- Fake-only admission gates with external calls kept at 0 in current paths
- Optional SQLite-backed replay wiring for fake admission gates
- Canonical approval persistence before durable replay claim
- Sanitized fake admission API demo paths for provider/live approval persistence
- SQLite-backed fake admission API mode selected only through server-side config
- Sanitized evidence read-model API for local repository projections
- Optional fixture evidence persistence for local repository projections
- Repository-backed run/artifact read APIs for local projection rows
- SQLite-backed canonical run/artifact read APIs for local projection rows
- Composed canonical run and evidence read models when described as sanitized
  local read-model composition only
- Local service-shaped fixture/dry-run demo over public API projections
- Minimal Markdown/CLI run status surface over local fixture/dry-run projections
- Fail-closed live-open readiness policy gate with provider/runtime calls kept
  at 0 and execution permission not granted
- Static local UI shell over sanitized fixture/dry-run projections
- Disabled Solar Pro 3 provider adapter skeleton with fake/live path separation
  and provider calls kept at 0
- No-call Solar Pro 3 request/response contract fixtures with sanitized
  summary/hash projection and policy checks
- Sanitized provider envelope read model for no-call contract hashes, counts,
  and status
- Local no-call provider envelope admission service before disabled Solar
  adapter invocation
- Local dry-admission checklist for future provider test proposals, with
  execution permission closed
- Local manual provider test proposal gate that remains disabled by default
- Disabled local executor boundary for manual provider test proposals
- Blocked one-shot permission contract projection for a local manual provider
  test candidate
- Blocked local preflight audit bundle for a manual provider test candidate
- Blocked readiness decision record for a local manual provider test candidate
- Blocked review packet for local manual provider test policy/preflight/readiness hashes
- Hash-only review packet export/read-model for a local manual provider test candidate
- Final no-call handoff packet for local manual provider test evidence
- First live-call operator opt-in checklist bound to the handoff packet hash,
  with execution permission closed
- Sealed pre-execution packet over handoff, opt-in, cost/timeout/quota, and
  rollback/abort hashes, with execution permission closed
- No-call arming record over sealed packet, operator, expiry, rollback, and
  abort policy hashes, with execution permission closed
- No-call release proposal over arming record, operator, release window, and
  rollback/abort hashes, with execution permission closed
- No-call final release packet over release proposal, arming record, operator,
  release window, and rollback/abort hashes, with execution permission closed
- Sanitized public summaries and correlation hashes
- Fixture-based smoke tests and local regression tests

## Public Conditional

Use only with a scope qualifier such as `local`, `fixture-based`, `dry-run`, `fake-only`, or `current MVP`.

- approval gate
- replay guard
- provider boundary
- runner boundary
- verification report
- local test baseline

## Public Forbidden

- fully autonomous development guarantee
- production readiness
- security completion or certification
- external provider outcome as a current capability
- live runtime success
- generated app as a production output
- hosted deployment success
- code-generation success-rate guarantee
- productivity multiplier proof
- benchmark superiority claim
- production trust root, production verifier, or production replay infrastructure
- fake/dry-run result described as live execution
- source runtime described as directly integrated
- fake admission API demo described as external provider or target runtime outcome
- SQLite-backed fake admission API wiring described as hosted approval service or multi-host replay protection
- evidence read-model API described as execution, provider, target runtime, or generated app outcome
- fixture evidence persistence described as durable user approval, provider outcome, target runtime outcome, or generated app outcome
- evidence-backed run/artifact read API described as canonical run-session state, raw artifact storage, approval authority, provider outcome, target runtime outcome, or generated app outcome
- canonical run/artifact read API described as provider outcome, target runtime outcome, generated app outcome, hosted persistence, production database layer, or repository trust certification
- composed run/evidence read model described as live observability, production monitoring, provider outcome, target runtime outcome, or generated app delivery
- local service-shaped demo described as hosted service, live execution, generated app delivery, or production demo
- Markdown/CLI status surface described as web dashboard, hosted observability, live runtime monitor, or production UI
- live-open readiness policy described as provider integration, runtime
  integration, production execution permission, or external model quality proof
- static local UI shell described as hosted dashboard, production UI, live
  monitor, generated app delivery, provider outcome, or target runtime outcome
- disabled Solar Pro 3 adapter skeleton described as an external provider
  outcome, model-quality proof, SDK integration, or production provider path
- Solar Pro 3 contract fixture described as an external call, provider outcome,
  model-quality proof, live response parser, or production provider readiness
- provider envelope read model described as provider outcome, hosted
  observability, live response parser, or production provider readiness
- provider envelope admission service described as provider execution,
  model-quality proof, hosted provider service, or production provider readiness
- provider envelope API/read-model hook described as external provider
  behavior, hosted provider service, provider quality proof, or production
  provider readiness
- operator approval envelope described as production operator identity,
  external provider execution permission, hosted approval authority, or
  production provider readiness
- dry-admission checklist described as external provider behavior, execution
  permission, hosted approval authority, or production provider readiness
- manual provider test proposal gate described as external provider behavior,
  execution permission, hosted approval authority, or production provider
  readiness
- disabled manual provider test executor boundary described as external
  provider behavior, hosted execution, or production provider readiness
- one-shot permission contract described as external provider behavior,
  execution permission, hosted execution, or production provider readiness
- preflight audit bundle described as external provider behavior, execution
  permission, hosted execution, or production provider readiness
- readiness decision record described as external provider behavior, execution
  permission, hosted execution, or production provider readiness
- review packet described as external provider behavior, execution permission,
  hosted execution, or production provider readiness
- review packet export/read-model described as external provider behavior,
  execution permission, hosted execution, or production provider readiness
- handoff packet described as external provider behavior, execution permission,
  hosted execution, or production provider readiness
- operator opt-in checklist described as external provider behavior, execution
  permission, hosted execution, or production provider readiness
- sealed pre-execution packet described as external provider behavior,
  execution permission, hosted execution, or production provider readiness
- arming record described as external provider behavior, execution permission,
  hosted execution, or production provider readiness
- release proposal described as external provider behavior, execution
  permission, hosted execution, or production provider readiness
- final release packet described as external provider behavior, execution
  permission, hosted execution, or production provider readiness

## Public Artifact Rules

Public documents, README, evidence, portfolio exports, API examples, and reports must not include:

- secret, token, password, API key, DB URL, cookie, bearer token
- `.env` value
- raw payload
- raw prompt or prompt messages
- raw search result, private corpus, or raw provider response
- raw log, stack trace, raw event body
- raw file body or generated source body as evidence
- raw approval authorization fields
- PII-like values
- internal absolute path

Allowed replacements:

- sanitized summary
- normalized relative path
- aggregate metric count
- safe run id
- correlation hashes such as `approval_hash`, `state_hash`, `plan_hash`, `prompt_contract_hash`, `content_hash`, `replay_marker_hash`
- non-secret reference names such as `env_key_name`

## Acceptance Gates

| Gate | Purpose |
|---|---|
| Secret Redaction Gate | Logs, events, artifacts, and reports do not expose secret-like values |
| PII/Path Redaction Gate | PII-like values, DB URLs, bearer tokens, and internal paths are removed from public payloads |
| Evidence Boundary Gate | Raw evidence becomes sanitized summaries |
| Public Artifact Exposure Gate | Forbidden raw fields are removed from public artifacts |
| Path Boundary Gate | Artifact paths remain normalized and relative |
| Claim Copy Gate | Unsupported public claims are blocked by scan/review |
| No-Live-Call Gate | Current paths are not described as live-provider or live-runtime success |
| Non-Dummy Test Gate | Schema, adapter, redaction, pathing, approval, runner, and smoke tests remain executable |
| Provider Envelope Read Gate | No-call provider envelope evidence exposes hashes, counts, and status only |
| Provider Envelope Admission Gate | Disabled adapter path is reachable only after no-call envelope evidence is saved and read back |
| Provider Envelope API Hook Gate | Local API/demo precheck exposes status, hashes, and counts only |
| Operator Approval Envelope Gate | Provider precheck requires a local operator approval bound to a sanitized policy summary hash |
| Dry-Admission Checklist Gate | Provider precheck exposes manual conditions while keeping execution permission closed |
| Manual Proposal Gate | First provider test proposal requires exact proposal-hash approval and remains disabled |
| Disabled Executor Gate | Manual provider test executor remains blocked and exposes only status/reason/hash |
| Handoff Packet Gate | Manual provider test handoff packet remains blocked and exposes only status/reason/hash/count |
| Operator Opt-In Checklist Gate | Operator opt-in binds to the handoff packet hash but remains blocked and exposes only status/reason/hash/count |
| Sealed Pre-Execution Packet Gate | Sealed packet binds handoff, opt-in, policy, rollback, and abort hashes but remains execution-closed |
| Arming Record Gate | Arming record binds sealed packet, operator, expiry, rollback, and abort hashes but remains execution-closed |
| Release Proposal Gate | Release proposal binds arming record, operator, release window, and rollback hashes but remains execution-closed |
| Final Release Packet Gate | Final release packet binds release proposal, arming record, operator, release window, and rollback hashes but remains execution-closed |

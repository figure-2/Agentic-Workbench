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

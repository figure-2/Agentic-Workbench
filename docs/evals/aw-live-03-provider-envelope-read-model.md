# AW-LIVE-03 Provider Envelope Persistence and Read Model

## Conclusion

`AW-LIVE-03` adds sanitized provider envelope persistence and a public read
model for no-call Solar contract fixture evidence. The store keeps contract
hashes, field counts, status, and safe labels. The public read model returns a
narrower projection: hashes, counts, status, repository boundary, and zero-call
execution counters.

## Scope

- `ProviderEnvelopeRecord`
- `InMemoryProviderEnvelopeRepository`
- `SQLiteProviderEnvelopeStore`
- `SQLiteProviderEnvelopeRepository`
- `provider_envelope_record_from_contract_result`
- `provider_envelope_public_read_model`
- `provider_envelope_public_read_model_from_sqlite`
- unit tests for safe storage, read-model shape, corruption handling, and
  no-call guards

## Non-Scope

- Solar Pro 3 API call
- Upstage SDK import
- `.env` value read
- network call
- provider response parser
- provider quality evaluation
- hosted execution
- production provider readiness

## Acceptance Evidence

| Gate | Result |
|---|---|
| request contract hash stored | covered |
| response contract hash stored | covered |
| raw prompt/provider body/provider payload in DB rows | 0 |
| public read model field shape | hash/count/status only |
| corrupted SQLite store | blocked |
| unavailable SQLite store | blocked |
| wrong-schema SQLite store | blocked |
| escaping SQLite filename | blocked |
| env value reads | 0 |
| provider SDK imports | 0 |
| network calls | 0 |
| Solar Pro 3 API calls | 0 |
| forbidden public key findings | 0 |

## Measured Commands

```powershell
python -m pytest tests\unit\test_provider_envelope_store.py -q
python -m compileall packages apps tests examples
python -m pytest tests -q
.\scripts\verify.ps1
git diff --check
```

## Public Claim Boundary

Allowed:

```text
AW-LIVE-03 adds no-call provider envelope persistence and a sanitized public
read model for Solar contract fixture evidence.
```

Forbidden:

```text
AW-LIVE-03 calls Solar Pro 3, validates model output, proves provider quality,
parses provider responses, or opens production provider execution.
```

## External Audit

Finding: no blocker.

- Provider envelope rows store hashes, counts, status, and safe labels only.
- Public read model omits provider/model labels and timestamps, leaving
  hash/count/status evidence only.
- Corrupted, unavailable, wrong-schema, and escaping-path stores are blocked.
- No SDK import, env value read, network call, or external API call is present.

Residual risk:

- This is still persistence/read-model scaffolding. Future work must wire this
  evidence boundary into admission services before any provider adapter path is
  opened.

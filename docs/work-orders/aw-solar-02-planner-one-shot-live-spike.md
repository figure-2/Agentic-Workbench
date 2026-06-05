# AW-SOLAR-02 Planner One-Shot Spike

## Summary

```text
id: AW-SOLAR-02
depends_on:
  - AW-APP-01
  - AW-SOLAR-01
  - AW-LIVE-00
scope:
  Prepare a one-shot Solar planner spike path for the planning stage.
  The default product path remains the fixture planner.
  The spike path must be explicit, operator-approved, cost/timeout bounded,
  and documented against official Upstage/Solar references before any external
  request is allowed.
risk_level: high
rollback_plan:
  Remove the Solar spike selector, manual runbook, tests, and documentation.
  Keep the AW-MVP-01 fixture planner and AW-APP-01 preview path unchanged.
```

## Why This Comes Next

`AW-APP-01` makes the local service-shaped output visible to a reviewer. The
next portfolio gap is planner quality: the system should show that the planning
stage can be connected to a real model behind a controlled spike path, without
turning the default demo into an external dependency.

## Official References To Verify First

Before implementation, re-check official references and record the checked date
in the eval document:

- Upstage developer chat API documentation: <https://developers.upstage.ai/docs/apis/chat>
- Upstage Solar API/product guidance: <https://www.upstage.ai/blog/en/solar-pro-preview-the-most-intelligent-llm-on-a-single-gpu>
- Upstage Hugging Face organization/model listing: <https://huggingface.co/upstage/models>

If docs differ from existing assumptions, update the request envelope contract
before writing adapter code.

## Implementation Scope

### AW-SOLAR-02A: Provider Selection Boundary

Add an explicit planner selector:

- `fixture`: default, current deterministic planner
- `solar_spike_preflight`: validates request envelope and policy only
- `solar_spike_manual`: reserved for a manually approved one-shot run

Acceptance tests:

- Default `/api/v1/runs` and demo script still use fixture planner.
- No environment variable value is read in default or preflight mode.
- No SDK import, network call, or provider call occurs in tests.
- Public response includes planner mode/status/hash/count only.
- Raw prompt and raw provider body are not stored or returned.

### AW-SOLAR-02B: Request Envelope Contract

Create a sanitized planner request envelope from the existing run contract:

- `run_id`
- `prompt_contract_hash`
- `planning_request_hash`
- `model_family`
- `timeout_seconds`
- `output_budget`
- `cost_limit_label`
- `response_projection_schema_hash`

Acceptance tests:

- Missing timeout/cost/quota config blocks the spike path.
- Missing approval blocks the manual spike path.
- Request envelope stores hashes and config labels only.
- Raw prompt text is not persisted in repository rows.
- Public projection returns hash/status/reason/count only.

### AW-SOLAR-02C: Manual Spike Runbook

Add a runbook for a single manual planner call.

Acceptance tests:

- Runbook states default execution is closed.
- Runbook requires explicit operator approval.
- Runbook states abort criteria, timeout, cost boundary, rollback, and evidence
  capture rules.
- On failure, the instruction is to check official docs and request/response
  contract mismatch first, then retry only if the failure is transient and the
  one-shot boundary still allows it.
- No secret value, raw response body, or full prompt is copied into docs.

### AW-SOLAR-02D: Mocked Contract Test

Add a mocked adapter test that simulates a successful Solar-shaped response.

Acceptance tests:

- The mocked response can produce a sanitized planning summary.
- Response body is not stored.
- Response projection contains summary hash, section count, and status.
- Malformed response is blocked with sanitized reason.
- No external request occurs during the test.

## Quantitative Metrics To Record

Record these in `docs/metrics.md` and the eval document:

| Metric | Target |
|---|---:|
| Default planner mode | fixture |
| Solar spike modes added | 2 |
| Official references checked | >= 3 |
| Mocked adapter contract cases | >= 2 |
| Raw prompt persistence findings | 0 |
| Raw provider body persistence findings | 0 |
| Env value reads in automated tests | 0 |
| SDK imports in automated tests | 0 |
| Network calls in automated tests | 0 |
| Default demo regression failures | 0 |

## Out Of Scope

- Running Solar by default
- Running an external request in CI
- Adding a large frontend
- Replacing the fixture planner
- Claiming hosted behavior or generated app quality
- Persisting raw prompt text or raw provider responses

## Done Criteria

- Planner selector and envelope contracts are implemented.
- Default demo and AW-APP-01 preview still work without external access.
- Mocked Solar-shaped planner response is converted into sanitized planning
  evidence.
- Manual one-shot runbook exists, but actual external execution remains a
  separate operator action.
- Targeted tests and one final full test pass.

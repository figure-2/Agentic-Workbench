# AW-SOLAR-LIVE-01 One-Shot Planner Live Spike

## Scope

`AW-SOLAR-LIVE-01` adds an explicit, one-shot Solar planner live spike path.
The default `/api/v1/runs` planner remains fixture-based. The live path is
available only through an operator opt-in flag, reads only the configured
`UPSTAGE_API_KEY` environment value, performs at most one Upstage chat
completion attempt, and returns only hash/status/count evidence.

This does not open DAACS target runtime execution, generated app server start,
hosting, multi-call planning, live research/search, or raw provider body
storage.

## Official Reference Check

Checked on 2026-06-05.

| Source | Finding |
|---|---|
| Upstage Console Chat example, `https://console.upstage.ai/api-keys?api=chat` | The official Console example uses an OpenAI-compatible client with `base_url="https://api.upstage.ai/v1"` and `model="solar-pro3"`. |
| Upstage Console Chat with Reasoning example, `https://console.upstage.ai/api-keys?api=chat` | The same model is shown through `chat.completions.create` with `reasoning_effort="high"` available for reasoning mode. |
| Upstage Solar Pro 3 March 2026 blog, `https://www.upstage.ai/blog/en/solar-pro-3-0323` | Solar Pro 3 is described as an API-available Solar Pro update with the same API interface as Solar Pro 2. |

Implementation choice: use the OpenAI-compatible REST endpoint
`https://api.upstage.ai/v1/chat/completions` via Python standard library
`urllib.request`, not an SDK import. This keeps the dependency surface small and
lets tests inject a fake runner.

## Boundary Flow

```text
run_id + prompt_contract_hash
-> operator_live_opt_in
-> timeout/input/output/cost caps
-> env key presence check
-> private one-shot request body
-> Upstage chat completion attempt
-> sanitized response hash/count projection
```

Public projection fields are limited to status, reason, hashes, counts,
response section count, artifact hint count, and execution counters. Raw prompt
text, provider body, credential values, local root paths, and generated app
file bodies are not returned.

## Quantitative Results

| Metric | Value |
|---|---:|
| Representative live planner scenarios | 1 |
| Explicit operator opt-in | 1 |
| Provider call count in manual spike | 1 |
| Network call count in manual spike | 1 |
| Env value reads in manual spike | 1 |
| SDK imports in manual spike | 0 |
| Response projection count | 1 |
| Response status code | 200 |
| Response body bytes observed privately | 2300 |
| Response section count | 18 |
| Artifact hint count | 3 |
| DAACS target runtime calls | 0 |
| Server starts | 0 |
| Credential value exposure findings | 0 |
| Raw prompt/body exposure findings | 0 |
| Public local root path exposure findings | 0 |

## Verification

```powershell
python -m pytest tests\unit\test_solar_planner_live_spike.py -q --color=no
```

Result:

```text
4 passed
```

```powershell
python -m pytest tests\smoke\test_solar_planner_preflight.py -q --color=no
```

Result:

```text
6 passed
```

Blocked default CLI path:

```powershell
python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-solar-live-01-blocked --include-solar-planner-live-spike
```

Observed:

```text
status: passed
solar_live_spike_status: blocked
reason: operator_live_opt_in_missing
provider_calls: 0
network_calls: 0
credential_value_exposure_count: 0
```

Manual one-shot CLI path:

```powershell
python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-solar-live-01 --include-solar-planner-live-spike --allow-solar-planner-live-call
```

Observed:

```text
status: passed
solar_live_spike_status: projected
provider_calls: 1
network_calls: 1
env_value_reads: 1
response_projection_count: 1
target_runtime_calls: 0
server_start_calls: 0
credential_value_exposure_count: 0
raw_provider_body_returned_count: 0
raw_provider_body_stored_count: 0
```

## Comparison

| Variant | Status | Stage coverage | Provider calls | Env reads | Network calls | Target runtime calls |
|---|---|---:|---:|---:|---:|---:|
| `fixture_planner` | passed | 7/7 | 0 | 0 | 0 | 0 |
| `solar_live_one_shot_blocked` | blocked | fixture remains 7/7 | 0 | 0 | 0 | 0 |
| `solar_live_one_shot_projected` | projected | fixture remains 7/7 | 1 | 1 | 1 | 0 |

## Team Review

- Product: this is the first measured external planner call evidence and gives
  the portfolio a concrete provider integration signal without changing the
  default fixture demo.
- Architecture: the live spike is isolated in `packages.div_planner` and uses a
  runner injection seam, so API and tests can keep deterministic paths.
- Security: the key value and provider body remain private; public output uses
  hashes and counts only.
- Testing: automated tests cover blocked admission, missing credential,
  sanitized fake-runner projection, provider-error projection, API blocked path,
  and local demo blocked path.

## Remaining Work

The next step should compare the live planner projection against fixture
planning quality, then decide whether to let Solar output populate a draft
PlanningBlueprint/PRDPackage behind explicit review. DAACS runtime should remain
separate until the generated artifact verification/build path is ready to accept
provider-authored implementation briefs.

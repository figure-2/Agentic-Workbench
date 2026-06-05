# AW-SOLAR-02 Planner One-Shot Spike

## Scope

`AW-SOLAR-02` prepares a controlled Solar planner one-shot spike path without
opening external execution by default. The fixture planner remains the default
artifact-producing planner for `/api/v1/runs` and the local demo.

The new path adds:

- `solar_spike_preflight` planner mode
- `solar_spike_manual` planner mode
- hash-only planner spike envelope
- mocked Solar-shaped response projection
- optional local demo comparison

It does not read `UPSTAGE_API_KEY` values, import provider SDKs, call Solar,
open network sockets, or persist raw prompts/provider responses.

## Official Reference Check

Checked on 2026-06-04.

| Source | Relevant finding |
|---|---|
| Upstage Console Chat with Reasoning example | The official Console example uses an OpenAI-compatible Python client, `base_url="https://api.upstage.ai/v1"`, `model="solar-pro3"`, `reasoning_effort="high"`, and streaming support. |
| Upstage Solar Pro Preview blog | Upstage documents a Solar chat completions style endpoint and emphasizes model/API exploration through Console. |
| Upstage Hugging Face organization | Upstage publishes Solar model artifacts and tokenizers, including Solar Pro related listings. |

Interpretation: the project now records the expected Solar planner request
shape as a spike envelope, but automated tests still use mocked projections
only.

## Boundary Flow

```text
IdeaBrief
-> prompt_contract_hash
-> fixture planner path
-> AW-MVP-01 artifact chain
```

Optional spike comparison:

```text
run_id + prompt_contract_hash + ready policy
-> planner provider selector
-> solar_spike_preflight
-> planner_spike_envelope
-> mocked response projection
-> public hash/status/count summary
```

Manual spike mode:

```text
run_id + prompt_contract_hash + ready policy
-> solar_spike_manual
-> requires operator_approval_hash
-> still keeps one-shot execution permission false
```

## Quantitative Results

| Metric | Value |
|---|---:|
| Default planner mode | fixture |
| Solar spike modes added | 2 |
| Official references checked | 3 |
| Planner spike envelope count in demo | 1 |
| Mocked response projection count in demo | 1 |
| Demo comparison variants | 3 |
| Fixture stage coverage | 7/7 |
| Raw prompt persistence findings | 0 |
| Raw provider body persistence findings | 0 |
| Env value reads in automated tests | 0 |
| SDK imports in automated tests | 0 |
| Network calls in automated tests | 0 |
| Provider calls in automated tests | 0 |
| New unit tests | 4 |
| New smoke tests | 2 |

## Verification

```powershell
python -m pytest tests\unit\test_planner_provider_preflight.py tests\smoke\test_solar_planner_preflight.py -q
```

Result:

```text
15 passed
```

```powershell
python examples\demo-service-flow\run_local_demo.py --store-root .local\aw-solar-02-demo --include-solar-planner-spike
```

Observed signals:

```text
status: passed
solar_spike_status: mock_projected
solar_spike_mock_projection_count: 1
solar_spike_provider_calls: 0
solar_spike_network_calls: 0
```

Full regression:

```powershell
python -m pytest tests -q
```

Result:

```text
648 passed in 230.04s
```

## Comparison

| Variant | Status | Stage coverage | Provider calls | SDK imports | Env value reads | Network calls |
|---|---|---:|---:|---:|---:|---:|
| `fixture_planner` | passed | 7/7 | 0 | 0 | 0 | 0 |
| `solar_pro_3_disabled_preflight` | preflight_only | preflight-only | 0 | 0 | 0 | 0 |
| `solar_spike_preflight_mock` | mock_projected | fixture remains 7/7 | 0 | 0 | 0 | 0 |

## Claim Boundary

This is planner spike preparation and mocked response projection only. It does
not prove live Solar behavior, provider response quality, generated app
delivery, hosted behavior, or target runtime execution.

## Team Review

- Product: this closes the next portfolio gap by making the Solar planner path
  visible without changing the default fixture demo.
- Architecture: the selector/envelope design keeps planner provider concerns
  separate from DAACS runtime work.
- Security: raw prompt text, provider body, env values, SDK imports, and
  network calls remain outside automated execution.
- Testing: targeted tests cover fixture default, spike preflight, manual
  approval block, mock projection, API, and local demo comparison.

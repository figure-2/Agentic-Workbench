"""One-shot Solar Pro 3 planner live spike boundary.

The default planner path remains fixture-based. This module opens exactly one
operator-approved Upstage chat completion attempt and returns only sanitized
hash/count evidence. It does not store or return raw prompts, provider bodies,
or credential values.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
import re
from typing import Any, Callable, Protocol
import urllib.error
import urllib.request

from packages.core.exposure import sanitize_public_payload
from packages.core.live_open_policy import SOLAR_PRO_3_ENV_KEY_NAME
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash

from .provider_boundary import CONTRACT_HASH_PATTERN, SAFE_RUN_ID_PATTERN


SOLAR_PLANNER_LIVE_SPIKE_VERSION = "planner-provider-solar-live-spike-public-v1"
SOLAR_PLANNER_LIVE_SPIKE_MODE = "solar_live_one_shot"
SOLAR_PLANNER_LIVE_MODEL = "solar-pro3"
UPSTAGE_CHAT_COMPLETIONS_URL = "https://api.upstage.ai/v1/chat/completions"
DEFAULT_SOLAR_LIVE_TIMEOUT_SECONDS = 20
DEFAULT_SOLAR_LIVE_MAX_INPUT_CHARS = 1800
DEFAULT_SOLAR_LIVE_MAX_OUTPUT_TOKENS = 384
DEFAULT_SOLAR_LIVE_COST_LIMIT_LABEL = "one-shot-bounded"
SAFE_SUMMARY_PATTERN = re.compile(r"^[A-Za-z0-9가-힣 .,;:()/_+-]{0,280}$")


@dataclass(frozen=True, slots=True)
class SolarPlannerLiveSpikeRequest:
    """Operator-controlled live planner spike request."""

    run_id: str
    prompt_contract_hash: str
    operator_live_opt_in: bool = False
    env_key_name: str = SOLAR_PRO_3_ENV_KEY_NAME
    model: str = SOLAR_PLANNER_LIVE_MODEL
    request_timeout_seconds: int | None = None
    max_input_chars: int | None = None
    max_output_tokens: int | None = None
    max_live_api_calls: int | None = None
    cost_limit_label: str = DEFAULT_SOLAR_LIVE_COST_LIMIT_LABEL
    sanitized_idea_summary: str = "study group task collaboration app"
    endpoint_url: str = UPSTAGE_CHAT_COMPLETIONS_URL
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SolarPlannerHTTPResponse:
    """Private HTTP response envelope returned by the live call runner."""

    status_code: int
    body: bytes
    elapsed_ms: int = 0


class SolarPlannerLiveRunner(Protocol):
    """Callable used by tests to fake the live network operation."""

    def __call__(
        self,
        *,
        endpoint_url: str,
        request_body: JsonDict,
        credential_value: str,
        timeout_seconds: int,
    ) -> SolarPlannerHTTPResponse:
        """Perform one provider call and return the raw private response."""


class SolarPlannerLiveProviderError(RuntimeError):
    """Sanitized provider failure that carries no body or credential value."""

    def __init__(
        self,
        reason: str,
        *,
        status_code: int = 0,
        body_byte_count: int = 0,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code
        self.body_byte_count = body_byte_count


@dataclass(frozen=True, slots=True)
class SolarPlannerLiveSpikeResult:
    """Public-safe projection for the one-shot live planner spike."""

    projection_version: str
    run_id: str
    planner_provider_mode: str
    status: str
    reason: str
    request_contract_hash: str
    prompt_contract_hash: str
    model: str
    endpoint_host_hash: str
    response_projection: JsonDict
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("solar live spike projection must be a mapping")
        assert_public_projection_safe(payload)
        return payload


def _safe_run_id(run_id: str) -> str:
    if isinstance(run_id, str) and SAFE_RUN_ID_PATTERN.fullmatch(run_id):
        return run_id
    return "run-redacted"


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def _check(
    checks: list[JsonDict],
    failures: list[str],
    *,
    name: str,
    passed: bool,
    reason: str,
) -> None:
    checks.append({"name": name, "passed": bool(passed)})
    if not passed:
        failures.append(reason)


def _endpoint_host_hash(endpoint_url: str) -> str:
    host = "api.upstage.ai" if "api.upstage.ai" in endpoint_url else "custom"
    return stable_contract_hash({"endpoint_host": host})


def _sanitize_idea_summary(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return "study group task collaboration app"
    stripped = value.strip()[:280]
    if SAFE_SUMMARY_PATTERN.fullmatch(stripped):
        return stripped
    return "sanitized planner idea summary"


def _request_contract_hash(request: SolarPlannerLiveSpikeRequest) -> str:
    return stable_contract_hash(
        {
            "projection_version": SOLAR_PLANNER_LIVE_SPIKE_VERSION,
            "run_id": _safe_run_id(request.run_id),
            "prompt_contract_hash": request.prompt_contract_hash,
            "planner_provider_mode": SOLAR_PLANNER_LIVE_SPIKE_MODE,
            "model": request.model,
            "endpoint_host_hash": _endpoint_host_hash(request.endpoint_url),
            "timeout_seconds": request.request_timeout_seconds,
            "max_input_chars": request.max_input_chars,
            "max_output_tokens": request.max_output_tokens,
            "max_live_api_calls": request.max_live_api_calls,
            "cost_limit_label": request.cost_limit_label,
        }
    )


def _execution_boundary(
    *,
    env_value_reads: int = 0,
    provider_calls: int = 0,
    network_calls: int = 0,
    request_created: bool = False,
    response_projected: bool = False,
) -> JsonDict:
    return {
        "provider_calls": provider_calls,
        "solar_provider_calls": provider_calls,
        "live_api_calls": provider_calls,
        "live_llm_calls": provider_calls,
        "sdk_imports": 0,
        "env_key_value_reads": env_value_reads,
        "network_calls": network_calls,
        "subprocess_calls": 0,
        "filesystem_writes": 0,
        "target_runtime_calls": 0,
        "server_start_calls": 0,
        "request_contract_created": request_created,
        "response_projection_parsed": response_projected,
        "one_shot_execution_permission": request_created and provider_calls <= 1,
    }


def _claim_boundary(status: str) -> JsonDict:
    return {
        "scope": "one-shot planner provider spike evidence",
        "status": status,
        "fixture_planner_default": True,
        "provider_generated_blueprint": False,
        "provider_success_claim": False,
        "external_provider_outcome_claim": False,
        "target_runtime_outcome": False,
        "hosted_behavior_claim": False,
        "production_trust_claim": False,
    }


def _counts(
    *,
    status: str,
    check_count: int,
    failed_check_count: int,
    env_value_reads: int,
    provider_calls: int,
    request_created: bool,
    response_projected: bool,
    response_status_code: int = 0,
    response_body_byte_count: int = 0,
) -> JsonDict:
    return {
        "live_spike_count": 1,
        "check_count": check_count,
        "failed_check_count": failed_check_count,
        "operator_opt_in_count": 1 if request_created else 0,
        "request_contract_hash_count": 1,
        "request_body_created_count": 1 if request_created else 0,
        "provider_call_count": provider_calls,
        "solar_provider_call_count": provider_calls,
        "live_api_call_count": provider_calls,
        "network_call_count": provider_calls if provider_calls else 0,
        "env_value_read_count": env_value_reads,
        "sdk_import_count": 0,
        "credential_value_exposure_count": 0,
        "input_text_exposure_count": 0,
        "raw_provider_body_stored_count": 0,
        "raw_provider_body_returned_count": 0,
        "response_projection_count": 1 if response_projected else 0,
        "summary_hash_count": 1 if response_projected else 0,
        "artifact_hint_count": 0,
        "target_runtime_call_count": 0,
        "server_start_count": 0,
        "status_projected_count": 1 if status == "projected" else 0,
        "status_blocked_count": 1 if status == "blocked" else 0,
        "status_failed_count": 1 if status == "failed" else 0,
        "response_status_code": response_status_code,
        "response_body_byte_count": response_body_byte_count,
    }


def _blocked_result(
    request: SolarPlannerLiveSpikeRequest,
    *,
    checks: list[JsonDict],
    failures: list[str],
    env_value_reads: int = 0,
) -> SolarPlannerLiveSpikeResult:
    reason = failures[0] if failures else "solar_live_spike_blocked"
    failed_count = sum(1 for check in checks if not check["passed"])
    return SolarPlannerLiveSpikeResult(
        projection_version=SOLAR_PLANNER_LIVE_SPIKE_VERSION,
        run_id=_safe_run_id(request.run_id),
        planner_provider_mode=SOLAR_PLANNER_LIVE_SPIKE_MODE,
        status="blocked",
        reason=reason,
        request_contract_hash=_request_contract_hash(request),
        prompt_contract_hash=request.prompt_contract_hash,
        model=request.model,
        endpoint_host_hash=_endpoint_host_hash(request.endpoint_url),
        response_projection={},
        checks=checks,
        counts=_counts(
            status="blocked",
            check_count=len(checks),
            failed_check_count=failed_count,
            env_value_reads=env_value_reads,
            provider_calls=0,
            request_created=False,
            response_projected=False,
        ),
        execution_boundary=_execution_boundary(env_value_reads=env_value_reads),
        claim_boundary=_claim_boundary("blocked"),
    )


def _failed_result(
    request: SolarPlannerLiveSpikeRequest,
    *,
    checks: list[JsonDict],
    reason: str,
    status_code: int = 0,
    body_byte_count: int = 0,
) -> SolarPlannerLiveSpikeResult:
    return SolarPlannerLiveSpikeResult(
        projection_version=SOLAR_PLANNER_LIVE_SPIKE_VERSION,
        run_id=_safe_run_id(request.run_id),
        planner_provider_mode=SOLAR_PLANNER_LIVE_SPIKE_MODE,
        status="failed",
        reason=reason,
        request_contract_hash=_request_contract_hash(request),
        prompt_contract_hash=request.prompt_contract_hash,
        model=request.model,
        endpoint_host_hash=_endpoint_host_hash(request.endpoint_url),
        response_projection={},
        checks=checks,
        counts=_counts(
            status="failed",
            check_count=len(checks),
            failed_check_count=0,
            env_value_reads=1,
            provider_calls=1,
            request_created=True,
            response_projected=False,
            response_status_code=status_code,
            response_body_byte_count=body_byte_count,
        ),
        execution_boundary=_execution_boundary(
            env_value_reads=1,
            provider_calls=1,
            network_calls=1,
            request_created=True,
        ),
        claim_boundary=_claim_boundary("failed"),
    )


def _sanitized_planner_instruction(request: SolarPlannerLiveSpikeRequest) -> str:
    idea_summary = _sanitize_idea_summary(request.sanitized_idea_summary)
    instruction = (
        "Agentic Workbench one-shot planning spike.\n"
        "Return compact JSON with keys: planning_blueprint, prd_package, "
        "implementation_brief, acceptance_criteria.\n"
        f"run_id={_safe_run_id(request.run_id)}\n"
        f"prompt_contract_hash={request.prompt_contract_hash}\n"
        f"sanitized_idea_summary={idea_summary}\n"
        "Do not include secrets, raw prompt text, provider metadata, or file bodies."
    )
    max_chars = int(request.max_input_chars or 0)
    return instruction[:max_chars]


def _build_private_request_body(request: SolarPlannerLiveSpikeRequest) -> JsonDict:
    return {
        "model": request.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You produce concise planning artifacts for a local "
                    "workflow harness demo."
                ),
            },
            {"role": "user", "content": _sanitized_planner_instruction(request)},
        ],
        "stream": False,
        "temperature": 0.2,
        "max_tokens": int(request.max_output_tokens or 0),
    }


def _default_live_runner(
    *,
    endpoint_url: str,
    request_body: JsonDict,
    credential_value: str,
    timeout_seconds: int,
) -> SolarPlannerHTTPResponse:
    body = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    http_request = urllib.request.Request(
        endpoint_url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {credential_value}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(http_request, timeout=timeout_seconds) as response:
            response_body = response.read(1024 * 256)
            return SolarPlannerHTTPResponse(
                status_code=int(getattr(response, "status", 200)),
                body=response_body,
            )
    except urllib.error.HTTPError as exc:
        error_body = exc.read(1024 * 16)
        raise SolarPlannerLiveProviderError(
            "provider_http_error",
            status_code=int(exc.code),
            body_byte_count=len(error_body),
        ) from exc
    except urllib.error.URLError as exc:
        raise SolarPlannerLiveProviderError("provider_network_error") from exc
    except TimeoutError as exc:
        raise SolarPlannerLiveProviderError("provider_timeout") from exc


def _extract_content(response_body: bytes) -> str:
    try:
        payload = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SolarPlannerLiveProviderError(
            "provider_response_unusable",
            body_byte_count=len(response_body),
        ) from exc
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise SolarPlannerLiveProviderError(
            "provider_response_missing_choices",
            body_byte_count=len(response_body),
        )
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise SolarPlannerLiveProviderError(
            "provider_response_missing_content",
            body_byte_count=len(response_body),
        )
    return content.strip()


def _section_and_hint_counts(content: str) -> tuple[int, int]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        section_count = len([key for key, value in parsed.items() if value])
    else:
        section_count = len(
            [
                line
                for line in content.splitlines()
                if line.strip().startswith(("-", "*", "#")) or ":" in line
            ]
        )
    lowered = content.lower()
    hints = [
        "planning",
        "blueprint",
        "prd",
        "implementation",
        "acceptance",
        "artifact",
        "verification",
    ]
    artifact_hint_count = sum(1 for hint in hints if hint in lowered)
    return max(section_count, 1), artifact_hint_count


def _project_response(
    request: SolarPlannerLiveSpikeRequest,
    *,
    response: SolarPlannerHTTPResponse,
    content: str,
) -> JsonDict:
    section_count, artifact_hint_count = _section_and_hint_counts(content)
    summary_hash = stable_contract_hash(
        {
            "request_contract_hash": _request_contract_hash(request),
            "content": content,
        }
    )
    response_contract_hash = stable_contract_hash(
        {
            "projection_version": SOLAR_PLANNER_LIVE_SPIKE_VERSION,
            "request_contract_hash": _request_contract_hash(request),
            "summary_hash": summary_hash,
            "summary_section_count": section_count,
            "artifact_hint_count": artifact_hint_count,
        }
    )
    return {
        "response_kind": "sanitized_live_planner_summary_hash",
        "response_contract_hash": response_contract_hash,
        "summary_hash": summary_hash,
        "summary_section_count": section_count,
        "artifact_hint_count": artifact_hint_count,
        "source_body_included": False,
        "provider_body_included": False,
        "response_status_code": int(response.status_code),
        "response_elapsed_ms": int(response.elapsed_ms),
    }


def run_solar_planner_live_spike(
    request: SolarPlannerLiveSpikeRequest,
    *,
    credential_reader: Callable[[str], str | None] | None = None,
    live_runner: SolarPlannerLiveRunner | None = None,
) -> SolarPlannerLiveSpikeResult:
    """Run one explicit Solar planner spike and return public-safe evidence."""
    checks: list[JsonDict] = []
    failures: list[str] = []
    credential_reader = credential_reader or os.environ.get
    live_runner = live_runner or _default_live_runner

    _check(
        checks,
        failures,
        name="fixture_planner_remains_default",
        passed=True,
        reason="fixture_planner_default_unavailable",
    )
    _check(
        checks,
        failures,
        name="operator_live_opt_in_explicit",
        passed=request.operator_live_opt_in is True,
        reason="operator_live_opt_in_missing",
    )
    _check(
        checks,
        failures,
        name="run_id_safe",
        passed=isinstance(request.run_id, str)
        and SAFE_RUN_ID_PATTERN.fullmatch(request.run_id) is not None,
        reason="run_id_invalid",
    )
    _check(
        checks,
        failures,
        name="prompt_contract_hash_valid",
        passed=isinstance(request.prompt_contract_hash, str)
        and CONTRACT_HASH_PATTERN.fullmatch(request.prompt_contract_hash) is not None,
        reason="prompt_contract_hash_invalid",
    )
    _check(
        checks,
        failures,
        name="env_key_name_expected",
        passed=request.env_key_name == SOLAR_PRO_3_ENV_KEY_NAME,
        reason="env_key_name_invalid",
    )
    _check(
        checks,
        failures,
        name="model_supported",
        passed=request.model == SOLAR_PLANNER_LIVE_MODEL,
        reason="model_unsupported",
    )
    _check(
        checks,
        failures,
        name="timeout_configured",
        passed=_positive_int(request.request_timeout_seconds),
        reason="timeout_missing",
    )
    _check(
        checks,
        failures,
        name="input_size_cap_configured",
        passed=_positive_int(request.max_input_chars),
        reason="input_size_cap_missing",
    )
    _check(
        checks,
        failures,
        name="output_token_cap_configured",
        passed=_positive_int(request.max_output_tokens),
        reason="output_token_cap_missing",
    )
    _check(
        checks,
        failures,
        name="one_call_quota_configured",
        passed=request.max_live_api_calls == 1,
        reason="one_call_quota_missing",
    )
    _check(
        checks,
        failures,
        name="cost_limit_label_present",
        passed=isinstance(request.cost_limit_label, str)
        and bool(request.cost_limit_label.strip()),
        reason="cost_limit_label_missing",
    )
    if failures:
        return _blocked_result(request, checks=checks, failures=failures)

    credential_value = credential_reader(request.env_key_name)
    _check(
        checks,
        failures,
        name="credential_available",
        passed=isinstance(credential_value, str) and bool(credential_value.strip()),
        reason="credential_unavailable",
    )
    if failures or not credential_value:
        return _blocked_result(
            request,
            checks=checks,
            failures=failures,
            env_value_reads=1,
        )

    request_body = _build_private_request_body(request)
    request_body_bytes = len(json.dumps(request_body, ensure_ascii=False).encode("utf-8"))
    _check(
        checks,
        failures,
        name="request_body_under_input_cap",
        passed=request_body_bytes <= int(request.max_input_chars or 0),
        reason="request_body_input_cap_exceeded",
    )
    if failures:
        return _blocked_result(
            request,
            checks=checks,
            failures=failures,
            env_value_reads=1,
        )

    try:
        response = live_runner(
            endpoint_url=request.endpoint_url,
            request_body=request_body,
            credential_value=credential_value,
            timeout_seconds=int(request.request_timeout_seconds or 0),
        )
    except SolarPlannerLiveProviderError as exc:
        return _failed_result(
            request,
            checks=checks,
            reason=exc.reason,
            status_code=exc.status_code,
            body_byte_count=exc.body_byte_count,
        )

    try:
        content = _extract_content(response.body)
    except SolarPlannerLiveProviderError as exc:
        return _failed_result(
            request,
            checks=checks,
            reason=exc.reason,
            status_code=int(response.status_code),
            body_byte_count=exc.body_byte_count,
        )

    projection = _project_response(request, response=response, content=content)
    result = SolarPlannerLiveSpikeResult(
        projection_version=SOLAR_PLANNER_LIVE_SPIKE_VERSION,
        run_id=_safe_run_id(request.run_id),
        planner_provider_mode=SOLAR_PLANNER_LIVE_SPIKE_MODE,
        status="projected",
        reason="solar_live_spike_projected",
        request_contract_hash=_request_contract_hash(request),
        prompt_contract_hash=request.prompt_contract_hash,
        model=request.model,
        endpoint_host_hash=_endpoint_host_hash(request.endpoint_url),
        response_projection=projection,
        checks=checks,
        counts={
            **_counts(
                status="projected",
                check_count=len(checks),
                failed_check_count=0,
                env_value_reads=1,
                provider_calls=1,
                request_created=True,
                response_projected=True,
                response_status_code=int(response.status_code),
                response_body_byte_count=len(response.body),
            ),
            "artifact_hint_count": int(projection.get("artifact_hint_count", 0)),
        },
        execution_boundary=_execution_boundary(
            env_value_reads=1,
            provider_calls=1,
            network_calls=1,
            request_created=True,
            response_projected=True,
        ),
        claim_boundary=_claim_boundary("projected"),
    )
    return result


def solar_live_spike_request_from_payload(payload: dict[str, Any]) -> SolarPlannerLiveSpikeRequest:
    """Build a live spike request from API/demo payload."""
    return SolarPlannerLiveSpikeRequest(
        run_id=str(payload["run_id"]),
        prompt_contract_hash=str(payload["prompt_contract_hash"]),
        operator_live_opt_in=payload.get("operator_live_opt_in") is True,
        env_key_name=str(payload.get("env_key_name", SOLAR_PRO_3_ENV_KEY_NAME)),
        model=str(payload.get("model", SOLAR_PLANNER_LIVE_MODEL)),
        request_timeout_seconds=payload.get(
            "request_timeout_seconds",
            DEFAULT_SOLAR_LIVE_TIMEOUT_SECONDS,
        ),
        max_input_chars=payload.get(
            "max_input_chars",
            DEFAULT_SOLAR_LIVE_MAX_INPUT_CHARS,
        ),
        max_output_tokens=payload.get(
            "max_output_tokens",
            DEFAULT_SOLAR_LIVE_MAX_OUTPUT_TOKENS,
        ),
        max_live_api_calls=payload.get("max_live_api_calls", 1),
        cost_limit_label=str(
            payload.get("cost_limit_label", DEFAULT_SOLAR_LIVE_COST_LIMIT_LABEL)
        ),
        sanitized_idea_summary=str(
            payload.get("sanitized_idea_summary", "study group task collaboration app")
        ),
        endpoint_url=str(payload.get("endpoint_url", UPSTAGE_CHAT_COMPLETIONS_URL)),
        metadata={},
    )


__all__ = [
    "DEFAULT_SOLAR_LIVE_COST_LIMIT_LABEL",
    "DEFAULT_SOLAR_LIVE_MAX_INPUT_CHARS",
    "DEFAULT_SOLAR_LIVE_MAX_OUTPUT_TOKENS",
    "DEFAULT_SOLAR_LIVE_TIMEOUT_SECONDS",
    "SOLAR_PLANNER_LIVE_MODEL",
    "SOLAR_PLANNER_LIVE_SPIKE_MODE",
    "SOLAR_PLANNER_LIVE_SPIKE_VERSION",
    "UPSTAGE_CHAT_COMPLETIONS_URL",
    "SolarPlannerHTTPResponse",
    "SolarPlannerLiveProviderError",
    "SolarPlannerLiveRunner",
    "SolarPlannerLiveSpikeRequest",
    "SolarPlannerLiveSpikeResult",
    "run_solar_planner_live_spike",
    "solar_live_spike_request_from_payload",
]

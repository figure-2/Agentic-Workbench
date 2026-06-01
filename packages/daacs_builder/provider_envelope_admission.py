"""Provider envelope admission service for disabled live adapter paths.

This service verifies and persists no-call Solar contract envelope evidence
before a disabled live adapter can be invoked. It never reads env values,
imports provider SDKs, opens network sockets, or calls external APIs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from packages.core.exposure import sanitize_public_payload
from packages.core.schemas import JsonDict, stable_contract_hash

from .provider_boundary import (
    CONTRACT_HASH_PATTERN,
    SOLAR_PRO_3_MODEL,
    SOLAR_PRO_3_PROVIDER,
    ProviderRequest,
    ProviderResult,
    zero_provider_side_effect_metrics,
)
from .provider_envelope_store import (
    ProviderEnvelopeRepository,
    provider_envelope_public_read_model,
    provider_envelope_record_from_contract_result,
)
from .runner_provider import safe_public_run_id
from .solar_contracts import SOLAR_CONTRACT_VERSION, SolarContractFixtureResult


class ProviderEnvelopeAdapter(Protocol):
    """Minimal adapter shape used by the admission wrapper."""

    def invoke(self, request: ProviderRequest) -> ProviderResult:
        ...


@dataclass(frozen=True, slots=True)
class ProviderEnvelopeAdmissionResult:
    """Public-safe admission result for provider envelope evidence."""

    status: str
    run_id: str
    checks: list[JsonDict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    request_contract_hash: str = ""
    response_contract_hash: str = ""
    envelope_id: str = ""
    read_model: JsonDict = field(default_factory=dict)
    metrics: JsonDict = field(default_factory=dict)

    def to_dict(self) -> JsonDict:
        return sanitize_public_payload(asdict(self))


def _zero_metrics(extra: dict[str, Any] | None = None) -> JsonDict:
    return {
        **zero_provider_side_effect_metrics(),
        "provider_envelope_admission_service_present_count": 0,
        "provider_envelope_admission_persist_count": 0,
        "provider_envelope_admission_duplicate_count": 0,
        "provider_envelope_admission_read_model_count": 0,
        "provider_envelope_admission_hash_match_count": 0,
        "provider_envelope_admission_block_count": 0,
        "provider_envelope_adapter_invocation_count": 0,
        "provider_envelope_sdk_imports": 0,
        "provider_envelope_env_value_reads": 0,
        "provider_envelope_api_calls": 0,
        "provider_envelope_network_calls": 0,
        **(extra or {}),
    }


def _check(
    checks: list[JsonDict],
    failures: list[tuple[str, str]],
    *,
    name: str,
    passed: bool,
    message: str,
) -> None:
    checks.append({"name": name, "passed": bool(passed)})
    if not passed:
        failures.append((name, message))


def _hash_value(value: object) -> str:
    return value if isinstance(value, str) else ""


def _is_contract_hash(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


def _expected_response_contract_hash(response_projection: JsonDict) -> str:
    return stable_contract_hash(
        {
            "version": response_projection.get("version", ""),
            "run_id": response_projection.get("run_id", ""),
            "provider_name": response_projection.get("provider_name", SOLAR_PRO_3_PROVIDER),
            "model_name": response_projection.get("model_name", SOLAR_PRO_3_MODEL),
            "content_hash": response_projection.get("content_hash", ""),
        }
    )


def _blocked_admission_result(
    request: ProviderRequest,
    failures: list[tuple[str, str]],
    *,
    checks: list[JsonDict] | None = None,
    read_model: JsonDict | None = None,
    extra_metrics: dict[str, Any] | None = None,
) -> ProviderEnvelopeAdmissionResult:
    result_checks = list(checks or [])
    if failures:
        failure_name = failures[0][0]
        if not any(check.get("name") == failure_name for check in result_checks):
            result_checks.append({"name": failure_name, "passed": False})
    return ProviderEnvelopeAdmissionResult(
        status="blocked",
        run_id=safe_public_run_id(request.run_id),
        checks=result_checks
        or [{"name": "provider_envelope_admission_blocked", "passed": False}],
        errors=[message for _, message in failures] or ["provider envelope admission blocked."],
        read_model=read_model or {},
        metrics=_zero_metrics(
            {
                "provider_envelope_admission_service_present_count": 1,
                "provider_envelope_admission_block_count": 1,
                **(extra_metrics or {}),
            }
        ),
    )


class ProviderEnvelopeAdmissionService:
    """Persist and verify provider envelope evidence before adapter invocation."""

    def __init__(self, repository: ProviderEnvelopeRepository) -> None:
        self.repository = repository

    def admit(
        self,
        request: ProviderRequest,
        contract_result: SolarContractFixtureResult,
    ) -> ProviderEnvelopeAdmissionResult:
        checks: list[JsonDict] = []
        failures: list[tuple[str, str]] = []
        request_contract = dict(contract_result.request_contract)
        response_projection = dict(contract_result.response_projection)

        _check(
            checks,
            failures,
            name="provider_envelope_contract_projected",
            passed=contract_result.status == "projected_fixture"
            and bool(request_contract)
            and bool(response_projection),
            message="provider envelope admission requires a projected no-call contract fixture.",
        )
        if failures:
            return _blocked_admission_result(request, failures, checks=checks)

        self._validate_contract_shape(
            request=request,
            request_contract=request_contract,
            response_projection=response_projection,
            checks=checks,
            failures=failures,
        )
        if failures:
            return _blocked_admission_result(request, failures, checks=checks)

        try:
            record = provider_envelope_record_from_contract_result(contract_result)
        except Exception:
            return _blocked_admission_result(
                request,
                [
                    (
                        "provider_envelope_record_buildable",
                        "provider envelope record could not be built.",
                    )
                ],
                checks=checks,
            )

        duplicate = False
        try:
            self.repository.save(record)
            persist_count = 1
        except ValueError as exc:
            if "duplicate" not in str(exc).lower() and "conflict" not in str(exc).lower():
                return _blocked_admission_result(
                    request,
                    [
                        (
                            "provider_envelope_persistence_available",
                            "provider envelope persistence service is unavailable.",
                        )
                    ],
                    checks=checks,
                )
            duplicate = True
            persist_count = 0
        except Exception:
            return _blocked_admission_result(
                request,
                [
                    (
                        "provider_envelope_persistence_available",
                        "provider envelope persistence service is unavailable.",
                    )
                ],
                checks=checks,
            )

        read_model = provider_envelope_public_read_model(self.repository, run_id=request.run_id)
        if read_model.get("status") != "available":
            return _blocked_admission_result(
                request,
                [
                    (
                        "provider_envelope_read_model_available",
                        "provider envelope read model is unavailable.",
                    )
                ],
                checks=checks,
                read_model=read_model,
                extra_metrics={
                    "provider_envelope_admission_persist_count": persist_count,
                    "provider_envelope_admission_duplicate_count": 1 if duplicate else 0,
                    "provider_envelope_admission_read_model_count": 1,
                },
            )

        matching = [
            envelope
            for envelope in read_model.get("provider_envelopes", [])
            if envelope.get("request_contract_hash") == record.request_contract_hash
            and envelope.get("response_contract_hash") == record.response_contract_hash
        ]
        _check(
            checks,
            failures,
            name="provider_envelope_hashes_visible_in_read_model",
            passed=bool(matching),
            message="provider envelope read model does not contain matching request/response hashes.",
        )
        if failures:
            return _blocked_admission_result(
                request,
                failures,
                checks=checks,
                read_model=read_model,
                extra_metrics={
                    "provider_envelope_admission_persist_count": persist_count,
                    "provider_envelope_admission_duplicate_count": 1 if duplicate else 0,
                    "provider_envelope_admission_read_model_count": 1,
                },
            )

        return ProviderEnvelopeAdmissionResult(
            status="admitted",
            run_id=safe_public_run_id(request.run_id),
            checks=checks,
            errors=[],
            request_contract_hash=record.request_contract_hash,
            response_contract_hash=record.response_contract_hash,
            envelope_id=record.envelope_id,
            read_model=read_model,
            metrics=_zero_metrics(
                {
                    "provider_envelope_admission_service_present_count": 1,
                    "provider_envelope_admission_persist_count": persist_count,
                    "provider_envelope_admission_duplicate_count": 1 if duplicate else 0,
                    "provider_envelope_admission_read_model_count": 1,
                    "provider_envelope_admission_hash_match_count": 1,
                }
            ),
        )

    def _validate_contract_shape(
        self,
        *,
        request: ProviderRequest,
        request_contract: JsonDict,
        response_projection: JsonDict,
        checks: list[JsonDict],
        failures: list[tuple[str, str]],
    ) -> None:
        _check(
            checks,
            failures,
            name="provider_envelope_request_contract_hash_valid",
            passed=_is_contract_hash(request_contract.get("request_contract_hash"))
            and self._request_hash_matches_explicit_expectation(
                request=request,
                request_contract=request_contract,
            ),
            message="request contract hash does not match the no-call request fixture.",
        )
        _check(
            checks,
            failures,
            name="provider_envelope_response_contract_hash_valid",
            passed=_is_contract_hash(response_projection.get("response_contract_hash"))
            and response_projection.get("response_contract_hash")
            == _expected_response_contract_hash(response_projection),
            message="response contract hash does not match the no-call response projection.",
        )
        _check(
            checks,
            failures,
            name="provider_envelope_contract_version",
            passed=request_contract.get("version") == SOLAR_CONTRACT_VERSION
            and response_projection.get("version") == SOLAR_CONTRACT_VERSION,
            message="provider envelope contract version is unsupported.",
        )
        _check(
            checks,
            failures,
            name="provider_envelope_request_matches_invocation",
            passed=request_contract.get("run_id") == safe_public_run_id(request.run_id)
            and request_contract.get("provider_name") == request.provider_name
            and request_contract.get("model_name") == request.model_name
            and request_contract.get("mode") == request.mode
            and request_contract.get("prompt_contract_hash") == request.prompt_contract_hash,
            message="provider envelope request contract does not match the adapter invocation.",
        )
        _check(
            checks,
            failures,
            name="provider_envelope_response_matches_request",
            passed=response_projection.get("run_id") == request_contract.get("run_id")
            and response_projection.get("provider_name") == request_contract.get("provider_name")
            and response_projection.get("model_name") == request_contract.get("model_name")
            and _is_contract_hash(response_projection.get("content_hash")),
            message="provider envelope response projection does not match the request contract.",
        )
        _check(
            checks,
            failures,
            name="provider_envelope_request_response_hash_pair_present",
            passed=bool(_hash_value(request_contract.get("request_contract_hash")))
            and bool(_hash_value(response_projection.get("response_contract_hash"))),
            message="provider envelope requires request and response contract hashes.",
        )

    def _request_hash_matches_explicit_expectation(
        self,
        *,
        request: ProviderRequest,
        request_contract: JsonDict,
    ) -> bool:
        expected = request.metadata.get("expected_request_contract_hash")
        if expected is None:
            return True
        return request_contract.get("request_contract_hash") == expected


def invoke_adapter_after_provider_envelope_admission(
    *,
    adapter: ProviderEnvelopeAdapter,
    request: ProviderRequest,
    contract_result: SolarContractFixtureResult,
    admission_service: ProviderEnvelopeAdmissionService | None,
) -> ProviderResult:
    """Invoke a disabled adapter only after provider envelope evidence passes."""
    if admission_service is None:
        return _blocked_provider_result(
            request,
            [
                (
                    "provider_envelope_admission_service_present",
                    "provider envelope admission service is required before adapter invocation.",
                )
            ],
            checks=[],
            metrics=_zero_metrics({"provider_envelope_admission_block_count": 1}),
        )

    admission = admission_service.admit(request, contract_result)
    if admission.status != "admitted":
        return _blocked_provider_result(
            request,
            [
                (
                    "provider_envelope_admission_passed",
                    "provider envelope admission did not pass.",
                )
            ],
            checks=admission.checks,
            metrics=admission.metrics,
        )

    try:
        result = adapter.invoke(request)
    except Exception:
        return _blocked_provider_result(
            request,
            [
                (
                    "provider_envelope_adapter_available",
                    "provider adapter is unavailable after envelope admission.",
                )
            ],
            checks=admission.checks,
            metrics=admission.metrics,
        )

    result.checks = [
        {"name": "provider_envelope_admission_passed", "passed": True},
        *admission.checks,
        *result.checks,
    ]
    result.metrics.update(admission.metrics)
    result.metrics["provider_envelope_adapter_invocation_count"] = 1
    result.audit_events = [
        {
            "event": "provider_envelope_admitted",
            "run_id": safe_public_run_id(request.run_id),
            "envelope_id": admission.envelope_id,
            "request_contract_hash": admission.request_contract_hash,
            "response_contract_hash": admission.response_contract_hash,
        },
        *result.audit_events,
    ]
    return result


def _blocked_provider_result(
    request: ProviderRequest,
    failures: list[tuple[str, str]],
    *,
    checks: list[JsonDict],
    metrics: JsonDict,
) -> ProviderResult:
    reason = failures[0][0] if failures else "provider_envelope_admission_blocked"
    return ProviderResult(
        run_id=safe_public_run_id(request.run_id),
        provider_name=request.provider_name,
        model_name=request.model_name,
        status="blocked",
        checks=checks or [{"name": reason, "passed": False}],
        errors=[message for _, message in failures] or ["provider envelope admission blocked."],
        output_contract={},
        metrics={
            **_zero_metrics(),
            **metrics,
            "provider_envelope_adapter_invocation_count": 0,
        },
        audit_events=[
            {
                "event": "provider_envelope_admission_blocked",
                "run_id": safe_public_run_id(request.run_id),
                "failed_gate": reason,
            }
        ],
    )


__all__ = [
    "ProviderEnvelopeAdmissionResult",
    "ProviderEnvelopeAdmissionService",
    "invoke_adapter_after_provider_envelope_admission",
]

"""Explicit browser runtime setup boundary for local preview screenshots.

This boundary may run local Playwright setup commands only after a separate
operator opt-in is present. Public output stays hash/status/count-only and
never returns command output, browser errors, local paths, provider payloads,
environment values, or credentials.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import subprocess
import sys
from time import monotonic
from typing import Protocol

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys, sanitize_public_payload
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash

from .runner_provider import is_safe_run_id, safe_public_run_id
from .target_runtime_local_preview_attempt import (
    BROWSER_RUNTIME_PREFLIGHT_VERSION,
    BrowserRuntimePreflightResult,
    BrowserRuntimeProbe,
    PlaywrightBrowserRuntimeProbe,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_VERSION = (
    "target-runtime-browser-setup-attempt-public-v1"
)
TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE = "target_runtime_browser_setup_attempt"
BROWSER_RUNTIME_SETUP_COMMAND_LABELS = (
    "install-playwright-python-package",
    "install-playwright-chromium-browser",
)
BROWSER_RUNTIME_SETUP_OFFICIAL_DOCS = (
    "https://playwright.dev/python/docs/browsers",
    "https://playwright.dev/docs/screenshots",
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeBrowserSetupAttemptRequest:
    """Request to set up browser runtime for local preview screenshots."""

    run_id: str
    browser_runtime_preflight_hash: str
    browser_runtime_preflight_projection: JsonDict = field(default_factory=dict)
    mode: str = TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE
    operator_opt_in: bool = False
    allow_browser_runtime_setup: bool = False
    setup_timeout_seconds: int = 180
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BrowserRuntimeSetupCommandOutcome:
    """Sanitized local browser setup command result."""

    label: str
    attempted: bool
    exit_code: int | None
    timed_out: bool
    output_hash: str
    output_byte_count: int
    duration_ms: int
    reason: str

    def to_public_record(self, *, order: int) -> JsonDict:
        return {
            "order": order,
            "label": self.label,
            "attempted": self.attempted,
            "exit_code": self.exit_code,
            "exit_code_hash": stable_contract_hash(self.exit_code),
            "timed_out": self.timed_out,
            "output_hash": self.output_hash,
            "output_byte_count": self.output_byte_count,
            "duration_ms": self.duration_ms,
            "reason": self.reason,
            "raw_output_returned": False,
            "argv_returned": False,
            "root_path_returned": False,
            "env_value_returned": False,
        }


class BrowserRuntimeSetupCommandRunner(Protocol):
    """Runner contract for explicit local browser runtime setup."""

    def run(
        self,
        *,
        label: str,
        argv: tuple[str, ...],
        cwd: Path,
        timeout_seconds: int,
    ) -> BrowserRuntimeSetupCommandOutcome:
        """Run a local setup command and return sanitized evidence."""


class SubprocessBrowserRuntimeSetupCommandRunner:
    """Run Playwright setup commands without exposing outputs or local paths."""

    def run(
        self,
        *,
        label: str,
        argv: tuple[str, ...],
        cwd: Path,
        timeout_seconds: int,
    ) -> BrowserRuntimeSetupCommandOutcome:
        started = monotonic()
        try:
            completed = subprocess.run(
                list(argv),
                cwd=cwd,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=max(1, int(timeout_seconds)),
                check=False,
            )
            output = completed.stdout or ""
            duration_ms = int((monotonic() - started) * 1000)
            return BrowserRuntimeSetupCommandOutcome(
                label=label,
                attempted=True,
                exit_code=completed.returncode,
                timed_out=False,
                output_hash=stable_contract_hash(output),
                output_byte_count=len(output.encode("utf-8", errors="replace")),
                duration_ms=duration_ms,
                reason="browser_runtime_setup_command_completed"
                if completed.returncode == 0
                else "browser_runtime_setup_command_failed",
            )
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            duration_ms = int((monotonic() - started) * 1000)
            return BrowserRuntimeSetupCommandOutcome(
                label=label,
                attempted=True,
                exit_code=None,
                timed_out=True,
                output_hash=stable_contract_hash(output),
                output_byte_count=len(output.encode("utf-8", errors="replace")),
                duration_ms=duration_ms,
                reason="browser_runtime_setup_command_timeout",
            )
        except FileNotFoundError:
            duration_ms = int((monotonic() - started) * 1000)
            return BrowserRuntimeSetupCommandOutcome(
                label=label,
                attempted=True,
                exit_code=None,
                timed_out=False,
                output_hash=stable_contract_hash(""),
                output_byte_count=0,
                duration_ms=duration_ms,
                reason="browser_runtime_setup_command_missing",
            )


@dataclass(frozen=True, slots=True)
class TargetRuntimeBrowserSetupAttemptResult:
    """Public-safe browser runtime setup attempt projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    setup_attempted: bool
    operator_opt_in_present: bool
    browser_runtime_setup_allowed: bool
    browser_runtime_preflight_hash: str
    browser_runtime_setup_attempt_hash: str
    command_records: list[JsonDict]
    browser_runtime_preflight: JsonDict
    post_setup_browser_runtime_preflight: JsonDict
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    repository_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("browser setup attempt projection must be a mapping")
        assert_public_projection_safe(payload)
        return payload


def _is_hash(value: object) -> bool:
    return isinstance(value, str) and bool(CONTRACT_HASH_PATTERN.fullmatch(value))


def _preflight_hash_matches(projection: JsonDict, expected_hash: str) -> bool:
    return _is_hash(expected_hash) and stable_contract_hash(projection) == expected_hash


def _official_doc_hashes() -> list[str]:
    return [stable_contract_hash(url) for url in BROWSER_RUNTIME_SETUP_OFFICIAL_DOCS]


def _planned_setup_command_specs() -> tuple[tuple[str, tuple[str, ...]], ...]:
    return (
        (
            "install-playwright-python-package",
            (sys.executable, "-m", "pip", "install", "playwright"),
        ),
        (
            "install-playwright-chromium-browser",
            (sys.executable, "-m", "playwright", "install", "chromium"),
        ),
    )


def _blocked_command_records() -> list[JsonDict]:
    records: list[JsonDict] = []
    for order, (label, argv) in enumerate(_planned_setup_command_specs(), start=1):
        records.append(
            {
                "order": order,
                "label": label,
                "attempted": False,
                "argv_hash": stable_contract_hash(tuple(argv)),
                "exit_code": None,
                "exit_code_hash": stable_contract_hash(None),
                "timed_out": False,
                "output_hash": stable_contract_hash(""),
                "output_byte_count": 0,
                "duration_ms": 0,
                "reason": "browser_runtime_setup_not_attempted",
                "raw_output_returned": False,
                "argv_returned": False,
                "root_path_returned": False,
                "env_value_returned": False,
            }
        )
    return records


def _check(name: str, passed: bool, reason: str) -> JsonDict:
    return {"name": name, "passed": passed, "reason": reason}


def _counts(
    *,
    command_records: list[JsonDict],
    checks: list[JsonDict],
    operator_opt_in: bool,
    allow_browser_runtime_setup: bool,
    preflight_record: JsonDict,
    post_setup_preflight_record: JsonDict,
) -> JsonDict:
    command_attempt_count = sum(
        1 for record in command_records if record.get("attempted") is True
    )
    return {
        "browser_runtime_setup_attempt_scenario_count": 1,
        "check_count": len(checks),
        "passed_check_count": sum(1 for check in checks if check.get("passed") is True),
        "failed_check_count": sum(1 for check in checks if check.get("passed") is not True),
        "operator_opt_in_present_count": 1 if operator_opt_in else 0,
        "browser_runtime_setup_allowed_count": 1 if allow_browser_runtime_setup else 0,
        "planned_setup_command_label_count": len(BROWSER_RUNTIME_SETUP_COMMAND_LABELS),
        "planned_setup_command_hash_count": len(BROWSER_RUNTIME_SETUP_COMMAND_LABELS),
        "setup_command_record_count": len(command_records),
        "setup_command_attempt_count": command_attempt_count,
        "setup_command_pass_count": sum(
            1 for record in command_records if record.get("exit_code") == 0
        ),
        "setup_command_failure_count": sum(
            1
            for record in command_records
            if record.get("attempted") is True and record.get("exit_code") != 0
        ),
        "setup_command_timeout_count": sum(
            1 for record in command_records if record.get("timed_out") is True
        ),
        "default_setup_command_execution_count": 0
        if not operator_opt_in or not allow_browser_runtime_setup
        else command_attempt_count,
        "explicit_setup_opt_in_count": 1
        if operator_opt_in and allow_browser_runtime_setup
        else 0,
        "browser_runtime_preflight_count": 1 if preflight_record else 0,
        "browser_runtime_available_before_setup_count": 1
        if preflight_record.get("available") is True
        else 0,
        "post_setup_browser_runtime_preflight_count": 1
        if post_setup_preflight_record
        else 0,
        "browser_runtime_available_after_setup_count": 1
        if post_setup_preflight_record.get("available") is True
        else 0,
        "official_doc_label_count": len(BROWSER_RUNTIME_SETUP_OFFICIAL_DOCS),
        "official_doc_hash_count": len(BROWSER_RUNTIME_SETUP_OFFICIAL_DOCS),
        "raw_output_public_return_count": 0,
        "argv_public_return_count": 0,
        "browser_error_public_return_count": 0,
        "local_root_path_return_count": 0,
        "env_value_return_count": 0,
        "provider_call_count": 0,
        "solar_live_call_count": 0,
        "daacs_target_runtime_call_count": 0,
    }


def _execution_boundary(
    *,
    command_records: list[JsonDict],
    operator_opt_in: bool,
    allow_browser_runtime_setup: bool,
) -> JsonDict:
    attempted = sum(1 for record in command_records if record.get("attempted") is True)
    return {
        "runner": "browser_runtime_setup_attempt",
        "default_setup_command_execution_count": 0
        if not operator_opt_in or not allow_browser_runtime_setup
        else attempted,
        "setup_command_attempt_count": attempted,
        "local_process_calls": attempted,
        "package_install_calls": 1
        if any(
            record.get("attempted") is True
            and record.get("label") == "install-playwright-python-package"
            for record in command_records
        )
        else 0,
        "browser_binary_install_calls": 1
        if any(
            record.get("attempted") is True
            and record.get("label") == "install-playwright-chromium-browser"
            for record in command_records
        )
        else 0,
        "provider_calls": 0,
        "solar_live_calls": 0,
        "daacs_target_runtime_calls": 0,
        "raw_command_output_returned": False,
        "argv_returned": False,
        "env_value_read_count": 0,
        "external_network_possible_when_attempted": attempted > 0,
    }


def _repository_boundary() -> JsonDict:
    return {
        "projection_only": True,
        "raw_command_output_stored": False,
        "raw_browser_error_stored": False,
        "local_root_path_returned": False,
        "env_value_returned": False,
        "provider_payload_stored": False,
    }


def _claim_boundary(
    *,
    status: str,
    preflight_record: JsonDict,
    post_setup_preflight_record: JsonDict,
) -> JsonDict:
    public_claims = {
        "scope": "explicit local browser runtime setup attempt",
        "status": status,
        "browser_runtime_available_before_setup": (
            preflight_record.get("available") is True
        ),
        "browser_runtime_available_after_setup": (
            post_setup_preflight_record.get("available") is True
        ),
        "screenshot_verification_claim": False,
        "hosted_success_claim": False,
        "production_success_claim": False,
        "provider_success_claim": False,
        "daacs_runtime_success_claim": False,
    }
    return {
        **public_claims,
        "forbidden_claim_findings": find_forbidden_claims(
            json.dumps(public_claims, ensure_ascii=True, sort_keys=True)
        ),
    }


class TargetRuntimeBrowserSetupAttemptService:
    """Create sanitized browser runtime setup attempt evidence."""

    def __init__(
        self,
        *,
        command_runner: BrowserRuntimeSetupCommandRunner | None = None,
        browser_runtime_probe: BrowserRuntimeProbe | None = None,
    ) -> None:
        self._command_runner = (
            command_runner or SubprocessBrowserRuntimeSetupCommandRunner()
        )
        self._browser_runtime_probe = (
            browser_runtime_probe or PlaywrightBrowserRuntimeProbe()
        )

    def create_attempt(
        self,
        request: TargetRuntimeBrowserSetupAttemptRequest,
    ) -> TargetRuntimeBrowserSetupAttemptResult:
        if not is_safe_run_id(request.run_id):
            raise ValueError("unsafe run_id")

        provided_preflight = bool(request.browser_runtime_preflight_projection)
        preflight = sanitize_public_payload(request.browser_runtime_preflight_projection)
        if not isinstance(preflight, dict):
            raise ValueError("browser runtime preflight projection must be a mapping")
        if not provided_preflight:
            preflight = self._browser_runtime_probe.probe().to_public_record()
        effective_preflight_hash = (
            request.browser_runtime_preflight_hash
            if provided_preflight
            else stable_contract_hash(preflight)
        )

        checks: list[JsonDict] = [
            _check(
                "browser_setup_attempt_mode_valid",
                request.mode == TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE,
                "browser_setup_attempt_mode_valid"
                if request.mode == TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE
                else "browser_setup_attempt_mode_invalid",
            ),
            _check(
                "browser_runtime_preflight_projection_version",
                preflight.get("projection_version") == BROWSER_RUNTIME_PREFLIGHT_VERSION,
                "browser_runtime_preflight_projection_version_valid"
                if preflight.get("projection_version") == BROWSER_RUNTIME_PREFLIGHT_VERSION
                else "browser_runtime_preflight_projection_version_invalid",
            ),
            _check(
                "browser_runtime_preflight_hash_matches",
                _preflight_hash_matches(preflight, effective_preflight_hash),
                "browser_runtime_preflight_hash_matches"
                if _preflight_hash_matches(preflight, effective_preflight_hash)
                else "browser_runtime_preflight_hash_mismatch",
            ),
        ]

        if any(check["passed"] is not True for check in checks):
            return self._result(
                request=request,
                status="blocked",
                reason="browser_runtime_setup_preflight_invalid",
                command_records=_blocked_command_records(),
                preflight_record=preflight,
                effective_preflight_hash=effective_preflight_hash,
                post_setup_preflight_record={},
                checks=checks,
            )

        if preflight.get("available") is True:
            checks.append(
                _check(
                    "browser_runtime_already_available",
                    True,
                    "browser_runtime_already_available",
                )
            )
            return self._result(
                request=request,
                status="passed",
                reason="browser_runtime_already_available",
                command_records=_blocked_command_records(),
                preflight_record=preflight,
                effective_preflight_hash=effective_preflight_hash,
                post_setup_preflight_record=preflight,
                checks=checks,
            )

        if not request.operator_opt_in or not request.allow_browser_runtime_setup:
            checks.extend(
                [
                    _check(
                        "browser_runtime_setup_operator_opt_in_present",
                        request.operator_opt_in,
                        "browser_runtime_setup_operator_opt_in_present"
                        if request.operator_opt_in
                        else "browser_runtime_setup_opt_in_required",
                    ),
                    _check(
                        "browser_runtime_setup_allowed",
                        request.allow_browser_runtime_setup,
                        "browser_runtime_setup_allowed"
                        if request.allow_browser_runtime_setup
                        else "browser_runtime_setup_flag_required",
                    ),
                ]
            )
            return self._result(
                request=request,
                status="blocked",
                reason="browser_runtime_setup_opt_in_required",
                command_records=_blocked_command_records(),
                preflight_record=preflight,
                effective_preflight_hash=effective_preflight_hash,
                post_setup_preflight_record={},
                checks=checks,
            )

        records: list[JsonDict] = []
        for order, (label, argv) in enumerate(_planned_setup_command_specs(), start=1):
            outcome = self._command_runner.run(
                label=label,
                argv=argv,
                cwd=Path.cwd(),
                timeout_seconds=request.setup_timeout_seconds,
            )
            record = outcome.to_public_record(order=order)
            record["argv_hash"] = stable_contract_hash(tuple(argv))
            records.append(record)
            if outcome.exit_code != 0 or outcome.timed_out:
                break

        post_setup = self._browser_runtime_probe.probe().to_public_record()
        command_success = len(records) == len(BROWSER_RUNTIME_SETUP_COMMAND_LABELS) and all(
            record.get("exit_code") == 0 for record in records
        )
        runtime_available = post_setup.get("available") is True
        checks.extend(
            [
                _check(
                    "browser_runtime_setup_operator_opt_in_present",
                    True,
                    "browser_runtime_setup_operator_opt_in_present",
                ),
                _check(
                    "browser_runtime_setup_allowed",
                    True,
                    "browser_runtime_setup_allowed",
                ),
                _check(
                    "browser_runtime_setup_commands_passed",
                    command_success,
                    "browser_runtime_setup_commands_passed"
                    if command_success
                    else "browser_runtime_setup_command_failed",
                ),
                _check(
                    "post_setup_browser_runtime_available",
                    runtime_available,
                    "post_setup_browser_runtime_available"
                    if runtime_available
                    else "post_setup_browser_runtime_unavailable",
                ),
            ]
        )
        return self._result(
            request=request,
            status="passed" if command_success and runtime_available else "environment_blocked",
            reason="browser_runtime_setup_verified"
            if command_success and runtime_available
            else "browser_runtime_setup_incomplete",
            command_records=records,
            preflight_record=preflight,
            effective_preflight_hash=effective_preflight_hash,
            post_setup_preflight_record=post_setup,
            checks=checks,
        )

    def _result(
        self,
        *,
        request: TargetRuntimeBrowserSetupAttemptRequest,
        status: str,
        reason: str,
        command_records: list[JsonDict],
        preflight_record: JsonDict,
        effective_preflight_hash: str,
        post_setup_preflight_record: JsonDict,
        checks: list[JsonDict],
    ) -> TargetRuntimeBrowserSetupAttemptResult:
        payload_to_hash = {
            "version": TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_VERSION,
            "run_id": safe_public_run_id(request.run_id),
            "status": status,
            "reason": reason,
            "browser_runtime_preflight_hash": effective_preflight_hash,
            "command_records": command_records,
            "post_setup_browser_runtime_preflight": post_setup_preflight_record,
        }
        counts = _counts(
            command_records=command_records,
            checks=checks,
            operator_opt_in=request.operator_opt_in,
            allow_browser_runtime_setup=request.allow_browser_runtime_setup,
            preflight_record=preflight_record,
            post_setup_preflight_record=post_setup_preflight_record,
        )
        result = TargetRuntimeBrowserSetupAttemptResult(
            projection_version=TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_VERSION,
            run_id=safe_public_run_id(request.run_id),
            mode=request.mode,
            status=status,
            reason=reason,
            setup_attempted=any(
                record.get("attempted") is True for record in command_records
            ),
            operator_opt_in_present=request.operator_opt_in,
            browser_runtime_setup_allowed=request.allow_browser_runtime_setup,
            browser_runtime_preflight_hash=effective_preflight_hash,
            browser_runtime_setup_attempt_hash=stable_contract_hash(payload_to_hash),
            command_records=command_records,
            browser_runtime_preflight=preflight_record,
            post_setup_browser_runtime_preflight=post_setup_preflight_record,
            checks=checks,
            counts=counts,
            execution_boundary=_execution_boundary(
                command_records=command_records,
                operator_opt_in=request.operator_opt_in,
                allow_browser_runtime_setup=request.allow_browser_runtime_setup,
            ),
            repository_boundary=_repository_boundary(),
            claim_boundary=_claim_boundary(
                status=status,
                preflight_record=preflight_record,
                post_setup_preflight_record=post_setup_preflight_record,
            ),
        )
        data = result.to_dict()
        findings = find_forbidden_public_keys(data)
        if findings:
            raise ValueError(f"forbidden public setup projection keys: {findings}")
        return result


def default_target_runtime_browser_setup_attempt_service() -> (
    TargetRuntimeBrowserSetupAttemptService
):
    return TargetRuntimeBrowserSetupAttemptService()


def create_target_runtime_browser_setup_attempt(
    *,
    request: TargetRuntimeBrowserSetupAttemptRequest,
    service: TargetRuntimeBrowserSetupAttemptService | None = None,
    command_runner: BrowserRuntimeSetupCommandRunner | None = None,
    browser_runtime_probe: BrowserRuntimeProbe | None = None,
) -> TargetRuntimeBrowserSetupAttemptResult:
    selected_service = service or TargetRuntimeBrowserSetupAttemptService(
        command_runner=command_runner,
        browser_runtime_probe=browser_runtime_probe,
    )
    return selected_service.create_attempt(request)


__all__ = [
    "BROWSER_RUNTIME_SETUP_COMMAND_LABELS",
    "BROWSER_RUNTIME_SETUP_OFFICIAL_DOCS",
    "BrowserRuntimeSetupCommandOutcome",
    "BrowserRuntimeSetupCommandRunner",
    "SubprocessBrowserRuntimeSetupCommandRunner",
    "TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_MODE",
    "TARGET_RUNTIME_BROWSER_SETUP_ATTEMPT_VERSION",
    "TargetRuntimeBrowserSetupAttemptRequest",
    "TargetRuntimeBrowserSetupAttemptResult",
    "TargetRuntimeBrowserSetupAttemptService",
    "create_target_runtime_browser_setup_attempt",
    "default_target_runtime_browser_setup_attempt_service",
]

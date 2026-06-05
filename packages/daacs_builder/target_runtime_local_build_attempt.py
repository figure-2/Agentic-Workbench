"""Explicit local fixture app build attempt boundary.

This boundary is the first DAACS-side portfolio path that may execute local
package manager/build commands. It only runs inside the generated run-scoped
fixture app workspace after AW-BUILD-03 preflight and a separate opt-in flag.
It never calls Solar Pro 3, external providers, a hosted server, or the DAACS
target runtime.
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
from packages.core.pathing import PathBoundaryError, resolve_within_root
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash

from .runner_provider import is_safe_run_id, safe_public_run_id
from .target_runtime_local_build_preflight import (
    TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION = (
    "target-runtime-local-build-attempt-public-v1"
)
TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE = "target_runtime_local_build_attempt"
LOCAL_BUILD_ATTEMPT_COMMAND_LABELS = ("npm install", "npm run build")


@dataclass(frozen=True, slots=True)
class TargetRuntimeLocalBuildAttemptRequest:
    """Request to attempt a local fixture app package install/build."""

    run_id: str
    local_build_preflight_hash: str
    local_build_preflight_projection: JsonDict = field(default_factory=dict)
    workspace_root: str | Path | None = None
    mode: str = TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE
    operator_opt_in: bool = False
    allow_local_command_execution: bool = False
    install_timeout_seconds: int = 180
    build_timeout_seconds: int = 180
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LocalBuildCommandOutcome:
    """Sanitized local package/build command result."""

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
            "root_path_returned": False,
        }


class LocalBuildCommandRunner(Protocol):
    """Runner contract used by tests and the real local package/build path."""

    def run(
        self,
        *,
        label: str,
        argv: tuple[str, ...],
        cwd: Path,
        timeout_seconds: int,
    ) -> LocalBuildCommandOutcome:
        """Run a local command and return sanitized evidence."""


class SubprocessLocalBuildCommandRunner:
    """Run npm commands without exposing local paths or output bodies."""

    def run(
        self,
        *,
        label: str,
        argv: tuple[str, ...],
        cwd: Path,
        timeout_seconds: int,
    ) -> LocalBuildCommandOutcome:
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
            return LocalBuildCommandOutcome(
                label=label,
                attempted=True,
                exit_code=completed.returncode,
                timed_out=False,
                output_hash=stable_contract_hash(output),
                output_byte_count=len(output.encode("utf-8", errors="replace")),
                duration_ms=duration_ms,
                reason="local_command_completed"
                if completed.returncode == 0
                else "local_command_failed",
            )
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            duration_ms = int((monotonic() - started) * 1000)
            return LocalBuildCommandOutcome(
                label=label,
                attempted=True,
                exit_code=None,
                timed_out=True,
                output_hash=stable_contract_hash(output),
                output_byte_count=len(output.encode("utf-8", errors="replace")),
                duration_ms=duration_ms,
                reason="local_command_timeout",
            )
        except FileNotFoundError:
            duration_ms = int((monotonic() - started) * 1000)
            return LocalBuildCommandOutcome(
                label=label,
                attempted=True,
                exit_code=None,
                timed_out=False,
                output_hash=stable_contract_hash(""),
                output_byte_count=0,
                duration_ms=duration_ms,
                reason="local_package_manager_unavailable",
            )


@dataclass(frozen=True, slots=True)
class TargetRuntimeLocalBuildAttemptResult:
    """Public-safe local build attempt projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    local_build_attempted: bool
    local_build_opt_in_present: bool
    local_command_execution_allowed: bool
    local_build_preflight_hash: str
    local_build_preflight_projection_hash: str
    local_build_attempt_hash: str
    command_results: list[JsonDict]
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    repository_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("local build attempt must be a mapping")
        _assert_projection_safe(payload)
        return payload


def _npm_executable() -> str:
    return "npm.cmd" if sys.platform.startswith("win") else "npm"


def _is_contract_hash(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


def _assert_projection_safe(value: JsonDict) -> None:
    public = sanitize_public_payload(value)
    if not isinstance(public, dict):
        raise ValueError("local build attempt must be a mapping")
    if find_forbidden_public_keys(public):
        raise ValueError("local build attempt contains forbidden keys")
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError("local build attempt contains forbidden claims")
    assert_public_projection_safe(public)


def _check(
    checks: list[JsonDict],
    failures: list[str],
    *,
    name: str,
    passed: bool,
    reason: str,
) -> None:
    checks.append({"name": name, "passed": bool(passed), "reason": "" if passed else reason})
    if not passed:
        failures.append(reason)


def _projection_hash(projection: JsonDict) -> str:
    sanitized = sanitize_public_payload(projection)
    if not isinstance(sanitized, dict):
        return ""
    _assert_projection_safe(sanitized)
    return stable_contract_hash(sanitized)


def _app_dir(*, workspace_root: Path, run_id: str) -> Path:
    return resolve_within_root(
        workspace_root,
        f"runs/{safe_public_run_id(run_id)}/generated-app",
    )


def _repository_boundary(*, configured: bool) -> JsonDict:
    return {
        "local_build_attempt_backend": "local" if configured else "unconfigured",
        "root_path_returned": False,
        "raw_row_returned": False,
        "file_content_returned": False,
        "command_output_returned": False,
        "dependency_value_returned": False,
    }


def _claim_boundary(
    *,
    status: str,
    attempted: bool,
    build_attempted: bool,
) -> JsonDict:
    return {
        "scope": "explicit local fixture app build attempt only",
        "local_fixture_build_attempt_recorded": attempted,
        "local_fixture_build_succeeded": status == "passed",
        "package_install_executed": attempted,
        "build_executed": build_attempted,
        "server_started": False,
        "target_runtime_outcome": False,
        "external_provider_outcome": False,
        "hosted_behavior": False,
        "production_success_claim": False,
    }


def _execution_boundary(
    *,
    command_records: list[JsonDict],
    package_install_attempt_count: int,
    build_attempt_count: int,
    package_manager_network_attempt_count: int,
) -> JsonDict:
    command_attempt_count = sum(1 for record in command_records if record.get("attempted"))
    return {
        "target_runtime_calls": 0,
        "provider_calls": 0,
        "live_api_calls": 0,
        "sdk_imports": 0,
        "env_key_value_reads": 0,
        "subprocess_calls": command_attempt_count,
        "network_calls": package_manager_network_attempt_count,
        "package_manager_network_attempts": package_manager_network_attempt_count,
        "package_install_calls": package_install_attempt_count,
        "build_calls": build_attempt_count,
        "server_start_calls": 0,
        "execution_permission_count": 1 if command_attempt_count else 0,
        "local_build_attempt_only": True,
        "command_output_body_public_return_count": 0,
        "generated_file_content_public_return_count": 0,
        "local_root_path_public_return_count": 0,
    }


def _counts(
    *,
    checks: list[JsonDict],
    command_records: list[JsonDict],
    local_build_attempted: bool,
    operator_opt_in: bool,
    local_command_execution_allowed: bool,
    package_install_attempt_count: int,
    build_attempt_count: int,
    package_manager_network_attempt_count: int,
    status: str,
) -> JsonDict:
    return {
        "local_build_attempt_scenario_count": 1 if local_build_attempted else 0,
        "check_count": len(checks),
        "passed_check_count": sum(1 for check in checks if check.get("passed") is True),
        "failed_check_count": sum(1 for check in checks if check.get("passed") is not True),
        "command_result_count": len(command_records),
        "command_attempt_count": sum(
            1 for record in command_records if record.get("attempted") is True
        ),
        "successful_command_count": sum(
            1 for record in command_records if record.get("exit_code") == 0
        ),
        "failed_command_count": sum(
            1
            for record in command_records
            if record.get("attempted") is True and record.get("exit_code") != 0
        ),
        "command_output_hash_count": sum(
            1 for record in command_records if _is_contract_hash(record.get("output_hash"))
        ),
        "operator_opt_in_present_count": 1 if operator_opt_in else 0,
        "local_command_execution_allowed_count": (
            1 if local_command_execution_allowed else 0
        ),
        "package_install_attempt_count": package_install_attempt_count,
        "build_attempt_count": build_attempt_count,
        "server_start_attempt_count": 0,
        "package_manager_network_attempt_count": package_manager_network_attempt_count,
        "local_build_pass_count": 1 if status == "passed" else 0,
        "raw_output_public_return_count": 0,
        "file_content_public_return_count": 0,
        "local_root_path_return_count": 0,
        "dependency_value_return_count": 0,
        "target_runtime_call_count": 0,
        "provider_call_count": 0,
        "sdk_import_count": 0,
        "env_value_read_count": 0,
        "subprocess_call_count": sum(
            1 for record in command_records if record.get("attempted") is True
        ),
        "network_call_count": package_manager_network_attempt_count,
        "package_install_call_count": package_install_attempt_count,
        "build_call_count": build_attempt_count,
        "server_start_call_count": 0,
        "execution_permission_count": (
            1 if sum(1 for record in command_records if record.get("attempted")) else 0
        ),
    }


def _result(
    *,
    request: TargetRuntimeLocalBuildAttemptRequest,
    status: str,
    reason: str,
    checks: list[JsonDict],
    preflight_projection_hash: str,
    configured: bool,
    command_records: list[JsonDict],
    package_install_attempt_count: int = 0,
    build_attempt_count: int = 0,
    package_manager_network_attempt_count: int = 0,
) -> TargetRuntimeLocalBuildAttemptResult:
    local_build_attempted = bool(command_records)
    claim_boundary = _claim_boundary(
        status=status,
        attempted=local_build_attempted,
        build_attempted=build_attempt_count > 0,
    )
    payload_to_hash = {
        "projection_version": TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION,
        "run_id": safe_public_run_id(request.run_id),
        "mode": request.mode,
        "status": status,
        "reason": reason,
        "local_build_attempted": local_build_attempted,
        "local_build_opt_in_present": request.operator_opt_in,
        "local_command_execution_allowed": request.allow_local_command_execution,
        "local_build_preflight_hash": request.local_build_preflight_hash,
        "local_build_preflight_projection_hash": preflight_projection_hash,
        "command_results": command_records,
        "claim_boundary": claim_boundary,
    }
    return TargetRuntimeLocalBuildAttemptResult(
        projection_version=TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION,
        run_id=safe_public_run_id(request.run_id),
        mode=request.mode,
        status=status,
        reason=reason,
        local_build_attempted=local_build_attempted,
        local_build_opt_in_present=request.operator_opt_in,
        local_command_execution_allowed=request.allow_local_command_execution,
        local_build_preflight_hash=request.local_build_preflight_hash,
        local_build_preflight_projection_hash=preflight_projection_hash,
        local_build_attempt_hash=stable_contract_hash(payload_to_hash),
        command_results=command_records,
        checks=checks,
        counts=_counts(
            checks=checks,
            command_records=command_records,
            local_build_attempted=local_build_attempted,
            operator_opt_in=request.operator_opt_in,
            local_command_execution_allowed=request.allow_local_command_execution,
            package_install_attempt_count=package_install_attempt_count,
            build_attempt_count=build_attempt_count,
            package_manager_network_attempt_count=package_manager_network_attempt_count,
            status=status,
        ),
        execution_boundary=_execution_boundary(
            command_records=command_records,
            package_install_attempt_count=package_install_attempt_count,
            build_attempt_count=build_attempt_count,
            package_manager_network_attempt_count=package_manager_network_attempt_count,
        ),
        repository_boundary=_repository_boundary(configured=configured),
        claim_boundary=claim_boundary,
    )


class TargetRuntimeLocalBuildAttemptService:
    """Attempt package install/build after explicit preflight and opt-in."""

    def __init__(
        self,
        *,
        command_runner: LocalBuildCommandRunner | None = None,
    ) -> None:
        self._command_runner = command_runner or SubprocessLocalBuildCommandRunner()

    def create_attempt(
        self,
        request: TargetRuntimeLocalBuildAttemptRequest,
    ) -> TargetRuntimeLocalBuildAttemptResult:
        preflight_projection = (
            request.local_build_preflight_projection
            if isinstance(request.local_build_preflight_projection, dict)
            else {}
        )
        preflight_projection_hash = (
            _projection_hash(preflight_projection) if preflight_projection else ""
        )
        workspace_root = Path(request.workspace_root) if request.workspace_root else None
        configured = workspace_root is not None
        checks: list[JsonDict] = []
        failures: list[str] = []

        _check(
            checks,
            failures,
            name="local_build_attempt_mode_valid",
            passed=request.mode == TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE,
            reason="local_build_attempt_mode_invalid",
        )
        _check(
            checks,
            failures,
            name="run_id_safe",
            passed=is_safe_run_id(request.run_id),
            reason="run_id_invalid",
        )
        _check(
            checks,
            failures,
            name="local_build_preflight_hash_valid",
            passed=_is_contract_hash(request.local_build_preflight_hash),
            reason="local_build_preflight_hash_missing_or_invalid",
        )
        _check(
            checks,
            failures,
            name="local_build_preflight_projection_present",
            passed=bool(preflight_projection),
            reason="local_build_preflight_projection_missing",
        )
        _check(
            checks,
            failures,
            name="local_build_preflight_projection_version",
            passed=preflight_projection.get("projection_version")
            == TARGET_RUNTIME_LOCAL_BUILD_PREFLIGHT_VERSION,
            reason="local_build_preflight_projection_version_invalid",
        )
        _check(
            checks,
            failures,
            name="local_build_preflight_projection_passed",
            passed=preflight_projection.get("status") == "passed"
            and preflight_projection.get("local_build_eligible") is True,
            reason="local_build_preflight_projection_status_invalid",
        )
        _check(
            checks,
            failures,
            name="local_build_preflight_run_matches",
            passed=preflight_projection.get("run_id") == safe_public_run_id(request.run_id),
            reason="local_build_preflight_run_mismatch",
        )
        _check(
            checks,
            failures,
            name="local_build_preflight_hash_matches_projection",
            passed=request.local_build_preflight_hash
            == preflight_projection.get("local_build_preflight_hash"),
            reason="local_build_preflight_hash_mismatch",
        )
        _check(
            checks,
            failures,
            name="restricted_workspace_root_configured",
            passed=configured,
            reason="restricted_workspace_root_unconfigured",
        )

        if failures:
            return _result(
                request=request,
                status="blocked",
                reason=failures[0],
                checks=checks,
                preflight_projection_hash=preflight_projection_hash,
                configured=configured,
                command_records=[],
            )

        if not request.operator_opt_in or not request.allow_local_command_execution:
            blocked_checks = [
                *checks,
                {
                    "name": "local_build_attempt_operator_opt_in_present",
                    "passed": request.operator_opt_in,
                    "reason": ""
                    if request.operator_opt_in
                    else "local_build_attempt_opt_in_required",
                },
                {
                    "name": "local_command_execution_allowed",
                    "passed": request.allow_local_command_execution,
                    "reason": ""
                    if request.allow_local_command_execution
                    else "local_command_execution_flag_required",
                },
            ]
            return _result(
                request=request,
                status="blocked",
                reason="local_build_attempt_opt_in_required",
                checks=blocked_checks,
                preflight_projection_hash=preflight_projection_hash,
                configured=configured,
                command_records=[],
            )

        assert workspace_root is not None
        try:
            app_dir = _app_dir(workspace_root=workspace_root, run_id=request.run_id)
        except PathBoundaryError:
            return _result(
                request=request,
                status="blocked",
                reason="local_build_attempt_path_traversal",
                checks=[
                    *checks,
                    {
                        "name": "local_build_attempt_workspace_path_safe",
                        "passed": False,
                        "reason": "local_build_attempt_path_traversal",
                    },
                ],
                preflight_projection_hash=preflight_projection_hash,
                configured=configured,
                command_records=[],
            )
        if not app_dir.exists() or not app_dir.is_dir():
            return _result(
                request=request,
                status="blocked",
                reason="local_build_attempt_workspace_missing",
                checks=[
                    *checks,
                    {
                        "name": "local_build_attempt_workspace_exists",
                        "passed": False,
                        "reason": "local_build_attempt_workspace_missing",
                    },
                ],
                preflight_projection_hash=preflight_projection_hash,
                configured=configured,
                command_records=[],
            )
        if not (app_dir / "package.json").is_file():
            return _result(
                request=request,
                status="blocked",
                reason="local_build_attempt_package_json_missing",
                checks=[
                    *checks,
                    {
                        "name": "local_build_attempt_package_json_exists",
                        "passed": False,
                        "reason": "local_build_attempt_package_json_missing",
                    },
                ],
                preflight_projection_hash=preflight_projection_hash,
                configured=configured,
                command_records=[],
            )

        npm = _npm_executable()
        command_records: list[JsonDict] = []
        install_outcome = self._command_runner.run(
            label="npm install",
            argv=(npm, "install", "--no-audit", "--no-fund"),
            cwd=app_dir,
            timeout_seconds=request.install_timeout_seconds,
        )
        command_records.append(install_outcome.to_public_record(order=1))
        package_install_attempt_count = 1
        package_manager_network_attempt_count = 1

        if (
            install_outcome.reason == "local_package_manager_unavailable"
            or install_outcome.timed_out
        ):
            status = "environment_blocked"
            reason = install_outcome.reason
            build_attempt_count = 0
        elif install_outcome.exit_code != 0:
            status = "failed"
            reason = "local_package_install_failed"
            build_attempt_count = 0
        else:
            build_outcome = self._command_runner.run(
                label="npm run build",
                argv=(npm, "run", "build"),
                cwd=app_dir,
                timeout_seconds=request.build_timeout_seconds,
            )
            command_records.append(build_outcome.to_public_record(order=2))
            build_attempt_count = 1
            if build_outcome.timed_out:
                status = "environment_blocked"
                reason = "local_build_command_timeout"
            elif build_outcome.exit_code == 0:
                status = "passed"
                reason = "local_fixture_app_build_passed"
            else:
                status = "failed"
                reason = "local_fixture_app_build_failed"

        return _result(
            request=request,
            status=status,
            reason=reason,
            checks=[
                *checks,
                {
                    "name": "local_build_attempt_operator_opt_in_present",
                    "passed": True,
                    "reason": "",
                },
                {
                    "name": "local_command_execution_allowed",
                    "passed": True,
                    "reason": "",
                },
                {
                    "name": "local_build_attempt_recorded",
                    "passed": bool(command_records),
                    "reason": "" if command_records else "local_build_attempt_not_recorded",
                },
            ],
            preflight_projection_hash=preflight_projection_hash,
            configured=configured,
            command_records=command_records,
            package_install_attempt_count=package_install_attempt_count,
            build_attempt_count=build_attempt_count,
            package_manager_network_attempt_count=package_manager_network_attempt_count,
        )


def default_target_runtime_local_build_attempt_service() -> (
    TargetRuntimeLocalBuildAttemptService
):
    return TargetRuntimeLocalBuildAttemptService()


def create_target_runtime_local_build_attempt(
    *,
    request: TargetRuntimeLocalBuildAttemptRequest,
    service: TargetRuntimeLocalBuildAttemptService | None = None,
    command_runner: LocalBuildCommandRunner | None = None,
) -> TargetRuntimeLocalBuildAttemptResult:
    selected_service = service or TargetRuntimeLocalBuildAttemptService(
        command_runner=command_runner
    )
    return selected_service.create_attempt(request)


__all__ = [
    "LOCAL_BUILD_ATTEMPT_COMMAND_LABELS",
    "TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_MODE",
    "TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION",
    "LocalBuildCommandOutcome",
    "LocalBuildCommandRunner",
    "SubprocessLocalBuildCommandRunner",
    "TargetRuntimeLocalBuildAttemptRequest",
    "TargetRuntimeLocalBuildAttemptResult",
    "TargetRuntimeLocalBuildAttemptService",
    "create_target_runtime_local_build_attempt",
    "default_target_runtime_local_build_attempt_service",
]

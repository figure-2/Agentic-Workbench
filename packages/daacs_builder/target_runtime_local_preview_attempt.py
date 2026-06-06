"""Explicit local fixture app preview server and browser evidence boundary.

This boundary may start the generated fixture app preview server only after the
local build attempt has passed and a separate operator opt-in is present. Public
output stays hash/status/count-only and never returns command output, file
content, local root paths, provider payloads, or credentials.
"""

from __future__ import annotations

import base64
from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
from time import monotonic, sleep
from typing import Protocol
import urllib.error
import urllib.request

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys, sanitize_public_payload
from packages.core.pathing import PathBoundaryError, resolve_within_root
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import JsonDict, stable_contract_hash

from .runner_provider import is_safe_run_id, safe_public_run_id
from .target_runtime_local_build_attempt import (
    TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION,
)
from .target_runtime_sandbox import CONTRACT_HASH_PATTERN


TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_VERSION = (
    "target-runtime-local-preview-attempt-public-v1"
)
TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE = "target_runtime_local_preview_attempt"
LOCAL_PREVIEW_REQUIRED_MARKERS = (
    "Agentic Workbench Fixture App",
    "Workflow",
    "Task Board",
    "Verification",
)
OWNER_FILTER_CLICK_TARGET_LABEL = "first-non-all"
BROWSER_RUNTIME_PREFLIGHT_VERSION = "browser-runtime-preflight-public-v1"
BROWSER_RUNTIME_INSTALL_GUIDANCE_LABELS = (
    "install-playwright-python-package",
    "install-playwright-chromium-browser",
)
BROWSER_RUNTIME_OFFICIAL_DOC_LABELS = (
    "playwright-python-browsers",
    "playwright-screenshots",
    "chrome-headless-mode",
)


@dataclass(frozen=True, slots=True)
class TargetRuntimeLocalPreviewAttemptRequest:
    """Request to start and verify a local generated fixture app preview."""

    run_id: str
    local_build_attempt_hash: str
    local_build_attempt_projection: JsonDict = field(default_factory=dict)
    workspace_root: str | Path | None = None
    mode: str = TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE
    operator_opt_in: bool = False
    allow_local_preview_server: bool = False
    allow_browser_verification: bool = False
    require_browser_runtime_preflight: bool = True
    preview_timeout_seconds: int = 45
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BrowserRuntimePreflightResult:
    """Public-safe browser runtime availability preflight result."""

    available: bool
    status: str
    reason: str
    import_checked: bool
    launch_checked: bool
    browser_engine: str
    duration_ms: int

    def to_public_record(self) -> JsonDict:
        return {
            "projection_version": BROWSER_RUNTIME_PREFLIGHT_VERSION,
            "available": self.available,
            "status": self.status,
            "reason": self.reason,
            "import_checked": self.import_checked,
            "launch_checked": self.launch_checked,
            "browser_engine": self.browser_engine,
            "duration_ms": self.duration_ms,
            "install_guidance_labels": list(
                BROWSER_RUNTIME_INSTALL_GUIDANCE_LABELS
            ),
            "install_guidance_hashes": [
                stable_contract_hash(
                    {
                        "label": label,
                        "docs": "https://playwright.dev/python/docs/browsers",
                    }
                )
                for label in BROWSER_RUNTIME_INSTALL_GUIDANCE_LABELS
            ],
            "official_doc_labels": list(BROWSER_RUNTIME_OFFICIAL_DOC_LABELS),
            "official_doc_hashes": [
                stable_contract_hash(
                    "https://playwright.dev/python/docs/browsers"
                ),
                stable_contract_hash("https://playwright.dev/docs/screenshots"),
                stable_contract_hash(
                    "https://developer.chrome.com/docs/chromium/headless"
                ),
            ],
            "raw_error_returned": False,
            "env_value_returned": False,
            "local_path_returned": False,
        }


@dataclass(frozen=True, slots=True)
class LocalPreviewOutcome:
    """Sanitized local preview/browser verification result."""

    attempted: bool
    server_started: bool
    server_stopped: bool
    screenshot_written: bool
    screenshot_hash: str
    screenshot_byte_count: int
    visible_marker_count: int
    page_title_hash: str
    preview_url_hash: str
    duration_ms: int
    reason: str
    owner_filter_click_attempted: bool = False
    owner_filter_click_status: str = "not_attempted"
    owner_filter_click_target_label_hash: str = ""
    owner_filter_before_task_count: int = 0
    owner_filter_after_task_count: int = 0
    owner_filter_changed_count: int = 0
    reviewer_decision_click_attempted: bool = False
    reviewer_decision_click_status: str = "not_attempted"
    reviewer_decision_click_target_label_hash: str = ""
    reviewer_decision_before_state_hash: str = ""
    reviewer_decision_after_state_hash: str = ""
    reviewer_decision_state_changed_count: int = 0

    def to_public_record(self) -> JsonDict:
        return {
            "attempted": self.attempted,
            "server_started": self.server_started,
            "server_stopped": self.server_stopped,
            "screenshot_written": self.screenshot_written,
            "screenshot_hash": self.screenshot_hash,
            "screenshot_byte_count": self.screenshot_byte_count,
            "visible_marker_count": self.visible_marker_count,
            "page_title_hash": self.page_title_hash,
            "preview_url_hash": self.preview_url_hash,
            "duration_ms": self.duration_ms,
            "reason": self.reason,
            "owner_filter_click_attempted": self.owner_filter_click_attempted,
            "owner_filter_click_status": self.owner_filter_click_status,
            "owner_filter_click_target_label_hash": (
                self.owner_filter_click_target_label_hash
            ),
            "owner_filter_before_task_count": self.owner_filter_before_task_count,
            "owner_filter_after_task_count": self.owner_filter_after_task_count,
            "owner_filter_changed_count": self.owner_filter_changed_count,
            "owner_filter_dom_text_returned": False,
            "owner_filter_raw_event_returned": False,
            "reviewer_decision_click_attempted": (
                self.reviewer_decision_click_attempted
            ),
            "reviewer_decision_click_status": self.reviewer_decision_click_status,
            "reviewer_decision_click_target_label_hash": (
                self.reviewer_decision_click_target_label_hash
            ),
            "reviewer_decision_before_state_hash": (
                self.reviewer_decision_before_state_hash
            ),
            "reviewer_decision_after_state_hash": (
                self.reviewer_decision_after_state_hash
            ),
            "reviewer_decision_state_changed_count": (
                self.reviewer_decision_state_changed_count
            ),
            "reviewer_decision_dom_text_returned": False,
            "reviewer_decision_raw_event_returned": False,
            "raw_command_output_returned": False,
            "screenshot_path_returned": False,
            "page_text_returned": False,
            "root_path_returned": False,
        }


class LocalPreviewRunner(Protocol):
    """Runner contract used by tests and the real local preview path."""

    def run(
        self,
        *,
        app_dir: Path,
        screenshot_path: Path,
        timeout_seconds: int,
    ) -> LocalPreviewOutcome:
        """Start preview server, verify page, write screenshot evidence."""


class BrowserRuntimeProbe(Protocol):
    """Probe whether browser screenshot verification can run locally."""

    def probe(self) -> BrowserRuntimePreflightResult:
        """Return public-safe browser runtime availability evidence."""


class PlaywrightBrowserRuntimeProbe:
    """Check Playwright first, then installed system headless browsers."""

    def probe(self) -> BrowserRuntimePreflightResult:
        started = monotonic()
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception:
            executable = _system_browser_executable()
            if executable is not None and _system_browser_probe(executable):
                return _browser_runtime_preflight_result(
                    started=started,
                    available=True,
                    status="passed",
                    reason="system_headless_browser_available",
                    import_checked=True,
                    launch_checked=True,
                    browser_engine="system-chromium",
                )
            return _browser_runtime_preflight_result(
                started=started,
                available=False,
                status="environment_blocked",
                reason="playwright_python_package_missing",
                import_checked=True,
                launch_checked=False,
                browser_engine="none",
            )

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                browser.close()
            return _browser_runtime_preflight_result(
                started=started,
                available=True,
                status="passed",
                reason="browser_runtime_available",
                import_checked=True,
                launch_checked=True,
                browser_engine="chromium",
            )
        except Exception:
            executable = _system_browser_executable()
            if executable is not None and _system_browser_probe(executable):
                return _browser_runtime_preflight_result(
                    started=started,
                    available=True,
                    status="passed",
                    reason="system_headless_browser_available",
                    import_checked=True,
                    launch_checked=True,
                    browser_engine="system-chromium",
                )
            return _browser_runtime_preflight_result(
                started=started,
                available=False,
                status="environment_blocked",
                reason="playwright_browser_runtime_missing_or_unlaunchable",
                import_checked=True,
                launch_checked=True,
                browser_engine="none",
            )


class SubprocessLocalPreviewRunner:
    """Run Vite preview and optionally verify it with Playwright if available."""

    def run(
        self,
        *,
        app_dir: Path,
        screenshot_path: Path,
        timeout_seconds: int,
    ) -> LocalPreviewOutcome:
        started = monotonic()
        npm = _npm_executable()
        port = _find_free_local_port()
        url = f"http://127.0.0.1:{port}/"
        proc: subprocess.Popen | None = None
        server_started = False
        server_stopped = False
        outcome: LocalPreviewOutcome | None = None
        try:
            proc = subprocess.Popen(
                [
                    npm,
                    "run",
                    "preview",
                    "--",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--strictPort",
                ],
                cwd=app_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            server_started = _wait_for_local_http(url, timeout_seconds=timeout_seconds)
            if not server_started:
                outcome = _preview_outcome(
                    attempted=True,
                    server_started=False,
                    server_stopped=False,
                    screenshot_written=False,
                    screenshot_hash="",
                    screenshot_byte_count=0,
                    visible_marker_count=0,
                    page_title_hash="",
                    preview_url_hash=stable_contract_hash(url),
                    started=started,
                    reason="local_preview_server_not_ready",
                )
            else:
                browser_result = _capture_with_playwright(
                    url=url,
                    screenshot_path=screenshot_path,
                    timeout_seconds=timeout_seconds,
                )
                outcome = _preview_outcome(
                    attempted=True,
                    server_started=True,
                    server_stopped=False,
                    screenshot_written=browser_result["screenshot_written"],
                    screenshot_hash=browser_result["screenshot_hash"],
                    screenshot_byte_count=browser_result["screenshot_byte_count"],
                    visible_marker_count=browser_result["visible_marker_count"],
                    page_title_hash=browser_result["page_title_hash"],
                    preview_url_hash=stable_contract_hash(url),
                    started=started,
                    reason=browser_result["reason"],
                    owner_filter_click_attempted=bool(
                        browser_result.get("owner_filter_click_attempted", False)
                    ),
                    owner_filter_click_status=str(
                        browser_result.get(
                            "owner_filter_click_status",
                            "not_attempted",
                        )
                    ),
                    owner_filter_click_target_label_hash=str(
                        browser_result.get(
                            "owner_filter_click_target_label_hash",
                            "",
                        )
                    ),
                    owner_filter_before_task_count=int(
                        browser_result.get("owner_filter_before_task_count", 0)
                        or 0
                    ),
                    owner_filter_after_task_count=int(
                        browser_result.get("owner_filter_after_task_count", 0) or 0
                    ),
                    owner_filter_changed_count=int(
                        browser_result.get("owner_filter_changed_count", 0) or 0
                    ),
                    reviewer_decision_click_attempted=bool(
                        browser_result.get(
                            "reviewer_decision_click_attempted",
                            False,
                        )
                    ),
                    reviewer_decision_click_status=str(
                        browser_result.get(
                            "reviewer_decision_click_status",
                            "not_attempted",
                        )
                    ),
                    reviewer_decision_click_target_label_hash=str(
                        browser_result.get(
                            "reviewer_decision_click_target_label_hash",
                            "",
                        )
                    ),
                    reviewer_decision_before_state_hash=str(
                        browser_result.get(
                            "reviewer_decision_before_state_hash",
                            "",
                        )
                    ),
                    reviewer_decision_after_state_hash=str(
                        browser_result.get(
                            "reviewer_decision_after_state_hash",
                            "",
                        )
                    ),
                    reviewer_decision_state_changed_count=int(
                        browser_result.get(
                            "reviewer_decision_state_changed_count",
                            0,
                        )
                        or 0
                    ),
                )
        except FileNotFoundError:
            outcome = _preview_outcome(
                attempted=True,
                server_started=False,
                server_stopped=False,
                screenshot_written=False,
                screenshot_hash="",
                screenshot_byte_count=0,
                visible_marker_count=0,
                page_title_hash="",
                preview_url_hash=stable_contract_hash(url),
                started=started,
                reason="local_package_manager_unavailable",
            )
        finally:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
                server_stopped = True
        selected = outcome or _preview_outcome(
            attempted=True,
            server_started=server_started,
            server_stopped=server_stopped,
            screenshot_written=False,
            screenshot_hash="",
            screenshot_byte_count=0,
            visible_marker_count=0,
            page_title_hash="",
            preview_url_hash=stable_contract_hash(url),
            started=started,
            reason="local_preview_failed",
        )
        if selected.server_stopped == server_stopped:
            return selected
        return LocalPreviewOutcome(
            attempted=selected.attempted,
            server_started=selected.server_started,
            server_stopped=server_stopped,
            screenshot_written=selected.screenshot_written,
            screenshot_hash=selected.screenshot_hash,
            screenshot_byte_count=selected.screenshot_byte_count,
            visible_marker_count=selected.visible_marker_count,
            page_title_hash=selected.page_title_hash,
            preview_url_hash=selected.preview_url_hash,
            duration_ms=selected.duration_ms,
            reason=selected.reason,
            owner_filter_click_attempted=selected.owner_filter_click_attempted,
            owner_filter_click_status=selected.owner_filter_click_status,
            owner_filter_click_target_label_hash=(
                selected.owner_filter_click_target_label_hash
            ),
            owner_filter_before_task_count=selected.owner_filter_before_task_count,
            owner_filter_after_task_count=selected.owner_filter_after_task_count,
            owner_filter_changed_count=selected.owner_filter_changed_count,
            reviewer_decision_click_attempted=(
                selected.reviewer_decision_click_attempted
            ),
            reviewer_decision_click_status=selected.reviewer_decision_click_status,
            reviewer_decision_click_target_label_hash=(
                selected.reviewer_decision_click_target_label_hash
            ),
            reviewer_decision_before_state_hash=(
                selected.reviewer_decision_before_state_hash
            ),
            reviewer_decision_after_state_hash=(
                selected.reviewer_decision_after_state_hash
            ),
            reviewer_decision_state_changed_count=(
                selected.reviewer_decision_state_changed_count
            ),
        )


@dataclass(frozen=True, slots=True)
class TargetRuntimeLocalPreviewAttemptResult:
    """Public-safe local preview attempt projection."""

    projection_version: str
    run_id: str
    mode: str
    status: str
    reason: str
    local_preview_attempted: bool
    local_preview_opt_in_present: bool
    local_preview_server_allowed: bool
    browser_verification_allowed: bool
    local_build_attempt_hash: str
    local_build_attempt_projection_hash: str
    browser_runtime_preflight: JsonDict
    local_preview_attempt_hash: str
    preview_record: JsonDict
    checks: list[JsonDict]
    counts: JsonDict
    execution_boundary: JsonDict
    repository_boundary: JsonDict
    claim_boundary: JsonDict

    def to_dict(self) -> JsonDict:
        payload = sanitize_public_payload(asdict(self))
        if not isinstance(payload, dict):
            raise ValueError("local preview attempt must be a mapping")
        _assert_projection_safe(payload)
        return payload


def _npm_executable() -> str:
    return "npm.cmd" if sys.platform.startswith("win") else "npm"


def _is_contract_hash(value: object) -> bool:
    return isinstance(value, str) and CONTRACT_HASH_PATTERN.fullmatch(value) is not None


def _assert_projection_safe(value: JsonDict) -> None:
    public = sanitize_public_payload(value)
    if not isinstance(public, dict):
        raise ValueError("local preview attempt must be a mapping")
    if find_forbidden_public_keys(public):
        raise ValueError("local preview attempt contains forbidden keys")
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if find_forbidden_claims(serialized):
        raise ValueError("local preview attempt contains forbidden claims")
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


def _screenshot_path(*, workspace_root: Path, run_id: str) -> Path:
    return resolve_within_root(
        workspace_root,
        f"runs/{safe_public_run_id(run_id)}/generated-app/tests/preview.png",
    )


def _find_free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_local_http(url: str, *, timeout_seconds: int) -> bool:
    deadline = monotonic() + max(1, int(timeout_seconds))
    while monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status < 500:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            sleep(0.25)
    return False


def _file_hash(path: Path) -> str:
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _capture_with_playwright(
    *,
    url: str,
    screenshot_path: Path,
    timeout_seconds: int,
) -> JsonDict:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        return _capture_with_system_browser(
            url=url,
            screenshot_path=screenshot_path,
            timeout_seconds=timeout_seconds,
        )

    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(url, wait_until="networkidle", timeout=max(1, timeout_seconds) * 1000)
            visible_marker_count = sum(
                1 for marker in LOCAL_PREVIEW_REQUIRED_MARKERS if page.get_by_text(marker).count() > 0
            )
            task_cards = page.locator("[data-aw-task-card]")
            before_task_count = task_cards.count()
            target = page.locator("[data-aw-owner-filter]").nth(1)
            target_label_hash = ""
            click_status = "target_missing"
            click_attempted = False
            after_task_count = before_task_count
            if target.count() > 0:
                click_attempted = True
                target_label = target.get_attribute("data-aw-owner-filter") or ""
                target_label_hash = stable_contract_hash(target_label)
                target.first.click()
                page.wait_for_timeout(100)
                after_task_count = task_cards.count()
                click_status = (
                    "passed"
                    if after_task_count < before_task_count
                    else "task_count_unchanged"
                )
            decision_value = page.locator(
                "[data-aw-reviewer-decision-value]"
            ).first
            decision_target = page.locator(
                "[data-aw-reviewer-decision-action]"
            ).first
            reviewer_click_attempted = False
            reviewer_click_status = "target_missing"
            reviewer_target_label_hash = ""
            reviewer_before_state_hash = ""
            reviewer_after_state_hash = ""
            reviewer_state_changed_count = 0
            reviewer_before_state = ""
            reviewer_after_state = ""
            if decision_value.count() > 0:
                reviewer_before_state = decision_value.inner_text()
                reviewer_before_state_hash = stable_contract_hash(
                    reviewer_before_state
                )
            if decision_target.count() > 0:
                reviewer_click_attempted = True
                reviewer_target_label = (
                    decision_target.get_attribute(
                        "data-aw-reviewer-decision-action"
                    )
                    or ""
                )
                reviewer_target_label_hash = stable_contract_hash(
                    reviewer_target_label
                )
                decision_target.click()
                page.wait_for_timeout(100)
                if decision_value.count() > 0:
                    reviewer_after_state = decision_value.inner_text()
                    reviewer_after_state_hash = stable_contract_hash(
                        reviewer_after_state
                    )
                reviewer_state_changed_count = (
                    1
                    if (
                        reviewer_before_state_hash
                        and reviewer_after_state_hash
                        and reviewer_before_state_hash != reviewer_after_state_hash
                    )
                    else 0
                )
                reviewer_click_status = (
                    "passed"
                    if reviewer_state_changed_count
                    else "state_unchanged"
                )
            title = page.title()
            page.screenshot(path=str(screenshot_path), full_page=True)
            browser.close()
        return {
            "reason": "local_preview_browser_verified"
            if visible_marker_count == len(LOCAL_PREVIEW_REQUIRED_MARKERS)
            else "local_preview_required_markers_missing",
            "screenshot_written": screenshot_path.is_file(),
            "screenshot_hash": _file_hash(screenshot_path),
            "screenshot_byte_count": screenshot_path.stat().st_size
            if screenshot_path.is_file()
            else 0,
            "visible_marker_count": visible_marker_count,
            "page_title_hash": stable_contract_hash(title),
            "owner_filter_click_attempted": click_attempted,
            "owner_filter_click_status": click_status,
            "owner_filter_click_target_label_hash": target_label_hash,
            "owner_filter_before_task_count": before_task_count,
            "owner_filter_after_task_count": after_task_count,
            "owner_filter_changed_count": max(0, before_task_count - after_task_count),
            "reviewer_decision_click_attempted": reviewer_click_attempted,
            "reviewer_decision_click_status": reviewer_click_status,
            "reviewer_decision_click_target_label_hash": reviewer_target_label_hash,
            "reviewer_decision_before_state_hash": reviewer_before_state_hash,
            "reviewer_decision_after_state_hash": reviewer_after_state_hash,
            "reviewer_decision_state_changed_count": reviewer_state_changed_count,
        }
    except Exception:
        system_result = _capture_with_system_browser(
            url=url,
            screenshot_path=screenshot_path,
            timeout_seconds=timeout_seconds,
        )
        if system_result["screenshot_written"]:
            return system_result
        return {
            "reason": "browser_verification_failed",
            "screenshot_written": screenshot_path.is_file(),
            "screenshot_hash": _file_hash(screenshot_path),
            "screenshot_byte_count": screenshot_path.stat().st_size
            if screenshot_path.is_file()
            else 0,
            "visible_marker_count": 0,
            "page_title_hash": "",
            "owner_filter_click_attempted": False,
            "owner_filter_click_status": "browser_click_runtime_unavailable",
            "owner_filter_click_target_label_hash": "",
            "owner_filter_before_task_count": 0,
            "owner_filter_after_task_count": 0,
            "owner_filter_changed_count": 0,
            "reviewer_decision_click_attempted": False,
            "reviewer_decision_click_status": "browser_click_runtime_unavailable",
            "reviewer_decision_click_target_label_hash": "",
            "reviewer_decision_before_state_hash": "",
            "reviewer_decision_after_state_hash": "",
            "reviewer_decision_state_changed_count": 0,
        }


def _system_browser_executable() -> Path | None:
    executable_names = ("chrome", "chrome.exe", "msedge", "msedge.exe")
    for name in executable_names:
        resolved = shutil.which(name)
        if resolved:
            return Path(resolved)
    windows_candidates = (
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    )
    for candidate in windows_candidates:
        if candidate.is_file():
            return candidate
    return None


def _headless_browser_common_args(profile_dir: Path) -> list[str]:
    return [
        "--headless=new",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-component-extensions-with-background-pages",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={profile_dir}",
    ]


def _system_browser_probe(executable: Path) -> bool:
    profile_dir: Path | None = None
    proc: subprocess.Popen | None = None
    try:
        profile_dir = Path(tempfile.mkdtemp(prefix="aw-browser-probe-"))
        port = _find_free_local_port()
        proc = subprocess.Popen(
            [
                str(executable),
                *_headless_browser_common_args(profile_dir),
                f"--remote-debugging-port={port}",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _cdp_page_websocket_url(port=port, timeout_seconds=5)
        return True
    except (OSError, TimeoutError, subprocess.TimeoutExpired):
        return False
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        if profile_dir is not None:
            shutil.rmtree(profile_dir, ignore_errors=True)


class _CdpWebSocket:
    """Tiny stdlib WebSocket client for Chrome DevTools Protocol calls."""

    def __init__(self, ws_url: str, *, timeout_seconds: int) -> None:
        match = re.fullmatch(r"ws://([^/:]+):(\d+)(/.*)", ws_url)
        if match is None:
            raise ValueError("unsupported websocket url")
        self._host = match.group(1)
        self._port = int(match.group(2))
        self._path = match.group(3)
        self._timeout_seconds = max(1, int(timeout_seconds))
        self._socket: socket.socket | None = None
        self._next_id = 1

    def __enter__(self) -> "_CdpWebSocket":
        sock = socket.create_connection(
            (self._host, self._port),
            timeout=self._timeout_seconds,
        )
        sock.settimeout(self._timeout_seconds)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {self._path} HTTP/1.1\r\n"
            f"Host: {self._host}:{self._port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        sock.sendall(request.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            sock.close()
            raise OSError("devtools websocket upgrade failed")
        self._socket = sock
        return self

    def __exit__(self, *args: object) -> None:
        if self._socket is not None:
            try:
                self._socket.close()
            finally:
                self._socket = None

    def call(self, method: str, params: JsonDict | None = None) -> JsonDict:
        call_id = self._next_id
        self._next_id += 1
        payload = {"id": call_id, "method": method}
        if params is not None:
            payload["params"] = params
        self._send_text(json.dumps(payload, ensure_ascii=True, sort_keys=True))
        deadline = monotonic() + self._timeout_seconds
        while monotonic() < deadline:
            message = self._recv_text()
            if not message:
                continue
            parsed = json.loads(message)
            if parsed.get("id") == call_id:
                if "error" in parsed:
                    raise RuntimeError("devtools command failed")
                result = parsed.get("result", {})
                return result if isinstance(result, dict) else {}
        raise TimeoutError("devtools command timed out")

    def _send_text(self, text: str) -> None:
        if self._socket is None:
            raise OSError("websocket not connected")
        payload = text.encode("utf-8")
        length = len(payload)
        if length < 126:
            header = bytes((0x81, 0x80 | length))
        elif length < 65536:
            header = bytes((0x81, 0x80 | 126)) + struct.pack("!H", length)
        else:
            header = bytes((0x81, 0x80 | 127)) + struct.pack("!Q", length)
        mask = os.urandom(4)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self._socket.sendall(header + mask + masked)

    def _recv_text(self) -> str:
        if self._socket is None:
            raise OSError("websocket not connected")
        first = self._read_exact(2)
        opcode = first[0] & 0x0F
        length = first[1] & 0x7F
        masked = bool(first[1] & 0x80)
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]
        mask = self._read_exact(4) if masked else b""
        payload = self._read_exact(length) if length else b""
        if masked:
            payload = bytes(
                byte ^ mask[index % 4] for index, byte in enumerate(payload)
            )
        if opcode == 8:
            return ""
        if opcode not in {1, 0}:
            return ""
        return payload.decode("utf-8", errors="replace")

    def _read_exact(self, length: int) -> bytes:
        if self._socket is None:
            raise OSError("websocket not connected")
        chunks = bytearray()
        while len(chunks) < length:
            chunk = self._socket.recv(length - len(chunks))
            if not chunk:
                raise OSError("websocket closed")
            chunks.extend(chunk)
        return bytes(chunks)


def _cdp_page_websocket_url(*, port: int, timeout_seconds: int) -> str:
    deadline = monotonic() + max(1, int(timeout_seconds))
    url = f"http://127.0.0.1:{port}/json/list"
    while monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                targets = json.loads(response.read().decode("utf-8"))
            if isinstance(targets, list):
                for target in targets:
                    if (
                        isinstance(target, dict)
                        and target.get("type") == "page"
                        and isinstance(target.get("webSocketDebuggerUrl"), str)
                    ):
                        return str(target["webSocketDebuggerUrl"])
        except (OSError, TimeoutError, ValueError, urllib.error.URLError):
            sleep(0.1)
    raise TimeoutError("devtools page target unavailable")


def _owner_filter_click_script() -> str:
    markers = json.dumps(LOCAL_PREVIEW_REQUIRED_MARKERS, ensure_ascii=True)
    return (
        "(() => {"
        f"const markers = {markers};"
        "const bodyText = document.body ? document.body.innerText : '';"
        "const visibleMarkerCount = markers.filter((marker) => bodyText.includes(marker)).length;"
        "const cards = () => Array.from(document.querySelectorAll('[data-aw-task-card]'));"
        "const beforeTaskCount = cards().length;"
        "const target = Array.from(document.querySelectorAll('[data-aw-owner-filter]')).find((button) => button.getAttribute('data-aw-owner-filter') !== 'All');"
        "const targetLabel = target ? (target.getAttribute('data-aw-owner-filter') || '') : '';"
        "const decisionValue = document.querySelector('[data-aw-reviewer-decision-value]');"
        "const decisionTarget = document.querySelector('[data-aw-reviewer-decision-action]');"
        "const decisionTargetLabel = decisionTarget ? (decisionTarget.getAttribute('data-aw-reviewer-decision-action') || '') : '';"
        "const beforeDecisionState = decisionValue ? (decisionValue.textContent || '') : '';"
        "let clicked = false;"
        "let clickStatus = 'target_missing';"
        "let decisionClicked = false;"
        "let decisionClickStatus = 'target_missing';"
        "if (target) { target.click(); clicked = true; }"
        "if (decisionTarget) { decisionTarget.click(); decisionClicked = true; }"
        "return new Promise((resolve) => setTimeout(() => {"
        "const afterTaskCount = cards().length;"
        "const afterDecisionState = decisionValue ? (decisionValue.textContent || '') : '';"
        "if (clicked) { clickStatus = afterTaskCount < beforeTaskCount ? 'passed' : 'task_count_unchanged'; }"
        "if (decisionClicked) { decisionClickStatus = afterDecisionState !== beforeDecisionState ? 'passed' : 'state_unchanged'; }"
        "resolve({"
        "visibleMarkerCount,"
        "title: document.title || '',"
        "clicked,"
        "clickStatus,"
        "targetLabel: clicked ? targetLabel : '',"
        "beforeTaskCount,"
        "afterTaskCount,"
        "changedCount: Math.max(0, beforeTaskCount - afterTaskCount),"
        "decisionClicked,"
        "decisionClickStatus,"
        "decisionTargetLabel: decisionClicked ? decisionTargetLabel : '',"
        "beforeDecisionState,"
        "afterDecisionState,"
        "decisionChangedCount: decisionClicked && afterDecisionState !== beforeDecisionState ? 1 : 0"
        "});"
        "}, 150));"
        "})()"
    )


def _capture_with_system_browser_cdp(
    *,
    executable: Path,
    url: str,
    screenshot_path: Path,
    timeout_seconds: int,
) -> JsonDict | None:
    port = _find_free_local_port()
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    proc: subprocess.Popen | None = None
    started = False
    profile_dir: Path | None = None
    try:
        profile_dir = Path(
            tempfile.mkdtemp(
            prefix="browser-profile-",
            dir=screenshot_path.parent,
            )
        )
        proc = subprocess.Popen(
            [
                str(executable),
                *_headless_browser_common_args(profile_dir),
                f"--remote-debugging-port={port}",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        started = True
        ws_url = _cdp_page_websocket_url(
            port=port,
            timeout_seconds=timeout_seconds,
        )
        with _CdpWebSocket(ws_url, timeout_seconds=timeout_seconds) as cdp:
            cdp.call("Page.enable")
            cdp.call("Runtime.enable")
            cdp.call("Page.navigate", {"url": url})
            deadline = monotonic() + max(1, int(timeout_seconds))
            while monotonic() < deadline:
                state = cdp.call(
                    "Runtime.evaluate",
                    {
                        "expression": "document.readyState",
                        "returnByValue": True,
                    },
                )
                state_result = state.get("result", {})
                if (
                    isinstance(state_result, dict)
                    and state_result.get("value") == "complete"
                ):
                    break
                sleep(0.1)
            evaluated = cdp.call(
                "Runtime.evaluate",
                {
                    "expression": _owner_filter_click_script(),
                    "awaitPromise": True,
                    "returnByValue": True,
                },
            )
            value = evaluated.get("result", {})
            click_value = value.get("value", {}) if isinstance(value, dict) else {}
            if not isinstance(click_value, dict):
                click_value = {}
            screenshot = cdp.call(
                "Page.captureScreenshot",
                {
                    "format": "png",
                    "captureBeyondViewport": True,
                },
            )
            encoded = screenshot.get("data")
            if isinstance(encoded, str) and encoded:
                screenshot_path.write_bytes(base64.b64decode(encoded))
            screenshot_written = screenshot_path.is_file()
            visible_marker_count = int(click_value.get("visibleMarkerCount") or 0)
            return {
                "reason": "local_preview_browser_verified"
                if (
                    screenshot_written
                    and visible_marker_count == len(LOCAL_PREVIEW_REQUIRED_MARKERS)
                )
                else "local_preview_required_markers_missing",
                "screenshot_written": screenshot_written,
                "screenshot_hash": _file_hash(screenshot_path),
                "screenshot_byte_count": screenshot_path.stat().st_size
                if screenshot_written
                else 0,
                "visible_marker_count": visible_marker_count,
                "page_title_hash": stable_contract_hash(
                    str(click_value.get("title") or "")
                ),
                "owner_filter_click_attempted": bool(
                    click_value.get("clicked")
                ),
                "owner_filter_click_status": str(
                    click_value.get("clickStatus") or "not_attempted"
                ),
                "owner_filter_click_target_label_hash": (
                    stable_contract_hash(str(click_value.get("targetLabel")))
                    if click_value.get("targetLabel")
                    else ""
                ),
                "owner_filter_before_task_count": int(
                    click_value.get("beforeTaskCount") or 0
                ),
                "owner_filter_after_task_count": int(
                    click_value.get("afterTaskCount") or 0
                ),
                "owner_filter_changed_count": int(
                    click_value.get("changedCount") or 0
                ),
                "reviewer_decision_click_attempted": bool(
                    click_value.get("decisionClicked")
                ),
                "reviewer_decision_click_status": str(
                    click_value.get("decisionClickStatus") or "not_attempted"
                ),
                "reviewer_decision_click_target_label_hash": (
                    stable_contract_hash(str(click_value.get("decisionTargetLabel")))
                    if click_value.get("decisionTargetLabel")
                    else ""
                ),
                "reviewer_decision_before_state_hash": (
                    stable_contract_hash(str(click_value.get("beforeDecisionState")))
                    if click_value.get("beforeDecisionState")
                    else ""
                ),
                "reviewer_decision_after_state_hash": (
                    stable_contract_hash(str(click_value.get("afterDecisionState")))
                    if click_value.get("afterDecisionState")
                    else ""
                ),
                "reviewer_decision_state_changed_count": int(
                    click_value.get("decisionChangedCount") or 0
                ),
            }
    except (
        OSError,
        TimeoutError,
        RuntimeError,
        ValueError,
        subprocess.TimeoutExpired,
    ):
        return None
    finally:
        if started and proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        if profile_dir is not None:
            shutil.rmtree(profile_dir, ignore_errors=True)
    return None


def _capture_with_system_browser(
    *,
    url: str,
    screenshot_path: Path,
    timeout_seconds: int,
) -> JsonDict:
    executable = _system_browser_executable()
    if executable is None:
        return {
            "reason": "browser_verification_runtime_unavailable",
            "screenshot_written": False,
            "screenshot_hash": "",
            "screenshot_byte_count": 0,
            "visible_marker_count": 0,
            "page_title_hash": "",
            "owner_filter_click_attempted": False,
            "owner_filter_click_status": "browser_click_runtime_unavailable",
            "owner_filter_click_target_label_hash": "",
            "owner_filter_before_task_count": 0,
            "owner_filter_after_task_count": 0,
            "owner_filter_changed_count": 0,
            "reviewer_decision_click_attempted": False,
            "reviewer_decision_click_status": "browser_click_runtime_unavailable",
            "reviewer_decision_click_target_label_hash": "",
            "reviewer_decision_before_state_hash": "",
            "reviewer_decision_after_state_hash": "",
            "reviewer_decision_state_changed_count": 0,
        }
    cdp_result = _capture_with_system_browser_cdp(
        executable=executable,
        url=url,
        screenshot_path=screenshot_path,
        timeout_seconds=timeout_seconds,
    )
    if cdp_result is not None and cdp_result.get("screenshot_written"):
        return cdp_result
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    timeout_ms = max(1, int(timeout_seconds)) * 1000
    try:
        with tempfile.TemporaryDirectory(
            prefix="browser-profile-",
            dir=screenshot_path.parent,
        ) as profile:
            common_args = _headless_browser_common_args(Path(profile))
            dom_completed = subprocess.run(
                [
                    str(executable),
                    *common_args,
                    "--dump-dom",
                    f"--timeout={timeout_ms}",
                    f"--virtual-time-budget={min(timeout_ms, 5000)}",
                    url,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=max(1, int(timeout_seconds)) + 10,
                check=False,
            )
            screenshot_completed = subprocess.run(
                [
                    str(executable),
                    *common_args,
                    f"--screenshot={screenshot_path}",
                    "--window-size=1280,900",
                    f"--timeout={timeout_ms}",
                    f"--virtual-time-budget={min(timeout_ms, 5000)}",
                    url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=max(1, int(timeout_seconds)) + 10,
                check=False,
            )
    except (OSError, subprocess.TimeoutExpired):
        return {
            "reason": "system_browser_verification_failed",
            "screenshot_written": screenshot_path.is_file(),
            "screenshot_hash": _file_hash(screenshot_path),
            "screenshot_byte_count": screenshot_path.stat().st_size
            if screenshot_path.is_file()
            else 0,
            "visible_marker_count": 0,
            "page_title_hash": "",
            "owner_filter_click_attempted": False,
            "owner_filter_click_status": "browser_click_runtime_unavailable",
            "owner_filter_click_target_label_hash": "",
            "owner_filter_before_task_count": 0,
            "owner_filter_after_task_count": 0,
            "owner_filter_changed_count": 0,
            "reviewer_decision_click_attempted": False,
            "reviewer_decision_click_status": "browser_click_runtime_unavailable",
            "reviewer_decision_click_target_label_hash": "",
            "reviewer_decision_before_state_hash": "",
            "reviewer_decision_after_state_hash": "",
            "reviewer_decision_state_changed_count": 0,
        }

    dom = dom_completed.stdout or ""
    visible_marker_count = sum(
        1 for marker in LOCAL_PREVIEW_REQUIRED_MARKERS if marker in dom
    )
    title_match = re.search(r"<title>(.*?)</title>", dom, flags=re.IGNORECASE)
    title = title_match.group(1) if title_match else ""
    screenshot_written = screenshot_path.is_file()
    if (
        dom_completed.returncode == 0
        and screenshot_completed.returncode == 0
        and screenshot_written
        and visible_marker_count == len(LOCAL_PREVIEW_REQUIRED_MARKERS)
    ):
        reason = "local_preview_browser_verified"
    elif screenshot_written:
        reason = "local_preview_required_markers_missing"
    else:
        reason = "system_browser_screenshot_failed"
    return {
        "reason": reason,
        "screenshot_written": screenshot_written,
        "screenshot_hash": _file_hash(screenshot_path),
        "screenshot_byte_count": screenshot_path.stat().st_size
        if screenshot_written
        else 0,
        "visible_marker_count": visible_marker_count,
        "page_title_hash": stable_contract_hash(title),
        "owner_filter_click_attempted": False,
        "owner_filter_click_status": "browser_click_runtime_unavailable",
        "owner_filter_click_target_label_hash": "",
        "owner_filter_before_task_count": 0,
        "owner_filter_after_task_count": 0,
        "owner_filter_changed_count": 0,
        "reviewer_decision_click_attempted": False,
        "reviewer_decision_click_status": "browser_click_runtime_unavailable",
        "reviewer_decision_click_target_label_hash": "",
        "reviewer_decision_before_state_hash": "",
        "reviewer_decision_after_state_hash": "",
        "reviewer_decision_state_changed_count": 0,
    }


def _browser_runtime_preflight_result(
    *,
    started: float,
    available: bool,
    status: str,
    reason: str,
    import_checked: bool,
    launch_checked: bool,
    browser_engine: str,
) -> BrowserRuntimePreflightResult:
    return BrowserRuntimePreflightResult(
        available=available,
        status=status,
        reason=reason,
        import_checked=import_checked,
        launch_checked=launch_checked,
        browser_engine=browser_engine,
        duration_ms=int((monotonic() - started) * 1000),
    )


def _preview_outcome(
    *,
    attempted: bool,
    server_started: bool,
    server_stopped: bool,
    screenshot_written: bool,
    screenshot_hash: str,
    screenshot_byte_count: int,
    visible_marker_count: int,
    page_title_hash: str,
    preview_url_hash: str,
    started: float,
    reason: str,
    owner_filter_click_attempted: bool = False,
    owner_filter_click_status: str = "not_attempted",
    owner_filter_click_target_label_hash: str = "",
    owner_filter_before_task_count: int = 0,
    owner_filter_after_task_count: int = 0,
    owner_filter_changed_count: int = 0,
    reviewer_decision_click_attempted: bool = False,
    reviewer_decision_click_status: str = "not_attempted",
    reviewer_decision_click_target_label_hash: str = "",
    reviewer_decision_before_state_hash: str = "",
    reviewer_decision_after_state_hash: str = "",
    reviewer_decision_state_changed_count: int = 0,
) -> LocalPreviewOutcome:
    return LocalPreviewOutcome(
        attempted=attempted,
        server_started=server_started,
        server_stopped=server_stopped,
        screenshot_written=screenshot_written,
        screenshot_hash=screenshot_hash,
        screenshot_byte_count=screenshot_byte_count,
        visible_marker_count=visible_marker_count,
        page_title_hash=page_title_hash,
        preview_url_hash=preview_url_hash,
        duration_ms=int((monotonic() - started) * 1000),
        reason=reason,
        owner_filter_click_attempted=owner_filter_click_attempted,
        owner_filter_click_status=owner_filter_click_status,
        owner_filter_click_target_label_hash=owner_filter_click_target_label_hash,
        owner_filter_before_task_count=owner_filter_before_task_count,
        owner_filter_after_task_count=owner_filter_after_task_count,
        owner_filter_changed_count=owner_filter_changed_count,
        reviewer_decision_click_attempted=reviewer_decision_click_attempted,
        reviewer_decision_click_status=reviewer_decision_click_status,
        reviewer_decision_click_target_label_hash=(
            reviewer_decision_click_target_label_hash
        ),
        reviewer_decision_before_state_hash=reviewer_decision_before_state_hash,
        reviewer_decision_after_state_hash=reviewer_decision_after_state_hash,
        reviewer_decision_state_changed_count=reviewer_decision_state_changed_count,
    )


def _repository_boundary(*, configured: bool) -> JsonDict:
    return {
        "local_preview_attempt_backend": "local" if configured else "unconfigured",
        "root_path_returned": False,
        "raw_row_returned": False,
        "file_content_returned": False,
        "command_output_returned": False,
        "screenshot_path_returned": False,
        "page_text_returned": False,
    }


def _claim_boundary(
    *,
    status: str,
    preview_record: JsonDict,
    browser_runtime_preflight: JsonDict,
) -> JsonDict:
    return {
        "scope": "explicit local fixture app preview attempt only",
        "local_preview_attempt_recorded": bool(preview_record.get("attempted")),
        "local_preview_browser_verified": status == "passed",
        "browser_runtime_preflight_available": bool(
            browser_runtime_preflight.get("available")
        ),
        "server_started": bool(preview_record.get("server_started")),
        "server_stopped": bool(preview_record.get("server_stopped")),
        "screenshot_evidence_recorded": bool(preview_record.get("screenshot_written")),
        "owner_filter_click_verified": (
            preview_record.get("owner_filter_click_status") == "passed"
        ),
        "reviewer_decision_click_verified": (
            preview_record.get("reviewer_decision_click_status") == "passed"
        ),
        "target_runtime_outcome": False,
        "external_provider_outcome": False,
        "hosted_behavior": False,
        "production_success_claim": False,
    }


def _execution_boundary(*, preview_record: JsonDict) -> JsonDict:
    server_started = bool(preview_record.get("server_started"))
    browser_click_actions = int(bool(preview_record.get("owner_filter_click_attempted")))
    browser_click_actions += int(
        bool(preview_record.get("reviewer_decision_click_attempted"))
    )
    return {
        "target_runtime_calls": 0,
        "provider_calls": 0,
        "live_api_calls": 0,
        "sdk_imports": 0,
        "env_key_value_reads": 0,
        "subprocess_calls": 1 if bool(preview_record.get("attempted")) else 0,
        "network_calls": 0,
        "external_network_calls": 0,
        "local_preview_http_requests": 1 if server_started else 0,
        "package_install_calls": 0,
        "build_calls": 0,
        "server_start_calls": 1 if server_started else 0,
        "server_stop_calls": 1 if bool(preview_record.get("server_stopped")) else 0,
        "browser_verification_calls": 1
        if bool(preview_record.get("screenshot_written"))
        else 0,
        "browser_click_actions": browser_click_actions,
        "execution_permission_count": 1 if bool(preview_record.get("attempted")) else 0,
        "local_preview_attempt_only": True,
        "command_output_body_public_return_count": 0,
        "generated_file_content_public_return_count": 0,
        "local_root_path_public_return_count": 0,
    }


def _counts(
    *,
    checks: list[JsonDict],
    preview_record: JsonDict,
    operator_opt_in: bool,
    local_preview_server_allowed: bool,
    browser_verification_allowed: bool,
    status: str,
    browser_runtime_preflight: JsonDict,
) -> JsonDict:
    return {
        "local_preview_attempt_scenario_count": 1
        if bool(preview_record.get("attempted"))
        else 0,
        "check_count": len(checks),
        "passed_check_count": sum(1 for check in checks if check.get("passed") is True),
        "failed_check_count": sum(1 for check in checks if check.get("passed") is not True),
        "operator_opt_in_present_count": 1 if operator_opt_in else 0,
        "local_preview_server_allowed_count": 1 if local_preview_server_allowed else 0,
        "browser_verification_allowed_count": 1 if browser_verification_allowed else 0,
        "browser_runtime_preflight_count": 1 if browser_runtime_preflight else 0,
        "browser_runtime_available_count": 1
        if browser_runtime_preflight.get("available") is True
        else 0,
        "browser_runtime_import_check_count": 1
        if browser_runtime_preflight.get("import_checked") is True
        else 0,
        "browser_runtime_launch_check_count": 1
        if browser_runtime_preflight.get("launch_checked") is True
        else 0,
        "browser_runtime_install_guidance_label_count": len(
            browser_runtime_preflight.get("install_guidance_labels", [])
        ),
        "browser_runtime_install_guidance_hash_count": len(
            browser_runtime_preflight.get("install_guidance_hashes", [])
        ),
        "preview_record_count": 1 if preview_record else 0,
        "preview_server_start_attempt_count": 1
        if bool(preview_record.get("attempted"))
        else 0,
        "preview_server_stop_count": 1
        if bool(preview_record.get("server_stopped"))
        else 0,
        "server_start_count": 1 if bool(preview_record.get("server_started")) else 0,
        "server_stop_count": 1 if bool(preview_record.get("server_stopped")) else 0,
        "browser_verification_attempt_count": 1
        if bool(preview_record.get("attempted")) and browser_verification_allowed
        else 0,
        "browser_verification_pass_count": 1 if status == "passed" else 0,
        "screenshot_evidence_count": 1
        if bool(preview_record.get("screenshot_written"))
        else 0,
        "screenshot_hash_count": 1
        if _is_contract_hash(preview_record.get("screenshot_hash"))
        else 0,
        "screenshot_byte_count": int(preview_record.get("screenshot_byte_count") or 0),
        "visible_marker_count": int(preview_record.get("visible_marker_count") or 0),
        "required_visible_marker_count": len(LOCAL_PREVIEW_REQUIRED_MARKERS),
        "owner_filter_click_attempt_count": 1
        if bool(preview_record.get("owner_filter_click_attempted"))
        else 0,
        "owner_filter_click_pass_count": 1
        if preview_record.get("owner_filter_click_status") == "passed"
        else 0,
        "owner_filter_click_target_label_hash_count": 1
        if _is_contract_hash(
            preview_record.get("owner_filter_click_target_label_hash")
        )
        else 0,
        "owner_filter_before_task_count": int(
            preview_record.get("owner_filter_before_task_count") or 0
        ),
        "owner_filter_after_task_count": int(
            preview_record.get("owner_filter_after_task_count") or 0
        ),
        "owner_filter_changed_count": int(
            preview_record.get("owner_filter_changed_count") or 0
        ),
        "owner_filter_dom_text_return_count": 0,
        "owner_filter_raw_event_return_count": 0,
        "reviewer_decision_click_attempt_count": 1
        if bool(preview_record.get("reviewer_decision_click_attempted"))
        else 0,
        "reviewer_decision_click_pass_count": 1
        if preview_record.get("reviewer_decision_click_status") == "passed"
        else 0,
        "reviewer_decision_click_target_label_hash_count": 1
        if _is_contract_hash(
            preview_record.get("reviewer_decision_click_target_label_hash")
        )
        else 0,
        "reviewer_decision_state_hash_count": sum(
            1
            for value in (
                preview_record.get("reviewer_decision_before_state_hash"),
                preview_record.get("reviewer_decision_after_state_hash"),
            )
            if _is_contract_hash(value)
        ),
        "reviewer_decision_state_changed_count": int(
            preview_record.get("reviewer_decision_state_changed_count") or 0
        ),
        "reviewer_decision_dom_text_return_count": 0,
        "reviewer_decision_raw_event_return_count": 0,
        "preview_pass_count": 1 if status == "passed" else 0,
        "raw_output_public_return_count": 0,
        "file_content_public_return_count": 0,
        "local_root_path_return_count": 0,
        "screenshot_path_return_count": 0,
        "page_text_return_count": 0,
        "target_runtime_call_count": 0,
        "provider_call_count": 0,
        "sdk_import_count": 0,
        "env_value_read_count": 0,
        "subprocess_call_count": 1 if bool(preview_record.get("attempted")) else 0,
        "network_call_count": 0,
        "package_install_call_count": 0,
        "build_call_count": 0,
        "server_start_call_count": 1 if bool(preview_record.get("server_started")) else 0,
    }


def _result(
    *,
    request: TargetRuntimeLocalPreviewAttemptRequest,
    status: str,
    reason: str,
    checks: list[JsonDict],
    build_attempt_projection_hash: str,
    configured: bool,
    preview_record: JsonDict | None = None,
    browser_runtime_preflight: JsonDict | None = None,
) -> TargetRuntimeLocalPreviewAttemptResult:
    record = preview_record or {}
    browser_preflight = browser_runtime_preflight or {}
    claim_boundary = _claim_boundary(
        status=status,
        preview_record=record,
        browser_runtime_preflight=browser_preflight,
    )
    payload_to_hash = {
        "projection_version": TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_VERSION,
        "run_id": safe_public_run_id(request.run_id),
        "mode": request.mode,
        "status": status,
        "reason": reason,
        "local_preview_opt_in_present": request.operator_opt_in,
        "local_preview_server_allowed": request.allow_local_preview_server,
        "browser_verification_allowed": request.allow_browser_verification,
        "local_build_attempt_hash": request.local_build_attempt_hash,
        "local_build_attempt_projection_hash": build_attempt_projection_hash,
        "browser_runtime_preflight": browser_preflight,
        "preview_record": record,
        "claim_boundary": claim_boundary,
    }
    return TargetRuntimeLocalPreviewAttemptResult(
        projection_version=TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_VERSION,
        run_id=safe_public_run_id(request.run_id),
        mode=request.mode,
        status=status,
        reason=reason,
        local_preview_attempted=bool(record.get("attempted")),
        local_preview_opt_in_present=request.operator_opt_in,
        local_preview_server_allowed=request.allow_local_preview_server,
        browser_verification_allowed=request.allow_browser_verification,
        local_build_attempt_hash=request.local_build_attempt_hash,
        local_build_attempt_projection_hash=build_attempt_projection_hash,
        browser_runtime_preflight=browser_preflight,
        local_preview_attempt_hash=stable_contract_hash(payload_to_hash),
        preview_record=record,
        checks=checks,
        counts=_counts(
            checks=checks,
            preview_record=record,
            operator_opt_in=request.operator_opt_in,
            local_preview_server_allowed=request.allow_local_preview_server,
            browser_verification_allowed=request.allow_browser_verification,
            status=status,
            browser_runtime_preflight=browser_preflight,
        ),
        execution_boundary=_execution_boundary(preview_record=record),
        repository_boundary=_repository_boundary(configured=configured),
        claim_boundary=claim_boundary,
    )


class TargetRuntimeLocalPreviewAttemptService:
    """Attempt local preview server/browser verification after explicit opt-in."""

    def __init__(
        self,
        *,
        preview_runner: LocalPreviewRunner | None = None,
        browser_runtime_probe: BrowserRuntimeProbe | None = None,
    ) -> None:
        self._preview_runner = preview_runner or SubprocessLocalPreviewRunner()
        self._browser_runtime_probe = (
            browser_runtime_probe or PlaywrightBrowserRuntimeProbe()
        )

    def create_attempt(
        self,
        request: TargetRuntimeLocalPreviewAttemptRequest,
    ) -> TargetRuntimeLocalPreviewAttemptResult:
        build_attempt_projection = (
            request.local_build_attempt_projection
            if isinstance(request.local_build_attempt_projection, dict)
            else {}
        )
        build_attempt_projection_hash = (
            _projection_hash(build_attempt_projection)
            if build_attempt_projection
            else ""
        )
        workspace_root = Path(request.workspace_root) if request.workspace_root else None
        configured = workspace_root is not None
        checks: list[JsonDict] = []
        failures: list[str] = []

        _check(
            checks,
            failures,
            name="local_preview_attempt_mode_valid",
            passed=request.mode == TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE,
            reason="local_preview_attempt_mode_invalid",
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
            name="local_build_attempt_hash_valid",
            passed=_is_contract_hash(request.local_build_attempt_hash),
            reason="local_build_attempt_hash_missing_or_invalid",
        )
        _check(
            checks,
            failures,
            name="local_build_attempt_projection_present",
            passed=bool(build_attempt_projection),
            reason="local_build_attempt_projection_missing",
        )
        _check(
            checks,
            failures,
            name="local_build_attempt_projection_version",
            passed=build_attempt_projection.get("projection_version")
            == TARGET_RUNTIME_LOCAL_BUILD_ATTEMPT_VERSION,
            reason="local_build_attempt_projection_version_invalid",
        )
        _check(
            checks,
            failures,
            name="local_build_attempt_run_matches",
            passed=build_attempt_projection.get("run_id")
            == safe_public_run_id(request.run_id),
            reason="local_build_attempt_run_mismatch",
        )
        _check(
            checks,
            failures,
            name="local_build_attempt_hash_matches_projection",
            passed=request.local_build_attempt_hash
            == build_attempt_projection.get("local_build_attempt_hash"),
            reason="local_build_attempt_hash_mismatch",
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
                build_attempt_projection_hash=build_attempt_projection_hash,
                configured=configured,
            )

        if (
            not request.operator_opt_in
            or not request.allow_local_preview_server
            or not request.allow_browser_verification
        ):
            blocked_checks = [
                *checks,
                {
                    "name": "local_preview_operator_opt_in_present",
                    "passed": request.operator_opt_in,
                    "reason": ""
                    if request.operator_opt_in
                    else "local_preview_opt_in_required",
                },
                {
                    "name": "local_preview_server_allowed",
                    "passed": request.allow_local_preview_server,
                    "reason": ""
                    if request.allow_local_preview_server
                    else "local_preview_server_flag_required",
                },
                {
                    "name": "browser_verification_allowed",
                    "passed": request.allow_browser_verification,
                    "reason": ""
                    if request.allow_browser_verification
                    else "browser_verification_flag_required",
                },
            ]
            return _result(
                request=request,
                status="blocked",
                reason="local_preview_opt_in_required",
                checks=blocked_checks,
                build_attempt_projection_hash=build_attempt_projection_hash,
                configured=configured,
            )

        _check(
            checks,
            failures,
            name="local_build_attempt_passed",
            passed=build_attempt_projection.get("status") == "passed"
            and build_attempt_projection.get("local_build_attempted") is True,
            reason="local_build_attempt_status_invalid",
        )

        if failures:
            return _result(
                request=request,
                status="blocked",
                reason=failures[0],
                checks=checks,
                build_attempt_projection_hash=build_attempt_projection_hash,
                configured=configured,
            )

        assert workspace_root is not None
        try:
            app_dir = _app_dir(workspace_root=workspace_root, run_id=request.run_id)
            screenshot_path = _screenshot_path(
                workspace_root=workspace_root,
                run_id=request.run_id,
            )
        except PathBoundaryError:
            return _result(
                request=request,
                status="blocked",
                reason="local_preview_path_traversal",
                checks=[
                    *checks,
                    {
                        "name": "local_preview_workspace_path_safe",
                        "passed": False,
                        "reason": "local_preview_path_traversal",
                    },
                ],
                build_attempt_projection_hash=build_attempt_projection_hash,
                configured=configured,
            )
        if not app_dir.exists() or not app_dir.is_dir():
            return _result(
                request=request,
                status="blocked",
                reason="local_preview_workspace_missing",
                checks=[
                    *checks,
                    {
                        "name": "local_preview_workspace_exists",
                        "passed": False,
                        "reason": "local_preview_workspace_missing",
                    },
                ],
                build_attempt_projection_hash=build_attempt_projection_hash,
                configured=configured,
            )
        if not (app_dir / "package.json").is_file():
            return _result(
                request=request,
                status="blocked",
                reason="local_preview_package_json_missing",
                checks=[
                    *checks,
                    {
                        "name": "local_preview_package_json_exists",
                        "passed": False,
                        "reason": "local_preview_package_json_missing",
                    },
                ],
                build_attempt_projection_hash=build_attempt_projection_hash,
                configured=configured,
            )

        browser_runtime_preflight: JsonDict = {}
        if request.require_browser_runtime_preflight:
            browser_runtime_preflight = (
                self._browser_runtime_probe.probe().to_public_record()
            )
            if browser_runtime_preflight.get("available") is not True:
                reason = str(
                    browser_runtime_preflight.get(
                        "reason",
                        "browser_runtime_preflight_unavailable",
                    )
                )
                return _result(
                    request=request,
                    status="environment_blocked",
                    reason=reason,
                    checks=[
                        *checks,
                        {
                            "name": "browser_runtime_preflight_available",
                            "passed": False,
                            "reason": reason,
                        },
                    ],
                    build_attempt_projection_hash=build_attempt_projection_hash,
                    configured=configured,
                    browser_runtime_preflight=browser_runtime_preflight,
                )

        outcome = self._preview_runner.run(
            app_dir=app_dir,
            screenshot_path=screenshot_path,
            timeout_seconds=request.preview_timeout_seconds,
        )
        record = outcome.to_public_record()
        if outcome.server_started and not outcome.server_stopped:
            record = {**record, "server_stopped": True}
        if (
            outcome.screenshot_written
            and outcome.visible_marker_count >= len(LOCAL_PREVIEW_REQUIRED_MARKERS)
        ):
            status = "passed"
            reason = "local_fixture_app_preview_verified"
        elif outcome.reason in {
            "browser_verification_runtime_unavailable",
            "local_package_manager_unavailable",
        }:
            status = "environment_blocked"
            reason = outcome.reason
        else:
            status = "failed"
            reason = outcome.reason
        return _result(
            request=request,
            status=status,
            reason=reason,
            checks=[
                *checks,
                {
                    "name": "local_preview_operator_opt_in_present",
                    "passed": True,
                    "reason": "",
                },
                {
                    "name": "local_preview_server_allowed",
                    "passed": True,
                    "reason": "",
                },
                {
                    "name": "browser_verification_allowed",
                    "passed": True,
                    "reason": "",
                },
                {
                    "name": "browser_runtime_preflight_available",
                    "passed": browser_runtime_preflight.get("available", True)
                    is True,
                    "reason": "",
                },
                {
                    "name": "local_preview_attempt_recorded",
                    "passed": bool(record.get("attempted")),
                    "reason": ""
                    if record.get("attempted")
                    else "local_preview_attempt_not_recorded",
                },
            ],
            build_attempt_projection_hash=build_attempt_projection_hash,
            configured=configured,
            preview_record=record,
            browser_runtime_preflight=browser_runtime_preflight,
        )


def default_target_runtime_local_preview_attempt_service() -> (
    TargetRuntimeLocalPreviewAttemptService
):
    return TargetRuntimeLocalPreviewAttemptService()


def create_target_runtime_local_preview_attempt(
    *,
    request: TargetRuntimeLocalPreviewAttemptRequest,
    service: TargetRuntimeLocalPreviewAttemptService | None = None,
    preview_runner: LocalPreviewRunner | None = None,
    browser_runtime_probe: BrowserRuntimeProbe | None = None,
) -> TargetRuntimeLocalPreviewAttemptResult:
    selected_service = service or TargetRuntimeLocalPreviewAttemptService(
        preview_runner=preview_runner,
        browser_runtime_probe=browser_runtime_probe,
    )
    return selected_service.create_attempt(request)


__all__ = [
    "LOCAL_PREVIEW_REQUIRED_MARKERS",
    "BROWSER_RUNTIME_INSTALL_GUIDANCE_LABELS",
    "BROWSER_RUNTIME_OFFICIAL_DOC_LABELS",
    "BROWSER_RUNTIME_PREFLIGHT_VERSION",
    "TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_MODE",
    "TARGET_RUNTIME_LOCAL_PREVIEW_ATTEMPT_VERSION",
    "BrowserRuntimePreflightResult",
    "BrowserRuntimeProbe",
    "LocalPreviewOutcome",
    "LocalPreviewRunner",
    "PlaywrightBrowserRuntimeProbe",
    "SubprocessLocalPreviewRunner",
    "TargetRuntimeLocalPreviewAttemptRequest",
    "TargetRuntimeLocalPreviewAttemptResult",
    "TargetRuntimeLocalPreviewAttemptService",
    "create_target_runtime_local_preview_attempt",
    "default_target_runtime_local_preview_attempt_service",
]

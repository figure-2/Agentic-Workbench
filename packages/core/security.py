"""Safety helpers for logs and public artifacts."""

from __future__ import annotations

import re
from typing import Any


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|client[_-]?secret)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(postgres|postgresql|mysql|mongodb(?:\+srv)?|redis)://[^'\"\s]+"),
    re.compile(r"(?i)(xox[baprs]-[A-Za-z0-9-]+)"),
    re.compile(r"(?i)(sk-[A-Za-z0-9_-]{16,})"),
]

PII_PATTERNS = [
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    re.compile(r"(?<!\d)(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}(?!\d)"),
]

PATH_PATTERNS = [
    re.compile(r"(?i)\b[A-Z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n\s]*"),
    re.compile(r"(?<!\w)/(?:Users|home|var|etc|tmp|mnt|opt|root)(?:/[^\s'\"<>|]+)+"),
]

PUBLIC_HASH_PATTERN = re.compile(r"\b[a-f0-9]{32,64}\b", re.IGNORECASE)

SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|client[_-]?secret|authorization|cookie|set-cookie|raw[_-]?content|"
    r"full[_-]?prompt|full[_-]?search|private[_-]?corpus)"
)


def redact_text(value: str) -> str:
    """Redact likely secrets, PII, and local paths from text while preserving context."""
    protected_hashes: dict[str, str] = {}

    def protect_hash(match: re.Match[str]) -> str:
        placeholder = f"__PUBLIC_HASH_{len(protected_hashes)}__"
        protected_hashes[placeholder] = match.group(0)
        return placeholder

    redacted = PUBLIC_HASH_PATTERN.sub(protect_hash, value)
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    for pattern in PII_PATTERNS:
        redacted = pattern.sub("[REDACTED_PII]", redacted)
    for pattern in PATH_PATTERNS:
        redacted = pattern.sub("[REDACTED_PATH]", redacted)
    for placeholder, original in protected_hashes.items():
        redacted = redacted.replace(placeholder, original)
    return redacted


def redact_secrets(value: Any) -> Any:
    """Recursively redact likely secrets from JSON-like values."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item) for item in value)
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            if isinstance(key, str) and SENSITIVE_KEY_PATTERN.search(key):
                redacted[key] = "[REDACTED_SECRET]"
            else:
                redacted[key] = redact_secrets(item)
        return redacted
    return value

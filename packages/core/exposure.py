"""Public artifact exposure checks."""

from __future__ import annotations

from typing import Any

from .security import redact_secrets


FORBIDDEN_PUBLIC_KEYS = {
    "raw_content",
    "rawContent",
    "full_prompt",
    "fullPrompt",
    "prompt_messages",
    "messages",
    "full_search_result",
    "fullSearchResult",
    "search_results",
    "private_corpus",
    "privateCorpus",
}


def find_forbidden_public_keys(value: Any, *, prefix: str = "") -> list[str]:
    """Return JSON paths containing fields that must not appear in public artifacts."""
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if key in FORBIDDEN_PUBLIC_KEYS:
                findings.append(path)
            findings.extend(find_forbidden_public_keys(item, prefix=path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            findings.extend(find_forbidden_public_keys(item, prefix=path))
    return findings


def assert_no_forbidden_public_keys(value: Any) -> None:
    """Raise if a public artifact payload contains raw prompt/search/corpus fields."""
    findings = find_forbidden_public_keys(value)
    if findings:
        raise ValueError(f"forbidden public artifact keys found: {', '.join(findings)}")


def sanitize_public_payload(value: Any) -> Any:
    """Drop forbidden public fields and redact sensitive values recursively."""
    if isinstance(value, dict):
        sanitized = {
            key: sanitize_public_payload(item)
            for key, item in value.items()
            if key not in FORBIDDEN_PUBLIC_KEYS
        }
        return redact_secrets(sanitized)
    if isinstance(value, list):
        return [sanitize_public_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_public_payload(item) for item in value)
    return redact_secrets(value)

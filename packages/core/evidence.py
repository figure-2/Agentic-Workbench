"""Evidence sanitization for planner/research artifacts."""

from __future__ import annotations

from typing import Any

from .security import redact_secrets


MAX_SNIPPET_CHARS = 280


def sanitize_evidence_item(item: dict[str, Any], *, max_chars: int = MAX_SNIPPET_CHARS) -> dict[str, Any]:
    """Keep public evidence concise and remove raw content fields."""
    title = str(item.get("title") or "Untitled evidence")
    url = str(item.get("url") or "")
    content = str(item.get("summary") or item.get("snippet") or item.get("content") or "")
    snippet = content[:max_chars].strip()
    if len(content) > max_chars:
        snippet = f"{snippet}..."
    return redact_secrets(
        {
            "title": title,
            "url": url,
            "snippet": snippet,
            "score": item.get("score"),
        }
    )


def sanitize_evidence(items: list[dict[str, Any]], *, max_chars: int = MAX_SNIPPET_CHARS) -> list[dict[str, Any]]:
    """Sanitize a list of research evidence for public artifacts."""
    return [sanitize_evidence_item(item, max_chars=max_chars) for item in items]

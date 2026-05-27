"""Path boundary helpers for artifact and workspace access."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote


class PathBoundaryError(ValueError):
    """Raised when a requested path escapes the configured root."""


def resolve_within_root(root: str | Path, requested_path: str | Path) -> Path:
    """Resolve a user-supplied relative path and require it to stay inside root."""
    root_path = Path(root).resolve()
    raw_path = str(requested_path).strip()
    decoded_path = unquote(raw_path)
    candidate = Path(decoded_path)

    if not decoded_path:
        raise PathBoundaryError("requested path is required")
    if "\x00" in decoded_path:
        raise PathBoundaryError("null byte is not allowed in requested path")
    if candidate.is_absolute() or candidate.drive:
        raise PathBoundaryError("absolute paths are not allowed")

    resolved = (root_path / candidate).resolve()
    try:
        resolved.relative_to(root_path)
    except ValueError as exc:
        raise PathBoundaryError("requested path escapes root") from exc
    return resolved


def normalize_public_relative_path(requested_path: str | Path) -> str:
    """Normalize an artifact path and require it to be relative and non-escaping."""
    root = Path.cwd() / "__agentic_workbench_path_boundary__"
    resolved = resolve_within_root(root, requested_path)
    relative = resolved.relative_to(root)
    return relative.as_posix()

import pytest

from packages.core.pathing import (
    PathBoundaryError,
    normalize_public_relative_path,
    resolve_within_root,
)


@pytest.mark.parametrize(
    "requested_path",
    [
        "../secret.txt",
        r"..\secret.txt",
        "%2e%2e/secret.txt",
        r"F:\File\02_Project\.env",
        "/home/user/.env",
        "",
        "safe/\x00.txt",
    ],
)
def test_resolve_within_root_rejects_escaping_or_unsafe_paths(tmp_path, requested_path):
    with pytest.raises(PathBoundaryError):
        resolve_within_root(tmp_path, requested_path)


def test_resolve_within_root_allows_normalized_relative_path(tmp_path):
    resolved = resolve_within_root(tmp_path, "subdir/../ok.txt")
    assert resolved == tmp_path.resolve() / "ok.txt"


def test_public_relative_path_normalizes_safe_paths():
    assert normalize_public_relative_path("backend/../backend/main.py") == "backend/main.py"


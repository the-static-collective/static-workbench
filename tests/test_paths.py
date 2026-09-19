from pathlib import Path

import pytest

from static_workbench.paths import PathOutsideRoot, resolve_under_root


def test_resolve_under_root_allows_relative_child(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    child = root / "folder" / "file.txt"
    child.parent.mkdir()
    child.write_text("hello", encoding="utf-8")

    assert resolve_under_root(root, "folder/file.txt") == child.resolve()


def test_resolve_under_root_rejects_parent_traversal(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()

    with pytest.raises(PathOutsideRoot):
        resolve_under_root(root, "../outside.txt")


def test_resolve_under_root_rejects_absolute_path(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()

    with pytest.raises(PathOutsideRoot):
        resolve_under_root(root, str((tmp_path / "outside.txt").resolve()))


def test_resolve_under_root_rejects_symlink_escape(tmp_path: Path):
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_text("secret", encoding="utf-8")
    (root / "link").symlink_to(outside, target_is_directory=True)

    with pytest.raises(PathOutsideRoot):
        resolve_under_root(root, "link/secret.txt")

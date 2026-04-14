"""Filesystem scanning — find files not registered in the database."""

from __future__ import annotations

from pathlib import Path


def find_untracked_files(
    project_path: Path,
    registered_paths: set[str],
    ignore_patterns: set[str] | None = None,
) -> list[Path]:
    """Walk a project folder and return files not in the database.

    Args:
        project_path: Absolute path to the project folder.
        registered_paths: Set of relative file paths already in DataFile table.
        ignore_patterns: Glob patterns to skip (e.g., {"*.log", ".git/**"}).

    Returns:
        List of Path objects (relative to project_path) not yet registered.
    """
    if ignore_patterns is None:
        ignore_patterns = {".git", "__pycache__", "*.pyc", ".gitignore"}

    untracked = []

    # TODO: implement walking logic
    # - Walk project_path recursively
    # - Skip directories/files matching ignore_patterns
    # - Compare each file's relative path to registered_paths
    # - Return unmatched files

    return untracked

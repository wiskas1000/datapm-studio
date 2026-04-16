"""Filesystem scanning — find files not registered in the database."""

from __future__ import annotations

from pathlib import Path

# Directories to always skip when walking project folders.
DEFAULT_IGNORE_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".mypy_cache"}

# File patterns to always skip.
DEFAULT_IGNORE_SUFFIXES = {".pyc", ".pyo"}

# Specific filenames to always skip (datapm metadata, etc.).
DEFAULT_IGNORE_FILES = {"project.json"}


def find_untracked_files(
    project_path: Path,
    registered_paths: set[str],
    ignore_dirs: set[str] | None = None,
) -> list[Path]:
    """Walk a project folder and return files not in the database.

    Args:
        project_path: Absolute path to the project folder.
        registered_paths: Set of relative file paths already in the DataFile table.
        ignore_dirs: Directory names to skip (defaults to common dev dirs).

    Returns:
        List of Path objects (relative to project_path) not yet registered.
        Returns empty list if the project path doesn't exist.
    """
    if not project_path.is_dir():
        return []

    if ignore_dirs is None:
        ignore_dirs = DEFAULT_IGNORE_DIRS

    untracked: list[Path] = []

    for child in sorted(project_path.rglob("*")):
        if not child.is_file():
            continue

        # Skip files inside ignored directories.
        if any(part in ignore_dirs for part in child.relative_to(project_path).parts):
            continue

        # Skip ignored file suffixes and specific filenames.
        if child.suffix in DEFAULT_IGNORE_SUFFIXES:
            continue
        if child.name in DEFAULT_IGNORE_FILES:
            continue

        rel = child.relative_to(project_path)
        # Compare using forward-slash POSIX paths for consistency.
        if rel.as_posix() not in registered_paths:
            untracked.append(rel)

    return untracked

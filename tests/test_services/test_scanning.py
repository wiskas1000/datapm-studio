"""Tests for the filesystem scanning service."""

from __future__ import annotations

from pathlib import Path

from datapm_studio.services.scanning import find_untracked_files


class TestFindUntrackedFiles:
    """Tests for find_untracked_files()."""

    def test_empty_dir_returns_empty(self, tmp_path):
        """An empty project folder has no untracked files."""
        result = find_untracked_files(tmp_path, set())
        assert result == []

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        """A nonexistent path returns an empty list (no crash)."""
        missing = tmp_path / "does-not-exist"
        result = find_untracked_files(missing, set())
        assert result == []

    def test_finds_untracked_file(self, tmp_path):
        """A file on disk but not in the DB should be returned."""
        (tmp_path / "data.csv").write_text("a,b,c")
        result = find_untracked_files(tmp_path, set())
        assert Path("data.csv") in result

    def test_registered_file_not_returned(self, tmp_path):
        """A file already in the DB should not be returned."""
        (tmp_path / "data.csv").write_text("a,b,c")
        result = find_untracked_files(tmp_path, {"data.csv"})
        assert result == []

    def test_mixed_tracked_and_untracked(self, tmp_path):
        """Only unregistered files are returned."""
        (tmp_path / "tracked.csv").write_text("ok")
        (tmp_path / "untracked.xlsx").write_text("new")

        result = find_untracked_files(tmp_path, {"tracked.csv"})
        assert len(result) == 1
        assert Path("untracked.xlsx") in result

    def test_skips_git_directory(self, tmp_path):
        """Files inside .git should be ignored."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git stuff")

        result = find_untracked_files(tmp_path, set())
        assert result == []

    def test_skips_pycache_directory(self, tmp_path):
        """Files inside __pycache__ should be ignored."""
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "module.cpython-310.pyc").write_text("bytecode")

        result = find_untracked_files(tmp_path, set())
        assert result == []

    def test_skips_pyc_files(self, tmp_path):
        """*.pyc files should be ignored even outside __pycache__."""
        (tmp_path / "module.pyc").write_text("bytecode")
        result = find_untracked_files(tmp_path, set())
        assert result == []

    def test_nested_files(self, tmp_path):
        """Files in subdirectories should use POSIX relative paths."""
        sub = tmp_path / "src" / "scripts"
        sub.mkdir(parents=True)
        (sub / "run.py").write_text("print('hi')")

        result = find_untracked_files(tmp_path, set())
        assert Path("src/scripts/run.py") in result

    def test_nested_registered_with_posix_path(self, tmp_path):
        """Registered paths use forward slashes (POSIX style)."""
        sub = tmp_path / "data" / "raw"
        sub.mkdir(parents=True)
        (sub / "file.csv").write_text("a,b")

        result = find_untracked_files(tmp_path, {"data/raw/file.csv"})
        assert result == []

    def test_custom_ignore_dirs(self, tmp_path):
        """Custom ignore_dirs replaces the defaults."""
        custom_dir = tmp_path / "build"
        custom_dir.mkdir()
        (custom_dir / "output.bin").write_text("binary")
        (tmp_path / "data.csv").write_text("a,b")

        result = find_untracked_files(tmp_path, set(), ignore_dirs={"build"})
        assert Path("data.csv") in result
        assert not any("build" in str(p) for p in result)

    def test_skips_project_json(self, tmp_path):
        """project.json (datapm metadata) should always be ignored."""
        (tmp_path / "project.json").write_text("{}")
        (tmp_path / "data.csv").write_text("a,b")

        result = find_untracked_files(tmp_path, set())
        assert Path("data.csv") in result
        assert Path("project.json") not in result

    def test_results_sorted(self, tmp_path):
        """Results should be in sorted order."""
        (tmp_path / "b.csv").write_text("b")
        (tmp_path / "a.csv").write_text("a")
        (tmp_path / "c.csv").write_text("c")

        result = find_untracked_files(tmp_path, set())
        assert result == sorted(result)

    def test_skips_directories_themselves(self, tmp_path):
        """Directories should not appear in results, only files."""
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "file.txt").write_text("content")

        result = find_untracked_files(tmp_path, set())
        assert all(r.suffix or r.name != "subdir" for r in result)
        assert Path("subdir/file.txt") in result

"""Tests for the project routes."""

from __future__ import annotations

from unittest.mock import patch

from data_project_manager.db.repositories.project import (
    ProjectRepository,
    ProjectRootRepository,
)


def test_project_list_empty(client):
    """An empty database shows the empty-state card."""
    r = client.get("/projects/")
    assert r.status_code == 200
    assert b"No projects yet" in r.data


def test_project_list_with_data(client, db_conn):
    """Projects in the database render in the table."""
    repo = ProjectRepository(db_conn)
    repo.create(title="Alpha Report", slug="2026-04-15-alpha-report", is_adhoc=False)
    repo.create(title="Beta Analysis", slug="2026-04-15-beta-analysis", is_adhoc=True)

    r = client.get("/projects/")
    assert r.status_code == 200
    assert b"Alpha Report" in r.data
    assert b"Beta Analysis" in r.data
    assert b"No projects yet" not in r.data


def test_project_list_shows_status_badge(client, db_conn):
    """Status values render with badge CSS classes."""
    repo = ProjectRepository(db_conn)
    repo.create(
        title="Active Project", slug="2026-04-15-active-project", is_adhoc=False
    )

    r = client.get("/projects/")
    assert b"badge-active" in r.data


def test_project_detail_not_found(client):
    """Requesting a non-existent project slug returns 404."""
    r = client.get("/projects/nonexistent-slug")
    assert r.status_code == 404


class TestProjectListCapAndToggle:
    """Issue #87: cap at 15, hide done/archived by default, More link."""

    def test_hides_done_and_archived_by_default(self, client, db_conn):
        repo = ProjectRepository(db_conn)
        active = repo.create(
            title="Active Work", slug="2026-04-15-active-work", is_adhoc=False
        )
        done = repo.create(
            title="Finished Thing", slug="2026-04-15-finished-thing", is_adhoc=False
        )
        archived = repo.create(
            title="Old Archive", slug="2026-04-15-old-archive", is_adhoc=False
        )
        repo.update(done.id, status="done")
        repo.update(archived.id, status="archived")

        r = client.get("/projects/")
        assert b"Active Work" in r.data
        assert b"Finished Thing" not in r.data
        assert b"Old Archive" not in r.data
        _ = active  # silence unused

    def test_include_done_shows_everything(self, client, db_conn):
        repo = ProjectRepository(db_conn)
        repo.create(title="Active", slug="2026-04-15-active", is_adhoc=False)
        done = repo.create(title="Done Job", slug="2026-04-15-done-job", is_adhoc=False)
        repo.update(done.id, status="done")

        r = client.get("/projects/?include_done=1")
        assert b"Active" in r.data
        assert b"Done Job" in r.data
        assert b"checked" in r.data  # checkbox rendered checked

    def test_caps_at_fifteen(self, client, db_conn):
        repo = ProjectRepository(db_conn)
        for i in range(20):
            repo.create(
                title=f"Project {i:02d}",
                slug=f"2026-04-15-project-{i:02d}",
                is_adhoc=False,
            )

        r = client.get("/projects/")
        body = r.data.decode()
        # Most-recent 15 survive; the 5 oldest are truncated.
        for i in range(5, 20):
            assert f"Project {i:02d}" in body
        for i in range(0, 5):
            assert f"Project {i:02d}" not in body

    def test_more_link_appears_only_when_truncated(self, client, db_conn):
        repo = ProjectRepository(db_conn)
        for i in range(10):
            repo.create(title=f"P{i}", slug=f"2026-04-15-p{i}-only", is_adhoc=False)

        r = client.get("/projects/")
        assert b"More \xe2\x86\x92" not in r.data  # "More →" not present

        for i in range(10, 20):
            repo.create(title=f"P{i}", slug=f"2026-04-15-p{i}-only", is_adhoc=False)
        r = client.get("/projects/")
        assert b"More \xe2\x86\x92" in r.data

    def test_open_folder_icon_rendered_only_for_rooted_projects(
        self, client, db_conn, tmp_path
    ):
        root = ProjectRootRepository(db_conn).create(
            name="test-root", absolute_path=str(tmp_path), is_default=True
        )
        folder = tmp_path / "2026-04-15-rooted"
        folder.mkdir()
        ProjectRepository(db_conn).create(
            title="Rooted",
            slug="2026-04-15-rooted",
            is_adhoc=False,
            root_id=root.id,
            relative_path="2026-04-15-rooted",
        )
        ProjectRepository(db_conn).create(
            title="Adhoc", slug="2026-04-15-adhoc", is_adhoc=True
        )

        r = client.get("/projects/")
        body = r.data.decode()
        # One open-folder button for the rooted project, none for adhoc.
        assert body.count('class="btn-icon open-folder-btn"') == 1
        assert "/projects/2026-04-15-rooted/open-folder" in body
        assert "/projects/2026-04-15-adhoc/open-folder" not in body

    def test_empty_active_message_when_only_done(self, client, db_conn):
        repo = ProjectRepository(db_conn)
        done = repo.create(
            title="Only Done", slug="2026-04-15-only-done", is_adhoc=False
        )
        repo.update(done.id, status="done")

        r = client.get("/projects/")
        assert b"No active projects" in r.data


class TestOpenFolder:
    """Issue #88: POST /projects/<slug>/open-folder dispatch."""

    def _make_rooted_project(self, db_conn, tmp_path, slug="2026-04-15-demo"):
        root = ProjectRootRepository(db_conn).create(
            name="test-root", absolute_path=str(tmp_path), is_default=True
        )
        folder = tmp_path / slug
        folder.mkdir()
        ProjectRepository(db_conn).create(
            title="Demo",
            slug=slug,
            is_adhoc=False,
            root_id=root.id,
            relative_path=slug,
        )
        return folder

    def test_dispatches_to_xdg_open_on_linux(self, client, db_conn, tmp_path):
        folder = self._make_rooted_project(db_conn, tmp_path)

        with (
            patch("datapm_studio.routes.projects.sys") as mock_sys,
            patch("datapm_studio.routes.projects.subprocess.Popen") as mock_popen,
        ):
            mock_sys.platform = "linux"
            r = client.post("/projects/2026-04-15-demo/open-folder")

        assert r.status_code == 204
        mock_popen.assert_called_once()
        argv = mock_popen.call_args[0][0]
        assert argv[0] == "xdg-open"
        assert argv[1] == str(folder.resolve())

    def test_404_for_unknown_slug(self, client):
        r = client.post("/projects/does-not-exist/open-folder")
        assert r.status_code == 404

    def test_400_for_adhoc_project_without_folder(self, client, db_conn):
        ProjectRepository(db_conn).create(
            title="Adhoc", slug="2026-04-15-adhoc", is_adhoc=True
        )
        r = client.post("/projects/2026-04-15-adhoc/open-folder")
        assert r.status_code == 400

    def test_404_when_folder_missing_on_disk(self, client, db_conn, tmp_path):
        root = ProjectRootRepository(db_conn).create(
            name="test-root", absolute_path=str(tmp_path), is_default=True
        )
        ProjectRepository(db_conn).create(
            title="Ghost",
            slug="2026-04-15-ghost",
            is_adhoc=False,
            root_id=root.id,
            relative_path="2026-04-15-ghost",
        )
        r = client.post("/projects/2026-04-15-ghost/open-folder")
        assert r.status_code == 404

    def test_rejects_path_escape_via_relative_path(self, client, db_conn, tmp_path):
        root = ProjectRootRepository(db_conn).create(
            name="test-root",
            absolute_path=str(tmp_path / "inside"),
            is_default=True,
        )
        (tmp_path / "inside").mkdir()
        escape_target = tmp_path / "outside"
        escape_target.mkdir()
        ProjectRepository(db_conn).create(
            title="Escape",
            slug="2026-04-15-escape",
            is_adhoc=False,
            root_id=root.id,
            relative_path="../outside",
        )
        r = client.post("/projects/2026-04-15-escape/open-folder")
        assert r.status_code == 400

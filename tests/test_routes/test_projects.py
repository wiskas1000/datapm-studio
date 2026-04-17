"""Tests for the project routes."""

from __future__ import annotations

from data_project_manager.db.repositories.project import ProjectRepository


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

    def test_empty_active_message_when_only_done(self, client, db_conn):
        repo = ProjectRepository(db_conn)
        done = repo.create(
            title="Only Done", slug="2026-04-15-only-done", is_adhoc=False
        )
        repo.update(done.id, status="done")

        r = client.get("/projects/")
        assert b"No active projects" in r.data

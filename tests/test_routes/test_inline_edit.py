"""Tests for inline editing of project scalar fields."""

from __future__ import annotations

from data_project_manager.db.repositories.project import ProjectRepository


def _seed_project(db_conn) -> str:
    """Create a test project and return its slug."""
    repo = ProjectRepository(db_conn)
    project = repo.create(
        title="Inline Edit Test",
        slug="inline-edit-test",
        status="active",
        domain="testing",
        description="Original description",
        expected_start="2026-06-01",
        expected_end="2026-06-30",
        estimated_hours=20.0,
    )
    return project.slug


class TestEditFieldGet:
    """GET /projects/<slug>/edit/<field> returns the edit form partial."""

    def test_get_edit_status(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/edit/status")
        assert resp.status_code == 200
        assert b"<select" in resp.data
        assert b"active" in resp.data
        assert b"paused" in resp.data
        assert b"done" in resp.data
        assert b"archived" in resp.data

    def test_get_edit_domain(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/edit/domain")
        assert resp.status_code == 200
        assert b'type="text"' in resp.data
        assert b"testing" in resp.data

    def test_get_edit_description(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/edit/description")
        assert resp.status_code == 200
        assert b"<textarea" in resp.data
        assert b"Original description" in resp.data

    def test_get_edit_external_url(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/edit/external_url")
        assert resp.status_code == 200
        assert b'type="url"' in resp.data

    def test_get_edit_date_field(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/edit/expected_start")
        assert resp.status_code == 200
        assert b'type="date"' in resp.data
        assert b"2026-06-01" in resp.data

    def test_get_edit_estimated_hours(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/edit/estimated_hours")
        assert resp.status_code == 200
        assert b'type="number"' in resp.data
        assert b"20.0" in resp.data

    def test_get_edit_unknown_field_400(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/edit/nonexistent")
        assert resp.status_code == 400

    def test_get_edit_missing_project_404(self, client):
        resp = client.get("/projects/no-such-slug/edit/status")
        assert resp.status_code == 404


class TestEditFieldPost:
    """POST /projects/<slug>/edit/<field> saves and returns read partial."""

    def test_update_status(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(f"/projects/{slug}/edit/status", data={"value": "paused"})
        assert resp.status_code == 200
        assert b"paused" in resp.data

        # Verify persisted
        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.status == "paused"

    def test_update_status_to_done_redirects_to_closeout(self, client, db_conn):
        """Setting status to 'done' should redirect to the close-out checklist."""
        slug = _seed_project(db_conn)
        resp = client.post(f"/projects/{slug}/edit/status", data={"value": "done"})
        assert resp.status_code == 200
        assert resp.headers.get("HX-Redirect") == f"/projects/{slug}/closeout"

        # Verify status was still persisted
        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.status == "done"

    def test_update_domain(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(f"/projects/{slug}/edit/domain", data={"value": "analytics"})
        assert resp.status_code == 200
        assert b"analytics" in resp.data

        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.domain == "analytics"

    def test_update_description(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(
            f"/projects/{slug}/edit/description",
            data={"value": "Updated description"},
        )
        assert resp.status_code == 200
        assert b"Updated description" in resp.data

        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.description == "Updated description"

    def test_update_external_url(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(
            f"/projects/{slug}/edit/external_url",
            data={"value": "https://example.com/board"},
        )
        assert resp.status_code == 200
        assert b"https://example.com/board" in resp.data

        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.external_url == "https://example.com/board"

    def test_update_expected_start(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(
            f"/projects/{slug}/edit/expected_start",
            data={"value": "2026-05-15"},
        )
        assert resp.status_code == 200

        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.expected_start == "2026-05-15"

    def test_update_estimated_hours(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(
            f"/projects/{slug}/edit/estimated_hours",
            data={"value": "35.5"},
        )
        assert resp.status_code == 200

        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.estimated_hours == 35.5

    def test_clear_field_to_none(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(f"/projects/{slug}/edit/domain", data={"value": ""})
        assert resp.status_code == 200

        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.domain is None

    def test_invalid_estimated_hours(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(
            f"/projects/{slug}/edit/estimated_hours",
            data={"value": "not-a-number"},
        )
        assert resp.status_code == 200
        assert b"Must be a number" in resp.data

        # Value unchanged
        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.estimated_hours == 20.0


class TestDateValidation:
    """Date ordering validation for inline edits."""

    def test_expected_end_before_start_rejected(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(
            f"/projects/{slug}/edit/expected_end",
            data={"value": "2026-05-01"},
        )
        assert resp.status_code == 200
        assert b"cannot be before" in resp.data

        # Value unchanged
        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.expected_end == "2026-06-30"

    def test_expected_start_after_end_rejected(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(
            f"/projects/{slug}/edit/expected_start",
            data={"value": "2026-07-15"},
        )
        assert resp.status_code == 200
        assert b"cannot be after" in resp.data

    def test_equal_dates_allowed(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(
            f"/projects/{slug}/edit/expected_end",
            data={"value": "2026-06-01"},
        )
        assert resp.status_code == 200
        assert b"cannot be before" not in resp.data

        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.expected_end == "2026-06-01"

    def test_clear_date_allowed(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.post(f"/projects/{slug}/edit/expected_end", data={"value": ""})
        assert resp.status_code == 200

        project = ProjectRepository(db_conn).get_by_slug(slug)
        assert project.expected_end is None


class TestReadField:
    """GET /projects/<slug>/field/<field> returns the read-mode partial."""

    def test_read_field_status(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/field/status")
        assert resp.status_code == 200
        assert b"active" in resp.data
        assert b"badge" in resp.data

    def test_read_field_domain(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/field/domain")
        assert resp.status_code == 200
        assert b"testing" in resp.data
        assert b"Edit" in resp.data

    def test_read_field_description(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/field/description")
        assert resp.status_code == 200
        assert b"Original description" in resp.data

    def test_read_field_unknown_400(self, client, db_conn):
        slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/field/nonexistent")
        assert resp.status_code == 400

    def test_read_field_missing_project_404(self, client):
        resp = client.get("/projects/no-such/field/status")
        assert resp.status_code == 404

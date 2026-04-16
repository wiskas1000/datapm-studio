"""Tests for deliverable routes on the project detail page."""

from __future__ import annotations

from data_project_manager.db.repositories.deliverable import DeliverableRepository
from data_project_manager.db.repositories.project import ProjectRepository


def _create_project(conn, **overrides):
    """Create a minimal project and return it."""
    defaults = {
        "title": "Test Deliverables",
        "slug": "test-deliverables",
        "status": "active",
    }
    defaults.update(overrides)
    return ProjectRepository(conn).create(**defaults)


class TestDeliverablesSection:
    """Tests for the deliverables section on the project detail page."""

    def test_detail_shows_deliverables_section(self, client, db_conn):
        """Project detail page should include the deliverables section."""
        _create_project(db_conn)
        resp = client.get("/projects/test-deliverables")
        assert resp.status_code == 200
        assert b"Deliverables" in resp.data

    def test_detail_shows_empty_state(self, client, db_conn):
        """Empty deliverables section shows placeholder text."""
        _create_project(db_conn)
        resp = client.get("/projects/test-deliverables")
        assert b"No deliverables registered yet" in resp.data

    def test_detail_shows_existing_deliverables(self, client, db_conn):
        """Registered deliverables are displayed."""
        project = _create_project(db_conn)
        DeliverableRepository(db_conn).create(
            project_id=project.id,
            type="report",
            file_path="output/report_Q1.pdf",
            file_format="pdf",
            version="v1.0",
        )
        resp = client.get("/projects/test-deliverables")
        assert b"report" in resp.data
        assert b"output/report_Q1.pdf" in resp.data
        assert b"v1.0" in resp.data

    def test_pending_deliverable_shows_mark_delivered_button(self, client, db_conn):
        """Deliverables without delivered_at show a 'Mark delivered' button."""
        project = _create_project(db_conn)
        DeliverableRepository(db_conn).create(
            project_id=project.id,
            type="dashboard",
        )
        resp = client.get("/projects/test-deliverables")
        assert b"Pending" in resp.data
        assert b"Mark delivered" in resp.data

    def test_delivered_deliverable_hides_mark_button(self, client, db_conn):
        """Deliverables already delivered do not show the button."""
        project = _create_project(db_conn)
        DeliverableRepository(db_conn).create(
            project_id=project.id,
            type="report",
            delivered_at="2026-04-01T10:00:00Z",
        )
        resp = client.get("/projects/test-deliverables")
        assert b"Delivered" in resp.data
        assert b"Mark delivered" not in resp.data


class TestAddDeliverableForm:
    """Tests for the add-deliverable form endpoint."""

    def test_add_form_returns_form(self, client, db_conn):
        """GET add-form returns the deliverable registration form."""
        _create_project(db_conn)
        resp = client.get("/projects/test-deliverables/deliverables/add-form")
        assert resp.status_code == 200
        assert b'name="type"' in resp.data
        assert b'name="file_path"' in resp.data
        assert b'name="version"' in resp.data

    def test_add_form_404_for_missing_project(self, client):
        """Should return 404 for a nonexistent project."""
        resp = client.get("/projects/nonexistent/deliverables/add-form")
        assert resp.status_code == 404


class TestAddDeliverable:
    """Tests for POST add deliverable."""

    def test_add_deliverable_success(self, client, db_conn):
        """POST with valid data creates a deliverable and returns updated section."""
        project = _create_project(db_conn)
        resp = client.post(
            "/projects/test-deliverables/deliverables/add",
            data={
                "type": "report",
                "file_path": "output/Q1_report.pdf",
                "file_format": "pdf",
                "version": "v1.0",
            },
        )
        assert resp.status_code == 200
        assert b"output/Q1_report.pdf" in resp.data
        assert b"No deliverables registered yet" not in resp.data

        deliverables = DeliverableRepository(db_conn).list_for_project(project.id)
        assert len(deliverables) == 1
        assert deliverables[0].type == "report"
        assert deliverables[0].file_path == "output/Q1_report.pdf"
        assert deliverables[0].file_format == "pdf"
        assert deliverables[0].version == "v1.0"
        assert deliverables[0].delivered_at is None

    def test_add_deliverable_minimal(self, client, db_conn):
        """POST with only type creates a deliverable with defaults."""
        project = _create_project(db_conn)
        resp = client.post(
            "/projects/test-deliverables/deliverables/add",
            data={"type": "dashboard"},
        )
        assert resp.status_code == 200

        deliverables = DeliverableRepository(db_conn).list_for_project(project.id)
        assert len(deliverables) == 1
        assert deliverables[0].type == "dashboard"
        assert deliverables[0].file_path is None
        assert deliverables[0].delivered_at is None

    def test_add_deliverable_marked_delivered(self, client, db_conn):
        """POST with mark_delivered sets delivered_at on creation."""
        project = _create_project(db_conn)
        resp = client.post(
            "/projects/test-deliverables/deliverables/add",
            data={
                "type": "report",
                "mark_delivered": "1",
            },
        )
        assert resp.status_code == 200

        deliverables = DeliverableRepository(db_conn).list_for_project(project.id)
        assert len(deliverables) == 1
        assert deliverables[0].delivered_at is not None

    def test_add_deliverable_empty_type_shows_error(self, client, db_conn):
        """POST with empty type returns validation error."""
        _create_project(db_conn)
        resp = client.post(
            "/projects/test-deliverables/deliverables/add",
            data={"type": ""},
        )
        assert resp.status_code == 200
        assert b"Type is required" in resp.data

    def test_add_deliverable_404_for_missing_project(self, client):
        """Should return 404 for a nonexistent project."""
        resp = client.post(
            "/projects/nonexistent/deliverables/add",
            data={"type": "report"},
        )
        assert resp.status_code == 404

    def test_add_multiple_deliverables(self, client, db_conn):
        """Multiple deliverables can be registered to a project."""
        project = _create_project(db_conn)
        client.post(
            "/projects/test-deliverables/deliverables/add",
            data={"type": "report"},
        )
        client.post(
            "/projects/test-deliverables/deliverables/add",
            data={"type": "dashboard"},
        )

        deliverables = DeliverableRepository(db_conn).list_for_project(project.id)
        assert len(deliverables) == 2


class TestMarkDelivered:
    """Tests for marking a deliverable as delivered."""

    def test_mark_delivered_sets_timestamp(self, client, db_conn):
        """POST mark-delivered sets delivered_at on a pending deliverable."""
        project = _create_project(db_conn)
        deliverable = DeliverableRepository(db_conn).create(
            project_id=project.id,
            type="report",
        )
        assert deliverable.delivered_at is None

        resp = client.post(
            f"/projects/test-deliverables/deliverables/{deliverable.id}/mark-delivered",
        )
        assert resp.status_code == 200
        assert b"Delivered" in resp.data

        refreshed = DeliverableRepository(db_conn).get(deliverable.id)
        assert refreshed is not None
        assert refreshed.delivered_at is not None

    def test_mark_delivered_404_for_missing_project(self, client):
        """Should return 404 for a nonexistent project."""
        resp = client.post(
            "/projects/nonexistent/deliverables/some-id/mark-delivered",
        )
        assert resp.status_code == 404

    def test_mark_delivered_404_for_missing_deliverable(self, client, db_conn):
        """Should return 404 for a nonexistent deliverable."""
        _create_project(db_conn)
        resp = client.post(
            "/projects/test-deliverables/deliverables/nonexistent/mark-delivered",
        )
        assert resp.status_code == 404

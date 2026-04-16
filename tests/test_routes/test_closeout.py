"""Tests for the close-out routes."""

from __future__ import annotations

from data_project_manager.db.repositories.deliverable import DeliverableRepository
from data_project_manager.db.repositories.person import (
    PersonRepository,
    ProjectPersonRepository,
)
from data_project_manager.db.repositories.project import ProjectRepository


def _create_project(conn, **overrides):
    """Create a minimal project and return it."""
    defaults = {
        "title": "Test Close-out",
        "slug": "test-closeout",
        "status": "active",
    }
    defaults.update(overrides)
    return ProjectRepository(conn).create(**defaults)


def _make_closable(conn, project):
    """Add enough metadata so the project passes all critical checks."""
    # Add a requestor
    person = PersonRepository(conn).create(first_name="Alice", last_name="Smith")
    ProjectPersonRepository(conn).add(
        project_id=project.id, person_id=person.id, role="requestor"
    )
    # Add a delivered deliverable
    DeliverableRepository(conn).create(
        project_id=project.id, type="report", delivered_at="2026-03-01"
    )


class TestCloseoutChecklist:
    """Tests for GET /projects/<slug>/closeout."""

    def test_checklist_page_loads(self, client, db_conn):
        """The checklist page should load for a valid project."""
        _create_project(db_conn)
        resp = client.get("/projects/test-closeout/closeout")
        assert resp.status_code == 200
        assert b"Close-out" in resp.data

    def test_checklist_404_for_missing_project(self, client):
        """Should return 404 for a nonexistent project."""
        resp = client.get("/projects/nonexistent/closeout")
        assert resp.status_code == 404

    def test_checklist_shows_gaps(self, client, db_conn):
        """A new project should show gap items."""
        _create_project(db_conn)
        resp = client.get("/projects/test-closeout/closeout")
        assert b"No requestor" in resp.data
        assert b"No deliverables" in resp.data

    def test_checklist_shows_critical_badge(self, client, db_conn):
        """Critical gaps should display with the critical badge."""
        _create_project(db_conn)
        resp = client.get("/projects/test-closeout/closeout")
        assert b"critical" in resp.data

    def test_checklist_mark_done_disabled_with_critical(self, client, db_conn):
        """Mark as done button should be disabled when critical gaps exist."""
        _create_project(db_conn)
        resp = client.get("/projects/test-closeout/closeout")
        assert b"disabled" in resp.data

    def test_checklist_mark_done_enabled_when_closable(self, client, db_conn):
        """Mark as done button should be enabled when no critical gaps."""
        project = _create_project(db_conn)
        _make_closable(db_conn, project)
        resp = client.get("/projects/test-closeout/closeout")
        html = resp.data.decode()
        # The submit button should exist without disabled
        assert "Mark as done</button>" in html

    def test_checklist_shows_fix_links(self, client, db_conn):
        """Gaps with fix_url should show Fix links."""
        _create_project(db_conn)
        resp = client.get("/projects/test-closeout/closeout")
        assert b"Fix</a>" in resp.data

    def test_done_project_shows_banner(self, client, db_conn):
        """A done project should show the done banner."""
        _create_project(db_conn, status="done")
        resp = client.get("/projects/test-closeout/closeout")
        assert b"already been marked" in resp.data


class TestMarkDone:
    """Tests for POST /projects/<slug>/closeout/done."""

    def test_mark_done_success(self, client, db_conn):
        """Should set status=done and redirect to project detail."""
        project = _create_project(db_conn)
        _make_closable(db_conn, project)

        resp = client.post(
            "/projects/test-closeout/closeout/done", follow_redirects=False
        )
        assert resp.status_code == 302
        assert "/projects/test-closeout" in resp.headers["Location"]

        # Verify the project is now done
        updated = ProjectRepository(db_conn).get_by_slug("test-closeout")
        assert updated.status == "done"
        assert updated.realized_end is not None

    def test_mark_done_preserves_existing_realized_end(self, client, db_conn):
        """If realized_end is already set, it should not be overwritten."""
        project = _create_project(db_conn, realized_end="2026-02-15")
        _make_closable(db_conn, project)

        client.post("/projects/test-closeout/closeout/done")

        updated = ProjectRepository(db_conn).get_by_slug("test-closeout")
        assert updated.realized_end == "2026-02-15"

    def test_mark_done_blocked_by_critical_gaps(self, client, db_conn):
        """Should not close if critical gaps remain."""
        _create_project(db_conn)

        resp = client.post(
            "/projects/test-closeout/closeout/done", follow_redirects=False
        )
        assert resp.status_code == 302
        assert "closeout" in resp.headers["Location"]

        # Should still be active
        project = ProjectRepository(db_conn).get_by_slug("test-closeout")
        assert project.status == "active"

    def test_mark_done_404_for_missing_project(self, client):
        """Should return 404 for a nonexistent project."""
        resp = client.post("/projects/nonexistent/closeout/done")
        assert resp.status_code == 404


class TestInlineFixFields:
    """Tests for inline fix of scalar fields on the closeout page."""

    def test_fix_form_description(self, client, db_conn):
        """GET fix form for description returns a textarea."""
        _create_project(db_conn)
        resp = client.get("/projects/test-closeout/closeout/fix/description")
        assert resp.status_code == 200
        assert b"<textarea" in resp.data

    def test_fix_form_realized_start(self, client, db_conn):
        """GET fix form for realized_start returns a date input."""
        _create_project(db_conn)
        resp = client.get("/projects/test-closeout/closeout/fix/realized_start")
        assert resp.status_code == 200
        assert b'type="date"' in resp.data

    def test_fix_form_invalid_field(self, client, db_conn):
        """Unknown field should return 400."""
        _create_project(db_conn)
        resp = client.get("/projects/test-closeout/closeout/fix/nonexistent")
        assert resp.status_code == 400

    def test_fix_save_description(self, client, db_conn):
        """POST fix for description saves and returns updated checklist."""
        _create_project(db_conn)
        resp = client.post(
            "/projects/test-closeout/closeout/fix/description",
            data={"value": "A proper description"},
        )
        assert resp.status_code == 200
        # The returned checklist should no longer show the description gap
        assert b"No description set" not in resp.data

        project = ProjectRepository(db_conn).get_by_slug("test-closeout")
        assert project.description == "A proper description"

    def test_fix_save_realized_end(self, client, db_conn):
        """POST fix for realized_end saves and clears that gap."""
        _create_project(db_conn)
        resp = client.post(
            "/projects/test-closeout/closeout/fix/realized_end",
            data={"value": "2026-04-16"},
        )
        assert resp.status_code == 200
        assert b"Realized end date not set" not in resp.data

        project = ProjectRepository(db_conn).get_by_slug("test-closeout")
        assert project.realized_end == "2026-04-16"

    def test_fix_save_invalid_field(self, client, db_conn):
        """POST fix for unknown field should return 400."""
        _create_project(db_conn)
        resp = client.post(
            "/projects/test-closeout/closeout/fix/nonexistent",
            data={"value": "anything"},
        )
        assert resp.status_code == 400

    def test_checklist_shows_fix_buttons(self, client, db_conn):
        """Gaps with fix_field should show Fix buttons (not links)."""
        _create_project(db_conn)
        resp = client.get("/projects/test-closeout/closeout")
        assert b"closeout-fix-btn" in resp.data


class TestInlineFixRequestor:
    """Tests for inline requestor fix on the closeout page."""

    def test_requestor_form_shows_search(self, client, db_conn):
        """GET requestor fix form shows search input."""
        _create_project(db_conn)
        resp = client.get("/projects/test-closeout/closeout/fix/requestor")
        assert resp.status_code == 200
        assert b"Search people" in resp.data

    def test_requestor_form_with_selection(self, client, db_conn):
        """GET requestor fix with person_id shows selected person."""
        _create_project(db_conn)
        person = PersonRepository(db_conn).create(first_name="Alice", last_name="Smith")
        resp = client.get(
            f"/projects/test-closeout/closeout/fix/requestor?person_id={person.id}"
        )
        assert resp.status_code == 200
        assert b"Alice Smith" in resp.data
        assert b"Add as requestor" in resp.data

    def test_requestor_search(self, client, db_conn):
        """Search endpoint returns matching persons."""
        _create_project(db_conn)
        PersonRepository(db_conn).create(first_name="Alice", last_name="Smith")
        resp = client.get(
            "/projects/test-closeout/closeout/fix/requestor/search?q=alice"
        )
        assert resp.status_code == 200
        assert b"Alice" in resp.data

    def test_requestor_save(self, client, db_conn):
        """POST saves the requestor and returns updated checklist."""
        _create_project(db_conn)
        person = PersonRepository(db_conn).create(first_name="Alice", last_name="Smith")
        resp = client.post(
            "/projects/test-closeout/closeout/fix/requestor",
            data={"person_id": person.id},
        )
        assert resp.status_code == 200
        # The returned checklist should no longer show the requestor gap
        assert b"No requestor linked" not in resp.data

    def test_requestor_save_empty_returns_form(self, client, db_conn):
        """POST with no person_id returns the form again."""
        _create_project(db_conn)
        resp = client.post(
            "/projects/test-closeout/closeout/fix/requestor",
            data={"person_id": ""},
        )
        assert resp.status_code == 200
        assert b"Search people" in resp.data


class TestProjectDetailCloseoutLink:
    """Test that the project detail page links to the closeout checklist."""

    def test_closeout_button_on_detail(self, client, db_conn):
        """Project detail page should have a close-out checklist link."""
        _create_project(db_conn)
        resp = client.get("/projects/test-closeout")
        assert b"Close-out checklist" in resp.data
        assert b"/projects/test-closeout/closeout" in resp.data

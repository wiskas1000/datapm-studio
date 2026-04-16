"""Tests for person detail, edit (SCD2), and list search."""

from __future__ import annotations

from data_project_manager.db.repositories.person import PersonRepository


def _seed_person(db_conn, **overrides) -> str:
    """Create a test person and return their ID."""
    defaults = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "function_title": "Analyst",
        "department": "Data",
    }
    defaults.update(overrides)
    repo = PersonRepository(db_conn)
    person = repo.create(**defaults)
    return person.id


class TestPersonDetail:
    """GET /persons/<id>"""

    def test_detail_shows_all_fields(self, client, db_conn):
        pid = _seed_person(db_conn)
        resp = client.get(f"/persons/{pid}")
        assert resp.status_code == 200
        assert b"Alice" in resp.data
        assert b"Smith" in resp.data
        assert b"alice@example.com" in resp.data
        assert b"Analyst" in resp.data
        assert b"Data" in resp.data

    def test_detail_404_for_missing(self, client):
        resp = client.get("/persons/nonexistent-id")
        assert resp.status_code == 404

    def test_detail_has_edit_link(self, client, db_conn):
        pid = _seed_person(db_conn)
        resp = client.get(f"/persons/{pid}")
        assert b"Edit" in resp.data


class TestPersonEdit:
    """GET/POST /persons/<id>/edit"""

    def test_get_edit_form(self, client, db_conn):
        pid = _seed_person(db_conn)
        resp = client.get(f"/persons/{pid}/edit")
        assert resp.status_code == 200
        assert b"Alice" in resp.data
        assert b"Smith" in resp.data
        assert b"Save changes" in resp.data

    def test_edit_creates_scd2_version(self, client, db_conn):
        pid = _seed_person(db_conn)
        resp = client.post(
            f"/persons/{pid}/edit",
            data={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
                "function_title": "Senior Analyst",
                "department": "Data",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Senior Analyst" in resp.data
        assert b"Updated" in resp.data

        # Old version should no longer be current
        repo = PersonRepository(db_conn)
        old = repo.get(pid)
        assert not old.is_current

    def test_edit_no_changes_redirects(self, client, db_conn):
        pid = _seed_person(db_conn)
        resp = client.post(
            f"/persons/{pid}/edit",
            data={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
                "function_title": "Analyst",
                "department": "Data",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"No changes" in resp.data

    def test_edit_missing_name_error(self, client, db_conn):
        pid = _seed_person(db_conn)
        resp = client.post(
            f"/persons/{pid}/edit",
            data={
                "first_name": "",
                "last_name": "Smith",
            },
        )
        assert resp.status_code == 200
        assert b"required" in resp.data

    def test_edit_404_for_missing(self, client):
        resp = client.get("/persons/nonexistent-id/edit")
        assert resp.status_code == 404


class TestVersionHistory:
    """Version history displayed on person detail page."""

    def test_history_shown_after_edit(self, client, db_conn):
        pid = _seed_person(db_conn)

        # Edit to create a version
        resp = client.post(
            f"/persons/{pid}/edit",
            data={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice-new@example.com",
                "function_title": "Analyst",
                "department": "Data",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Version history" in resp.data
        assert b"Email" in resp.data
        assert b"alice-new@example.com" in resp.data


class TestPersonListSearch:
    """GET /persons?q=... filter."""

    def test_list_search_filter(self, client, db_conn):
        _seed_person(db_conn, first_name="Alice", last_name="Smith")
        _seed_person(db_conn, first_name="Bob", last_name="Jones")

        resp = client.get(
            "/persons/?q=alice",
            headers={"HX-Request": "true"},
        )
        assert resp.status_code == 200
        assert b"Alice" in resp.data
        assert b"Bob" not in resp.data

    def test_list_search_no_match(self, client, db_conn):
        _seed_person(db_conn)

        resp = client.get(
            "/persons/?q=nobody",
            headers={"HX-Request": "true"},
        )
        assert resp.status_code == 200
        assert b"No people found" in resp.data

    def test_list_links_to_detail(self, client, db_conn):
        pid = _seed_person(db_conn)
        resp = client.get("/persons/")
        assert resp.status_code == 200
        assert f"/persons/{pid}".encode() in resp.data

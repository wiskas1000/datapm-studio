"""Tests for person routes — list, search, inline create, page create."""

from __future__ import annotations

from data_project_manager.db.repositories.person import PersonRepository


def test_persons_list_empty(client):
    """An empty database shows the persons page."""
    r = client.get("/persons/")
    assert r.status_code == 200


def test_persons_list_with_data(client, db_conn):
    """Persons in the database render on the page."""
    repo = PersonRepository(db_conn)
    repo.create(first_name="Alice", last_name="Smith")
    repo.create(first_name="Bob", last_name="Jones")

    r = client.get("/persons/")
    assert r.status_code == 200
    assert b"Alice" in r.data
    assert b"Bob" in r.data


# ── Search endpoint ──


def test_search_returns_all_when_empty_query(client, db_conn):
    """GET /persons/search?q= returns all persons."""
    repo = PersonRepository(db_conn)
    repo.create(first_name="Alice", last_name="Smith")
    repo.create(first_name="Bob", last_name="Jones")

    r = client.get("/persons/search?q=")
    assert r.status_code == 200
    assert b"Alice" in r.data
    assert b"Bob" in r.data


def test_search_filters_by_first_name(client, db_conn):
    """Search by first name returns matching persons only."""
    repo = PersonRepository(db_conn)
    repo.create(first_name="Alice", last_name="Smith")
    repo.create(first_name="Bob", last_name="Jones")

    r = client.get("/persons/search?q=alice")
    assert r.status_code == 200
    assert b"Alice" in r.data
    assert b"Bob" not in r.data


def test_search_filters_by_last_name(client, db_conn):
    """Search by last name returns matching persons only."""
    repo = PersonRepository(db_conn)
    repo.create(first_name="Alice", last_name="Smith")
    repo.create(first_name="Bob", last_name="Jones")

    r = client.get("/persons/search?q=jones")
    assert r.status_code == 200
    assert b"Bob" in r.data
    assert b"Alice" not in r.data


def test_search_filters_by_full_name(client, db_conn):
    """Search by full name matches."""
    repo = PersonRepository(db_conn)
    repo.create(first_name="Alice", last_name="Smith")
    repo.create(first_name="Bob", last_name="Jones")

    r = client.get("/persons/search?q=alice+smith")
    assert r.status_code == 200
    assert b"Alice" in r.data


def test_search_no_match_shows_add_button(client):
    """When no persons match, the dropdown shows '+ Add new person'."""
    r = client.get("/persons/search?q=nonexistent")
    assert r.status_code == 200
    assert b"Add new person" in r.data


# ── Inline create (for project form) ──


def test_inline_form_get(client):
    """GET /persons/new-inline returns the inline form partial."""
    r = client.get("/persons/new-inline")
    assert r.status_code == 200
    assert b"first_name" in r.data


def test_inline_create_success(client, db_conn):
    """POST /persons/new-inline with valid data creates a person."""
    r = client.post(
        "/persons/new-inline",
        data={"first_name": "Jane", "last_name": "Doe"},
    )
    assert r.status_code == 200
    assert b"Jane" in r.data
    assert b"Doe" in r.data
    # Should contain a hidden input with the person ID
    assert b"requestor_id" in r.data

    # Verify in DB
    repo = PersonRepository(db_conn)
    persons = repo.list(current_only=True)
    assert any(p.first_name == "Jane" and p.last_name == "Doe" for p in persons)


def test_inline_create_missing_name(client):
    """POST /persons/new-inline without names shows an error."""
    r = client.post(
        "/persons/new-inline",
        data={"first_name": "", "last_name": ""},
    )
    assert r.status_code == 200
    assert b"required" in r.data.lower()


# ── Page create (from persons list) ──


def test_page_form_get(client):
    """GET /persons/new returns the page form partial."""
    r = client.get("/persons/new")
    assert r.status_code == 200
    assert b"first_name" in r.data
    assert b"department" in r.data


def test_page_create_success(client, db_conn):
    """POST /persons/new with valid data creates a person and redirects."""
    r = client.post(
        "/persons/new",
        data={
            "first_name": "John",
            "last_name": "Smith",
            "function_title": "Analyst",
            "department": "BI",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    repo = PersonRepository(db_conn)
    persons = repo.list(current_only=True)
    person = next(p for p in persons if p.first_name == "John")
    assert person.last_name == "Smith"
    assert person.function_title == "Analyst"
    assert person.department == "BI"


def test_page_create_missing_name(client):
    """POST /persons/new without names shows an error."""
    r = client.post(
        "/persons/new",
        data={"first_name": "John", "last_name": ""},
    )
    assert r.status_code == 200
    assert b"required" in r.data.lower()

"""Tests for tag routes — search and inline create."""

from __future__ import annotations

import json

from data_project_manager.db.repositories.tag import TagRepository


# ── Search endpoint ──


def test_search_returns_all_when_empty_query(client, db_conn):
    """GET /tags/search?q= returns all tags."""
    repo = TagRepository(db_conn)
    repo.create(name="python")
    repo.create(name="sql")

    r = client.get("/tags/search?q=")
    assert r.status_code == 200
    assert b"python" in r.data
    assert b"sql" in r.data


def test_search_filters_by_name(client, db_conn):
    """Search filters tags by name substring."""
    repo = TagRepository(db_conn)
    repo.create(name="python")
    repo.create(name="sql")

    r = client.get("/tags/search?q=pyt")
    assert r.status_code == 200
    assert b"python" in r.data
    assert b"sql" not in r.data


def test_search_no_match_shows_create_option(client):
    """When no tags match, the dropdown shows a create option."""
    r = client.get("/tags/search?q=newtag")
    assert r.status_code == 200
    assert b"newtag" in r.data
    assert b"Create" in r.data


# ── Inline create ──


def test_inline_create_success(client, db_conn):
    """POST /tags/new-inline creates a tag and returns JSON."""
    r = client.post("/tags/new-inline", data={"name": "machine-learning"})
    assert r.status_code == 200

    data = json.loads(r.data)
    assert data["name"] == "machine-learning"
    assert "id" in data

    # Verify in DB
    repo = TagRepository(db_conn)
    tag = repo.get_by_name("machine-learning")
    assert tag is not None


def test_inline_create_empty_name_returns_400(client):
    """POST /tags/new-inline with empty name returns 400."""
    r = client.post("/tags/new-inline", data={"name": ""})
    assert r.status_code == 400

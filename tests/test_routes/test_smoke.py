"""Smoke tests — every registered route returns a valid response."""

from __future__ import annotations

import pytest

from datapm_studio.app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index_redirects_to_projects(client):
    r = client.get("/")
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/projects/")


def test_project_list(client):
    assert client.get("/projects/").status_code == 200


def test_project_create_page(client):
    assert client.get("/projects/new").status_code == 200


def test_persons_list(client):
    assert client.get("/persons/").status_code == 200


def test_search_page(client):
    assert client.get("/search/").status_code == 200

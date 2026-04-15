"""Shared test fixtures — Flask test client backed by a temporary database."""

from __future__ import annotations

import pytest

from datapm_studio.app import create_app


@pytest.fixture()
def tmp_db(tmp_path):
    """Return the path to a fresh temporary SQLite database.

    The database is auto-created and migrated by ``get_connection()``
    on first use, so no explicit setup is needed here.
    """
    return tmp_path / "test.db"


@pytest.fixture()
def app(tmp_db):
    """Create a Flask app wired to the temporary database."""
    app = create_app(db_path=tmp_db)
    app.config["TESTING"] = True
    return app


@pytest.fixture()
def client(app):
    """A Flask test client for making HTTP requests."""
    with app.test_client() as c:
        yield c


@pytest.fixture()
def db_conn(app):
    """A raw database connection to the temp DB for seeding test data."""
    with app.app_context():
        conn = app.get_db()  # type: ignore[attr-defined]
        yield conn

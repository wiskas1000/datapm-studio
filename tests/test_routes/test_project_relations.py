"""Tests for adding/removing persons and tags on existing projects."""

from __future__ import annotations

from data_project_manager.db.repositories.person import (
    PersonRepository,
    ProjectPersonRepository,
)
from data_project_manager.db.repositories.project import ProjectRepository
from data_project_manager.db.repositories.tag import ProjectTagRepository, TagRepository


def _seed_project(db_conn) -> tuple[str, str]:
    """Create a test project. Returns (project_id, slug)."""
    repo = ProjectRepository(db_conn)
    project = repo.create(
        title="Relations Test",
        slug="relations-test",
        status="active",
    )
    return project.id, project.slug


def _seed_person(db_conn) -> str:
    """Create a test person. Returns person_id."""
    repo = PersonRepository(db_conn)
    person = repo.create(first_name="Jane", last_name="Doe", email="jane@example.com")
    return person.id


def _seed_tag(db_conn) -> str:
    """Create a test tag. Returns tag_id."""
    repo = TagRepository(db_conn)
    tag = repo.create(name="test-tag")
    return tag.id


class TestAddPerson:
    """POST /projects/<slug>/persons/add"""

    def test_add_person_to_project(self, client, db_conn):
        project_id, slug = _seed_project(db_conn)
        person_id = _seed_person(db_conn)

        resp = client.post(
            f"/projects/{slug}/persons/add",
            data={"person_id": person_id, "role": "analyst"},
        )
        assert resp.status_code == 200
        assert b"Jane Doe" in resp.data
        assert b"Analyst" in resp.data

        # Verify persisted
        persons = ProjectPersonRepository(db_conn).list_for_project(project_id)
        assert len(persons) == 1
        assert persons[0].role == "analyst"

    def test_add_person_missing_fields(self, client, db_conn):
        _, slug = _seed_project(db_conn)

        resp = client.post(
            f"/projects/{slug}/persons/add",
            data={"person_id": "", "role": ""},
        )
        assert resp.status_code == 200
        assert b"required" in resp.data

    def test_add_person_idempotent(self, client, db_conn):
        project_id, slug = _seed_project(db_conn)
        person_id = _seed_person(db_conn)

        # Add twice — should not duplicate
        client.post(
            f"/projects/{slug}/persons/add",
            data={"person_id": person_id, "role": "analyst"},
        )
        client.post(
            f"/projects/{slug}/persons/add",
            data={"person_id": person_id, "role": "analyst"},
        )

        persons = ProjectPersonRepository(db_conn).list_for_project(project_id)
        assert len(persons) == 1

    def test_add_person_404_missing_project(self, client):
        resp = client.post(
            "/projects/no-such/persons/add",
            data={"person_id": "x", "role": "y"},
        )
        assert resp.status_code == 404


class TestRemovePerson:
    """POST /projects/<slug>/persons/remove"""

    def test_remove_person_from_project(self, client, db_conn):
        project_id, slug = _seed_project(db_conn)
        person_id = _seed_person(db_conn)

        # First add
        ProjectPersonRepository(db_conn).add(
            project_id=project_id, person_id=person_id, role="requestor"
        )

        resp = client.post(
            f"/projects/{slug}/persons/remove",
            data={"person_id": person_id, "role": "requestor"},
        )
        assert resp.status_code == 200

        # Verify removed
        persons = ProjectPersonRepository(db_conn).list_for_project(project_id)
        assert len(persons) == 0

    def test_remove_nonexistent_person_ok(self, client, db_conn):
        _, slug = _seed_project(db_conn)

        resp = client.post(
            f"/projects/{slug}/persons/remove",
            data={"person_id": "nonexistent", "role": "analyst"},
        )
        assert resp.status_code == 200


class TestAddTag:
    """POST /projects/<slug>/tags/add"""

    def test_add_tag_to_project(self, client, db_conn):
        project_id, slug = _seed_project(db_conn)
        tag_id = _seed_tag(db_conn)

        resp = client.post(
            f"/projects/{slug}/tags/add",
            data={"tag_id": tag_id},
        )
        assert resp.status_code == 200
        assert b"test-tag" in resp.data

        # Verify persisted
        tags = ProjectTagRepository(db_conn).list_for_project(project_id)
        assert len(tags) == 1
        assert tags[0].name == "test-tag"

    def test_add_tag_missing_id(self, client, db_conn):
        _, slug = _seed_project(db_conn)

        resp = client.post(
            f"/projects/{slug}/tags/add",
            data={"tag_id": ""},
        )
        assert resp.status_code == 200
        assert b"select a tag" in resp.data

    def test_add_tag_idempotent(self, client, db_conn):
        project_id, slug = _seed_project(db_conn)
        tag_id = _seed_tag(db_conn)

        client.post(f"/projects/{slug}/tags/add", data={"tag_id": tag_id})
        client.post(f"/projects/{slug}/tags/add", data={"tag_id": tag_id})

        tags = ProjectTagRepository(db_conn).list_for_project(project_id)
        assert len(tags) == 1


class TestRemoveTag:
    """POST /projects/<slug>/tags/remove"""

    def test_remove_tag_from_project(self, client, db_conn):
        project_id, slug = _seed_project(db_conn)
        tag_id = _seed_tag(db_conn)

        ProjectTagRepository(db_conn).add(project_id=project_id, tag_id=tag_id)

        resp = client.post(
            f"/projects/{slug}/tags/remove",
            data={"tag_id": tag_id},
        )
        assert resp.status_code == 200

        tags = ProjectTagRepository(db_conn).list_for_project(project_id)
        assert len(tags) == 0

    def test_remove_nonexistent_tag_ok(self, client, db_conn):
        _, slug = _seed_project(db_conn)

        resp = client.post(
            f"/projects/{slug}/tags/remove",
            data={"tag_id": "nonexistent"},
        )
        assert resp.status_code == 200


class TestSearchEndpoints:
    """Person/tag search endpoints on the project detail page."""

    def test_search_person_for_detail(self, client, db_conn):
        _, slug = _seed_project(db_conn)
        _seed_person(db_conn)

        resp = client.get(f"/projects/{slug}/persons/search?q=jane")
        assert resp.status_code == 200
        assert b"Jane" in resp.data

    def test_search_person_no_match(self, client, db_conn):
        _, slug = _seed_project(db_conn)

        resp = client.get(f"/projects/{slug}/persons/search?q=nobody")
        assert resp.status_code == 200
        assert b"No matching" in resp.data

    def test_search_tag_for_detail(self, client, db_conn):
        _, slug = _seed_project(db_conn)
        _seed_tag(db_conn)

        resp = client.get(f"/projects/{slug}/tags/search?q=test")
        assert resp.status_code == 200
        assert b"test-tag" in resp.data


class TestFormEndpoints:
    """GET endpoints for add forms."""

    def test_add_person_form(self, client, db_conn):
        _, slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/persons/add-form")
        assert resp.status_code == 200
        assert b"Person" in resp.data
        assert b"Role" in resp.data

    def test_add_tag_form(self, client, db_conn):
        _, slug = _seed_project(db_conn)
        resp = client.get(f"/projects/{slug}/tags/add-form")
        assert resp.status_code == 200
        assert b"Tag" in resp.data

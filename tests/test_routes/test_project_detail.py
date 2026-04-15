"""Tests for the project detail page."""

from __future__ import annotations

from data_project_manager.db.repositories.person import (
    PersonRepository,
    ProjectPersonRepository,
)
from data_project_manager.db.repositories.project import (
    ProjectRepository,
    ProjectRootRepository,
)
from data_project_manager.db.repositories.tag import ProjectTagRepository, TagRepository


def test_detail_not_found_returns_404(client):
    """Requesting a non-existent slug returns 404."""
    r = client.get("/projects/nonexistent-slug")
    assert r.status_code == 404


def test_detail_shows_project_metadata(client, db_conn):
    """Detail page renders all basic project fields."""
    repo = ProjectRepository(db_conn)
    repo.create(
        title="Alpha Report",
        slug="2026-04-15-alpha-report",
        is_adhoc=False,
        domain="healthcare",
        request_date="2026-04-10",
        expected_start="2026-04-15",
        expected_end="2026-05-15",
        estimated_hours=40.0,
        template_used="analysis",
    )

    r = client.get("/projects/2026-04-15-alpha-report")
    assert r.status_code == 200
    assert b"Alpha Report" in r.data
    assert b"2026-04-15-alpha-report" in r.data
    assert b"healthcare" in r.data
    assert b"Planned" in r.data
    assert b"2026-04-10" in r.data
    assert b"2026-04-15" in r.data
    assert b"2026-05-15" in r.data
    assert b"40.0" in r.data
    assert b"analysis" in r.data


def test_detail_shows_adhoc_type(client, db_conn):
    """Ad-hoc projects display 'Ad-hoc' as type."""
    repo = ProjectRepository(db_conn)
    repo.create(
        title="Quick Task",
        slug="2026-04-15-quick-task",
        is_adhoc=True,
    )

    r = client.get("/projects/2026-04-15-quick-task")
    assert r.status_code == 200
    assert b"Ad-hoc" in r.data


def test_detail_shows_requestor(client, db_conn):
    """Linked requestor appears on the detail page."""
    proj_repo = ProjectRepository(db_conn)
    project = proj_repo.create(
        title="With Requestor",
        slug="2026-04-15-with-requestor",
        is_adhoc=False,
    )

    person_repo = PersonRepository(db_conn)
    person = person_repo.create(first_name="Jane", last_name="Doe")

    pp_repo = ProjectPersonRepository(db_conn)
    pp_repo.add(project_id=project.id, person_id=person.id, role="requestor")

    r = client.get("/projects/2026-04-15-with-requestor")
    assert r.status_code == 200
    assert b"Jane" in r.data
    assert b"Doe" in r.data
    assert b"Requestor" in r.data


def test_detail_shows_tags(client, db_conn):
    """Linked tags appear as chips on the detail page."""
    proj_repo = ProjectRepository(db_conn)
    project = proj_repo.create(
        title="Tagged",
        slug="2026-04-15-tagged",
        is_adhoc=False,
    )

    tag_repo = TagRepository(db_conn)
    tag1 = tag_repo.create(name="python")
    tag2 = tag_repo.create(name="ml")

    pt_repo = ProjectTagRepository(db_conn)
    pt_repo.add(project_id=project.id, tag_id=tag1.id)
    pt_repo.add(project_id=project.id, tag_id=tag2.id)

    r = client.get("/projects/2026-04-15-tagged")
    assert r.status_code == 200
    assert b"python" in r.data
    assert b"ml" in r.data


def test_detail_shows_root(client, db_conn):
    """The project root name is displayed when available."""
    root_repo = ProjectRootRepository(db_conn)
    root = root_repo.create(
        name="work", absolute_path="/home/user/projects", is_default=True
    )

    proj_repo = ProjectRepository(db_conn)
    proj_repo.create(
        title="Rooted",
        slug="2026-04-15-rooted",
        is_adhoc=False,
        root_id=root.id,
    )

    r = client.get("/projects/2026-04-15-rooted")
    assert r.status_code == 200
    assert b"work" in r.data


def test_detail_shows_status_badge(client, db_conn):
    """Status is rendered with a badge class."""
    repo = ProjectRepository(db_conn)
    repo.create(
        title="Active Project",
        slug="2026-04-15-active-project",
        is_adhoc=False,
    )

    r = client.get("/projects/2026-04-15-active-project")
    assert r.status_code == 200
    assert b"badge-active" in r.data

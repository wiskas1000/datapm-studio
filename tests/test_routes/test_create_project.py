"""Tests for the project creation form and POST handler."""

from __future__ import annotations

from werkzeug.datastructures import MultiDict

from data_project_manager.db.repositories.data_file import (
    AggregationLevelRepository,
    EntityTypeRepository,
)
from data_project_manager.db.repositories.person import (
    PersonRepository,
    ProjectPersonRepository,
)
from data_project_manager.db.repositories.project import (
    ProjectRepository,
    ProjectRootRepository,
)
from data_project_manager.db.repositories.question import RequestQuestionRepository
from data_project_manager.db.repositories.tag import ProjectTagRepository, TagRepository


def test_create_form_renders(client):
    """GET /projects/new returns 200 with all form fields."""
    r = client.get("/projects/new")
    assert r.status_code == 200
    assert b'name="title"' in r.data
    assert b'name="project_type"' in r.data
    assert b'name="domain"' in r.data
    assert b'name="request_date"' in r.data
    assert b'name="folders"' in r.data
    assert b'name="do_git_init"' in r.data
    assert b'name="external_url"' in r.data
    assert b"Create Project" in r.data


def test_create_form_shows_archetypes(client):
    """The form shows all built-in archetypes in the dropdown."""
    r = client.get("/projects/new")
    assert r.status_code == 200
    assert b"Minimal" in r.data
    assert b"Analysis" in r.data
    assert b"Modeling" in r.data
    assert b"Reporting" in r.data
    assert b"Research" in r.data
    assert b"Full" in r.data


def test_create_form_shows_folder_toggles(client):
    """The form shows toggleable checkboxes for optional folders."""
    r = client.get("/projects/new")
    assert r.status_code == 200
    assert b'value="data"' in r.data
    assert b'value="src"' in r.data
    assert b'value="notebooks"' in r.data
    assert b'value="queries"' in r.data
    assert b'value="literatuur"' in r.data
    assert b'value="resultaten"' in r.data


def test_create_form_shows_roots(client, db_conn):
    """The form populates the root dropdown from the database."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(name="personal", absolute_path="/tmp/personal", is_default=False)

    r = client.get("/projects/new")
    assert b"personal" in r.data


def test_create_requires_title(client):
    """POST with empty title re-renders the form with an error."""
    r = client.post("/projects/new", data={"title": ""})
    assert r.status_code == 200
    assert b"Title is required" in r.data


def test_create_project_success(client, db_conn, tmp_path):
    """POST with a valid title creates a project and redirects."""
    # Ensure a root exists so create_project can scaffold folders
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "Test Analysis",
            "project_type": "planned",
            "root_name": "test-root",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "/projects/" in r.headers["Location"]

    # Verify project exists in DB
    proj_repo = ProjectRepository(db_conn)
    projects = proj_repo.list()
    assert len(projects) == 1
    assert projects[0].title == "Test Analysis"
    assert projects[0].is_adhoc is False


def test_create_adhoc_project(client, db_conn, tmp_path):
    """Selecting ad-hoc type sets is_adhoc=True on the project."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "Quick Request",
            "project_type": "adhoc",
            "root_name": "test-root",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    proj_repo = ProjectRepository(db_conn)
    projects = proj_repo.list()
    assert projects[0].is_adhoc is True


def test_create_project_links_requestor(client, db_conn, tmp_path):
    """A selected requestor is linked to the project via ProjectPersonRepository."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )
    person_repo = PersonRepository(db_conn)
    person = person_repo.create(first_name="Jane", last_name="Doe")

    r = client.post(
        "/projects/new",
        data={
            "title": "Linked Project",
            "root_name": "test-root",
            "requestor_id": person.id,
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    proj_repo = ProjectRepository(db_conn)
    project = proj_repo.list()[0]
    pp_repo = ProjectPersonRepository(db_conn)
    links = pp_repo.list_for_project(project.id)
    assert len(links) == 1
    assert links[0].role == "requestor"


def test_create_project_links_tags(client, db_conn, tmp_path):
    """Selected tags are linked to the project via ProjectTagRepository."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )
    tag_repo = TagRepository(db_conn)
    tag1 = tag_repo.create(name="python")
    tag2 = tag_repo.create(name="ml")

    r = client.post(
        "/projects/new",
        data=MultiDict(
            [
                ("title", "Tagged Project"),
                ("root_name", "test-root"),
                ("tag_ids", tag1.id),
                ("tag_ids", tag2.id),
            ]
        ),
        follow_redirects=False,
    )
    assert r.status_code == 302

    proj_repo = ProjectRepository(db_conn)
    project = proj_repo.list()[0]
    pt_repo = ProjectTagRepository(db_conn)
    tags = pt_repo.list_for_project(project.id)
    assert len(tags) == 2
    tag_names = {t.name for t in tags}
    assert tag_names == {"python", "ml"}


def test_create_project_with_dates_and_hours(client, db_conn, tmp_path):
    """Date and estimated hours fields are persisted correctly."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "Dated Project",
            "root_name": "test-root",
            "request_date": "2026-04-15",
            "expected_start": "2026-04-20",
            "expected_end": "2026-05-15",
            "estimated_hours": "40",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    proj_repo = ProjectRepository(db_conn)
    project = proj_repo.list()[0]
    assert project.request_date == "2026-04-15"
    assert project.expected_start == "2026-04-20"
    assert project.expected_end == "2026-05-15"
    assert project.estimated_hours == 40.0


def test_create_project_with_domain(client, db_conn, tmp_path):
    """Domain field is persisted."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "Healthcare Project",
            "root_name": "test-root",
            "domain": "healthcare",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    proj_repo = ProjectRepository(db_conn)
    project = proj_repo.list()[0]
    assert project.domain == "healthcare"


def test_create_duplicate_folder_shows_error(client, db_conn, tmp_path):
    """Creating a project whose folder already exists shows an error."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    # Create first project
    client.post(
        "/projects/new",
        data={"title": "Duplicate Test", "root_name": "test-root"},
        follow_redirects=False,
    )

    # Try creating another with the same title (same slug → same folder)
    r = client.post(
        "/projects/new",
        data={"title": "Duplicate Test", "root_name": "test-root"},
    )
    assert r.status_code == 200
    # Should show an error, not a redirect
    assert b"already exists" in r.data or b"error" in r.data.lower()


def test_create_end_before_start_shows_error(client):
    """Expected end before expected start re-renders with an error."""
    r = client.post(
        "/projects/new",
        data={
            "title": "Bad Dates",
            "expected_start": "2026-05-15",
            "expected_end": "2026-04-01",
        },
    )
    assert r.status_code == 200
    assert b"end date cannot be before" in r.data


def test_create_same_start_and_end_is_valid(client, db_conn, tmp_path):
    """Expected start equal to expected end is allowed (same-day project)."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "Same Day Project",
            "root_name": "test-root",
            "expected_start": "2026-05-01",
            "expected_end": "2026-05-01",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302


def test_create_only_start_date_is_valid(client, db_conn, tmp_path):
    """Providing only expected start (no end) is allowed."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "Start Only",
            "root_name": "test-root",
            "expected_start": "2026-05-01",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302


def test_create_only_end_date_is_valid(client, db_conn, tmp_path):
    """Providing only expected end (no start) is allowed."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "End Only",
            "root_name": "test-root",
            "expected_end": "2026-06-01",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302


def test_create_with_custom_folders(client, db_conn, tmp_path):
    """Selected folders are passed to create_project and created on disk."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data=MultiDict(
            [
                ("title", "Folder Project"),
                ("root_name", "test-root"),
                ("folders", "data"),
                ("folders", "resultaten"),
            ]
        ),
        follow_redirects=False,
    )
    assert r.status_code == 302

    # Verify folders were created on disk
    import os

    project_dirs = os.listdir(tmp_path / "projects")
    assert len(project_dirs) == 1
    project_dir = tmp_path / "projects" / project_dirs[0]
    assert (project_dir / "data").is_dir()
    assert (project_dir / "resultaten").is_dir()
    # src should NOT exist (not selected)
    assert not (project_dir / "src").exists()


def test_create_with_git_init(client, db_conn, tmp_path):
    """Git init checkbox creates a git repo in src/."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data=MultiDict(
            [
                ("title", "Git Project"),
                ("root_name", "test-root"),
                ("folders", "data"),
                ("folders", "src"),
                ("do_git_init", "1"),
            ]
        ),
        follow_redirects=False,
    )
    assert r.status_code == 302

    import os

    project_dirs = os.listdir(tmp_path / "projects")
    project_dir = tmp_path / "projects" / project_dirs[0]
    assert (project_dir / "src" / ".git").is_dir()

    # Verify has_git_repo is True in DB
    proj_repo = ProjectRepository(db_conn)
    project = proj_repo.list()[0]
    assert project.has_git_repo is True


def test_create_with_external_url(client, db_conn, tmp_path):
    """External URL field is persisted on the project."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "URL Project",
            "root_name": "test-root",
            "external_url": "https://dev.azure.com/org/project",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    proj_repo = ProjectRepository(db_conn)
    project = proj_repo.list()[0]
    assert project.external_url == "https://dev.azure.com/org/project"


def test_create_form_shows_research_context(client):
    """The form exposes the research context fields."""
    r = client.get("/projects/new")
    assert r.status_code == 200
    assert b'name="questions_text"' in r.data
    assert b'name="entity_types_text"' in r.data
    assert b'name="agg_levels_text"' in r.data


def test_create_project_creates_initial_questions(client, db_conn, tmp_path):
    """Each non-empty line in questions_text becomes a RequestQuestion."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "With Questions",
            "root_name": "test-root",
            "questions_text": (
                "What is the churn rate for Q1?\n"
                "\n"
                "Which segments drive retention?\n"
                "   \n"
            ),
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    project = ProjectRepository(db_conn).list()[0]
    questions = RequestQuestionRepository(db_conn).list_for_project(project.id)
    assert len(questions) == 2
    texts = {q.question_text for q in questions}
    assert texts == {
        "What is the churn rate for Q1?",
        "Which segments drive retention?",
    }


def test_create_project_seeds_entity_types(client, db_conn, tmp_path):
    """Comma-separated entity types are added to the vocabulary."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "With Entity Types",
            "root_name": "test-root",
            "entity_types_text": "patient, visit ,  claim",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    names = {e.name for e in EntityTypeRepository(db_conn).list()}
    assert {"patient", "visit", "claim"}.issubset(names)


def test_create_project_seeds_agg_levels(client, db_conn, tmp_path):
    """Comma-separated aggregation levels are added to the vocabulary."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "With Agg Levels",
            "root_name": "test-root",
            "agg_levels_text": "biweekly, quarterly",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    names = {a.name for a in AggregationLevelRepository(db_conn).list()}
    assert {"biweekly", "quarterly"}.issubset(names)


def test_create_project_empty_metadata_is_noop(client, db_conn, tmp_path):
    """Empty metadata fields don't create spurious records."""
    root_repo = ProjectRootRepository(db_conn)
    root_repo.create(
        name="test-root", absolute_path=str(tmp_path / "projects"), is_default=True
    )

    r = client.post(
        "/projects/new",
        data={
            "title": "No Metadata",
            "root_name": "test-root",
            "questions_text": "   \n\n",
            "entity_types_text": "  ",
            "agg_levels_text": " , , ",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    project = ProjectRepository(db_conn).list()[0]
    questions = RequestQuestionRepository(db_conn).list_for_project(project.id)
    assert questions == []

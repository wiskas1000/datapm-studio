"""Project routes — list, create, detail, edit."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from data_project_manager.db.repositories.person import (
    PersonRepository,
    ProjectPersonRepository,
)
from data_project_manager.db.repositories.project import (
    ProjectRepository,
    ProjectRootRepository,
)
from data_project_manager.db.repositories.tag import ProjectTagRepository, TagRepository

bp = Blueprint("projects", __name__, url_prefix="/projects")


def _get_conn():
    """Get the database connection from the current app."""
    from flask import current_app

    return current_app.get_db()  # type: ignore[attr-defined]


def _get_repo() -> ProjectRepository:
    """Get a ProjectRepository using the current app's DB connection."""
    return ProjectRepository(_get_conn())


def _form_data() -> dict:
    """Extract form fields into a dict for re-rendering on validation error."""
    return {
        "title": request.form.get("title", "").strip(),
        "project_type": request.form.get("project_type", "planned"),
        "domain": request.form.get("domain", "").strip(),
        "description": request.form.get("description", "").strip(),
        "requestor_id": request.form.get("requestor_id", "").strip(),
        "template_used": request.form.get("template_used", "analysis"),
        "root_name": request.form.get("root_name", ""),
        "request_date": request.form.get("request_date", ""),
        "expected_start": request.form.get("expected_start", ""),
        "expected_end": request.form.get("expected_end", ""),
        "estimated_hours": request.form.get("estimated_hours", ""),
    }


def _render_create_form(form: dict, error: str | None = None):
    """Render the creation form with current form data and dropdown options."""
    conn = _get_conn()
    roots = ProjectRootRepository(conn).list()

    selected_person = None
    if form.get("requestor_id"):
        selected_person = PersonRepository(conn).get(form["requestor_id"])

    selected_tags: list = []
    tag_ids = request.form.getlist("tag_ids")
    if tag_ids:
        tag_repo = TagRepository(conn)
        for tid in tag_ids:
            tag = tag_repo.get(tid)
            if tag:
                selected_tags.append(tag)

    return render_template(
        "projects/create.html",
        form=form,
        error=error,
        roots=roots,
        today=date.today().isoformat(),
        selected_person=selected_person,
        selected_tags=selected_tags,
    )


@bp.route("/")
def list_projects():
    """List all projects, most recent first."""
    repo = _get_repo()
    projects = repo.list()
    return render_template("projects/list.html", projects=projects)


@bp.route("/new", methods=["GET", "POST"])
def create_project():
    """Project creation wizard."""
    if request.method == "GET":
        return _render_create_form(
            form={"project_type": "planned", "template_used": "analysis"},
        )

    form = _form_data()

    # Validate required fields
    if not form["title"]:
        return _render_create_form(form, error="Title is required.")

    # Call the core create_project function
    from data_project_manager.core.project import (
        create_project as core_create_project,
    )

    from flask import current_app

    try:
        result = core_create_project(
            title=form["title"],
            domain=form["domain"] or None,
            description=form["description"] or None,
            is_adhoc=form["project_type"] == "adhoc",
            root_name=form["root_name"] or None,
            request_date=form["request_date"] or None,
            expected_start=form["expected_start"] or None,
            expected_end=form["expected_end"] or None,
            estimated_hours=(
                float(form["estimated_hours"]) if form["estimated_hours"] else None
            ),
            template_used=form["template_used"],
            db_path=current_app.config.get("DATAPM_DB_PATH"),
        )
    except FileExistsError:
        return _render_create_form(
            form,
            error="A project with this name already exists (folder collision).",
        )
    except (ValueError, OSError) as exc:
        return _render_create_form(form, error=str(exc))

    project_id = result["id"]
    slug = result["slug"]
    conn = _get_conn()

    # Link requestor
    if form["requestor_id"]:
        ProjectPersonRepository(conn).add(
            project_id=project_id,
            person_id=form["requestor_id"],
            role="requestor",
        )

    # Link tags
    tag_ids = request.form.getlist("tag_ids")
    if tag_ids:
        pt_repo = ProjectTagRepository(conn)
        for tag_id in tag_ids:
            pt_repo.add(project_id=project_id, tag_id=tag_id)

    flash(f'Created project "{form["title"]}".', "success")
    return redirect(url_for("projects.detail", slug=slug))


@bp.route("/<slug>")
def detail(slug):
    """Show all metadata for a single project."""
    repo = _get_repo()
    project = repo.get_by_slug(slug)
    return render_template("projects/detail.html", project=project)


@bp.route("/<slug>/edit/<field>", methods=["GET", "PUT"])
def edit_field(slug, field):
    """Inline edit a single field (HTMX partial)."""
    # TODO: GET returns edit form partial, PUT saves and returns read partial
    return "", 501

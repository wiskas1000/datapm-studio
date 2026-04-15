"""Project routes — list, create, detail, edit."""

from __future__ import annotations

from flask import Blueprint, render_template, request

from data_project_manager.db.repositories.project import ProjectRepository

bp = Blueprint("projects", __name__, url_prefix="/projects")


def _get_repo() -> ProjectRepository:
    """Get a ProjectRepository using the current app's DB connection."""
    from flask import current_app

    conn = current_app.get_db()  # type: ignore[attr-defined]
    return ProjectRepository(conn)


@bp.route("/")
def list_projects():
    """List all projects, most recent first."""
    repo = _get_repo()
    projects = repo.list()
    return render_template("projects/list.html", projects=projects)


@bp.route("/new", methods=["GET", "POST"])
def create_project():
    """Project creation wizard."""
    if request.method == "POST":
        # TODO: validate form, create project via ProjectRepository,
        # scaffold folder, link requestor, redirect to detail
        pass
    # TODO: load persons, tags, roots for dropdowns
    return render_template("projects/create.html")


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

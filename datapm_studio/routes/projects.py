"""Project routes — list, create, detail, edit."""

from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint("projects", __name__, url_prefix="/projects")


@bp.route("/")
def list_projects():
    """List all projects, most recent first."""
    # TODO: use ProjectRepository to fetch projects
    projects = []
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
    # TODO: fetch project by slug
    project = None
    return render_template("projects/detail.html", project=project)


@bp.route("/<slug>/edit/<field>", methods=["GET", "PUT"])
def edit_field(slug, field):
    """Inline edit a single field (HTMX partial)."""
    # TODO: GET returns edit form partial, PUT saves and returns read partial
    pass

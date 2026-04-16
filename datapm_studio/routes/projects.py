"""Project routes — list, create, detail, edit."""

from __future__ import annotations

from datetime import date
from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for

from data_project_manager.core.templates import (
    BUILT_IN_ARCHETYPES,
    OPTIONAL_FOLDERS,
    SRC_TOGGLES,
    SUBFOLDERS,
)
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

# Field configuration for inline editing
EDITABLE_FIELDS: dict[str, dict[str, Any]] = {
    "status": {
        "label": "Status",
        "type": "select",
        "options": ["active", "paused", "done", "archived"],
    },
    "domain": {"label": "Domain", "type": "text"},
    "description": {"label": "Description", "type": "textarea"},
    "external_url": {"label": "External URL", "type": "url"},
    "request_date": {"label": "Request date", "type": "date"},
    "expected_start": {"label": "Expected start", "type": "date"},
    "expected_end": {"label": "Expected end", "type": "date"},
    "realized_start": {"label": "Realized start", "type": "date"},
    "realized_end": {"label": "Realized end", "type": "date"},
    "estimated_hours": {"label": "Estimated hours", "type": "number"},
}


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
        "external_url": request.form.get("external_url", "").strip(),
        "do_git_init": bool(request.form.get("do_git_init")),
    }


def _selected_folders(form: dict) -> list[str]:
    """Get selected folders from form or archetype defaults."""
    folders = request.form.getlist("folders")
    if folders:
        return folders
    # Default: use archetype folders
    archetype = BUILT_IN_ARCHETYPES.get(form.get("template_used", "analysis"))
    if archetype:
        return list(archetype.folders)
    return []


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

    archetypes = [(key, arch) for key, arch in BUILT_IN_ARCHETYPES.items()]
    selected_folders = _selected_folders(form)

    return render_template(
        "projects/create.html",
        form=form,
        error=error,
        roots=roots,
        archetypes=archetypes,
        optional_folders=OPTIONAL_FOLDERS,
        src_toggles=SRC_TOGGLES,
        subfolders=SUBFOLDERS,
        selected_folders=selected_folders,
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

    # Validate date ordering (only when both are provided)
    if form["expected_start"] and form["expected_end"]:
        if form["expected_end"] < form["expected_start"]:
            return _render_create_form(
                form, error="Expected end date cannot be before expected start date."
            )

    # Resolve selected folders
    selected_folders = request.form.getlist("folders")

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
            optional_folders=selected_folders if selected_folders else None,
            do_git_init=form["do_git_init"],
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

    # Update external_url if provided (create_project doesn't accept it)
    if form["external_url"]:
        ProjectRepository(conn).update(project_id, external_url=form["external_url"])

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
    if project is None:
        from flask import abort

        abort(404)

    conn = _get_conn()

    # Fetch linked persons (requestor, etc.)
    persons = ProjectPersonRepository(conn).list_for_project(project.id)

    # Fetch linked tags
    tags = ProjectTagRepository(conn).list_for_project(project.id)

    # Fetch project root name
    root = None
    if project.root_id:
        root = ProjectRootRepository(conn).get(project.root_id)

    return render_template(
        "projects/detail.html",
        project=project,
        persons=persons,
        tags=tags,
        root=root,
    )


@bp.route("/<slug>/field/<field>")
def read_field(slug, field):
    """Return the read-mode partial for a single field (HTMX target for cancel)."""
    from flask import abort

    if field not in EDITABLE_FIELDS:
        abort(400)

    repo = _get_repo()
    project = repo.get_by_slug(slug)
    if project is None:
        abort(404)

    if field == "description":
        return render_template(
            "projects/partials/_description_read.html",
            project=project,
            slug=slug,
        )

    if field == "status":
        return render_template(
            "projects/partials/_status_read.html",
            project=project,
        )

    cfg = EDITABLE_FIELDS[field]
    value = getattr(project, field, None)
    return render_template(
        "projects/partials/_field_read.html",
        slug=slug,
        field=field,
        label=cfg["label"],
        value=value,
    )


@bp.route("/<slug>/edit/<field>", methods=["GET", "POST"])
def edit_field(slug, field):
    """Inline edit a single field (HTMX partial).

    GET returns the edit form partial.
    POST validates, saves via ProjectRepository.update(), and returns read partial.
    """
    from flask import abort

    if field not in EDITABLE_FIELDS:
        abort(400)

    repo = _get_repo()
    project = repo.get_by_slug(slug)
    if project is None:
        abort(404)

    cfg = EDITABLE_FIELDS[field]

    if request.method == "GET":
        value = getattr(project, field, None)
        if field == "description":
            return render_template(
                "projects/partials/_description_edit.html",
                slug=slug,
                value=value,
            )
        if field == "status":
            return render_template(
                "projects/partials/_status_edit.html",
                slug=slug,
                value=value,
                options=cfg["options"],
            )
        return render_template(
            "projects/partials/_field_edit.html",
            slug=slug,
            field=field,
            label=cfg["label"],
            value=value,
            field_type=cfg["type"],
            options=cfg.get("options"),
        )

    # POST — save the field
    raw_value = request.form.get("value", "").strip()
    save_value: str | float | None = raw_value or None

    # Type-specific coercion
    if field == "estimated_hours" and raw_value:
        try:
            save_value = float(raw_value)
        except ValueError:
            return _render_edit_with_error(
                slug, field, cfg, raw_value, "Must be a number."
            )

    # Date ordering validation
    error = _validate_dates(project, field, raw_value)
    if error:
        return _render_edit_with_error(slug, field, cfg, raw_value, error)

    repo.update(project.id, **{field: save_value})

    # When status is set to "done", redirect to the close-out checklist
    if field == "status" and save_value == "done":
        from flask import make_response

        resp = make_response("")
        resp.headers["HX-Redirect"] = url_for("closeout.checklist", slug=slug)
        return resp

    # Re-fetch project to get updated value
    project = repo.get_by_slug(slug)

    if field == "description":
        return render_template(
            "projects/partials/_description_read.html",
            project=project,
            slug=slug,
        )

    if field == "status":
        return render_template(
            "projects/partials/_status_read.html",
            project=project,
        )

    value = getattr(project, field, None)
    return render_template(
        "projects/partials/_field_read.html",
        slug=slug,
        field=field,
        label=cfg["label"],
        value=value,
    )


def _render_edit_with_error(slug: str, field: str, cfg: dict, value: str, error: str):
    """Re-render the edit form with an error message."""
    if field == "description":
        return render_template(
            "projects/partials/_description_edit.html",
            slug=slug,
            value=value,
            error=error,
        )
    if field == "status":
        return render_template(
            "projects/partials/_status_edit.html",
            slug=slug,
            value=value,
            options=cfg["options"],
            error=error,
        )
    return render_template(
        "projects/partials/_field_edit.html",
        slug=slug,
        field=field,
        label=cfg["label"],
        value=value,
        field_type=cfg["type"],
        options=cfg.get("options"),
        error=error,
    )


def _validate_dates(project, field: str, new_value: str) -> str | None:
    """Validate date ordering when editing a date field.

    Returns an error message if invalid, None if OK.
    """
    if field not in (
        "expected_start",
        "expected_end",
        "realized_start",
        "realized_end",
    ):
        return None

    if not new_value:
        return None

    if field == "expected_end":
        start = project.expected_start
        if start and new_value < start:
            return "Expected end cannot be before expected start."
    elif field == "expected_start":
        end = project.expected_end
        if end and new_value > end:
            return "Expected start cannot be after expected end."
    elif field == "realized_end":
        start = project.realized_start
        if start and new_value < start:
            return "Realized end cannot be before realized start."
    elif field == "realized_start":
        end = project.realized_end
        if end and new_value > end:
            return "Realized start cannot be after realized end."

    return None


# ── Person relation management ──


def _get_project_or_404(slug: str):
    """Get a project by slug or abort 404."""
    from flask import abort

    repo = _get_repo()
    project = repo.get_by_slug(slug)
    if project is None:
        abort(404)
    return project


def _render_persons_section(project):
    """Render the persons section partial."""
    conn = _get_conn()
    persons = ProjectPersonRepository(conn).list_for_project(project.id)
    return render_template(
        "projects/partials/_persons_section.html",
        project=project,
        persons=persons,
    )


def _render_tags_section(project):
    """Render the tags section partial."""
    conn = _get_conn()
    tags = ProjectTagRepository(conn).list_for_project(project.id)
    return render_template(
        "projects/partials/_tags_section.html",
        project=project,
        tags=tags,
    )


@bp.route("/<slug>/persons/add-form")
def add_person_form(slug):
    """Return the inline form for adding a person to a project."""
    _ = _get_project_or_404(slug)

    selected_person = None
    person_id = request.args.get("person_id", "").strip()
    if person_id:
        conn = _get_conn()
        selected_person = PersonRepository(conn).get(person_id)

    return render_template(
        "projects/partials/_person_add_form.html",
        slug=slug,
        selected_person=selected_person,
    )


@bp.route("/<slug>/persons/search")
def search_person_for_detail(slug):
    """HTMX endpoint: person search dropdown for project detail add-person form."""
    q = request.args.get("q", "").strip().lower()
    conn = _get_conn()
    all_persons = PersonRepository(conn).list(current_only=True)

    if q:
        persons = [
            p
            for p in all_persons
            if q in p.first_name.lower()
            or q in p.last_name.lower()
            or q in f"{p.first_name} {p.last_name}".lower()
            or (p.function_title is not None and q in p.function_title.lower())
            or (p.department is not None and q in p.department.lower())
        ]
    else:
        persons = all_persons

    return render_template(
        "projects/partials/_person_dropdown_detail.html",
        persons=persons,
        slug=slug,
    )


@bp.route("/<slug>/persons/add", methods=["POST"])
def add_person(slug):
    """Add a person to a project with a role."""
    project = _get_project_or_404(slug)

    person_id = request.form.get("person_id", "").strip()
    role = request.form.get("role", "").strip()

    if not person_id or not role:
        return render_template(
            "projects/partials/_person_add_form.html",
            slug=slug,
            error="Person and role are required.",
        )

    conn = _get_conn()
    ProjectPersonRepository(conn).add(
        project_id=project.id,
        person_id=person_id,
        role=role,
    )
    return _render_persons_section(project)


@bp.route("/<slug>/persons/remove", methods=["POST"])
def remove_person(slug):
    """Remove a person-role link from a project."""
    project = _get_project_or_404(slug)

    person_id = request.form.get("person_id", "").strip()
    role = request.form.get("role", "").strip()

    if person_id and role:
        conn = _get_conn()
        ProjectPersonRepository(conn).remove(
            project_id=project.id,
            person_id=person_id,
            role=role,
        )
    return _render_persons_section(project)


# ── Tag relation management ──


@bp.route("/<slug>/tags/add-form")
def add_tag_form(slug):
    """Return the inline form for adding a tag to a project."""
    _ = _get_project_or_404(slug)

    selected_tag = None
    tag_id = request.args.get("tag_id", "").strip()
    if tag_id:
        conn = _get_conn()
        selected_tag = TagRepository(conn).get(tag_id)

    return render_template(
        "projects/partials/_tag_add_form.html",
        slug=slug,
        selected_tag=selected_tag,
    )


@bp.route("/<slug>/tags/search")
def search_tag_for_detail(slug):
    """HTMX endpoint: tag search dropdown for project detail add-tag form."""
    q = request.args.get("q", "").strip().lower()
    conn = _get_conn()
    all_tags = TagRepository(conn).list()

    if q:
        tags = [t for t in all_tags if q in t.name.lower()]
    else:
        tags = all_tags

    return render_template(
        "projects/partials/_tag_dropdown_detail.html",
        tags=tags,
        query=q,
        slug=slug,
    )


@bp.route("/<slug>/tags/create-and-select", methods=["POST"])
def create_and_select_tag(slug):
    """Create a new tag and return the add-tag form with it selected."""
    _ = _get_project_or_404(slug)

    name = request.form.get("name", "").strip()
    if not name:
        return render_template(
            "projects/partials/_tag_add_form.html",
            slug=slug,
            error="Tag name is required.",
        )

    conn = _get_conn()
    tag = TagRepository(conn).create(name=name)
    return render_template(
        "projects/partials/_tag_add_form.html",
        slug=slug,
        selected_tag=tag,
    )


@bp.route("/<slug>/tags/add", methods=["POST"])
def add_tag(slug):
    """Add a tag to a project."""
    project = _get_project_or_404(slug)

    tag_id = request.form.get("tag_id", "").strip()

    if not tag_id:
        return render_template(
            "projects/partials/_tag_add_form.html",
            slug=slug,
            error="Please select a tag.",
        )

    conn = _get_conn()
    ProjectTagRepository(conn).add(project_id=project.id, tag_id=tag_id)
    return _render_tags_section(project)


@bp.route("/<slug>/tags/remove", methods=["POST"])
def remove_tag(slug):
    """Remove a tag from a project."""
    project = _get_project_or_404(slug)

    tag_id = request.form.get("tag_id", "").strip()

    if tag_id:
        conn = _get_conn()
        ProjectTagRepository(conn).remove(project_id=project.id, tag_id=tag_id)
    return _render_tags_section(project)

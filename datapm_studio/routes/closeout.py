"""Close-out routes — project completion checklist."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from data_project_manager.db.repositories.data_file import DataFileRepository
from data_project_manager.db.repositories.person import (
    PersonRepository,
    ProjectPersonRepository,
)
from data_project_manager.db.repositories.project import (
    ProjectRepository,
    ProjectRootRepository,
)

from datapm_studio.services.closeout import analyze_gaps
from datapm_studio.services.scanning import find_untracked_files

bp = Blueprint("closeout", __name__)

# Fields that can be fixed inline on the closeout page.
INLINE_FIX_FIELDS = {"description", "realized_start", "realized_end"}


def _get_conn():
    """Get the database connection from the current app."""
    from flask import current_app

    return current_app.get_db()  # type: ignore[attr-defined]


def _get_project_or_404(slug):
    """Fetch a project by slug or abort with 404."""
    project = ProjectRepository(_get_conn()).get_by_slug(slug)
    if project is None:
        abort(404)
    return project


def _render_checklist(project, conn):
    """Build the full checklist context and render the template."""
    gaps = analyze_gaps(project, conn)

    # Run filesystem scan if the project has a folder
    untracked_files: list = []
    if project.root_id and project.relative_path:
        root = ProjectRootRepository(conn).get(project.root_id)
        if root:
            from pathlib import Path

            project_path = Path(root.absolute_path) / project.relative_path
            data_files = DataFileRepository(conn).list_for_project(project.id)
            registered = {f.file_path for f in data_files}
            untracked_files = find_untracked_files(project_path, registered)

    has_critical = any(g.severity == "critical" for g in gaps)
    can_close = not has_critical and project.status != "done"

    return render_template(
        "closeout/checklist.html",
        project=project,
        gaps=gaps,
        untracked_files=untracked_files,
        can_close=can_close,
        has_critical=has_critical,
    )


def _render_checklist_content(project, conn):
    """Render just the checklist content partial (for HTMX swaps)."""
    gaps = analyze_gaps(project, conn)

    untracked_files: list = []
    if project.root_id and project.relative_path:
        root = ProjectRootRepository(conn).get(project.root_id)
        if root:
            from pathlib import Path

            project_path = Path(root.absolute_path) / project.relative_path
            data_files = DataFileRepository(conn).list_for_project(project.id)
            registered = {f.file_path for f in data_files}
            untracked_files = find_untracked_files(project_path, registered)

    has_critical = any(g.severity == "critical" for g in gaps)
    can_close = not has_critical and project.status != "done"

    return render_template(
        "closeout/_checklist_content.html",
        project=project,
        gaps=gaps,
        untracked_files=untracked_files,
        can_close=can_close,
        has_critical=has_critical,
    )


@bp.route("/projects/<slug>/closeout")
def checklist(slug):
    """Show the close-out checklist for a project."""
    conn = _get_conn()
    project = _get_project_or_404(slug)
    return _render_checklist(project, conn)


@bp.route("/projects/<slug>/closeout/done", methods=["POST"])
def mark_done(slug):
    """Mark the project as done and set realized_end."""
    conn = _get_conn()
    repo = ProjectRepository(conn)
    project = _get_project_or_404(slug)

    gaps = analyze_gaps(project, conn)
    has_critical = any(g.severity == "critical" for g in gaps)
    if has_critical:
        flash("Cannot close project — critical gaps remain.", "error")
        return redirect(url_for("closeout.checklist", slug=slug))

    updates: dict = {"status": "done"}
    if not project.realized_end:
        updates["realized_end"] = date.today().isoformat()

    repo.update(project.id, **updates)
    flash("Project marked as done.", "success")
    return redirect(url_for("projects.detail", slug=slug))


# ── Inline fix routes ──────────────────────────────────────────────


@bp.route("/projects/<slug>/closeout/fix/<field>", methods=["GET"])
def fix_field_form(slug, field):
    """Return an inline edit form for a fixable field (HTMX partial)."""
    if field not in INLINE_FIX_FIELDS:
        abort(400)

    project = _get_project_or_404(slug)
    value = getattr(project, field, None)

    return render_template(
        "closeout/_fix_form.html",
        slug=slug,
        field=field,
        value=value,
    )


@bp.route("/projects/<slug>/closeout/fix/<field>", methods=["POST"])
def fix_field_save(slug, field):
    """Save an inline fix and return the re-rendered checklist content."""
    if field not in INLINE_FIX_FIELDS:
        abort(400)

    conn = _get_conn()
    repo = ProjectRepository(conn)
    project = _get_project_or_404(slug)

    raw_value = request.form.get("value", "").strip()
    save_value: str | None = raw_value or None

    repo.update(project.id, **{field: save_value})

    # Re-fetch and return the full checklist content
    project = repo.get_by_slug(slug)
    return _render_checklist_content(project, conn)


@bp.route("/projects/<slug>/closeout/fix/requestor", methods=["GET"])
def fix_requestor_form(slug):
    """Return the person search dropdown for adding a requestor (HTMX partial)."""
    project = _get_project_or_404(slug)
    selected_person = None

    person_id = request.args.get("person_id")
    if person_id:
        selected_person = PersonRepository(_get_conn()).get(person_id)

    return render_template(
        "closeout/_fix_requestor.html",
        slug=slug,
        project=project,
        selected_person=selected_person,
    )


@bp.route("/projects/<slug>/closeout/fix/requestor/search")
def fix_requestor_search(slug):
    """Search persons for the requestor dropdown on closeout page."""
    _get_project_or_404(slug)
    q = request.args.get("q", "").strip().lower()
    persons = PersonRepository(_get_conn()).list(current_only=True)

    if q:
        persons = [
            p
            for p in persons
            if q in p.first_name.lower()
            or q in p.last_name.lower()
            or q in f"{p.first_name} {p.last_name}".lower()
            or (p.function_title is not None and q in p.function_title.lower())
            or (p.department is not None and q in p.department.lower())
        ]

    return render_template(
        "closeout/_fix_requestor_dropdown.html",
        slug=slug,
        persons=persons,
    )


@bp.route("/projects/<slug>/closeout/fix/requestor", methods=["POST"])
def fix_requestor_save(slug):
    """Add the selected person as requestor and re-render checklist."""
    conn = _get_conn()
    project = _get_project_or_404(slug)

    person_id = request.form.get("person_id", "").strip()
    if not person_id:
        # Return the form with no selection — let the user try again
        return render_template(
            "closeout/_fix_requestor.html",
            slug=slug,
            project=project,
            selected_person=None,
        )

    ProjectPersonRepository(conn).add(
        project_id=project.id, person_id=person_id, role="requestor"
    )

    # Re-fetch and return the full checklist content
    project = ProjectRepository(conn).get_by_slug(slug)
    return _render_checklist_content(project, conn)

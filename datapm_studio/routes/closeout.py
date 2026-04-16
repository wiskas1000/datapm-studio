"""Close-out routes — project completion checklist."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, url_for

from data_project_manager.db.repositories.data_file import DataFileRepository
from data_project_manager.db.repositories.project import (
    ProjectRepository,
    ProjectRootRepository,
)

from datapm_studio.services.closeout import analyze_gaps
from datapm_studio.services.scanning import find_untracked_files

bp = Blueprint("closeout", __name__)


def _get_conn():
    """Get the database connection from the current app."""
    from flask import current_app

    return current_app.get_db()  # type: ignore[attr-defined]


@bp.route("/projects/<slug>/closeout")
def checklist(slug):
    """Show the close-out checklist for a project.

    Computes gaps on the fly (no stored state).
    """
    conn = _get_conn()
    repo = ProjectRepository(conn)
    project = repo.get_by_slug(slug)
    if project is None:
        abort(404)

    # Run gap analysis
    gaps = analyze_gaps(project, conn)

    # Run filesystem scan if the project has a folder
    untracked_files: list = []
    if project.root_id and project.relative_path:
        root = ProjectRootRepository(conn).get(project.root_id)
        if root:
            from pathlib import Path

            project_path = Path(root.absolute_path) / project.relative_path
            # Get registered file paths for comparison
            data_files = DataFileRepository(conn).list_for_project(project.id)
            registered = {f.file_path for f in data_files}
            untracked_files = find_untracked_files(project_path, registered)

    # Determine if "mark as done" is allowed (no critical gaps)
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


@bp.route("/projects/<slug>/closeout/done", methods=["POST"])
def mark_done(slug):
    """Mark the project as done and set realized_end."""
    conn = _get_conn()
    repo = ProjectRepository(conn)
    project = repo.get_by_slug(slug)
    if project is None:
        abort(404)

    # Re-check for critical gaps before allowing close
    gaps = analyze_gaps(project, conn)
    has_critical = any(g.severity == "critical" for g in gaps)
    if has_critical:
        flash("Cannot close project — critical gaps remain.", "error")
        return redirect(url_for("closeout.checklist", slug=slug))

    # Set status to "done" and realized_end to today (if not already set)
    updates: dict = {"status": "done"}
    if not project.realized_end:
        updates["realized_end"] = date.today().isoformat()

    repo.update(project.id, **updates)
    flash("Project marked as done.", "success")
    return redirect(url_for("projects.detail", slug=slug))

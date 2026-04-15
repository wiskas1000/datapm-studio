"""Tag routes — search dropdown, create inline."""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from data_project_manager.db.repositories.tag import TagRepository

bp = Blueprint("tags", __name__, url_prefix="/tags")


def _get_repo() -> TagRepository:
    """Get a TagRepository using the current app's DB connection."""
    from flask import current_app

    conn = current_app.get_db()  # type: ignore[attr-defined]
    return TagRepository(conn)


@bp.route("/search")
def search_tags():
    """HTMX endpoint: return matching tags as multi-select options.

    Query param: q (search string)
    """
    q = request.args.get("q", "").strip().lower()
    repo = _get_repo()
    all_tags = repo.list()

    if q:
        tags = [t for t in all_tags if q in t.name.lower()]
    else:
        tags = all_tags

    return render_template("tags/_dropdown.html", tags=tags, query=q)


@bp.route("/new-inline", methods=["POST"])
def new_inline():
    """HTMX endpoint: create a new tag on the fly and return it as JSON.

    Used by the createAndSelectTag() JS function to add a tag chip.
    """
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "Tag name is required"}), 400

    repo = _get_repo()
    tag = repo.create(name=name)
    return jsonify({"id": tag.id, "name": tag.name})

"""Search routes — full-text search across projects."""

from __future__ import annotations

from flask import Blueprint, render_template, request

bp = Blueprint("search", __name__, url_prefix="/search")


@bp.route("/")
def search():
    """Search projects using FTS5.

    Query param: q (search string)
    """
    q = request.args.get("q", "").strip()
    results = []
    if q:
        # TODO: use existing FTS5 search from core
        pass
    return render_template("search/results.html", results=results, query=q)

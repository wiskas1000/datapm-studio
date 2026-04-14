"""Tag routes — search dropdown, create inline."""

from flask import Blueprint, render_template, request

bp = Blueprint("tags", __name__, url_prefix="/tags")


@bp.route("/search")
def search_tags():
    """HTMX endpoint: return matching tags as multi-select options.

    Query param: q (search string)
    """
    q = request.args.get("q", "").strip()
    # TODO: TagRepository.search(q)
    tags = []
    return render_template("tags/_dropdown.html", tags=tags, query=q)


@bp.route("/new-inline", methods=["POST"])
def new_inline():
    """HTMX endpoint: create a new tag on the fly and return it as a selected chip."""
    # TODO: TagRepository.create(name=request.form["name"])
    pass

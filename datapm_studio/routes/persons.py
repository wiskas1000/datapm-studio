"""Person routes — list, search dropdown, create inline."""

from __future__ import annotations

from flask import Blueprint, render_template, request

bp = Blueprint("persons", __name__, url_prefix="/persons")


@bp.route("/")
def list_persons():
    """List all current persons."""
    # TODO: PersonRepository.list_current()
    persons = []
    return render_template("persons/list.html", persons=persons)


@bp.route("/search")
def search_persons():
    """HTMX endpoint: return matching persons as dropdown items.

    Used by the searchable person dropdown in project forms.
    Query param: q (search string)
    """
    q = request.args.get("q", "").strip()
    # TODO: PersonRepository.search(q) — filter by first_name, last_name
    persons = []
    return render_template("persons/_dropdown.html", persons=persons, query=q)


@bp.route("/new-inline", methods=["GET", "POST"])
def new_inline():
    """HTMX endpoint: inline form to add a new person without leaving the page.

    GET returns the mini-form. POST creates the person and returns
    the selected-person partial.
    """
    if request.method == "POST":
        # TODO: PersonRepository.create(...)
        pass
    return render_template("persons/_inline_form.html")

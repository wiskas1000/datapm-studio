"""Person routes — list, search dropdown, create inline."""

from __future__ import annotations

from flask import Blueprint, render_template, request

from data_project_manager.db.repositories.person import PersonRepository

bp = Blueprint("persons", __name__, url_prefix="/persons")


def _get_repo() -> PersonRepository:
    """Get a PersonRepository using the current app's DB connection."""
    from flask import current_app

    conn = current_app.get_db()  # type: ignore[attr-defined]
    return PersonRepository(conn)


@bp.route("/")
def list_persons():
    """List all current persons."""
    repo = _get_repo()
    persons = repo.list(current_only=True)
    return render_template("persons/list.html", persons=persons)


@bp.route("/search")
def search_persons():
    """HTMX endpoint: return matching persons as dropdown items.

    Used by the searchable person dropdown in project forms.
    Query param: q (search string)
    """
    q = request.args.get("q", "").strip().lower()
    repo = _get_repo()
    all_persons = repo.list(current_only=True)

    if q:
        persons = [
            p
            for p in all_persons
            if q in p.first_name.lower()
            or q in p.last_name.lower()
            or q in f"{p.first_name} {p.last_name}".lower()
        ]
    else:
        persons = all_persons

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

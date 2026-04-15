"""Person routes — list, search dropdown, create inline."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

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
    the selected-person partial so the new person is immediately selected.
    """
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip() or None

        if not first_name or not last_name:
            return render_template(
                "persons/_inline_form.html",
                error="First and last name are required.",
                first_name=first_name,
                last_name=last_name,
                email=email,
            )

        repo = _get_repo()
        person = repo.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        return render_template("persons/_selected.html", person=person)

    return render_template("persons/_inline_form.html")


@bp.route("/new", methods=["GET", "POST"])
def new_page():
    """Add a new person from the persons page.

    GET returns a card with the form (HTMX partial).
    POST creates the person and redirects to the persons list.
    """
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip() or None
        function_title = request.form.get("function_title", "").strip() or None
        department = request.form.get("department", "").strip() or None

        if not first_name or not last_name:
            return render_template(
                "persons/_page_form.html",
                error="First and last name are required.",
                first_name=first_name,
                last_name=last_name,
                email=email,
                function_title=function_title,
                department=department,
            )

        repo = _get_repo()
        repo.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            function_title=function_title,
            department=department,
        )
        flash(f"Added {first_name} {last_name}.", "success")
        return redirect(url_for("persons.list_persons"))

    return render_template("persons/_page_form.html")

"""Person routes — list, search dropdown, create inline, detail, edit (SCD2)."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from data_project_manager.db.repositories.changelog import ChangeLogRepository
from data_project_manager.db.repositories.person import PersonRepository

bp = Blueprint("persons", __name__, url_prefix="/persons")


def _get_conn():
    """Get the database connection from the current app."""
    from flask import current_app

    return current_app.get_db()  # type: ignore[attr-defined]


def _get_repo() -> PersonRepository:
    """Get a PersonRepository using the current app's DB connection."""
    return PersonRepository(_get_conn())


def _get_repo_with_changelog() -> PersonRepository:
    """Get a PersonRepository with changelog wired up for SCD2 versioning."""
    conn = _get_conn()
    changelog = ChangeLogRepository(conn)
    return PersonRepository(conn, changelog=changelog)


@bp.route("/")
def list_persons():
    """List all current persons, with optional search filter."""
    repo = _get_repo()
    all_persons = repo.list(current_only=True)

    q = request.args.get("q", "").strip().lower()
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

    # If HTMX request (filter), return just the table partial
    if request.headers.get("HX-Request"):
        return render_template("persons/_table.html", persons=persons)

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


@bp.route("/<person_id>")
def detail(person_id):
    """Show person detail with all fields and version history."""
    from flask import abort

    repo = _get_repo()
    person = repo.get(person_id)
    if person is None:
        abort(404)

    conn = _get_conn()
    changelog = ChangeLogRepository(conn)
    history = changelog.list_for_entity("person", person_id)

    return render_template(
        "persons/detail.html",
        person=person,
        history=history,
    )


@bp.route("/<person_id>/edit", methods=["GET", "POST"])
def edit(person_id):
    """Edit a person (SCD2 versioning).

    GET returns the edit form partial.
    POST creates a new version via PersonRepository.create_new_version().
    """
    from flask import abort

    repo = _get_repo()
    person = repo.get(person_id)
    if person is None:
        abort(404)

    if request.method == "GET":
        return render_template("persons/_edit_form.html", person=person)

    # POST — collect form data
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip() or None
    function_title = request.form.get("function_title", "").strip() or None
    department = request.form.get("department", "").strip() or None

    if not first_name or not last_name:
        return render_template(
            "persons/_edit_form.html",
            person=person,
            error="First and last name are required.",
        )

    # Determine which fields actually changed
    changes: dict[str, str | None] = {}
    if first_name != person.first_name:
        changes["first_name"] = first_name
    if last_name != person.last_name:
        changes["last_name"] = last_name
    if email != person.email:
        changes["email"] = email
    if function_title != person.function_title:
        changes["function_title"] = function_title
    if department != person.department:
        changes["department"] = department

    if not changes:
        flash("No changes to save.", "info")
        return redirect(url_for("persons.detail", person_id=person_id))

    # Create new SCD2 version
    versioned_repo = _get_repo_with_changelog()
    new_person = versioned_repo.create_new_version(person_id, **changes)

    flash(
        f"Updated {new_person.first_name} {new_person.last_name}.",
        "success",
    )
    return redirect(url_for("persons.detail", person_id=new_person.id))

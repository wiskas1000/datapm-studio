"""Flask application factory for datapm-studio."""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from data_project_manager.config.loader import load_config
from data_project_manager.db.connection import get_connection


def create_app(*, db_path: str | Path | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        db_path: Override the database path. Used by tests to point at a
            temporary SQLite file instead of the user's real database.
    """
    app = Flask(__name__)
    # Hardcoded key is acceptable: Studio is local single-user, no auth, and
    # sessions are used only for flash messages. Do not reuse this app in a
    # multi-user or networked deployment without replacing the key.
    app.secret_key = "datapm-studio-local-only"

    # Load datapm config
    app.config["DATAPM"] = load_config()

    # Store DB path so routes can pass it to core functions that open
    # their own connections (e.g. create_project).
    app.config["DATAPM_DB_PATH"] = db_path

    def get_db():
        """Return a database connection, cached on the app context."""
        from flask import g

        if "db" not in g:
            g.db = get_connection(db_path)
        return g.db

    app.get_db = get_db  # type: ignore[attr-defined]

    @app.teardown_appcontext
    def close_db(exc):
        from flask import g

        db = g.pop("db", None)
        if db is not None:
            db.close()

    # Register blueprints
    from datapm_studio.routes.closeout import bp as closeout_bp
    from datapm_studio.routes.persons import bp as persons_bp
    from datapm_studio.routes.projects import bp as projects_bp
    from datapm_studio.routes.search import bp as search_bp
    from datapm_studio.routes.tags import bp as tags_bp

    app.register_blueprint(projects_bp)
    app.register_blueprint(persons_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(closeout_bp)

    # Index route redirects to projects
    @app.route("/")
    def index():
        from flask import redirect, url_for

        return redirect(url_for("projects.list_projects"))

    return app


def main() -> None:
    """Entry point for `datapm-studio` CLI command."""
    app = create_app()
    app.run(port=5555, debug=False)

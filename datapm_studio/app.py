"""Flask application factory for datapm-studio."""

from flask import Flask

from datapm_studio.config import load_datapm_config


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load datapm config
    datapm_config = load_datapm_config()
    app.config["DATAPM"] = datapm_config

    # Register blueprints
    from datapm_studio.routes.projects import bp as projects_bp
    from datapm_studio.routes.persons import bp as persons_bp
    from datapm_studio.routes.tags import bp as tags_bp
    from datapm_studio.routes.search import bp as search_bp
    from datapm_studio.routes.closeout import bp as closeout_bp

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

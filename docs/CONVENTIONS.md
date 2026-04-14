# Coding Conventions — datapm-studio

Inherited from `data-project-manager` where applicable. All code — Opus or Sonnet — must follow these.

## Python Naming (PEP 8 baseline + project-specific)

| What | Convention | Example |
|------|-----------|---------|
| Classes | PascalCase, noun | `ProjectRoutes`, `GapAnalyzer` |
| Functions/methods | snake_case, verb phrase | `create_project()`, `search_persons()` |
| Private helpers | `_` prefix | `_parse_form_data()`, `_build_gap_list()` |
| Constants | UPPER_SNAKE | `DEFAULT_PORT`, `IGNORE_PATTERNS` |
| Flask blueprints | lowercase, named after entity | `bp = Blueprint("projects", ...)` |
| Route functions | `verb_noun` or `noun` for GET | `list_projects()`, `create_project()`, `detail()` |
| Template files | `noun.html` for pages, `_noun.html` for HTMX partials | `list.html`, `_dropdown.html` |
| DB connections | `conn` (never `connection`, `db`, `cursor`) | `conn = get_connection()` |
| UUIDs | `{entity}_id` as parameter | `project_id`, `person_id` |
| Timestamps | `created_at = now_iso()` | Never `ts`, `timestamp`, `time` |
| Boolean params | `is_` or `do_` prefix | `is_adhoc`, `do_git_init` |
| Optional return | `Entity | None` | `def get(...) -> Project | None` |
| Keyword-only args | After `*` in signatures | `def create(self, *, title: str, ...)` |

## Flask / Web Conventions

| What | Convention | Example |
|------|-----------|---------|
| App factory | `create_app()` in `app.py` | `app = create_app()` |
| Blueprints | One per entity group, registered in `create_app()` | `projects_bp`, `persons_bp` |
| URL structure | Plural nouns, RESTful | `/projects`, `/projects/<slug>`, `/persons` |
| HTMX endpoints | Same blueprint, return HTML partials | `/persons/search` returns `_dropdown.html` |
| Form handling | GET shows form, POST processes it | `methods=["GET", "POST"]` |
| Redirects | Use `url_for()`, 303 for POST-redirect-GET | `redirect(url_for("projects.detail", slug=slug), 303)` |
| Flash messages | Use `flask.flash()` with categories | `flash("Project created", "success")` |

## Template Conventions

| What | Convention | Example |
|------|-----------|---------|
| Page templates | Extend `base.html` | `{% extends "base.html" %}` |
| HTMX partials | Start with `_`, no `base.html` extend | `_dropdown.html` — bare HTML fragment |
| Block names | `title`, `content` | `{% block content %}...{% endblock %}` |
| Variables | snake_case | `{{ project.request_date }}` |
| Loops | Descriptive iterator names | `{% for person in persons %}` |

## CSS Conventions

| What | Convention |
|------|-----------|
| Framework | Custom CSS design system in `static/css/style.css` — use CSS variables and component classes (`.card`, `.btn`, `.badge-*`) |
| Custom styles | `static/css/style.css` — overrides only |
| Class naming | Plain descriptive, no BEM, no utility classes | 
| JS variables | camelCase (JS standard) |

## SQL Conventions (inherited from core)

Studio should not write SQL — it uses the repository layer. But if raw queries are ever needed:

| What | Convention | Example |
|------|-----------|---------|
| Table names | snake_case, singular | `project`, `data_file` |
| Parameterized | Always `?` placeholders | `conn.execute("... WHERE id = ?", (id,))` |
| Never | f-strings or string formatting in SQL | — |

## File and Module Conventions

| What | Convention | Example |
|------|-----------|---------|
| Routes | `routes/{entity}.py` | `routes/projects.py` |
| Services | `services/{concern}.py` | `services/closeout.py` |
| Templates | `templates/{entity}/{page}.html` | `templates/projects/create.html` |
| Tests | `tests/test_{area}/test_{module}.py` | `tests/test_routes/test_projects.py` |
| Imports | `from __future__ import annotations` at top | All files |

## Function Structure Pattern

```python
def create_project(*, title: str, domain: str | None = None) -> Project:
    """Create a new project and scaffold its folder.

    Args:
        title: Human-readable project title.
        domain: Optional subject area.

    Returns:
        The newly created :class:`Project`.
    """
    # 1. Validate
    # 2. Call repository
    # 3. Return result
```

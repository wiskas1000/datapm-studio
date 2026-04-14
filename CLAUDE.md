# CLAUDE.md — datapm-studio

## Project Overview

datapm-studio is a local Flask + HTMX web UI for managing analytical project metadata. It imports from `data-project-manager` (the core CLI/library) and reads/writes the same SQLite database. It exists because metadata entry via CLI flags is too tedious — smart dropdowns and forms make the difference between "I actually capture metadata" and "I skip it every time."

## What This Tool Is

- A web interface to browse, create, and edit project metadata
- A project creation wizard with searchable dropdowns for people, tags, and dimensions
- A project close-out checklist that surfaces missing metadata
- A person management UI (search, select, add new — reusing the existing SCD2 Person table)
- A companion to `datapm` — launched via `datapm web`, uses the same DB

## What This Tool Is NOT (for now)

- Not a replacement for `datapm new` on the CLI — both paths create projects
- Not a dashboard or monitoring tool — no always-on service, no charts
- Not a run tracker — script execution logs stay in text files
- Not a data entry tool for DataFile/Query/Deliverable — those are populated by scripts via the Python API; Studio shows them read-only in v0.1.0
- Not a Jira/DevOps integration — that's post-v1.0
- Not a file manager — it doesn't move, copy, or delete files on disk
- Not authenticated — local single-user only, no login

## Relationship to data-project-manager

- **Core repo**: the `data-project-manager` package (installed via pip/uv)
- **What Studio imports**: `data_project_manager.db.repositories.{entity}` (e.g., `.project.ProjectRepository`, `.person.PersonRepository`), `data_project_manager.db.connection.get_connection`, `data_project_manager.core.*` (project creation, slug generation, search)
- **Boundary rule**: if the logic is about the data model, schema, or business rules (SCD2 versioning, slug generation, changelog entries), it belongs in the core. If it's about presenting forms, handling HTTP requests, or computing UI-specific views (gap analysis for close-out), it belongs in Studio.
- **Database**: Studio reads/writes `~/.datapm/projects.db` — the same file the CLI uses. No separate database. Ever.
- **Config**: Studio reads `~/.datapm/config.json`. Studio-specific settings go under a `"studio"` key if ever needed.

## Tech Stack

| Component | Choice | Notes |
|-----------|--------|-------|
| Package manager | uv | All commands use `uv run` |
| Python | ≥ 3.10 | |
| Web framework | Flask ≥ 3.0 | Runtime dependency |
| Frontend interactivity | HTMX 2.x | Loaded from CDN, no npm |
| CSS | Custom design system | DM Sans / DM Mono from Google Fonts CDN, dark/light theme toggle |
| Templates | Jinja2 (via Flask) | No extra dependency |
| Database | Existing projects.db | Via core's repository layer |
| Testing | pytest | Dev dependency |
| Linting | ruff | Dev dependency |
| Type checking | pyright | Dev dependency |

No JavaScript framework. No npm. No build step.

## Running the Tool

```bash
# Install dependencies (including dev)
uv sync --extra dev

# Launch the web UI
uv run datapm web

# Run tests
uv run pytest

# Lint (format first, then check)
uv run ruff format . && uv run ruff check .

# Type check
uv run pyright datapm_studio/
```

## Repository Structure

```
datapm-studio/
├── ARCHITECTURE.md
├── CLAUDE.md                ← this file
├── PLAN.md                  ← milestones, acceptance criteria, PR breakdown
├── README.md
├── pyproject.toml
├── docs/
│   └── CONVENTIONS.md       ← naming, SQL style, file patterns
├── datapm_studio/
│   ├── __init__.py
│   ├── app.py               ← Flask app factory (create_app)
│   ├── config.py            ← reads ~/.datapm/config.json
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── projects.py      ← CRUD + creation wizard
│   │   ├── persons.py       ← person management + search dropdown
│   │   ├── tags.py          ← tag search + inline create
│   │   ├── search.py        ← FTS5 search across projects
│   │   └── closeout.py      ← project close-out checklist
│   ├── services/
│   │   ├── __init__.py
│   │   ├── closeout.py      ← gap analysis logic
│   │   └── scanning.py      ← find untracked files in project folders
│   ├── templates/
│   │   ├── base.html        ← layout, nav, HTMX + custom CSS, theme toggle
│   │   ├── projects/
│   │   │   ├── list.html
│   │   │   ├── create.html  ← new project wizard
│   │   │   ├── detail.html
│   │   │   └── edit.html
│   │   ├── persons/
│   │   │   ├── list.html
│   │   │   ├── _dropdown.html    ← HTMX partial
│   │   │   └── _inline_form.html ← HTMX partial
│   │   ├── tags/
│   │   │   └── _dropdown.html
│   │   ├── closeout/
│   │   │   └── checklist.html
│   │   ├── search/
│   │   │   └── results.html
│   │   └── partials/
│   │       └── _flash.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js       ← minimal, only if HTMX can't handle it
└── tests/
    ├── conftest.py          ← Flask test client, temp DB fixtures
    ├── test_routes/
    │   ├── test_projects.py
    │   ├── test_persons.py
    │   └── test_closeout.py
    └── test_services/
        ├── test_closeout.py
        └── test_scanning.py
```

## Design Principles

1. **Companion, not fork.** Always import from `data-project-manager`. Never duplicate core logic. If something is missing in the core, add it there and import it here.
2. **Same database, different door.** Studio reads/writes `projects.db` via the existing repository classes. No separate storage. No sync.
3. **Low-friction or it won't be used.** If capturing metadata takes more effort than skipping it, the tool has failed. Smart dropdowns, auto-complete, and sensible defaults are the priority.
4. **Server-rendered + HTMX.** No JavaScript framework. Templates with HTMX attributes handle all interactivity. Vanilla JS only when HTMX genuinely can't handle it.
5. **Start small, grow when needed.** No new database tables until a real wall is hit. No features beyond the current milestone.

## Branch / Commit / PR Conventions

- **Branches**: `type/short-description` (e.g., `feat/project-create-form`, `fix/person-dropdown`, `test/closeout-gaps`)
- **Commits**: Conventional Commits — `type(scope): description`
  - Types: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`, `style`
  - Scope: module or area (e.g., `routes`, `templates`, `services`, `config`)
- **PR body template**:
  ```
  ## Summary
  What changed and why.

  ## Test plan
  How it was tested. Include commands run and results.
  ```
- Update PLAN.md checkboxes when a milestone item is completed.
- GitHub Project: #6

## Model Workflow

This project uses a two-model workflow:
- **Opus**: planning, architecture, specs, reviews, audits
- **Sonnet**: implementation per spec, tests, commits, PRs

Specs live in `docs/specs/` — one file per milestone or PR group.
Sonnet should follow specs exactly. If a spec is ambiguous or seems wrong, flag it rather than guessing.

## Coding Conventions

See `docs/CONVENTIONS.md` for naming, SQL style, file structure, and function patterns. All code — whether written by Opus or Sonnet — must follow these conventions.

## Testing

- Framework: pytest
- Fixtures: Flask test client + temporary SQLite DB (never the user's real DB)
- Test-first when possible: Opus writes tests during spec phase, Sonnet implements until they pass
- Coverage goal: high, but not a vanity metric — test behavior, not lines
- Run: `uv run pytest`

## Linting Workflow

Always format before checking:
```bash
uv run ruff format . && uv run ruff check .
```

Pre-commit auto-formats and auto-fixes. No `--check` flags.

## Type Checking

Pyright is configured for this project. Run before committing:
```bash
uv run pyright datapm_studio/
```

If the user pastes a Pyright diagnostic, fix the type error precisely — do not suppress with `# type: ignore` unless the error is a false positive and you explain why.

## Current Phase

**Milestone 0 — scaffold + bootstrap.** We are implementing the initial Flask app scaffold, config reader, base template, and empty blueprints. The app should start and serve pages, but business logic is still stubbed.

# datapm-studio — Architecture

## What This Is

datapm-studio is a local web UI for [datapm](https://github.com/your-username/data-project-manager) (data-project-manager). It provides form-based metadata management with smart dropdowns, making it fast to capture project metadata that would be too tedious to type via CLI flags.

It lives in a **separate repository** and **imports from `data_project_manager`**. It adds Flask + HTMX as dependencies. The core `datapm` package remains zero-dependency.

## Design Principles

1. **Same database, different door.** Studio reads and writes `~/.datapm/projects.db` via the existing repository classes. No separate database, no sync.
2. **Low-friction metadata entry.** If it takes more effort to record metadata than to skip it, the tool has failed. Smart dropdowns, auto-complete, and sensible defaults are the priority.
3. **Launch-when-needed.** Started via `datapm web`, runs on localhost, dies when you close it. No background services, no daemon management.
4. **Server-rendered + HTMX.** No JavaScript framework. Flask templates with HTMX attributes handle all interactivity (searchable dropdowns, inline editing, dynamic form sections). Minimal custom JS.
5. **Progressive value.** The tool is useful on day one with just project creation and person selection. Close-out checklists, file scanning, and external integrations come later.

## System Context

```
┌──────────────────────────────────────────────────────────┐
│                    datapm (core)                         │
│  Zero dependencies · CLI · Repository layer · Schema     │
│  uv add data-project-manager                             │
├──────────────────────────────────────────────────────────┤
│                   projects.db                            │
│  SQLite · 16 tables · FTS5 · ~/.datapm/projects.db       │
├──────────────────────────────────────────────────────────┤
│                  datapm-studio                           │
│  Flask + HTMX · Imports from data_project_manager        │
│  uv add datapm-studio                                    │
│  Launched via: datapm web                                │
└──────────────────────────────────────────────────────────┘
```

## How It Integrates With Core

### Database Access

Studio uses the existing repository classes directly:

```python
from data_project_manager.db.repositories.project import ProjectRepository
from data_project_manager.db.repositories.person import PersonRepository
from data_project_manager.db.repositories.tag import TagRepository
from data_project_manager.db.repositories.data_file import DataFileRepository
from data_project_manager.db.repositories.deliverable import DeliverableRepository
from data_project_manager.db.repositories.question import QuestionRepository
from data_project_manager.db.repositories.changelog import ChangeLogRepository
from data_project_manager.db.connection import get_connection
```

It never writes raw SQL. All reads and writes go through the repository layer so that business rules (slug generation, SCD2 versioning, changelog entries) remain consistent whether metadata is entered via CLI, Python scripts, or Studio.

### Launch Mechanism

The core `datapm` CLI gains a single new command:

```
datapm web [--port 5555] [--no-browser]
```

This command checks if `datapm_studio` is importable. If yes, it starts the Flask dev server and opens the browser. If not, it prints a message: `Install datapm-studio for the web UI: uv add datapm-studio`.

Implementation in core (thin wrapper, no Flask dependency):

```python
# In data_project_manager/cli/commands/web.py
def run_web(port=5555, no_browser=False):
    try:
        from datapm_studio.app import create_app
    except ImportError:
        print("Install datapm-studio for the web UI: uv add datapm-studio")
        return
    app = create_app()
    if not no_browser:
        import webbrowser
        webbrowser.open(f"http://localhost:{port}")
    app.run(port=port, debug=False)
```

### Configuration

Studio reads the existing `~/.datapm/config.json` for:
- `roots` — to know where project folders live
- `defaults` — template, git_init, sensitivity
- `preferences.folder_language` — folder names (nl/en)

Studio does **not** have its own config file. If Studio-specific preferences are needed later (e.g., theme, items-per-page), they go under a `"studio"` key in the existing config.

## Package Structure

```
datapm-studio/
├── ARCHITECTURE.md          ← this file
├── CLAUDE.md                ← instructions for Claude Code
├── PLAN.md                  ← milestones, acceptance criteria, PR breakdown
├── README.md
├── pyproject.toml
├── docs/
│   ├── CONVENTIONS.md       ← naming, SQL style, file patterns
│   ├── specs/               ← one spec file per milestone or PR group
│   └── reflections-claude-code-workflow.md  ← lessons from data-project-manager
├── datapm_studio/
│   ├── __init__.py
│   ├── app.py               ← Flask app factory (create_app)
│   ├── config.py             ← reads ~/.datapm/config.json
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── projects.py       ← CRUD + creation wizard
│   │   ├── persons.py        ← person management
│   │   ├── tags.py           ← tag management
│   │   ├── search.py         ← search across projects
│   │   └── closeout.py       ← project close-out checklist
│   ├── services/
│   │   ├── __init__.py
│   │   ├── closeout.py       ← gap analysis logic
│   │   └── scanning.py       ← file system scanning
│   ├── templates/
│   │   ├── base.html          ← layout, HTMX script, navigation
│   │   ├── projects/
│   │   │   ├── list.html
│   │   │   ├── create.html    ← new project wizard
│   │   │   ├── detail.html
│   │   │   └── edit.html
│   │   ├── persons/
│   │   │   ├── list.html
│   │   │   └── _dropdown.html ← HTMX partial for person search
│   │   ├── tags/
│   │   │   └── _dropdown.html
│   │   ├── closeout/
│   │   │   └── checklist.html
│   │   └── partials/
│   │       ├── _flash.html
│   │       └── _search_results.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js         ← minimal JS (if any beyond HTMX)
└── tests/
    ├── conftest.py
    ├── test_routes/
    └── test_services/
```

## Key Screens

### 1. Project Creation Wizard (`/projects/new`)

Single-page form with these sections:

| Section | Fields | UX |
|---------|--------|----|
| Basics | title, type (ad-hoc/planned), domain | Text input, radio buttons, dropdown |
| People | requestor, responder | Searchable dropdown (HTMX), "add new" inline |
| Time | request_date, expected_start, expected_end | Date pickers, defaults to today |
| Data scope | time granularity, data period | Dropdowns built from existing values |
| Tags | tags | Multi-select with auto-complete (HTMX) |
| Template | template choice, git_init | Radio buttons, checkbox |
| Root | project root | Dropdown from config roots |

On submit:
1. Calls `ProjectRepository.create(...)` to create the DB record
2. Calls the core scaffold function to create the folder structure
3. Calls `PersonRepository` to link requestor/responder
4. Redirects to the project detail page

### 2. Project Detail (`/projects/<slug>`)

Read view showing all metadata for one project. Inline edit buttons (HTMX) for each section. Links to associated people, tags, files, deliverables.

### 3. Project Close-out (`/projects/<slug>/closeout`)

Computed checklist — no stored state. The service layer queries the DB and filesystem to find gaps:

- Files in the project folder not registered in DataFile table
- DataFiles with no sensitivity level set
- No requestor linked
- No deliverables recorded
- Questions without data period
- Status still "active"

Each item links to an inline edit form to fix it on the spot.

### 4. Person Management (`/persons`)

List of current persons (is_current=True). Search/filter. Quick "add new" form. Edit triggers SCD2 versioning via PersonRepository.

### 5. Search (`/search`)

Uses FTS5 via the existing search infrastructure. Results link to project detail pages.

## HTMX Interaction Patterns

### Searchable Person Dropdown

```html
<!-- In create.html -->
<input type="text" name="requestor_search"
       hx-get="/persons/search"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#requestor-results"
       placeholder="Search by name...">
<div id="requestor-results">
  <!-- HTMX loads _dropdown.html partial here -->
</div>
```

```html
<!-- _dropdown.html partial (returned by server) -->
{% for person in persons %}
<button type="button"
        hx-get="/persons/{{ person.id }}/select"
        hx-target="#requestor-field"
        class="dropdown-item">
  {{ person.first_name }} {{ person.last_name }}
  <span class="text-muted">{{ person.department }}</span>
</button>
{% endfor %}
{% if not persons %}
<button type="button"
        hx-get="/persons/new-inline"
        hx-target="#requestor-field"
        class="dropdown-item add-new">
  + Add new person
</button>
{% endif %}
```

### Inline Edit Pattern

```html
<!-- Read mode -->
<div id="status-field">
  <span>{{ project.status }}</span>
  <button hx-get="/projects/{{ project.slug }}/edit/status"
          hx-target="#status-field">Edit</button>
</div>

<!-- Edit mode (returned by server) -->
<div id="status-field">
  <select name="status"
          hx-put="/projects/{{ project.slug }}/status"
          hx-target="#status-field"
          hx-trigger="change">
    <option value="active" {{ 'selected' if project.status == 'active' }}>Active</option>
    <option value="paused">Paused</option>
    <option value="done">Done</option>
    <option value="archived">Archived</option>
  </select>
</div>
```

## Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Web framework | Flask | Known to user, mature, good for server-rendered HTML |
| Interactivity | HTMX 2.x | Smart dropdowns and inline editing without JS framework |
| CSS | Custom design system (adapted from Wagenwacht) | CSS variables, dark/light theme, DM Sans / DM Mono fonts |
| Templates | Jinja2 (via Flask) | Standard, no extra dependency |
| Database | Existing projects.db via repository layer | No new storage |
| Python packaging | pyproject.toml with setuptools | Standard modern Python |

## Dependencies

```toml
[project]
name = "datapm-studio"
requires-python = ">=3.10"
dependencies = [
    "data-project-manager",
    "flask>=3.0",
]
```

HTMX is loaded from CDN and Google Fonts (DM Sans, DM Mono) are loaded from CDN in the base template. Custom CSS lives in `static/css/style.css`. No npm, no build step.

## What Studio Does NOT Do

- **No separate database.** Reads/writes `projects.db` only.
- **No run tracking in the DB.** Script execution logs stay in text files.
- **No authentication.** Local-only, single-user.
- **No background tasks.** Everything is request/response.
- **No JavaScript build pipeline.** HTMX + CDN only.
- **No data entry for DataFile/Query/Deliverable via forms (v1).** These are populated by scripts via the Python API. Studio shows them read-only. Editing may come later.

## Future Extensions (Post v1)

| Feature | Notes |
|---------|-------|
| DataFile/Deliverable editing | Forms to register files and deliverables manually |
| Jira/DevOps sync | Webhook receiver or polling, maps to projects |
| GDPR dashboard | Filter projects/files by sensitivity, show retention dates |
| Bulk operations | Archive multiple projects, bulk-tag |
| Script registration | Register helper scripts, link to DataFiles they produce |
| Folder opener | Button that opens project folder in OS file manager |

# PLAN.md — datapm-studio

## Definition of Done

| Category | Requirement |
|----------|-------------|
| Implementation | Code follows `docs/CONVENTIONS.md` |
| Implementation | All imports from `data-project-manager` use the repository layer (no raw SQL) |
| Testing | All new code has tests; tests pass (`uv run pytest`) |
| Testing | Tests use a temporary DB, never the user's real `projects.db` |
| Linting | `uv run ruff format . && uv run ruff check .` passes |
| Type checking | `uv run pyright datapm_studio/` passes |
| Release | PLAN.md checkboxes updated |

---

## Milestone 0: Scaffold + Bootstrap (v0.0.1)

**Goal**: A running Flask app with one page that reads from the database. Proves the integration between Studio and core works end-to-end.

### Acceptance Criteria

- [ ] `uv run datapm-studio` starts a Flask dev server on localhost:5555
- [ ] Visiting `/` redirects to `/projects`
- [ ] `/projects` shows a list of projects from the database (title, slug, status, date)
- [ ] `base.html` loads HTMX and Pico CSS from CDN
- [ ] Navigation works: Projects, People, Search, + New
- [ ] `conftest.py` provides a Flask test client with a temporary SQLite DB
- [ ] At least one route test passes

### PR Breakdown

| # | Branch | Size | Description |
|---|--------|------|-------------|
| 1 | `chore/scaffold` | S | pyproject.toml, app factory, config reader, base template, empty blueprints |
| 2 | `feat/project-list` | M | Project list route, template, reads from ProjectRepository |
| 3 | `test/bootstrap` | S | conftest.py with temp DB fixture, test for project list route |

---

## Milestone 1: Project Creation Wizard (v0.1.0)

**Goal**: Create a new project through the web UI with the same result as `datapm new` — folder scaffolded, DB record created, requestor linked.

### Acceptance Criteria

- [ ] `/projects/new` shows a form with: title, type (ad-hoc/planned), domain, requestor (searchable dropdown), tags (multi-select), template, root, dates
- [ ] Requestor dropdown searches existing persons (HTMX, 300ms debounce)
- [ ] Requestor dropdown shows "add new person" when no match
- [ ] "Add new person" opens an inline form (HTMX partial) — no page reload
- [ ] Tags dropdown auto-completes from existing tags
- [ ] On submit: project record created in DB, folder scaffolded on disk, requestor linked as ProjectPerson
- [ ] Redirect to `/projects/<slug>` after creation
- [ ] Validation: empty title shows error, slug collision shows error
- [ ] Project detail page shows all metadata (read-only for now)

### PR Breakdown

| # | Branch | Size | Description |
|---|--------|------|-------------|
| 4 | `feat/person-dropdown` | M | Person search endpoint, `_dropdown.html` partial, HTMX wiring |
| 5 | `feat/person-inline-create` | S | Inline "add new person" form, creates via PersonRepository |
| 6 | `feat/tag-dropdown` | S | Tag search endpoint, `_dropdown.html` partial, multi-select |
| 7 | `feat/project-create-form` | L | Full creation form, validation, calls core scaffold, links requestor |
| 8 | `feat/project-detail` | M | Detail page showing all project metadata |
| 9 | `test/milestone-1` | M | Tests for all milestone 1 routes and form submissions |

---

## Milestone 2: Project Editing + Person Management (v0.2.0)

**Goal**: Edit existing project metadata via inline forms. Manage people as a first-class entity.

### Acceptance Criteria

- [ ] Project detail page has inline edit buttons for: status, domain, tags, external_url, dates
- [ ] Clicking "Edit" on a field swaps it to an edit form (HTMX); saving swaps back to read mode
- [ ] `/persons` shows a list of current persons with search/filter
- [ ] Editing a person triggers SCD2 versioning via PersonRepository
- [ ] Quick "add new person" form on the persons page

### PR Breakdown

| # | Branch | Size | Description |
|---|--------|------|-------------|
| 10 | `feat/inline-edit` | M | Generic inline edit pattern for project fields |
| 11 | `feat/person-management` | M | Person list, edit (SCD2), add new |
| 12 | `test/milestone-2` | M | Tests for inline editing and person management |

---

## Milestone 3: Close-out Checklist (v0.3.0)

**Goal**: When closing a project, show a checklist of metadata gaps and let the user fix them on the spot.

### Acceptance Criteria

- [ ] `/projects/<slug>/closeout` shows a computed checklist
- [ ] Checklist items: untracked files, missing sensitivity, no requestor, no deliverables, status still active, missing dates
- [ ] Each checklist item links to an inline edit form to fix it
- [ ] Filesystem scanning finds files in project folder not registered in DataFile table
- [ ] Checklist is computed on every request (no stored state)

### PR Breakdown

| # | Branch | Size | Description |
|---|--------|------|-------------|
| 13 | `feat/closeout-gaps` | M | Gap analysis service, closeout route |
| 14 | `feat/file-scanning` | M | Filesystem scanner for untracked files |
| 15 | `feat/closeout-ui` | M | Checklist template with inline fix links |
| 16 | `test/milestone-3` | M | Tests for gap analysis and scanning |

---

## Milestone 4: Search + Polish (v0.4.0)

**Goal**: Full-text search across projects. UI polish and usability improvements based on real usage.

### Acceptance Criteria

- [ ] `/search?q=...` returns results using FTS5
- [ ] Results show project title, slug, status, domain, requestor name
- [ ] Results link to project detail pages
- [ ] UI polish: loading indicators on HTMX requests, consistent error messages, flash messages

### PR Breakdown

| # | Branch | Size | Description |
|---|--------|------|-------------|
| 17 | `feat/search` | M | Search route using core FTS5, results template |
| 18 | `feat/polish` | M | Loading states, error handling, flash messages |
| 19 | `test/milestone-4` | S | Tests for search |

---

## Milestone 5: Audit + v1.0.0 (v1.0.0)

**Goal**: Full codebase audit, then tag v1.0.0.

### Acceptance Criteria

- [ ] Opus audit: imports, SQL safety (should be none), cross-platform, security, docs, test gaps
- [ ] All audit findings fixed
- [ ] README updated with final usage instructions
- [ ] Tagged v1.0.0

---

## Post v1.0.0 (ideas, unprioritized)

- DataFile/Deliverable editing via forms
- GDPR dashboard (filter by sensitivity, show retention dates)
- Jira/DevOps webhook integration
- Bulk operations (archive, tag)
- Script registration and linking to DataFiles
- Folder opener button (open project folder in OS file manager)
- `datapm web` command in the core CLI (thin wrapper, optional import)

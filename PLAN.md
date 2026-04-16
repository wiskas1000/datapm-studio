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

- [x] `uv run datapm-studio` starts a Flask dev server on localhost:5555
- [x] Visiting `/` redirects to `/projects`
- [x] `/projects` shows a list of projects from the database (title, slug, status, date)
- [x] `base.html` loads HTMX from CDN, custom CSS with dark/light theme toggle
- [x] Navigation works: Projects, People, Search, + New
- [x] `conftest.py` provides a Flask test client with a temporary SQLite DB
- [x] At least one route test passes

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

- [x] `/projects/new` shows a form with: title, type (ad-hoc/planned), domain, requestor (searchable dropdown), tags (multi-select), template, root, dates
- [x] Requestor dropdown searches existing persons (HTMX, 300ms debounce)
- [x] Requestor dropdown shows "add new person" when no match
- [x] "Add new person" opens an inline form (HTMX partial) — no page reload
- [x] Tags dropdown auto-completes from existing tags
- [x] On submit: project record created in DB, folder scaffolded on disk, requestor linked as ProjectPerson
- [x] Redirect to `/projects/<slug>` after creation
- [x] Validation: empty title shows error, slug collision shows error
- [x] Project detail page shows all metadata (read-only for now)

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

- [x] Project detail page has inline "Edit" buttons for scalar fields: status, domain, description, dates, estimated hours, external_url
- [x] Clicking "Edit" on a field swaps it to an inline edit form (HTMX `hx-get`); saving swaps back to read mode (HTMX `hx-post`)
- [x] Status field uses a `<select>` dropdown with valid values: active, paused, done, archived
- [x] Project detail page allows adding/removing persons (with role) and tags
- [x] Adding a person reuses the existing HTMX search dropdown from the create form
- [x] Adding a tag reuses the existing HTMX search dropdown from the create form
- [x] Removing a person or tag uses `ProjectPersonRepository.remove()` / `ProjectTagRepository.remove()`
- [x] `/persons` shows a searchable list of current persons with name, email, function, department
- [x] `/persons/<id>` shows person detail with edit form for all fields
- [x] Editing a person creates a new SCD2 version via `PersonRepository.create_new_version()`
- [x] Version history shown on person detail page via `ChangeLogRepository`
- [x] Quick "add new person" form on the persons list page

### PR Breakdown

| # | Branch | Size | Description |
|---|--------|------|-------------|
| 10 | `feat/project-inline-edit` | M | Inline edit partials for project scalar fields (status, domain, description, dates, hours, external_url) |
| 11 | `feat/project-edit-relations` | M | Add/remove persons and tags on existing project detail page |
| 12 | `feat/person-management` | M | Person list search, person detail page, SCD2 edit form, version history |
| 13 | `test/milestone-2` | M | Tests for inline editing, relation management, and person management |

---

## Milestone 3: Close-out Checklist (v0.3.0)

**Goal**: When closing a project, show a checklist of metadata gaps and let the user fix them on the spot. The close-out page is a pre-flight check before marking a project as "done" — it surfaces missing metadata so nothing falls through the cracks.

### Acceptance Criteria

- [x] `/projects/<slug>/closeout` shows a computed checklist (re-computed on every request, no stored state)
- [x] "Close-out" button on project detail page links to the checklist
- [x] Gap analysis checks:
  - [x] Status is still active (not yet closed)
  - [x] No requestor linked
  - [x] No description set
  - [x] Missing realized dates (realized_start, realized_end)
  - [x] No deliverables registered (`DeliverableRepository.list_for_project()`)
  - [x] Undelivered deliverables (`delivered_at IS NULL`)
  - [x] No data files registered (`DataFileRepository.list_for_project()`)
  - [x] Data files missing sensitivity (`sensitivity IS NULL`)
- [x] Filesystem scanner finds files on disk not registered in the DataFile table
- [x] Each gap shows: status icon (pass/warn/fail), description, and a link to fix it (inline edit or detail page)
- [x] "Mark as done" button at the bottom (only enabled when no critical gaps remain)
- [x] Marking as done sets `status = "done"` and `realized_end = today` (if not already set)

### PR Breakdown

| # | Branch | Size | Description |
|---|--------|------|-------------|
| 14 | `feat/closeout-service` | M | Gap analysis service: computes checklist items from DB + filesystem |
| 15 | `feat/file-scanning` | S | Filesystem scanner: walks project folder, compares to DataFile table |
| 16 | `feat/closeout-ui` | M | Closeout route, checklist template, "mark as done" action |
| 17 | `test/milestone-3` | M | Tests for gap analysis, file scanning, and closeout route |

---

## Milestone 3.1: Close-out Inline Fixes (v0.3.1)

**Goal**: Let users fix common metadata gaps directly on the close-out checklist page, without navigating back to the project detail page.

### Acceptance Criteria

- [x] Description gap shows an inline edit form
- [x] Realized start/end gaps show inline date pickers
- [ ] ~~Status gap shows an inline select dropdown~~ (skipped — "mark as done" button already handles this)
- [x] Requestor gap shows the person search dropdown
- [x] After fixing a gap inline, the checklist re-renders to reflect the change
- [x] Gaps without inline fix (deliverables, data files) keep the current "Fix" link to the project page

### PR Breakdown

| # | Branch | Size | Description |
|---|--------|------|-------------|
| 18 | `feat/closeout-inline-fields` | S | Inline edit for description, dates, status on closeout page |
| 19 | `feat/closeout-inline-requestor` | M | Person search dropdown for adding requestor on closeout page |

---

## Milestone 3.5: Data Files, Lookups & Request Questions (v0.4.0)

**Goal**: Surface and manage the metadata that makes search useful — data files (with entity types and aggregation levels), request questions, and deliverables. All managed from the project detail page, creation wizard, and close-out checklist.

### Acceptance Criteria

- [x] **Request Questions** — project detail page shows list of request questions; inline form to add new (question_text, data_period_from, data_period_to)
- [x] **Data Files — read + create** — project detail page shows registered data files (file_path, file_format, sensitivity, is_source, data period); form to register a new file
- [x] **Data Files — edit** — inline edit for data file scalar fields (sensitivity, file_format, data period, retention_date)
- [x] **Entity Types per file** — searchable dropdown on each data file to add/remove entity types (autocomplete from lookup table, create-on-type like tags)
- [x] **Aggregation Levels per file** — searchable dropdown on each data file to add/remove aggregation levels (autocomplete from lookup table, create-on-type like tags)
- [x] **Deliverables — read + create** — project detail page shows deliverables (type, file_path, version, delivered_at); form to register a new deliverable; "Mark delivered" button
- [x] **Creation wizard** — add entity types, aggregation levels, and request questions to the project creation form
- [x] **Close-out updates** — update gap checks to account for new metadata; inline fix where appropriate
- [x] All new code has tests; tests pass

### PR Breakdown

| # | Branch | Size | Description |
|---|--------|------|-------------|
| 20 | `feat/request-questions` | S | Request questions section on project detail: list + add form — shipped in #65 |
| 21 | `feat/data-files-read-create` | M | Data files section on project detail: list + register form — shipped in #66 |
| 22 | `feat/data-files-edit-lookups` | L | Inline edit for data file fields; entity type and aggregation level dropdowns per file (add/remove) — shipped in #67 |
| 23 | `feat/deliverables` | M | Deliverables section on project detail: list + register form + mark delivered — shipped in #68 |
| 24 | `feat/wizard-closeout-metadata` | M | Add entity types, agg levels, request questions to creation wizard; update closeout gap checks — shipped in #69 |
| 25 | _(folded in)_ | — | Tests shipped with each feature PR (#65–#69); no separate test PR needed |

---

## Milestone 4: Search + Polish (v0.5.0)

**Goal**: Full-text search across projects. UI polish and usability improvements based on real usage. Now powered by the rich metadata from M3.5.

### Acceptance Criteria

- [x] `/search?q=...` returns results using FTS5
- [x] Results show project title, slug, status, domain, requestor name, entity types, aggregation levels
- [x] Results link to project detail pages
- [x] UI polish: loading indicators on HTMX requests, consistent error messages, flash messages

### PR Breakdown

| # | Branch | Size | Description |
|---|--------|------|-------------|
| 26 | `feat/search` | M | Search route using core FTS5, results template |
| 27 | `feat/polish` | M | Loading states, error handling, flash messages |
| 28 | `test/milestone-4` | S | Tests for search |

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

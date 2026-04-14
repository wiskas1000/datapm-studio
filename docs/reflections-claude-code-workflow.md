# Reflections on Working with Claude Code — Lessons for a New Project

Based on the full development history of `data-project-manager` (v0.0.0 through v1.1.2,
25+ PRs, 350+ tests, 6 milestones over ~7 days).

---

## 1. What Worked: The CLAUDE.md Structure

The CLAUDE.md in `data-project-manager` evolved into a strong contract between you and
Claude Code. Here's what made it effective — replicate these in the new project:

### 1.1 "What This Tool Is" / "What This Tool Is NOT"

This was one of the most valuable sections. It prevented scope creep at the instruction
level. When Claude Code knows the tool is "not a manual data entry system", it won't
propose `datapm files add` CLI commands unprompted.

**Recommendation for new project**: Write both sections early, even if tentative. You can
always update them. The "NOT" section is especially useful — it's a list of things Claude
Code should not waste your time on.

### 1.2 Tech Stack as Constraints

Listing `uv` as preferred, `argparse` before Typer, `pathlib` everywhere — these act as
guardrails. Claude Code followed them consistently once written.

**Recommendation**: Be explicit about:
- Package manager (uv? pip?)
- Web framework choice (once decided)
- Database approach (reuse existing `data-project-manager` SQLite? new DB?)
- Python version minimum
- What is a runtime dependency vs dev-only

### 1.3 Design Principles as Numbered Rules

The 7 design principles at the bottom of CLAUDE.md were referenced constantly. "Zero-
dependency core", "Library first, CLI second", "SQLite is source of truth" — these
prevented architectural drift across 25 PRs.

**Recommendation**: Write 3-5 design principles for the new project before any code.
Examples that might apply:
- "Companion, not fork — always imports from `data-project-manager`, never duplicates"
- "Web UI is read-write — changes go to the same SQLite DB"
- "Helper scripts opt in, folder scan discovers"

### 1.4 Repository Structure as a Map

The ASCII tree of the folder structure gave Claude Code a mental model of where things
belong. It prevented files from being created in wrong locations.

**Recommendation**: Sketch the folder structure even before the first PR. Mark files that
don't exist yet with comments like `# future: web UI routes`.

### 1.5 Explicit Command Examples

The "Running the Tool" section with exact `uv run` commands meant Claude Code knew exactly
how to invoke things. This still required a reminder early on (see feedback below), but
once established it was followed consistently.

---

## 2. What Worked: The PLAN.md Approach

### 2.1 Milestones with Acceptance Criteria

Each milestone had checkboxes. This was extremely effective for two reasons:
- You could see progress at a glance
- Claude Code could verify whether work was actually done, not just attempted

### 2.2 PR Breakdown Per Milestone

Listing PRs in merge order with sizes (S/M/L) and one-line descriptions gave Claude Code
a clear scope for each unit of work. It prevented the "let me just also add..." tendency.

### 2.3 Definition of Done

The table (Implementation / Testing / Release) set clear expectations. Especially
important: "write tests before marking complete" — this prevented the pattern of shipping
code and only testing later.

**Recommendation for new project**: Write PLAN.md with:
- Milestones (even rough ones)
- Acceptance criteria per milestone
- A definition of done that matches your expectations
- PR breakdown if you already know the decomposition

---

## 3. Workflow Patterns That Worked

### 3.1 One Logical Change Per Commit

Conventional commits (`type(scope): description`) kept the history readable. When issues
arose (#14-#17 post-v0.1.0), it was easy to trace what changed and why.

### 3.2 Branch-Per-Feature with Small PRs

The `type/short-description` convention kept PRs focused. The largest PRs (folder
selection redesign, schema migration) were still reviewable because they had clear scope
boundaries defined in PLAN.md.

### 3.3 "Test First, Then Ship" Cadence

Every milestone had a testing strategy section. Coverage went from 64 tests (v0.1.0) to
351 (v1.0.0, 94% coverage). This wasn't accidental — it was in the instructions.

### 3.4 GitHub as a Collaborative Surface

One of the most effective parts of the workflow was using GitHub as a shared workspace,
not just a code host. Claude Code handled the full lifecycle:

- **Commit messages**: Conventional Commits written by Claude, reviewed by you before
  confirming. This kept the history clean without you needing to draft messages.
- **PR creation**: Claude drafted PR titles and bodies (`## Summary` + `## Test plan`)
  using `gh pr create`. The body explained "why" and "what changed" — not just a diff
  summary. You reviewed before merging.
- **PR reviews**: Asking Claude to review a PR (or its own code) produced actionable
  feedback — the v1.1.1 audit that found issues #56-#60 came from this pattern.
- **GitHub Project board**: Issues and PRs were tracked in GitHub Project #4. Claude
  created issues for audit findings, linked them to the project, and closed them
  via PR merges. This kept PLAN.md and the board in sync.
- **PLAN.md as the source of truth for scope**: The PR table in PLAN.md defined what
  each PR should contain. Claude followed this when creating branches and PRs. The
  GitHub project board tracked execution status; PLAN.md tracked the plan itself.

**Recommendation for new project**: Continue this pattern. Include in CLAUDE.md:
- Branch naming and commit conventions (already standard)
- PR body template (Summary + Test plan)
- Reference to the GitHub project board (if using one)
- Instruction: "Update PLAN.md checkboxes when a milestone item is completed"

### 3.5 Audit Before Rest

The v1.1.1 audit — a full codebase review that produced 5 actionable issues — was a good
pattern. It gave you confidence to step away from the project knowing exactly what was
left.

**Recommendation**: Plan an audit milestone for the new project too. After the first usable
version, do a sweep before adding more features.

---

## 4. What Needed Correction (Feedback Learned the Hard Way)

### 4.1 Always Use `uv run`

Claude Code defaulted to bare `python` or `pytest` multiple times early on. You had to
remind it to use `uv run`. Once this was saved as a memory/feedback, it stuck.

**Recommendation**: Put tool invocation commands in CLAUDE.md from day one. Don't assume
Claude Code will infer the right runner.

### 4.2 Don't Make Improvements During Testing Phase

After v1.1.2, you explicitly said: "currently we will test everything on v1.1.2 without
making any improvements yet. First testing." This was necessary because the default
behavior is to keep improving.

**Recommendation**: If you have a "freeze" or "stabilize" phase, state it explicitly in
CLAUDE.md or the conversation. Something like:

```
## Current Phase: Design (no code yet)
We are in the design interview phase. Do not write code or create files
unless explicitly asked. Focus on helping crystallize requirements.
```

### 4.3 Scope Boundaries Need Enforcement

The "What This Tool Is NOT" section helped, but in conversations Claude Code still
sometimes proposed features beyond the current milestone. The PLAN.md with per-milestone
scope was the real enforcement mechanism.

**Recommendation**: For the new project, decide early what version 0.1.0 looks like and
write it down. Everything else is "post v0.1.0".

---

## 5. How the Memory System Helped

### 5.1 Feedback Memories Persisted Across Sessions

The `uv run` preference, the testing phase status, and the folder redesign decisions all
survived conversation resets. This prevented re-litigating decisions.

### 5.2 Project Memories Tracked State

The v1.1.1 audit memory meant that when you came back days later, Claude Code knew exactly
what was done and what was pending.

**Recommendation for new project**: Let memories build naturally. The most valuable types:
- **Feedback**: "always do X / never do Y" — these prevent repeated corrections
- **Project**: key decisions and their rationale — prevents re-debating
- **User**: your role and preferences — helps calibrate the level of explanation

---

## 6. Opus for Planning, Sonnet for Building

> **Status: Untested hypothesis.** The entire `data-project-manager` project was built
> with Opus alone. This workflow is the intended approach for the next project — to be
> validated and updated after the first milestone. Treat it as a starting plan, not
> proven doctrine.

### 6.1 The Core Insight

The `data-project-manager` project was built entirely with Opus. This worked, but
the cost/speed tradeoff can be improved. The key observation:

**Sonnet's bottleneck is ambiguity, not capability.** When Sonnet has a clear spec —
method signature, inputs/outputs, which modules to use, algorithmic steps — it produces
clean, coherent code quickly. Where it struggles is when it has to make architectural
decisions, weigh tradeoffs, or figure out scope on its own.

Opus excels at exactly those things: decomposition, architecture, and writing detailed
specifications. This suggests a deliberate two-model workflow.

### 6.2 The Workflow

```
                    Opus                              Sonnet
                    ────                              ──────
Phase 1: Plan      Write PLAN.md milestones
                    Design ARCHITECTURE.md
                    Specify method/class contracts
                    Define data flow between modules
                    Choose libraries + patterns

Phase 2: Spec      For each PR in the milestone:
                    - List files to create/modify
                    - Write function signatures
                    - Describe parameters + return types
                    - Outline the algorithm in steps
                    - Name the modules/imports to use
                    - Write example usage if non-obvious

Phase 3: Build                                       Implement per spec
                                                     Write tests
                                                     Run linter + formatter
                                                     Create commits
                                                     Draft PR body

Phase 4: Review    Review the PR
                    Check for architectural drift
                    Audit edge cases
                    Update PLAN.md
                    Plan next PR

Phase 5: Repeat    → back to Phase 2 for next PR     → Phase 3
```

### 6.3 What Makes a Spec "Good Enough for Sonnet"

A spec that Sonnet can execute cleanly should include:

1. **Function/method signature**: name, parameters with types, return type
2. **Purpose**: one sentence on what it does and why it exists
3. **Algorithm sketch**: numbered steps, not pseudocode — natural language is fine
4. **Dependencies**: which imports, which repository classes, which config values
5. **Edge cases**: what should happen on empty input, missing data, duplicates
6. **Example call**: how the function is invoked from the caller's perspective

Example of a spec Opus might write:

```
### web/routes/project.py — create_project()

Signature: async def create_project(request: Request) -> RedirectResponse

Purpose: Handle POST /projects/new — validate form data, call
ProjectRepository.create(), redirect to the new project's detail page.

Algorithm:
1. Parse form fields: title, domain, is_adhoc, root_id
2. Call core.project.create_project() with those fields + conn from app state
3. On success: redirect to /projects/{slug}
4. On ValueError (slug collision): re-render form with error message

Dependencies: data_project_manager.core.project.create_project,
             data_project_manager.db.connection.get_connection,
             starlette.requests.Request, starlette.responses.RedirectResponse

Edge cases: empty title → form validation before hitting create_project()
```

With a spec like this, Sonnet knows exactly what to build, which modules to import,
and how to handle failure — no architectural guesswork required.

### 6.4 What Opus Should NOT Delegate

Some tasks benefit from Opus staying in the loop:

- **Schema design**: table structure, migrations, relationship modeling
- **Design decisions with tradeoffs**: "should this be a query param or a form field?"
- **Cross-cutting changes**: anything that touches 3+ files for architectural reasons
- **Audit and review**: the final pass before merging
- **Debugging non-obvious failures**: when the error message doesn't point to the cause

### 6.5 Practical Setup in Claude Code

You can switch models mid-conversation using `/model` or start a session with a specific
model. A practical pattern:

1. Start a session with Opus. Do planning, write specs into PLAN.md or a spec file.
2. Switch to Sonnet (or start a new session with Sonnet). Point it at the spec:
   "Implement the spec in docs/specs/web-routes.md, PR 1: project CRUD routes"
3. Sonnet builds, tests, commits.
4. Switch back to Opus for review: "Review the PR on branch feat/project-routes"

Alternatively, use Opus in Claude.ai for the planning/interview phase, then use
Sonnet in Claude Code for all implementation. The handoff artifact is the spec file.

**Note on prompting**: The Opus planning phase — especially design interviews in
Claude.ai — is itself a prompting task. If you have a prompting guide with principles
like "be specific," "use examples," and "define output structure," apply those when
writing specs. A spec is a prompt for Sonnet; the same qualities that make a good
prompt make a good spec.

### 6.6 Implications for CLAUDE.md

Add to the new project's CLAUDE.md:

```markdown
## Model Workflow

This project uses a two-model workflow:
- **Opus**: planning, architecture, specs, reviews, audits
- **Sonnet**: implementation per spec, tests, commits, PRs

Specs live in `docs/specs/` — one file per milestone or PR group.
Sonnet should follow specs exactly. If a spec is ambiguous or seems
wrong, flag it rather than guessing.
```

---

## 7. Linting, Testing, and Hooks — Optimizations

### 7.1 Ruff: Format Before Check

**The problem**: In `data-project-manager`, the pre-commit config runs `ruff --fix` (auto-
fixes lint issues) then `ruff-format --check` (fails on formatting, but doesn't fix).
During Claude Code sessions, the typical sequence was:

1. Write code
2. `ruff check` → passes (or auto-fixed)
3. Commit attempt → pre-commit runs `ruff-format --check` → fails
4. `ruff format` → fixes formatting
5. Re-commit

Steps 3-4 waste a round trip every time. With Sonnet, that's tokens and an action burned
on something fully automatable.

**The fix for the new project**: Always run format *before* check:

```bash
# In CLAUDE.md "Running the Tool" section:
uv run ruff format . && uv run ruff check .
```

Or better, configure pre-commit to auto-format (no `--check` flag):

```yaml
# .pre-commit-config.yaml
- id: ruff-format
  # no --check flag → auto-formats on commit
- id: ruff
  args: [--fix]
```

This way code is always formatted before it's checked. Claude Code never wastes a cycle
on formatting feedback.

### 7.2 Git Hooks: What's Real vs What's Claimed

**The problem**: CLAUDE.md for `data-project-manager` states:
- pre-commit: `ruff check` + `ruff format --check` — **actually configured** ✓
- pre-push: `uv run pytest` — **NOT actually configured** ✗

The pre-push hook file exists (installed by `pre-commit install --hook-type pre-push`) but
`.pre-commit-config.yaml` has no `stages: [pre-push]` entries. The hook runs but does
nothing.

**The fix for the new project**: Either properly configure it:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: uv run pytest
      language: system
      always_run: true
      pass_filenames: false
      stages: [pre-push]
```

Or don't claim it in CLAUDE.md. Both are fine — the key is that the docs match reality.

**Should we use pre-push pytest?** Yes, it's worth keeping. Claude Code runs pytest before
committing anyway (part of the definition of done), so it rarely blocks a push. But it
catches the case where tests pass locally on one file but fail in combination — cheap
insurance. Just make sure it's actually wired up.

### 7.3 Test-First Development: Opus Writes Tests, Sonnet Implements

**The observation**: In `data-project-manager`, the pattern was always code-first:
1. Write implementation
2. Write tests
3. Fix failures
4. Commit

This worked, but it means tests are shaped by the implementation rather than the
requirements. And with the Opus/Sonnet split, there's a much stronger pattern available.

**The proposed workflow — Opus as test author, Sonnet as implementer:**

```
Opus (planning session):
1. Write the spec (function signatures, algorithm sketch, edge cases)
2. Write the test file — tests that will FAIL because the code doesn't exist yet
3. Tests define the contract: inputs, outputs, error cases, edge behavior
4. Commit the spec + tests to the branch

Sonnet (implementation session):
1. Read the spec and tests
2. Implement until all tests pass
3. Run ruff format + check
4. Commit
```

**Why this is powerful:**

- **Tests become the spec**: Sonnet doesn't need to interpret prose — it can run the tests
  and get concrete pass/fail feedback. This is the tightest possible feedback loop.
- **Opus controls quality**: The test file defines what "correct" means. Sonnet can't
  silently skip an edge case because the test is already written for it.
- **Catches misunderstandings early**: If Sonnet's implementation passes all tests but
  feels wrong, the problem is in the test design (Opus's responsibility), not the
  implementation.
- **Natural TDD**: This is textbook Test-Driven Development, but with the "design the
  tests" and "write the code" roles assigned to different models optimized for each task.

**What Opus should write in the test file:**

```python
# tests/test_project_routes.py
# Written by Opus — defines the contract for web/routes/project.py

import pytest

class TestCreateProject:
    """POST /projects/new"""

    def test_creates_project_and_redirects(self, client, db_conn):
        response = client.post("/projects/new", data={
            "title": "Churn analysis",
            "domain": "marketing",
        })
        assert response.status_code == 303
        assert "/projects/2026-04-14-churn-analysis" in response.headers["location"]

    def test_empty_title_shows_error(self, client):
        response = client.post("/projects/new", data={"title": ""})
        assert response.status_code == 200  # re-renders form
        assert "Title is required" in response.text

    def test_slug_collision_shows_error(self, client, existing_project):
        response = client.post("/projects/new", data={
            "title": existing_project.title,  # same title → same slug
        })
        assert response.status_code == 200
        assert "already exists" in response.text
```

Sonnet sees this and knows exactly what to build: a route that accepts POST, validates
the title, calls create_project, handles slug collisions, and redirects on success.
No ambiguity.

**Practical note — fixtures and bootstrapping**: The tests need working fixtures
(`client`, `db_conn`, `existing_project`). Opus should write `conftest.py` fixtures as
part of the test authoring phase, or at minimum spec them out so Sonnet can create them
alongside the implementation.

**Practical note — scaffold first for milestone 1**: Test-first assumes enough
infrastructure exists for tests to run against. For the very first milestone of the new
project, you may need to bootstrap before tests can work: install the web framework, wire
up a test client, configure the database connection for tests, create the app factory.
Expect the first PR or two to follow a "scaffold first, then test-first" approach. Once
the app skeleton and `conftest.py` fixtures exist, subsequent PRs can go full test-first.

### 7.4 Implications for CLAUDE.md

```markdown
## Linting Workflow

Always format before checking:
    uv run ruff format . && uv run ruff check .

Pre-commit auto-formats and auto-fixes. No --check flags.

## Testing Workflow

Test-first: tests are written during the planning/spec phase (by Opus).
Implementation is done by Sonnet against those tests.
Run tests with: uv run pytest
Pre-push hook runs the full test suite.
```

---

## 8. Editor Integration: Neovim + Pyright + Claude Code

### 8.1 The Opportunity

Pyright is already configured in Neovim and provides real-time type checking. Claude Code
does not run Pyright on its own — it only sees type errors if you surface them or if
they're part of a CI/pre-commit check. Connecting the two creates a stronger feedback
loop, especially for Sonnet which benefits from concrete error messages.

### 8.2 Ways to Connect Them

**Option A: Claude Code inside nvim terminal**
Run `:terminal` in a split, launch `claude` there. You edit in one pane, Claude Code runs
in the other. Pyright diagnostics appear in your buffer — you can read them to Claude Code
or copy-paste the error.

Pros: Simple, no plugins needed. Cons: Manual copy-paste of diagnostics.

**Option B: Claude Code Neovim extension**
Claude Code has a native Neovim integration that runs as a side panel. It can read buffer
context and LSP diagnostics from Pyright.

Pros: Tightest integration, Claude Code sees what Pyright sees. Cons: Requires setup and
the extension to be maintained.

**Option C: Pyright in pre-commit / CI**
Add `pyright` as a pre-commit hook or as a step in the definition of done:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pyright
      name: pyright
      entry: uv run pyright
      language: system
      types: [python]
      pass_filenames: false
```

Or in CLAUDE.md:

```
## Type Checking
uv run pyright src/
Run after implementation, before committing. Fix all errors.
```

Pros: Claude Code (Opus or Sonnet) gets type feedback in the same way it gets ruff
feedback — as a failed check with a concrete error message. Works regardless of editor
setup. Cons: Slower than real-time LSP feedback.

**Option D: Manual feedback loop**
Run Claude Code in a separate terminal. When Pyright flags something in nvim, paste the
diagnostic:

> "Pyright says `Argument of type 'str | None' is not assignable to parameter of type
> 'str'` at `routes/project.py:42`"

This is enough for Claude Code to fix the issue precisely.

### 8.3 Recommendation

Use **Option C (Pyright in pre-commit)** as the baseline — it works for every Claude Code
session regardless of how you launch it. Layer **Option A or B** on top for interactive
sessions where you want real-time feedback.

For the Opus/Sonnet workflow specifically: Opus writes typed specs and tests. Sonnet
implements. Pyright catches type mismatches between the spec and implementation
automatically. This is a three-layer guardrail:

```
Opus spec (types + signatures) → Sonnet implementation → Pyright verification
                                                       → Tests verification
```

### 8.4 For CLAUDE.md

```markdown
## Type Checking

Pyright is configured for this project. Run before committing:
    uv run pyright src/

The editor (Neovim) runs Pyright via LSP. If the user pastes a Pyright
diagnostic, fix the type error precisely — do not suppress with `# type: ignore`
unless the error is a false positive and you explain why.
```

---

## 9. Coding Conventions

When Sonnet implements from a spec, Opus controls the class names, method names, and
signatures. But Sonnet makes hundreds of smaller naming decisions: local variables, loop
iterators, intermediate results, helper functions, SQL aliases, config keys, template
variables. Without conventions, each Sonnet session may invent its own style.

Put these in CLAUDE.md (or a separate `CONVENTIONS.md` referenced from CLAUDE.md) so
every instance — Opus or Sonnet — writes consistent code.

### 9.1 Conventions Established in `data-project-manager`

These patterns emerged across 25+ PRs. Codify them for the new project:

**Python naming (PEP 8 baseline, project-specific additions):**

| What | Convention | Example |
|------|-----------|---------|
| Classes | PascalCase, noun | `ProjectRepository`, `PersonWithRole` |
| Functions/methods | snake_case, verb phrase | `create_project()`, `get_db_path()` |
| Private helpers | `_` prefix | `_build_project_export()`, `_today()` |
| Constants | UPPER_SNAKE | `SCHEMA_VERSION`, `BASE_FOLDERS`, `SRC_TOGGLES` |
| Dataclass models | PascalCase, frozen, with `from_row()` classmethod | `Project`, `Person` |
| Repository classes | `{Entity}Repository` | `DataFileRepository` |
| DB connections | `conn` (never `connection`, `db`, or `cursor`) | `self._conn = conn` |
| Instance state | `self._conn`, `self._changelog` (private) | — |
| UUIDs | `{entity}_id` as parameter, `str(uuid.uuid4())` | `root_id`, `person_id` |
| Timestamps | `created_at = now_iso()` | never `ts`, `timestamp`, `time` |
| SQL result rows | `row` (single), `rows` (list) | `row = conn.execute(...).fetchone()` |
| Boolean params | `is_` or `do_` prefix | `is_default`, `do_git_init` |
| Boolean DB fields | `is_` prefix, stored as `INTEGER` | `is_adhoc`, `has_git_repo` |
| Optional return | `Entity | None` | `def get(...) -> Project | None` |
| Keyword-only args | After `*` in signatures | `def create(self, *, title: str, ...)` |
| Module docstrings | First line states purpose, second notes stdlib-only if applicable | — |

**SQL conventions:**

| What | Convention | Example |
|------|-----------|---------|
| Table names | snake_case, singular | `project`, `data_file`, `change_log` |
| Junction tables | `{table1}_{table2}` | `project_person`, `data_file_entity_type` |
| Column names | snake_case, match Python model field names | `file_path`, `valid_from` |
| Parameterized queries | Always `?` placeholders, never f-strings | `conn.execute("... WHERE id = ?", (id,))` |
| Multi-line SQL | Triple-quoted, indented inside `conn.execute()` | see repository files |

**File and module conventions:**

| What | Convention | Example |
|------|-----------|---------|
| One model per file | `db/models/{entity}.py` | `models/project.py`, `models/person.py` |
| One repo per entity group | `db/repositories/{entity}.py` | `repositories/data_file.py` |
| Core modules | One per domain concept | `core/project.py`, `core/search.py` |
| Shared helpers | `_helpers.py` with `_` prefix (internal) | `repositories/_helpers.py` |
| Test files | `test_{module}.py`, mirror src structure | `tests/test_project_repo.py` |
| Imports | `from __future__ import annotations` at top | all files |
| TYPE_CHECKING | Guard heavy/circular imports | `if TYPE_CHECKING: from ... import ...` |

**Function structure patterns:**

```python
# Repository method pattern:
def create(self, *, field: str, optional: str | None = None) -> Entity:
    """One-line summary.

    Args:
        field: Description.
        optional: Description.

    Returns:
        The newly created :class:`Entity`.
    """
    entity_id = str(uuid.uuid4())
    created_at = now_iso()
    with self._conn:
        self._conn.execute("INSERT INTO ...", (entity_id, field, ...))
    result = self.get(entity_id)
    assert result is not None
    return result
```

### 9.2 Conventions to Decide for the New Project (checklist)

The new project adds a web layer. These are **not yet decided** — tick them off during the
design phase so they don't surface mid-implementation:

- [ ] Route function names: `get_project()` vs `project_detail()` vs `show_project()`
- [ ] Template file names: `project_detail.html` vs `project/detail.html`
- [ ] Form variable names: `form_data`, `payload`, or just unpack into params?
- [ ] Request/Response objects: framework-specific — name once, use everywhere
- [ ] JS variable naming: camelCase (JS standard) or snake_case (Python consistency)?
- [ ] CSS class naming: BEM? Tailwind utility? Plain descriptive?
- [ ] API endpoint naming: `/projects/{slug}` vs `/project/{slug}` (plural vs singular)

### 9.3 How to Reference in CLAUDE.md

Keep conventions in a separate file so CLAUDE.md stays focused on architecture and
workflow. Add one line to CLAUDE.md:

```markdown
## Coding Conventions

See `docs/CONVENTIONS.md` for naming, SQL style, file structure, and function patterns.
All code — whether written by Opus or Sonnet — must follow these conventions.
```

This keeps the conventions findable, updatable, and out of the way of the high-level
project instructions.

---

## 10. Error Recovery: How Bugs Were Caught

A missing reflection from the earlier draft. The project had two rounds of bug-catching
that are worth distilling into a repeatable pattern.

### 10.1 Post-v0.1.0 Fixes (#14-#17)

These were found during the v0.2.0 planning phase — Opus reviewed the v0.1.0 code before
designing the next milestone. The pattern:

1. **Opus reviews the previous milestone's code** before planning the next one
2. Issues found: slug collision not handled (#14), DB connections not closed (#15),
   unvalidated column names in update (#16), Sphinx docstring warning (#17)
3. Fix PR merged before starting v0.2.0 work

**What caught them**: Code review by Opus with a focus on "what could go wrong" —
not test failures, not user reports. The bugs were all logical gaps that tests didn't
cover because the tests were written alongside the code (shaped by the implementation,
not the requirements).

### 10.2 Post-v1.1.1 Audit (#56-#60)

A deliberate full-codebase audit before resting the project. The pattern:

1. **Ask Opus to audit the entire codebase** — import boundaries, SQL injection, cross-
   platform issues, dead code, doc completeness
2. Issues found: missing CLI docs (#56-#57), dead code (#58), missing tests (#59-#60)
3. Issues filed in GitHub Project #4, fixed in a single PR

**What caught them**: A structured audit with specific categories to check. The audit
prompt was essentially: "Check imports, SQL safety, cross-platform, security, docs
completeness, test gaps."

### 10.3 Pattern to Replicate

| When | What to do | Who |
|------|-----------|-----|
| After each milestone | Review previous milestone's code for logical gaps | Opus |
| Before stabilization | Full structured audit (imports, security, docs, tests) | Opus |
| During implementation | Run test suite + ruff + pyright on every commit | Sonnet |
| After PR merge | Spot-check: does the feature work end-to-end? | You (manual) |

The key insight: **tests catch regressions, but code review catches design gaps.** Both
are needed. The test-first workflow (Section 7.3) addresses the test side. The audit
pattern addresses the review side. Schedule both.

---

## 11. Instructions for Writing CLAUDE.md for the New Project

Based on everything above, your new CLAUDE.md should have these sections (in order):

```markdown
# CLAUDE.md — [Project Name]

## Project Overview
One paragraph: what this tool does, who it's for, how it relates to
data-project-manager.

## What This Tool Is
Bullet list of capabilities.

## What This Tool Is NOT (for now)
Bullet list of out-of-scope items. Update as scope becomes clearer.

## Relationship to data-project-manager
- Where the core repo lives (path)
- What this project imports from it
- What belongs here vs there (boundary rule)

## Tech Stack
Every tool, framework, and version constraint. Be explicit about:
- Web framework (once chosen)
- Frontend approach (HTMX? React? plain Jinja?)
- Package manager (uv)
- Python version
- Testing framework
- Linting

## Running the Tool
Exact commands. Copy-paste ready. Use `uv run` throughout.

## Repository Structure
ASCII tree with comments for planned-but-not-yet-created files.

## Design Principles
3-5 numbered rules. These are the non-negotiable architectural decisions.

## Branch / Commit / PR Conventions
Copy from data-project-manager if they still apply.
Include PR body template (Summary + Test plan).
Reference the GitHub project board if using one.
"Update PLAN.md checkboxes when a milestone item is completed."

## Model Workflow
- Opus: planning, architecture, specs, reviews, audits
- Sonnet: implementation per spec, tests, commits, PRs
- Specs live in docs/specs/ — one file per milestone or PR group
- Sonnet should follow specs exactly; flag ambiguity, don't guess

## Coding Conventions
Reference docs/CONVENTIONS.md — naming, SQL style, file structure, patterns.
All code — Opus or Sonnet — must follow these conventions.

## Testing
What framework, what coverage expectations, how to run.

## Current Phase
What phase the project is in RIGHT NOW. Update this as you progress.
Example: "Design — no code yet" or "v0.1.0 — building core web UI"
```

### Additional files to create early:

- **PLAN.md**: Milestones, acceptance criteria, PR breakdown
- **docs/ARCHITECTURE.md**: Data model, system diagram, component responsibilities
- **docs/DESIGN.md**: Open questions, decisions made, decisions pending

---

## 12. Suggestions for the Design Interview

> **One-time checklist.** This section is prep for the initial design interview. Once
> completed, move it to `docs/DESIGN_INTERVIEW_PREP.md` or delete it — it will be dead
> weight in this document after that.

When you go into the Claude.ai interview, you already have good material. Here are topics
to make sure you cover:

### Decisions to make:
- Module name (this affects imports, CLI entry point, PyPI name)
- Web framework (FastAPI + Jinja + HTMX is a strong default for this kind of tool)
- Whether the web UI runs as `datapm-web serve` or as a separate command entirely
- How helper scripts discover/register themselves (hybrid was the leading candidate)
- What a "run record" schema looks like
- Whether requestor management deserves its own CLI commands or is web-UI only
- Whether project creation in the web UI replaces or supplements `datapm new`

### Things to bring to the interview:
- The data model from docs/ARCHITECTURE.md lines 47-279 (entity table + ER diagram + all field definitions)
- The interview prompt from the earlier conversation (with existing capabilities context)
- This document (so you can reference workflow preferences)

### Questions to ask yourself during the interview:
- "What do I do every week that this tool should make faster?"
- "What metadata do I wish I had captured on old projects?"
- "Who else might use this, and what would they need?"
- "What's the simplest version I would actually use?"

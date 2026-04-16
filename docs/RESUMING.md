# Resuming Development — datapm-studio

Written at the start of a long testing phase (v0.5.1, 2026-04-16). Read this before picking
development back up — a lot of state lives in conventions that are easy to forget.

## Where things stand

- **Version**: 0.5.1. Tagged on `main`. GitHub Release published.
- **Tests**: 241 passing. `uv run ruff format . && uv run ruff check .` and `uv run pyright
  datapm_studio/` are clean.
- **Milestone state** (see `PLAN.md`): M0–M4 shipped. M5 (audit + v1.0.0) is effectively
  done on the documentation/security side via PR #78; the remaining item is the actual
  v1.0.0 tag once real-world testing has validated the release.
- **Known follow-up**: `wiskas1000/data-project-manager#62` will ship a metadata-FTS
  extension for `/search`. When it lands, extend Studio's search route to call it.

## Non-negotiable contracts

These are cheap to forget and expensive to get wrong.

1. **Same database as core, always.** Studio reads/writes `~/.datapm/projects.db` via
   `data_project_manager.db.repositories.*`. No raw SQL. No separate storage. If a
   repository method is missing, add it in core, not here.
2. **Don't edit the core repo from Studio sessions.** If core needs a change, open an
   issue in `wiskas1000/data-project-manager`. (This is in memory already.)
3. **`uv run` only.** Never bare `python3`/`pip`. Applies to tests, lint, type check, and
   the CLI entrypoint itself.
4. **Local-only assumptions are load-bearing.** `app.run(debug=False)`, the hardcoded
   `secret_key`, no auth, and no CSRF protection are all fine *because* Studio is a local
   single-user tool. Anyone considering deploying this behind a network needs to revisit
   all four.

## Release workflow (already bitten us twice)

`main` is branch-protected. Direct pushes are rejected. Every release follows the same
shape:

1. Branch: `chore/release-X.Y.Z`.
2. Bump version in **three** places: `pyproject.toml`, `datapm_studio/__init__.py`,
   `uv.lock` (the last via `uv lock`).
3. Update `PLAN.md` milestone checkboxes.
4. PR → squash-merge → delete branch.
5. Annotated tag `vX.Y.Z` on `main`, push the tag.
6. `gh release create vX.Y.Z --notes ...`.

Do not try `git push origin main` — it will fail and waste time.

## Toolchain gates (run before every PR)

```bash
uv run ruff format . && uv run ruff check .
uv run pyright datapm_studio/
uv run pytest -q
```

All three must be clean. This has been the habit across all releases and it keeps the
main branch green.

## Things that are intentional (not bugs)

- `app.secret_key = "datapm-studio-local-only"` — see inline comment in `app.py`.
- `app.run(debug=False)` — the Werkzeug debugger is a remote-exec hole even on
  localhost. Flip to `True` locally while debugging; never commit it.
- No `datapm web` subcommand. The entrypoint is `uv run datapm-studio`. Earlier README
  drafts described flags (`--port`, `--no-browser`) that never existed — cleaned up in
  PR #78.
- No PyPI release. Local clone + `uv sync` is the documented install path.
- `data-project-manager` is referenced as a path source in `pyproject.toml` pointing to
  `../data-analysis-project-manager`. Adjust if the sibling repo path changes.

## When you pick up work again

1. `git pull` on `main` — verify clean, 241+ tests passing.
2. Read the latest GitHub release notes (link the version → understand what shipped).
3. Check `PLAN.md` — is there still an M5 item open, or are we moving to the Post-v1.0
   list?
4. If there are testing-phase bug reports, prefer one PR per bug with a failing test
   first, then the fix. Don't batch them.
5. Before opening any new feature PR, check whether `data-project-manager#62` (or
   whatever's next) has landed — Studio should call the core's new surface, not
   reimplement.

## Pointers

- Architecture: `ARCHITECTURE.md`
- Coding conventions: `docs/CONVENTIONS.md`
- Milestone map: `PLAN.md`
- Cross-project reflections: `docs/reflections-claude-code-workflow.md`
- This collaboration's lessons: `docs/LESSONS.md`

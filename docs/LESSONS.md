# Lessons Learned — datapm-studio Collaboration

Notes from shipping v0.0.1 through v0.5.1 with Claude Code. Complementary to
`reflections-claude-code-workflow.md` (which covers the core repo); this one is
specific to how Studio was built.

## What went well — keep doing

### Tight PR cadence with "stop before merge"
Every PR landed with a human checkpoint: Claude stopped after opening the PR, the user
reviewed and said "merge". That one beat of human input per PR caught a lot of drift
without slowing things down. Keep it.

### Bundling related work into one audit PR
PR #78 rolled six discrete audit findings into a single commit instead of six tiny PRs.
When fixes are all of the same shape (docs, safety, minor hygiene), one PR with a
numbered body is cleaner than a stack. Reserve this for low-risk batches — features
still get their own PR.

### Running the full gate before each commit
`ruff format + ruff check + pyright + pytest` ran before *every* commit, not just
release ones. Main stayed green across all 241 tests with no revert commits. Do not
let this habit slip during the testing phase.

### Using existing CSS variables
Adding Catppuccin was ~60 lines because the stylesheet was already threaded through
`--bg`, `--text`, `--accent`, etc. The discipline of "no hardcoded colors in
components" paid off three milestones later. Keep this constraint for any future theme
work.

### User challenging unnecessary complexity
The "why was `import os` needed?" moment killed a pointless env-var gate. That kind of
interjection is worth more than any review comment — the first-draft answer was
over-engineered and needed the nudge.

### Session rules in memory
`use uv`, `don't edit core from Studio`, `tag at milestones but don't auto-release` —
these persisted across compactions and prevented recurring mistakes. The memory system
earned its keep.

## What should change — do better

### Docs drifted for multiple releases
README described a `datapm web` CLI with `--port` and `--no-browser` flags that *never
existed*. CLAUDE.md said Python 3.10 while pyproject said 3.11. Placeholder
`your-username/...` URLs shipped through v0.5.0. All caught in the M5 audit — but all
should have been caught at v0.1.0 the first time the text was written.

**Fix forward**: whenever a README documents a command or flag, grep for that exact
string in the code *in the same session*. If it's not there, either implement it or
don't document it. And audit the docs at every minor version bump, not only at v1.0.0.

### `debug=True` survived four releases
The Werkzeug debugger was on by default from M0 until the audit. It's a remote-exec
surface. For a local-only tool the blast radius is small, but the principle stands:
security-relevant defaults deserve a deliberate decision, documented, at the moment
they're introduced — not discovered later.

**Fix forward**: when scaffolding any Flask/web project, treat `debug`, `secret_key`,
CSRF, and auth as mandatory early-decision items. Write the comment explaining the
choice at the moment the line is typed.

### UX decisions went unchallenged too long
The `EDIT` uppercase buttons and the `Created` column in search were live for several
milestones before the user flagged them as wrong. Claude had no signal to question
them because tests passed and the code was clean. The feedback loop on *usability* was
slower than the feedback loop on correctness.

**Fix forward**: at the end of each milestone, explicitly ask "what feels wrong using
this?" rather than waiting for the user to volunteer it. UI review as a scheduled step,
not a reactive one.

### Third-party asset attribution was an afterthought
Catppuccin needed a license check and an attribution file. It went fine because MIT is
permissive, but the instinct to check *before* pulling values was absent — the user
asked about licensing, which prompted the check. For any future third-party
asset (fonts, icon sets, snippets), the first action should be reading the license.

### Release-branch dance keeps catching us off guard
Branch protection on `main` has rejected direct pushes at least twice in this
project's history. Each time it's a small correction (`reset --soft HEAD~1`, new
branch, PR) but it interrupts the release flow.

**Fix forward**: document the release workflow in `RESUMING.md` (done) so the first
attempt is always a `chore/release-X.Y.Z` branch, not a direct push.

## What was neutral but worth noting

### The two-model workflow (Opus plan / Sonnet implement)
Described in `CLAUDE.md` but used loosely — most work ran on Opus start to finish. It
didn't hurt, but the separation wasn't a load-bearing part of the collaboration. If
kept, it should have an actual trigger (spec in `docs/specs/` before any PR above size
S). Otherwise drop the convention.

### Memory growth
Four memory files is the right order of magnitude. Lean to delete stale entries
rather than accumulate. The one entry that grew brittle (`milestone progress`) needed
updating every release — consider whether a project-progress memory is worth it when
`PLAN.md` is already authoritative.

## One-line summary

The technical gates (tests, lint, types, repository-layer-only) worked exactly as
designed. The weak spots were all *editorial*: docs not matching code, defaults not
reconsidered, UX not reviewed. Build a rhythm for those too.

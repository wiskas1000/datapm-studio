# Lookup Table Management — Planning Notes

Scope: UI for managing `entity_type` and `aggregation_level` lookup tables
(rename / delete / merge / index + counts). Captured after the v0.6.0 search
wiring shipped, while the idea was fresh. **Not yet on the roadmap** — this
doc is a picture of the workload so we can decide whether to commit.

## Why this exists

Today, entity types and aggregation levels can be created from the data-file
form and are visible as chips on search and as options in the new search
filters (v0.6.0). There is no way to:

- See them all in one place with usage counts.
- Rename one (e.g. fix a typo or normalise `customers` → `customer`).
- Delete an unused one.
- Merge a duplicate into another.

Tags have the same structural shape and the same gap. Decide up-front whether
to include them (see "Open decisions" below).

## Where the work splits: core vs Studio

Most of the hard work is **in core** (`data-project-manager`), not Studio.
Studio can't add repository methods — it can only call them. So the
dependency order is core-first.

### Core (data-project-manager) — prerequisites

| # | Work item | Blocks Studio item |
|---|-----------|--------------------|
| C1 | `list_with_counts()` / `usage_count(id)` on `EntityTypeRepository` and `AggregationLevelRepository` | S1 |
| C2 | `rename(id, new_name)` — normalises, rejects collisions | S2 |
| C3 | `delete(id)` — rejects if any `data_file_entity_type` / `data_file_aggregation` row references it | S3 |
| C4 | `merge(source_id, target_id)` — reassigns join rows, deletes source, idempotent on the target | S4 |

Open issues in the **core** repo for each. Can be grouped (e.g. one issue per
method family covering both repositories).

### Studio — depends on core

| # | Work item | Blocked by |
|---|-----------|------------|
| S1 | `/entity-types` and `/aggregation-levels` index pages: list every name with usage count, seeded vs custom badge | C1 |
| S2 | Inline rename on index page (same pattern as existing inline-edit on project fields) | C2 |
| S3 | Delete button, disabled when `usage_count > 0`, with confirm dialog | C3 |
| S4 | Merge flow: pick source → pick target → confirm → toast | C4 |
| S5 | Nav entry (one "Lookups" menu or two links) — trivial, lands with S1 | — |
| S6 | "Add new" button on the index page (symmetry with current tag/person management) | — |

## Priority call (as of 2026-04-17)

Ship the 80%: **C1 → S1 → C2 → S2**. That covers "see what's there" and "fix
typos." Defer C3/S3 and C4/S4 until the pain is real — delete and merge are
rarely-needed power-user features and the migration-safety implications of
merge (referential integrity across 4+ join tables) are not trivial.

## Open decisions (before opening issues)

1. **Tags in scope?** Structurally identical (lookup + M:N join, seeded +
   custom). Either include them now and pay once, or explicitly exclude and
   accept the inconsistency until a future pass. Leaning exclude — addressing
   later as "same pattern, apply here too" is cheap.
2. **Case normalisation in the UI.** Core lowercases on create. Should the
   index page display values as-is (lowercase) or preserve a display name?
   Simplest: display lowercase everywhere. Affects S1 + S2.
3. **Seeded values: immutable?** Probably yes — rename/delete only for
   user-created rows. Would need a `seeded BOOLEAN` flag (or a lookup against
   the migration seed list) to enforce. Decide before C2/C3.

## Suggested issue layout

If we commit to this:

- **Tracker / epic** on `wiskas1000/datapm-studio`: "Lookup table management
  for entity types and aggregation levels." Links to the core issues and
  lists S1–S6.
- **Core issues** on `wiskas1000/data-project-manager`: one per method family
  (C1, C2, C3, C4) or consolidated as one "Lookup management API" issue if
  preferred.
- **Studio issues**: one per row in the Studio table above, each marked
  `blocked by #<core issue>` where applicable.

## What this isn't

- Not scoped: a generic "admin panel". Keep it to these specific tables.
- Not scoped: bulk import/export of lookup values. If needed, a separate
  issue after S1 exists.
- Not scoped: per-project lookup overrides. Lookups are global.

## Pointers

- v0.6.0 release notes — where entity types / agg levels got search filter
  exposure: <https://github.com/wiskas1000/datapm-studio/releases/tag/v0.6.0>
- Core `core.search.search_project_metadata` — the existing surface that
  already reads from these tables, useful reference for the shape of new
  methods.
- `docs/RESUMING.md` — release workflow and non-negotiable contracts.

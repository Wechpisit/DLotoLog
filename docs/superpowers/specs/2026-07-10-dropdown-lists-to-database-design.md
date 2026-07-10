# Design: Move Hardcoded Dropdown Lists to Database

**Date:** 2026-07-10
**Status:** Approved by user, pending implementation plan

## Problem

`D-Loto.py`'s `list_setup()` (D-Loto.py:655-758) hardcodes 7 dropdown option lists directly in source: `incharge_list` (departments), `owner_list` (200+ employees), `sectionmgr_list` (6 section managers), `lomember_list` (~35 LO team members), `area_list` (work areas), `machine_list` (equipment), and `email_list` (name→email dict, currently unused dead data). Adding, removing, or editing any option requires editing source code and rebuilding/redistributing the executable to every client.

## Scope

- Move all 7 lists to SQLite tables in the existing app database.
- Admin edits list contents directly via SQL (`UPDATE`/`INSERT`/`UPDATE ... SET active=0`) — no new in-app admin UI in this iteration.
- Reuse the existing refresh button (calls `refresh_treeview()`) so running clients can pick up list changes without restarting.
- Out of scope: in-app UI for managing lists, cascading/filtered dropdowns (e.g. machine filtered by area), reordering (see "Sort order" below).

## Schema

### `employees`

Consolidates `owner_list`, `sectionmgr_list`, `lomember_list`, and `email_list` — these represent the same people wearing multiple overlapping "roles," not independent lists.

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    email TEXT,
    is_sectionmgr INTEGER NOT NULL DEFAULT 0,   -- 0/1
    is_lomember INTEGER NOT NULL DEFAULT 0,      -- 0/1
    active INTEGER NOT NULL DEFAULT 1            -- 0/1, soft-delete flag
);
```

Derived lists:
- `owner_list` = `SELECT name FROM employees WHERE active=1`
- `sectionmgr_list` = `SELECT name FROM employees WHERE active=1 AND is_sectionmgr=1`
- `lomember_list` = `SELECT name FROM employees WHERE active=1 AND is_lomember=1`
- `email_list` = `SELECT name, email FROM employees WHERE email IS NOT NULL` (preserved for potential future use — currently no code path reads it)

Removing someone (e.g. resignation) sets `active=0` rather than deleting the row, so historical LOTO records (which store names as free text, not foreign keys) stay unaffected and the person can be reactivated later without retyping.

### `dropdown_options`

Consolidates `incharge_list`, `area_list`, `machine_list` — flat text lists with no role overlap, so one generic lookup table covers all three instead of three near-identical tables.

```sql
CREATE TABLE dropdown_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_name TEXT NOT NULL,   -- 'incharge' | 'area' | 'machine'
    value TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    UNIQUE(list_name, value)
);
```

Derived lists: `SELECT value FROM dropdown_options WHERE list_name = ? AND active = 1`

### Sort order

Not tracked in either table. `input_field_dropdown.__init__` and `input_field_dropdown_linebreak.__init__` both already do `self.original_values = sorted(options)` (D-Loto.py:1762, 1933) — every dropdown is alphabetized by the widget at construction time regardless of input order, so a `sort_order` column would be unused dead weight.

## Data Flow

### Startup

`list_setup()` is replaced by a **module-level** function (following the precedent set by the auto-update feature: "core functions are module-level, not nested in `main()`, so they're unit-testable in isolation"):

```python
# module-level
def load_dropdown_lists(conn):
    # CREATE TABLE IF NOT EXISTS for both tables (idempotent, guards against
    # a DB that hasn't been migrated yet)
    # ... queries ...
    return incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list
```

Called once inside `main()` right after a successful DB connection, replacing the old `list_setup()` call — same 7-value unpacking signature, so every call site elsewhere in the file (~15 usages of these variable names) needs no changes.

### Refresh without restart

The app already has a refresh button (`refresh2.png` icon) on all three tabs (Overview/Pending/Completed), wired to `refresh_treeview()` (D-Loto.py:761). `reload_dropdown_lists()` — a `main()`-nested function using `nonlocal` to rebind the 7 outer variables — is added as the first line of `refresh_treeview()`:

```python
def refresh_treeview():
    reload_dropdown_lists()   # re-query DB, rebind list variables
    print("Refreshing treeview")
    update_table_overview()
    update_table_pending()
    update_table_completed()
```

Because dropdown widgets snapshot `sorted(options)` at construction time (not a live reference), reassigning the module-level list variables is safe — it doesn't affect popups already open, and any popup opened after a refresh picks up the latest data automatically.

### Migration (one-time)

A one-off script (`migrate_dropdown_lists.py`) that:
1. `CREATE TABLE IF NOT EXISTS` for both tables.
2. Seeds rows from the current hardcoded lists in `list_setup()` — computing `is_sectionmgr`/`is_lomember` from membership in `sectionmgr_list`/`lomember_list`, and `email` from `email_list`.
3. Is run once against the dev DB first, then again against the production DB during rollout (same pattern as the still-pending `app_info.exe_path` production setup — document the reminder in `DatabaseLocation/` the same way).
4. After migration is verified, the hardcoded lists are deleted from `D-Loto.py` entirely (`list_setup()` removed, replaced by `load_dropdown_lists()`).

## Error Handling

`load_dropdown_lists()` runs `CREATE TABLE IF NOT EXISTS` for both tables before querying, so a DB that hasn't been migrated yet doesn't crash the app. If a query returns zero rows (e.g. migration was forgotten), a one-time `show_message()` warning is shown at startup instead of silently presenting empty dropdowns to the user.

## Testing

Added to `test_loto.py` (or a new `test_dropdown_lists.py`, following the `test_auto_update.py` precedent):
- `load_dropdown_lists()` returns data matching what's in the DB, respecting `active=1` filters.
- A person with `is_sectionmgr=1` appears in `sectionmgr_list`; a person with `active=0` does not appear in `owner_list`.
- The migration script is idempotent — re-running it doesn't error or duplicate rows (enforced by the `UNIQUE` constraints).

## Explicitly Out of Scope (this iteration)

- In-app UI for adding/editing/removing list entries (admin uses direct SQL for now).
- Cascading/filtered dropdowns (e.g., machine list filtered by selected area) — not present today, not being added.
- Any change to how `loto_new` and other data tables store these values (still stored as plain text, not foreign keys).

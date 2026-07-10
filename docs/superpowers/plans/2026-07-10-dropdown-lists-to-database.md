# Dropdown Lists to Database Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 7 hardcoded dropdown lists in `list_setup()` (D-Loto.py) with data read from two new SQLite tables (`employees`, `dropdown_options`), so an admin can add/edit/remove options via SQL without rebuilding the executable, and running clients can pick up changes via the existing refresh button.

**Architecture:** A module-level `load_dropdown_lists(cursor)` function (following the existing auto-update-feature precedent of module-level, unit-testable functions) queries both tables and returns the same 7-value tuple `list_setup()` used to return, so every call site elsewhere in `D-Loto.py` needs zero changes. A one-off `migrate_dropdown_lists.py` script seeds the tables from the current hardcoded data by parsing `list_setup()`'s AST (not executing it — `list_setup()` is nested inside `main()`, which launches the GUI). A new `reload_dropdown_lists()` nested function inside `main()` rebinds the list variables via `nonlocal` and is wired into the existing `refresh_treeview()` so users can refresh without restarting.

**Tech Stack:** Python 3.13, sqlite3 (stdlib), Tkinter (existing app), `ast` (stdlib, for one-off migration parsing) — no new dependencies.

## Global Constraints

- No in-app admin UI in this iteration — admin edits table contents directly via SQL (`INSERT`/`UPDATE ... SET active=0`). See spec §Scope.
- `employees` table columns: `id, name (UNIQUE), email, is_sectionmgr, is_lomember, active` (0/1 ints). See spec §Schema.
- `dropdown_options` table columns: `id, list_name, value, active` (0/1 int), `UNIQUE(list_name, value)`. `list_name` values used: `'incharge'`, `'area'`, `'machine'`. See spec §Schema.
- No `sort_order` column anywhere — `input_field_dropdown`/`input_field_dropdown_linebreak` already do `sorted(options)` at construction time (D-Loto.py:1762, 1933). See spec §Sort order.
- Soft-delete only: removing a person/option sets `active=0`, never `DELETE`. See spec §Schema.
- New functions that don't need Tkinter state must be **module-level**, not nested in `main()`, per the precedent set by the auto-update feature — this is what makes them unit-testable via plain `assert`-based test files (see `test_auto_update.py`). This repo has no pytest; tests are plain functions run via `python test_x.py` with a trailing `if __name__ == "__main__":` block, matching `test_auto_update.py` exactly.
- User-facing dialog text is Thai (matches existing `show_message`/`messagebox` calls elsewhere in D-Loto.py).
- Only edit the root `D-Loto.py` — `TestBuildFromCommandLine/D-Loto.py` is a generated copy, synced by `build.ps1`, never hand-edited.

---

### Task 1: Migration script — extract hardcoded lists via AST, seed DB

**Files:**
- Create: `migrate_dropdown_lists.py`
- Test: `test_migrate_dropdown_lists.py`

**Interfaces:**
- Produces: `_extract_list_setup_lists(dloto_source_path: str) -> dict[str, list | dict]` — keys `incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list`.
- Produces: `create_dropdown_tables(cursor)` — idempotent `CREATE TABLE IF NOT EXISTS` for both tables.
- Produces: `seed_employees(cursor, owner_list, sectionmgr_list, lomember_list, email_list)`.
- Produces: `seed_dropdown_options(cursor, list_name: str, values: list[str])`.
- Produces: `migrate(cursor, lists: dict) -> None` — calls the three functions above in order.

This script reads the *current* hardcoded lists straight out of `D-Loto.py`'s source (via `ast`, without executing `main()` or launching the GUI) rather than having them retyped here, so there's no risk of a transcription error in a 200+ name roster. It only works while `list_setup()` still exists in the D-Loto.py source being parsed — Task 4 deletes it from `D-Loto.py`'s HEAD, so a future production run must point this script at an older revision of the file (see Task 5's `DatabaseLocation` reminder for the exact command).

- [ ] **Step 1: Write the failing tests**

```python
# test_migrate_dropdown_lists.py
import os
import sqlite3
import migrate_dropdown_lists as migrate_mod


def test_extract_list_setup_lists_finds_all_seven_lists():
    dloto_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "D-Loto.py")
    lists = migrate_mod._extract_list_setup_lists(dloto_path)
    assert set(lists.keys()) == {
        "incharge_list", "owner_list", "sectionmgr_list",
        "lomember_list", "area_list", "machine_list", "email_list",
    }
    assert len(lists["owner_list"]) > 200
    assert "Kittiwat.Ro" in lists["sectionmgr_list"]
    assert "Kittiwat.Ro" in lists["lomember_list"]
    assert "Kittiwat.Ro" in lists["owner_list"]


def test_migrate_seeds_employees_with_correct_roles():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    lists = {
        "incharge_list": ["MT.Mech"],
        "owner_list": ["Alice", "Bob"],
        "sectionmgr_list": ["Alice"],
        "lomember_list": ["Bob"],
        "area_list": ["HP Pump"],
        "machine_list": ["HP Pump A"],
        "email_list": {"Bob": "bob@pttlng.com"},
    }
    migrate_mod.migrate(cursor, lists)
    conn.commit()

    cursor.execute("SELECT name, email, is_sectionmgr, is_lomember, active FROM employees ORDER BY name")
    rows = cursor.fetchall()
    assert rows == [
        ("Alice", None, 1, 0, 1),
        ("Bob", "bob@pttlng.com", 0, 1, 1),
    ]
    conn.close()


def test_migrate_seeds_dropdown_options():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    lists = {
        "incharge_list": ["MT.Mech", "MT.Ins"],
        "owner_list": [],
        "sectionmgr_list": [],
        "lomember_list": [],
        "area_list": ["HP Pump"],
        "machine_list": ["HP Pump A", "HP Pump B"],
        "email_list": {},
    }
    migrate_mod.migrate(cursor, lists)
    conn.commit()

    cursor.execute("SELECT value FROM dropdown_options WHERE list_name = 'incharge' ORDER BY value")
    assert [r[0] for r in cursor.fetchall()] == ["MT.Ins", "MT.Mech"]
    cursor.execute("SELECT value FROM dropdown_options WHERE list_name = 'machine' ORDER BY value")
    assert [r[0] for r in cursor.fetchall()] == ["HP Pump A", "HP Pump B"]
    conn.close()


def test_migrate_is_idempotent():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    lists = {
        "incharge_list": ["MT.Mech"],
        "owner_list": ["Alice"],
        "sectionmgr_list": [],
        "lomember_list": [],
        "area_list": [],
        "machine_list": [],
        "email_list": {},
    }
    migrate_mod.migrate(cursor, lists)
    migrate_mod.migrate(cursor, lists)  # run twice — must not error or duplicate
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM employees")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT COUNT(*) FROM dropdown_options")
    assert cursor.fetchone()[0] == 1
    conn.close()


if __name__ == "__main__":
    test_extract_list_setup_lists_finds_all_seven_lists()
    test_migrate_seeds_employees_with_correct_roles()
    test_migrate_seeds_dropdown_options()
    test_migrate_is_idempotent()
    print("All tests passed.")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python test_migrate_dropdown_lists.py`
Expected: `ModuleNotFoundError: No module named 'migrate_dropdown_lists'`

- [ ] **Step 3: Write the implementation**

```python
# migrate_dropdown_lists.py
"""One-off migration: seed `employees` and `dropdown_options` tables in the
LOTO SQLite database from the hardcoded dropdown lists still defined in
`list_setup()` inside D-Loto.py's main(). Reads the lists via source parsing
(ast), NOT by importing/executing D-Loto.py — list_setup() is nested inside
main(), and executing main() would launch the GUI.

Only works while list_setup() still exists in the D-Loto.py source being
parsed. After it's removed from HEAD (see the commit that wires
load_dropdown_lists() into main()), point this script at an older revision
of the file instead, e.g.:
    git show <commit-before-removal>:D-Loto.py > old_D-Loto.py
    python migrate_dropdown_lists.py <db-path> old_D-Loto.py

Usage: python migrate_dropdown_lists.py <path-to-loto_data.db> [path-to-D-Loto.py-source]
"""
import ast
import os
import sqlite3
import sys


def _extract_list_setup_lists(dloto_source_path):
    with open(dloto_source_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=dloto_source_path)

    list_setup_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "list_setup":
            list_setup_node = node
            break
    if list_setup_node is None:
        raise ValueError("list_setup() not found in D-Loto.py — already migrated?")

    target_names = {
        "incharge_list", "owner_list", "sectionmgr_list",
        "lomember_list", "area_list", "machine_list", "email_list",
    }
    values = {}
    for stmt in list_setup_node.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                and isinstance(stmt.targets[0], ast.Name) \
                and stmt.targets[0].id in target_names:
            values[stmt.targets[0].id] = ast.literal_eval(stmt.value)

    missing = target_names - values.keys()
    if missing:
        raise ValueError(f"Could not find these lists in list_setup(): {missing}")
    return values


def create_dropdown_tables(cursor):
    cursor.execute("""CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        email TEXT,
        is_sectionmgr INTEGER NOT NULL DEFAULT 0,
        is_lomember INTEGER NOT NULL DEFAULT 0,
        active INTEGER NOT NULL DEFAULT 1
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS dropdown_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_name TEXT NOT NULL,
        value TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        UNIQUE(list_name, value)
    )""")


def seed_employees(cursor, owner_list, sectionmgr_list, lomember_list, email_list):
    for name in owner_list:
        cursor.execute(
            "INSERT OR IGNORE INTO employees (name, email, is_sectionmgr, is_lomember, active) "
            "VALUES (?, ?, ?, ?, 1)",
            (name, email_list.get(name), int(name in sectionmgr_list), int(name in lomember_list)),
        )


def seed_dropdown_options(cursor, list_name, values):
    for value in values:
        cursor.execute(
            "INSERT OR IGNORE INTO dropdown_options (list_name, value, active) VALUES (?, ?, 1)",
            (list_name, value),
        )


def migrate(cursor, lists):
    create_dropdown_tables(cursor)
    seed_employees(cursor, lists["owner_list"], lists["sectionmgr_list"], lists["lomember_list"], lists["email_list"])
    seed_dropdown_options(cursor, "incharge", lists["incharge_list"])
    seed_dropdown_options(cursor, "area", lists["area_list"])
    seed_dropdown_options(cursor, "machine", lists["machine_list"])


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("Usage: python migrate_dropdown_lists.py <path-to-loto_data.db> [path-to-D-Loto.py-source]")
        sys.exit(1)

    db_path = sys.argv[1]
    dloto_path = sys.argv[2] if len(sys.argv) == 3 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "D-Loto.py"
    )
    lists = _extract_list_setup_lists(dloto_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    migrate(cursor, lists)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM employees")
    employee_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM dropdown_options")
    option_count = cursor.fetchone()[0]
    conn.close()

    print(f"Migration complete: {employee_count} employees, {option_count} dropdown options seeded into {db_path}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python test_migrate_dropdown_lists.py`
Expected: `All tests passed.`

- [ ] **Step 5: Commit**

```bash
git add migrate_dropdown_lists.py test_migrate_dropdown_lists.py
git commit -m "Add one-off migration script for dropdown lists to DB tables"
```

---

### Task 2: `load_dropdown_lists()` — module-level DB reader in D-Loto.py

**Files:**
- Modify: `D-Loto.py` (add module-level function, right after the auto-update helpers block and before `def main():`)
- Test: `test_dropdown_lists.py`

**Interfaces:**
- Consumes: nothing from Task 1 (independent — reads from whatever DB schema it creates itself).
- Produces: module-level `load_dropdown_lists(cursor) -> tuple[list, list, list, list, list, list, dict]` — order: `incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list`. This exact signature and return order is what Task 4 wires into `main()`.

- [ ] **Step 1: Write the failing tests**

```python
# test_dropdown_lists.py
import importlib.util
import os
import sqlite3


def _load_dloto_module():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "D-Loto.py")
    spec = importlib.util.spec_from_file_location("dloto_module_under_test_dropdowns", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dloto = _load_dloto_module()


def test_load_dropdown_lists_creates_tables_on_empty_db():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    result = dloto.load_dropdown_lists(cursor)
    assert result == ([], [], [], [], [], [], {})
    conn.close()


def test_load_dropdown_lists_filters_active_and_roles():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    dloto.load_dropdown_lists(cursor)  # creates tables
    cursor.executemany(
        "INSERT INTO employees (name, email, is_sectionmgr, is_lomember, active) VALUES (?, ?, ?, ?, ?)",
        [
            ("Alice", None, 1, 0, 1),
            ("Bob", "bob@pttlng.com", 0, 1, 1),
            ("Charlie", None, 0, 0, 0),  # inactive — must not appear anywhere
        ],
    )
    conn.commit()

    incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list = \
        dloto.load_dropdown_lists(cursor)

    assert owner_list == ["Alice", "Bob"]
    assert sectionmgr_list == ["Alice"]
    assert lomember_list == ["Bob"]
    assert email_list == {"Bob": "bob@pttlng.com"}
    conn.close()


def test_load_dropdown_lists_filters_dropdown_options_by_list_name_and_active():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    dloto.load_dropdown_lists(cursor)  # creates tables
    cursor.executemany(
        "INSERT INTO dropdown_options (list_name, value, active) VALUES (?, ?, ?)",
        [
            ("incharge", "MT.Mech", 1),
            ("area", "HP Pump", 1),
            ("area", "Old Area", 0),  # inactive — must not appear
            ("machine", "HP Pump A", 1),
        ],
    )
    conn.commit()

    incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list = \
        dloto.load_dropdown_lists(cursor)

    assert incharge_list == ["MT.Mech"]
    assert area_list == ["HP Pump"]
    assert machine_list == ["HP Pump A"]
    conn.close()


if __name__ == "__main__":
    test_load_dropdown_lists_creates_tables_on_empty_db()
    test_load_dropdown_lists_filters_active_and_roles()
    test_load_dropdown_lists_filters_dropdown_options_by_list_name_and_active()
    print("All tests passed.")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python test_dropdown_lists.py`
Expected: `AttributeError: module 'dloto_module_under_test_dropdowns' has no attribute 'load_dropdown_lists'`

- [ ] **Step 3: Add the implementation to D-Loto.py**

Insert this as a new module-level function, immediately after the `cleanup_stale_backup()` function definition (D-Loto.py, right before `def perform_update(...)`) — i.e. in the same module-level block as the other auto-update helpers, since it follows the same "module-level, testable" convention:

```python
# --- Dropdown list helpers (module-level: testable — see test_dropdown_lists.py.
# Table DDL here must stay in sync with migrate_dropdown_lists.py's
# create_dropdown_tables()) ---

def load_dropdown_lists(cursor):
    """Reads all 7 dropdown lists from the DB, creating the backing tables
    first if they don't exist yet (so a DB that hasn't been migrated yet
    doesn't crash the app — see migrate_dropdown_lists.py for the one-time
    seed from the old hardcoded lists)."""
    cursor.execute("""CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        email TEXT,
        is_sectionmgr INTEGER NOT NULL DEFAULT 0,
        is_lomember INTEGER NOT NULL DEFAULT 0,
        active INTEGER NOT NULL DEFAULT 1
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS dropdown_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_name TEXT NOT NULL,
        value TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        UNIQUE(list_name, value)
    )""")

    cursor.execute("SELECT name FROM employees WHERE active = 1")
    owner_list = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM employees WHERE active = 1 AND is_sectionmgr = 1")
    sectionmgr_list = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM employees WHERE active = 1 AND is_lomember = 1")
    lomember_list = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name, email FROM employees WHERE email IS NOT NULL")
    email_list = {row[0]: row[1] for row in cursor.fetchall()}

    def _dropdown_values(list_name):
        cursor.execute(
            "SELECT value FROM dropdown_options WHERE list_name = ? AND active = 1",
            (list_name,),
        )
        return [row[0] for row in cursor.fetchall()]

    incharge_list = _dropdown_values('incharge')
    area_list = _dropdown_values('area')
    machine_list = _dropdown_values('machine')

    return incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python test_dropdown_lists.py`
Expected: `All tests passed.`

- [ ] **Step 5: Commit**

```bash
git add D-Loto.py test_dropdown_lists.py
git commit -m "Add load_dropdown_lists() module-level DB reader"
```

---

### Task 3: Run migration against the dev database

**Files:**
- Modify (binary, via script): `loto_data.db` (repo root — the dev-mode DB per `ENV = 'dev'` in D-Loto.py:181)

**Interfaces:**
- Consumes: Task 1's `migrate_dropdown_lists.py` CLI.
- Produces: a `loto_data.db` with populated `employees` and `dropdown_options` tables, ready for Task 4's manual verification.

This must run **before** Task 4 removes `list_setup()` from `D-Loto.py` — the script depends on that function still being present in the source it's parsing.

- [ ] **Step 1: Run the migration**

Run (from repo root):
```bash
python migrate_dropdown_lists.py loto_data.db
```
Expected output: `Migration complete: <N> employees, <M> dropdown options seeded into loto_data.db` where N is 200+ and M is the combined count of incharge+area+machine entries.

- [ ] **Step 2: Spot-check the seeded data**

Run:
```bash
python -c "import sqlite3; c = sqlite3.connect('loto_data.db').cursor(); print(c.execute(\"SELECT name, is_sectionmgr, is_lomember, active FROM employees WHERE name = 'Kittiwat.Ro'\").fetchone()); print(c.execute(\"SELECT COUNT(*) FROM employees\").fetchone()); print(c.execute(\"SELECT COUNT(*) FROM dropdown_options WHERE list_name='area'\").fetchone())"
```
Expected: first line shows `('Kittiwat.Ro', 1, 1, 1)` (both role flags set, matching that this person is in `owner_list`, `sectionmgr_list`, and `lomember_list` in the current source); second line shows a count above 200; third line shows the area-list count (51 per the current hardcoded `area_list`).

- [ ] **Step 3: Commit the migrated dev DB**

```bash
git add loto_data.db
git commit -m "Run dropdown-list migration against dev database"
```

---

### Task 4: Wire `load_dropdown_lists()`/`reload_dropdown_lists()` into `main()`, remove `list_setup()`

**Files:**
- Modify: `D-Loto.py` (inside `main()`)

**Interfaces:**
- Consumes: Task 2's `load_dropdown_lists(cursor)`; Task 3's populated dev DB.
- Produces: `reload_dropdown_lists()` — a `main()`-nested function, no args, no return value, rebinds `incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list` via `nonlocal`. Called once at startup and from `refresh_treeview()`.

No automated test is possible for this step (it's Tkinter GUI wiring; this repo has no headless UI test harness) — verification is manual, per this repo's established practice for GUI changes (see `verify` skill / CLAUDE.md's "Running/testing the app").

- [ ] **Step 1: Replace `list_setup()` with the DB-backed loader**

In `D-Loto.py`, find the block starting at the comment `# Create list for Dropdown` and ending at the line `incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list = list_setup()` (the entire `list_setup()` function definition plus its call — currently ~105 lines). Read the file to get the exact text for the edit's `old_string` (it's uniquely bounded by that comment and that call line, so an exact match is unambiguous). Replace the whole block with:

```python
    # Load dropdown lists from DB (module-level load_dropdown_lists() —
    # see migrate_dropdown_lists.py for the one-time seed from the old
    # hardcoded lists, and test_dropdown_lists.py for its tests)
    incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list = ([], [], [], [], [], [], {})

    def reload_dropdown_lists():
        """Re-queries the DB and rebinds the dropdown list variables in place.
        Called once at startup and again from refresh_treeview(). Safe to call
        any time a popup is open: input_field_dropdown/_linebreak snapshot
        sorted(options) at construction time (see their __init__), so this
        never mutates a widget already on screen — only popups opened after
        this call see the refreshed data."""
        nonlocal incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list
        incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list = load_dropdown_lists(c)
        if not (incharge_list and owner_list and area_list and machine_list):
            show_message(
                "Warning",
                "รายการตัวเลือกบางส่วนว่างเปล่า กรุณาตรวจสอบข้อมูลใน database (employees / dropdown_options)"
            )
    reload_dropdown_lists()
```

- [ ] **Step 2: Hook the refresh button into the reload**

Find:
```python
    def refresh_treeview():
        print("Refreshing treeview")
        update_table_overview()
        update_table_pending()
        update_table_completed()
```

Replace with:
```python
    def refresh_treeview():
        reload_dropdown_lists()
        print("Refreshing treeview")
        update_table_overview()
        update_table_pending()
        update_table_completed()
```

- [ ] **Step 3: Sync the build copy and sanity-check the file compiles**

```bash
powershell -File "TestBuildFromCommandLine/build.ps1"
```
Expected: no PyInstaller errors; this both syncs `TestBuildFromCommandLine/D-Loto.py` and proves the edited file is syntactically valid (PyInstaller imports it).

If you'd rather not do a full PyInstaller build at this point, at minimum run:
```bash
py -3.13 -c "import ast; ast.parse(open('D-Loto.py', encoding='utf-8').read())"
```
Expected: no output (no `SyntaxError`).

- [ ] **Step 4: Manually verify — real run against the migrated dev DB**

The empty-list case (`reload_dropdown_lists()`'s `if not (...)` branch) is already covered by Task 2's automated test `test_load_dropdown_lists_creates_tables_on_empty_db` — no need to re-verify that in the running app. This step verifies the real end-to-end flow against actual data.

Run (dev `ENV` is already `'dev'` by default in D-Loto.py:181):
```bash
py -3.13 D-Loto.py
```
Checklist while the app is open:
- Main window opens with no "Warning" popup (dev DB was migrated in Task 3, so lists aren't empty).
- Open "New LOTO" (the form that uses `owner_list`, `incharge_list`, `area_list`, `machine_list`, `sectionmgr_list`, `lomember_list`) and confirm each dropdown shows real names/values, not empty.
- While the app is still running, in a separate terminal add a test option:
  ```bash
  python -c "import sqlite3; c = sqlite3.connect('loto_data.db'); c.execute(\"INSERT INTO dropdown_options (list_name, value, active) VALUES ('area', 'Test New Area', 1)\"); c.commit(); c.close()"
  ```
- Click the refresh icon button on any tab (Overview/Pending/Completed).
- Open "New LOTO" again and confirm "Test New Area" now appears in the Working area dropdown — proving the refresh button picked up the DB change without restarting.
- Clean up the test row:
  ```bash
  python -c "import sqlite3; c = sqlite3.connect('loto_data.db'); c.execute(\"DELETE FROM dropdown_options WHERE value = 'Test New Area'\"); c.commit(); c.close()"
  ```
- Close the app.

- [ ] **Step 5: Commit**

```bash
git add D-Loto.py "TestBuildFromCommandLine/D-Loto.py"
git commit -m "Wire load_dropdown_lists()/reload_dropdown_lists() into main(), remove hardcoded list_setup()"
```

---

### Task 5: Documentation

**Files:**
- Modify: `CLAUDE.md`
- Create: `DatabaseLocation/Before going to Production - migrate dropdown lists.txt`

**Interfaces:** None (docs only).

- [ ] **Step 1: Update CLAUDE.md's Quick Reference line**

Find:
```
- Employee lists: D-Loto.py:429-490 (`list_setup()` function)
```

Replace with:
```
- Employee/dropdown lists: `employees` and `dropdown_options` tables in the DB (loaded via `load_dropdown_lists()`, D-Loto.py) — edit via SQL, not code. See `migrate_dropdown_lists.py` for the one-time seed script.
```

- [ ] **Step 2: Update CLAUDE.md's Business Data section**

Find:
```
**Business Data** (D-Loto.py:429-490):
- Hardcoded dropdown lists defined in `list_setup()` function:
  - `incharge_list`: Departments (MT.Mech, MT.Ins, MT.Elec, ED.*, Project, LO., etc.)
  - `owner_list`: 200+ employee names (full employee roster)
  - `sectionmgr_list`: Section managers (6 names)
  - `lomember_list`: LO (Lock Out) team members (~35 names)
  - `area_list`: Work areas (HP Pump, BOG Compressor, Jetty, etc.)
- These lists are critical for data validation and dropdown population
- Updating employee names or departments requires modifying `list_setup()`
```

Replace with:
```
**Business Data** (`load_dropdown_lists()` in D-Loto.py, reads from the DB):
- `employees` table: name, email, `is_sectionmgr`/`is_lomember` role flags, `active` flag — one row per person, since owner/section-manager/LO-member roles overlap on the same people. Derives `owner_list` (all active), `sectionmgr_list` (active + `is_sectionmgr=1`), `lomember_list` (active + `is_lomember=1`), `email_list` (name→email dict, currently unused by any code path but preserved for future use).
- `dropdown_options` table: flat `(list_name, value, active)` rows for `incharge` (departments), `area` (work areas), and `machine` (equipment) — no role overlap between these three, so one generic table covers all of them.
- No sort order is stored — `input_field_dropdown`/`input_field_dropdown_linebreak` already alphabetize at construction time.
- To add/edit/remove an option: run SQL directly against the DB (e.g. `INSERT INTO employees (name, is_lomember, active) VALUES ('New.Person', 1, 1);` or `UPDATE employees SET active=0 WHERE name='Old.Person';`) — never delete rows, use the `active` flag so historical LOTO records (which store names as plain text) stay unaffected.
- Running clients pick up changes via the existing refresh button (calls `refresh_treeview()`, which now also calls `reload_dropdown_lists()`) — no restart needed.
- See `docs/superpowers/specs/2026-07-10-dropdown-lists-to-database-design.md` for the full design.
```

- [ ] **Step 3: Add the production migration reminder file**

```
ก่อนขึ้น Production จริง ต้อง migrate ตาราง employees / dropdown_options ก่อน!

ฟีเจอร์นี้ย้าย dropdown lists (owner, section manager, LO member, department,
area, machine) จาก hardcode ในโค้ด ไปเก็บใน 2 ตารางของ database:
employees และ dropdown_options

ตอนพัฒนา ได้รัน migrate_dropdown_lists.py กับ dev DB ไปแล้ว (ดู commit
"Run dropdown-list migration against dev database") แต่ยังไม่เคยรันกับ
production DB (L:\4.4LO.T1\06-Operational_and_Record\6.56 LOTO\loto_data.db)

migrate_dropdown_lists.py อ่านรายชื่อ/ตัวเลือกโดย parse โค้ดจาก list_setup()
ใน D-Loto.py ซึ่งถูกลบออกจากไฟล์ปัจจุบันแล้ว (หลัง commit "Wire
load_dropdown_lists()/reload_dropdown_lists() into main(), remove hardcoded
list_setup()") ต้องดึงไฟล์ D-Loto.py เวอร์ชันก่อนถูกลบมาใช้แทน:

    git log --oneline -- D-Loto.py
    (หา commit ก่อนหน้า commit ที่ชื่อ "Wire load_dropdown_lists()... remove
    hardcoded list_setup()" แล้วใช้ commit นั้น)

    git show <commit-hash-ก่อนลบ>:D-Loto.py > old_D-Loto.py
    python migrate_dropdown_lists.py "L:/4.4LO.T1/06-Operational_and_Record/6.56 LOTO/loto_data.db" old_D-Loto.py

รันคำสั่งด้านบนแล้วเช็คผลลัพธ์ว่า "Migration complete: <N> employees, <M>
dropdown options seeded" ก่อนปล่อยให้ users เชื่อมต่อ production DB

ดูรายละเอียดทั้งหมดได้ที่ docs/superpowers/specs/2026-07-10-dropdown-lists-to-database-design.md
```

Save this to `DatabaseLocation/Before going to Production - migrate dropdown lists.txt`.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md "DatabaseLocation/Before going to Production - migrate dropdown lists.txt"
git commit -m "Document DB-backed dropdown lists, add pre-production migration reminder"
```

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

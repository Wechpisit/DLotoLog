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

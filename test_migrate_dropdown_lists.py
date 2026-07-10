import os
import sqlite3
import tempfile
import migrate_dropdown_lists as migrate_mod


_SAMPLE_LIST_SETUP_SOURCE = '''
def main():
    def list_setup():
        incharge_list = ['MT.Mech', 'MT.Ins']
        owner_list = ['Alice', 'Bob', 'Kittiwat.Ro']
        sectionmgr_list = ['Kittiwat.Ro']
        lomember_list = ['Bob', 'Kittiwat.Ro']
        area_list = ['HP Pump']
        machine_list = ['HP Pump A']
        email_list = {'Kittiwat.Ro': 'kittiwat.ro@pttlng.com'}
        return incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list
    incharge_list, owner_list, sectionmgr_list, lomember_list, area_list, machine_list, email_list = list_setup()
'''


def test_extract_list_setup_lists_finds_all_seven_lists():
    # Uses a small embedded fixture (not the live D-Loto.py) — after this
    # feature ships, list_setup() no longer exists in D-Loto.py's HEAD, so
    # this test must stay independent of that file's current state.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(_SAMPLE_LIST_SETUP_SOURCE)
        fixture_path = f.name
    try:
        lists = migrate_mod._extract_list_setup_lists(fixture_path)
        assert set(lists.keys()) == {
            "incharge_list", "owner_list", "sectionmgr_list",
            "lomember_list", "area_list", "machine_list", "email_list",
        }
        assert lists["owner_list"] == ["Alice", "Bob", "Kittiwat.Ro"]
        assert lists["sectionmgr_list"] == ["Kittiwat.Ro"]
        assert lists["lomember_list"] == ["Bob", "Kittiwat.Ro"]
        assert lists["email_list"] == {"Kittiwat.Ro": "kittiwat.ro@pttlng.com"}
    finally:
        os.remove(fixture_path)


def test_extract_list_setup_lists_raises_when_missing():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write("def main():\n    pass\n")
        fixture_path = f.name
    try:
        try:
            migrate_mod._extract_list_setup_lists(fixture_path)
            assert False, "expected ValueError"
        except ValueError as e:
            assert "list_setup" in str(e)
    finally:
        os.remove(fixture_path)


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
    test_extract_list_setup_lists_raises_when_missing()
    test_migrate_seeds_employees_with_correct_roles()
    test_migrate_seeds_dropdown_options()
    test_migrate_is_idempotent()
    print("All tests passed.")

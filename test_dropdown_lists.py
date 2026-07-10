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

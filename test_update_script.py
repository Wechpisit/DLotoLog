import importlib.util
import os
import sqlite3
import tempfile


def _load_dloto_module():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "D-Loto.py")
    spec = importlib.util.spec_from_file_location("dloto_module_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dloto = _load_dloto_module()


def test_marker_file_path_is_stable():
    p1 = dloto.get_marker_file_path()
    p2 = dloto.get_marker_file_path()
    assert p1 == p2
    assert p1.endswith("dloto_started.flag")


def test_mark_startup_success_writes_marker():
    marker = dloto.get_marker_file_path()
    if os.path.exists(marker):
        os.remove(marker)
    dloto.mark_startup_success()
    assert os.path.exists(marker)
    os.remove(marker)


def test_get_update_exe_path_returns_none_when_missing():
    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    c.execute("CREATE TABLE app_info (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    assert dloto.get_update_exe_path(c) is None
    conn.close()


def test_get_update_exe_path_returns_value_when_set():
    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    c.execute("CREATE TABLE app_info (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("INSERT INTO app_info VALUES ('exe_path', 'L:/some/path/D-Loto.exe')")
    conn.commit()
    assert dloto.get_update_exe_path(c) == 'L:/some/path/D-Loto.exe'
    conn.close()


def test_build_update_script_contains_all_paths():
    script = dloto.build_update_script(
        pid=1234,
        source_exe=r"L:\update\D-Loto.exe",
        dest_exe=r"C:\apps\D-Loto.exe",
        marker_file=r"C:\temp\dloto_started.flag",
        timeout_seconds=10,
    )
    assert "1234" in script
    assert r'"L:\update\D-Loto.exe"' in script
    assert r'"C:\apps\D-Loto.exe"' in script
    assert r'"C:\apps\D-Loto.exe.bak"' in script
    assert r'"C:\temp\dloto_started.flag"' in script
    assert "%WAITED% GEQ 10" in script
    assert "D-Loto.exe" in script  # exe_name used in taskkill


def test_build_update_script_normalizes_forward_slashes():
    """Regression test: cmd.exe's copy/move silently fail to find forward-slash
    paths (e.g. paths stored in the DB as "C:/foo/bar.exe") even though the file
    exists — confirmed by manually running `copy /y "C:/dtest/.../source" "C:/dtest/.../dest"`,
    which printed "The system cannot find the file specified." while the
    identical command with backslashes succeeded. build_update_script must
    always normalize to backslashes.
    """
    script = dloto.build_update_script(
        pid=1234,
        source_exe="C:/dtest/update/D-Loto_new.exe",
        dest_exe="C:/dtest/D-Loto.exe",
        marker_file="C:/temp/dloto_started.flag",
    )
    assert "C:/dtest" not in script  # the forward-slash form must not survive into the script
    assert r'"C:\dtest\update\D-Loto_new.exe"' in script
    assert r'"C:\dtest\D-Loto.exe"' in script


def test_write_update_script_creates_file():
    path = dloto.write_update_script(
        pid=1234,
        source_exe="L:/update/D-Loto.exe",
        dest_exe="C:/apps/D-Loto.exe",
        marker_file="C:/temp/dloto_started.flag",
    )
    assert os.path.exists(path)
    assert path.endswith("dloto_update.bat")
    with open(path) as f:
        content = f.read()
    assert "1234" in content
    os.remove(path)


if __name__ == "__main__":
    test_marker_file_path_is_stable()
    test_mark_startup_success_writes_marker()
    test_get_update_exe_path_returns_none_when_missing()
    test_get_update_exe_path_returns_value_when_set()
    test_build_update_script_contains_all_paths()
    test_build_update_script_normalizes_forward_slashes()
    test_write_update_script_creates_file()
    print("All tests passed.")

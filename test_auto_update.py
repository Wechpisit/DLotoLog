import importlib.util
import os
import shutil
import sqlite3
import subprocess
import tempfile
import threading


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


def test_swap_in_new_exe_replaces_content_and_returns_backup():
    tmp_dir = tempfile.mkdtemp(prefix="dloto_swap_test_")
    try:
        source = os.path.join(tmp_dir, "new.bin")
        dest = os.path.join(tmp_dir, "app.exe")
        with open(source, "wb") as f:
            f.write(b"NEW VERSION BYTES")
        with open(dest, "wb") as f:
            f.write(b"OLD VERSION BYTES")

        backup = dloto.swap_in_new_exe(source, dest)

        assert backup == dest + ".bak"
        assert os.path.exists(backup)
        assert os.path.exists(dest)
        assert not os.path.exists(dest + ".new")  # staging file cleaned up (renamed away)
        with open(backup, "rb") as f:
            assert f.read() == b"OLD VERSION BYTES"
        with open(dest, "rb") as f:
            assert f.read() == b"NEW VERSION BYTES"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_swap_in_new_exe_leaves_dest_untouched_if_copy_fails():
    tmp_dir = tempfile.mkdtemp(prefix="dloto_swap_test_")
    try:
        missing_source = os.path.join(tmp_dir, "does_not_exist.bin")
        dest = os.path.join(tmp_dir, "app.exe")
        with open(dest, "wb") as f:
            f.write(b"OLD VERSION BYTES")

        try:
            dloto.swap_in_new_exe(missing_source, dest)
            assert False, "expected OSError"
        except OSError:
            pass

        assert os.path.exists(dest)
        with open(dest, "rb") as f:
            assert f.read() == b"OLD VERSION BYTES"
        assert not os.path.exists(dest + ".bak")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_perform_update_rolls_back_when_new_exe_never_signals_success():
    """Regression test for the auto-update relaunch mechanism. Uses a copy of
    cmd.exe as a stand-in "new version" — it launches fine but never writes
    the startup marker, exactly like a hung/crashed real build would look
    from perform_update()'s point of view. Verifies the rollback path: the
    hung process gets killed, the original file is restored, and the caller
    is told not to exit (still-running old exe should keep the app usable).
    """
    tmp_dir = tempfile.mkdtemp(prefix="dloto_perform_update_test_")
    try:
        source = os.path.join(tmp_dir, "new_app.exe")
        dest = os.path.join(tmp_dir, "app.exe")
        shutil.copy2(r"C:\Windows\System32\cmd.exe", source)
        shutil.copy2(r"C:\Windows\System32\cmd.exe", dest)

        marker = dloto.get_marker_file_path()
        if os.path.exists(marker):
            os.remove(marker)

        success, message = dloto.perform_update(source, dest_exe=dest, timeout_seconds=2)

        assert success is False
        assert "ย้อนกลับ" in message
        assert os.path.exists(dest)  # restored
        assert not os.path.exists(dest + ".bak")  # backup consumed by the rollback
        assert not os.path.exists(dest + ".new")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_perform_update_succeeds_even_when_backup_is_a_running_exe():
    """Regression test for the real-world success path. In production, the
    backup file (dest.bak) IS the currently running old exe — Windows allows
    renaming a running executable's file but locks it against deletion, so
    the old success path's os.remove(backup) raised PermissionError, which
    Tkinter swallowed: no success popup, old process never exited, and its
    main window reappeared alongside the new version.

    Simulated here by launching dest as a live process before updating (same
    lock semantics as the running app), and writing the startup marker from a
    background thread mid-wait (as the freshly launched new version would).
    perform_update must report success; a leftover .bak is acceptable (cleaned
    up by cleanup_stale_backup on a later startup).
    """
    tmp_dir = tempfile.mkdtemp(prefix="dloto_perform_update_test_")
    running_old = None
    try:
        source = os.path.join(tmp_dir, "new_app.exe")
        dest = os.path.join(tmp_dir, "dloto_locktest_app.exe")
        shutil.copy2(r"C:\Windows\System32\cmd.exe", source)
        shutil.copy2(r"C:\Windows\System32\cmd.exe", dest)

        # The old version is running from dest — its image file is now
        # rename-able but not deletable, exactly like the real running app.
        # stdin must be an open pipe (not DEVNULL): cmd.exe exits immediately
        # on EOF, which would silently release the file lock.
        running_old = subprocess.Popen([dest], stdin=subprocess.PIPE,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       creationflags=subprocess.CREATE_NO_WINDOW)

        marker = dloto.get_marker_file_path()
        if os.path.exists(marker):
            os.remove(marker)
        threading.Timer(1.0, dloto.mark_startup_success).start()

        success, message = dloto.perform_update(source, dest_exe=dest, timeout_seconds=10)

        assert success is True, f"expected success, got failure: {message}"
        assert os.path.exists(dest)
        assert not os.path.exists(marker)  # consumed by the success path
    finally:
        if running_old is not None:
            running_old.kill()
            running_old.wait()
        # perform_update's own Popen spawned a second copy of the dest exe;
        # its unique image name keeps this from touching anything else.
        subprocess.run(['taskkill', '/F', '/IM', 'dloto_locktest_app.exe'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_cleanup_stale_backup_removes_leftover_bak():
    tmp_dir = tempfile.mkdtemp(prefix="dloto_cleanup_test_")
    try:
        exe = os.path.join(tmp_dir, "app.exe")
        with open(exe + ".bak", "wb") as f:
            f.write(b"OLD VERSION BYTES")

        dloto.cleanup_stale_backup(exe)
        assert not os.path.exists(exe + ".bak")

        dloto.cleanup_stale_backup(exe)  # no .bak present: must not raise
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_marker_file_path_is_stable()
    test_mark_startup_success_writes_marker()
    test_get_update_exe_path_returns_none_when_missing()
    test_get_update_exe_path_returns_value_when_set()
    test_swap_in_new_exe_replaces_content_and_returns_backup()
    test_swap_in_new_exe_leaves_dest_untouched_if_copy_fails()
    test_perform_update_rolls_back_when_new_exe_never_signals_success()
    test_perform_update_succeeds_even_when_backup_is_a_running_exe()
    test_cleanup_stale_backup_removes_leftover_bak()
    print("All tests passed.")

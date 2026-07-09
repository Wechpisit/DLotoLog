# Auto-Update Relaunch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the "อัพเดทเวอร์ชัน" button in the version-check dialog (`check_and_update()` in `D-Loto.py`) actually replace the running `.exe` with a new one from a DB-configured path and relaunch it, with automatic rollback if the new version fails to start.

**Architecture:** The running app cannot overwrite its own locked `.exe` file, so on click it writes a small batch script to `%TEMP%` and launches it detached, then exits itself. The batch script waits for the old process (by PID) to fully exit, backs up the old `.exe`, copies the new one over it, and relaunches it. The new instance writes a "heartbeat" marker file right after successfully reaching its main window; the batch script watches for that marker with a timeout and rolls back to the backup automatically if it never appears (crash or hang before startup completes).

**Tech Stack:** Python 3.13, tkinter, sqlite3, Windows `cmd.exe` batch scripting, `subprocess`, `tempfile`. No new dependencies.

## Global Constraints

- Edit **only** `D-Loto.py` at the project root — it is the single source of truth (`TestBuildFromCommandLine/D-Loto.py` is a generated copy, synced by `TestBuildFromCommandLine/build.ps1`; never hand-edit it, per `CLAUDE.md`).
- This feature only activates when running as a frozen PyInstaller `.exe` (`getattr(sys, 'frozen', False)`). In dev mode (`python D-Loto.py`), clicking "อัพเดทเวอร์ชัน" keeps today's placeholder behavior (info message + exit) — there is no `.exe` to replace.
- New DB value: reuse the existing `app_info` key-value table (no new table). Add key `'exe_path'` holding the full path to the new `.exe`. This is set manually by an admin via a DB tool — this plan does not build UI for setting it.
- All new Thai-language user-facing text must match the tone/style already used in `check_and_update()` (see `D-Loto.py`'s existing dialog and `design-system.md`).
- Follow the project's existing testing convention: there is no pytest in this repo (`test_loto.py` is a plain script, no test framework installed). New tests are standalone scripts run directly with `python`, using `assert`, following that same convention — but unlike `test_loto.py` (which duplicates code because `D-Loto.py`'s hyphenated filename can't be `import`ed normally), use `importlib.util.spec_from_file_location` to import the real module by path, so tests exercise actual code, not a copy. Importing is safe because `main()` is guarded by `if __name__ == "__main__":` — module-level functions load without starting the app.
- The pure/testable helper functions added in Task 1 go at **module level** (outside `main()`), not nested inside it like the rest of the app. This is a deliberate, narrow exception to the codebase's "everything nested in `main()`" convention (see `CLAUDE.md` → Monolithic Architecture): these functions take no closure state, and pulling them out is what makes Task 1's automated test possible at all.

---

### Task 1: Module-level update-script helpers

**Files:**
- Modify: `D-Loto.py:1-24` (imports) and add new module-level functions right after the imports, before `def main():` (currently `D-Loto.py:26`)
- Test: Create `test_update_script.py` (project root, alongside `test_loto.py`)

**Interfaces:**
- Produces (used by Task 3):
  - `get_marker_file_path() -> str`
  - `mark_startup_success() -> None`
  - `get_update_exe_path(cursor) -> str | None`
  - `build_update_script(pid: int, source_exe: str, dest_exe: str, marker_file: str, timeout_seconds: int = 10) -> str`
  - `write_update_script(pid: int, source_exe: str, dest_exe: str, marker_file: str, timeout_seconds: int = 10) -> str` (returns path to the written `.bat` file)

- [ ] **Step 1: Add `tempfile` to the imports**

`D-Loto.py:1-9` currently reads:

```python
import tkinter as tk
import webbrowser
import os
import sys
import shutil
import datetime
import subprocess
import json
import time
```

Change to:

```python
import tkinter as tk
import webbrowser
import os
import sys
import shutil
import datetime
import subprocess
import json
import time
import tempfile
```

- [ ] **Step 2: Add the module-level helper functions**

Insert this block right after the existing imports (after the `from reportlab...` lines, before `def main():` at `D-Loto.py:26`):

```python
# --- Auto-update helpers (module-level: no closure state needed, and this
# is what makes them testable in isolation — see test_update_script.py) ---

def get_marker_file_path():
    """Fixed path both the old and new .exe write to/watch, so a relaunch can detect success."""
    return os.path.join(tempfile.gettempdir(), "dloto_started.flag")


def mark_startup_success():
    """Call once the app has reached its main window with no startup errors."""
    with open(get_marker_file_path(), "w") as f:
        f.write("ok")


def get_update_exe_path(cursor):
    """Reads the admin-configured path to the new .exe from app_info, or None if unset."""
    cursor.execute("SELECT value FROM app_info WHERE key = 'exe_path'")
    result = cursor.fetchone()
    return result[0] if result else None


UPDATE_SCRIPT_TEMPLATE = """@echo off
setlocal

:WAITLOOP
tasklist /FI "PID eq {pid}" 2>NUL | findstr /I "{pid}" >NUL
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto WAITLOOP
)

if exist "{marker}" del /f /q "{marker}"
if exist "{backup}" del /f /q "{backup}"
move /y "{dest}" "{backup}"
copy /y "{source}" "{dest}"
start "" "{dest}"

set WAITED=0
:CHECKLOOP
if exist "{marker}" goto SUCCESS
timeout /t 1 /nobreak >nul
set /a WAITED+=1
if %WAITED% GEQ {timeout_seconds} goto ROLLBACK
goto CHECKLOOP

:SUCCESS
del /f /q "{backup}" >nul 2>nul
goto CLEANUP

:ROLLBACK
taskkill /F /IM "{exe_name}" >nul 2>nul
move /y "{backup}" "{dest}"
start "" "{dest}"

:CLEANUP
if exist "{marker}" del /f /q "{marker}"
(goto) 2>nul & del "%~f0"
"""


def build_update_script(pid, source_exe, dest_exe, marker_file, timeout_seconds=10):
    """Pure function: renders the batch script text. No file I/O — easy to unit test."""
    backup_exe = dest_exe + ".bak"
    exe_name = os.path.basename(dest_exe)
    return UPDATE_SCRIPT_TEMPLATE.format(
        pid=pid,
        source=source_exe,
        dest=dest_exe,
        backup=backup_exe,
        marker=marker_file,
        timeout_seconds=timeout_seconds,
        exe_name=exe_name,
    )


def write_update_script(pid, source_exe, dest_exe, marker_file, timeout_seconds=10):
    """Writes the rendered script to %TEMP%\\dloto_update.bat and returns its path."""
    script_text = build_update_script(pid, source_exe, dest_exe, marker_file, timeout_seconds)
    script_path = os.path.join(tempfile.gettempdir(), "dloto_update.bat")
    with open(script_path, "w") as f:
        f.write(script_text)
    return script_path
```

- [ ] **Step 3: Write the test script**

Create `test_update_script.py`:

```python
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
        source_exe="L:/update/D-Loto.exe",
        dest_exe="C:/apps/D-Loto.exe",
        marker_file="C:/temp/dloto_started.flag",
        timeout_seconds=10,
    )
    assert "1234" in script
    assert '"L:/update/D-Loto.exe"' in script
    assert '"C:/apps/D-Loto.exe"' in script
    assert '"C:/apps/D-Loto.exe.bak"' in script
    assert '"C:/temp/dloto_started.flag"' in script
    assert "WAITED GEQ 10" in script
    assert "D-Loto.exe" in script  # exe_name used in taskkill


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
    test_write_update_script_creates_file()
    print("All tests passed.")
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `python test_update_script.py`
Expected: `AttributeError` (or import error) — `get_marker_file_path` etc. don't exist yet if Step 2 wasn't done, or the test simply hasn't been run before the code exists. If you did Steps 1-2 first, skip to Step 5 — this ordering note exists because Step 2's code and Step 3's test were written together above; if strictly following red-green, write Step 3 before Step 2 and confirm the `AttributeError` here first.

- [ ] **Step 5: Run the test to verify it passes**

Run: `python test_update_script.py`
Expected:
```
All tests passed.
```

- [ ] **Step 6: Compile-check the main file**

Run: `python -m py_compile D-Loto.py`
Expected: no output (success)

- [ ] **Step 7: Commit**

```bash
git add D-Loto.py test_update_script.py
git commit -m "Add module-level auto-update helpers (marker file, exe_path lookup, batch script builder)"
```

---

### Task 2: Write startup marker after successful launch

**Files:**
- Modify: `D-Loto.py` — the line `root.deiconify()  # Show root window again once update check passes` (currently right after `check_and_update()` is called, near the top of `main()`)

**Interfaces:**
- Consumes: `mark_startup_success()` from Task 1

- [ ] **Step 1: Call `mark_startup_success()` right after `root.deiconify()`**

Find:

```python
    check_and_update()
    root.deiconify()  # Show root window again once update check passes
```

Replace with:

```python
    check_and_update()
    root.deiconify()  # Show root window again once update check passes
    mark_startup_success()  # Heartbeat file: signals a relaunching update script that startup succeeded
```

- [ ] **Step 2: Compile-check**

Run: `python -m py_compile D-Loto.py`
Expected: no output (success)

- [ ] **Step 3: Manual verification**

Run: `python D-Loto.py`, let the main window appear, then check the marker file exists:

```bash
python -c "import tempfile, os; p = os.path.join(tempfile.gettempdir(), 'dloto_started.flag'); print(os.path.exists(p))"
```

Expected: `True`

- [ ] **Step 4: Commit**

```bash
git add D-Loto.py
git commit -m "Write startup-success marker file after main window is shown"
```

---

### Task 3: Wire real update logic into the "อัพเดทเวอร์ชัน" button

**Files:**
- Modify: `D-Loto.py` — the `on_update()` function inside `check_and_update()` (currently a placeholder that just shows an info message and exits)

**Interfaces:**
- Consumes: `get_update_exe_path`, `write_update_script`, `get_marker_file_path` from Task 1

- [ ] **Step 1: Replace the placeholder `on_update()`**

Find (inside `check_and_update()`, in the version-check dialog block):

```python
            def on_update():
                # TODO (Step 2): copy new exe from update folder and relaunch automatically
                messagebox.showinfo(
                    "Update",
                    "ฟีเจอร์อัพเดทอัตโนมัติจะถูกเพิ่มในขั้นตอนถัดไป\nโปรแกรมจะปิดตัวลงตอนนี้"
                )
                dialog.destroy()
                root.destroy()
                sys.exit()
```

Replace with:

```python
            def on_update():
                if not getattr(sys, 'frozen', False):
                    messagebox.showinfo(
                        "Update",
                        "ฟีเจอร์อัพเดทอัตโนมัติใช้ได้เฉพาะเมื่อรันจากโปรแกรม .exe เท่านั้น\n"
                        "โปรแกรมจะปิดตัวลงตอนนี้"
                    )
                    dialog.destroy()
                    root.destroy()
                    sys.exit()
                    return

                exe_path = get_update_exe_path(c)
                if not exe_path or not os.path.exists(exe_path):
                    messagebox.showerror(
                        "Update Failed",
                        f"ไม่พบไฟล์อัพเดทที่ {exe_path or '(ยังไม่ได้ตั้งค่า exe_path ใน app_info)'}\n"
                        f"กรุณาติดต่อผู้ดูแลระบบ"
                    )
                    dialog.destroy()
                    return

                dest_exe = sys.executable
                marker_file = get_marker_file_path()
                if os.path.exists(marker_file):
                    os.remove(marker_file)

                script_path = write_update_script(os.getpid(), exe_path, dest_exe, marker_file)
                subprocess.Popen(
                    ['cmd', '/c', script_path],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )

                dialog.destroy()
                root.destroy()
                sys.exit()
```

- [ ] **Step 2: Compile-check**

Run: `python -m py_compile D-Loto.py`
Expected: no output (success)

- [ ] **Step 3: Manual verification — dev mode click (not frozen)**

1. Set `app_info.version` to `'1.0.4'` in `loto_data.db` (temporarily).
2. Run `python D-Loto.py`.
3. Click "อัพเดทเวอร์ชัน".
4. Expected: message "ฟีเจอร์อัพเดทอัตโนมัติใช้ได้เฉพาะเมื่อรันจากโปรแกรม .exe เท่านั้น..." then the app closes. No file operations happen.
5. Set `app_info.version` back to `'1.0.3'`.

- [ ] **Step 4: Manual verification — missing exe_path**

1. Confirm `app_info` has no `exe_path` row: `SELECT * FROM app_info WHERE key = 'exe_path'` returns nothing.
2. Build the app into an `.exe` using `powershell -File "TestBuildFromCommandLine/build.ps1"`.
3. Set `app_info.version` to `'1.0.4'`, run the built `TestBuildFromCommandLine/dist/D-Loto.exe`.
4. Click "อัพเดทเวอร์ชัน".
5. Expected: error box "ไม่พบไฟล์อัพเดทที่ (ยังไม่ได้ตั้งค่า exe_path ใน app_info)...". Dialog closes, **main app window appears and works normally** (not force-closed).
6. Set `app_info.version` back to `'1.0.3'`.

- [ ] **Step 5: Manual verification — full successful update + relaunch**

1. Build once with the current `rev` (e.g. `1.0.3`) — this becomes the "old" exe, e.g. copy `dist/D-Loto.exe` to a test folder as `C:\dtest\D-Loto.exe`.
2. Bump `rev = '1.0.4'` in `D-Loto.py` (root), rebuild via `build.ps1` — this becomes the "new" exe. Copy `dist/D-Loto.exe` to `C:\dtest\update\D-Loto_new.exe` (rename during copy so it doesn't collide with the old one on disk).
3. Revert `rev` back to `1.0.3` in `D-Loto.py` and rebuild again, so the root/build-dir source matches what's actually deployed as "current" (avoids leaving the repo on a bumped version).
4. In `loto_data.db`: set `app_info.version = '1.0.4'`, set `app_info.exe_path = 'C:\dtest\update\D-Loto_new.exe'`.
5. Run `C:\dtest\D-Loto.exe` (the "old" one). The version dialog should appear.
6. Click "อัพเดทเวอร์ชัน".
7. Expected: app closes, a few seconds pass (batch script waiting for the process to exit + running), then `C:\dtest\D-Loto.exe` **relaunches automatically** running the new version (check by looking at `app_info.version` no longer being newer, or by a visible change if one was made) and `C:\dtest\D-Loto.exe.bak` no longer exists (cleaned up on success).
8. Set `app_info.version` back to `'1.0.3'` when done testing.

- [ ] **Step 6: Manual verification — rollback on failed update**

1. Repeat Step 5's setup, but at `app_info.exe_path` point to a **corrupt/non-functional exe** (e.g. copy `cmd.exe` and rename it `D-Loto_broken.exe` — it will "start" but never write the marker file since it isn't the real app).
2. Run the old `D-Loto.exe`, click "อัพเดทเวอร์ชัน".
3. Expected: after ~10 seconds, the script detects no marker file appeared, kills the broken process, restores `D-Loto.exe.bak` back to `D-Loto.exe`, and relaunches the **original working exe** automatically. The user ends up back in a working app without manual intervention.
4. Set `app_info.version` back to `'1.0.3'` when done testing.

- [ ] **Step 7: Commit**

```bash
git add D-Loto.py
git commit -m "Implement real auto-copy/relaunch logic for the update-version button"
```

---

### Task 4: Document the new `app_info.exe_path` key

**Files:**
- Modify: `CLAUDE.md` (Auto-Update Check section)

**Interfaces:** none (docs only)

- [ ] **Step 1: Update the Auto-Update Check section**

In `CLAUDE.md`, find the `### Auto-Update Check` section (documents `check_and_update()`) and add a bullet after the existing ones describing the dialog:

```markdown
- The "อัพเดทเวอร์ชัน" button only works when running as a frozen `.exe` (`getattr(sys, 'frozen', False)`); in dev mode it just shows a message and exits, same as before
- Reads the new exe's location from `app_info` key `'exe_path'` (full path, e.g. `L:/4.4LO.T1/___LOTO___/D-Loto.exe`) — **set this manually in the DB** alongside bumping `version` when rolling out a new build. If unset or the file doesn't exist, the button shows an error and leaves the current app untouched.
- On click, writes a batch script to `%TEMP%\dloto_update.bat` that: waits for this process to exit (by PID), backs up the current `.exe` to `.exe.bak`, copies the new one over it, and relaunches it
- The relaunched app calls `mark_startup_success()` right after `root.deiconify()`, writing `%TEMP%\dloto_started.flag`. The batch script watches for that marker for 10 seconds; if it never appears (crash/hang before startup completes), it automatically kills the new process, restores `.exe.bak`, and relaunches the previous working version — no manual user action needed
- Core logic lives in module-level functions (`get_marker_file_path`, `mark_startup_success`, `get_update_exe_path`, `build_update_script`, `write_update_script`) defined just before `def main():` — see `test_update_script.py` for their tests
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "Document the exe_path auto-update mechanism in CLAUDE.md"
```

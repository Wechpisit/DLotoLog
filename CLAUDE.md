# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Collaboration Rules

- **Always use `AskUserQuestion` tool when any requirement is unclear before implementing.** Do not assume or proceed with guesses. Confirm first, implement after.

## Skills to Invoke

Skills available depend on the user's installed Claude Code plugins and may change over time — treat this list as guidance current as of 2026-07, not a guarantee. When starting work in this repo, check which of these apply before acting.

**Before any feature/design work (mandatory per `superpowers:using-superpowers`)**:
- `superpowers:brainstorming` — before creating features, adding functionality, or changing behavior (e.g. designing the auto-update dialog). Explores intent/requirements before implementation.
- `grill-me` — for **high-risk, hard-to-reverse changes** (e.g. Step 2 auto-update: overwriting the running .exe, process relaunch logic). Interviews until the design is fully resolved. Use before implementing, not after.
- `grill-with-docs` — same as `grill-me` but also keeps CONTEXT.md/ADRs in sync as decisions are made. Prefer this over `grill-me` once this repo has docs like that to update.
- For low-risk/additive UI tweaks (e.g. popup wording, button layout), a quick `AskUserQuestion` is enough — no need for `grill-me`.

**Debugging (mandatory before proposing any fix)**:
- `superpowers:systematic-debugging` — any bug report, hang, crash, or unexpected behavior (used to find the `root.withdraw()`/`deiconify()` root cause). Do not guess-and-patch.
- `diagnose` — alternative disciplined reproduce→fix loop, usable interchangeably with the above.

**Implementation process**:
- `superpowers:test-driven-development` / `tdd` — before writing implementation code for a feature or bugfix, when a test harness makes sense.
- `superpowers:writing-plans` → `superpowers:executing-plans` — for multi-step tasks with a clear spec, when the user wants a reviewable plan before code changes (e.g. the full auto-update Step 2 rollout).
- `andrej-karpathy-skills:karpathy-guidelines` — apply throughout: minimum code for the ask, surgical edits only, state assumptions, define verifiable success criteria. (Already the default working style in this repo.)

**Before claiming work done**:
- `superpowers:verification-before-completion` — run and confirm actual output before saying a fix/feature works. Don't just claim success.
- `verify` — drive the change end-to-end in the running app (not just read code) before considering it complete. Relevant here since this is a Tkinter desktop app with no automated UI tests.

**Review**:
- `code-review` / `simplify` — after a change is implemented, to catch correctness bugs or simplification opportunities.
- `security-review` — if a change touches file paths, network calls, or file overwrite logic (e.g. Step 2's exe self-replace) — check for path traversal / unsafe overwrite issues.

**UI work specifically**:
- `ui-ux-pro-max` — when designing or reviewing GUI elements (dialogs, buttons, layout, color/theme consistency) — used to theme the version-check popup to match the app's `#dcdad5` / Tahoma look.

**Running/testing the app**:
- `run` — to launch and interact with `D-Loto.py` directly instead of just reading code, when asked to "run" or "test" a change live.

**Documentation**:
- `init` — only if CLAUDE.md needs a full regeneration from scratch (not for incremental updates — those are done directly).

**Not typically relevant to this repo** (Windows desktop Tkinter app, no web/cloud/CI): `claude-in-chrome`, `dataviz`, `to-issues`, `to-prd`, `triage`, `schedule`, `loop`, `claude-api` (unless the app ever integrates an LLM), `fewer-permission-prompts`, `keybindings-help`, `update-config`.

## Project Overview

D-LOTO is a Lock Out, Tag Out (LOTO) management system for PTT LNG operations. It's a Windows desktop application built with Python/Tkinter that manages work requests, lock details, and approval workflows using a SQLite database stored on a network drive.

**Current version**: 1.0.3 (defined in D-Loto.py:28)

**Platform**: Windows only (uses Windows-specific DPI awareness APIs)

## Dependencies

Required Python packages:
- **tkinter**: GUI framework (usually included with Python)
- **Pillow (PIL)**: Image handling for icons and buttons
- **reportlab**: PDF generation for LOTO reports
- **sqlite3**: Database operations (included with Python)
- **ctypes**: Windows DPI awareness (included with Python)

Standard library: `os`, `sys`, `shutil`, `datetime`, `subprocess`, `json`, `time`, `webbrowser`

## Quick Reference

**Running the application**:
```bash
python D-Loto.py
```

**Building executable**:
```bash
cd TestBuildFromCommandLine
pyinstaller D-Loto.spec
```

**Running tests**:
```bash
python test_loto.py
```

**Key files to modify**:
- Version number: D-Loto.py:28
- Environment switch (`dev`/`prod`): D-Loto.py:33
- Employee lists: D-Loto.py:429-490 (`list_setup()` function)
- Database path: config.json or D-Loto.py:50-55 (ENV-based directory selection)
- Build configuration: TestBuildFromCommandLine/D-Loto.spec

## Build and Distribution

### Building the Executable

The application is packaged using PyInstaller. Build from the `TestBuildFromCommandLine` directory:

```bash
cd "TestBuildFromCommandLine"
pyinstaller --onefile --windowed D-Loto.py ^
--add-data "C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/1.LNG Project/2024/2.LOTO Project/TestBuildFromCommandLine/*.png;." ^
--add-data "C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/1.LNG Project/2024/2.LOTO Project/TestBuildFromCommandLine/*.ico;." ^
--add-data "config.json;." ^
--icon "C:/Users/wechp/OneDrive - PTT GROUP/PTTLNG/3.Project/1.LNG Project/2024/2.LOTO Project/TestBuildFromCommandLine/IconProgram1.ico"
```

The executable will be generated in `dist/D-Loto.exe`.

Alternatively, use the spec file:
```bash
pyinstaller D-Loto.spec
```

### Build Configuration

- **config.json**: Contains the database path configuration. Must be bundled with the executable.
- **Resource files**: PNG icons and ICO files must be included via `--add-data`
- **PyInstaller settings**: `--windowed` for GUI app (no console), `--onefile` for single executable

## Architecture

### Main Application Entry Point

The application uses a `main()` function wrapper (D-Loto.py:26) to enable proper error handling. All application logic is contained within this function.

### Database Schema

Three main SQLite tables with status-based workflow:

1. **loto_new**: All LOTO entries (source of truth)
   - Fields: ID, log_id, new_work_title, new_incharge_dept, new_owner, new_telephone, new_area, new_equipment, new_lock_date, new_loto_no, new_loto_keys, new_pid_pdf, new_override, new_remark, new_prepare, new_verify, new_approve, status
   - Status values: 'Waiting' → 'Active'/'Onsite' → 'Completed'/'Cancel'
   - Contains approval chain fields: new_prepare, new_verify, new_approve

2. **loto_overview**: Active LOTO entries (view table)
   - Fields: ID, loto_no, work_title, owner, lock_date, status
   - Auto-populated from loto_new where status IN ('Active', 'Onsite')
   - Represents currently active lockout/tagout operations

3. **loto_completed**: Completed LOTO entries (archive table)
   - Fields: ID, loto_no, work_title, owner, lock_date, status
   - Auto-populated from loto_new where status IN ('Completed', 'Cancel')
   - Historical record of finished operations

**Status Workflow**:
- New entries inserted to loto_new with status='Waiting' (D-Loto.py:153)
- Upon approval → status changes to 'Active' or 'Onsite' → auto-transferred to loto_overview
- Upon completion → status changes to 'Completed' or 'Cancel' → auto-transferred to loto_completed

### Database Connection

- Database location configured in `config.json`, but currently overridden by an ENV-based directory (D-Loto.py:33, 50-55) rather than by `config.json` directly
- Production path: `L:/4.4LO.T1/06-Operational_and_Record/6.56 LOTO/loto_data.db`
- **ENV switch** (D-Loto.py:33): `ENV = 'dev'` or `'prod'`
  - `dev`: uses a local OneDrive project folder for the DB, skips the intranet check (D-Loto.py:50-51, 77)
  - `prod`: uses the `L:` network drive path and requires a successful intranet check before connecting (D-Loto.py:52-53, 77)
  - Window title shows `[DEV MODE]` suffix when `ENV != 'prod'` (D-Loto.py:247)
  - **Must be set to `'prod'` before building the production executable**
- **Intranet check** (`check_intranet_connection()`, D-Loto.py:57-72): pings server `10.232.104.130`; only enforced when `ENV == 'prod'`
- Connection includes error handling for network drive availability (`connect_to_database()`, D-Loto.py:75-102)
  - Shows "Intranet Connection Error" if the ping fails in prod mode
  - Shows "Network Error" if the DB file itself is not accessible
- Uses `resource_path()` helper for PyInstaller compatibility with bundled resources

### Auto-Update Check

- An `app_info` table (D-Loto.py:238-243) stores a `version` key in the SQLite DB, seeded with the running app's `rev` on first launch (`INSERT OR IGNORE`)
- On startup, `check_and_update()` (D-Loto.py:252-289) compares the DB-stored version against the local `rev`
  - If the DB version is newer, shows a warning dialog telling the user to copy the new `.exe` from an update folder, then exits
  - Update folder: `update/` (dev) or `L:/4.4LO.T1/___LOTO___` (prod, D-Loto.py:271) — note `TestBuildFromCommandLine/D-Loto.py` uses a different prod path (`.../6.56 LOTO/update/`); keep these in sync when editing
- To roll out a new version: bump `rev`, update the `app_info.version` row in the shared DB (e.g. via a manual `UPDATE`), and drop the new `.exe` in the update folder — existing clients will detect the mismatch and prompt users to update

### Key Components

**GUI Framework**: Tkinter with custom widget classes
- Multiple custom input field classes (dropdown, date, telephone, remark, pdf)
- High DPI awareness enabled via `ctypes.windll.shcore.SetProcessDpiAwareness(1)`
- Scaling factor calculated based on screen DPI (D-Loto.py:205)

**Business Data** (D-Loto.py:429-490):
- Hardcoded dropdown lists defined in `list_setup()` function:
  - `incharge_list`: Departments (MT.Mech, MT.Ins, MT.Elec, ED.*, Project, LO., etc.)
  - `owner_list`: 200+ employee names (full employee roster)
  - `sectionmgr_list`: Section managers (6 names)
  - `lomember_list`: LO (Lock Out) team members (~35 names)
  - `area_list`: Work areas (HP Pump, BOG Compressor, Jetty, etc.)
- These lists are critical for data validation and dropdown population
- Updating employee names or departments requires modifying `list_setup()`

**Data Flow**:
1. New work entries → `loto_new` table (via `insert_new_loto()`)
2. Upon approval → transferred to `loto_overview` (via `transfer_data_overview()`)
3. Upon completion → moved to `loto_completed` (via `transfer_data_completed()`)

**PDF Handling**: Application supports attaching and viewing PDF documents for LOTO procedures

**File Management**:
- Creates folder structure for storing LOTO-related documents
- Copies and renames files during update workflows
- Uses `create_folder_copy_file` and `copy_rename_file_for_update_widget` classes

### Testing

Test file: `test_loto.py` - Contains unit tests for database connection functionality

## Development Notes

### Version Management

To update the application version:
1. Modify `rev = '1.0.3'` in D-Loto.py:28
2. Rebuild the executable with PyInstaller
3. Version is displayed in the application UI

### Resource Path Handling

The `resource_path()` function (D-Loto.py:31) handles both development and PyInstaller bundled environments:
- In development: Returns absolute path from current directory
- In PyInstaller bundle: Returns path from temporary `_MEIPASS` folder
- **Critical**: Always use `resource_path()` for accessing config.json and image files

### Work Title String Handling

Work titles are stripped of trailing whitespace before database insertion (commit 613ff0f) to prevent data inconsistencies.

### Common Operations

**Refresh data display**:
- `refresh_treeview()` - Updates all three table views (overview, pending, completed)
- Called after any data modification to sync UI with database

**Three-step approval workflow**:
1. **Prepare**: Initial preparation by requestor
2. **Verify**: Verification by supervisor
3. **Approve**: Final approval by section manager
4. Status changes from 'Waiting' → 'Active'/'Onsite'
5. Auto-transfer to `loto_overview` via `transfer_data_overview()`

**User interactions**:
- Double-click on rows triggers detail views:
  - `on_row_double_click_overview()` - View active LOTO details
  - `on_row_double_click_pending()` - Edit/approve pending items
  - `on_row_double_click_completed()` - View completed items

**Database operations**:
- INSERT: `insert_new_loto()` (new entries), `insert_data()` (overview)
- READ: `view_data()`, `view_data_new()`, `view_data_completed()`
- TRANSFER: `transfer_data_overview()` (to active), `transfer_data_completed()` (to archive)
- UPDATE: Directly via SQL UPDATE statements on `loto_new` table

### Network Dependencies

The application requires access to PTT LNG network drive (L:) or server 10.232.104.130. Connection failures show appropriate error messages to users. The intranet ping check only runs in `ENV == 'prod'` — in `'dev'` mode the app connects to a local DB copy and skips this check entirely.

### UI Considerations

**Application Structure**:
- Three-tab interface using `ttk.Notebook`:
  1. Overview tab - Active LOTO operations
  2. Pending tab - Awaiting approval
  3. Completed tab - Archived operations
- Tab focus control via `set_focus_on_tab(index)`

**Styling and Theming**:
- Custom ttk styles: `Custom1.TButton`, `Custom2.TButton`, `Custom3.TButton`
- Custom notebook tab style with blue highlight on selection
- Font setup via `font_setup()` and `configure_widget_style()`
- DPI-aware scaling for all widgets (padding, fonts, buttons)

**Custom Widget Classes**:
- `input_field_dropdown` / `input_field_dropdown_linebreak` - Dropdown selectors
- `input_field_date` - Date picker widgets
- `input_field_telephone` - Phone number input
- `input_field_remark` / `input_field_remark_click_toplevel` - Multi-line remark fields
- `input_field_pdf` / `pdf_show` - PDF attachment and viewing
- All widgets auto-scale based on screen DPI

**Window Management**:
- Window centering via `center_windows(w, h)`
- Icon setting via `set_window_icon(root)`
- Focus management with Tab key navigation (`focus_next_widget`)
- Message boxes via `show_message(title, message)`

## Critical Patterns and Gotchas

### Database Path Configuration
- The DB path is chosen by the `ENV` switch (D-Loto.py:33), not directly from `config.json` — `config.json`'s `database_path` is loaded but then overwritten by the ENV-based `directory` (D-Loto.py:44-55)
- **Before building for production**: set `ENV = 'prod'` in D-Loto.py:33, otherwise the exe will still point at the dev OneDrive path and skip the intranet check
- Always verify `ENV` is correct before building the executable

### Monolithic Architecture
- All application code is in a single `main()` function
- All classes and functions are nested inside `main()`
- Variables and state are shared through function closure
- Makes unit testing challenging but simplifies deployment

### Data Synchronization
- `loto_new` is the master table - never delete data directly from it
- `loto_overview` and `loto_completed` are derived views
- Always call `refresh_treeview()` after database modifications
- Transfer functions prevent duplicates using NOT IN clauses

### File Path Considerations
- PyInstaller paths use `;` as separator on Windows, not `:`
- All resource files must be explicitly listed in `--add-data`
- Icon file must be .ico format for Windows executable
- PDF and image files stored on network drive, not bundled

## File Organization

- `D-Loto.py`: Main application (production version in root directory)
- `TestBuildFromCommandLine/D-Loto.py`: Build directory version for creating executable
- `TestBuildFromCommandLine/config.json`: Production database configuration
- `DB_loto.py`: Standalone database operations module (legacy)
- `combined_loto.py`, `optimized_combined_loto.py`: Earlier combined versions (legacy)
- `loto.py`, `test.py`: Development/testing files
- `test_loto.py`: Unit tests for database connection
- `ImproveFromChatGPT.py`: Experimental improvements
- `*.spec`: PyInstaller specification files for build configuration
- `update/`: Holds the latest `D-Loto.exe` for the auto-update flow to point users to (dev-mode location)
- `DatabaseLocation/`: Notes on where the production DB lives on Drive L:

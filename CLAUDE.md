# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
- Employee lists: D-Loto.py:341-400 (`list_setup()` function)
- Database path: config.json or D-Loto.py:44-47
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

- Database location configured in `config.json`
- Production path: `L:/4.4LO.T1/06-Operational_and_Record/6.56 LOTO/loto_data.db`
- **Development override** (D-Loto.py:44-47): Hardcoded path overrides config.json during development
- Connection includes error handling for network drive availability (D-Loto.py:50-63)
  - Shows "Network Error" if L: drive is not accessible
  - References server: 10.232.104.130
- Uses `resource_path()` helper for PyInstaller compatibility with bundled resources

### Key Components

**GUI Framework**: Tkinter with custom widget classes
- Multiple custom input field classes (dropdown, date, telephone, remark, pdf)
- High DPI awareness enabled via `ctypes.windll.shcore.SetProcessDpiAwareness(1)`
- Scaling factor calculated based on screen DPI (D-Loto.py:205)

**Business Data** (D-Loto.py:341-400):
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

The application requires access to PTT LNG network drive (L:) or server 10.232.104.130. Connection failures show appropriate error messages to users.

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
- **Development**: Hardcoded path in D-Loto.py:44-47 overrides config.json
- **Production**: Comment out the hardcoded path, rely on config.json
- Always verify which path is active before building executable

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

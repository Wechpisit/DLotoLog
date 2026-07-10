# Long Work Title Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the PDF export table overflowing when a Work Description is long (word-wrap instead of truncating — this is a safety document, nothing gets hidden), and add a hover tooltip to the Tkinter "Work Description" column (all three tabs) that shows the full text only when the native ellipsis truncation actually kicked in.

**Architecture:** `capture_table_to_pdf` moves from a `main()`-nested function to a module-level, duck-typed-on-`treeview` function (it has zero dependency on `main()`'s closure state), following the auto-update feature's precedent of module-level/testable helpers — this lets it be tested with a small fake Treeview instead of a real Tkinter one. A new module-level `is_text_truncated(text, font, column_width)` pure function is the testable core of the tooltip decision logic; the actual tooltip widget (a borderless `Toplevel`) stays nested in `main()` since it needs a live Treeview and event bindings, wired up once per tab via a single reusable `attach_truncation_tooltip()` helper.

**Tech Stack:** Python 3.13, Tkinter (existing), reportlab (existing) — no new dependencies. Tests are plain `assert`-based files run via `python test_x.py`, matching this repo's existing convention (no pytest).

## Global Constraints

- No truncation/ellipsis for the PDF — full text must always be present (word-wrapped), per the design decision that this is a LOTO safety record. See spec §Decision.
- PDF fix affects the Overview tab only — it's the only tab with a "PRINT" button; no PDF export is being added to Pending/Completed. See spec §Scope.
- Tooltip goes on all three tabs' "Work Description" column: `loto_datalist` (Overview), `loto_datalist_p` (Pending), `loto_datalist_c` (Completed).
- Tooltip must only appear when the cell's text actually overflows the column width — never on short text that already fits. See spec §Tooltip fix.
- Cell text passed to `reportlab.Paragraph` must be escaped (`xml.sax.saxutils.escape`) — `Paragraph` parses its input as markup, so a work title containing `&`/`<`/`>` would otherwise break PDF generation.
- Only edit the root `D-Loto.py` — `TestBuildFromCommandLine/D-Loto.py` is a generated copy, synced by `build.ps1`, never hand-edited.
- New logic that doesn't need Tkinter GUI state must be module-level (not nested in `main()`), per this repo's established testability convention.

---

### Task 1: Move `capture_table_to_pdf` to module level, fix PDF overflow via word-wrap

**Files:**
- Modify: `D-Loto.py` (remove the `main()`-nested `capture_table_to_pdf`, add a module-level replacement; add 3 new imports)
- Test: `test_pdf_export.py`

**Interfaces:**
- Produces: module-level `capture_table_to_pdf(treeview, file_name)` — same signature as before, still called by `save_table_as_pdf` (which stays nested in `main()`, unchanged call site) via ordinary module-level name resolution (no `nonlocal`/import needed for a nested function to call a module-level one).

- [ ] **Step 1: Write the failing tests**

```python
# test_pdf_export.py
import importlib.util
import os
import shutil
import tempfile


def _load_dloto_module():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "D-Loto.py")
    spec = importlib.util.spec_from_file_location("dloto_module_under_test_pdf", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dloto = _load_dloto_module()


class _FakeTreeview:
    """Duck-typed stand-in for ttk.Treeview — capture_table_to_pdf only
    calls cget('columns'), get_children(), item(child, 'values'), and
    column(col, 'width')."""
    def __init__(self, columns, rows, col_widths):
        self._columns = columns
        self._rows = rows
        self._col_widths = dict(zip(columns, col_widths))

    def cget(self, key):
        assert key == "columns"
        return self._columns

    def get_children(self):
        return list(range(len(self._rows)))

    def item(self, child, key):
        assert key == "values"
        return self._rows[child]

    def column(self, col, key):
        assert key == "width"
        return self._col_widths[col]


def test_capture_table_to_pdf_handles_special_characters_and_long_text():
    tmp_dir = tempfile.mkdtemp(prefix="dloto_pdf_test_")
    try:
        columns = ("LOTO No.", "Work Description", "Status")
        col_widths = [90, 440, 95]
        long_title = "Isolate Valve A & B <manual override> for overhaul " * 5
        rows = [("1", long_title, "Active")]
        fake = _FakeTreeview(columns, rows, col_widths)

        out_path = os.path.join(tmp_dir, "test.pdf")
        dloto.capture_table_to_pdf(fake, out_path)

        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_capture_table_to_pdf_handles_empty_table():
    tmp_dir = tempfile.mkdtemp(prefix="dloto_pdf_test_")
    try:
        columns = ("LOTO No.", "Work Description", "Status")
        col_widths = [90, 440, 95]
        fake = _FakeTreeview(columns, [], col_widths)

        out_path = os.path.join(tmp_dir, "empty.pdf")
        dloto.capture_table_to_pdf(fake, out_path)

        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_capture_table_to_pdf_handles_special_characters_and_long_text()
    test_capture_table_to_pdf_handles_empty_table()
    print("All tests passed.")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -3.13 test_pdf_export.py`
Expected: `AttributeError: module 'dloto_module_under_test_pdf' has no attribute 'capture_table_to_pdf'` — the function still only exists nested inside `main()` at this point, not as a module attribute.

- [ ] **Step 3: Add the 3 new imports**

At the top of `D-Loto.py`, find:
```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
```

Replace with:
```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from xml.sax.saxutils import escape as xml_escape
```

- [ ] **Step 4: Remove the old nested `capture_table_to_pdf` from `main()`**

Find this whole block inside `main()` (currently right before `def save_table_as_pdf`) and delete it entirely:
```python
    def capture_table_to_pdf(treeview, file_name):
        # Set up the PDF document
        pdf = SimpleDocTemplate(file_name, pagesize=A4)
        elements = []
        
        # Table header
        data = [treeview.cget("columns")]
        
        # Add all rows of the Treeview to the data list
        for child in treeview.get_children():
            row = [treeview.item(child, "values")[i] for i in range(len(data[0]))]
            data.append(row)
        
        # Calculate the total number of rows (excluding the header)
        total_rows = len(treeview.get_children())

        # Create the table in the PDF
        table = Table(data)
        
        # Define table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        table.setStyle(style)
        
        # Get the current date
        current_date = datetime.now().strftime("%d/%m/%Y")

        # Add the table to elements and build the PDF
        elements.append(table)
        # Add total rows count text
        styles = getSampleStyleSheet()
        total_rows_text = Paragraph(
            f"Total lock box is: {total_rows} <font size=8 color=grey>    (as of: {current_date})</font>", styles['Normal']
        )
        elements.append(total_rows_text)
        
        # Build the PDF
        pdf.build(elements)
        
        print(f"PDF saved successfully as {file_name}")

    def save_table_as_pdf(treeview):
```

Replace with just:
```python
    def save_table_as_pdf(treeview):
```

(i.e. delete everything from `def capture_table_to_pdf(treeview, file_name):` down to the blank line right before `def save_table_as_pdf(treeview):`, keeping `def save_table_as_pdf(treeview):` itself).

- [ ] **Step 5: Add the module-level replacement**

Find (module level, near the end of `perform_update`):
```python
    kill_process_tree(new_proc.pid)
    os.replace(backup_exe, dest_exe)
    return False, "เวอร์ชันใหม่เปิดไม่สำเร็จ ระบบได้ย้อนกลับเป็นเวอร์ชันเดิมให้อัตโนมัติแล้ว"


def main():
```

Replace with:
```python
    kill_process_tree(new_proc.pid)
    os.replace(backup_exe, dest_exe)
    return False, "เวอร์ชันใหม่เปิดไม่สำเร็จ ระบบได้ย้อนกลับเป็นเวอร์ชันเดิมให้อัตโนมัติแล้ว"


# --- PDF export (module-level: testable, no main() closure state needed —
# see test_pdf_export.py) ---

def capture_table_to_pdf(treeview, file_name):
    """Exports a Treeview's rows to a PDF, wrapping long cell text instead of
    letting it force the table wider than the printable page. Duck-typed on
    `treeview` (cget/get_children/item/column) so it can be tested with a
    fake object instead of a real Tkinter widget."""
    pdf = SimpleDocTemplate(
        file_name, pagesize=A4,
        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36,
    )
    elements = []

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        'LotoPdfHeader', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=10, leading=12, textColor=colors.whitesmoke, alignment=TA_CENTER,
    )
    cell_style = ParagraphStyle(
        'LotoPdfCell', parent=styles['Normal'], fontSize=9, leading=11, alignment=TA_LEFT,
    )

    columns = treeview.cget("columns")
    data = [[Paragraph(xml_escape(str(col)), header_style) for col in columns]]

    for child in treeview.get_children():
        row_values = treeview.item(child, "values")
        data.append([Paragraph(xml_escape(str(v)), cell_style) for v in row_values])

    total_rows = len(treeview.get_children())

    # Column widths proportional to the Treeview's own on-screen widths,
    # scaled to the PDF's printable width — single source of truth instead
    # of a second hardcoded set of widths that could drift out of sync.
    col_pixel_widths = [treeview.column(col, 'width') for col in columns]
    total_pixels = sum(col_pixel_widths)
    printable_width = A4[0] - 72  # 36pt left + 36pt right margin
    col_widths = [w / total_pixels * printable_width for w in col_pixel_widths]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)

    current_date = datetime.now().strftime("%d/%m/%Y")
    elements.append(table)
    total_rows_text = Paragraph(
        f"Total lock box is: {total_rows} <font size=8 color=grey>    (as of: {current_date})</font>",
        styles['Normal']
    )
    elements.append(total_rows_text)

    pdf.build(elements)
    print(f"PDF saved successfully as {file_name}")


def main():
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `py -3.13 test_pdf_export.py`
Expected: `All tests passed.`

- [ ] **Step 7: Regression-check the other test suites**

Run: `py -3.13 test_dropdown_lists.py && py -3.13 test_migrate_dropdown_lists.py && py -3.13 test_auto_update.py`
Expected: `All tests passed.` for all three (confirms moving `capture_table_to_pdf` didn't break anything these tests import-and-exercise).

- [ ] **Step 8: Commit**

```bash
git add D-Loto.py test_pdf_export.py
git commit -m "Move capture_table_to_pdf to module level, wrap long text instead of overflowing"
```

---

### Task 2: `is_text_truncated()` — module-level truncation-detection helper

**Files:**
- Modify: `D-Loto.py` (add module-level function, right before `def main():`)
- Test: `test_treeview_tooltip.py`

**Interfaces:**
- Produces: module-level `is_text_truncated(text, font, column_width, padding=10) -> bool`. Task 3's `attach_truncation_tooltip()` (nested in `main()`) calls this with `font` = the Treeview's body font (`FONT3`) and `column_width` = `treeview.column(col, 'width')`.

- [ ] **Step 1: Write the failing tests**

```python
# test_treeview_tooltip.py
import importlib.util
import os
import tkinter as tk
from tkinter import font as tkFont


def _load_dloto_module():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "D-Loto.py")
    spec = importlib.util.spec_from_file_location("dloto_module_under_test_tooltip", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dloto = _load_dloto_module()


def test_is_text_truncated_short_text_fits():
    root = tk.Tk()
    root.withdraw()
    try:
        font = tkFont.Font(root=root, family="Tahoma", size=9)
        assert dloto.is_text_truncated("Short", font, column_width=440) is False
    finally:
        root.destroy()


def test_is_text_truncated_long_text_overflows():
    root = tk.Tk()
    root.withdraw()
    try:
        font = tkFont.Font(root=root, family="Tahoma", size=9)
        long_text = "Isolate Valve A for overhaul and maintenance work on the primary system " * 3
        assert dloto.is_text_truncated(long_text, font, column_width=440) is True
    finally:
        root.destroy()


def test_is_text_truncated_respects_padding():
    root = tk.Tk()
    root.withdraw()
    try:
        font = tkFont.Font(root=root, family="Tahoma", size=9)
        text = "Exactly medium length text"
        width = font.measure(text)
        # Text exactly filling the column, with zero padding, must not count as truncated
        assert dloto.is_text_truncated(text, font, column_width=width, padding=0) is False
        # A column narrower than the text must count as truncated
        assert dloto.is_text_truncated(text, font, column_width=width - 5, padding=0) is True
    finally:
        root.destroy()


if __name__ == "__main__":
    test_is_text_truncated_short_text_fits()
    test_is_text_truncated_long_text_overflows()
    test_is_text_truncated_respects_padding()
    print("All tests passed.")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -3.13 test_treeview_tooltip.py`
Expected: `AttributeError: module 'dloto_module_under_test_tooltip' has no attribute 'is_text_truncated'`

- [ ] **Step 3: Add the implementation**

In `D-Loto.py`, find (this is the module-level function added by Task 1, Step 5):
```python
def main():
```

Replace with:
```python
def is_text_truncated(text, font, column_width, padding=10):
    """True if `text` rendered in `font` would overflow a Treeview column of
    `column_width` pixels — i.e. native ellipsis truncation would kick in.
    `padding` accounts for the cell's internal padding/borders."""
    return font.measure(text) > column_width - padding


def main():
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -3.13 test_treeview_tooltip.py`
Expected: `All tests passed.`

- [ ] **Step 5: Commit**

```bash
git add D-Loto.py test_treeview_tooltip.py
git commit -m "Add is_text_truncated() module-level helper for the Treeview tooltip"
```

---

### Task 3: Wire the hover tooltip into all three tabs

**Files:**
- Modify: `D-Loto.py` (inside `main()`)

**Interfaces:**
- Consumes: Task 2's `is_text_truncated(text, font, column_width)`.
- Produces: `attach_truncation_tooltip(treeview, columns, tooltip_column_name, font)` — a `main()`-nested function, called once per tab right after that tab's header-creation loop.

No automated test is possible for this step (Tkinter GUI event wiring, no headless UI test harness in this repo) — verified by a syntax/runtime smoke check plus a manual hover check (Task 4).

- [ ] **Step 1: Add `attach_truncation_tooltip()`**

Find (end of the `create_work_title_show`-adjacent class block, right before the Overview tab section starts):
```python
        def get_text(self):
            """Returns the current text from the Text widget."""
            return self.text_widget.get('1.0', 'end-1c')
        
    ################################################# OVERVIEW TAB ################################################# 
```

Replace with:
```python
        def get_text(self):
            """Returns the current text from the Text widget."""
            return self.text_widget.get('1.0', 'end-1c')

    # FUNCTION: Hover tooltip for a Treeview column whose text is natively
    # truncated (ellipsis) because it doesn't fit the column width
    def attach_truncation_tooltip(treeview, columns, tooltip_column_name, font):
        tooltip_col_id = f"#{columns.index(tooltip_column_name) + 1}"
        tooltip_state = {'win': None, 'row': None}

        def hide_tooltip():
            if tooltip_state['win'] is not None:
                tooltip_state['win'].destroy()
            tooltip_state['win'] = None
            tooltip_state['row'] = None

        def on_motion(event):
            row_id = treeview.identify_row(event.y)
            col_id = treeview.identify_column(event.x)
            if not row_id or col_id != tooltip_col_id:
                hide_tooltip()
                return
            col_index = int(col_id.replace('#', '')) - 1
            values = treeview.item(row_id, 'values')
            if col_index >= len(values):
                hide_tooltip()
                return
            text = str(values[col_index])
            column_width = treeview.column(tooltip_col_id, 'width')
            if not is_text_truncated(text, font, column_width):
                hide_tooltip()
                return
            if tooltip_state['win'] is not None and tooltip_state['row'] == row_id:
                return  # already showing for this row
            hide_tooltip()
            win = tk.Toplevel(treeview)
            win.wm_overrideredirect(True)
            win.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 12}")
            tk.Label(win, text=text, background="#ffffe0", relief='solid', borderwidth=1,
                     font=font, wraplength=400, justify='left').pack()
            tooltip_state['win'] = win
            tooltip_state['row'] = row_id

        def on_leave(event):
            hide_tooltip()

        treeview.bind("<Motion>", on_motion, add="+")
        treeview.bind("<Leave>", on_leave, add="+")

    ################################################# OVERVIEW TAB ################################################# 
```

- [ ] **Step 2: Wire it into the Overview tab**

Find:
```python
    for h,w in zip(header,headerw):
        loto_datalist.heading(h,text=h, command=lambda _col=h: treeview_sort_column(loto_datalist, _col, False))
        loto_datalist.column(h,width=w,anchor='center')

    # FUNCTION: Sort value by click at the Column header
```

Replace with:
```python
    for h,w in zip(header,headerw):
        loto_datalist.heading(h,text=h, command=lambda _col=h: treeview_sort_column(loto_datalist, _col, False))
        loto_datalist.column(h,width=w,anchor='center')

    attach_truncation_tooltip(loto_datalist, header, 'Work Description', FONT3)

    # FUNCTION: Sort value by click at the Column header
```

- [ ] **Step 3: Wire it into the Pending tab**

Find:
```python
    for h,w in zip(header_p,headerw_p):
        loto_datalist_p.heading(h,text=h, command=lambda _col=h: treeview_sort_column(loto_datalist_p, _col, False))
        loto_datalist_p.column(h,width=w,anchor='center')

    # FUNCTION: Sort value by click at the Column header
```

Replace with:
```python
    for h,w in zip(header_p,headerw_p):
        loto_datalist_p.heading(h,text=h, command=lambda _col=h: treeview_sort_column(loto_datalist_p, _col, False))
        loto_datalist_p.column(h,width=w,anchor='center')

    attach_truncation_tooltip(loto_datalist_p, header_p, 'Work Description', FONT3)

    # FUNCTION: Sort value by click at the Column header
```

- [ ] **Step 4: Wire it into the Completed tab**

Find:
```python
    for h,w in zip(header_c,headerw_c):
        loto_datalist_c.heading(h,text=h)
        loto_datalist_c.column(h,width=w,anchor='center')

    # CREATE: COLUMN WIDTH DISABLE RESIZABLE
    def disable_column_resize(event):
        if loto_datalist_c.identify_region(event.x, event.y) == "separator":
            return "break"  # This stops the event from propagating further
```

Replace with:
```python
    for h,w in zip(header_c,headerw_c):
        loto_datalist_c.heading(h,text=h)
        loto_datalist_c.column(h,width=w,anchor='center')

    attach_truncation_tooltip(loto_datalist_c, header_c, 'Work Description', FONT3)

    # CREATE: COLUMN WIDTH DISABLE RESIZABLE
    def disable_column_resize(event):
        if loto_datalist_c.identify_region(event.x, event.y) == "separator":
            return "break"  # This stops the event from propagating further
```

- [ ] **Step 5: Syntax/runtime sanity check**

```bash
py -3.13 -c "import ast; ast.parse(open('D-Loto.py', encoding='utf-8').read()); print('syntax OK')"
```
Expected: `syntax OK`

Then sync + build to fully validate imports:
```bash
powershell -File "TestBuildFromCommandLine/build.ps1"
```
(If plain `pyinstaller` isn't on PATH in this shell, run `py -3.13 -m PyInstaller D-Loto.spec --noconfirm` from `TestBuildFromCommandLine/` instead — see CLAUDE.md.)
Expected: build completes with no errors.

- [ ] **Step 6: Regression-check all test suites**

```bash
py -3.13 test_pdf_export.py && py -3.13 test_treeview_tooltip.py && py -3.13 test_dropdown_lists.py && py -3.13 test_migrate_dropdown_lists.py && py -3.13 test_auto_update.py
```
Expected: `All tests passed.` for each.

- [ ] **Step 7: Commit**

```bash
git add D-Loto.py "TestBuildFromCommandLine/D-Loto.py"
git commit -m "Add hover tooltip for truncated Work Description cells on all three tabs"
```

---

### Task 4: End-to-end verification

**Files:** None (verification only).

**Interfaces:** None.

- [ ] **Step 1: Verify the PDF fix with a real Treeview, not just the fake one**

Run D-Loto.py (dev `ENV`), open the Overview tab, and if there's at least one entry with a long Work Description, click "PRINT" and open the generated PDF — confirm the Work Description column wraps onto multiple lines instead of the table running off the page edge. If no long-title entry exists yet, this can be skipped since Task 1's automated test already exercises the wrapping code path directly (a long title with `&`/`<` that doesn't crash and produces a non-empty PDF) — note this explicitly rather than fabricating a screenshot-based check.

- [ ] **Step 2: Verify the tooltip manually**

This requires live mouse interaction with the running app's window, which this assistant cannot safely automate in this environment (no desktop-automation tool is available in this session — attempting one during the previous feature's work ended up capturing the user's actual live screen instead of just the app, so it was abandoned). Ask the user to manually:
- Hover over a long, truncated "Work Description" cell in each of the three tabs and confirm a tooltip with the full text appears near the cursor.
- Hover over a short, non-truncated cell and confirm no tooltip appears.
- Move the mouse to a different row/column and confirm the tooltip disappears/updates correctly.

Report back if anything doesn't match.

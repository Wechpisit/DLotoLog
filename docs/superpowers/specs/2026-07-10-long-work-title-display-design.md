# Design: Handling Long Work Titles in PDF Export and Tkinter Tables

**Date:** 2026-07-10
**Status:** Approved by user, pending implementation plan

## Problem

Long `work_title` values cause two separate display problems:

1. **PDF export** (`capture_table_to_pdf`, D-Loto.py:1656, triggered by the "PRINT" button on the Overview tab): raw strings are placed directly into a `reportlab.Table` with no `colWidths` specified, so the table auto-sizes to fit its widest content — a long Work Description pushes the table wider than the printable page, causing visual overflow/clipping in the generated PDF.
2. **Tkinter tables** (`ttk.Treeview`, all three tabs — Overview/Pending/Completed, each with their own "Work Description" column): the native Windows list-view control already truncates overflowing text with an ellipsis automatically, and the full title is already viewable by double-clicking a row to open its detail popup. This is not broken, but there's no quick way to see the full title without that extra click.

## Decision: no truncation for the PDF

Truncating the Work Description in the PDF (e.g. cutting to N characters + "…") was considered and rejected: this document is a LOTO safety record, and hiding part of a work description in a printed/exported artifact used for reference or audit is an unacceptable trade-off. Word-wrapping (full text, multiple lines) is used instead.

## Scope

- Fix PDF export column overflow via word-wrap (Overview tab only — it's the only tab with a "PRINT" button; Pending and Completed have no PDF export today, and none is being added).
- Add a hover tooltip to the "Work Description" column on all three tabs' Treeviews, shown only when the displayed text is actually wider than the column (i.e. only when native truncation kicked in).
- Out of scope: adding PDF export to Pending/Completed, changing page orientation, pagination/multi-page handling for the PDF table (pre-existing limitation, not part of this fix).

## PDF fix: `capture_table_to_pdf`

- Every cell (header and body, all columns) is wrapped in a `reportlab.platypus.Paragraph` instead of a plain string, so long text wraps within a fixed-width column instead of forcing the table wider.
- Cell text is escaped via `xml.sax.saxutils.escape` before wrapping in `Paragraph` — `Paragraph` parses its input as a small XML-like markup, so an unescaped `&`, `<`, or `>` in a user-entered work title would break rendering or raise an exception. Plain strings (the current code) don't have this problem, so this is a new failure mode introduced by switching to `Paragraph` and must be handled at the same time.
- `colWidths` for the `Table` are computed by reading each column's current on-screen width via `treeview.column(col, 'width')` and scaling those pixel proportions to fit the PDF's printable width — this ties the PDF layout to the same single source of truth as the Treeview's own column configuration (`header_w1..w5` in `main()`), instead of hardcoding a second set of widths that could drift out of sync.
- Page margins are reduced from reportlab's default (1 inch) to 0.5 inch on all sides, freeing up horizontal space for the Work Description column.
- Table style commands that only make sense for plain-string cells (`ALIGN`, `FONTNAME`, `FONTSIZE`, `TEXTCOLOR` on the header) move into two `ParagraphStyle`s (header: bold, whitesmoke, centered; body: normal weight, left-aligned — long wrapped text reads poorly centered). `BACKGROUND`, `GRID`, and `BOTTOMPADDING` stay as `TableStyle` commands since those are cell-level properties independent of the flowable inside. `VALIGN: MIDDLE` is added so rows with wrapped multi-line cells stay visually aligned with single-line neighbors.
- `repeatRows=1` is added to `Table` so the header repeats if the table spans multiple pages (a pre-existing gap, cheap to fix while already touching this code).

## Tooltip fix: Treeview hover

A single helper function, defined once in `main()` and called once per tab's Treeview after that tab's headers are configured:

```
attach_truncation_tooltip(treeview, columns, "Work Description", font)
```

- `columns` is that tab's header list (`header`, `header_p`, or `header_c`) — the column's position is looked up by name (`columns.index("Work Description")`), not hardcoded to an index, so it keeps working if a tab's column order changes later.
- On `<Motion>`, the handler identifies the hovered row/column via `treeview.identify_row`/`identify_column`. If the hovered column isn't the Work Description column, any existing tooltip is hidden and nothing else happens.
- If it is the right column: the cell's text is measured with `tkFont.Font.measure` (using the same font the Treeview body uses) and compared against that column's configured pixel width. If the text fits, no tooltip is shown — this is the "only when actually truncated" behavior. If it overflows, a borderless `tk.Toplevel` (`overrideredirect(True)`) is placed near the cursor showing the full text in a `tk.Label`.
- On `<Leave>`, the tooltip is destroyed.
- Applied to `loto_datalist` (Overview), `loto_datalist_p` (Pending), and `loto_datalist_c` (Completed).

## Testing

This is GUI-only behavior (Treeview hover interaction, PDF visual layout) with no headless test harness in this repo (same constraint as the rest of the Tkinter UI — see CLAUDE.md). Verification is manual:
- Generate a PDF from the Overview tab with a work title long enough to previously overflow, confirm it wraps within the column instead of pushing the table off the page, and confirm a title containing `&` or `<` doesn't break generation.
- Manually hover a long, truncated Work Description cell in each of the three tabs and confirm the tooltip appears with the full text; hover a short, non-truncated cell and confirm no tooltip appears.

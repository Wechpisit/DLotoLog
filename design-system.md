# D-LOTO Design System

This is a reference extracted from the actual `D-Loto.py` code (not an aspirational spec). Follow these values when adding or restyling any UI in this app so new screens/dialogs look native, not bolted on. If you introduce a new value, add it here too.

## Colors

| Name | Hex | Used for |
|---|---|---|
| Panel background | `#dcdad5` | Background of every `Toplevel` popup, `Frame`, and `Canvas` in the app (new-LOTO form, approve/reject/update/postpone dialogs, dropdown popups) |
| Row border (outer) | `#a9a7a3` | Outline on canvas rectangles that frame a popup's content area |
| Row border (inset highlight) | `#f8f2ea` | Second, lighter outline drawn just inside the outer border — gives the panel a subtle inset/bevel look |
| Focus highlight | `#5f87aa` | `highlightbackground`/`highlightcolor` on an input field when it gains focus (`on_focus_in`) |
| Unfocused border | `grey` | Input field border when not focused (`on_focus_out`) |
| Table row (even) | `#ffffff` | Treeview row background, alternating rows |
| Table row (odd) | `#F1F0E8` | Treeview row background, alternating rows |
| Tab selected | `lightblue` (bg) / `Black` (fg) | `Custom1.TNotebook.Tab` selected state |
| Button hover/active bg | `#e0e0e0` | Some plain `tk.Button` icon buttons (PDF/check toggles) |
| Button highlight border | `#cccccc` | Same icon buttons as above |

Don't invent new colors for standard panels/dialogs — reuse `#dcdad5` background + `#a9a7a3`/`#f8f2ea` double-outline. Only the treeview striping and focus states use other colors.

## Typography

Font family is **Tahoma** everywhere, no exceptions. Defined once in `font_setup()`:

| Token | Size / weight | Used for |
|---|---|---|
| FONT1 | 9, normal | Notebook tab labels |
| FONT2 | 10, bold | Emphasized labels |
| FONT3 | 10, normal | Body text |
| FONT4 | 18, bold | Large headers |
| FONT5 | 14, bold | Section headers |
| FONT6–8 | 9, normal | Misc labels |

Font sizes are **not** multiplied by `scaling_factor` — Tk/Windows scales point-sized fonts correctly on its own under DPI awareness. Only pixel-based geometry (padding, widths, window size) needs manual scaling — see below.

Buttons use ad-hoc sizes tied to their ttk style (see below), not the FONT1–8 tokens.

## Button Styles (ttk, theme = `"clam"`)

Defined once in `configure_button_styles()`, called right after `style = ttk.Style(root); style.theme_use("clam")`. Always reuse one of these — don't hand-roll `tk.Button` styling for standard actions.

| Style | Font | Padding (unscaled base, × `scaling_factor`) | Typical use |
|---|---|---|---|
| `Custom1.TButton` | tahoma 10 | (12, 8) | Primary/large actions |
| `Custom2.TButton` | tahoma 9 | (8, 5) | Standard dialog buttons (CONFIRM, CLOSE, COMPLETED, APPROVE, REJECT, etc.) — **default choice for any new dialog** |
| `Custom3.TButton` | tahoma 8 | (4, 5) | Small icon-adjacent buttons (e.g. inside compact dropdown rows) |

All three set `focuscolor='none'` (no dotted focus ring — matches the rest of the app's flat look).

## DPI Scaling

The app calls `ctypes.windll.shcore.SetProcessDpiAwareness(1)` at import time, meaning **Tk does not auto-scale pixel geometry** — every raw pixel value (window width/height, frame padding, `padx`/`pady`) must be manually multiplied by `scaling_factor`:

```python
def get_scaling_factor():
    user32 = ctypes.windll.user32
    dpi = user32.GetDpiForSystem()
    return dpi / 96  # 1.0 at 100%, 2.25 at 225%, etc.
```

`scaling_factor`, the `ttk.Style` object, and `configure_button_styles()` are all set up **immediately after `root = tk.Tk()`** (before the version-check dialog runs), specifically so any dialog shown during startup — not just the main window — can scale and use the shared button styles correctly. Keep this ordering if you touch that section of `main()`.

Rule of thumb: any literal pixel number you write for a `Toplevel`/`Frame`/`Canvas` size or padding must be wrapped as `int(N * scaling_factor)`. Font point sizes should stay literal (no scaling).

**Known pitfall** (hit while building the version-update dialog): forgetting to scale a popup's forced width/padding makes it render far too small on high-DPI displays (tested at 225% scaling, `dpi=216`) — title bar text gets truncated and small icons (e.g. Tk's built-in `bitmap="warning"`, only ~10px wide) become invisible. Prefer a Unicode glyph (e.g. `"⚠️"` with a plain, unscaled font size like 24) over Tk's legacy X11 bitmaps for icons in custom dialogs — glyphs scale via the font engine automatically; bitmaps don't.

## Standard Popup Anatomy

Every custom `Toplevel` dialog in this app (new-LOTO form, approve/reject/update/postpone, dropdown pickers) follows the same shape — use it for new dialogs too:

```python
dialog = tk.Toplevel(root, background='#dcdad5')
dialog.title("...")
dialog.resizable(False, False)
# icon: reuse resource_path("IconProgram1.ico") via ImageTk.PhotoImage + dialog.iconphoto(False, ...)
dialog.grab_set()  # modal

# Content area, padded, background matches the dialog
content_frame = tk.Frame(dialog, background='#dcdad5',
                          padx=int(20*scaling_factor), pady=int(15*scaling_factor))
content_frame.pack(fill="both", expand=True)

# ... labels/widgets using Tahoma font, #dcdad5 background ...

# Button row at the bottom, Custom2.TButton style
button_frame = tk.Frame(dialog, background='#dcdad5')
button_frame.pack(pady=(0, int(15*scaling_factor)))
ttk.Button(button_frame, text="...", style="Custom2.TButton", command=...).pack(side="left", padx=int(5*scaling_factor))
```

For dialogs shown before the main window's `center_windows()` helper exists (e.g. during startup, like the version-check dialog), center manually:

```python
dialog.update_idletasks()
w = max(dialog.winfo_reqwidth(), int(<min_width> * scaling_factor))
h = dialog.winfo_reqheight()
x = (dialog.winfo_screenwidth() - w) // 2
y = (dialog.winfo_screenheight() - h) // 2
dialog.geometry(f"{w}x{h}+{x}+{y}")
```

## Icons / Assets

- App/window icon: `IconProgram1.ico` (via `resource_path()` + `ImageTk.PhotoImage`)
- Small inline icons (resized via `create_resized_image(path, w, h)`, size always `int(N*scaling_factor)`): `DD.png` (dropdown arrow), `pdf2.png`/`folder.png` (attachment), `check.png` (checkbox), `refresh2.png` (refresh button)
- No existing "notification/warning" icon asset — use a Unicode emoji glyph instead (see DPI Scaling pitfall above) rather than adding a new image file, unless a custom illustrated icon is specifically requested.

## Where This Was Applied

The version-update dialog (`check_and_update()` in `D-Loto.py`) was redesigned to follow this system: `#dcdad5` background, Tahoma font, `Custom2.TButton` buttons, DPI-scaled padding/width, and a `⚠️` glyph instead of the tiny built-in Tk warning bitmap.

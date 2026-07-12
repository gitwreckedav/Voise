"""
theme.py

The entire look of Voise in one file.

Six dark themes, each defined as a small palette (9 colours). One
stylesheet template turns any palette into the full app look, and
hover/pressed/gradient shades are DERIVED from the palette - so every
theme automatically gets consistent depth, contrast and states
instead of hand-tuned one-offs.

Colour rules kept across all themes:
- Backgrounds stay near-black (this is a dark-only app).
- Text stays light for WCAG-friendly contrast on every surface.
- The accent is used sparingly: primary buttons, selection, focus.
- Red is reserved for the live microphone; green for success. Those
  never change with the theme, so their meaning stays constant.
"""

# --- colours that keep their MEANING regardless of theme -------------
REC_RED = "#ff5d5d"
OK_GREEN = "#5fc98e"

DEFAULT_THEME = "Midnight Blues"

# name -> palette. Keys: BG (window), SURFACE (text boxes),
# SURFACE_2 (buttons), BORDER, BORDER_LIT, TEXT, MUTED, ACCENT,
# ACCENT_DIM (selection / primary-button base).
THEMES = {
    "Midnight Blues": {
        "BG": "#131316", "SURFACE": "#1b1b1f", "SURFACE_2": "#232329",
        "BORDER": "#2c2c34", "BORDER_LIT": "#3d3d47",
        "TEXT": "#e9e9ec", "MUTED": "#8f8f9a",
        "ACCENT": "#5b9cf5", "ACCENT_DIM": "#2b4a75",
    },
    "Forest Dark": {
        "BG": "#101512", "SURFACE": "#171d19", "SURFACE_2": "#1f2721",
        "BORDER": "#2a352e", "BORDER_LIT": "#3b4a40",
        "TEXT": "#e7ece8", "MUTED": "#8d9a91",
        "ACCENT": "#4ecb71", "ACCENT_DIM": "#235c38",
    },
    "Amber Noir": {
        "BG": "#151210", "SURFACE": "#1d1915", "SURFACE_2": "#26211b",
        "BORDER": "#332c23", "BORDER_LIT": "#473d30",
        "TEXT": "#ece8e2", "MUTED": "#9c9284",
        "ACCENT": "#f5a623", "ACCENT_DIM": "#6b4a15",
    },
    "Deep Purple": {
        "BG": "#131118", "SURFACE": "#1a1721", "SURFACE_2": "#221e2b",
        "BORDER": "#2e2839", "BORDER_LIT": "#40374e",
        "TEXT": "#eae7f0", "MUTED": "#948da1",
        "ACCENT": "#9b7bf5", "ACCENT_DIM": "#453267",
    },
    "Slate Storm": {
        "BG": "#14161a", "SURFACE": "#1b1e23", "SURFACE_2": "#23272d",
        "BORDER": "#2e333a", "BORDER_LIT": "#414851",
        "TEXT": "#e8eaed", "MUTED": "#8e959e",
        "ACCENT": "#4d9fff", "ACCENT_DIM": "#24486f",
    },
    "Rose Gold": {
        "BG": "#161214", "SURFACE": "#1e181c", "SURFACE_2": "#272025",
        "BORDER": "#342a31", "BORDER_LIT": "#483a43",
        "TEXT": "#eee8eb", "MUTED": "#9c8f96",
        "ACCENT": "#f06292", "ACCENT_DIM": "#63263f",
    },
}


# --- shade helpers: derive hover/gradient states from any colour -----

def _hex_to_rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def lighten(value: str, factor: float) -> str:
    """Move a colour toward white. factor 0..1."""
    r, g, b = _hex_to_rgb(value)
    return "#{:02x}{:02x}{:02x}".format(
        *(min(255, int(c + (255 - c) * factor)) for c in (r, g, b))
    )


def darken(value: str, factor: float) -> str:
    """Move a colour toward black. factor 0..1."""
    r, g, b = _hex_to_rgb(value)
    return "#{:02x}{:02x}{:02x}".format(
        *(max(0, int(c * (1 - factor))) for c in (r, g, b))
    )


def swatches(name: str) -> list:
    """Six representative colours for the theme picker row."""
    p = THEMES.get(name, THEMES[DEFAULT_THEME])
    return [p["BG"], p["SURFACE_2"], p["ACCENT_DIM"],
            p["ACCENT"], p["MUTED"], p["TEXT"]]


def build_stylesheet(theme_name: str) -> str:
    p = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    bg, surface, s2 = p["BG"], p["SURFACE"], p["SURFACE_2"]
    border, border_lit = p["BORDER"], p["BORDER_LIT"]
    text, muted = p["TEXT"], p["MUTED"]
    accent, ad = p["ACCENT"], p["ACCENT_DIM"]

    return f"""
QMainWindow, QWidget {{
    background: {bg};
    color: {text};
    font-size: 13px;
}}

/* --- text areas (OT1 / OT2 / prompt editor) --- */
QTextEdit {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 10px;
    font-size: 14px;
    selection-background-color: {ad};
}}
QTextEdit:focus {{
    border: 1px solid {ad};
}}

/* --- buttons: top-light gradient + darker base edge = depth --- */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {lighten(s2, 0.07)}, stop:0.08 {lighten(s2, 0.035)}, stop:1 {darken(s2, 0.16)});
    border: 1px solid {border};
    border-top-color: {lighten(border, 0.12)};
    border-bottom-color: {darken(border, 0.35)};
    border-radius: 7px;
    padding: 7px 16px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {lighten(s2, 0.12)}, stop:0.08 {lighten(s2, 0.08)}, stop:1 {darken(s2, 0.08)});
    border-color: {border_lit};
    border-top-color: {lighten(border_lit, 0.1)};
}}
QPushButton:pressed {{
    background: {darken(s2, 0.3)};
    border-top-color: {darken(border, 0.4)};
    border-bottom-color: {border_lit};
    padding-top: 8px;
    padding-bottom: 6px;
}}
QPushButton:disabled {{
    color: {darken(muted, 0.35)};
    background: {darken(s2, 0.2)};
    border-color: {darken(border, 0.2)};
}}

/* primary action (Start Recording, Process, Save) */
QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {lighten(ad, 0.32)}, stop:0.08 {lighten(ad, 0.2)}, stop:1 {ad});
    border: 1px solid {lighten(ad, 0.18)};
    border-top-color: {lighten(ad, 0.45)};
    border-bottom-color: {darken(ad, 0.35)};
    color: {lighten(accent, 0.8)};
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {lighten(ad, 0.42)}, stop:0.08 {lighten(ad, 0.3)}, stop:1 {lighten(ad, 0.08)});
}}
QPushButton#primary:pressed {{
    background: {darken(ad, 0.15)};
    border-top-color: {darken(ad, 0.3)};
    padding-top: 8px;
    padding-bottom: 6px;
}}
QPushButton#primary:disabled {{
    background: {darken(ad, 0.45)};
    color: {muted};
    border-color: {darken(ad, 0.3)};
}}

/* the flat toggle for the developer panel */
QPushButton#flat {{
    background: transparent;
    border: none;
    color: {muted};
    text-align: left;
    padding: 4px 2px;
}}
QPushButton#flat:hover {{
    color: {text};
}}

/* --- dropdowns --- */
QComboBox {{
    background: {s2};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 5px 10px;
}}
QComboBox:hover {{
    border-color: {border_lit};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background: {s2};
    border: 1px solid {border_lit};
    border-radius: 6px;
    padding: 4px;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    min-height: 20px;
    border-radius: 4px;
    color: {text};
}}
QComboBox QAbstractItemView::item:hover,
QComboBox QAbstractItemView::item:selected {{
    background: {ad};
    color: {lighten(accent, 0.8)};
}}

/* --- single-line inputs --- */
QLineEdit {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {ad};
}}
QLineEdit:focus {{
    border-color: {ad};
}}

/* --- checkboxes --- */
QCheckBox {{
    spacing: 8px;
    color: {muted};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {border_lit};
    border-radius: 4px;
    background: {surface};
}}
QCheckBox::indicator:checked {{
    background: {ad};
    border-color: {lighten(ad, 0.2)};
}}

/* --- radio buttons (theme picker) --- */
QRadioButton {{
    spacing: 10px;
    color: {text};
    background: transparent;
}}
QRadioButton::indicator {{
    width: 15px;
    height: 15px;
    border: 1px solid {border_lit};
    border-radius: 8px;
    background: {surface};
}}
QRadioButton::indicator:checked {{
    background: {accent};
    border-color: {lighten(ad, 0.25)};
}}

/* theme picker rows */
QFrame#themeRow {{
    background: {surface};
    border: 1px solid {border};
    border-radius: 8px;
}}
QFrame#themeRow:hover {{
    border-color: {border_lit};
}}
QFrame#themeRow[selected="true"] {{
    border-color: {accent};
}}

/* --- group boxes (dev panel) --- */
QGroupBox {{
    border: 1px solid {border};
    border-radius: 8px;
    margin-top: 12px;
    padding: 10px 8px 8px 8px;
    color: {muted};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}

/* --- collapsible section headers (chevron toggles) --- */
QToolButton#sectionToggle {{
    background: transparent;
    border: none;
    color: {text};
    font-size: 13px;
    font-weight: 700;
    padding: 8px 4px;
}}
QToolButton#sectionToggle:hover {{
    color: {accent};
}}

QScrollArea {{
    border: none;
}}

/* --- special labels (set via setObjectName in the UI code) --- */
QLabel#recOn   {{ color: {REC_RED};  font-weight: 700; }}
QLabel#recOff  {{ color: {darken(muted, 0.3)}; }}
QLabel#muted   {{ color: {muted}; font-size: 12px; }}
QLabel#section {{
    color: {muted};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-top: 4px;
}}
QLabel#mono {{
    font-family: Menlo, monospace;
    font-size: 11px;
    color: {muted};
}}
QLabel#ok {{ color: {OK_GREEN}; }}

/* --- scrollbars: slim and quiet --- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {border_lit};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}
"""

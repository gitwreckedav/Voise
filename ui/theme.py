"""
theme.py

The entire look of Voise in one file - a Qt stylesheet (QSS, works
like CSS). Tweak colours here freely; no logic lives in this file.

Palette: near-black surfaces, soft off-white text, one calm blue
accent, red reserved for the live microphone.
"""

# --- palette ---------------------------------------------------------
BG          = "#131316"   # window background
SURFACE     = "#1b1b1f"   # text boxes, panels
SURFACE_2   = "#232329"   # buttons
BORDER      = "#2c2c34"
BORDER_LIT  = "#3d3d47"
TEXT        = "#e9e9ec"
TEXT_MUTED  = "#8f8f9a"
ACCENT      = "#5b9cf5"   # calm blue - primary actions
ACCENT_DIM  = "#2b4a75"
REC_RED     = "#ff5d5d"   # live microphone only
OK_GREEN    = "#5fc98e"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background: {BG};
    color: {TEXT};
    font-size: 13px;
}}

/* --- text areas (OT1 / OT2 / prompt editor) --- */
QTextEdit {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px;
    font-size: 14px;
    selection-background-color: {ACCENT_DIM};
}}
QTextEdit:focus {{
    border: 1px solid {ACCENT_DIM};
}}

/* --- buttons --- */
QPushButton {{
    background: {SURFACE_2};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 16px;
}}
QPushButton:hover {{
    background: #2b2b33;
    border-color: {BORDER_LIT};
}}
QPushButton:pressed {{
    background: #18181d;
}}
QPushButton:disabled {{
    color: #55555e;
    background: #1a1a1f;
    border-color: #232329;
}}

/* primary action (Start Recording, Process, Save) */
QPushButton#primary {{
    background: {ACCENT_DIM};
    border: 1px solid #38598a;
    color: #eaf2ff;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background: #33578a;
}}
QPushButton#primary:disabled {{
    background: #1f2733;
    color: #55606e;
    border-color: #232c38;
}}

/* the flat toggle for the developer panel */
QPushButton#flat {{
    background: transparent;
    border: none;
    color: {TEXT_MUTED};
    text-align: left;
    padding: 4px 2px;
}}
QPushButton#flat:hover {{
    color: {TEXT};
}}

/* --- dropdowns --- */
QComboBox {{
    background: {SURFACE_2};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 10px;
}}
QComboBox:hover {{
    border-color: {BORDER_LIT};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background: {SURFACE_2};
    border: 1px solid {BORDER_LIT};
    selection-background-color: {ACCENT_DIM};
}}

/* --- group boxes (dev panel, settings) --- */
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding: 10px 8px 8px 8px;
    color: {TEXT_MUTED};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}

/* --- special labels (set via setObjectName in the UI code) --- */
QLabel#recOn   {{ color: {REC_RED};    font-weight: 700; }}
QLabel#recOff  {{ color: #55555e; }}
QLabel#muted   {{ color: {TEXT_MUTED}; font-size: 12px; }}
QLabel#section {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-top: 4px;
}}
QLabel#mono {{
    font-family: Menlo, monospace;
    font-size: 11px;
    color: {TEXT_MUTED};
}}
QLabel#ok {{ color: {OK_GREEN}; }}

/* --- scrollbars: slim and quiet --- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_LIT};
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

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

/* --- buttons: subtle top-light gradient + darker base edge = depth --- */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #303039, stop:0.08 #2a2a32, stop:1 #1e1e24);
    border: 1px solid {BORDER};
    border-top-color: #3f3f4a;
    border-bottom-color: #17171b;
    border-radius: 7px;
    padding: 7px 16px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #383842, stop:0.08 #31313a, stop:1 #24242b);
    border-color: {BORDER_LIT};
    border-top-color: #4a4a56;
}}
QPushButton:pressed {{
    background: #17171c;
    border-top-color: #131317;
    border-bottom-color: #2c2c34;
    padding-top: 8px;
    padding-bottom: 6px;
}}
QPushButton:disabled {{
    color: #55555e;
    background: #1a1a1f;
    border-color: #232329;
}}

/* primary action (Start Recording, Process, Save) */
QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #4a7cc0, stop:0.08 #3d6cae, stop:1 #2b4a75);
    border: 1px solid #38598a;
    border-top-color: #5d8ecf;
    border-bottom-color: #1d3350;
    color: #eaf2ff;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #5488cc, stop:0.08 #4577ba, stop:1 #315482);
}}
QPushButton#primary:pressed {{
    background: #27436b;
    border-top-color: #203858;
    padding-top: 8px;
    padding-bottom: 6px;
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
/* the dropdown list itself (needs a QListView view - set in code) */
QComboBox QAbstractItemView {{
    background: {SURFACE_2};
    border: 1px solid {BORDER_LIT};
    border-radius: 6px;
    padding: 4px;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    min-height: 20px;
    border-radius: 4px;
    color: {TEXT};
}}
QComboBox QAbstractItemView::item:hover,
QComboBox QAbstractItemView::item:selected {{
    background: {ACCENT_DIM};
    color: #eaf2ff;
}}

/* --- single-line inputs --- */
QLineEdit {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {ACCENT_DIM};
}}
QLineEdit:focus {{
    border-color: {ACCENT_DIM};
}}

/* --- checkboxes --- */
QCheckBox {{
    spacing: 8px;
    color: {TEXT_MUTED};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER_LIT};
    border-radius: 4px;
    background: {SURFACE};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT_DIM};
    border-color: #38598a;
}}

/* --- collapsible section headers (chevron toggles) --- */
QToolButton#sectionToggle {{
    background: transparent;
    border: none;
    color: {TEXT};
    font-size: 13px;
    font-weight: 700;
    padding: 8px 4px;
}}
QToolButton#sectionToggle:hover {{
    color: {ACCENT};
}}

QScrollArea {{
    border: none;
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

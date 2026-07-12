"""
theme_picker.py

The theme chooser rows in Settings -> Appearance: each row is a radio
button, the theme's name, and six little swatches previewing its
palette. The selected row gets an accent-coloured border.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QRadioButton, QVBoxLayout,
    QWidget
)

from ui.theme import DEFAULT_THEME, THEMES, swatches


class _ThemeRow(QFrame):

    def __init__(self, name: str, group: QButtonGroup):
        super().__init__()
        self.setObjectName("themeRow")
        self.name = name

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)

        self.radio = QRadioButton(name)
        group.addButton(self.radio)
        row.addWidget(self.radio)
        row.addStretch()

        # Six swatches: backgrounds, accent shades, text tones.
        for colour in swatches(name):
            chip = QLabel()
            chip.setFixedSize(18, 18)
            chip.setStyleSheet(
                f"background: {colour}; border-radius: 4px;"
                "border: 1px solid rgba(255,255,255,0.14);"
            )
            row.addWidget(chip)

    def mousePressEvent(self, event):
        # Clicking anywhere on the row selects its radio.
        self.radio.setChecked(True)
        super().mousePressEvent(event)


class ThemePicker(QWidget):

    def __init__(self, current_theme: str):
        super().__init__()
        # Never-picked-before means the default theme is in effect.
        if current_theme not in THEMES:
            current_theme = DEFAULT_THEME
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._group = QButtonGroup(self)
        self._rows = []
        for name in THEMES:
            row = _ThemeRow(name, self._group)
            if name == current_theme:
                row.radio.setChecked(True)
            row.radio.toggled.connect(self._restyle)
            self._rows.append(row)
            layout.addWidget(row)
        self._restyle()

    def current(self) -> str:
        for row in self._rows:
            if row.radio.isChecked():
                return row.name
        return self._rows[0].name

    def _restyle(self):
        """Re-apply the [selected="true"] border to the checked row."""
        for row in self._rows:
            row.setProperty("selected", row.radio.isChecked())
            row.style().unpolish(row)
            row.style().polish(row)

"""
collapsible.py

A settings section that folds away: a chevron header you click to
show/hide its content.

  ▸ Section name            (closed - just the name)
  ▾ Section name            (open - name + the whole section below)
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton, QVBoxLayout, QWidget


class CollapsibleSection(QWidget):

    def __init__(self, title: str, content: QWidget, expanded: bool = False):
        super().__init__()

        self._toggle = QToolButton()
        self._toggle.setObjectName("sectionToggle")
        # "&&" because a single "&" in button text is Qt's shortcut
        # marker and would vanish (e.g. "About & Updates" -> "About _Updates").
        self._toggle.setText(title.replace("&", "&&"))
        self._toggle.setCheckable(True)
        self._toggle.setChecked(expanded)
        self._toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._toggle.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self._toggle.clicked.connect(self._on_toggle)

        self._content = content
        self._content.setVisible(expanded)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self._toggle)
        layout.addWidget(self._content)

    def _on_toggle(self, checked: bool):
        self._content.setVisible(checked)
        self._toggle.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import STYLESHEET


def main():
    app = QApplication(sys.argv)

    # One stylesheet for the whole app - see ui/theme.py to retheme.
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

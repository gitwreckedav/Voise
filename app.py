import sys

from PySide6.QtWidgets import QApplication

from config import SettingsStore
from ui.main_window import MainWindow
from ui.theme import build_stylesheet


def main():
    app = QApplication(sys.argv)

    # One stylesheet for the whole app, built from the theme the user
    # picked in Settings -> Appearance (see ui/theme.py).
    app.setStyleSheet(build_stylesheet(SettingsStore().get_theme()))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

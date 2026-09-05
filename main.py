"""
Siedler 6 Mod & Map Manager - Haupteinstiegspunkt (main.py)
Initialisiert High-DPI, PyQt6 Application, QSS-Styling und startet die GUI.
"""

import os
import sys

# High DPI Awareness für gestochen scharfe Schriften auf Windows
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# Pfad zu ModManager sicherstellen
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ModManager.app_window import MainWindow


def main():
    # Windows High DPI Policy
    if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, 'PassThrough'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    app = QApplication(sys.argv)
    app.setApplicationName("Siedler 6 Mod & Map Manager")
    app.setOrganizationName("Siedler 6 Modding Community")

    # QSS Stylesheet laden
    theme_path = os.path.join(current_dir, "styles", "theme.qss")
    if os.path.exists(theme_path):
        with open(theme_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

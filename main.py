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

import traceback
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

try:
    from ModManager.app_window import MainWindow
except ImportError:
    from app_window import MainWindow

# Logdatei im UserMods-Verzeichnis
log_file = os.path.join(parent_dir, "mod_manager.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    encoding="utf-8"
)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.critical("Unbehandelte Ausnahme:\n" + err_msg)
    print("\n[KRITISCHER FEHLER]\n" + err_msg, file=sys.stderr)
    try:
        QMessageBox.critical(None, "Mod Manager Fehler", f"Ein unerwarteter Fehler ist aufgetreten:\n\n{exc_value}\n\nDetails in mod_manager.log.")
    except Exception:
        pass

sys.excepthook = handle_exception


def main():
    logging.info("Starte Siedler 6 Mod & Map Manager...")
    try:
        # Windows-spezifischer Fix, damit das Icon in der Taskleiste korrekt angezeigt wird
        # (verhindert das Standard-Python-Icon durch Setzen einer eigenen AppUserModelID)
        if sys.platform == "win32":
            try:
                import ctypes
                myappid = 'siedler6.modmanager.1_1' 
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception as e:
                logging.warning(f"Konnte AppUserModelID nicht setzen: {e}")

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

        # Icon laden
        icon_path = os.path.join(current_dir, "assets", "icon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        window = MainWindow()
        if os.path.exists(icon_path):
            window.setWindowIcon(QIcon(icon_path))
        window.show()

        logging.info("Hauptfenster erfolgreich geöffnet. Starte Event-Loop.")
        sys.exit(app.exec())
    except Exception as e:
        logging.exception(f"Fehler in main(): {e}")
        raise


if __name__ == "__main__":
    main()

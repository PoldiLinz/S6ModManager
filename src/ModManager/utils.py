import sys
import os

def get_base_path() -> str:
    """
    Gibt den Basis-Pfad der Anwendung zurück.
    Funktioniert sowohl beim direkten Ausführen über Python als auch wenn als .exe kompiliert (PyInstaller).
    """
    if getattr(sys, 'frozen', False):
        # Wenn als .exe gebündelt (OneDir oder OneFile)
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        # Wenn direkt über Python gestartet (dieses Skript liegt im ModManager-Ordner)
        return os.path.dirname(os.path.abspath(__file__))

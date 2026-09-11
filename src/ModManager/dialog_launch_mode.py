"""
Siedler 6 ModManager - Dialog: Start-Assistent (Launch Mode Dialog)
Ermöglicht dem Benutzer die Wahl zwischen Direktstart (Python) und lokaler .exe Kompilierung.
Herausgeber: Leopold Walli AI Software Productions
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QProgressBar, QFrame, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QProcess
from PyQt6.QtGui import QIcon, QPixmap

from ModManager.engines.system_engine import SystemEngine
from ModManager.engines.i18n_engine import t


class CompilationWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, str)  # success, message, exe_path

    def __init__(self, repo_dir: str):
        super().__init__()
        self.repo_dir = repo_dir

    def run(self):
        try:
            self.progress.emit(10, t("launcher.compiling_status", default="Prüfe PyInstaller-Umgebung..."))

            # 1. PyInstaller prüfen / installieren
            python_exe = sys.executable
            try:
                import PyInstaller
            except ImportError:
                self.progress.emit(20, "Installiere PyInstaller...")
                proc = subprocess.run(
                    [python_exe, "-m", "pip", "install", "pyinstaller"],
                    capture_output=True,
                    text=True
                )
                if proc.returncode != 0:
                    raise RuntimeError(f"PyInstaller-Installation fehlgeschlagen:\n{proc.stderr}")

            # 2. Build-Skript oder direkten PyInstaller-Befehl ausführen
            self.progress.emit(40, t("launcher.compiling_status", default="Kompiliere S6ModManager.exe... Bitte warten..."))
            
            build_script = os.path.join(self.repo_dir, "build_exe.py")
            if os.path.exists(build_script):
                proc = subprocess.run(
                    [python_exe, build_script],
                    cwd=self.repo_dir,
                    capture_output=True,
                    text=True
                )
                if proc.returncode != 0:
                    raise RuntimeError(f"Build-Prozess fehlgeschlagen:\n{proc.stderr}\n{proc.stdout}")
            else:
                # Fallback PyInstaller Befehl
                main_py = os.path.join(self.repo_dir, "ModManager", "main.py")
                icon_ico = os.path.join(self.repo_dir, "ModManager", "assets", "icon.ico")
                args = [
                    python_exe, "-m", "PyInstaller",
                    "--noconfirm", "--onedir", "--windowed",
                    "--name", "S6ModManager",
                    "--icon", icon_ico,
                    "--add-data", f"{os.path.join(self.repo_dir, 'ModManager', 'locales')}{os.pathsep}ModManager/locales",
                    "--add-data", f"{os.path.join(self.repo_dir, 'ModManager', 'styles')}{os.pathsep}ModManager/styles",
                    "--add-data", f"{os.path.join(self.repo_dir, 'ModManager', 'assets')}{os.pathsep}ModManager/assets",
                    "--add-data", f"{os.path.join(self.repo_dir, 'tools')}{os.pathsep}tools",
                    "--add-data", f"{os.path.join(self.repo_dir, 'Presets')}{os.pathsep}Presets",
                    "--add-data", f"{os.path.join(self.repo_dir, 'Scenarios')}{os.pathsep}Scenarios",
                    "--hidden-import", "PyQt6",
                    main_py
                ]
                proc = subprocess.run(args, cwd=self.repo_dir, capture_output=True, text=True)
                if proc.returncode != 0:
                    raise RuntimeError(f"PyInstaller-Aufruf fehlgeschlagen:\n{proc.stderr}")

            exe_path = os.path.join(self.repo_dir, "dist", "S6ModManager", "S6ModManager.exe")
            if not os.path.exists(exe_path):
                raise FileNotFoundError(f"S6ModManager.exe wurde nicht gefunden unter: {exe_path}")

            # 3. Desktop-Verknüpfung anlegen
            self.progress.emit(85, "Erstelle Desktop-Verknüpfung...")
            try:
                self._create_desktop_shortcut(exe_path)
            except Exception as e:
                print(f"[Warning] Konnte Verknüpfung nicht erstellen: {e}")

            self.progress.emit(100, t("launcher.compile_success", default="S6ModManager.exe erfolgreich erstellt!"))
            self.finished.emit(True, "", exe_path)

        except Exception as e:
            self.finished.emit(False, str(e), "")

    def _create_desktop_shortcut(self, target_exe: str):
        if sys.platform != "win32":
            return
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            return
        shortcut_path = os.path.join(desktop, "Die Siedler 6 Mod Manager.lnk")
        icon_path = os.path.join(self.repo_dir, "ModManager", "assets", "icon.ico")
        ps_cmd = (
            f"$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{shortcut_path}'); "
            f"$s.TargetPath = '{target_exe}'; "
            f"$s.WorkingDirectory = '{os.path.dirname(target_exe)}'; "
            f"$s.IconLocation = '{icon_path}'; "
            f"$s.Save()"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)


class LaunchModeDialog(QDialog):
    MODE_DIRECT = "direct"
    MODE_EXE = "exe"
    MODE_CANCEL = "cancel"

    def __init__(self, system_engine: SystemEngine, parent=None):
        super().__init__(parent)
        self.system = system_engine
        self.selected_mode = self.MODE_CANCEL
        self.compiled_exe_path = ""
        self.repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        self.setWindowTitle(t("launcher.dialog_title", default="Siedler 6 ModManager • Start-Assistent"))
        self.setFixedSize(620, 520)

        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. Header mit Logo
        h_header = QHBoxLayout()
        h_header.setSpacing(16)

        lbl_logo = QLabel()
        png_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(png_path):
            pixmap = QPixmap(png_path).scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_logo.setPixmap(pixmap)
        h_header.addWidget(lbl_logo)

        v_title = QVBoxLayout()
        v_title.setSpacing(2)
        lbl_title = QLabel(t("launcher.header_title", default="👑 DIE SIEDLER 6 • MOD & MAP MANAGER"))
        lbl_title.setObjectName("SectionHeader")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f1c40f;")
        v_title.addWidget(lbl_title)

        lbl_sub = QLabel("Leopold Walli AI Software Productions")
        lbl_sub.setObjectName("DimLabel")
        lbl_sub.setStyleSheet("font-size: 12px; color: #8fa0b5; font-style: italic;")
        v_title.addWidget(lbl_sub)
        h_header.addLayout(v_title)
        h_header.addStretch()
        layout.addLayout(h_header)

        # Trenner
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2e3846; margin: 2px 0;")
        layout.addWidget(sep)

        # Beschreibung
        lbl_desc = QLabel(t("launcher.choose_mode_desc", default="Wähle aus, wie der ModManager auf diesem PC ausgeführt werden soll:"))
        lbl_desc.setStyleSheet("font-size: 13px; color: #cfd8dc; font-weight: 500;")
        layout.addWidget(lbl_desc)

        # 2. Option Card 1: Direktstart (Python)
        self.card_direct = QFrame()
        self.card_direct.setObjectName("CardDirect")
        self.card_direct.setStyleSheet(
            "QFrame#CardDirect { background-color: #1a222d; border: 1px solid #2e3b4e; border-radius: 8px; padding: 10px; }"
            "QFrame#CardDirect:hover { border: 1px solid #3d82db; }"
        )
        v_card1 = QVBoxLayout(self.card_direct)
        v_card1.setSpacing(6)

        lbl_c1_title = QLabel(t("launcher.mode_direct_title", default="⚡ Direktstart (Python)"))
        lbl_c1_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #5dade2;")
        v_card1.addWidget(lbl_c1_title)

        lbl_c1_desc = QLabel(t("launcher.mode_direct_desc", default="Startet den ModManager sofort direkt aus dem Quellcode. Keine Wartezeit, maximale Sicherheit."))
        lbl_c1_desc.setWordWrap(True)
        lbl_c1_desc.setStyleSheet("color: #a0b2c6; font-size: 12px;")
        v_card1.addWidget(lbl_c1_desc)

        self.btn_direct = QPushButton(t("launcher.btn_direct", default="⚡ Jetzt direkt starten"))
        self.btn_direct.setObjectName("PrimaryButton")
        self.btn_direct.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_direct.clicked.connect(self._choose_direct)
        v_card1.addWidget(self.btn_direct)

        layout.addWidget(self.card_direct)

        # 3. Option Card 2: Lokale .exe erstellen
        self.card_exe = QFrame()
        self.card_exe.setObjectName("CardExe")
        self.card_exe.setStyleSheet(
            "QFrame#CardExe { background-color: #1a222d; border: 1px solid #2e3b4e; border-radius: 8px; padding: 10px; }"
            "QFrame#CardExe:hover { border: 1px solid #f1c40f; }"
        )
        v_card2 = QVBoxLayout(self.card_exe)
        v_card2.setSpacing(6)

        lbl_c2_title = QLabel(t("launcher.mode_exe_title", default="🔨 Eigene S6ModManager.exe erstellen"))
        lbl_c2_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f1c40f;")
        v_card2.addWidget(lbl_c2_title)

        lbl_c2_desc = QLabel(t("launcher.mode_exe_desc", default="Kompiliert eine eigenständige Windows-Anwendung (.exe) direkt auf deinem PC. Startet künftig per Doppelklick ohne Windows SmartScreen-Alarm."))
        lbl_c2_desc.setWordWrap(True)
        lbl_c2_desc.setStyleSheet("color: #a0b2c6; font-size: 12px;")
        v_card2.addWidget(lbl_c2_desc)

        # Prüfen ob bereits eine .exe existiert
        existing_exe = os.path.join(self.repo_dir, "dist", "S6ModManager", "S6ModManager.exe")
        btn_compile_text = "🚀 Fertige S6ModManager.exe starten" if os.path.exists(existing_exe) else t("launcher.btn_compile", default="🔨 .exe kompilieren & Desktop-Icon anlegen")

        self.btn_compile = QPushButton(btn_compile_text)
        self.btn_compile.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_compile.clicked.connect(self._choose_compile_or_run_exe)
        v_card2.addWidget(self.btn_compile)

        layout.addWidget(self.card_exe)

        # 4. Progress Bereich (initial unsichtbar)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.lbl_progress_status = QLabel("")
        self.lbl_progress_status.setStyleSheet("color: #f1c40f; font-size: 12px; font-style: italic;")
        self.lbl_progress_status.hide()
        layout.addWidget(self.lbl_progress_status)

        layout.addStretch()

        # 5. Footer: Checkbox & Beenden
        h_footer = QHBoxLayout()
        self.chk_remember = QCheckBox(t("launcher.remember_choice", default="Diese Auswahl für zukünftige Starts merken"))
        self.chk_remember.setStyleSheet("color: #cfd8dc; font-size: 12px;")
        h_footer.addWidget(self.chk_remember)
        h_footer.addStretch()

        self.btn_cancel = QPushButton(t("common.cancel", default="Abbrechen"))
        self.btn_cancel.setFixedWidth(100)
        self.btn_cancel.clicked.connect(self.reject)
        h_footer.addWidget(self.btn_cancel)
        layout.addLayout(h_footer)

    def _choose_direct(self):
        self._save_preference_if_checked("direct")
        self.selected_mode = self.MODE_DIRECT
        self.accept()

    def _choose_compile_or_run_exe(self):
        existing_exe = os.path.join(self.repo_dir, "dist", "S6ModManager", "S6ModManager.exe")
        if os.path.exists(existing_exe):
            self._save_preference_if_checked("exe")
            self.selected_mode = self.MODE_EXE
            self.compiled_exe_path = existing_exe
            self.accept()
            return

        # Kompilierung starten
        self.btn_direct.setEnabled(False)
        self.btn_compile.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.show()
        self.lbl_progress_status.show()

        self.worker = CompilationWorker(self.repo_dir)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._compilation_finished)
        self.worker.start()

    def _update_progress(self, val: int, text: str):
        self.progress_bar.setValue(val)
        self.lbl_progress_status.setText(text)

    def _compilation_finished(self, success: bool, error: str, exe_path: str):
        self.btn_cancel.setEnabled(True)
        if success:
            self._save_preference_if_checked("exe")
            self.compiled_exe_path = exe_path
            self.lbl_progress_status.setText(t("launcher.compile_success", default="S6ModManager.exe erfolgreich erstellt!"))
            self.btn_compile.setText(t("launcher.btn_launch_exe", default="🚀 S6ModManager.exe jetzt starten"))
            self.btn_compile.setObjectName("PrimaryButton")
            self.btn_compile.style().unpolish(self.btn_compile)
            self.btn_compile.style().polish(self.btn_compile)
            self.btn_compile.setEnabled(True)
            self.btn_compile.clicked.disconnect()
            self.btn_compile.clicked.connect(self._launch_compiled_exe)
        else:
            self.btn_direct.setEnabled(True)
            self.btn_compile.setEnabled(True)
            self.btn_compile.setText(t("launcher.btn_compile", default="Erneut versuchen"))
            QMessageBox.critical(
                self,
                "Kompilierungsfehler",
                f"{t('launcher.compile_error', default='Fehler beim Kompilieren:')}\n\n{error}\n\nDu kannst die Anwendung stattdessen direkt via Quellcode starten."
            )

    def _launch_compiled_exe(self):
        if self.compiled_exe_path and os.path.exists(self.compiled_exe_path):
            QProcess.startDetached(self.compiled_exe_path, [])
            self.selected_mode = self.MODE_EXE
            self.accept()
            sys.exit(0)

    def _save_preference_if_checked(self, mode: str):
        if self.chk_remember.isChecked():
            try:
                self.system.save_settings({"preferred_launch_mode": mode})
            except Exception as e:
                print(f"[Warning] Could not save preferred_launch_mode: {e}")

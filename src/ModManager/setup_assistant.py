"""
Siedler 6 ModManager - Setup Assistent (setup_assistant.py)
Eigenständiger Einrichtungs- und Installations-Assistent.
Bietet Sprachauswahl (Standard: Englisch / Deutsch), Direktstart und lokale .exe-Kompilierung.
Herausgeber: Leopold Walli AI Software Productions
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# High DPI Awareness
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QProgressBar, QFrame, QMessageBox, QComboBox, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QProcess
from PyQt6.QtGui import QIcon, QPixmap

try:
    from ModManager.engines.system_engine import SystemEngine
    from ModManager.engines.i18n_engine import I18nEngine, t
except ImportError:
    from engines.system_engine import SystemEngine
    from engines.i18n_engine import I18nEngine, t


class CompilationWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, str)  # success, message, exe_path

    def __init__(self, repo_dir: str):
        super().__init__()
        self.repo_dir = repo_dir

    def run(self):
        try:
            self.progress.emit(10, t("launcher.compiling_status", default="Checking PyInstaller environment..."))

            # 1. PyInstaller prüfen / installieren
            python_exe = sys.executable
            try:
                import PyInstaller
            except ImportError:
                self.progress.emit(20, "Installing PyInstaller...")
                proc = subprocess.run(
                    [python_exe, "-m", "pip", "install", "pyinstaller"],
                    capture_output=True,
                    text=True
                )
                if proc.returncode != 0:
                    raise RuntimeError(f"PyInstaller installation failed:\n{proc.stderr}")

            # 2. Build-Skript ausführen
            self.progress.emit(40, t("launcher.compiling_status", default="Compiling S6ModManager.exe... Please wait..."))
            
            build_script = os.path.join(self.repo_dir, "build_exe.py")
            if os.path.exists(build_script):
                proc = subprocess.run(
                    [python_exe, build_script],
                    cwd=self.repo_dir,
                    capture_output=True,
                    text=True
                )
                if proc.returncode != 0:
                    raise RuntimeError(f"Build failed:\n{proc.stderr}\n{proc.stdout}")
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
                if os.path.exists(os.path.join(app_dir, "main.py")):
                    build_cwd = app_dir
                    main_py = os.path.join(app_dir, "main.py")
                    icon_ico = os.path.join(app_dir, "assets", "icon.ico")
                    args = [
                        python_exe, "-m", "PyInstaller",
                        "--noconfirm", "--onedir", "--windowed",
                        "--name", "S6ModManager",
                        "--icon", icon_ico,
                        "--add-data", f"{os.path.join(app_dir, 'locales')}{os.pathsep}locales",
                        "--add-data", f"{os.path.join(app_dir, 'styles')}{os.pathsep}styles",
                        "--add-data", f"{os.path.join(app_dir, 'assets')}{os.pathsep}assets",
                        "--add-data", f"{os.path.join(app_dir, 'tools')}{os.pathsep}tools",
                        "--add-data", f"{os.path.join(app_dir, 'Presets')}{os.pathsep}Presets",
                        "--add-data", f"{os.path.join(app_dir, 'Scenarios')}{os.pathsep}Scenarios",
                        "--hidden-import", "PyQt6",
                        main_py
                    ]
                else:
                    build_cwd = self.repo_dir
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
                proc = subprocess.run(args, cwd=build_cwd, capture_output=True, text=True)
                if proc.returncode != 0:
                    raise RuntimeError(f"PyInstaller error:\n{proc.stderr}")

            app_dir = os.path.dirname(os.path.abspath(__file__))
            exe_path = os.path.join(app_dir, "dist", "S6ModManager", "S6ModManager.exe")
            if not os.path.exists(exe_path):
                exe_path = os.path.join(self.repo_dir, "dist", "S6ModManager", "S6ModManager.exe")
            if not os.path.exists(exe_path):
                raise FileNotFoundError(f"S6ModManager.exe not found at: {exe_path}")

            # 3. Desktop-Verknüpfung anlegen
            self.progress.emit(85, "Creating Desktop shortcut...")
            try:
                self._create_desktop_shortcut(exe_path)
            except Exception as e:
                print(f"[Warning] Failed to create shortcut: {e}")

            self.progress.emit(100, t("launcher.compile_success", default="S6ModManager.exe compiled successfully!"))
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
        app_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(app_dir, "assets", "icon.ico")
        if not os.path.exists(icon_path):
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



class DisclaimerDialog(QDialog):
    """
    Erster Begrüßungs- und Haftungsausschluss-Dialog mit prominenter Sprachauswahl.
    Muss vom Benutzer bestätigt werden ("Verstanden" / "I Understand"), um den Setup-Assistenten zu öffnen.
    """
    def __init__(self, system_engine: SystemEngine = None, parent=None):
        super().__init__(parent)
        self.system = system_engine or SystemEngine()
        self.current_lang = getattr(self.system, "language", "en")
        I18nEngine.get_instance().set_language(self.current_lang)

        self.setFixedSize(580, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        icon_path = os.path.join(current_dir, "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._init_ui()
        self.retranslate_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)

        # 1. Header mit Logo und Titel
        h_header = QHBoxLayout()
        h_header.setSpacing(14)

        lbl_logo = QLabel()
        png_path = os.path.join(current_dir, "assets", "icon.png")
        if os.path.exists(png_path):
            pixmap = QPixmap(png_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_logo.setPixmap(pixmap)
        h_header.addWidget(lbl_logo)

        v_head = QVBoxLayout()
        v_head.setSpacing(2)
        self.lbl_head_title = QLabel("👑 THE SETTLERS 6 • MOD & MAP MANAGER")
        self.lbl_head_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #f1c40f;")
        v_head.addWidget(self.lbl_head_title)

        lbl_head_sub = QLabel("Leopold Walli AI Software Productions • Version 1.1")
        lbl_head_sub.setStyleSheet("font-size: 11px; color: #8fa0b5; font-style: italic;")
        v_head.addWidget(lbl_head_sub)
        h_header.addLayout(v_head)
        h_header.addStretch()
        layout.addLayout(h_header)

        # 2. Prominente Sprachauswahl ganz oben (vor allem anderen!)
        lang_frame = QFrame()
        lang_frame.setObjectName("DisclaimerLangFrame")
        lang_frame.setStyleSheet(
            "QFrame#DisclaimerLangFrame { background-color: #1a222d; border: 1px solid #2e3b4e; border-radius: 8px; padding: 6px 12px; }"
        )
        h_lang = QHBoxLayout(lang_frame)
        h_lang.setContentsMargins(4, 2, 4, 2)
        h_lang.setSpacing(10)

        self.lbl_lang_prompt = QLabel()
        self.lbl_lang_prompt.setStyleSheet("color: #cfd8dc; font-weight: bold; font-size: 12px;")
        h_lang.addWidget(self.lbl_lang_prompt)

        self.btn_lang_en = QPushButton("🇬🇧 English")
        self.btn_lang_en.setCheckable(True)
        self.btn_lang_en.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lang_en.clicked.connect(lambda: self._set_language("en"))
        h_lang.addWidget(self.btn_lang_en)

        self.btn_lang_de = QPushButton("🇩🇪 Deutsch")
        self.btn_lang_de.setCheckable(True)
        self.btn_lang_de.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lang_de.clicked.connect(lambda: self._set_language("de"))
        h_lang.addWidget(self.btn_lang_de)

        h_lang.addStretch()
        layout.addWidget(lang_frame)

        # 3. Disclaimer Box (Gestylte Karte mit Warn-Akzent)
        self.card_frame = QFrame()
        self.card_frame.setObjectName("DisclaimerCard")
        self.card_frame.setStyleSheet(
            "QFrame#DisclaimerCard { background-color: #161b22; border: 1px solid #d29922; border-left: 5px solid #d29922; border-radius: 6px; padding: 14px; }"
        )
        v_card = QVBoxLayout(self.card_frame)
        v_card.setContentsMargins(12, 10, 12, 10)
        v_card.setSpacing(8)

        self.lbl_card_title = QLabel()
        self.lbl_card_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #f1c40f;")
        v_card.addWidget(self.lbl_card_title)

        self.lbl_card_text = QLabel()
        self.lbl_card_text.setWordWrap(True)
        self.lbl_card_text.setStyleSheet("font-size: 12px; color: #e6edf3; line-height: 1.4;")
        v_card.addWidget(self.lbl_card_text)

        layout.addWidget(self.card_frame)
        layout.addStretch()

        # 4. Buttons: Exit (rot/grau) & Understand (grün/blau hervorgehoben)
        h_btn = QHBoxLayout()
        h_btn.setSpacing(12)

        self.btn_exit = QPushButton()
        self.btn_exit.setFixedHeight(36)
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.setStyleSheet(
            "QPushButton { background-color: #21262d; color: #f85149; border: 1px solid #30363d; border-radius: 6px; font-weight: bold; padding: 6px 16px; font-size: 12px; }"
            "QPushButton:hover { background-color: #b62324; color: #ffffff; border-color: #f85149; }"
        )
        self.btn_exit.clicked.connect(self.reject)
        h_btn.addWidget(self.btn_exit)

        h_btn.addStretch()

        self.btn_understand = QPushButton()
        self.btn_understand.setFixedHeight(36)
        self.btn_understand.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_understand.setStyleSheet(
            "QPushButton { background-color: #238636; color: #ffffff; border: 1px solid #2ea043; border-radius: 6px; font-weight: bold; padding: 6px 20px; font-size: 13px; }"
            "QPushButton:hover { background-color: #2ea043; border-color: #3fb950; }"
        )
        self.btn_understand.clicked.connect(self.accept)
        h_btn.addWidget(self.btn_understand)

        layout.addLayout(h_btn)

    def _update_lang_button_styles(self, active_lang: str):
        active_style = (
            "QPushButton { background-color: #2980b9; color: #ffffff; font-weight: bold; "
            "border: 1px solid #5dade2; border-radius: 4px; padding: 4px 10px; }"
        )
        inactive_style = (
            "QPushButton { background-color: #1a222d; color: #8fa0b5; "
            "border: 1px solid #2e3b4e; border-radius: 4px; padding: 4px 10px; }"
            "QPushButton:hover { background-color: #242f3d; color: #cfd8dc; border-color: #3d82db; }"
        )
        if active_lang == "de":
            self.btn_lang_de.setStyleSheet(active_style)
            self.btn_lang_en.setStyleSheet(inactive_style)
            self.btn_lang_de.setChecked(True)
            self.btn_lang_en.setChecked(False)
        else:
            self.btn_lang_en.setStyleSheet(active_style)
            self.btn_lang_de.setStyleSheet(inactive_style)
            self.btn_lang_en.setChecked(True)
            self.btn_lang_de.setChecked(False)

    def _set_language(self, lang: str):
        self.current_lang = lang
        I18nEngine.get_instance().set_language(lang)
        try:
            self.system.save_settings({"language": lang})
        except Exception:
            pass
        self.retranslate_ui()

    def retranslate_ui(self):
        cur_lang = I18nEngine.get_instance().get_language()
        self._update_lang_button_styles(cur_lang)
        self.setWindowTitle(t("launcher.disclaimer_title", default="AI Development Notice & Disclaimer"))
        self.lbl_lang_prompt.setText(t("launcher.lang_selector_label", default="🌐 Language / Sprache:"))
        self.lbl_card_title.setText(t("launcher.disclaimer_heading", default="⚠️ IMPORTANT NOTICE / WICHTIGER HINWEIS"))
        self.lbl_card_text.setText(t(
            "launcher.disclaimer_text",
            default=(
                "This software was implemented with high quality standards, nevertheless it is vibe coded fully by AI only, "
                "therefore I fully understand the risks of using it. I can test and verify code correctness by using AI Tools myself. "
                "The author is not responsible for any software damage."
            )
        ))
        self.btn_exit.setText(t("launcher.btn_exit", default="✕ Exit"))
        self.btn_understand.setText(t("launcher.btn_understand", default="✓ I Understand"))


class SetupAssistantDialog(QDialog):
    def __init__(self, system_engine: SystemEngine = None, parent=None):
        super().__init__(parent)
        self.system = system_engine or SystemEngine()
        self.app_dir = current_dir
        self.repo_dir = parent_dir
        self.compiled_exe_path = ""

        # Default to current language from I18nEngine if available
        active_lang = getattr(self.system, "language", I18nEngine.get_instance().get_language())
        I18nEngine.get_instance().set_language(active_lang)

        self.setFixedSize(650, 560)
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._init_ui()
        self.retranslate_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 20, 26, 20)
        layout.setSpacing(12)

        # 1. Header
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
        self.lbl_title = QLabel()
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f1c40f;")
        v_title.addWidget(self.lbl_title)

        lbl_sub = QLabel("Leopold Walli AI Software Productions")
        lbl_sub.setStyleSheet("font-size: 12px; color: #8fa0b5; font-style: italic;")
        v_title.addWidget(lbl_sub)
        h_header.addLayout(v_title)
        h_header.addStretch()
        layout.addLayout(h_header)

        # 2. Sprache-Auswahlleiste (Prominent ganz oben)
        lang_frame = QFrame()
        lang_frame.setObjectName("LangSelectorFrame")
        lang_frame.setStyleSheet(
            "QFrame#LangSelectorFrame { background-color: #1a222d; border: 1px solid #2e3b4e; border-radius: 8px; padding: 8px 14px; }"
        )
        h_lang = QHBoxLayout(lang_frame)
        h_lang.setContentsMargins(4, 2, 4, 2)
        h_lang.setSpacing(10)

        self.lbl_lang_prompt = QLabel()
        self.lbl_lang_prompt.setStyleSheet("font-weight: bold; color: #5dade2; font-size: 13px;")
        h_lang.addWidget(self.lbl_lang_prompt)

        h_lang.addStretch()

        self.btn_lang_en = QPushButton("English (Default)")
        self.btn_lang_en.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lang_en.setCheckable(True)
        self.btn_lang_en.setFixedHeight(30)
        self.btn_lang_en.setMinimumWidth(130)
        self.btn_lang_en.clicked.connect(lambda: self._set_language("en"))
        h_lang.addWidget(self.btn_lang_en)

        self.btn_lang_de = QPushButton("Deutsch")
        self.btn_lang_de.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lang_de.setCheckable(True)
        self.btn_lang_de.setFixedHeight(30)
        self.btn_lang_de.setMinimumWidth(100)
        self.btn_lang_de.clicked.connect(lambda: self._set_language("de"))
        h_lang.addWidget(self.btn_lang_de)

        layout.addWidget(lang_frame)

        # Trenner
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2e3846; margin: 2px 0;")
        layout.addWidget(sep)

        # Beschreibung
        self.lbl_desc = QLabel()
        self.lbl_desc.setStyleSheet("font-size: 13px; color: #cfd8dc; font-weight: 500;")
        layout.addWidget(self.lbl_desc)

        # Card 1: Direktstart (Python)
        self.card_direct = QFrame()
        self.card_direct.setObjectName("CardDirect")
        self.card_direct.setStyleSheet(
            "QFrame#CardDirect { background-color: #1a222d; border: 1px solid #2e3b4e; border-radius: 8px; padding: 10px; }"
            "QFrame#CardDirect:hover { border: 1px solid #3d82db; }"
        )
        v_card1 = QVBoxLayout(self.card_direct)
        v_card1.setSpacing(6)

        self.lbl_c1_title = QLabel()
        self.lbl_c1_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #5dade2;")
        v_card1.addWidget(self.lbl_c1_title)

        self.lbl_c1_desc = QLabel()
        self.lbl_c1_desc.setWordWrap(True)
        self.lbl_c1_desc.setStyleSheet("color: #a0b2c6; font-size: 12px;")
        v_card1.addWidget(self.lbl_c1_desc)

        h_c1_actions = QHBoxLayout()
        self.btn_direct = QPushButton()
        self.btn_direct.setObjectName("PrimaryButton")
        self.btn_direct.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_direct.clicked.connect(self._start_direct)
        h_c1_actions.addWidget(self.btn_direct)

        self.btn_shortcut_bat = QPushButton("📌 Desktop-Icon (BAT)")
        self.btn_shortcut_bat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_shortcut_bat.clicked.connect(self._create_bat_shortcut)
        h_c1_actions.addWidget(self.btn_shortcut_bat)

        v_card1.addLayout(h_c1_actions)
        layout.addWidget(self.card_direct)

        # Card 2: Lokale .exe erstellen
        self.card_exe = QFrame()
        self.card_exe.setObjectName("CardExe")
        self.card_exe.setStyleSheet(
            "QFrame#CardExe { background-color: #1a222d; border: 1px solid #2e3b4e; border-radius: 8px; padding: 10px; }"
            "QFrame#CardExe:hover { border: 1px solid #f1c40f; }"
        )
        v_card2 = QVBoxLayout(self.card_exe)
        v_card2.setSpacing(6)

        self.lbl_c2_title = QLabel()
        self.lbl_c2_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f1c40f;")
        v_card2.addWidget(self.lbl_c2_title)

        self.lbl_c2_desc = QLabel()
        self.lbl_c2_desc.setWordWrap(True)
        self.lbl_c2_desc.setStyleSheet("color: #a0b2c6; font-size: 12px;")
        v_card2.addWidget(self.lbl_c2_desc)

        self.btn_compile = QPushButton()
        self.btn_compile.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_compile.clicked.connect(self._start_compilation)
        v_card2.addWidget(self.btn_compile)

        layout.addWidget(self.card_exe)

        # Progress
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

        # Footer
        h_footer = QHBoxLayout()
        h_footer.addStretch()
        self.btn_close = QPushButton()
        self.btn_close.setFixedWidth(150)
        self.btn_close.clicked.connect(self.close)
        h_footer.addWidget(self.btn_close)
        layout.addLayout(h_footer)

    def _update_lang_button_styles(self, active_lang: str):
        active_style = (
            "QPushButton { background-color: #2980b9; color: #ffffff; font-weight: bold; "
            "border: 1px solid #5dade2; border-radius: 4px; padding: 4px 10px; }"
        )
        inactive_style = (
            "QPushButton { background-color: #1a222d; color: #8fa0b5; "
            "border: 1px solid #2e3b4e; border-radius: 4px; padding: 4px 10px; }"
            "QPushButton:hover { background-color: #242f3d; color: #cfd8dc; border-color: #3d82db; }"
        )
        if active_lang == "de":
            self.btn_lang_de.setStyleSheet(active_style)
            self.btn_lang_en.setStyleSheet(inactive_style)
            self.btn_lang_de.setChecked(True)
            self.btn_lang_en.setChecked(False)
        else:
            self.btn_lang_en.setStyleSheet(active_style)
            self.btn_lang_de.setStyleSheet(inactive_style)
            self.btn_lang_en.setChecked(True)
            self.btn_lang_de.setChecked(False)

    def retranslate_ui(self):
        cur_lang = I18nEngine.get_instance().get_language()
        self._update_lang_button_styles(cur_lang)

        self.setWindowTitle(t("launcher.dialog_title", default="Settlers 6 ModManager - Setup Assistant"))
        self.lbl_title.setText(t("launcher.setup_heading", default="THE SETTLERS 6 - SETUP ASSISTANT"))
        self.lbl_lang_prompt.setText(t("launcher.lang_selector_label", default="Setup Language / Sprache:"))
        self.lbl_desc.setText(t("launcher.choose_mode_desc", default="Choose how you want to run the ModManager on this PC:"))

        self.lbl_c1_title.setText(t("launcher.mode_direct_title", default="Direct Launch (Python)"))
        self.lbl_c1_desc.setText(t("launcher.mode_direct_desc", default="Launches the ModManager directly from source code. Instant start, maximum safety, no wait time."))
        self.btn_direct.setText(t("launcher.btn_direct", default="Launch Directly Now"))
        self.btn_shortcut_bat.setText("Desktop Shortcut (BAT)" if cur_lang == "en" else "Desktop-Verknuepfung (BAT)")

        self.lbl_c2_title.setText(t("launcher.mode_exe_title", default="Build Local S6ModManager.exe"))
        self.lbl_c2_desc.setText(t("launcher.mode_exe_desc", default="Compiles a standalone Windows application (.exe) directly on this PC. Starts via double-click without Windows SmartScreen warnings."))

        existing_exe = os.path.join(self.app_dir, "dist", "S6ModManager", "S6ModManager.exe") if os.path.exists(os.path.join(self.app_dir, "dist", "S6ModManager", "S6ModManager.exe")) else os.path.join(self.repo_dir, "dist", "S6ModManager", "S6ModManager.exe")
        if os.path.exists(existing_exe):
            self.btn_compile.setText(t("launcher.btn_launch_exe", default="Launch S6ModManager.exe Now"))
        else:
            self.btn_compile.setText(t("launcher.btn_compile", default="Compile .exe & Create Desktop Icon"))

        self.btn_close.setText(t("common.close", default="Close / Beenden"))

    def _set_language(self, lang: str):
        I18nEngine.get_instance().set_language(lang)
        try:
            self.system.save_settings({"language": lang})
        except Exception as e:
            print(f"[Warning] Could not persist language: {e}")
        self.retranslate_ui()

    def _start_direct(self):
        # Startet den ModManager direkt via Python und schliesst den Assistenten
        if os.path.exists(os.path.join(self.app_dir, "main.py")):
            main_py = os.path.join(self.app_dir, "main.py")
        else:
            main_py = os.path.join(self.repo_dir, "ModManager", "main.py")
        python_exe = sys.executable
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | (subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0)
        subprocess.Popen(
            [python_exe, main_py],
            cwd=os.path.dirname(main_py),
            creationflags=flags,
            close_fds=True
        )
        self.accept()

    def _create_bat_shortcut(self):
        bat_file = os.path.join(self.app_dir, "START_MOD_MANAGER.bat")
        if not os.path.exists(bat_file):
            bat_file = os.path.join(self.repo_dir, "START_MOD_MANAGER.bat")
        if not os.path.exists(bat_file):
            bat_file = os.path.join(os.path.dirname(self.repo_dir), "START_MOD_MANAGER.bat")
        if not os.path.exists(bat_file):
            return
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop, "Die Siedler 6 Mod Manager.lnk")
        icon_path = os.path.join(self.app_dir, "assets", "icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(self.repo_dir, "ModManager", "assets", "icon.ico")
        ps_cmd = (
            f"$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{shortcut_path}'); "
            f"$s.TargetPath = '{bat_file}'; "
            f"$s.WorkingDirectory = '{os.path.dirname(bat_file)}'; "
            f"$s.IconLocation = '{icon_path}'; "
            f"$s.Save()"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
        QMessageBox.information(self, "Shortcut Created", "Desktop shortcut created successfully!")

    def _start_compilation(self):
        existing_exe = os.path.join(self.app_dir, "dist", "S6ModManager", "S6ModManager.exe") if os.path.exists(os.path.join(self.app_dir, "dist", "S6ModManager", "S6ModManager.exe")) else os.path.join(self.repo_dir, "dist", "S6ModManager", "S6ModManager.exe")
        if os.path.exists(existing_exe):
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | (subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0)
            subprocess.Popen(
                [existing_exe],
                cwd=os.path.dirname(existing_exe),
                creationflags=flags,
                close_fds=True
            )
            self.accept()
            return

        self.btn_direct.setEnabled(False)
        self.btn_shortcut_bat.setEnabled(False)
        self.btn_compile.setEnabled(False)
        self.btn_close.setEnabled(False)
        self.combo_lang.setEnabled(False)
        self.progress_bar.show()
        self.lbl_progress_status.show()

        target_dir = self.app_dir if os.path.exists(os.path.join(self.app_dir, "main.py")) else self.repo_dir
        self.worker = CompilationWorker(target_dir)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._compilation_finished)
        self.worker.start()

    def _update_progress(self, val: int, text: str):
        self.progress_bar.setValue(val)
        self.lbl_progress_status.setText(text)

    def _compilation_finished(self, success: bool, error: str, exe_path: str):
        self.btn_close.setEnabled(True)
        self.combo_lang.setEnabled(True)
        if success:
            self.compiled_exe_path = exe_path
            self.lbl_progress_status.setText(t("launcher.compile_success", default="S6ModManager.exe created!"))
            self.btn_compile.setText(t("launcher.btn_launch_exe", default="Launch S6ModManager.exe Now"))
            self.btn_compile.setObjectName("PrimaryButton")
            self.btn_compile.style().unpolish(self.btn_compile)
            self.btn_compile.style().polish(self.btn_compile)
            self.btn_compile.setEnabled(True)
            self.btn_compile.clicked.disconnect()
            self.btn_compile.clicked.connect(self._launch_compiled_exe)
        else:
            self.btn_direct.setEnabled(True)
            self.btn_shortcut_bat.setEnabled(True)
            self.btn_compile.setEnabled(True)
            self.btn_compile.setText(t("launcher.btn_compile", default="Try Again"))
            QMessageBox.critical(
                self,
                "Compilation Error",
                f"{t('launcher.compile_error', default='Error during compilation:')}\n\n{error}\n\nYou can always run the manager directly via Python."
            )

    def _launch_compiled_exe(self):
        if self.compiled_exe_path and os.path.exists(self.compiled_exe_path):
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | (subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0)
            subprocess.Popen(
                [self.compiled_exe_path],
                cwd=os.path.dirname(self.compiled_exe_path),
                creationflags=flags,
                close_fds=True
            )
            self.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Settlers 6 ModManager Setup")

    # QSS Stylesheet laden
    theme_path = os.path.join(current_dir, "styles", "theme.qss")
    if os.path.exists(theme_path):
        with open(theme_path, "r", encoding="utf-8") as f:
            theme_str = f.read()
            styles_abs_dir = os.path.join(current_dir, "styles").replace("\\", "/")
            theme_str = theme_str.replace("ModManager/styles", styles_abs_dir)
            app.setStyleSheet(theme_str)

    icon_path = os.path.join(current_dir, "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    system = SystemEngine()
    disclaimer = DisclaimerDialog(system_engine=system)
    if disclaimer.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    dlg = SetupAssistantDialog(system_engine=system)
    dlg.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

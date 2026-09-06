"""
Siedler 6 Mod Manager - Hauptfenster (MainWindow)
Verbindet alle 4 Registerkarten, Header-Statusanzeigen und Live-Log-Konsole.
"""

import os
import sys
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QFrame, QPlainTextEdit, QStatusBar, QPushButton,
    QMessageBox, QInputDialog, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSlot, QProcess, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QCloseEvent, QIcon

from ModManager.engines.system_engine import SystemEngine
from ModManager.engines.config_engine import ConfigEngine
from ModManager.engines.scenario_engine import ScenarioEngine
from ModManager.engines.sandbox_engine import SandboxEngine
from ModManager.engines.i18n_engine import t

from ModManager.tab_config import ConfigTab
from ModManager.tab_scenarios import ScenarioTab
from ModManager.tab_sandbox import SandboxTab
from ModManager.tab_system import SystemTab
from ModManager.dialog_settings import SettingsDialog


class GameProcessWatcher(QThread):
    """Hintergrund-Thread, der auf das Beenden des Spielprozesses wartet, ohne die GUI zu blockieren."""
    game_finished = pyqtSignal(int)

    def __init__(self, exe_path: str, cwd: str, parent=None):
        super().__init__(parent)
        self.exe_path = exe_path
        self.cwd = cwd

    def run(self):
        try:
            proc = subprocess.Popen([self.exe_path], cwd=self.cwd)
            ret = proc.wait()
            self.game_finished.emit(ret)
        except Exception as e:
            print(f"[Error] Game process failed to run: {e}")
            self.game_finished.emit(-1)


class MainWindow(QMainWindow):
    """Das zentrale Hauptfenster des Siedler 6 Mod & Map Managers."""

    def __init__(self):
        super().__init__()
        # Engines initialisieren (SystemEngine lädt settings.json & initialisiert Sprachauswahl)
        self.system_engine = SystemEngine()
        self.config_engine = ConfigEngine(self.system_engine)
        self.scenario_engine = ScenarioEngine(self.system_engine)
        self.sandbox_engine = SandboxEngine(self.system_engine)

        self.setWindowTitle(t("app.title"))
        self.setMinimumSize(1024, 720)
        self.resize(self.system_engine.window_width, self.system_engine.window_height)

        self._tab_loaded = {}  # Tracking: welche Tabs wurden bereits geladen?
        self._init_ui()
        self._apply_windows_taskbar_icon()
        self.log(t("app.initialized"), "info")
        self._update_header_status()

    def _init_ui(self):
        self._init_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Frame
        header = QFrame()
        header.setObjectName("HeaderFrame")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 16, 12)

        # Titel & Untertitel
        v_title = QVBoxLayout()
        lbl_title = QLabel(t("app.header_title"))
        lbl_title.setObjectName("HeaderTitle")
        v_title.addWidget(lbl_title)

        lbl_sub = QLabel(t("app.header_subtitle"))
        lbl_sub.setObjectName("HeaderSubtitle")
        v_title.addWidget(lbl_sub)
        h_layout.addLayout(v_title)

        h_layout.addStretch()

        # Direkt-Start Buttons für Hauptspiel & Addon
        self.btn_launch_base = QPushButton("👑 " + t("app.btn_launch_base"))
        self.btn_launch_base.setObjectName("HeaderLaunchBase")
        self.btn_launch_base.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_launch_base.setToolTip(t("app.tt_launch_base"))
        self.btn_launch_base.clicked.connect(lambda: self._launch_game(is_addon=False))
        h_layout.addWidget(self.btn_launch_base)

        self.btn_launch_addon = QPushButton("✨ " + t("app.btn_launch_addon"))
        self.btn_launch_addon.setObjectName("HeaderLaunchAddon")
        self.btn_launch_addon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_launch_addon.setToolTip(t("app.tt_launch_addon"))
        self.btn_launch_addon.clicked.connect(lambda: self._launch_game(is_addon=True))
        h_layout.addWidget(self.btn_launch_addon)

        h_layout.addSpacing(20)

        # Global Status Pill
        self.lbl_global_status = QLabel()
        h_layout.addWidget(self.lbl_global_status)

        main_layout.addWidget(header)

        # 2. Haupt-Registerkarten (QTabWidget)
        self.tab_widget = QTabWidget()
        self.tab_widget.setContentsMargins(10, 10, 10, 0)

        # Tabs instanziieren
        self.tab_config = ConfigTab(self.config_engine, self.system_engine)
        self.tab_scenarios = ScenarioTab(self.scenario_engine, self.system_engine)
        self.tab_sandbox = SandboxTab(self.sandbox_engine, self.system_engine)
        self.tab_system = SystemTab(self.system_engine)

        # Signale verbinden
        self.tab_config.status_message.connect(self.log)
        self.tab_scenarios.status_message.connect(self.log)
        self.tab_sandbox.status_message.connect(self.log)
        self.tab_system.status_message.connect(self.log)

        # Tabs hinzufügen
        self.tab_widget.addTab(self.tab_config, t("tabs.config"))
        self.tab_widget.addTab(self.tab_scenarios, t("tabs.scenarios"))
        self.tab_widget.addTab(self.tab_sandbox, t("tabs.sandbox"))
        self.tab_widget.addTab(self.tab_system, t("tabs.system"))

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tab_widget, 1)

        # 3. Log-Konsole & Statuszeile am unteren Rand
        log_frame = QFrame()
        log_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        log_frame.setContentsMargins(10, 5, 10, 8)
        v_log = QVBoxLayout(log_frame)
        v_log.setContentsMargins(0, 0, 0, 0)
        v_log.setSpacing(4)

        h_log_header = QHBoxLayout()
        h_log_header.addWidget(QLabel(t("app.log_title")))
        h_log_header.addStretch()

        btn_clear_log = QPushButton(t("app.clear_log"))
        btn_clear_log.clicked.connect(lambda: self.log_console.clear())
        h_log_header.addWidget(btn_clear_log)
        v_log.addLayout(h_log_header)

        self.log_console = QPlainTextEdit()
        self.log_console.setObjectName("LogConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setMinimumHeight(80)
        self.log_console.setMaximumHeight(90)
        v_log.addWidget(self.log_console)

        main_layout.addWidget(log_frame)

        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(t("app.ready"))

    def _update_header_status(self):
        status, patcher_details = self.system_engine.check_s6patcher_integrity()
        if status == "OK":
            self.lbl_global_status.setText(t("app.status_ok"))
            self.lbl_global_status.setObjectName("BadgeSuccess")
        else:
            self.lbl_global_status.setText(t("app.status_error"))
            self.lbl_global_status.setObjectName("BadgeError")
            # Log details if missing
            self.log(t("app.status_error_log", status=status), "error")

        self.lbl_global_status.style().unpolish(self.lbl_global_status)
        self.lbl_global_status.style().polish(self.lbl_global_status)

    def _on_tab_changed(self, index: int):
        """Wird ausgelöst, wenn der Benutzer einen Tab wechselt."""
        if index == 1 and not self._tab_loaded.get(1):
            self.tab_scenarios.refresh_maps()
            self._tab_loaded[1] = True
        elif index == 2 and not self._tab_loaded.get(2):
            self.tab_sandbox.refresh_maps()
            self._tab_loaded[2] = True
        elif index == 3 and not self._tab_loaded.get(3):
            self.tab_system.refresh_all()
            self._tab_loaded[3] = True

    def _launch_game(self, is_addon: bool):
        """Startet das Hauptspiel oder das Addon, blendet den Mod Manager aus und stellt ihn nach Spielende wieder her."""
        game_dir = self.system_engine.game_path
        if is_addon:
            game_name = t("app.game_name_addon")
            candidates = [
                os.path.join(game_dir, "extra1", "bin", "Settlers6.exe"),
                os.path.join(game_dir, "Play Settlers 6 - The Eastern Realm.exe")
            ]
        else:
            game_name = t("app.game_name_base")
            candidates = [
                os.path.join(game_dir, "base", "bin", "Settlers6.exe"),
                os.path.join(game_dir, "Play Settlers 6.exe")
            ]

        target_exe = None
        for c in candidates:
            if os.path.exists(c):
                target_exe = c
                break

        if not target_exe:
            err_msg = t("app.err_game_not_found").format(path=candidates[0])
            self.log(err_msg, "error")
            QMessageBox.critical(self, t("app.error"), err_msg)
            return

        working_dir = os.path.dirname(target_exe)
        self.log(t("app.msg_game_starting").format(name=game_name), "info")

        # Fenster ausblenden
        self.hide()

        # Hintergrund-Überwachung starten
        self._game_watcher = GameProcessWatcher(target_exe, working_dir, self)
        self._game_watcher.game_finished.connect(self._on_game_finished)
        self._game_watcher.start()

    def _apply_windows_taskbar_icon(self):
        """Sendet explizit WM_SETICON (Small & Big) via Win32 API direkt an das HWND,
        damit die Windows 10/11 Shell-Taskleiste das Icon auch nach hide()/show() zuverlaessig anzeigt."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x00000010

            icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "icon.ico"))
            if not os.path.exists(icon_path):
                return

            hwnd = int(self.winId())
            hicon_small = user32.LoadImageW(None, icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
            hicon_big = user32.LoadImageW(None, icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
            if hicon_small:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
            if hicon_big:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
        except Exception as e:
            print(f"[Warning] Failed to apply native Win32 icon: {e}")

    def _on_game_finished(self, exit_code: int):
        """Wird automatisch aufgerufen, sobald der Spielprozess beendet wurde."""
        # 1. Fenster wiederherstellen
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.raise_()
        self.activateWindow()

        # 2. Qt-Icon auf Window und Application setzen
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "icon.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            app_inst = QApplication.instance()
            if app_inst:
                app_inst.setWindowIcon(QIcon(icon_path))

        # 3. Natives Win32 WM_SETICON an HWND senden (sofort und zeitverzoegert nach DWM Taskbar Re-registration)
        self._apply_windows_taskbar_icon()
        QTimer.singleShot(150, self._apply_windows_taskbar_icon)
        QTimer.singleShot(500, self._apply_windows_taskbar_icon)

        self.log(t("app.msg_game_closed").format(code=exit_code), "success" if exit_code == 0 else "info")

        # Nach Spielende: Aktive ModLoader-Konfiguration neu einlesen
        try:
            active_config = self.config_engine.read_active_config_from_modloader()
            self.tab_config._apply_data_to_widgets(active_config)
        except Exception:
            pass

    @pyqtSlot(str, str)
    def log(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        symbol = symbols.get(level, "•")
        log_entry = f"[{timestamp}] {symbol} {message}"
        self.log_console.appendPlainText(log_entry)
        self.statusBar().showMessage(message, 5000)

    # -------------------------------------------------------------------------
    # Menüleisten-Aktionen
    # -------------------------------------------------------------------------

    def _init_menu_bar(self):
        menubar = self.menuBar()

        # 1. Start-Menü
        menu_start = menubar.addMenu(t("menu.start"))

        act_load = menu_start.addAction(t("menu.load_preset"))
        act_load.triggered.connect(self._on_menu_load_preset)

        act_save = menu_start.addAction(t("menu.save_preset"))
        act_save.triggered.connect(self._on_menu_save_preset)

        menu_start.addSeparator()

        act_restart = menu_start.addAction(t("menu.restart"))
        act_restart.triggered.connect(self._on_menu_restart)

        act_exit = menu_start.addAction(t("menu.exit"))
        act_exit.triggered.connect(self.close)

        # 2. Einstellungen-Aktion
        act_settings = menubar.addAction(t("menu.settings"))
        act_settings.triggered.connect(self._on_menu_general_settings)

        # 3. Hilfe-Aktion
        act_help = menubar.addAction(t("menu.help"))
        act_help.triggered.connect(self._on_menu_about)

    def _on_menu_load_preset(self):
        self.tab_widget.setCurrentIndex(0)
        presets = self.config_engine.list_presets()
        if not presets:
            QMessageBox.information(self, t("dialogs.load_preset_title"), t("dialogs.no_presets"))
            return
        items = [f"{p['name']} ({p['filename']})" for p in presets]
        chosen, ok = QInputDialog.getItem(self, t("dialogs.load_preset_title"), t("dialogs.load_preset_prompt"), items, 0, False)
        if ok and chosen:
            for p in presets:
                if chosen.startswith(p['name']):
                    self.tab_config.load_preset_by_filename(p['filename'])
                    break

    def _on_menu_save_preset(self):
        self.tab_widget.setCurrentIndex(0)
        self.tab_config._on_save_preset()

    def _on_menu_restart(self):
        reply = QMessageBox.question(
            self,
            t("dialogs.restart_title"),
            t("dialogs.restart_prompt"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.log("Restarting...", "info")
            QProcess.startDetached(sys.executable, sys.argv)
            self.close()

    def _on_menu_general_settings(self):
        dlg = SettingsDialog(self.system_engine, self)
        dlg.exec()

    def _on_menu_about(self):
        QMessageBox.about(
            self,
            t("dialogs.about_title"),
            t("dialogs.about_text")
        )

    def closeEvent(self, event: QCloseEvent):
        """Wird aufgerufen, wenn das Fenster geschlossen wird."""
        try:
            self.system_engine.save_settings({
                "window_width": self.width(),
                "window_height": self.height()
            })
        except Exception as e:
            print(f"Failed to save window geometry: {e}")
        event.accept()

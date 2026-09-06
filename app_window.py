"""
Siedler 6 Mod Manager - Hauptfenster (MainWindow)
Verbindet alle 4 Registerkarten, Header-Statusanzeigen und Live-Log-Konsole.
"""

import os
import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QFrame, QPlainTextEdit, QStatusBar, QPushButton,
    QMessageBox, QInputDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSlot, QProcess
from PyQt6.QtGui import QCloseEvent

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
        self._update_header_status()
        # Nur neu laden wenn Tab noch nicht initial geladen wurde
        if index == 1 and not self._tab_loaded.get(1):
            self.tab_scenarios.refresh_maps()
            self._tab_loaded[1] = True
        elif index == 2 and not self._tab_loaded.get(2):
            self.tab_sandbox.refresh_maps()
            self._tab_loaded[2] = True
        elif index == 3 and not self._tab_loaded.get(3):
            self.tab_system.refresh_all()
            self._tab_loaded[3] = True

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

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
    QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSlot, QProcess

from ModManager.engines.system_engine import SystemEngine
from ModManager.engines.config_engine import ConfigEngine
from ModManager.engines.scenario_engine import ScenarioEngine
from ModManager.engines.sandbox_engine import SandboxEngine

from ModManager.tab_config import ConfigTab
from ModManager.tab_scenarios import ScenarioTab
from ModManager.tab_sandbox import SandboxTab
from ModManager.tab_system import SystemTab
from ModManager.dialog_settings import SettingsDialog


class MainWindow(QMainWindow):
    """Das zentrale Hauptfenster des Siedler 6 Mod & Map Managers."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Die Siedler 6 - Mod & Map Manager (S6Patcher Edition)")
        self.setMinimumSize(1024, 720)
        self.resize(1120, 780)

        # Engines initialisieren
        self.system_engine = SystemEngine()
        self.config_engine = ConfigEngine(self.system_engine)
        self.scenario_engine = ScenarioEngine(self.system_engine)
        self.sandbox_engine = SandboxEngine(self.system_engine)

        self._tab_loaded = {}  # Tracking: welche Tabs wurden bereits geladen?
        self._init_ui()
        self.log("Anwendung erfolgreich initialisiert.", "info")
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
        lbl_title = QLabel("👑 DIE SIEDLER 6 • MOD & MAP MANAGER")
        lbl_title.setObjectName("HeaderTitle")
        v_title.addWidget(lbl_title)

        lbl_sub = QLabel("S6Patcher ModLoader • Live Config & Limits • Szenario Switcher • Sandbox Injektor")
        lbl_sub.setObjectName("HeaderSubtitle")
        v_title.addWidget(lbl_sub)
        h_layout.addLayout(v_title)

        h_layout.addStretch()

        # Status Pills
        self.lbl_admin_badge = QLabel()
        h_layout.addWidget(self.lbl_admin_badge)

        self.lbl_patcher_badge = QLabel()
        h_layout.addWidget(self.lbl_patcher_badge)

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
        self.tab_widget.addTab(self.tab_config, "⚙️ Konfigurationen & Limits")
        self.tab_widget.addTab(self.tab_scenarios, "🗺️ Karten & Szenario-Varianten")
        self.tab_widget.addTab(self.tab_sandbox, "🧪 Testmap & Sandbox-Injektor")
        self.tab_widget.addTab(self.tab_system, "🛡️ System & ModLoader-Status")

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tab_widget, 1)

        # 3. Log-Konsole & Statuszeile am unteren Rand
        log_frame = QFrame()
        log_frame.setContentsMargins(10, 5, 10, 8)
        v_log = QVBoxLayout(log_frame)
        v_log.setContentsMargins(0, 0, 0, 0)
        v_log.setSpacing(4)

        h_log_header = QHBoxLayout()
        h_log_header.addWidget(QLabel("📋 Ereignis- & Aktionsprotokoll:"))
        h_log_header.addStretch()

        btn_clear_log = QPushButton("🧹 Log leeren")
        btn_clear_log.setMaximumHeight(22)
        btn_clear_log.clicked.connect(lambda: self.log_console.clear())
        h_log_header.addWidget(btn_clear_log)
        v_log.addLayout(h_log_header)

        self.log_console = QPlainTextEdit()
        self.log_console.setObjectName("LogConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(90)
        v_log.addWidget(self.log_console)

        main_layout.addWidget(log_frame)

        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Bereit.")

    def _update_header_status(self):
        # Admin Status
        if self.system_engine.is_admin():
            self.lbl_admin_badge.setText("  🟢 Administrator (UAC Aktiv)  ")
            self.lbl_admin_badge.setObjectName("BadgeSuccess")
        else:
            self.lbl_admin_badge.setText("  🟡 Eingeschränkte Rechte  ")
            self.lbl_admin_badge.setObjectName("BadgeWarning")
        self.lbl_admin_badge.style().unpolish(self.lbl_admin_badge)
        self.lbl_admin_badge.style().polish(self.lbl_admin_badge)

        # S6Patcher Status
        status, _ = self.system_engine.check_s6patcher_integrity()
        if status == "OK":
            self.lbl_patcher_badge.setText("  🛡️ S6Patcher: Bereit & Geschützt  ")
            self.lbl_patcher_badge.setObjectName("BadgeSuccess")
        else:
            self.lbl_patcher_badge.setText("  ⚠️ S6Patcher: Unvollständig  ")
            self.lbl_patcher_badge.setObjectName("BadgeWarning")
        self.lbl_patcher_badge.style().unpolish(self.lbl_patcher_badge)
        self.lbl_patcher_badge.style().polish(self.lbl_patcher_badge)

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
        menu_start = menubar.addMenu("▶ Start")

        act_load = menu_start.addAction("📂 Preset laden...")
        act_load.triggered.connect(self._on_menu_load_preset)

        act_save = menu_start.addAction("💾 Preset speichern unter...")
        act_save.triggered.connect(self._on_menu_save_preset)

        menu_start.addSeparator()

        act_restart = menu_start.addAction("🔄 Manager neu starten")
        act_restart.triggered.connect(self._on_menu_restart)

        act_exit = menu_start.addAction("🚪 Beenden")
        act_exit.triggered.connect(self.close)

        # 2. Einstellungen-Menü
        menu_settings = menubar.addMenu("⚙️ Einstellungen")
        act_general_settings = menu_settings.addAction("🔧 Allgemeine Einstellungen...")
        act_general_settings.triggered.connect(self._on_menu_general_settings)

        # 3. Hilfe-Menü
        menu_help = menubar.addMenu("❓ Hilfe")
        act_about = menu_help.addAction("ℹ️ Über Siedler 6 Mod & Map Manager...")
        act_about.triggered.connect(self._on_menu_about)

    def _on_menu_load_preset(self):
        self.tab_widget.setCurrentIndex(0)
        presets = self.config_engine.list_presets()
        if not presets:
            QMessageBox.information(self, "Presets", "Keine Presets im Verzeichnis gefunden.")
            return
        items = [f"{p['name']} ({p['filename']})" for p in presets]
        chosen, ok = QInputDialog.getItem(self, "Preset laden", "Wähle ein Preset-Profil:", items, 0, False)
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
            "Manager neu starten",
            "Möchtest du den Siedler 6 Mod & Map Manager jetzt neu starten?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.log("Starte Siedler 6 Mod Manager neu...", "info")
            QProcess.startDetached(sys.executable, sys.argv)
            self.close()

    def _on_menu_general_settings(self):
        dlg = SettingsDialog(self.system_engine, self)
        dlg.exec()

    def _on_menu_about(self):
        QMessageBox.about(
            self,
            "Über Siedler 6 Mod & Map Manager",
            "<h3>👑 DIE SIEDLER 6 • MOD & MAP MANAGER</h3>"
            "<p><b>Version:</b> 1.1 (S6Patcher Edition)</p>"
            "<p>Modernes Werkzeug zur Verwaltung von Konfigurationen, Spiel-Limits, "
            "Szenario-Varianten und Test-Maps für <i>Die Siedler: Aufstieg eines Königreichs</i>.</p>"
            "<hr>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Live XML-Editor mit Vanilla-Referenzwerten & Lightroom-Revert</li>"
            "<li>Szenario-Karten-Switcher mit Backup-Sicherheit</li>"
            "<li>Sandbox-Testmap Lua-Injektor</li>"
            "<li>S6Patcher Integritätskontrolle</li>"
            "</ul>"
            "<p style='color:#9aa5b8;'>Entwickelt für die Siedler 6 Modding Community.</p>"
        )


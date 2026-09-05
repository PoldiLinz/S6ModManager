"""
Siedler 6 Mod Manager - Dialog: Allgemeine Einstellungen
Ermöglicht das Einsehen und Verwalten der Spiel- und Mod-Pfade sowie des Systemstatus.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QGroupBox, QFileDialog
)
from PyQt6.QtCore import Qt

from ModManager.engines.system_engine import SystemEngine


class SettingsDialog(QDialog):
    """Dialog zur Anzeige und Verwaltung der allgemeinen Einstellungen & Pfade."""

    def __init__(self, system_engine: SystemEngine, parent=None):
        super().__init__(parent)
        self.system = system_engine
        self.setWindowTitle("⚙️ Allgemeine Einstellungen & Pfade")
        self.setMinimumWidth(780)
        self.resize(840, 500)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Titel-Bereich
        lbl_title = QLabel("⚙️ Allgemeine Einstellungen")
        lbl_title.setObjectName("SectionHeader")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Hier kannst du die Verzeichnisse für Spiel, Maps und Modifikationen anpassen und durchsuchen.")
        lbl_sub.setObjectName("DimLabel")
        layout.addWidget(lbl_sub)

        # 1. Pfade
        box_paths = QGroupBox("Verzeichnisse & Speicherorte")
        g_paths = QGridLayout(box_paths)
        g_paths.setSpacing(10)

        # A. Spielverzeichnis
        g_paths.addWidget(QLabel("Spielverzeichnis:"), 0, 0)
        self.txt_game = QLineEdit(self.system.game_path)
        g_paths.addWidget(self.txt_game, 0, 1)

        btn_browse_game = QPushButton("📁 Durchsuchen...")
        btn_browse_game.setFixedWidth(125)
        btn_browse_game.clicked.connect(lambda: self._browse_folder(self.txt_game, "Spielverzeichnis auswählen", is_game=True))
        g_paths.addWidget(btn_browse_game, 0, 2)

        btn_open_game = QPushButton("↗️ Öffnen")
        btn_open_game.setFixedWidth(85)
        btn_open_game.clicked.connect(lambda: self._open_in_explorer(self.txt_game.text()))
        g_paths.addWidget(btn_open_game, 0, 3)

        # B. UserMaps
        g_paths.addWidget(QLabel("UserMaps-Ordner:"), 1, 0)
        self.txt_maps = QLineEdit(self.system.user_maps_path)
        g_paths.addWidget(self.txt_maps, 1, 1)

        btn_browse_maps = QPushButton("📁 Durchsuchen...")
        btn_browse_maps.setFixedWidth(125)
        btn_browse_maps.clicked.connect(lambda: self._browse_folder(self.txt_maps, "UserMaps-Verzeichnis auswählen"))
        g_paths.addWidget(btn_browse_maps, 1, 2)

        btn_open_maps = QPushButton("↗️ Öffnen")
        btn_open_maps.setFixedWidth(85)
        btn_open_maps.clicked.connect(lambda: self._open_in_explorer(self.txt_maps.text()))
        g_paths.addWidget(btn_open_maps, 1, 3)

        # C. ModLoader shr/mod
        g_paths.addWidget(QLabel("ModLoader-Ordner:"), 2, 0)
        self.txt_mod = QLineEdit(self.system.modloader_path)
        g_paths.addWidget(self.txt_mod, 2, 1)

        btn_browse_mod = QPushButton("📁 Durchsuchen...")
        btn_browse_mod.setFixedWidth(125)
        btn_browse_mod.clicked.connect(lambda: self._browse_folder(self.txt_mod, "ModLoader-Verzeichnis auswählen"))
        g_paths.addWidget(btn_browse_mod, 2, 2)

        btn_open_mod = QPushButton("↗️ Öffnen")
        btn_open_mod.setFixedWidth(85)
        btn_open_mod.clicked.connect(lambda: self._open_in_explorer(self.txt_mod.text()))
        g_paths.addWidget(btn_open_mod, 2, 3)

        # D. Preloaded Mods (S6Patcher Fixes)
        g_paths.addWidget(QLabel("Preloaded Mods:"), 3, 0)
        self.txt_original = QLineEdit(self.system.original_mods_path)
        g_paths.addWidget(self.txt_original, 3, 1)

        btn_browse_original = QPushButton("📁 Durchsuchen...")
        btn_browse_original.setFixedWidth(125)
        btn_browse_original.clicked.connect(lambda: self._browse_folder(self.txt_original, "Preloaded Mods Verzeichnis auswählen"))
        g_paths.addWidget(btn_browse_original, 3, 2)

        btn_open_original = QPushButton("↗️ Öffnen")
        btn_open_original.setFixedWidth(85)
        btn_open_original.clicked.connect(lambda: self._open_in_explorer(self.txt_original.text()))
        g_paths.addWidget(btn_open_original, 3, 3)

        # E. Presets
        g_paths.addWidget(QLabel("Presets-Ordner:"), 4, 0)
        self.txt_presets = QLineEdit(self.system.presets_path)
        g_paths.addWidget(self.txt_presets, 4, 1)

        btn_browse_presets = QPushButton("📁 Durchsuchen...")
        btn_browse_presets.setFixedWidth(125)
        btn_browse_presets.clicked.connect(lambda: self._browse_folder(self.txt_presets, "Presets-Verzeichnis auswählen"))
        g_paths.addWidget(btn_browse_presets, 4, 2)

        btn_open_presets = QPushButton("↗️ Öffnen")
        btn_open_presets.setFixedWidth(85)
        btn_open_presets.clicked.connect(lambda: self._open_in_explorer(self.txt_presets.text()))
        g_paths.addWidget(btn_open_presets, 4, 3)

        layout.addWidget(box_paths)

        # 2. System-Status
        box_status = QGroupBox("System- & Sicherheitsstatus")
        g_status = QGridLayout(box_status)
        g_status.setSpacing(10)

        # Admin
        g_status.addWidget(QLabel("Administratorrechte (UAC):"), 0, 0)
        self.lbl_admin = QLabel()
        g_status.addWidget(self.lbl_admin, 0, 1)

        # S6Patcher
        g_status.addWidget(QLabel("S6Patcher Schutz:"), 1, 0)
        self.lbl_patcher = QLabel()
        g_status.addWidget(self.lbl_patcher, 1, 1)

        self._refresh_status_badges()
        layout.addWidget(box_status)

        layout.addStretch()

        # Footer Buttons
        h_btn = QHBoxLayout()
        h_btn.addStretch()

        btn_save = QPushButton("💾 Einstellungen speichern")
        btn_save.setObjectName("PrimaryButton")
        btn_save.setMinimumWidth(180)
        btn_save.clicked.connect(self._save_settings)
        h_btn.addWidget(btn_save)

        btn_close = QPushButton("Schließen")
        btn_close.setMinimumWidth(110)
        btn_close.clicked.connect(self.reject)
        h_btn.addWidget(btn_close)

        layout.addLayout(h_btn)

    def _browse_folder(self, line_edit: QLineEdit, caption: str, is_game: bool = False):
        current_dir = line_edit.text().strip()
        if not os.path.exists(current_dir):
            current_dir = self.system.workspace_path

        folder = QFileDialog.getExistingDirectory(
            self,
            caption,
            current_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            folder_norm = os.path.normpath(folder)
            line_edit.setText(folder_norm)
            if is_game:
                auto_mod = os.path.normpath(os.path.join(folder_norm, "modloader", "shr", "mod"))
                self.txt_mod.setText(auto_mod)

    def _refresh_status_badges(self):
        # Admin Status
        if self.system.is_admin():
            self.lbl_admin.setText("  🟢 Aktiv - Vollzugriff auf Programme & Systemordner  ")
            self.lbl_admin.setObjectName("BadgeSuccess")
        else:
            self.lbl_admin.setText("  🟡 Eingeschränkt - Eventuell Schreibschutz im Spielordner  ")
            self.lbl_admin.setObjectName("BadgeWarning")
        self.lbl_admin.style().unpolish(self.lbl_admin)
        self.lbl_admin.style().polish(self.lbl_admin)

        # S6Patcher Status
        patcher_status, patcher_details = self.system.check_s6patcher_integrity()
        if patcher_status == "OK":
            self.lbl_patcher.setText("  🛡️ Integrität geschützt (S6Patcher aktiv)  ")
            self.lbl_patcher.setObjectName("BadgeSuccess")
        else:
            self.lbl_patcher.setText(f"  ⚠️ Status: {patcher_status} ({len(patcher_details)} ModLoader-Dateien)  ")
            self.lbl_patcher.setObjectName("BadgeWarning")
        self.lbl_patcher.style().unpolish(self.lbl_patcher)
        self.lbl_patcher.style().polish(self.lbl_patcher)

    def _save_settings(self):
        paths = {
            "game_path": self.txt_game.text().strip(),
            "user_maps_path": self.txt_maps.text().strip(),
            "modloader_path": self.txt_mod.text().strip(),
            "original_mods_path": self.txt_original.text().strip(),
            "presets_path": self.txt_presets.text().strip()
        }
        try:
            self.system.save_settings(paths)
            self._refresh_status_badges()
            QMessageBox.information(self, "Einstellungen gespeichert", "Die Verzeichnispfade wurden erfolgreich gespeichert.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Speichern", f"Die Einstellungen konnten nicht gespeichert werden:\n{e}")

    def _open_in_explorer(self, folder_path: str):
        if not folder_path or not os.path.exists(folder_path):
            QMessageBox.warning(self, "Ordner nicht gefunden", f"Das Verzeichnis existiert nicht:\n{folder_path}")
            return
        try:
            os.startfile(folder_path)
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Konnte Ordner nicht öffnen: {e}")

"""
Siedler 6 Mod Manager - Dialog: Allgemeine Einstellungen
Ermöglicht das Einsehen und Verwalten der Spiel- und Mod-Pfade sowie des Systemstatus.
"""

import os
import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QGroupBox, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt, QProcess

from ModManager.engines.system_engine import SystemEngine
from ModManager.engines.i18n_engine import t


class SettingsDialog(QDialog):
    """Dialog zur Anzeige und Verwaltung der allgemeinen Einstellungen, Sprache & Pfade."""

    def __init__(self, system_engine: SystemEngine, parent=None):
        super().__init__(parent)
        self.system = system_engine
        self._initial_language = getattr(self.system, "language", "en")
        self.setWindowTitle(t("settings.dialog_title"))
        self.setMinimumWidth(780)
        self.resize(840, 560)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Titel-Bereich
        lbl_title = QLabel(t("settings.section_title"))
        lbl_title.setObjectName("SectionHeader")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel(t("settings.section_subtitle"))
        lbl_sub.setObjectName("DimLabel")
        layout.addWidget(lbl_sub)
        
        self.lbl_global_status = QLabel()
        layout.addWidget(self.lbl_global_status)

        # 1. Sprache / Language
        box_lang = QGroupBox(t("settings.group_language"))
        h_lang = QHBoxLayout(box_lang)
        h_lang.setContentsMargins(12, 10, 12, 10)
        h_lang.setSpacing(12)

        h_lang.addWidget(QLabel(t("settings.lbl_language")))
        self.combo_lang = QComboBox()
        self.combo_lang.setFixedWidth(220)
        self.combo_lang.addItem(t("settings.lang_en"), "en")
        self.combo_lang.addItem(t("settings.lang_de"), "de")

        idx = self.combo_lang.findData(self._initial_language)
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)

        h_lang.addWidget(self.combo_lang)
        h_lang.addStretch()
        layout.addWidget(box_lang)

        # 2. Pfade
        box_paths = QGroupBox(t("settings.group_paths"))
        g_paths = QGridLayout(box_paths)
        g_paths.setSpacing(10)

        # A. Spielverzeichnis
        g_paths.addWidget(QLabel(t("settings.game_path")), 0, 0)
        self.txt_game = QLineEdit(self.system.game_path)
        g_paths.addWidget(self.txt_game, 0, 1)

        btn_browse_game = QPushButton(t("settings.btn_browse"))
        btn_browse_game.setFixedWidth(125)
        btn_browse_game.clicked.connect(lambda: self._browse_folder(self.txt_game, t("settings.browse_game_title"), is_game=True))
        g_paths.addWidget(btn_browse_game, 0, 2)

        btn_open_game = QPushButton(t("settings.btn_open"))
        btn_open_game.setFixedWidth(85)
        btn_open_game.clicked.connect(lambda: self._open_in_explorer(self.txt_game.text()))
        g_paths.addWidget(btn_open_game, 0, 3)

        # B. UserMaps
        g_paths.addWidget(QLabel(t("settings.maps_path")), 1, 0)
        self.txt_maps = QLineEdit(self.system.user_maps_path)
        g_paths.addWidget(self.txt_maps, 1, 1)

        btn_browse_maps = QPushButton(t("settings.btn_browse"))
        btn_browse_maps.setFixedWidth(125)
        btn_browse_maps.clicked.connect(lambda: self._browse_folder(self.txt_maps, t("settings.browse_maps_title")))
        g_paths.addWidget(btn_browse_maps, 1, 2)

        btn_open_maps = QPushButton(t("settings.btn_open"))
        btn_open_maps.setFixedWidth(85)
        btn_open_maps.clicked.connect(lambda: self._open_in_explorer(self.txt_maps.text()))
        g_paths.addWidget(btn_open_maps, 1, 3)

        # C. ModLoader shr/mod
        g_paths.addWidget(QLabel(t("settings.modloader_path")), 2, 0)
        self.txt_mod = QLineEdit(self.system.modloader_path)
        g_paths.addWidget(self.txt_mod, 2, 1)

        btn_browse_mod = QPushButton(t("settings.btn_browse"))
        btn_browse_mod.setFixedWidth(125)
        btn_browse_mod.clicked.connect(lambda: self._browse_folder(self.txt_mod, t("settings.browse_modloader_title")))
        g_paths.addWidget(btn_browse_mod, 2, 2)

        btn_open_mod = QPushButton(t("settings.btn_open"))
        btn_open_mod.setFixedWidth(85)
        btn_open_mod.clicked.connect(lambda: self._open_in_explorer(self.txt_mod.text()))
        g_paths.addWidget(btn_open_mod, 2, 3)

        # D. Preloaded Mods (S6Patcher Fixes)
        g_paths.addWidget(QLabel(t("settings.original_mods_path")), 3, 0)
        self.txt_original = QLineEdit(self.system.original_mods_path)
        g_paths.addWidget(self.txt_original, 3, 1)

        btn_browse_original = QPushButton(t("settings.btn_browse"))
        btn_browse_original.setFixedWidth(125)
        btn_browse_original.clicked.connect(lambda: self._browse_folder(self.txt_original, t("settings.browse_original_title")))
        g_paths.addWidget(btn_browse_original, 3, 2)

        btn_open_original = QPushButton(t("settings.btn_open"))
        btn_open_original.setFixedWidth(85)
        btn_open_original.clicked.connect(lambda: self._open_in_explorer(self.txt_original.text()))
        g_paths.addWidget(btn_open_original, 3, 3)

        # E. Presets
        g_paths.addWidget(QLabel(t("settings.presets_path")), 4, 0)
        self.txt_presets = QLineEdit(self.system.presets_path)
        g_paths.addWidget(self.txt_presets, 4, 1)

        btn_browse_presets = QPushButton(t("settings.btn_browse"))
        btn_browse_presets.setFixedWidth(125)
        btn_browse_presets.clicked.connect(lambda: self._browse_folder(self.txt_presets, t("settings.browse_presets_title")))
        g_paths.addWidget(btn_browse_presets, 4, 2)

        btn_open_presets = QPushButton(t("settings.btn_open"))
        btn_open_presets.setFixedWidth(85)
        btn_open_presets.clicked.connect(lambda: self._open_in_explorer(self.txt_presets.text()))
        g_paths.addWidget(btn_open_presets, 4, 3)
        layout.addWidget(box_paths)

        self._refresh_global_status()
        layout.addStretch()

        # Footer Buttons
        h_btn = QHBoxLayout()
        h_btn.addStretch()

        btn_save = QPushButton(t("settings.btn_save"))
        btn_save.setObjectName("PrimaryButton")
        btn_save.setMinimumWidth(180)
        btn_save.clicked.connect(self._save_settings)
        h_btn.addWidget(btn_save)

        btn_close = QPushButton(t("settings.btn_close"))
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

    def _refresh_global_status(self):
        patcher_status, patcher_details = self.system.check_s6patcher_integrity()
        if patcher_status == "OK":
            self.lbl_global_status.setText(t("app.status_ok"))
            self.lbl_global_status.setObjectName("GlobalStatusOK")
        else:
            self.lbl_global_status.setText(t("app.status_error"))
            self.lbl_global_status.setObjectName("GlobalStatusError")
            print(f"S6Patcher Error: {patcher_status}. Details:")
            for d in patcher_details:
                if d.get('status') != 'OK':
                    print(f" - {d.get('relative_path')}: {d.get('status')}")

        self.lbl_global_status.style().unpolish(self.lbl_global_status)
        self.lbl_global_status.style().polish(self.lbl_global_status)

    def _save_settings(self):
        new_lang = self.combo_lang.currentData()
        lang_changed = (new_lang != self._initial_language)

        settings_data = {
            "language": new_lang,
            "game_path": self.txt_game.text().strip(),
            "user_maps_path": self.txt_maps.text().strip(),
            "modloader_path": self.txt_mod.text().strip(),
            "original_mods_path": self.txt_original.text().strip(),
            "presets_path": self.txt_presets.text().strip()
        }
        try:
            self.system.save_settings(settings_data)
            self._refresh_global_status()

            if lang_changed:
                lang_display = self.combo_lang.currentText()
                reply = QMessageBox.question(
                    self,
                    t("dialogs.restart_required_title"),
                    t("dialogs.restart_required_prompt", lang=lang_display),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    QProcess.startDetached(sys.executable, sys.argv)
                    if self.parent():
                        self.parent().close()
                    self.accept()
                    sys.exit(0)
                else:
                    self.accept()
            else:
                QMessageBox.information(self, t("settings.saved_title"), t("settings.saved_msg"))
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, t("settings.save_error_title"), t("settings.save_error_msg", error=str(e)))

    def _open_in_explorer(self, folder_path: str):
        if not folder_path or not os.path.exists(folder_path):
            QMessageBox.warning(self, t("settings.folder_not_found_title"), t("settings.folder_not_found_msg", path=folder_path))
            return
        try:
            os.startfile(folder_path)
        except Exception as e:
            QMessageBox.warning(self, t("common.error"), t("settings.folder_open_error", error=str(e)))

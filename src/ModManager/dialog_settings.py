"""
Siedler 6 Mod Manager - Dialog: Allgemeine Einstellungen
Ermöglicht das Einsehen und Verwalten der Spiel- und Mod-Pfade sowie des Systemstatus.
"""

import os
import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QGroupBox, QFileDialog, QComboBox, QFrame
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
        self.setMinimumWidth(940)
        self.resize(1020, 520)
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
        g_paths.setVerticalSpacing(12)
        g_paths.setColumnStretch(0, 0)
        g_paths.setColumnStretch(1, 1)
        g_paths.setColumnStretch(2, 0)
        g_paths.setColumnStretch(3, 0)

        # 1. Spielverzeichnis (Game Directory)
        g_paths.addWidget(QLabel(t("settings.game_path")), 0, 0)
        self.txt_game = QLineEdit(self.system.game_path)
        self.txt_game.setCursorPosition(0)
        g_paths.addWidget(self.txt_game, 0, 1)

        btn_browse_game = QPushButton(t("settings.btn_browse"))
        btn_browse_game.setFixedWidth(125)
        btn_browse_game.clicked.connect(lambda: self._browse_folder(self.txt_game, t("settings.browse_game_title"), is_game=True))
        g_paths.addWidget(btn_browse_game, 0, 2)

        btn_open_game = QPushButton(t("settings.btn_open"))
        btn_open_game.setFixedWidth(85)
        btn_open_game.clicked.connect(lambda: self._open_in_explorer(self.txt_game.text()))
        g_paths.addWidget(btn_open_game, 0, 3)

        # 2. Modloader-Verzeichnis (Modloader Directory)
        g_paths.addWidget(QLabel(t("settings.modloader_path")), 1, 0)
        self.txt_modloader = QLineEdit(self.system.modloader_root_path)
        self.txt_modloader.setCursorPosition(0)
        g_paths.addWidget(self.txt_modloader, 1, 1)

        btn_browse_modloader = QPushButton(t("settings.btn_browse"))
        btn_browse_modloader.setFixedWidth(125)
        btn_browse_modloader.clicked.connect(lambda: self._browse_folder(self.txt_modloader, t("settings.browse_modloader_title")))
        g_paths.addWidget(btn_browse_modloader, 1, 2)

        btn_open_modloader = QPushButton(t("settings.btn_open"))
        btn_open_modloader.setFixedWidth(85)
        btn_open_modloader.clicked.connect(lambda: self._open_in_explorer(self.txt_modloader.text()))
        g_paths.addWidget(btn_open_modloader, 1, 3)

        # 3. Spieldaten / Dokumenten-Ordner (Save Game Directory)
        g_paths.addWidget(QLabel(t("settings.documents_path")), 2, 0)
        self.txt_documents = QLineEdit(self.system.documents_path)
        self.txt_documents.setCursorPosition(0)
        g_paths.addWidget(self.txt_documents, 2, 1)

        btn_browse_docs = QPushButton(t("settings.btn_browse"))
        btn_browse_docs.setFixedWidth(125)
        btn_browse_docs.clicked.connect(lambda: self._browse_folder(self.txt_documents, t("settings.browse_documents_title"), is_docs=True))
        g_paths.addWidget(btn_browse_docs, 2, 2)

        btn_open_docs = QPushButton(t("settings.btn_open"))
        btn_open_docs.setFixedWidth(85)
        btn_open_docs.clicked.connect(lambda: self._open_in_explorer(self.txt_documents.text()))
        g_paths.addWidget(btn_open_docs, 2, 3)

        # Vertikaler Trenner / Platz zwischen Spiel-/Save-Dateien und Mod-Dateien
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #2e3846; margin: 4px 0px;")
        g_paths.addWidget(sep, 3, 0, 1, 4)

        # 4. Mod-Verzeichnis / Workspace (Mod Directory)
        g_paths.addWidget(QLabel(t("settings.mod_directory")), 4, 0)
        self.txt_workspace = QLineEdit(self.system.workspace_path)
        self.txt_workspace.setCursorPosition(0)
        g_paths.addWidget(self.txt_workspace, 4, 1)

        btn_browse_ws = QPushButton(t("settings.btn_browse"))
        btn_browse_ws.setFixedWidth(125)
        btn_browse_ws.clicked.connect(lambda: self._browse_folder(self.txt_workspace, t("settings.browse_mod_dir_title")))
        g_paths.addWidget(btn_browse_ws, 4, 2)

        btn_open_ws = QPushButton(t("settings.btn_open"))
        btn_open_ws.setFixedWidth(85)
        btn_open_ws.clicked.connect(lambda: self._open_in_explorer(self.txt_workspace.text()))
        g_paths.addWidget(btn_open_ws, 4, 3)

        lbl_desc = QLabel(t("settings.workspace_desc"))
        lbl_desc.setStyleSheet("color: #8fa0b5; font-size: 11px; font-style: italic;")
        g_paths.addWidget(lbl_desc, 5, 1, 1, 3)

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

    def _browse_folder(self, line_edit: QLineEdit, caption: str, is_docs: bool = False, is_game: bool = False):
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
            norm_folder = os.path.normpath(folder)
            old_val = line_edit.text().strip()
            line_edit.setText(norm_folder)
            line_edit.setCursorPosition(0)
            if is_docs and hasattr(self, "txt_workspace"):
                old_default_ws = os.path.normpath(os.path.join(self.system.documents_path, "UserMods"))
                if self.txt_workspace.text().strip() == old_default_ws:
                    new_default_ws = os.path.normpath(os.path.join(norm_folder, "UserMods"))
                    self.txt_workspace.setText(new_default_ws)
                    self.txt_workspace.setCursorPosition(0)
            if is_game and hasattr(self, "txt_modloader"):
                old_default_ml = os.path.normpath(os.path.join(old_val, "modloader"))
                if self.txt_modloader.text().strip() == old_default_ml or not self.txt_modloader.text().strip():
                    new_default_ml = os.path.normpath(os.path.join(norm_folder, "modloader"))
                    self.txt_modloader.setText(new_default_ml)
                    self.txt_modloader.setCursorPosition(0)

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
            "modloader_path": self.txt_modloader.text().strip(),
            "documents_path": self.txt_documents.text().strip(),
            "workspace_path": self.txt_workspace.text().strip()
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
        if not folder_path:
            return
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
            except Exception:
                QMessageBox.warning(self, t("settings.folder_not_found_title"), t("settings.folder_not_found_msg", path=folder_path))
                return
        try:
            os.startfile(folder_path)
        except Exception as e:
            QMessageBox.warning(self, t("common.error"), t("settings.folder_open_error", error=str(e)))

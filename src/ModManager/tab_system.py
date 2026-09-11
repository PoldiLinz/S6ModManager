"""
Siedler 6 Mod Manager - Tab 4: System & ModLoader-Status
Überwacht S6Patcher-Schutzdateien, listet aktive ModLoader-Inhalte und verwaltet Backups.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QGroupBox, QMessageBox, QTabWidget, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, List, Any, Optional

from ModManager.engines.system_engine import SystemEngine
from ModManager.engines import t


class SystemTab(QWidget):
    """Registerkarte für System-Status, S6Patcher-Schutz und Backup-Verwaltung."""

    status_message = pyqtSignal(str, str)

    def __init__(self, system_engine: SystemEngine, parent=None):
        super().__init__(parent)
        self.system = system_engine

        self._init_ui()
        self.refresh_all()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. System Info Cards (Horizontal)
        info_card = QFrame()
        info_card.setObjectName("CardFrame")
        info_layout = QGridLayout(info_card)
        info_layout.setContentsMargins(10, 10, 10, 10)

        info_layout.addWidget(QLabel(t("system_tab.lbl_game_path")), 0, 0)
        self.lbl_game_path = QLabel(self.system.game_path)
        self.lbl_game_path.setObjectName("DimLabel")
        info_layout.addWidget(self.lbl_game_path, 0, 1)

        info_layout.addWidget(QLabel(t("system_tab.lbl_admin_status")), 0, 2)
        self.lbl_admin_badge = QLabel()
        info_layout.addWidget(self.lbl_admin_badge, 0, 3)

        info_layout.addWidget(QLabel(t("system_tab.lbl_usermaps")), 1, 0)
        self.lbl_usermaps_path = QLabel(self.system.user_maps_path)
        self.lbl_usermaps_path.setObjectName("DimLabel")
        info_layout.addWidget(self.lbl_usermaps_path, 1, 1)

        info_layout.addWidget(QLabel(t("system_tab.lbl_modloader")), 1, 2)
        self.lbl_modloader_badge = QLabel()
        info_layout.addWidget(self.lbl_modloader_badge, 1, 3)

        layout.addWidget(info_card)

        # 2. Sub-Tabs für Detailansichten
        sub_tabs = QTabWidget()
        sub_tabs.setObjectName("SubTabWidget")

        # Tab A: Aktive ModLoader-Dateien
        tab_files = QWidget()
        v_files = QVBoxLayout(tab_files)

        h_fbar = QHBoxLayout()
        h_fbar.addWidget(QLabel(t("system_tab.lbl_active_files")))
        h_fbar.addStretch()
        btn_refresh_files = QPushButton(t("system_tab.btn_reload"))
        btn_refresh_files.clicked.connect(self._refresh_modloader_files)
        h_fbar.addWidget(btn_refresh_files)
        v_files.addLayout(h_fbar)

        self.table_mod_files = QTableWidget()
        self.table_mod_files.setColumnCount(4)
        self.table_mod_files.setHorizontalHeaderLabels([t("system_tab.col_category"), t("system_tab.col_rel_file"), t("system_tab.col_size"), t("system_tab.col_modified")])
        self.table_mod_files.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        v_files.addWidget(self.table_mod_files)
        sub_tabs.addTab(tab_files, t("system_tab.tab_files"))

        # Tab B: S6Patcher Schutz-Dateien
        tab_patcher = QWidget()
        v_patcher = QVBoxLayout(tab_patcher)

        h_pbar = QHBoxLayout()
        h_pbar.addWidget(QLabel(t("system_tab.lbl_integrity")))
        h_pbar.addStretch()
        btn_refresh_patcher = QPushButton(t("system_tab.btn_check_integrity"))
        btn_refresh_patcher.clicked.connect(self._refresh_patcher_health)
        h_pbar.addWidget(btn_refresh_patcher)
        v_patcher.addLayout(h_pbar)

        self.table_patcher = QTableWidget()
        self.table_patcher.setColumnCount(4)
        self.table_patcher.setHorizontalHeaderLabels([t("system_tab.col_status"), t("system_tab.col_prot_file"), t("system_tab.col_size"), t("system_tab.col_full_path")])
        self.table_patcher.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        v_patcher.addWidget(self.table_patcher)
        sub_tabs.addTab(tab_patcher, t("system_tab.tab_patcher"))

        # Tab C: Backup & Snapshot Manager
        tab_backups = QWidget()
        v_backups = QVBoxLayout(tab_backups)

        h_bbar = QHBoxLayout()
        btn_new_backup = QPushButton(t("system_tab.btn_new_backup"))
        btn_new_backup.setObjectName("PrimaryButton")
        btn_new_backup.clicked.connect(self._on_create_backup)
        h_bbar.addWidget(btn_new_backup)

        btn_open_backups = QPushButton(t("system_tab.btn_open_backup"))
        btn_open_backups.clicked.connect(lambda: os.startfile(self.system.backups_path))
        h_bbar.addWidget(btn_open_backups)

        h_bbar.addStretch()
        btn_refresh_b = QPushButton(t("system_tab.btn_refresh"))
        btn_refresh_b.clicked.connect(self._refresh_backups)
        h_bbar.addWidget(btn_refresh_b)
        v_backups.addLayout(h_bbar)

        self.table_backups = QTableWidget()
        self.table_backups.setColumnCount(4)
        self.table_backups.setHorizontalHeaderLabels([t("system_tab.col_archive"), t("system_tab.col_size"), t("system_tab.col_created"), t("system_tab.col_actions")])
        self.table_backups.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        v_backups.addWidget(self.table_backups)
        sub_tabs.addTab(tab_backups, t("system_tab.tab_backups"))

        layout.addWidget(sub_tabs)
        
        # 3. Global Reset
        btn_force_reset = QPushButton(t("system_tab.btn_force_reset"))
        btn_force_reset.setObjectName("DangerButton")
        btn_force_reset.clicked.connect(self._on_force_reset)
        
        # Add some margin at the bottom
        layout.addSpacing(10)
        layout.addWidget(btn_force_reset)

    # -------------------------------------------------------------------------
    # Aktualisierung
    # -------------------------------------------------------------------------

    def refresh_all(self):
        # Admin Status
        is_adm = self.system.is_admin()
        if is_adm:
            self.lbl_admin_badge.setText(t("system_tab.status_admin"))
            self.lbl_admin_badge.setObjectName("BadgeSuccess")
        else:
            self.lbl_admin_badge.setText(t("system_tab.status_limited"))
            self.lbl_admin_badge.setObjectName("BadgeWarning")
        self.lbl_admin_badge.style().unpolish(self.lbl_admin_badge)
        self.lbl_admin_badge.style().polish(self.lbl_admin_badge)

        self._refresh_patcher_health()
        self._refresh_modloader_files()
        self._refresh_backups()

    def _refresh_patcher_health(self):
        status, results = self.system.check_s6patcher_integrity()
        if status == "OK":
            self.lbl_modloader_badge.setText(t("system_tab.status_ready"))
            self.lbl_modloader_badge.setObjectName("BadgeSuccess")
        elif status == "WARNING":
            self.lbl_modloader_badge.setText(t("system_tab.status_missing"))
            self.lbl_modloader_badge.setObjectName("BadgeWarning")
        else:
            self.lbl_modloader_badge.setText(t("system_tab.status_error"))
            self.lbl_modloader_badge.setObjectName("BadgeError")
        self.lbl_modloader_badge.style().unpolish(self.lbl_modloader_badge)
        self.lbl_modloader_badge.style().polish(self.lbl_modloader_badge)

        self.table_patcher.setRowCount(len(results))
        for row, item in enumerate(results):
            # Status Badge
            st_item = QTableWidgetItem(t("system_tab.status_ok") if item["exists"] else t("system_tab.status_missing_file"))
            st_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_patcher.setItem(row, 0, st_item)

            self.table_patcher.setItem(row, 1, QTableWidgetItem(item["relative_path"]))
            sz_item = QTableWidgetItem(f"{item['size_bytes']} B" if item["exists"] else "-")
            sz_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_patcher.setItem(row, 2, sz_item)
            self.table_patcher.setItem(row, 3, QTableWidgetItem(item["full_path"]))

    def _refresh_modloader_files(self):
        files = self.system.list_active_modloader_files()
        self.table_mod_files.setRowCount(len(files))

        for row, f in enumerate(files):
            cat_item = QTableWidgetItem(f["category"])
            self.table_mod_files.setItem(row, 0, cat_item)

            path_text = f["relative_path"] + (t("system_tab.protected_tag") if f["is_protected"] else "")
            self.table_mod_files.setItem(row, 1, QTableWidgetItem(path_text))

            sz_item = QTableWidgetItem(f["size_str"])
            sz_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_mod_files.setItem(row, 2, sz_item)

            self.table_mod_files.setItem(row, 3, QTableWidgetItem(f["modified"]))

    def _refresh_backups(self):
        backups = self.system.list_backups()
        self.table_backups.setRowCount(len(backups))

        for row, b in enumerate(backups):
            self.table_backups.setItem(row, 0, QTableWidgetItem(b["filename"]))
            
            sz_item = QTableWidgetItem(b["size_str"])
            sz_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_backups.setItem(row, 1, sz_item)

            self.table_backups.setItem(row, 2, QTableWidgetItem(b["created"]))

            # Action Buttons Widget
            w_act = QWidget()
            h_act = QHBoxLayout(w_act)
            h_act.setContentsMargins(2, 2, 2, 2)

            btn_rest = QPushButton(t("system_tab.btn_restore"))
            btn_rest.clicked.connect(lambda _, path=b["full_path"]: self._on_restore_backup(path))
            h_act.addWidget(btn_rest)

            btn_del = QPushButton("🗑️")
            btn_del.setObjectName("DangerButton")
            btn_del.clicked.connect(lambda _, path=b["full_path"]: self._on_delete_backup(path))
            h_act.addWidget(btn_del)

            self.table_backups.setCellWidget(row, 3, w_act)

    def _on_create_backup(self):
        name, ok = QInputDialog.getText(self, t("system_tab.title_create_backup"), t("system_tab.lbl_backup_name"))
        if ok:
            try:
                b_name = name.strip() if name.strip() else None
                zip_path = self.system.create_modloader_backup(b_name)
                msg = t("system_tab.msg_backup_success").format(name=os.path.basename(zip_path))
                self.status_message.emit(t("system_tab.log_backup_success").format(name=os.path.basename(zip_path)), "success")
                QMessageBox.information(self, t("system_tab.title_backup_created"), msg)
                self._refresh_backups()
            except Exception as e:
                err = t("system_tab.msg_backup_error").format(err=e)
                self.status_message.emit(err, "error")
                QMessageBox.critical(self, t("app.error") if t("app.error") != "app.error" else "Error", err)

    def _on_restore_backup(self, zip_path: str):
        reply = QMessageBox.question(
            self,
            t("system_tab.title_restore_backup"),
            t("system_tab.msg_restore_prompt").format(name=os.path.basename(zip_path)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                count = self.system.restore_modloader_backup(zip_path)
                msg = t("system_tab.msg_restore_success").format(count=count)
                self.status_message.emit(msg, "success")
                QMessageBox.information(self, t("system_tab.title_backup_restored"), msg)
                self.refresh_all()
            except Exception as e:
                err = t("system_tab.msg_restore_error").format(err=e)
                self.status_message.emit(err, "error")
                QMessageBox.critical(self, t("app.error") if t("app.error") != "app.error" else "Error", err)

    def _on_delete_backup(self, zip_path: str):
        reply = QMessageBox.question(
            self,
            t("system_tab.title_delete_backup"),
            t("system_tab.msg_delete_prompt").format(name=os.path.basename(zip_path)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(zip_path)
                self.status_message.emit(t("system_tab.log_backup_deleted"), "success")
                self._refresh_backups()
            except Exception as e:
                pass

    def _on_force_reset(self):
        reply = QMessageBox.question(
            self,
            t("system_tab.title_force_reset"),
            t("system_tab.msg_force_reset_prompt"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Da SystemTab keinen direkten Zugriff auf ConfigEngine hat, rufen wir es über das parent (MainWindow) auf
                # Alternativ können wir ConfigEngine hier kurz instanziieren, da es sich alle Pfade aus SystemEngine holt.
                from ModManager.engines.config_engine import ConfigEngine
                cfg = ConfigEngine(self.system)
                count = cfg.restore_vanilla_configs(force_global=True)
                
                msg = t("system_tab.msg_force_reset_success").format(count=count)
                self.status_message.emit(t("system_tab.log_force_reset"), "success")
                QMessageBox.information(self, t("system_tab.title_force_reset"), msg)
                self.refresh_all()
            except Exception as e:
                err = f"Error during Global Reset: {e}"
                self.status_message.emit(err, "error")
                QMessageBox.critical(self, t("app.error") if t("app.error") != "app.error" else "Error", err)

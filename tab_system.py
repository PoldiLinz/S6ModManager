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

        info_layout.addWidget(QLabel("🎮 Spielverzeichnis:"), 0, 0)
        self.lbl_game_path = QLabel(self.system.game_path)
        self.lbl_game_path.setObjectName("DimLabel")
        info_layout.addWidget(self.lbl_game_path, 0, 1)

        info_layout.addWidget(QLabel("🛡️ UAC Admin-Status:"), 0, 2)
        self.lbl_admin_badge = QLabel()
        info_layout.addWidget(self.lbl_admin_badge, 0, 3)

        info_layout.addWidget(QLabel("📁 UserMaps-Pfad:"), 1, 0)
        self.lbl_usermaps_path = QLabel(self.system.user_maps_path)
        self.lbl_usermaps_path.setObjectName("DimLabel")
        info_layout.addWidget(self.lbl_usermaps_path, 1, 1)

        info_layout.addWidget(QLabel("📦 ModLoader Status:"), 1, 2)
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
        h_fbar.addWidget(QLabel("Liste aller aktiven Dateien in modloader/shr/mod:"))
        h_fbar.addStretch()
        btn_refresh_files = QPushButton("🔄 Neu laden")
        btn_refresh_files.clicked.connect(self._refresh_modloader_files)
        h_fbar.addWidget(btn_refresh_files)
        v_files.addLayout(h_fbar)

        self.table_mod_files = QTableWidget()
        self.table_mod_files.setColumnCount(4)
        self.table_mod_files.setHorizontalHeaderLabels(["Kategorie", "Relative Datei", "Größe", "Zuletzt geändert"])
        self.table_mod_files.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        v_files.addWidget(self.table_mod_files)
        sub_tabs.addTab(tab_files, "📂 Aktive ModLoader-Dateien")

        # Tab B: S6Patcher Schutz-Dateien
        tab_patcher = QWidget()
        v_patcher = QVBoxLayout(tab_patcher)

        h_pbar = QHBoxLayout()
        h_pbar.addWidget(QLabel("Integritätsüberwachung der unersetzlichen S6Patcher-Basisdateien:"))
        h_pbar.addStretch()
        btn_refresh_patcher = QPushButton("🛡️ Integrität prüfen")
        btn_refresh_patcher.clicked.connect(self._refresh_patcher_health)
        h_pbar.addWidget(btn_refresh_patcher)
        v_patcher.addLayout(h_pbar)

        self.table_patcher = QTableWidget()
        self.table_patcher.setColumnCount(4)
        self.table_patcher.setHorizontalHeaderLabels(["Status", "Schutzdatei", "Größe", "Vollständiger Pfad"])
        self.table_patcher.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        v_patcher.addWidget(self.table_patcher)
        sub_tabs.addTab(tab_patcher, "🛡️ S6Patcher Schutz-Status")

        # Tab C: Backup & Snapshot Manager
        tab_backups = QWidget()
        v_backups = QVBoxLayout(tab_backups)

        h_bbar = QHBoxLayout()
        btn_new_backup = QPushButton("📦 Neues ModLoader-Backup erstellen")
        btn_new_backup.setObjectName("PrimaryButton")
        btn_new_backup.clicked.connect(self._on_create_backup)
        h_bbar.addWidget(btn_new_backup)

        btn_open_backups = QPushButton("📂 Backup-Ordner öffnen")
        btn_open_backups.clicked.connect(lambda: os.startfile(self.system.backups_path))
        h_bbar.addWidget(btn_open_backups)

        h_bbar.addStretch()
        btn_refresh_b = QPushButton("🔄 Aktualisieren")
        btn_refresh_b.clicked.connect(self._refresh_backups)
        h_bbar.addWidget(btn_refresh_b)
        v_backups.addLayout(h_bbar)

        self.table_backups = QTableWidget()
        self.table_backups.setColumnCount(4)
        self.table_backups.setHorizontalHeaderLabels(["Backup-Archiv", "Größe", "Erstellt am", "Aktionen"])
        self.table_backups.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        v_backups.addWidget(self.table_backups)
        sub_tabs.addTab(tab_backups, "📦 Backups & Snapshots")

        layout.addWidget(sub_tabs)

    # -------------------------------------------------------------------------
    # Aktualisierung
    # -------------------------------------------------------------------------

    def refresh_all(self):
        # Admin Status
        is_adm = self.system.is_admin()
        if is_adm:
            self.lbl_admin_badge.setText("  🟢 Administrator (Vollzugriff)  ")
            self.lbl_admin_badge.setObjectName("BadgeSuccess")
        else:
            self.lbl_admin_badge.setText("  🟡 Eingeschränkt (UAC benötigt)  ")
            self.lbl_admin_badge.setObjectName("BadgeWarning")
        self.lbl_admin_badge.style().unpolish(self.lbl_admin_badge)
        self.lbl_admin_badge.style().polish(self.lbl_admin_badge)

        self._refresh_patcher_health()
        self._refresh_modloader_files()
        self._refresh_backups()

    def _refresh_patcher_health(self):
        status, results = self.system.check_s6patcher_integrity()
        if status == "OK":
            self.lbl_modloader_badge.setText("  🟢 Bereit & Geschützt  ")
            self.lbl_modloader_badge.setObjectName("BadgeSuccess")
        elif status == "WARNING":
            self.lbl_modloader_badge.setText("  🟡 Dateien fehlen teilweise  ")
            self.lbl_modloader_badge.setObjectName("BadgeWarning")
        else:
            self.lbl_modloader_badge.setText("  🔴 S6Patcher nicht installiert  ")
            self.lbl_modloader_badge.setObjectName("BadgeError")
        self.lbl_modloader_badge.style().unpolish(self.lbl_modloader_badge)
        self.lbl_modloader_badge.style().polish(self.lbl_modloader_badge)

        self.table_patcher.setRowCount(len(results))
        for row, item in enumerate(results):
            # Status Badge
            st_item = QTableWidgetItem("🟢 OK" if item["exists"] else "🔴 FEHLT")
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

            path_text = f["relative_path"] + (" 🔒 [GESCHÜTZT]" if f["is_protected"] else "")
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

            btn_rest = QPushButton("🔄 Wiederherstellen")
            btn_rest.clicked.connect(lambda _, path=b["full_path"]: self._on_restore_backup(path))
            h_act.addWidget(btn_rest)

            btn_del = QPushButton("🗑️")
            btn_del.setObjectName("DangerButton")
            btn_del.clicked.connect(lambda _, path=b["full_path"]: self._on_delete_backup(path))
            h_act.addWidget(btn_del)

            self.table_backups.setCellWidget(row, 3, w_act)

    def _on_create_backup(self):
        name, ok = QInputDialog.getText(self, "Backup erstellen", "Name des Backups (optional):")
        if ok:
            try:
                b_name = name.strip() if name.strip() else None
                zip_path = self.system.create_modloader_backup(b_name)
                msg = f"ModLoader-Backup erfolgreich erstellt:\n{os.path.basename(zip_path)}"
                self.status_message.emit(f"Backup {os.path.basename(zip_path)} gespeichert.", "success")
                QMessageBox.information(self, "Backup erstellt", msg)
                self._refresh_backups()
            except Exception as e:
                err = f"Fehler bei Backup-Erstellung: {e}"
                self.status_message.emit(err, "error")
                QMessageBox.critical(self, "Fehler", err)

    def _on_restore_backup(self, zip_path: str):
        reply = QMessageBox.question(
            self,
            "Backup wiederherstellen",
            f"Möchtest du den ModLoader-Zustand aus folgendem Backup wiederherstellen?\n\n{os.path.basename(zip_path)}\n\nGeschützte S6Patcher-Dateien bleiben dabei sicher erhalten.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                count = self.system.restore_modloader_backup(zip_path)
                msg = f"{count} Dateien aus Backup erfolgreich wiederhergestellt!"
                self.status_message.emit(msg, "success")
                QMessageBox.information(self, "Backup wiederhergestellt", msg)
                self.refresh_all()
            except Exception as e:
                err = f"Fehler bei Wiederherstellung: {e}"
                self.status_message.emit(err, "error")
                QMessageBox.critical(self, "Fehler", err)

    def _on_delete_backup(self, zip_path: str):
        reply = QMessageBox.question(
            self,
            "Backup löschen",
            f"Möchtest du das Backup '{os.path.basename(zip_path)}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                self.status_message.emit("Backup gelöscht.", "warning")
                self._refresh_backups()
            except Exception as e:
                QMessageBox.critical(self, "Fehler", str(e))

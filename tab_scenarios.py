"""
Siedler 6 Mod Manager - Tab 2: Karten & Szenario-Varianten
Verwaltet Karten-Bibliothek, schaltet Abwandlungen um und erlaubt UserMap-Zuweisung.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFrame,
    QRadioButton, QButtonGroup, QScrollArea, QMessageBox,
    QDialog, QLineEdit, QTextEdit, QComboBox, QFileDialog
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, List, Any, Optional

from ModManager.engines.scenario_engine import ScenarioEngine
from ModManager.engines.system_engine import SystemEngine


class ScenarioTab(QWidget):
    """Registerkarte für Karten- und Szenario-Verwaltung."""

    status_message = pyqtSignal(str, str)

    def __init__(self, scenario_engine: ScenarioEngine, system_engine: SystemEngine, parent=None):
        super().__init__(parent)
        self.scenario_engine = scenario_engine
        self.system = system_engine
        self.current_map_data: Optional[Dict[str, Any]] = None
        self.selected_variant_id: Optional[str] = None

        self._init_ui()
        self.refresh_maps()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---------------------------------------------------------------------
        # Linke Spalte: Kartenliste
        # ---------------------------------------------------------------------
        left_card = QFrame()
        left_card.setObjectName("CardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(8, 8, 8, 8)

        lbl_maps = QLabel("🗺️ Unterstützte Karten")
        lbl_maps.setObjectName("SectionHeader")
        left_layout.addWidget(lbl_maps)

        self.list_maps = QListWidget()
        self.list_maps.currentItemChanged.connect(self._on_map_selection_changed)
        left_layout.addWidget(self.list_maps)

        btn_refresh = QPushButton("🔄 Liste aktualisieren")
        btn_refresh.clicked.connect(self.refresh_maps)
        left_layout.addWidget(btn_refresh)

        btn_import_usermap = QPushButton("➕ User-Map als Variante importieren")
        btn_import_usermap.clicked.connect(self._on_import_usermap_dialog)
        left_layout.addWidget(btn_import_usermap)

        splitter.addWidget(left_card)

        # ---------------------------------------------------------------------
        # Rechte Spalte: Detailansicht & Varianten
        # ---------------------------------------------------------------------
        right_card = QFrame()
        right_card.setObjectName("CardFrame")
        self.right_layout = QVBoxLayout(right_card)
        self.right_layout.setContentsMargins(12, 12, 12, 12)

        # Header Info
        self.lbl_map_title = QLabel("Keine Karte ausgewählt")
        self.lbl_map_title.setObjectName("SectionHeader")
        self.right_layout.addWidget(self.lbl_map_title)

        self.lbl_active_badge = QLabel("")
        self.right_layout.addWidget(self.lbl_active_badge)

        # Mittlerer Bereich (Vorschau + Varianten)
        mid_layout = QHBoxLayout()

        # Vorschau-Bild
        self.lbl_preview = QLabel()
        self.lbl_preview.setFixedSize(200, 150)
        self.lbl_preview.setStyleSheet("border: 1px solid #3c4354; border-radius: 6px; background-color: #121418;")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setText("Keine Vorschau")
        mid_layout.addWidget(self.lbl_preview)

        # Varianten-Auswahl
        var_box = QFrame()
        var_box.setObjectName("SubCardFrame")
        self.var_layout = QVBoxLayout(var_box)
        self.var_layout.addWidget(QLabel("Verfügbare Szenario-Abwandlungen:"))
        self.btn_group_vars = QButtonGroup(self)
        self.btn_group_vars.idClicked.connect(self._on_variant_radio_clicked)
        mid_layout.addWidget(var_box, 1)

        self.right_layout.addLayout(mid_layout)

        # Details-Bereich (Beschreibung & Features)
        self.details_box = QFrame()
        self.details_box.setObjectName("SubCardFrame")
        d_layout = QVBoxLayout(self.details_box)
        
        self.lbl_var_title = QLabel("")
        self.lbl_var_title.setObjectName("CardTitle")
        d_layout.addWidget(self.lbl_var_title)

        self.lbl_var_meta = QLabel("")
        self.lbl_var_meta.setObjectName("DimLabel")
        d_layout.addWidget(self.lbl_var_meta)

        self.lbl_var_desc = QLabel("")
        self.lbl_var_desc.setWordWrap(True)
        d_layout.addWidget(self.lbl_var_desc)

        self.lbl_var_features = QLabel("")
        self.lbl_var_features.setObjectName("DimLabel")
        self.lbl_var_features.setWordWrap(True)
        d_layout.addWidget(self.lbl_var_features)

        self.right_layout.addWidget(self.details_box)
        self.right_layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()

        self.btn_open_folder = QPushButton("📂 Szenario-Ordner öffnen")
        self.btn_open_folder.clicked.connect(self._on_open_folder)
        btn_layout.addWidget(self.btn_open_folder)

        btn_layout.addStretch()

        self.btn_revert = QPushButton("⏪ Auf Originalkarte (Vanilla) zurücksetzen")
        self.btn_revert.setObjectName("DangerButton")
        self.btn_revert.clicked.connect(self._on_revert_map)
        btn_layout.addWidget(self.btn_revert)

        self.btn_activate = QPushButton("🚀 Ausgewählte Variante aktivieren")
        self.btn_activate.setObjectName("PrimaryButton")
        self.btn_activate.clicked.connect(self._on_activate_variant)
        btn_layout.addWidget(self.btn_activate)

        self.right_layout.addLayout(btn_layout)

        splitter.addWidget(right_card)
        splitter.setSizes([260, 600])

        layout.addWidget(splitter)

    # -------------------------------------------------------------------------
    # Daten-Aktualisierung
    # -------------------------------------------------------------------------

    def refresh_maps(self):
        self.list_maps.clear()
        maps = self.scenario_engine.list_supported_maps()

        for m in maps:
            item = QListWidgetItem()
            status_text = "🟢 Mod aktiv" if m["is_mod_active"] else "⚪ Vanilla"
            item.setText(f"{m['friendly_name']}\n[{m['map_id']}] • {status_text}")
            item.setData(Qt.ItemDataRole.UserRole, m)
            self.list_maps.addItem(item)

        if self.list_maps.count() > 0:
            self.list_maps.setCurrentRow(0)

    def _on_map_selection_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if not current:
            return
        map_data = current.data(Qt.ItemDataRole.UserRole)
        self.current_map_data = map_data
        self._display_map_details(map_data)

    def _display_map_details(self, map_data: Dict[str, Any]):
        map_id = map_data["map_id"]
        friendly_name = map_data["friendly_name"]
        active_var = map_data["active_variant_id"]

        self.lbl_map_title.setText(f"{friendly_name} ({map_id})")

        if active_var and active_var != "vanilla":
            self.lbl_active_badge.setText(f"  AKTIV IM SPIEL: {active_var}  ")
            self.lbl_active_badge.setObjectName("BadgeSuccess")
        else:
            self.lbl_active_badge.setText("  AKTIV IM SPIEL: Original Ubisoft Vanilla Karte  ")
            self.lbl_active_badge.setObjectName("BadgeWarning")
        self.lbl_active_badge.style().unpolish(self.lbl_active_badge)
        self.lbl_active_badge.style().polish(self.lbl_active_badge)

        # Varianten neu aufbauen
        for btn in self.btn_group_vars.buttons():
            self.btn_group_vars.removeButton(btn)
            btn.deleteLater()

        variations = map_data.get("variations", [])
        for i, v in enumerate(variations):
            r_btn = QRadioButton(v.get("title", v["id"]))
            self.btn_group_vars.addButton(r_btn, i)
            self.var_layout.addWidget(r_btn)

            # Standardmäßig die aktive Variante auswählen
            if v["id"] == active_var:
                r_btn.setChecked(True)
                self._display_variant_details(v)
            elif not active_var and v.get("is_vanilla"):
                r_btn.setChecked(True)
                self._display_variant_details(v)

        if not self.btn_group_vars.checkedButton() and variations:
            self.btn_group_vars.buttons()[0].setChecked(True)
            self._display_variant_details(variations[0])

    def _on_variant_radio_clicked(self, index: int):
        if not self.current_map_data:
            return
        variations = self.current_map_data.get("variations", [])
        if 0 <= index < len(variations):
            self._display_variant_details(variations[index])

    def _display_variant_details(self, variant: Dict[str, Any]):
        self.selected_variant_id = variant["id"]
        self.lbl_var_title.setText(variant.get("title", variant["id"]))

        author = variant.get("author", "Unbekannt")
        ver = variant.get("version", "1.0")
        self.lbl_var_meta.setText(f"Autor: {author} • Version: {ver}")

        desc = variant.get("description", "Keine Beschreibung verfügbar.")
        self.lbl_var_desc.setText(desc)

        features = variant.get("features", [])
        if features:
            f_text = "Besonderheiten:\n" + "\n".join([f" • {feat}" for feat in features])
            self.lbl_var_features.setText(f_text)
        else:
            self.lbl_var_features.setText("")

        # Bildvorschau
        preview_img = variant.get("preview_image")
        if preview_img and os.path.exists(preview_img):
            pix = QPixmap(preview_img).scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_preview.setPixmap(pix)
        else:
            self.lbl_preview.setText("Keine Vorschau")

    # -------------------------------------------------------------------------
    # Aktionen
    # -------------------------------------------------------------------------

    def _on_activate_variant(self):
        if not self.current_map_data or not self.selected_variant_id:
            return
        map_id = self.current_map_data["map_id"]
        var_id = self.selected_variant_id

        try:
            self.scenario_engine.activate_scenario(map_id, var_id)
            msg = f"Szenario '{var_id}' für Karte '{map_id}' wurde erfolgreich im ModLoader aktiviert!"
            self.status_message.emit(msg, "success")
            QMessageBox.information(self, "Szenario aktiviert", msg)
            self.refresh_maps()
        except Exception as e:
            err = f"Fehler bei Aktivierung: {e}"
            self.status_message.emit(err, "error")
            QMessageBox.critical(self, "Fehler", err)

    def _on_revert_map(self):
        if not self.current_map_data:
            return
        map_id = self.current_map_data["map_id"]

        try:
            self.scenario_engine.revert_map_to_vanilla(map_id)
            msg = f"Karte '{map_id}' wurde auf Original-Vanilla zurückgesetzt."
            self.status_message.emit(msg, "warning")
            QMessageBox.information(self, "Karte zurückgesetzt", msg)
            self.refresh_maps()
        except Exception as e:
            err = f"Fehler beim Zurücksetzen: {e}"
            self.status_message.emit(err, "error")
            QMessageBox.critical(self, "Fehler", err)

    def _on_open_folder(self):
        if not self.current_map_data or not self.selected_variant_id:
            return
        map_id = self.current_map_data["map_id"]
        var_id = self.selected_variant_id
        folder = os.path.join(self.scenario_engine.scenarios_dir, map_id, var_id)
        if os.path.exists(folder):
            os.startfile(folder)

    def _on_import_usermap_dialog(self):
        """Öffnet Dialog zur Zuweisung einer UserMap als neue Variante."""
        dialog = QDialog(self)
        dialog.setWindowTitle("User-Map als Variante importieren")
        dialog.setMinimumWidth(450)
        d_layout = QVBoxLayout(dialog)

        d_layout.addWidget(QLabel("Wähle eine Karte aus deinem UserMaps-Ordner:"))
        combo_usermaps = QComboBox()
        usermaps = self.scenario_engine.list_available_usermaps()
        for u in usermaps:
            combo_usermaps.addItem(u["name"], u["folder_path"])
        d_layout.addWidget(combo_usermaps)

        d_layout.addWidget(QLabel("Ziel-Originalkarte (die ersetzt werden soll):"))
        combo_target_map = QComboBox()
        maps = self.scenario_engine.list_supported_maps()
        for m in maps:
            combo_target_map.addItem(f"{m['friendly_name']} ({m['map_id']})", m["map_id"])
        d_layout.addWidget(combo_target_map)

        d_layout.addWidget(QLabel("Name der neuen Variante:"))
        txt_title = QLineEdit()
        txt_title.setPlaceholderText("z.B. Meine Eigene Handelsmission")
        d_layout.addWidget(txt_title)

        d_layout.addWidget(QLabel("Varianten-ID (Ordnername):"))
        txt_id = QLineEdit()
        txt_id.setPlaceholderText("z.B. custom_trade_v1")
        d_layout.addWidget(txt_id)

        d_layout.addWidget(QLabel("Beschreibung:"))
        txt_desc = QTextEdit()
        txt_desc.setMaximumHeight(80)
        d_layout.addWidget(txt_desc)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(dialog.reject)
        btn_ok = QPushButton("Importieren")
        btn_ok.setObjectName("PrimaryButton")

        def do_import():
            src_folder = combo_usermaps.currentData()
            target_map = combo_target_map.currentData()
            v_title = txt_title.text().strip() or "Benutzer-Variante"
            v_id = txt_id.text().strip() or "custom_variant"
            v_desc = txt_desc.toPlainText().strip() or "Importierte Karte aus UserMaps."

            if not src_folder:
                return

            try:
                self.scenario_engine.import_usermap_as_scenario_variation(
                    target_map_id=target_map,
                    variant_id=v_id,
                    title=v_title,
                    description=v_desc,
                    source_usermap_folder=src_folder
                )
                self.status_message.emit(f"UserMap erfolgreich als Variante '{v_id}' importiert!", "success")
                dialog.accept()
                self.refresh_maps()
            except Exception as ex:
                QMessageBox.critical(dialog, "Importfehler", str(ex))

        btn_ok.clicked.connect(do_import)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_ok)
        d_layout.addLayout(btn_box)

        dialog.exec()

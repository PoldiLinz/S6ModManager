"""
Siedler 6 Mod Manager - Tab 2: Karten & Szenario-Varianten
Verwaltet Karten-Bibliothek, schaltet Abwandlungen um und erlaubt UserMap-Zuweisung.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFrame,
    QRadioButton, QButtonGroup, QScrollArea, QMessageBox,
    QDialog, QLineEdit, QTextEdit, QComboBox, QFileDialog,
    QSizePolicy
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, List, Any, Optional

from ModManager.engines.scenario_engine import ScenarioEngine
from ModManager.engines.system_engine import SystemEngine
from ModManager.engines import t


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
        layout.setSpacing(10)

        # ---------------------------------------------------------------------
        # Top Action Bar
        # ---------------------------------------------------------------------
        top_card = QFrame()
        top_card.setObjectName("CardFrame")
        top_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(12, 10, 12, 10)
        top_layout.setSpacing(10)

        self.btn_open_folder = QPushButton(t("scenarios_tab.btn_open_folder"))
        self.btn_open_folder.clicked.connect(self._on_open_folder)
        top_layout.addWidget(self.btn_open_folder)

        top_layout.addStretch()

        self.btn_activate = QPushButton(t("scenarios_tab.btn_activate"))
        self.btn_activate.setObjectName("PrimaryButton")
        self.btn_activate.clicked.connect(self._on_activate_variant)
        top_layout.addWidget(self.btn_activate)

        self.btn_revert = QPushButton("↺")
        self.btn_revert.setObjectName("HeaderRevertBtn")
        self.btn_revert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_revert.setToolTip(t("scenarios_tab.btn_revert"))
        self.btn_revert.clicked.connect(self._on_revert_map)
        top_layout.addWidget(self.btn_revert)

        layout.addWidget(top_card)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---------------------------------------------------------------------
        # Linke Spalte: Kartenliste
        # ---------------------------------------------------------------------
        left_card = QFrame()
        left_card.setObjectName("CardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(8, 8, 8, 8)

        lbl_maps = QLabel(t("scenarios_tab.lbl_maps"))
        lbl_maps.setObjectName("SectionHeader")
        left_layout.addWidget(lbl_maps)

        self.list_maps = QListWidget()
        self.list_maps.currentItemChanged.connect(self._on_map_selection_changed)
        left_layout.addWidget(self.list_maps)

        btn_refresh = QPushButton(t("scenarios_tab.btn_refresh"))
        btn_refresh.clicked.connect(self.refresh_maps)
        left_layout.addWidget(btn_refresh)

        btn_import_usermap = QPushButton(t("scenarios_tab.btn_import"))
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
        self.lbl_map_title = QLabel(t("scenarios_tab.lbl_no_map"))
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
        self.lbl_preview.setText(t("scenarios_tab.lbl_no_preview"))
        mid_layout.addWidget(self.lbl_preview)

        # Varianten-Auswahl
        var_box = QFrame()
        var_box.setObjectName("SubCardFrame")
        self.var_layout = QVBoxLayout(var_box)
        self.var_layout.addWidget(QLabel(t("scenarios_tab.lbl_variations")))
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
            status_text = t("scenarios_tab.status_mod") if m["is_mod_active"] else t("scenarios_tab.status_vanilla")
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
            self.lbl_active_badge.setText(t("scenarios_tab.status_active").format(active_var=active_var))
            self.lbl_active_badge.setObjectName("BadgeSuccess")
        else:
            self.lbl_active_badge.setText(t("scenarios_tab.status_original"))
            self.lbl_active_badge.setObjectName("BadgeWarning")
        self.lbl_active_badge.style().unpolish(self.lbl_active_badge)
        self.lbl_active_badge.style().polish(self.lbl_active_badge)

        # Varianten neu aufbauen - alte Buttons aus Layout UND ButtonGroup entfernen
        for btn in self.btn_group_vars.buttons():
            self.btn_group_vars.removeButton(btn)
            self.var_layout.removeWidget(btn)
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
        self.lbl_var_meta.setText(t("scenarios_tab.meta_info").format(author=author, ver=ver))

        desc = variant.get("description", t("scenarios_tab.no_desc"))
        self.lbl_var_desc.setText(desc)

        features = variant.get("features", [])
        if features:
            f_text = t("scenarios_tab.features") + "\n".join([f" • {feat}" for feat in features])
            self.lbl_var_features.setText(f_text)
        else:
            self.lbl_var_features.setText("")

        # Bildvorschau
        preview_img = variant.get("preview_image")
        if preview_img and os.path.exists(preview_img):
            pix = QPixmap(preview_img).scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_preview.setPixmap(pix)
        else:
            self.lbl_preview.setText(t("scenarios_tab.lbl_no_preview"))

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
            msg = t("scenarios_tab.msg_activate_success").format(var_id=var_id, map_id=map_id)
            self.status_message.emit(msg, "success")
            self.refresh_maps()
        except Exception as e:
            err = t("scenarios_tab.msg_activate_error").format(err=e)
            self.status_message.emit(err, "error")
            QMessageBox.critical(self, t("app.error") if t("app.error") != "app.error" else "Error", err)

    def _on_revert_map(self):
        if not self.current_map_data:
            return
        map_id = self.current_map_data["map_id"]

        try:
            self.scenario_engine.revert_map_to_vanilla(map_id)
            msg = t("scenarios_tab.msg_revert_success").format(map_id=map_id)
            self.status_message.emit(msg, "warning")
            self.refresh_maps()
        except Exception as e:
            err = t("scenarios_tab.msg_revert_error").format(err=e)
            self.status_message.emit(err, "error")
            QMessageBox.critical(self, t("app.error") if t("app.error") != "app.error" else "Error", err)

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
        dialog.setWindowTitle(t("scenarios_tab.title_import"))
        dialog.setMinimumWidth(450)
        d_layout = QVBoxLayout(dialog)

        d_layout.addWidget(QLabel(t("scenarios_tab.lbl_import_select")))
        combo_usermaps = QComboBox()
        usermaps = self.scenario_engine.list_available_usermaps()
        for u in usermaps:
            combo_usermaps.addItem(u["name"], u["folder_path"])
        d_layout.addWidget(combo_usermaps)

        d_layout.addWidget(QLabel(t("scenarios_tab.lbl_import_target")))
        combo_target_map = QComboBox()
        maps = self.scenario_engine.list_supported_maps()
        for m in maps:
            combo_target_map.addItem(f"{m['friendly_name']} ({m['map_id']})", m["map_id"])
        d_layout.addWidget(combo_target_map)

        d_layout.addWidget(QLabel(t("scenarios_tab.lbl_import_name")))
        txt_title = QLineEdit()
        txt_title.setPlaceholderText(t("scenarios_tab.ph_import_name"))
        d_layout.addWidget(txt_title)

        d_layout.addWidget(QLabel(t("scenarios_tab.lbl_import_id")))
        txt_id = QLineEdit()
        txt_id.setPlaceholderText(t("scenarios_tab.ph_import_id"))
        d_layout.addWidget(txt_id)

        d_layout.addWidget(QLabel(t("scenarios_tab.lbl_import_desc")))
        txt_desc = QTextEdit()
        txt_desc.setMaximumHeight(80)
        d_layout.addWidget(txt_desc)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton(t("scenarios_tab.btn_cancel"))
        btn_cancel.clicked.connect(dialog.reject)
        btn_ok = QPushButton(t("scenarios_tab.btn_ok"))
        btn_ok.setObjectName("PrimaryButton")

        def do_import():
            src_folder = combo_usermaps.currentData()
            target_map = combo_target_map.currentData()
            v_title = txt_title.text().strip() or t("scenarios_tab.default_variant_name")
            v_id = txt_id.text().strip() or t("scenarios_tab.default_variant_id")
            v_desc = txt_desc.toPlainText().strip() or t("scenarios_tab.default_variant_desc")

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
                self.status_message.emit(t("scenarios_tab.msg_import_success").format(v_id=v_id), "success")
                dialog.accept()
                self.refresh_maps()
            except Exception as ex:
                QMessageBox.critical(dialog, t("scenarios_tab.title_import_error"), str(ex))

        btn_ok.clicked.connect(do_import)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_ok)
        d_layout.addLayout(btn_box)

        dialog.exec()

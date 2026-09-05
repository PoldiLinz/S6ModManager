import os
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QFrame, QSplitter,
    QCheckBox, QComboBox, QPlainTextEdit, QScrollArea,
    QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView,
    QSpinBox, QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ModManager.engines.i18n_engine import t
from ModManager.engines.sandbox_engine import SandboxEngine
from ModManager.engines.system_engine import SystemEngine

class TabSandbox(QWidget):
    log_signal = pyqtSignal(str, str)

    def __init__(self, system_engine: SystemEngine):
        super().__init__()
        self.system_engine = system_engine
        self.sandbox_engine = SandboxEngine(self.system_engine)
        self.current_map_data: Optional[Dict[str, Any]] = None

        self._init_ui()
        self.refresh_maps()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # ------------------- LINKE SPALTE (Map List) -------------------
        left_card = QFrame()
        left_card.setObjectName("CardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)

        lbl_list_title = QLabel("🧪 Supported Test Maps")
        lbl_list_title.setObjectName("SectionHeader")
        left_layout.addWidget(lbl_list_title)

        self.list_maps = QListWidget()
        self.list_maps.currentItemChanged.connect(self._on_map_selection_changed)
        left_layout.addWidget(self.list_maps)

        splitter.addWidget(left_card)

        # ------------------- RECHTE SPALTE (Inhalt) -------------------
        right_container = QWidget()
        right_main_layout = QVBoxLayout(right_container)
        right_main_layout.setContentsMargins(0, 0, 0, 0)
        right_main_layout.setSpacing(12)

        # SCROLL AREA FÜR DEN RECHTEN BEREICH
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        self.right_layout = QVBoxLayout(scroll_content)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(12)

        # -- 1. Zielkarte
        card_map = QFrame()
        card_map.setObjectName("CardFrame")
        card_map.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        l_map = QVBoxLayout(card_map)

        lbl_target_title = QLabel("🎯 " + t("sandbox_tab.lbl_target_map"))
        lbl_target_title.setObjectName("SectionHeader")
        l_map.addWidget(lbl_target_title)

        h_pick = QHBoxLayout()
        self.lbl_current_map = QLabel("<b>[Keine Map ausgewählt]</b>")
        h_pick.addWidget(self.lbl_current_map, 1)

        btn_refresh = QPushButton(t("sandbox_tab.btn_refresh"))
        btn_refresh.clicked.connect(self.refresh_maps)
        h_pick.addWidget(btn_refresh)
        l_map.addLayout(h_pick)

        self.lbl_inject_status = QLabel("")
        l_map.addWidget(self.lbl_inject_status)
        self.right_layout.addWidget(card_map)

        # -- 2. Sandbox-Optionen (Konfigurator)
        card_opts = QFrame()
        card_opts.setObjectName("CardFrame")
        l_opts = QVBoxLayout(card_opts)
        
        # PRESET DROPDOWN
        h_preset = QHBoxLayout()
        h_preset.addWidget(QLabel(t("sandbox_tab.lbl_preset")))
        self.combo_preset = QComboBox()
        self.combo_preset.addItem(t("sandbox_tab.preset_vanilla"), "vanilla")
        self.combo_preset.addItem(t("sandbox_tab.preset_mid"), "mid")
        self.combo_preset.addItem(t("sandbox_tab.preset_high"), "high")
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        h_preset.addWidget(self.combo_preset, 1)
        l_opts.addLayout(h_preset)

        # GROUP: Title & Buildings
        grp_build = QGroupBox(t("sandbox_tab.grp_buildings"))
        grid_build = QGridLayout(grp_build)
        
        self.combo_title = QComboBox()
        for i, text in enumerate([t("sandbox_tab.title_knight"), t("sandbox_tab.title_sheriff"), 
                                  t("sandbox_tab.title_baron"), t("sandbox_tab.title_earl"), 
                                  t("sandbox_tab.title_marquis"), t("sandbox_tab.title_duke")], 1):
            self.combo_title.addItem(text, i)
        
        self.combo_castle = QComboBox()
        self.combo_storehouse = QComboBox()
        self.combo_church = QComboBox()
        for cb in [self.combo_castle, self.combo_storehouse, self.combo_church]:
            for i, text in enumerate([t("sandbox_tab.level_1"), t("sandbox_tab.level_2"), 
                                      t("sandbox_tab.level_3"), t("sandbox_tab.level_4")], 1):
                cb.addItem(text, i)
        
        grid_build.addWidget(QLabel(t("sandbox_tab.lbl_title")), 0, 0)
        grid_build.addWidget(self.combo_title, 0, 1)
        grid_build.addWidget(QLabel(t("sandbox_tab.lbl_castle")), 0, 2)
        grid_build.addWidget(self.combo_castle, 0, 3)
        grid_build.addWidget(QLabel(t("sandbox_tab.lbl_storehouse")), 1, 0)
        grid_build.addWidget(self.combo_storehouse, 1, 1)
        grid_build.addWidget(QLabel(t("sandbox_tab.lbl_church")), 1, 2)
        grid_build.addWidget(self.combo_church, 1, 3)
        
        for cb in [self.combo_title, self.combo_castle, self.combo_storehouse, self.combo_church]:
            cb.currentIndexChanged.connect(self._update_lua_preview)
            
        l_opts.addWidget(grp_build)

        # HBOX FOR TABLES
        h_tables = QHBoxLayout()

        # GROUP: Resources
        grp_res = QGroupBox(t("sandbox_tab.grp_resources"))
        v_res = QVBoxLayout(grp_res)
        self.table_res = QTableWidget(0, 4)
        self._setup_table(self.table_res, [t("sandbox_tab.col_res_name"), t("sandbox_tab.col_res_start"), t("sandbox_tab.col_res_vanilla"), ""])
        self.res_spinboxes = {}
        self._add_res_row("G_Gold", t("sandbox_tab.res_gold"), 0)
        self._add_res_row("G_Wood", t("sandbox_tab.res_wood"), 0)
        self._add_res_row("G_Stone", t("sandbox_tab.res_stone"), 0)
        self._add_res_row("G_Iron", t("sandbox_tab.res_iron"), 0)
        self._add_res_row("G_Grain", t("sandbox_tab.res_food"), 0)
        self._add_res_row("G_Wool", t("sandbox_tab.res_clothes"), 0)
        self._add_res_row("G_Honeycomb", t("sandbox_tab.res_clean"), 0)
        self._add_res_row("G_Herb", t("sandbox_tab.res_medicine"), 0)
        v_res.addWidget(self.table_res)
        h_tables.addWidget(grp_res)

        # GROUP: Troops
        grp_troops = QGroupBox(t("sandbox_tab.grp_troops"))
        v_troops = QVBoxLayout(grp_troops)
        self.table_troops = QTableWidget(0, 4)
        self._setup_table(self.table_troops, [t("sandbox_tab.col_res_name"), t("sandbox_tab.col_res_start"), t("sandbox_tab.col_res_vanilla"), ""])
        self.troop_spinboxes = {}
        self._add_troop_row("U_MilitarySword", t("sandbox_tab.troop_sword"), 0)
        self._add_troop_row("U_MilitaryBow", t("sandbox_tab.troop_bow"), 0)
        self._add_troop_row("U_CatapultCart", t("sandbox_tab.troop_siege"), 0)
        self._add_troop_row("U_Thief", t("sandbox_tab.troop_thief"), 0)
        v_troops.addWidget(self.table_troops)
        h_tables.addWidget(grp_troops)

        l_opts.addLayout(h_tables)

        # GROUP: Globals
        grp_glob = QGroupBox(t("sandbox_tab.grp_global"))
        h_glob = QHBoxLayout(grp_glob)
        self.chk_fog = QCheckBox(t("sandbox_tab.chk_fog"))
        self.chk_vic = QCheckBox(t("sandbox_tab.chk_victory"))
        self.chk_fog.stateChanged.connect(self._update_lua_preview)
        self.chk_vic.stateChanged.connect(self._update_lua_preview)
        h_glob.addWidget(self.chk_fog)
        h_glob.addWidget(self.chk_vic)
        h_glob.addStretch()
        l_opts.addWidget(grp_glob)

        self.right_layout.addWidget(card_opts)

        # -- 3. Vorschau
        card_preview = QFrame()
        card_preview.setObjectName("CardFrame")
        l_prev = QVBoxLayout(card_preview)
        lbl_prev_title = QLabel("Generated Lua Sandbox Code (executed at the end of mapscript.lua):")
        lbl_prev_title.setStyleSheet("color: #94a3b8;")
        l_prev.addWidget(lbl_prev_title)

        self.txt_preview = QPlainTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setObjectName("LogConsole")
        self.txt_preview.setMinimumHeight(120)
        l_prev.addWidget(self.txt_preview)

        # Buttons
        h_actions = QHBoxLayout()
        h_actions.addStretch()
        self.btn_inject = QPushButton("💉 " + t("sandbox_tab.btn_inject"))
        self.btn_inject.setObjectName("PrimaryButton")
        self.btn_inject.setMinimumWidth(180)
        self.btn_inject.clicked.connect(self._on_inject)
        h_actions.addWidget(self.btn_inject)

        self.btn_remove = QPushButton("🗑 " + t("sandbox_tab.btn_remove"))
        self.btn_remove.setObjectName("DangerButton")
        self.btn_remove.clicked.connect(self._on_remove)
        h_actions.addWidget(self.btn_remove)
        l_prev.addLayout(h_actions)

        self.right_layout.addWidget(card_preview)
        self.right_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        right_main_layout.addWidget(scroll_area)
        splitter.addWidget(right_container)
        splitter.setSizes([260, 600])

        main_layout.addWidget(splitter)
        self._apply_preset("vanilla")

    def _setup_table(self, table: QTableWidget, headers: list):
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(1, 100)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(2, 60)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(3, 40)
        table.horizontalHeader().setMinimumSectionSize(30)
        table.verticalHeader().setDefaultSectionSize(34)
        table.setMinimumHeight(240)

    def _add_res_row(self, res_id, name, vanilla_val):
        self._add_row_to_table(self.table_res, self.res_spinboxes, res_id, name, vanilla_val, max_val=999999)

    def _add_troop_row(self, troop_id, name, vanilla_val):
        self._add_row_to_table(self.table_troops, self.troop_spinboxes, troop_id, name, vanilla_val, max_val=100)

    def _add_row_to_table(self, table, sb_dict, item_id, name, vanilla_val, max_val):
        row = table.rowCount()
        table.insertRow(row)
        
        item_name = QTableWidgetItem(name)
        table.setItem(row, 0, item_name)
        
        sb = QSpinBox()
        sb.setRange(0, max_val)
        sb.setValue(vanilla_val)
        if max_val > 1000:
            sb.setSingleStep(50)
        sb.valueChanged.connect(self._update_lua_preview)
        sb_dict[item_id] = sb
        table.setCellWidget(row, 1, sb)
        
        item_van = QTableWidgetItem(str(vanilla_val))
        item_van.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_van.setForeground(QColor("#94a3b8"))
        table.setItem(row, 2, item_van)
        
        btn_reset = QPushButton("⟲")
        btn_reset.setToolTip("Reset to Vanilla")
        btn_reset.setFixedSize(24, 24)
        btn_reset.clicked.connect(lambda _, s=sb, v=vanilla_val: s.setValue(v))
        table.setCellWidget(row, 3, btn_reset)

    def _on_preset_changed(self, index: int):
        preset_id = self.combo_preset.currentData()
        self._apply_preset(preset_id)

    def _apply_preset(self, preset_id: str):
        # Block signals to avoid multiple updates
        for cb in [self.combo_title, self.combo_castle, self.combo_storehouse, self.combo_church]:
            cb.blockSignals(True)
        for sb in list(self.res_spinboxes.values()) + list(self.troop_spinboxes.values()):
            sb.blockSignals(True)
        self.chk_fog.blockSignals(True)
        self.chk_vic.blockSignals(True)

        # Reset alle
        self.combo_title.setCurrentIndex(0)
        self.combo_castle.setCurrentIndex(0)
        self.combo_storehouse.setCurrentIndex(0)
        self.combo_church.setCurrentIndex(0)
        for sb in list(self.res_spinboxes.values()) + list(self.troop_spinboxes.values()):
            sb.setValue(0)
        self.chk_fog.setChecked(False)
        self.chk_vic.setChecked(False)

        if preset_id == "mid":
            self.combo_title.setCurrentIndex(2) # Baron
            self.combo_castle.setCurrentIndex(1) # Lvl 2
            self.res_spinboxes["G_Gold"].setValue(10000)
            self.res_spinboxes["G_Wood"].setValue(150)
            self.res_spinboxes["G_Stone"].setValue(150)
            self.res_spinboxes["G_Iron"].setValue(50)
            self.troop_spinboxes["U_MilitarySword"].setValue(2)
        elif preset_id == "high":
            self.combo_title.setCurrentIndex(5) # Herzog
            self.combo_castle.setCurrentIndex(3) # Lvl 4
            self.combo_storehouse.setCurrentIndex(3)
            self.combo_church.setCurrentIndex(3)
            self.res_spinboxes["G_Gold"].setValue(50000)
            for r in ["G_Wood", "G_Stone", "G_Iron", "G_Grain", "G_Wool", "G_Honeycomb", "G_Herb"]:
                self.res_spinboxes[r].setValue(500)
            self.troop_spinboxes["U_MilitarySword"].setValue(5)
            self.troop_spinboxes["U_MilitaryBow"].setValue(5)
            self.troop_spinboxes["U_CatapultCart"].setValue(2)
            self.chk_fog.setChecked(True)

        for cb in [self.combo_title, self.combo_castle, self.combo_storehouse, self.combo_church]:
            cb.blockSignals(False)
        for sb in list(self.res_spinboxes.values()) + list(self.troop_spinboxes.values()):
            sb.blockSignals(False)
        self.chk_fog.blockSignals(False)
        self.chk_vic.blockSignals(False)
        
        self._update_lua_preview()

    def refresh_maps(self):
        self.list_maps.clear()
        maps = self.sandbox_engine.list_all_testable_maps()
        for m in maps:
            item = QListWidgetItem(m["name"])
            item.setData(Qt.ItemDataRole.UserRole, m)
            if m["is_injected"]:
                item.setForeground(QColor("#c59b27"))
            self.list_maps.addItem(item)
        if self.list_maps.count() > 0:
            self.list_maps.setCurrentRow(0)
        self.log_signal.emit("info", "Test Map Listen aktualisiert.")

    def _on_map_selection_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if not current:
            self.current_map_data = None
            self.lbl_current_map.setText("<b>[Keine Map ausgewählt]</b>")
            self.lbl_inject_status.setText("")
            self.btn_inject.setEnabled(False)
            self.btn_remove.setEnabled(False)
            return

        map_data = current.data(Qt.ItemDataRole.UserRole)
        self.current_map_data = map_data
        self.lbl_current_map.setText(f"<b>{map_data['name']}</b>")

        if map_data["is_injected"]:
            self.lbl_inject_status.setText(t("sandbox_tab.status_injected"))
            self.lbl_inject_status.setObjectName("BadgeWarning")
            self.btn_remove.setEnabled(True)
        else:
            self.lbl_inject_status.setText("🟢 STANDARD: Clean Original Script (No Injection)")
            self.lbl_inject_status.setObjectName("BadgeSuccess")
            self.btn_remove.setEnabled(False)

        self.lbl_inject_status.style().unpolish(self.lbl_inject_status)
        self.lbl_inject_status.style().polish(self.lbl_inject_status)
        self.btn_inject.setEnabled(True)

    def _build_options_dict(self) -> Dict[str, Any]:
        options = {
            "title_level": self.combo_title.currentData() or (self.combo_title.currentIndex() + 1),
            "b_castle": self.combo_castle.currentIndex() + 1,
            "b_storehouse": self.combo_storehouse.currentIndex() + 1,
            "b_church": self.combo_church.currentIndex() + 1,
            "reveal_fog": self.chk_fog.isChecked(),
            "instant_victory": self.chk_vic.isChecked(),
            "resources": {k: sb.value() for k, sb in self.res_spinboxes.items() if sb.value() > 0},
            "troops": {k: sb.value() for k, sb in self.troop_spinboxes.items() if sb.value() > 0}
        }
        return options

    def _update_lua_preview(self):
        code = self.sandbox_engine.generate_lua_sandbox_code(self._build_options_dict())
        self.txt_preview.setPlainText(code)

    def _on_inject(self):
        if not self.current_map_data:
            return
        script_path = self.current_map_data["script_path"]
        try:
            self.sandbox_engine.inject_sandbox_into_script(script_path, self._build_options_dict())
            self.log_signal.emit("success", f"Sandbox-Code erfolgreich in {os.path.basename(script_path)} injiziert.")
            self._update_map_item_status(True)
        except Exception as e:
            self.log_signal.emit("error", f"Fehler bei Injection: {e}")

    def _on_remove(self):
        if not self.current_map_data:
            return
        script_path = self.current_map_data["script_path"]
        try:
            removed = self.sandbox_engine.remove_sandbox_from_script(script_path)
            if removed:
                self.log_signal.emit("success", f"Sandbox-Code aus {os.path.basename(script_path)} entfernt.")
            else:
                self.log_signal.emit("info", "Kein Sandbox-Code gefunden.")
            self._update_map_item_status(False)
        except Exception as e:
            self.log_signal.emit("error", f"Fehler beim Entfernen: {e}")

    def _update_map_item_status(self, is_injected: bool):
        self.current_map_data["is_injected"] = is_injected
        item = self.list_maps.currentItem()
        if item:
            item.setData(Qt.ItemDataRole.UserRole, self.current_map_data)
            if is_injected:
                item.setForeground(QColor("#c59b27"))
            else:
                item.setForeground(QColor("#e4e8ee"))
        self._on_map_selection_changed(item, None)

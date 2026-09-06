import os
from typing import Dict, Any, Optional, List, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QFrame, QSplitter,
    QCheckBox, QComboBox, QPlainTextEdit, QScrollArea,
    QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView,
    QSpinBox, QGridLayout, QGroupBox, QTabWidget, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ModManager.engines.i18n_engine import t
from ModManager.engines.sandbox_engine import SandboxEngine
from ModManager.engines.system_engine import SystemEngine

class SandboxTab(QWidget):
    status_message = pyqtSignal(str, str)

    def __init__(self, sandbox_engine: SandboxEngine, system_engine: SystemEngine):
        super().__init__()
        self.system_engine = system_engine
        self.sandbox_engine = sandbox_engine
        self.current_map_data: Optional[Dict[str, Any]] = None
        self._revert_updaters: List[Callable[[], None]] = []

        self._init_ui()
        self.refresh_maps()

    def _create_combo_revert_btn(self, combo: QComboBox, default_idx: int = 0) -> QPushButton:
        btn = QPushButton("↺")
        btn.setObjectName("RevertBtn")
        btn.setFixedSize(28, 24)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(t("config_tab.tt_revert_btn").format(val_str=combo.itemText(default_idx)))

        def update_state():
            is_mod = (combo.currentIndex() != default_idx)
            mod_str = "true" if is_mod else "false"
            btn.setProperty("modified", mod_str)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            combo.setProperty("modified", mod_str)
            combo.style().unpolish(combo)
            combo.style().polish(combo)

        combo.currentIndexChanged.connect(lambda *_: update_state())
        btn.clicked.connect(lambda *_: combo.setCurrentIndex(default_idx))
        self._revert_updaters.append(update_state)
        update_state()
        return btn

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ---------------------------------------------------------------------
        # Top Action Bar
        # ---------------------------------------------------------------------
        top_card = QFrame()
        top_card.setObjectName("CardFrame")
        top_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(12, 10, 12, 10)
        top_layout.setSpacing(10)

        lbl_sandbox_mode = QLabel(t("sandbox_tab.title_supported_maps"))
        lbl_sandbox_mode.setStyleSheet("font-weight: bold; color: #94a3b8;")
        lbl_sandbox_mode.setMinimumHeight(32)
        lbl_sandbox_mode.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(lbl_sandbox_mode)

        top_layout.addStretch()

        self.btn_inject = QPushButton("⚡ " + t("sandbox_tab.btn_inject"))
        self.btn_inject.setObjectName("PrimaryButton")
        self.btn_inject.clicked.connect(self._on_inject)
        top_layout.addWidget(self.btn_inject)

        self.btn_remove = QPushButton("↺")
        self.btn_remove.setObjectName("HeaderRevertBtn")
        self.btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remove.setToolTip(t("sandbox_tab.btn_remove"))
        self.btn_remove.clicked.connect(self._on_remove)
        top_layout.addWidget(self.btn_remove)

        main_layout.addWidget(top_card)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # ------------------- LINKE SPALTE (Map List) -------------------
        left_card = QFrame()
        left_card.setObjectName("CardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)

        lbl_list_title = QLabel(t("sandbox_tab.title_supported_maps"))
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
        self.lbl_current_map = QLabel(f"<b>{t('sandbox_tab.no_map_selected')}</b>")
        h_pick.addWidget(self.lbl_current_map, 1)

        btn_refresh = QPushButton(t("sandbox_tab.btn_refresh"))
        btn_refresh.clicked.connect(self.refresh_maps)
        h_pick.addWidget(btn_refresh)
        l_map.addLayout(h_pick)

        self.lbl_inject_status = QLabel("")
        l_map.addWidget(self.lbl_inject_status)
        self.right_layout.addWidget(card_map)

        # -- 2. PRESET BAR
        card_opts = QFrame()
        card_opts.setObjectName("CardFrame")
        l_opts = QVBoxLayout(card_opts)
        
        h_preset = QHBoxLayout()
        h_preset.addWidget(QLabel(t("sandbox_tab.lbl_preset")))
        self.combo_preset = QComboBox()
        self.combo_preset.addItem(t("sandbox_tab.preset_vanilla"), "vanilla")
        self.combo_preset.addItem(t("sandbox_tab.preset_mid"), "mid")
        self.combo_preset.addItem(t("sandbox_tab.preset_high"), "high")
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        h_preset.addWidget(self.combo_preset, 1)
        l_opts.addLayout(h_preset)

        self.sub_tabs = QTabWidget()
        self.sub_tabs.setObjectName("SubTabWidget")

        # TAB 1: Player & Buildings
        tab_build = QWidget()
        tab_build_layout = QVBoxLayout(tab_build)
        grp_build = QGroupBox(t("sandbox_tab.grp_buildings"))
        grid_build = QGridLayout(grp_build)
        grid_build.setHorizontalSpacing(10)
        grid_build.setVerticalSpacing(8)
        grid_build.setColumnStretch(0, 0)
        grid_build.setColumnStretch(1, 0)
        grid_build.setColumnStretch(2, 0)
        grid_build.setColumnStretch(3, 0)
        grid_build.setColumnStretch(4, 1)

        # Header Row
        lbl_start = QLabel(t("sandbox_tab.col_res_start"))
        lbl_start.setObjectName("DimLabel")
        lbl_start.setStyleSheet("font-weight: bold; color: #aaaaaa; font-size: 11px;")
        lbl_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_build.addWidget(lbl_start, 0, 1)

        lbl_van = QLabel(t("sandbox_tab.col_res_vanilla"))
        lbl_van.setObjectName("DimLabel")
        lbl_van.setStyleSheet("font-weight: bold; color: #aaaaaa; font-size: 11px;")
        lbl_van.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_build.addWidget(lbl_van, 0, 2)

        lbl_rev = QLabel(t("config_tab.lbl_reset"))
        lbl_rev.setObjectName("DimLabel")
        lbl_rev.setStyleSheet("font-weight: bold; color: #aaaaaa; font-size: 11px;")
        lbl_rev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_build.addWidget(lbl_rev, 0, 3)

        def make_vanilla_badge(text: str) -> QLabel:
            b = QLabel(text)
            b.setObjectName("VanillaBadge")
            b.setAlignment(Qt.AlignmentFlag.AlignCenter)
            b.setFixedWidth(175)
            b.setToolTip(t("config_tab.tt_vanilla_badge").format(val_str=text))
            return b
        
        self.combo_player = QComboBox()
        self.combo_player.setFixedWidth(250)
        self.combo_player.addItem(t("sandbox_tab.player_default"), None)
        self.combo_player.addItem("Marcus", "Marcus")
        self.combo_player.addItem("Alandra", "Alandra")
        self.combo_player.addItem("Kestral", "Kestral")
        self.combo_player.addItem("Hakim", "Hakim")
        self.combo_player.addItem("Thordal", "Thordal")
        self.combo_player.addItem("Elias", "Elias")

        self.combo_title = QComboBox()
        self.combo_title.setFixedWidth(250)
        for i, text in enumerate([t("sandbox_tab.title_knight"), t("sandbox_tab.title_sheriff"), 
                                  t("sandbox_tab.title_baron"), t("sandbox_tab.title_earl"), 
                                  t("sandbox_tab.title_marquis"), t("sandbox_tab.title_duke")], 1):
            self.combo_title.addItem(text, i)
        
        self.combo_church = QComboBox()
        self.combo_storehouse = QComboBox()
        self.combo_castle = QComboBox()
        for cb in [self.combo_church, self.combo_storehouse, self.combo_castle]:
            cb.setFixedWidth(250)
            for i, text in enumerate([t("sandbox_tab.level_1"), t("sandbox_tab.level_2"), 
                                      t("sandbox_tab.level_3"), t("sandbox_tab.level_4")], 1):
                cb.addItem(text, i)
        
        # Col 1: Player & Title
        grid_build.addWidget(QLabel(t("sandbox_tab.lbl_overwrite_knight")), 1, 0)
        grid_build.addWidget(self.combo_player, 1, 1)
        grid_build.addWidget(make_vanilla_badge(self.combo_player.itemText(0)), 1, 2)
        grid_build.addWidget(self._create_combo_revert_btn(self.combo_player, 0), 1, 3)

        grid_build.addWidget(QLabel(t("sandbox_tab.lbl_title")), 2, 0)
        grid_build.addWidget(self.combo_title, 2, 1)
        grid_build.addWidget(make_vanilla_badge(self.combo_title.itemText(0)), 2, 2)
        grid_build.addWidget(self._create_combo_revert_btn(self.combo_title, 0), 2, 3)

        grid_build.addItem(QSpacerItem(20, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed), 3, 0, 1, 4)

        # Col 2: Church, Storehouse, Castle (matching tab_config order)
        grid_build.addWidget(QLabel(t("sandbox_tab.lbl_church")), 4, 0)
        grid_build.addWidget(self.combo_church, 4, 1)
        grid_build.addWidget(make_vanilla_badge(self.combo_church.itemText(0)), 4, 2)
        grid_build.addWidget(self._create_combo_revert_btn(self.combo_church, 0), 4, 3)

        grid_build.addWidget(QLabel(t("sandbox_tab.lbl_storehouse")), 5, 0)
        grid_build.addWidget(self.combo_storehouse, 5, 1)
        grid_build.addWidget(make_vanilla_badge(self.combo_storehouse.itemText(0)), 5, 2)
        grid_build.addWidget(self._create_combo_revert_btn(self.combo_storehouse, 0), 5, 3)

        grid_build.addWidget(QLabel(t("sandbox_tab.lbl_castle")), 6, 0)
        grid_build.addWidget(self.combo_castle, 6, 1)
        grid_build.addWidget(make_vanilla_badge(self.combo_castle.itemText(0)), 6, 2)
        grid_build.addWidget(self._create_combo_revert_btn(self.combo_castle, 0), 6, 3)
        
        for cb in [self.combo_player, self.combo_title, self.combo_church, self.combo_storehouse, self.combo_castle]:
            cb.currentIndexChanged.connect(self._update_lua_preview)
            
        tab_build_layout.addWidget(grp_build)
        tab_build_layout.addStretch()
        self.sub_tabs.addTab(tab_build, t("sandbox_tab.tab_title_buildings"))

        # TAB 2: Resources
        tab_res = QWidget()
        tab_res_layout = QVBoxLayout(tab_res)
        grp_res = QGroupBox(t("sandbox_tab.grp_resources"))
        v_res = QVBoxLayout(grp_res)
        self.table_res = QTableWidget(0, 4)
        self._setup_table(self.table_res, [
            t("sandbox_tab.col_res_name"), 
            t("sandbox_tab.col_res_start"), 
            t("sandbox_tab.col_res_vanilla"), 
            t("config_tab.lbl_reset")
        ])
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
        tab_res_layout.addWidget(grp_res)
        self.sub_tabs.addTab(tab_res, t("sandbox_tab.tab_start_resources"))

        # TAB 3: Troops
        tab_troops = QWidget()
        tab_troops_layout = QVBoxLayout(tab_troops)
        grp_troops = QGroupBox(t("sandbox_tab.grp_troops"))
        v_troops = QVBoxLayout(grp_troops)
        self.table_troops = QTableWidget(0, 4)
        self._setup_table(self.table_troops, [
            t("sandbox_tab.col_troop_name"), 
            t("sandbox_tab.col_res_start"), 
            t("sandbox_tab.col_res_vanilla"), 
            t("config_tab.lbl_reset")
        ])
        self.troop_spinboxes = {}
        self._add_troop_row("U_MilitarySword", t("sandbox_tab.troop_sword"), 0)
        self._add_troop_row("U_MilitaryBow", t("sandbox_tab.troop_bow"), 0)
        self._add_troop_row("U_CatapultCart", t("sandbox_tab.troop_siege"), 0)
        self._add_troop_row("U_Thief", t("sandbox_tab.troop_thief"), 0)
        v_troops.addWidget(self.table_troops)
        tab_troops_layout.addWidget(grp_troops)
        self.sub_tabs.addTab(tab_troops, t("sandbox_tab.tab_start_troops"))

        l_opts.addWidget(self.sub_tabs)

        # GROUP: Globals (always visible below tabs)
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
        lbl_prev_title = QLabel(t("sandbox_tab.lbl_preview"))
        lbl_prev_title.setStyleSheet("color: #94a3b8;")
        l_prev.addWidget(lbl_prev_title)

        self.txt_preview = QPlainTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setObjectName("LogConsole")
        self.txt_preview.setMinimumHeight(120)
        l_prev.addWidget(self.txt_preview)



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
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #2d3342;
                border-radius: 6px;
                background-color: #171922;
            }
            QTableWidget::item:hover { background-color: transparent; }
            QTableWidget::item:selected { background-color: transparent; }
        """)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(1, 110)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(2, 75)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(3, 55)
        table.horizontalHeader().setMinimumSectionSize(30)
        table.verticalHeader().setDefaultSectionSize(36)
        table.setMinimumHeight(260)

    def _add_res_row(self, res_id, name, vanilla_val):
        self._add_row_to_table(self.table_res, self.res_spinboxes, res_id, name, vanilla_val, max_val=999999)

    def _add_troop_row(self, troop_id, name, vanilla_val):
        self._add_row_to_table(self.table_troops, self.troop_spinboxes, troop_id, name, vanilla_val, max_val=100)

    def _add_row_to_table(self, table, sb_dict, item_id, name, vanilla_val, max_val):
        row = table.rowCount()
        table.insertRow(row)
        
        # Col 0: Item Name
        item_name = QTableWidgetItem(name)
        item_name.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        table.setItem(row, 0, item_name)
        
        # Col 1: SpinBox
        sb = QSpinBox()
        sb.setRange(0, max_val)
        sb.setValue(vanilla_val)
        sb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if max_val > 1000:
            sb.setSingleStep(50)
        sb.valueChanged.connect(self._update_lua_preview)
        sb_dict[item_id] = sb
        
        sb_wrap = QWidget()
        sb_l = QHBoxLayout(sb_wrap)
        sb_l.setContentsMargins(4, 2, 4, 2)
        sb_l.addWidget(sb)
        table.setCellWidget(row, 1, sb_wrap)
        
        # Col 2: Vanilla Badge (matches Tab 1)
        val_str = str(vanilla_val)
        lbl_van = QLabel(val_str)
        lbl_van.setObjectName("VanillaBadge")
        lbl_van.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_van.setToolTip(t("config_tab.tt_vanilla_badge").format(val_str=val_str))
        lbl_van.setFixedWidth(64)
        
        van_wrap = QWidget()
        van_l = QHBoxLayout(van_wrap)
        van_l.setContentsMargins(4, 2, 4, 2)
        van_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        van_l.addWidget(lbl_van)
        table.setCellWidget(row, 2, van_wrap)
        
        # Col 3: Revert Button (matches Tab 1)
        btn_reset = QPushButton("↺")
        btn_reset.setObjectName("RevertBtn")
        btn_reset.setToolTip(t("config_tab.tt_revert_btn").format(val_str=val_str))
        btn_reset.setFixedSize(28, 24)
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)

        def update_revert_state():
            is_mod = (sb.value() != vanilla_val)
            mod_str = "true" if is_mod else "false"
            btn_reset.setProperty("modified", mod_str)
            btn_reset.style().unpolish(btn_reset)
            btn_reset.style().polish(btn_reset)
            sb.setProperty("modified", mod_str)
            sb.style().unpolish(sb)
            sb.style().polish(sb)

        sb.valueChanged.connect(lambda *_: update_revert_state())
        btn_reset.clicked.connect(lambda *_: sb.setValue(vanilla_val))
        self._revert_updaters.append(update_revert_state)
        update_revert_state()

        btn_wrap = QWidget()
        btn_l = QHBoxLayout(btn_wrap)
        btn_l.setContentsMargins(0, 0, 0, 0)
        btn_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_l.addWidget(btn_reset)
        table.setCellWidget(row, 3, btn_wrap)

    def _on_preset_changed(self, index: int):
        preset_id = self.combo_preset.currentData()
        self._apply_preset(preset_id)

    def _apply_preset(self, preset_id: str):
        # Block signals to avoid cascading previews
        for cb in [self.combo_player, self.combo_title, self.combo_church, self.combo_storehouse, self.combo_castle]:
            cb.blockSignals(True)
        for sb in list(self.res_spinboxes.values()) + list(self.troop_spinboxes.values()):
            sb.blockSignals(True)
        self.chk_fog.blockSignals(True)
        self.chk_vic.blockSignals(True)

        # Reset all
        self.combo_player.setCurrentIndex(0)
        self.combo_title.setCurrentIndex(0)
        self.combo_church.setCurrentIndex(0)
        self.combo_storehouse.setCurrentIndex(0)
        self.combo_castle.setCurrentIndex(0)
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
            self.combo_church.setCurrentIndex(3)
            self.combo_storehouse.setCurrentIndex(3)
            self.combo_castle.setCurrentIndex(3) # Lvl 4
            self.res_spinboxes["G_Gold"].setValue(50000)
            for r in ["G_Wood", "G_Stone", "G_Iron", "G_Grain", "G_Wool", "G_Honeycomb", "G_Herb"]:
                self.res_spinboxes[r].setValue(500)
            self.troop_spinboxes["U_MilitarySword"].setValue(5)
            self.troop_spinboxes["U_MilitaryBow"].setValue(5)
            self.troop_spinboxes["U_CatapultCart"].setValue(2)
            self.chk_fog.setChecked(True)

        for cb in [self.combo_player, self.combo_title, self.combo_church, self.combo_storehouse, self.combo_castle]:
            cb.blockSignals(False)
        for sb in list(self.res_spinboxes.values()) + list(self.troop_spinboxes.values()):
            sb.blockSignals(False)
        self.chk_fog.blockSignals(False)
        self.chk_vic.blockSignals(False)

        # Refresh all revert visual states
        for fn in self._revert_updaters:
            fn()
        
        self._update_lua_preview()

    def refresh_maps(self):
        self.list_maps.clear()
        maps = self.sandbox_engine.list_testable_maps()
        for m in maps:
            item = QListWidgetItem(m["name"])
            item.setData(Qt.ItemDataRole.UserRole, m)
            if m["is_injected"]:
                item.setForeground(QColor("#c59b27"))
            self.list_maps.addItem(item)
        if self.list_maps.count() > 0:
            self.list_maps.setCurrentRow(0)
        self.status_message.emit("info", t("sandbox_tab.log_maps_refreshed"))

    def _on_map_selection_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if not current:
            self.current_map_data = None
            self.lbl_current_map.setText(f"<b>{t('sandbox_tab.no_map_selected')}</b>")
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
            self.lbl_inject_status.setText(t("sandbox_tab.status_clean"))
            self.lbl_inject_status.setObjectName("BadgeSuccess")
            self.btn_remove.setEnabled(False)

        self.lbl_inject_status.style().unpolish(self.lbl_inject_status)
        self.lbl_inject_status.style().polish(self.lbl_inject_status)
        self.btn_inject.setEnabled(True)

    def _build_options_dict(self) -> Dict[str, Any]:
        options = {
            "overwrite_knight": self.combo_player.currentData(),
            "title_level": self.combo_title.currentData() or (self.combo_title.currentIndex() + 1),
            "b_church": self.combo_church.currentIndex() + 1,
            "b_storehouse": self.combo_storehouse.currentIndex() + 1,
            "b_castle": self.combo_castle.currentIndex() + 1,
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
            self.status_message.emit("success", t("sandbox_tab.log_inject_success").format(name=os.path.basename(script_path)))
            self._update_map_item_status(True)
        except Exception as e:
            self.status_message.emit("error", t("sandbox_tab.log_inject_error").format(err=str(e)))

    def _on_remove(self):
        if not self.current_map_data:
            return
        script_path = self.current_map_data["script_path"]
        try:
            removed = self.sandbox_engine.remove_sandbox_from_script(script_path)
            if removed:
                self.status_message.emit("success", t("sandbox_tab.log_remove_success").format(name=os.path.basename(script_path)))
            else:
                self.status_message.emit("info", t("sandbox_tab.log_no_sandbox_found"))
            self._update_map_item_status(False)
        except Exception as e:
            self.status_message.emit("error", t("sandbox_tab.log_remove_error").format(err=str(e)))

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

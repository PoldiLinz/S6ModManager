"""
Siedler 6 Mod Manager - Tab 1: Konfigurationen & Limits
Bietet Live-Editor für Siedlerlimit, Stufen-Upgrades, Wirtschaft und Militär.
Alle Einstellungen sind kompakt und übersichtlich in einer Spalte (Rasterform) angeordnet,
sodass Beschreibung, Eingabefeld, Vanilla-Badge und Lightroom-Revert-Button (↺) direkt
nebeneinander liegen – als saubere Tabelle untereinander.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QTabWidget, QScrollArea, QFrame, QGroupBox, QMessageBox,
    QInputDialog, QRadioButton, QButtonGroup, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, Any, Optional

from ModManager.engines.config_engine import ConfigEngine
from ModManager.engines.system_engine import SystemEngine
from ModManager.engines import t


# Vanilla-Referenzwerte für Die Siedler: Aufstieg eines Königreichs
VANILLA_DEFAULTS = {
    # Siedlerlimits
    "settler_1": 50,
    "settler_2": 100,
    "settler_3": 150,
    "settler_4": 200,

    # Lagerhaus
    "store_1": 54,
    "store_2": 108,
    "store_3": 162,
    "store_4": 216,
    "store_max": 18,
    "store_gold": 500,

    # Burg & Schloss
    "castle_soldier_1": 25,
    "castle_soldier_2": 43,
    "castle_soldier_3": 61,
    "castle_soldier_4": 91,
    "castle_treasury": 20000,
    "castle_hp": 3000,

    # Kathedrale
    "cath_sermon": 60,
    "cath_prestige": 400,

    # Rohstoffe & Wirtschaft
    "mine_stone": 250,
    "mine_iron": 250,
    "well_refill": 0.5,
    "well_cap": 100,
    "road_speed": 1.25,
    "cart_speed": 320,
    "workshop_cap": 9,

    # Militär
    "battalion_size": 6,
    "wall_gate": 1200,
    "wall_turret": 1000,
    "wall_segment": 800,
    "soldier_speed": 480,
    "soldier_hp": 120,
}


class ConfigTab(QWidget):
    """Registerkarte für Spiel-Konfigurationen und Limits."""

    status_message = pyqtSignal(str, str)  # (message, type: 'info'|'success'|'warning'|'error')

    def __init__(self, config_engine: ConfigEngine, system_engine: SystemEngine, parent=None):
        super().__init__(parent)
        self.config_engine = config_engine
        self.system = system_engine

        self._init_ui()
        
        # Single Source of Truth: Die tatsächlichen XML-Dateien im ModLoader scannen
        active_config = self.config_engine.read_active_config_from_modloader()
        self._apply_data_to_widgets(active_config)
        self.status_message.emit(t("config_tab.msg_config_loaded"), "info")

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Top Action & Preset Bar
        top_card = QFrame()
        top_card.setObjectName("CardFrame")
        top_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(12, 10, 12, 10)
        top_layout.setSpacing(10)

        lbl_preset = QLabel(t("config_tab.lbl_preset"))
        lbl_preset.setStyleSheet("font-weight: bold;")
        lbl_preset.setMinimumHeight(32)
        lbl_preset.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(lbl_preset)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(240)
        self._refresh_presets_combo()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        top_layout.addWidget(self.preset_combo)

        btn_save_preset = QPushButton(t("config_tab.btn_save_preset"))
        btn_save_preset.clicked.connect(self._on_save_preset)
        top_layout.addWidget(btn_save_preset)

        top_layout.addStretch()

        btn_apply = QPushButton(t("config_tab.btn_apply"))
        btn_apply.setObjectName("PrimaryButton")
        btn_apply.clicked.connect(self._on_apply_config)
        top_layout.addWidget(btn_apply)

        btn_restore_vanilla = QPushButton("↺")
        btn_restore_vanilla.setObjectName("HeaderRevertBtn")
        btn_restore_vanilla.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_restore_vanilla.setToolTip(t("config_tab.btn_restore_vanilla"))
        btn_restore_vanilla.clicked.connect(self._on_restore_vanilla)
        top_layout.addWidget(btn_restore_vanilla)

        main_layout.addWidget(top_card)

        # 2. Sub-Tabs für Kategorien
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setObjectName("SubTabWidget")

        self.sub_tabs.addTab(self._create_main_buildings_tab(), t("config_tab.tab_buildings"))
        self.sub_tabs.addTab(self._create_economy_tab(), t("config_tab.tab_economy"))
        self.sub_tabs.addTab(self._create_military_tab(), t("config_tab.tab_military"))

        main_layout.addWidget(self.sub_tabs)

    # -------------------------------------------------------------------------
    # Layout- und Einstellungs-Hilfsmethoden
    # -------------------------------------------------------------------------

    def _setup_grid(self, box: QGroupBox) -> QGridLayout:
        """Erstellt ein standardisiertes 1-Spalten-Block Grid-Layout als Tabelle mit Headern."""
        grid = QGridLayout(box)
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(8)
        grid.setContentsMargins(14, 16, 14, 14)

        for col in range(4):
            grid.setColumnStretch(col, 0)
        grid.setColumnStretch(4, 1)

        lbl_mod = QLabel(t("config_tab.lbl_modded"))
        lbl_mod.setObjectName("DimLabel")
        lbl_mod.setStyleSheet("font-weight: bold; color: #aaaaaa; font-size: 11px;")
        lbl_mod.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(lbl_mod, 0, 1)

        lbl_van = QLabel(t("config_tab.lbl_vanilla"))
        lbl_van.setObjectName("DimLabel")
        lbl_van.setStyleSheet("font-weight: bold; color: #aaaaaa; font-size: 11px;")
        lbl_van.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(lbl_van, 0, 2)

        lbl_rev = QLabel(t("config_tab.lbl_reset"))
        lbl_rev.setObjectName("DimLabel")
        lbl_rev.setStyleSheet("font-weight: bold; color: #aaaaaa; font-size: 11px;")
        lbl_rev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(lbl_rev, 0, 3)

        return grid

    def _add_setting_item(
        self,
        grid: QGridLayout,
        row: int,
        col_offset: int,
        label_text: str,
        spin_widget: QSpinBox | QDoubleSpinBox,
        vanilla_val: int | float,
        label_width: int = 240,
        value_width: int = 140
    ) -> QPushButton:
        """Fügt eine Einheit [Label | SpinBox | Vanilla-Badge | Revert-Button] direkt nebeneinander ein."""
        # Da Row 0 nun Header ist, verschieben wir den übergebenen Row-Index intern um 1!
        row += 1

        lbl = QLabel(label_text)
        lbl.setMinimumWidth(label_width)
        grid.addWidget(lbl, row, col_offset)

        spin_widget.setFixedWidth(value_width)
        grid.addWidget(spin_widget, row, col_offset + 1)

        val_str = f"{vanilla_val:g}" if isinstance(vanilla_val, float) else str(vanilla_val)
        lbl_vanilla = QLabel(val_str)
        lbl_vanilla.setObjectName("VanillaBadge")
        lbl_vanilla.setToolTip(t("config_tab.tt_vanilla_badge").format(val_str=val_str))
        lbl_vanilla.setFixedWidth(value_width)
        lbl_vanilla.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(lbl_vanilla, row, col_offset + 2)

        # Spalte col_offset + 3: Lightroom Revert-Button
        btn_revert = QPushButton("↺")
        btn_revert.setObjectName("RevertBtn")
        btn_revert.setToolTip(t("config_tab.tt_revert_btn").format(val_str=val_str))
        btn_revert.setFixedSize(28, 24)
        btn_revert.setCursor(Qt.CursorShape.PointingHandCursor)

        def update_revert_state():
            cur = spin_widget.value()
            is_mod = abs(cur - vanilla_val) > 1e-4
            mod_str = "true" if is_mod else "false"
            btn_revert.setProperty("modified", mod_str)
            btn_revert.style().unpolish(btn_revert)
            btn_revert.style().polish(btn_revert)
            spin_widget.setProperty("modified", mod_str)
            spin_widget.style().unpolish(spin_widget)
            spin_widget.style().polish(spin_widget)
            spin_widget.update()

        spin_widget.valueChanged.connect(lambda *_: update_revert_state())
        btn_revert.clicked.connect(lambda *_: spin_widget.setValue(vanilla_val))

        update_revert_state()
        grid.addWidget(btn_revert, row, col_offset + 3)

        return btn_revert

    def _create_spin(self, min_val: int, max_val: int, val: int, step: int = 1) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(val)
        spin.setSingleStep(step)
        return spin

    def _create_double_spin(self, min_val: float, max_val: float, val: float, step: float = 0.1, decimals: int = 2) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(step)
        spin.setValue(val)
        spin.setDecimals(decimals)
        return spin

    # -------------------------------------------------------------------------
    # Sub-Tab 1: Hauptgebäude & Siedlerlimit
    # -------------------------------------------------------------------------

    def _create_main_buildings_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(6, 6, 6, 6)

        # A. Siedlerlimit
        box_settlers = QGroupBox(t("config_tab.group_settlers"))
        g_settlers = self._setup_grid(box_settlers)

        self.spin_settler_1 = self._create_spin(50, 2000, 100, 10)
        self.btn_revert_settler_1 = self._add_setting_item(g_settlers, 0, 0, t("config_tab.settler_1"), self.spin_settler_1, VANILLA_DEFAULTS["settler_1"])

        self.spin_settler_2 = self._create_spin(50, 3000, 300, 25)
        self._add_setting_item(g_settlers, 1, 0, t("config_tab.settler_2"), self.spin_settler_2, VANILLA_DEFAULTS["settler_2"])

        self.spin_settler_3 = self._create_spin(50, 4000, 500, 50)
        self._add_setting_item(g_settlers, 2, 0, t("config_tab.settler_3"), self.spin_settler_3, VANILLA_DEFAULTS["settler_3"])

        self.spin_settler_4 = self._create_spin(50, 5000, 800, 100)
        self._add_setting_item(g_settlers, 3, 0, t("config_tab.settler_4"), self.spin_settler_4, VANILLA_DEFAULTS["settler_4"])

        lbl_settler_info = QLabel(t("config_tab.settler_hint"))
        lbl_settler_info.setObjectName("DimLabel")
        g_settlers.addWidget(lbl_settler_info, 5, 0, 1, 5)

        layout.addWidget(box_settlers)

        # B. Lagerhaus
        box_store = QGroupBox(t("config_tab.group_storehouse"))
        g_store = self._setup_grid(box_store)

        self.spin_store_1 = self._create_spin(10, 5000, 54, 10)
        self._add_setting_item(g_store, 0, 0, t("config_tab.store_1"), self.spin_store_1, VANILLA_DEFAULTS["store_1"])

        self.spin_store_2 = self._create_spin(10, 5000, 250, 50)
        self._add_setting_item(g_store, 1, 0, t("config_tab.store_2"), self.spin_store_2, VANILLA_DEFAULTS["store_2"])

        self.spin_store_3 = self._create_spin(10, 5000, 500, 50)
        self._add_setting_item(g_store, 2, 0, t("config_tab.store_3"), self.spin_store_3, VANILLA_DEFAULTS["store_3"])

        self.spin_store_4 = self._create_spin(10, 5000, 1000, 100)
        self._add_setting_item(g_store, 3, 0, t("config_tab.store_4"), self.spin_store_4, VANILLA_DEFAULTS["store_4"])

        self.spin_store_max = self._create_spin(10, 500, 60, 5)
        self._add_setting_item(g_store, 4, 0, t("config_tab.store_max"), self.spin_store_max, VANILLA_DEFAULTS["store_max"])

        self.spin_store_gold = self._create_spin(0, 5000, 250, 50)
        self._add_setting_item(g_store, 5, 0, t("config_tab.store_gold"), self.spin_store_gold, VANILLA_DEFAULTS["store_gold"])

        layout.addWidget(box_store)

        # C. Burg / Schloss
        box_castle = QGroupBox(t("config_tab.group_castle"))
        g_castle = self._setup_grid(box_castle)

        self.spin_castle_soldier_1 = self._create_spin(5, 500, 30, 5)
        self._add_setting_item(g_castle, 0, 0, t("config_tab.castle_soldier_1"), self.spin_castle_soldier_1, VANILLA_DEFAULTS["castle_soldier_1"])

        self.spin_castle_soldier_2 = self._create_spin(5, 500, 55, 5)
        self._add_setting_item(g_castle, 1, 0, t("config_tab.castle_soldier_2"), self.spin_castle_soldier_2, VANILLA_DEFAULTS["castle_soldier_2"])

        self.spin_castle_soldier_3 = self._create_spin(5, 500, 85, 5)
        self._add_setting_item(g_castle, 2, 0, t("config_tab.castle_soldier_3"), self.spin_castle_soldier_3, VANILLA_DEFAULTS["castle_soldier_3"])

        self.spin_castle_soldier_4 = self._create_spin(5, 500, 130, 10)
        self._add_setting_item(g_castle, 3, 0, t("config_tab.castle_soldier_4"), self.spin_castle_soldier_4, VANILLA_DEFAULTS["castle_soldier_4"])

        self.spin_castle_treasury = self._create_spin(5000, 99000, 99000, 5000)
        self._add_setting_item(g_castle, 4, 0, t("config_tab.castle_treasury"), self.spin_castle_treasury, VANILLA_DEFAULTS["castle_treasury"])

        self.spin_castle_hp = self._create_spin(500, 20000, 5000, 500)
        self._add_setting_item(g_castle, 5, 0, t("config_tab.castle_hp"), self.spin_castle_hp, VANILLA_DEFAULTS["castle_hp"])

        layout.addWidget(box_castle)

        # D. Kathedrale
        box_cath = QGroupBox(t("config_tab.group_cathedral"))
        g_cath = self._setup_grid(box_cath)

        self.spin_cath_sermon = self._create_spin(10, 500, 120, 10)
        self._add_setting_item(g_cath, 0, 0, t("config_tab.cath_sermon"), self.spin_cath_sermon, VANILLA_DEFAULTS["cath_sermon"])

        self.spin_cath_prestige = self._create_spin(50, 2000, 500, 50)
        self._add_setting_item(g_cath, 1, 0, t("config_tab.cath_prestige"), self.spin_cath_prestige, VANILLA_DEFAULTS["cath_prestige"])

        layout.addWidget(box_cath)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    # -------------------------------------------------------------------------
    # Sub-Tab 2: Wirtschaft & Ressourcen
    # -------------------------------------------------------------------------

    def _create_economy_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(6, 6, 6, 6)

        # A. Rohstoff-Minen
        box_mines = QGroupBox(t("config_tab.group_mines"))
        g_mines = self._setup_grid(box_mines)

        self.spin_mine_stone = self._create_spin(250, 999999, 999999, 1000)
        self._add_setting_item(g_mines, 0, 0, t("config_tab.mine_stone"), self.spin_mine_stone, VANILLA_DEFAULTS["mine_stone"])

        self.spin_mine_iron = self._create_spin(250, 999999, 999999, 1000)
        self._add_setting_item(g_mines, 1, 0, t("config_tab.mine_iron"), self.spin_mine_iron, VANILLA_DEFAULTS["mine_iron"])
        layout.addWidget(box_mines)

        # B. Brunnen & Löschwasser
        box_well = QGroupBox(t("config_tab.group_well"))
        g_well = self._setup_grid(box_well)

        self.spin_well_refill = self._create_double_spin(0.1, 10.0, 1.5, 0.1, 1)
        self._add_setting_item(g_well, 0, 0, t("config_tab.well_refill"), self.spin_well_refill, VANILLA_DEFAULTS["well_refill"])

        self.spin_well_cap = self._create_spin(25, 1000, 200, 25)
        self._add_setting_item(g_well, 1, 0, t("config_tab.well_cap"), self.spin_well_cap, VANILLA_DEFAULTS["well_cap"])

        layout.addWidget(box_well)

        # C. Straßen & Logistik
        box_logistics = QGroupBox(t("config_tab.group_logistics"))
        g_log = self._setup_grid(box_logistics)

        self.spin_road_speed = self._create_double_spin(1.0, 3.0, 1.4, 0.05, 2)
        self._add_setting_item(g_log, 0, 0, t("config_tab.road_speed"), self.spin_road_speed, VANILLA_DEFAULTS["road_speed"])

        self.spin_cart_speed = self._create_spin(200, 1000, 400, 20)
        self._add_setting_item(g_log, 1, 0, t("config_tab.cart_speed"), self.spin_cart_speed, VANILLA_DEFAULTS["cart_speed"])

        self.spin_workshop_cap = self._create_spin(9, 100, 18, 3)
        self._add_setting_item(g_log, 2, 0, t("config_tab.workshop_cap"), self.spin_workshop_cap, VANILLA_DEFAULTS["workshop_cap"])

        layout.addWidget(box_logistics)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    # -------------------------------------------------------------------------
    # Sub-Tab 3: Militär & Verteidigung
    # -------------------------------------------------------------------------

    def _create_military_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(6, 6, 6, 6)

        # A. Bataillonsgröße
        box_bat = QGroupBox(t("config_tab.group_battalion"))
        g_bat = self._setup_grid(box_bat)

        lbl_bat = QLabel(t("config_tab.lbl_bat_size"))
        lbl_bat.setMinimumWidth(240)
        g_bat.addWidget(lbl_bat, 1, 0)

        h_bat = QHBoxLayout()
        h_bat.setSpacing(10)
        self.btn_group_bat = QButtonGroup(self)

        self.radio_bat_6 = QRadioButton(t("config_tab.bat_6"))
        self.radio_bat_9 = QRadioButton(t("config_tab.bat_9"))
        self.radio_bat_12 = QRadioButton(t("config_tab.bat_12"))

        self.btn_group_bat.addButton(self.radio_bat_6, 6)
        self.btn_group_bat.addButton(self.radio_bat_9, 9)
        self.btn_group_bat.addButton(self.radio_bat_12, 12)

        self.radio_bat_9.setChecked(True)

        h_bat.addWidget(self.radio_bat_6)
        h_bat.addWidget(self.radio_bat_9)
        h_bat.addWidget(self.radio_bat_12)
        h_bat.addStretch()

        g_bat.addLayout(h_bat, 1, 1)

        lbl_van_bat = QLabel("6")
        lbl_van_bat.setObjectName("VanillaBadge")
        lbl_van_bat.setToolTip(t("config_tab.tt_van_bat"))
        lbl_van_bat.setFixedWidth(140)
        lbl_van_bat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        g_bat.addWidget(lbl_van_bat, 1, 2)

        btn_rev_bat = QPushButton("↺")
        btn_rev_bat.setObjectName("RevertBtn")
        btn_rev_bat.setToolTip(t("config_tab.tt_rev_bat"))
        btn_rev_bat.setFixedSize(28, 24)
        btn_rev_bat.setCursor(Qt.CursorShape.PointingHandCursor)

        def update_bat_revert():
            is_mod = not self.radio_bat_6.isChecked()
            btn_rev_bat.setProperty("modified", "true" if is_mod else "false")
            btn_rev_bat.style().unpolish(btn_rev_bat)
            btn_rev_bat.style().polish(btn_rev_bat)

        self.btn_group_bat.idToggled.connect(lambda _id, _checked: update_bat_revert())
        btn_rev_bat.clicked.connect(lambda *_: self.radio_bat_6.setChecked(True))
        update_bat_revert()

        g_bat.addWidget(btn_rev_bat, 1, 3)
        layout.addWidget(box_bat)

        # B. Mauern & Befestigung
        box_walls = QGroupBox(t("config_tab.group_walls"))
        g_walls = self._setup_grid(box_walls)

        self.spin_wall_gate = self._create_spin(500, 20000, 3000, 250)
        self._add_setting_item(g_walls, 0, 0, t("config_tab.wall_gate"), self.spin_wall_gate, VANILLA_DEFAULTS["wall_gate"])

        self.spin_wall_turret = self._create_spin(500, 20000, 2500, 250)
        self._add_setting_item(g_walls, 1, 0, t("config_tab.wall_turret"), self.spin_wall_turret, VANILLA_DEFAULTS["wall_turret"])

        self.spin_wall_segment = self._create_spin(500, 20000, 2000, 200)
        self._add_setting_item(g_walls, 2, 0, t("config_tab.wall_segment"), self.spin_wall_segment, VANILLA_DEFAULTS["wall_segment"])

        layout.addWidget(box_walls)

        # C. Soldaten
        box_units = QGroupBox(t("config_tab.group_units"))
        g_units = self._setup_grid(box_units)

        self.spin_soldier_speed = self._create_spin(300, 1000, 540, 20)
        self._add_setting_item(g_units, 0, 0, t("config_tab.soldier_speed"), self.spin_soldier_speed, VANILLA_DEFAULTS["soldier_speed"])

        self.spin_soldier_hp = self._create_spin(50, 1000, 160, 10)
        self._add_setting_item(g_units, 1, 0, t("config_tab.soldier_hp"), self.spin_soldier_hp, VANILLA_DEFAULTS["soldier_hp"])

        layout.addWidget(box_units)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    # -------------------------------------------------------------------------
    # Presets & Event Handlers
    # -------------------------------------------------------------------------

    def _refresh_presets_combo(self):
        self.preset_combo.clear()
        presets = self.config_engine.list_presets()
        for p in presets:
            self.preset_combo.addItem(p["name"], p["filename"])

    def _load_initial_preset(self, filename: str):
        index = self.preset_combo.findData(filename)
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)

    def load_preset_by_filename(self, filename: str):
        """Öffentliche Methode zum Laden eines Presets per Dateiname."""
        self._load_initial_preset(filename)

    def _on_preset_changed(self, index: int):
        filename = self.preset_combo.currentData()
        if not filename:
            return
        try:
            data = self.config_engine.load_preset(filename)
            self._apply_data_to_widgets(data)
            self.status_message.emit(t("config_tab.msg_preset_loaded").format(name=data.get('name', filename)), "info")
        except Exception as e:
            self.status_message.emit(t("config_tab.msg_preset_load_err").format(err=e), "error")

    def _apply_data_to_widgets(self, data: Dict[str, Any]):
        # Settler limits
        s_limits = data.get("settler_limits", [50, 50, 100, 150, 200, 200])
        self.spin_settler_1.setValue(s_limits[0] if len(s_limits) > 0 else 50)
        self.spin_settler_2.setValue(s_limits[2] if len(s_limits) > 2 else 100)
        self.spin_settler_3.setValue(s_limits[3] if len(s_limits) > 3 else 150)
        self.spin_settler_4.setValue(s_limits[4] if len(s_limits) > 4 else 200)

        # Storehouse
        s_caps = data.get("storehouse_capacities", [54, 108, 162, 216])
        self.spin_store_1.setValue(s_caps[0] if len(s_caps) > 0 else 54)
        self.spin_store_2.setValue(s_caps[1] if len(s_caps) > 1 else 108)
        self.spin_store_3.setValue(s_caps[2] if len(s_caps) > 2 else 162)
        self.spin_store_4.setValue(s_caps[3] if len(s_caps) > 3 else 216)
        self.spin_store_max.setValue(data.get("storehouse_max_amount_on_stock", 18))

        # Storehouse Upgrade Gold (letzter Wert wird im UI exponiert)
        s_gold = data.get("storehouse_upgrade_gold", [150, 250, 250])
        self.spin_store_gold.setValue(s_gold[-1] if s_gold else 250)

        # Castle
        c_soldiers = data.get("castle_soldier_limits", [25, 43, 61, 91])
        self.spin_castle_soldier_1.setValue(c_soldiers[0] if len(c_soldiers) > 0 else 25)
        self.spin_castle_soldier_2.setValue(c_soldiers[1] if len(c_soldiers) > 1 else 43)
        self.spin_castle_soldier_3.setValue(c_soldiers[2] if len(c_soldiers) > 2 else 61)
        self.spin_castle_soldier_4.setValue(c_soldiers[3] if len(c_soldiers) > 3 else 91)

        c_treasury = data.get("castle_treasury_capacities", [20000, 20000, 20000, 20000])
        self.spin_castle_treasury.setValue(c_treasury[-1] if c_treasury else 20000)
        c_hp = data.get("castle_hitpoints", [750, 1500, 2250, 3000])
        self.spin_castle_hp.setValue(c_hp[-1] if c_hp else 3000)

        # Cathedral
        c_sermon = data.get("cathedral_sermon_limits", [10, 15, 30, 60])
        self.spin_cath_sermon.setValue(c_sermon[-1] if c_sermon else 60)
        c_prestige = data.get("cathedral_prestige_points", [100, 200, 400])
        self.spin_cath_prestige.setValue(c_prestige[-1] if c_prestige else 400)

        # Economy
        self.spin_mine_stone.setValue(data.get("mine_stone_capacity", 250))
        self.spin_mine_iron.setValue(data.get("mine_iron_capacity", 250))
        self.spin_well_refill.setValue(data.get("well_water_refill_rate", 0.5))
        w_cap = data.get("well_water_capacity", [25, 50, 75, 100])
        self.spin_well_cap.setValue(w_cap[-1] if w_cap else 100)
        self.spin_road_speed.setValue(data.get("road_speed_modifier", 1.25))
        self.spin_cart_speed.setValue(data.get("cart_speed", 320))
        self.spin_workshop_cap.setValue(data.get("workshop_output_capacity", 9))

        # Military
        b_size = data.get("battalion_size", 6)
        if b_size == 6:
            self.radio_bat_6.setChecked(True)
        elif b_size == 12:
            self.radio_bat_12.setChecked(True)
        else:
            self.radio_bat_9.setChecked(True)

        self.spin_wall_gate.setValue(data.get("wall_gate_health", 1200))
        self.spin_wall_turret.setValue(data.get("wall_turret_health", 1000))
        self.spin_wall_segment.setValue(data.get("wall_segment_health", 800))
        self.spin_soldier_speed.setValue(data.get("soldier_speed", 480))
        self.spin_soldier_hp.setValue(data.get("soldier_health", 120))

    def _collect_data_from_widgets(self) -> Dict[str, Any]:
        s1 = self.spin_settler_1.value()
        s2 = self.spin_settler_2.value()
        s3 = self.spin_settler_3.value()
        s4 = self.spin_settler_4.value()

        b_size = 9
        if self.radio_bat_6.isChecked():
            b_size = 6
        elif self.radio_bat_12.isChecked():
            b_size = 12

        return {
            "settler_limits": [s1, s1, s2, s3, s4, s4],
            "road_speed_modifier": self.spin_road_speed.value(),
            "storehouse_capacities": [
                self.spin_store_1.value(),
                self.spin_store_2.value(),
                self.spin_store_3.value(),
                self.spin_store_4.value()
            ],
            "storehouse_max_amount_on_stock": self.spin_store_max.value(),
            "storehouse_upgrade_gold": [150, 250, self.spin_store_gold.value()],
            "storehouse_upgrade_stone": [20, 40, 60],
            "storehouse_upgrade_seconds": [25, 50, 100],
            "storehouse_upgrade_settlers": [5, 10, 20],
            "castle_soldier_limits": [
                self.spin_castle_soldier_1.value(),
                self.spin_castle_soldier_2.value(),
                self.spin_castle_soldier_3.value(),
                self.spin_castle_soldier_4.value()
            ],
            "castle_treasury_capacities": [
                self.spin_castle_treasury.value() // 2,
                self.spin_castle_treasury.value() // 2,
                self.spin_castle_treasury.value(),
                self.spin_castle_treasury.value()
            ],
            "castle_hitpoints": [
                self.spin_castle_hp.value() // 4,
                self.spin_castle_hp.value() // 2,
                int(self.spin_castle_hp.value() * 0.75),
                self.spin_castle_hp.value()
            ],
            "cathedral_sermon_limits": [
                self.spin_cath_sermon.value() // 4,
                self.spin_cath_sermon.value() // 2,
                int(self.spin_cath_sermon.value() * 0.75),
                self.spin_cath_sermon.value()
            ],
            "cathedral_prestige_points": [
                self.spin_cath_prestige.value() // 4,
                self.spin_cath_prestige.value() // 2,
                self.spin_cath_prestige.value()
            ],
            "mine_stone_capacity": self.spin_mine_stone.value(),
            "mine_iron_capacity": self.spin_mine_iron.value(),
            "well_water_refill_rate": self.spin_well_refill.value(),
            "well_water_capacity": [
                self.spin_well_cap.value() // 4,
                self.spin_well_cap.value() // 2,
                int(self.spin_well_cap.value() * 0.75),
                self.spin_well_cap.value()
            ],
            "cart_speed": self.spin_cart_speed.value(),
            "workshop_output_capacity": self.spin_workshop_cap.value(),
            "battalion_size": b_size,
            "wall_gate_health": self.spin_wall_gate.value(),
            "wall_turret_health": self.spin_wall_turret.value(),
            "wall_segment_health": self.spin_wall_segment.value(),
            "soldier_speed": self.spin_soldier_speed.value(),
            "soldier_health": self.spin_soldier_hp.value()
        }

    def _on_apply_config(self):
        try:
            config = self._collect_data_from_widgets()
            count = self.config_engine.apply_config_to_modloader(config)
            msg = t("config_tab.msg_config_applied").format(count=count)
            self.status_message.emit(msg, "success")
            QMessageBox.information(self, t("config_tab.btn_apply"), msg)
        except Exception as e:
            err = t("config_tab.msg_config_apply_err").format(err=e)
            self.status_message.emit(err, "error")
            QMessageBox.critical(self, t("app.error") if t("app.error") != "app.error" else "Error", err)

    def _on_restore_vanilla(self):
        reply = QMessageBox.question(
            self,
            t("config_tab.title_restore"),
            t("config_tab.msg_restore_prompt"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                removed = self.config_engine.restore_vanilla_configs()
                # Aktuelle Dateien neu einlesen (Single Source of Truth)
                active_config = self.config_engine.read_active_config_from_modloader()
                self._apply_data_to_widgets(active_config)
                msg = t("config_tab.msg_restore_success").format(count=removed)
                self.status_message.emit(msg, "warning")
                QMessageBox.information(self, t("config_tab.title_restore"), msg)
            except Exception as e:
                err = t("config_tab.msg_restore_err").format(err=e)
                self.status_message.emit(err, "error")
                QMessageBox.critical(self, t("app.error") if t("app.error") != "app.error" else "Error", err)

    def _on_save_preset(self):
        name, ok = QInputDialog.getText(self, t("config_tab.title_save_preset"), t("config_tab.msg_save_preset_prompt"))
        if ok and name.strip():
            filename = f"Custom_{name.strip().replace(' ', '_')}.json"
            data = self._collect_data_from_widgets()
            data["name"] = name.strip()
            
            # Use dictionary or fallback
            profile_prefix = t("config_tab.custom_profile_prefix") 
            if profile_prefix == "config_tab.custom_profile_prefix":
                profile_prefix = "Custom Profile: "
            data["description"] = f"{profile_prefix}{name.strip()}"
            
            self.config_engine.save_custom_preset(filename, data)
            self._refresh_presets_combo()
            self._load_initial_preset(filename)
            self.status_message.emit(t("config_tab.msg_save_preset_success").format(filename=filename), "success")

"""
Siedler 6 Mod Manager - Tab 1: Konfigurationen & Limits
Bietet Live-Editor für Siedlerlimit, Stufen-Upgrades, Wirtschaft und Militär.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QSlider,
    QTabWidget, QScrollArea, QFrame, QGroupBox, QMessageBox,
    QInputDialog, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, Any, Optional

from ModManager.engines.config_engine import ConfigEngine
from ModManager.engines.system_engine import SystemEngine


class ConfigTab(QWidget):
    """Registerkarte für Spiel-Konfigurationen und Limits."""

    status_message = pyqtSignal(str, str)  # (message, type: 'info'|'success'|'warning'|'error')

    def __init__(self, config_engine: ConfigEngine, system_engine: SystemEngine, parent=None):
        super().__init__(parent)
        self.config_engine = config_engine
        self.system = system_engine

        self._init_ui()
        self._load_initial_preset("Extended_Balanced.json")

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Top Action & Preset Bar
        top_card = QFrame()
        top_card.setObjectName("CardFrame")
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(8, 8, 8, 8)

        top_layout.addWidget(QLabel("Preset-Profil:"))
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(220)
        self._refresh_presets_combo()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        top_layout.addWidget(self.preset_combo)

        btn_save_preset = QPushButton("💾 Als Preset sichern")
        btn_save_preset.clicked.connect(self._on_save_preset)
        top_layout.addWidget(btn_save_preset)

        top_layout.addStretch()

        btn_restore_vanilla = QPushButton("🔄 Vanilla wiederherstellen")
        btn_restore_vanilla.setObjectName("DangerButton")
        btn_restore_vanilla.clicked.connect(self._on_restore_vanilla)
        top_layout.addWidget(btn_restore_vanilla)

        btn_apply = QPushButton("🚀 Konfiguration anwenden")
        btn_apply.setObjectName("PrimaryButton")
        btn_apply.clicked.connect(self._on_apply_config)
        top_layout.addWidget(btn_apply)

        main_layout.addWidget(top_card)

        # 2. Sub-Tabs für Kategorien
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setObjectName("SubTabWidget")

        self.sub_tabs.addTab(self._create_main_buildings_tab(), "🏛️ Hauptgebäude & Siedlerlimit")
        self.sub_tabs.addTab(self._create_economy_tab(), "⛏️ Wirtschaft & Ressourcen")
        self.sub_tabs.addTab(self._create_military_tab(), "⚔️ Militär & Verteidigung")

        main_layout.addWidget(self.sub_tabs)

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

        # A. Siedlerlimit
        box_settlers = QGroupBox("Globales Siedlerlimit (Kathedralen-Ausbaustufen)")
        g_settlers = QGridLayout(box_settlers)

        g_settlers.addWidget(QLabel("Ohne / Kathedrale Stufe 1:"), 0, 0)
        self.spin_settler_1 = self._create_spin(50, 2000, 100, 10)
        g_settlers.addWidget(self.spin_settler_1, 0, 1)

        g_settlers.addWidget(QLabel("Kathedrale Stufe 2:"), 0, 2)
        self.spin_settler_2 = self._create_spin(50, 3000, 300, 25)
        g_settlers.addWidget(self.spin_settler_2, 0, 3)

        g_settlers.addWidget(QLabel("Kathedrale Stufe 3:"), 1, 0)
        self.spin_settler_3 = self._create_spin(50, 4000, 500, 50)
        g_settlers.addWidget(self.spin_settler_3, 1, 1)

        g_settlers.addWidget(QLabel("Kathedrale Stufe 4 (Max):"), 1, 2)
        self.spin_settler_4 = self._create_spin(50, 5000, 800, 100)
        g_settlers.addWidget(self.spin_settler_4, 1, 3)

        lbl_settler_info = QLabel("Hinweis: In Vanilla beträgt das absolute Limit bei Stufe 4 genau 200 Siedler.")
        lbl_settler_info.setObjectName("DimLabel")
        g_settlers.addWidget(lbl_settler_info, 2, 0, 1, 4)

        layout.addWidget(box_settlers)

        # B. Lagerhaus
        box_store = QGroupBox("Lagerhaus (Kapazitäten & Ausbau)")
        g_store = QGridLayout(box_store)

        g_store.addWidget(QLabel("Lager Stufe 1:"), 0, 0)
        self.spin_store_1 = self._create_spin(10, 5000, 54, 10)
        g_store.addWidget(self.spin_store_1, 0, 1)

        g_store.addWidget(QLabel("Lager Stufe 2:"), 0, 2)
        self.spin_store_2 = self._create_spin(10, 5000, 250, 50)
        g_store.addWidget(self.spin_store_2, 0, 3)

        g_store.addWidget(QLabel("Lager Stufe 3:"), 1, 0)
        self.spin_store_3 = self._create_spin(10, 5000, 500, 50)
        g_store.addWidget(self.spin_store_3, 1, 1)

        g_store.addWidget(QLabel("Lager Stufe 4:"), 1, 2)
        self.spin_store_4 = self._create_spin(10, 5000, 1000, 100)
        g_store.addWidget(self.spin_store_4, 1, 3)

        g_store.addWidget(QLabel("Warenstapel-Limit (MaxAmount):"), 2, 0)
        self.spin_store_max = self._create_spin(10, 500, 60, 5)
        g_store.addWidget(self.spin_store_max, 2, 1)

        g_store.addWidget(QLabel("Goldkosten Stufe 2/3/4:"), 2, 2)
        self.spin_store_gold = self._create_spin(0, 5000, 250, 50)
        g_store.addWidget(self.spin_store_gold, 2, 3)

        layout.addWidget(box_store)

        # C. Burg / Schloss
        box_castle = QGroupBox("Burg & Schloss (Soldaten, Schatzkammer & Trefferpunkte)")
        g_castle = QGridLayout(box_castle)

        g_castle.addWidget(QLabel("Soldaten Stufe 1:"), 0, 0)
        self.spin_castle_soldier_1 = self._create_spin(5, 500, 30, 5)
        g_castle.addWidget(self.spin_castle_soldier_1, 0, 1)

        g_castle.addWidget(QLabel("Soldaten Stufe 2:"), 0, 2)
        self.spin_castle_soldier_2 = self._create_spin(5, 500, 55, 5)
        g_castle.addWidget(self.spin_castle_soldier_2, 0, 3)

        g_castle.addWidget(QLabel("Soldaten Stufe 3:"), 1, 0)
        self.spin_castle_soldier_3 = self._create_spin(5, 500, 85, 5)
        g_castle.addWidget(self.spin_castle_soldier_3, 1, 1)

        g_castle.addWidget(QLabel("Soldaten Stufe 4:"), 1, 2)
        self.spin_castle_soldier_4 = self._create_spin(5, 500, 130, 10)
        g_castle.addWidget(self.spin_castle_soldier_4, 1, 3)

        g_castle.addWidget(QLabel("Schatzkammer Gold (Stufe 4):"), 2, 0)
        self.spin_castle_treasury = self._create_spin(5000, 99000, 99000, 5000)
        g_castle.addWidget(self.spin_castle_treasury, 2, 1)

        g_castle.addWidget(QLabel("Burg HP Stufe 4:"), 2, 2)
        self.spin_castle_hp = self._create_spin(500, 20000, 5000, 500)
        g_castle.addWidget(self.spin_castle_hp, 2, 3)

        layout.addWidget(box_castle)

        # D. Kathedrale
        box_cath = QGroupBox("Kathedrale (Predigt-Besucher & Prestige)")
        g_cath = QGridLayout(box_cath)

        g_cath.addWidget(QLabel("Predigt-Besucher Stufe 4:"), 0, 0)
        self.spin_cath_sermon = self._create_spin(10, 500, 120, 10)
        g_cath.addWidget(self.spin_cath_sermon, 0, 1)

        g_cath.addWidget(QLabel("Prestige-Punkte Stufe 4:"), 0, 2)
        self.spin_cath_prestige = self._create_spin(50, 2000, 500, 50)
        g_cath.addWidget(self.spin_cath_prestige, 0, 3)

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

        # A. Rohstoff-Minen
        box_mines = QGroupBox("Rohstoffvorkommen & Minen (Steinbruch & Eisenmine)")
        g_mines = QGridLayout(box_mines)

        g_mines.addWidget(QLabel("Steinbruch-Kapazität:"), 0, 0)
        self.spin_mine_stone = self._create_spin(250, 999999, 999999, 1000)
        g_mines.addWidget(self.spin_mine_stone, 0, 1)

        g_mines.addWidget(QLabel("Eisenmine-Kapazität:"), 0, 2)
        self.spin_mine_iron = self._create_spin(250, 999999, 999999, 1000)
        g_mines.addWidget(self.spin_mine_iron, 0, 3)

        btn_inf_mines = QPushButton("♾️ Minen auf Unendlich (999.999) setzen")
        btn_inf_mines.clicked.connect(lambda: (self.spin_mine_stone.setValue(999999), self.spin_mine_iron.setValue(999999)))
        g_mines.addWidget(btn_inf_mines, 1, 0, 1, 2)

        btn_van_mines = QPushButton("🔄 Minen auf Standard (250) setzen")
        btn_van_mines.clicked.connect(lambda: (self.spin_mine_stone.setValue(250), self.spin_mine_iron.setValue(250)))
        g_mines.addWidget(btn_van_mines, 1, 2, 1, 2)

        layout.addWidget(box_mines)

        # B. Brunnen & Brandschutz
        box_well = QGroupBox("Brunnen & Löschwasser")
        g_well = QGridLayout(box_well)

        g_well.addWidget(QLabel("Wassernachfüllung (Einheiten/Sek):"), 0, 0)
        self.spin_well_refill = QDoubleSpinBox()
        self.spin_well_refill.setRange(0.1, 10.0)
        self.spin_well_refill.setSingleStep(0.2)
        self.spin_well_refill.setValue(1.5)
        g_well.addWidget(self.spin_well_refill, 0, 1)

        g_well.addWidget(QLabel("Wasservorrat Stufe 4:"), 0, 2)
        self.spin_well_cap = self._create_spin(25, 1000, 200, 25)
        g_well.addWidget(self.spin_well_cap, 0, 3)

        layout.addWidget(box_well)

        # C. Straßen & Logistik
        box_logistics = QGroupBox("Straßen & Transportlogistik")
        g_log = QGridLayout(box_logistics)

        g_log.addWidget(QLabel("Straßen-Geschwindigkeitsbonus:"), 0, 0)
        self.spin_road_speed = QDoubleSpinBox()
        self.spin_road_speed.setRange(1.0, 3.0)
        self.spin_road_speed.setSingleStep(0.05)
        self.spin_road_speed.setValue(1.4)
        g_log.addWidget(self.spin_road_speed, 0, 1)

        g_log.addWidget(QLabel("Karren-Geschwindigkeit:"), 0, 2)
        self.spin_cart_speed = self._create_spin(200, 1000, 400, 20)
        g_log.addWidget(self.spin_cart_speed, 0, 3)

        g_log.addWidget(QLabel("Betriebs-Warenpuffer (Bäckerei/Metzgerei):"), 1, 0)
        self.spin_workshop_cap = self._create_spin(9, 100, 18, 3)
        g_log.addWidget(self.spin_workshop_cap, 1, 1)

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

        # A. Bataillonsgröße
        box_bat = QGroupBox("Bataillonsgröße (Kaserne & Bogner)")
        v_bat = QVBoxLayout(box_bat)

        lbl_bat_desc = QLabel("Wähle die Anzahl der Soldaten, die pro Bataillon rekrutiert werden:")
        lbl_bat_desc.setObjectName("DimLabel")
        v_bat.addWidget(lbl_bat_desc)

        h_bat = QHBoxLayout()
        self.btn_group_bat = QButtonGroup(self)

        self.radio_bat_6 = QRadioButton("6 Soldaten (Vanilla Standard)")
        self.radio_bat_9 = QRadioButton("9 Soldaten (Erweitert - Empfohlen)")
        self.radio_bat_12 = QRadioButton("12 Soldaten (Großschlacht-Modus)")

        self.btn_group_bat.addButton(self.radio_bat_6, 6)
        self.btn_group_bat.addButton(self.radio_bat_9, 9)
        self.btn_group_bat.addButton(self.radio_bat_12, 12)

        self.radio_bat_9.setChecked(True)

        h_bat.addWidget(self.radio_bat_6)
        h_bat.addWidget(self.radio_bat_9)
        h_bat.addWidget(self.radio_bat_12)
        h_bat.addStretch()

        v_bat.addLayout(h_bat)
        layout.addWidget(box_bat)

        # B. Mauern & Befestigung
        box_walls = QGroupBox("Stadtmauern, Stadttore & Wehrtürme")
        g_walls = QGridLayout(box_walls)

        g_walls.addWidget(QLabel("Stadttore Trefferpunkte:"), 0, 0)
        self.spin_wall_gate = self._create_spin(500, 20000, 3000, 250)
        g_walls.addWidget(self.spin_wall_gate, 0, 1)

        g_walls.addWidget(QLabel("Wehrtürme Trefferpunkte:"), 0, 2)
        self.spin_wall_turret = self._create_spin(500, 20000, 2500, 250)
        g_walls.addWidget(self.spin_wall_turret, 0, 3)

        g_walls.addWidget(QLabel("Mauersegmente Trefferpunkte:"), 1, 0)
        self.spin_wall_segment = self._create_spin(500, 20000, 2000, 200)
        g_walls.addWidget(self.spin_wall_segment, 1, 1)

        layout.addWidget(box_walls)

        # C. Soldaten
        box_units = QGroupBox("Soldaten-Attribute (Schwertkämpfer & Bogenschützen)")
        g_units = QGridLayout(box_units)

        g_units.addWidget(QLabel("Marschgeschwindigkeit:"), 0, 0)
        self.spin_soldier_speed = self._create_spin(300, 1000, 540, 20)
        g_units.addWidget(self.spin_soldier_speed, 0, 1)

        g_units.addWidget(QLabel("Lebenspunkte (HP):"), 0, 2)
        self.spin_soldier_hp = self._create_spin(50, 1000, 160, 10)
        g_units.addWidget(self.spin_soldier_hp, 0, 3)

        layout.addWidget(box_units)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    # -------------------------------------------------------------------------
    # Helper & Event Handlers
    # -------------------------------------------------------------------------

    def _create_spin(self, min_val: int, max_val: int, val: int, step: int = 1) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(val)
        spin.setSingleStep(step)
        return spin

    def _refresh_presets_combo(self):
        self.preset_combo.clear()
        presets = self.config_engine.list_presets()
        for p in presets:
            self.preset_combo.addItem(p["name"], p["filename"])

    def _load_initial_preset(self, filename: str):
        index = self.preset_combo.findData(filename)
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)

    def _on_preset_changed(self, index: int):
        filename = self.preset_combo.currentData()
        if not filename:
            return
        try:
            data = self.config_engine.load_preset(filename)
            self._apply_data_to_widgets(data)
            self.status_message.emit(f"Preset '{data.get('name', filename)}' geladen.", "info")
        except Exception as e:
            self.status_message.emit(f"Fehler beim Laden des Presets: {e}", "error")

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
            msg = f"Erfolg: {count} XML-Dateien wurden im ModLoader angewendet!"
            self.status_message.emit(msg, "success")
            QMessageBox.information(self, "Konfiguration angewendet", msg)
        except Exception as e:
            err = f"Fehler beim Anwenden der Konfiguration: {e}"
            self.status_message.emit(err, "error")
            QMessageBox.critical(self, "Fehler", err)

    def _on_restore_vanilla(self):
        reply = QMessageBox.question(
            self,
            "Vanilla wiederherstellen",
            "Möchtest du wirklich alle modifizierten Konfigurationen entfernen und die Original-Ubisoft-Werte wiederherstellen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                removed = self.config_engine.restore_vanilla_configs()
                self._load_initial_preset("Vanilla_Default.json")
                msg = f"{removed} modifizierte XML-Dateien wurden entfernt. Das Spiel lädt nun Original-Werte."
                self.status_message.emit(msg, "warning")
                QMessageBox.information(self, "Vanilla wiederhergestellt", msg)
            except Exception as e:
                err = f"Fehler beim Wiederherstellen: {e}"
                self.status_message.emit(err, "error")
                QMessageBox.critical(self, "Fehler", err)

    def _on_save_preset(self):
        name, ok = QInputDialog.getText(self, "Preset speichern", "Name des neuen Presets:")
        if ok and name.strip():
            filename = f"Custom_{name.strip().replace(' ', '_')}.json"
            data = self._collect_data_from_widgets()
            data["name"] = name.strip()
            data["description"] = f"Benutzerdefiniertes Profil: {name.strip()}"
            self.config_engine.save_custom_preset(filename, data)
            self._refresh_presets_combo()
            self._load_initial_preset(filename)
            self.status_message.emit(f"Preset '{filename}' erfolgreich gespeichert.", "success")

"""
Siedler 6 Mod Manager - Config Engine
Verarbeitet XML-Konfigurationen, Spiel-Limits, Stufenwerte und Presets.
"""

import os
import json
import shutil
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from ModManager.engines.system_engine import SystemEngine


class ConfigEngine:
    """Erstellt, modifiziert und wendet XML-Konfigurationen für Siedler 6 an."""

    def __init__(self, system_engine: Optional[SystemEngine] = None):
        self.system = system_engine or SystemEngine()
        self.vanilla_dir = os.path.join(self.system.presets_path, "Vanilla")
        self.presets_dir = self.system.presets_path

    def load_preset(self, preset_name: str) -> Dict[str, Any]:
        """Lädt ein Preset anhand des Dateinamens."""
        if not preset_name.endswith(".json"):
            preset_name += ".json"
        
        preset_file = os.path.join(self.presets_dir, preset_name)
        if not os.path.exists(preset_file):
            raise FileNotFoundError(f"Preset nicht gefunden: {preset_file}")

        with open(preset_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_custom_preset(self, preset_name: str, data: Dict[str, Any]) -> str:
        """Speichert eine benutzerdefinierte Konfiguration als Preset-JSON."""
        if not preset_name.endswith(".json"):
            preset_name += ".json"

        preset_file = os.path.join(self.presets_dir, preset_name)
        with open(preset_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return preset_file

    def list_presets(self) -> List[Dict[str, str]]:
        """Listet alle verfügbaren Presets auf."""
        presets = []
        if not os.path.exists(self.presets_dir):
            return presets

        for f in os.listdir(self.presets_dir):
            if f.endswith(".json"):
                p = os.path.join(self.presets_dir, f)
                try:
                    with open(p, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                        presets.append({
                            "filename": f,
                            "name": data.get("name", f),
                            "description": data.get("description", "")
                        })
                except Exception:
                    pass
        return presets

    def _read_xml_from_modloader(self, rel_path: str) -> Optional[ET.Element]:
        """Liest eine XML-Datei aus dem aktiven ModLoader-Ordner, falls vorhanden."""
        full_path = os.path.join(self.system.modloader_path, rel_path)
        if os.path.exists(full_path):
            try:
                tree = ET.parse(full_path)
                return tree.getroot()
            except Exception:
                return None
        return None

    def _read_xml_text(self, root: ET.Element, xpath: str, default, cast=int):
        """Liest einen einzelnen Textwert aus einem XML-Knoten."""
        elem = root.find(xpath)
        if elem is not None and elem.text:
            try:
                return cast(elem.text)
            except (ValueError, TypeError):
                return default
        return default

    def _read_xml_list(self, root: ET.Element, xpath: str, default_list: List, cast=int) -> List:
        """Liest eine Liste von Werten aus wiederholten XML-Knoten."""
        elems = root.findall(xpath)
        if elems:
            result = []
            for e in elems:
                if e.text:
                    try:
                        result.append(cast(e.text))
                    except (ValueError, TypeError):
                        pass
            return result if result else default_list
        return default_list

    def read_active_config_from_modloader(self) -> Dict[str, Any]:
        """
        Liest die tatsächlichen Werte direkt aus den XML-Dateien im aktiven
        ModLoader-Ordner. Dies ist die Single Source of Truth.
        Wenn eine Datei nicht existiert, werden die Vanilla-Defaults verwendet.
        """
        config: Dict[str, Any] = {}

        # 1. logic.xml -> settler_limits, road_speed_modifier
        logic = self._read_xml_from_modloader(os.path.normpath("config/logic.xml"))
        if logic is not None:
            config["settler_limits"] = self._read_xml_list(
                logic, ".//SettlerLimit", [50, 50, 100, 150, 200, 200]
            )
            config["road_speed_modifier"] = self._read_xml_text(
                logic, ".//SpeedFactorRoad", 1.25, float
            )
        else:
            config["settler_limits"] = [50, 50, 100, 150, 200, 200]
            config["road_speed_modifier"] = 1.25

        # 2. b_storehouse.xml
        store = self._read_xml_from_modloader(os.path.normpath("config/entities/b_storehouse.xml"))
        if store is not None:
            config["storehouse_capacities"] = self._read_xml_list(
                store, ".//OutStockCapacity", [54, 108, 162, 216]
            )
            config["storehouse_max_amount_on_stock"] = self._read_xml_text(
                store, ".//MaxAmountOnStock", 18
            )
            # Upgrade Gold: Letzen Wert extrahieren
            gold_amounts = []
            for uc in store.findall(".//UpgradeCost"):
                for ga in uc.findall("GoodAmount"):
                    gt = ga.find("GoodType")
                    amt = ga.find("Amount")
                    if gt is not None and gt.text == "G_Gold" and amt is not None:
                        try:
                            gold_amounts.append(int(amt.text))
                        except (ValueError, TypeError):
                            pass
            config["storehouse_upgrade_gold"] = gold_amounts if gold_amounts else [150, 250, 500]
        else:
            config["storehouse_capacities"] = [54, 108, 162, 216]
            config["storehouse_max_amount_on_stock"] = 18
            config["storehouse_upgrade_gold"] = [150, 250, 500]

        # 3. Castle (verwende b_castle_me.xml als Referenz)
        castle = self._read_xml_from_modloader(os.path.normpath("config/entities/b_castle_me.xml"))
        if castle is not None:
            config["castle_soldier_limits"] = self._read_xml_list(
                castle, ".//Limit", [25, 43, 61, 91]
            )
            config["castle_treasury_capacities"] = self._read_xml_list(
                castle, ".//TreasuryStorageCapacity", [20000, 20000, 20000, 20000]
            )
            config["castle_hitpoints"] = self._read_xml_list(
                castle, ".//MaxHitpoint", [750, 1500, 2250, 3000]
            )
        else:
            config["castle_soldier_limits"] = [25, 43, 61, 91]
            config["castle_treasury_capacities"] = [20000, 20000, 20000, 20000]
            config["castle_hitpoints"] = [750, 1500, 2250, 3000]

        # 4. Cathedral (b_cathedral.xml als Referenz)
        cath = self._read_xml_from_modloader(os.path.normpath("config/entities/b_cathedral.xml"))
        if cath is not None:
            config["cathedral_sermon_limits"] = self._read_xml_list(
                cath, ".//SermonSettlerLimit", [10, 15, 30, 60]
            )
            config["cathedral_prestige_points"] = self._read_xml_list(
                cath, ".//PrestigePoints", [100, 200, 400]
            )
        else:
            config["cathedral_sermon_limits"] = [10, 15, 30, 60]
            config["cathedral_prestige_points"] = [100, 200, 400]

        # 5. Minen
        stone = self._read_xml_from_modloader(os.path.normpath("config/entities/r_stonemine.xml"))
        config["mine_stone_capacity"] = self._read_xml_text(stone, ".//Capacity", 250) if stone is not None else 250

        iron = self._read_xml_from_modloader(os.path.normpath("config/entities/r_ironmine.xml"))
        config["mine_iron_capacity"] = self._read_xml_text(iron, ".//Capacity", 250) if iron is not None else 250

        # 6. Brunnen
        well = self._read_xml_from_modloader(os.path.normpath("config/entities/b_well.xml"))
        if well is not None:
            config["well_water_refill_rate"] = self._read_xml_text(
                well, ".//WaterRefillRatePerSecond", 0.5, float
            )
            config["well_water_capacity"] = self._read_xml_list(
                well, ".//OutStockCapacity", [25, 50, 75, 100]
            )
        else:
            config["well_water_refill_rate"] = 0.5
            config["well_water_capacity"] = [25, 50, 75, 100]

        # 7. Mauern / Tore / Türme (jeweils _me als Referenz)
        gate = self._read_xml_from_modloader(os.path.normpath("config/entities/b_wallgate_me.xml"))
        config["wall_gate_health"] = self._read_xml_text(gate, ".//MaxHealth", 1200) if gate is not None else 1200

        turret = self._read_xml_from_modloader(os.path.normpath("config/entities/b_wallturret_me.xml"))
        config["wall_turret_health"] = self._read_xml_text(turret, ".//MaxHealth", 1000) if turret is not None else 1000

        segment = self._read_xml_from_modloader(os.path.normpath("config/entities/b_wallsegment_me.xml"))
        config["wall_segment_health"] = self._read_xml_text(segment, ".//MaxHealth", 800) if segment is not None else 800

        # 8. Kasernen (Bataillonsgröße)
        barracks = self._read_xml_from_modloader(os.path.normpath("config/entities/b_barracks.xml"))
        config["battalion_size"] = self._read_xml_text(barracks, ".//BattalionSize", 6) if barracks is not None else 6

        # 9. Soldaten
        sword = self._read_xml_from_modloader(os.path.normpath("config/entities/u_militarysword.xml"))
        if sword is not None:
            config["soldier_speed"] = self._read_xml_text(sword, ".//Speed", 480)
            config["soldier_health"] = self._read_xml_text(sword, ".//MaxHealth", 120)
        else:
            config["soldier_speed"] = 480
            config["soldier_health"] = 120

        # 10. Karren
        cart = self._read_xml_from_modloader(os.path.normpath("config/entities/m_hunterpushcart.xml"))
        config["cart_speed"] = self._read_xml_text(cart, ".//Speed", 320) if cart is not None else 320

        # 11. Betriebe
        bakery = self._read_xml_from_modloader(os.path.normpath("config/entities/b_bakery.xml"))
        if bakery is not None:
            caps = self._read_xml_list(bakery, ".//OutStockCapacity", [9])
            config["workshop_output_capacity"] = caps[0] if caps else 9
        else:
            config["workshop_output_capacity"] = 9

        return config

    # -------------------------------------------------------------------------
    # XML Modification Helper Functions
    # -------------------------------------------------------------------------

    def _get_base_xml_path(self, rel_path: str) -> str:
        """
        Ermittelt den Pfad zur Basis-XML. 
        Bevorzugt Preloaded-Mods aus Original/mod (S6Patcher Fixes), fällt auf Vanilla zurück.
        """
        preloaded_path = os.path.join(self.system.original_mods_path, rel_path)
        if os.path.exists(preloaded_path):
            return preloaded_path
        return os.path.join(self.vanilla_dir, rel_path)

    def _modify_logic_xml(self, config: Dict[str, Any]) -> str:
        """Erstellt den modifizierten XML-Inhalt für logic.xml."""
        base_path = self._get_base_xml_path(os.path.normpath("config/logic.xml"))
        tree = ET.parse(base_path)
        root = tree.getroot()

        # Settler Limits
        settler_limits = config.get("settler_limits")
        if settler_limits:
            limits_elem = root.find("SettlerLimits")
            if limits_elem is not None:
                # Vorhandene Kinder entfernen
                limits_elem.clear()
                for val in settler_limits:
                    child = ET.SubElement(limits_elem, "SettlerLimit")
                    child.text = str(val)

        # Road Speed
        road_speed = config.get("road_speed_modifier")
        if road_speed is not None:
            elem = root.find("SpeedFactorRoad")
            if elem is not None:
                elem.text = str(road_speed)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _modify_storehouse_xml(self, config: Dict[str, Any]) -> str:
        """Modifiziert b_storehouse.xml."""
        base_path = self._get_base_xml_path(os.path.normpath("config/entities/b_storehouse.xml"))
        tree = ET.parse(base_path)
        root = tree.getroot()

        # OutStockCapacities
        capacities = config.get("storehouse_capacities")
        if capacities:
            elem = root.find(".//OutStockCapacities")
            if elem is not None:
                elem.clear()
                for val in capacities:
                    c = ET.SubElement(elem, "OutStockCapacity")
                    c.text = str(val)

        # MaxAmountOnStock
        max_amount = config.get("storehouse_max_amount_on_stock")
        if max_amount is not None:
            elem = root.find(".//MaxAmountOnStock")
            if elem is not None:
                elem.text = str(max_amount)

        # Upgrade Costs
        gold_costs = config.get("storehouse_upgrade_gold")
        stone_costs = config.get("storehouse_upgrade_stone")
        if gold_costs and stone_costs:
            upgrade_costs_elem = root.find(".//UpgradeCosts")
            if upgrade_costs_elem is not None:
                upgrade_costs_elem.clear()
                for g, s in zip(gold_costs, stone_costs):
                    uc = ET.SubElement(upgrade_costs_elem, "UpgradeCost")
                    
                    ga_stone = ET.SubElement(uc, "GoodAmount")
                    gt_s = ET.SubElement(ga_stone, "GoodType")
                    gt_s.text = "G_Stone"
                    amt_s = ET.SubElement(ga_stone, "Amount")
                    amt_s.text = str(s)

                    ga_gold = ET.SubElement(uc, "GoodAmount")
                    gt_g = ET.SubElement(ga_gold, "GoodType")
                    gt_g.text = "G_Gold"
                    amt_g = ET.SubElement(ga_gold, "Amount")
                    amt_g.text = str(g)

        # Seconds to upgrade
        seconds = config.get("storehouse_upgrade_seconds")
        if seconds:
            elem = root.find(".//SecondsToUpgradeByLevel")
            if elem is not None:
                elem.clear()
                for s in seconds:
                    c = ET.SubElement(elem, "Seconds")
                    c.text = str(s)

        # Max settlers for upgrade
        settlers = config.get("storehouse_upgrade_settlers")
        if settlers:
            elem = root.find(".//MaxSettlersForUpgradeByLevel")
            if elem is not None:
                elem.clear()
                for s in settlers:
                    c = ET.SubElement(elem, "MaxSettlers")
                    c.text = str(s)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _modify_castle_xml(self, xml_filename: str, config: Dict[str, Any]) -> str:
        """Modifiziert b_castle_*.xml."""
        base_path = self._get_base_xml_path(os.path.normpath(f"config/entities/{xml_filename}"))
        tree = ET.parse(base_path)
        root = tree.getroot()

        # SoldierLimits
        limits = config.get("castle_soldier_limits")
        if limits:
            elem = root.find(".//SoldierLimits")
            if elem is not None:
                elem.clear()
                for val in limits:
                    c = ET.SubElement(elem, "Limit")
                    c.text = str(val)

        # TreasuryStorageCapacity
        treasuries = config.get("castle_treasury_capacities")
        if treasuries:
            # Im Vanilla-XML gibt es mehrere TreasuryStorageCapacity Tags hintereinander
            elems = root.findall(".//TreasuryStorageCapacity")
            for i, elem in enumerate(elems):
                if i < len(treasuries):
                    elem.text = str(treasuries[i])

        # Hitpoints
        hitpoints = config.get("castle_hitpoints")
        if hitpoints:
            elems = root.findall(".//MaxHitpoint")
            for i, elem in enumerate(elems):
                if i < len(hitpoints):
                    elem.text = str(hitpoints[i])

        # Upgrade Costs (TODO: Aktuell nicht über die GUI exponiert – Schlüssel
        # castle_upgrade_gold / castle_upgrade_stone werden von _collect_data_from_widgets nicht erzeugt)
        gold_costs = config.get("castle_upgrade_gold")
        stone_costs = config.get("castle_upgrade_stone")
        if gold_costs and stone_costs:
            upgrade_costs_elem = root.find(".//UpgradeCosts")
            if upgrade_costs_elem is not None:
                upgrade_costs_elem.clear()
                for g, s in zip(gold_costs, stone_costs):
                    uc = ET.SubElement(upgrade_costs_elem, "UpgradeCost")
                    
                    ga_stone = ET.SubElement(uc, "GoodAmount")
                    gt_s = ET.SubElement(ga_stone, "GoodType")
                    gt_s.text = "G_Stone"
                    amt_s = ET.SubElement(ga_stone, "Amount")
                    amt_s.text = str(s)

                    ga_gold = ET.SubElement(uc, "GoodAmount")
                    gt_g = ET.SubElement(ga_gold, "GoodType")
                    gt_g.text = "G_Gold"
                    amt_g = ET.SubElement(ga_gold, "Amount")
                    amt_g.text = str(g)

        # Seconds
        seconds = config.get("castle_upgrade_seconds")
        if seconds:
            elem = root.find(".//SecondsToUpgradeByLevel")
            if elem is not None:
                elem.clear()
                for s in seconds:
                    c = ET.SubElement(elem, "Seconds")
                    c.text = str(s)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _modify_cathedral_xml(self, xml_filename: str, config: Dict[str, Any]) -> str:
        """Modifiziert b_cathedral*.xml."""
        base_path = self._get_base_xml_path(os.path.normpath(f"config/entities/{xml_filename}"))
        tree = ET.parse(base_path)
        root = tree.getroot()

        # SermonSettlerLimits
        sermons = config.get("cathedral_sermon_limits")
        if sermons:
            elem = root.find(".//SermonSettlerLimits")
            if elem is not None:
                elem.clear()
                for val in sermons:
                    c = ET.SubElement(elem, "SermonSettlerLimit")
                    c.text = str(val)

        # PrestigePoints
        prestige = config.get("cathedral_prestige_points")
        if prestige:
            elem = root.find(".//PrestigePointsForUpgrade")
            if elem is not None:
                elem.clear()
                for val in prestige:
                    c = ET.SubElement(elem, "PrestigePoints")
                    c.text = str(val)

        # Upgrade Costs (TODO: Aktuell nicht über die GUI exponiert – Schlüssel
        # cathedral_upgrade_gold / cathedral_upgrade_stone werden von _collect_data_from_widgets nicht erzeugt)
        gold_costs = config.get("cathedral_upgrade_gold")
        stone_costs = config.get("cathedral_upgrade_stone")
        if gold_costs and stone_costs:
            upgrade_costs_elem = root.find(".//UpgradeCosts")
            if upgrade_costs_elem is not None:
                upgrade_costs_elem.clear()
                for g, s in zip(gold_costs, stone_costs):
                    uc = ET.SubElement(upgrade_costs_elem, "UpgradeCost")
                    
                    ga_stone = ET.SubElement(uc, "GoodAmount")
                    gt_s = ET.SubElement(ga_stone, "GoodType")
                    gt_s.text = "G_Stone"
                    amt_s = ET.SubElement(ga_stone, "Amount")
                    amt_s.text = str(s)

                    ga_gold = ET.SubElement(uc, "GoodAmount")
                    gt_g = ET.SubElement(ga_gold, "GoodType")
                    gt_g.text = "G_Gold"
                    amt_g = ET.SubElement(ga_gold, "Amount")
                    amt_g.text = str(g)

        # Seconds
        seconds = config.get("cathedral_upgrade_seconds")
        if seconds:
            elem = root.find(".//SecondsToUpgradeByLevel")
            if elem is not None:
                elem.clear()
                for s in seconds:
                    c = ET.SubElement(elem, "Seconds")
                    c.text = str(s)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _modify_resource_mine_xml(self, xml_filename: str, capacity: int) -> str:
        """Modifiziert r_stonemine.xml und r_ironmine.xml."""
        base_path = self._get_base_xml_path(os.path.normpath(f"config/entities/{xml_filename}"))
        tree = ET.parse(base_path)
        root = tree.getroot()

        elem = root.find(".//Capacity")
        if elem is not None:
            elem.text = str(capacity)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _modify_well_xml(self, config: Dict[str, Any]) -> str:
        """Modifiziert b_well.xml."""
        base_path = self._get_base_xml_path(os.path.normpath("config/entities/b_well.xml"))
        tree = ET.parse(base_path)
        root = tree.getroot()

        refill = config.get("well_water_refill_rate")
        if refill is not None:
            elem = root.find(".//WaterRefillRatePerSecond")
            if elem is not None:
                elem.text = str(refill)

        capacities = config.get("well_water_capacity")
        if capacities:
            elems = root.findall(".//OutStockCapacity")
            for i, elem in enumerate(elems):
                if i < len(capacities):
                    elem.text = str(capacities[i])

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _modify_wall_health_xml(self, xml_filename: str, health: int) -> str:
        """Modifiziert MaxHealth von Mauern, Toren und Türmen."""
        base_path = self._get_base_xml_path(os.path.normpath(f"config/entities/{xml_filename}"))
        tree = ET.parse(base_path)
        root = tree.getroot()

        elem = root.find(".//MaxHealth")
        if elem is not None:
            elem.text = str(health)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _modify_barracks_xml(self, xml_filename: str, battalion_size: int) -> str:
        """Modifiziert BattalionSize in b_barracks*.xml."""
        base_path = self._get_base_xml_path(os.path.normpath(f"config/entities/{xml_filename}"))
        tree = ET.parse(base_path)
        root = tree.getroot()

        elem = root.find(".//BattalionSize")
        if elem is not None:
            elem.text = str(battalion_size)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _modify_soldier_xml(self, xml_filename: str, speed: Optional[int], health: Optional[int]) -> str:
        """Modifiziert Geschwindigkeit und Lebenspunkte von Soldaten."""
        base_path = self._get_base_xml_path(os.path.normpath(f"config/entities/{xml_filename}"))
        tree = ET.parse(base_path)
        root = tree.getroot()

        if speed is not None:
            elem = root.find(".//Speed")
            if elem is not None:
                elem.text = str(speed)

        if health is not None:
            elem = root.find(".//MaxHealth")
            if elem is not None:
                elem.text = str(health)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _modify_cart_xml(self, speed: int) -> str:
        """Modifiziert Geschwindigkeit von Karren."""
        base_path = self._get_base_xml_path(os.path.normpath("config/entities/m_hunterpushcart.xml"))
        tree = ET.parse(base_path)
        root = tree.getroot()

        elem = root.find(".//Speed")
        if elem is not None:
            elem.text = str(speed)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def _modify_workshop_xml(self, xml_filename: str, out_stock: int) -> str:
        """Modifiziert Puffer-Kapazität von Betrieben."""
        base_path = self._get_base_xml_path(os.path.normpath(f"config/entities/{xml_filename}"))
        tree = ET.parse(base_path)
        root = tree.getroot()

        elems = root.findall(".//OutStockCapacity")
        for elem in elems:
            elem.text = str(out_stock)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    # -------------------------------------------------------------------------
    # Application to ModLoader
    # -------------------------------------------------------------------------

    def generate_all_xmls(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Generiert alle geänderten XML-Dateien als Dict {rel_path: xml_content}."""
        generated = {}

        # 1. logic.xml
        generated[os.path.normpath("config/logic.xml")] = self._modify_logic_xml(config)

        # 2. Storehouse
        generated[os.path.normpath("config/entities/b_storehouse.xml")] = self._modify_storehouse_xml(config)

        # 3. Castles (ME, NA, NE, SE)
        for c_file in ["b_castle_me.xml", "b_castle_na.xml", "b_castle_ne.xml", "b_castle_se.xml"]:
            generated[os.path.normpath(f"config/entities/{c_file}")] = self._modify_castle_xml(c_file, config)

        # 4. Cathedrals
        for cath_file in ["b_cathedral.xml", "b_cathedral_big.xml"]:
            generated[os.path.normpath(f"config/entities/{cath_file}")] = self._modify_cathedral_xml(cath_file, config)

        # 5. Resource Mines
        stone_cap = config.get("mine_stone_capacity", 250)
        iron_cap = config.get("mine_iron_capacity", 250)
        generated[os.path.normpath("config/entities/r_stonemine.xml")] = self._modify_resource_mine_xml("r_stonemine.xml", stone_cap)
        generated[os.path.normpath("config/entities/r_ironmine.xml")] = self._modify_resource_mine_xml("r_ironmine.xml", iron_cap)

        # 6. Well
        generated[os.path.normpath("config/entities/b_well.xml")] = self._modify_well_xml(config)

        # 7. Walls, Gates, Turrets
        gate_hp = config.get("wall_gate_health")
        if gate_hp is not None:
            for gf in ["b_wallgate_me.xml", "b_wallgate_na.xml", "b_wallgate_ne.xml", "b_wallgate_se.xml"]:
                generated[os.path.normpath(f"config/entities/{gf}")] = self._modify_wall_health_xml(gf, gate_hp)

        turret_hp = config.get("wall_turret_health")
        if turret_hp is not None:
            for tf in ["b_wallturret_me.xml", "b_wallturret_na.xml", "b_wallturret_ne.xml", "b_wallturret_se.xml"]:
                generated[os.path.normpath(f"config/entities/{tf}")] = self._modify_wall_health_xml(tf, turret_hp)

        segment_hp = config.get("wall_segment_health")
        if segment_hp is not None:
            for sf in ["b_wallsegment_me.xml", "b_wallsegment_na.xml", "b_wallsegment_ne.xml", "b_wallsegment_se.xml"]:
                generated[os.path.normpath(f"config/entities/{sf}")] = self._modify_wall_health_xml(sf, segment_hp)

        # 8. Barracks
        b_size = config.get("battalion_size")
        if b_size is not None:
            for bf in ["b_barracks.xml", "b_barracksarchers.xml"]:
                generated[os.path.normpath(f"config/entities/{bf}")] = self._modify_barracks_xml(bf, b_size)

        # 9. Military units
        s_speed = config.get("soldier_speed")
        s_health = config.get("soldier_health")
        if s_speed or s_health:
            for uf in ["u_militarysword.xml", "u_militarybow.xml"]:
                generated[os.path.normpath(f"config/entities/{uf}")] = self._modify_soldier_xml(uf, s_speed, s_health)

        # 10. Cart Speed
        c_speed = config.get("cart_speed")
        if c_speed is not None:
            generated[os.path.normpath("config/entities/m_hunterpushcart.xml")] = self._modify_cart_xml(c_speed)

        # 11. Workshop Buffer
        ws_cap = config.get("workshop_output_capacity")
        if ws_cap is not None:
            for wsf in ["b_bakery.xml", "b_butcher.xml", "b_dairy.xml"]:
                generated[os.path.normpath(f"config/entities/{wsf}")] = self._modify_workshop_xml(wsf, ws_cap)

        return generated

    def apply_config_to_modloader(self, config: Dict[str, Any]) -> int:
        """Schreibt alle modifizierten XML-Dateien direkt in den ModLoader."""
        xml_files = self.generate_all_xmls(config)
        written_count = 0

        for rel_path, xml_content in xml_files.items():
            # Niemals geschützte S6Patcher-Dateien überschreiben
            if self.system.is_protected_file(rel_path):
                continue

            target_file = os.path.join(self.system.modloader_path, rel_path)
            os.makedirs(os.path.dirname(target_file), exist_ok=True)

            with open(target_file, "w", encoding="utf-8") as f:
                f.write(xml_content)
            written_count += 1

        return written_count

    def restore_vanilla_configs(self) -> int:
        """
        Entfernt alle ModManager-Änderungen aus dem ModLoader.
        Wenn eine Datei im S6Patcher-Preloaded-Ordner (Original/mod) existiert,
        wird sie daraus wiederhergestellt. Andernfalls wird sie gelöscht (echtes Vanilla).
        Geschützte S6Patcher-Dateien bleiben unangetastet!
        """
        restored_count = 0
        if not os.path.exists(self.system.modloader_path):
            return 0

        # Zu überprüfende Config-Pfade (wir iterieren durch die generierten Pfade)
        # Besser: Wir iterieren durch alle Dateien im config-Ordner des aktiven ModLoaders
        config_dir = os.path.join(self.system.modloader_path, "config")
        if os.path.exists(config_dir):
            for root, _, files in os.walk(config_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.system.modloader_path)
                    
                    if not self.system.is_protected_file(rel_path):
                        # Prüfen ob im Original-Ordner vorhanden
                        original_file_path = os.path.join(self.system.original_mods_path, rel_path)
                        if os.path.exists(original_file_path):
                            # Wiederherstellen aus Preloaded Mod
                            shutil.copy2(original_file_path, full_path)
                        else:
                            # Löschen (Vanilla Fallback auf .bba)
                            os.remove(full_path)
                        restored_count += 1

        return restored_count

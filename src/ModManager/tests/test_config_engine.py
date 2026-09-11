"""
Unit Tests für ConfigEngine
"""

import os
import unittest
import xml.etree.ElementTree as ET
from ModManager.engines.system_engine import SystemEngine
from ModManager.engines.config_engine import ConfigEngine


class TestConfigEngine(unittest.TestCase):

    def setUp(self):
        self.system = SystemEngine()
        self.config_engine = ConfigEngine(self.system)

    def test_load_presets(self):
        presets = self.config_engine.list_presets()
        self.assertGreaterEqual(len(presets), 3)

        vanilla = self.config_engine.load_preset("Vanilla_Default.json")
        self.assertEqual(vanilla["settler_limits"], [50, 50, 100, 150, 200, 200])

        extended = self.config_engine.load_preset("Extended_Balanced.json")
        self.assertEqual(extended["settler_limits"], [100, 150, 300, 500, 800, 800])
        self.assertEqual(extended["battalion_size"], 9)
        self.assertEqual(extended["mine_stone_capacity"], 999999)

    def test_modify_logic_xml(self):
        config = {
            "settler_limits": [100, 200, 400, 600, 1000, 1000],
            "road_speed_modifier": 1.5
        }
        xml_str = self.config_engine._modify_logic_xml(config)
        root = ET.fromstring(xml_str)
        
        limits = [int(x.text) for x in root.findall(".//SettlerLimit")]
        self.assertEqual(limits, [100, 200, 400, 600, 1000, 1000])

        speed = float(root.find(".//SpeedFactorRoad").text)
        self.assertEqual(speed, 1.5)

    def test_modify_storehouse_xml(self):
        config = {
            "storehouse_capacities": [54, 250, 500, 1000],
            "storehouse_max_amount_on_stock": 80,
            "storehouse_upgrade_gold": [100, 200, 300],
            "storehouse_upgrade_stone": [10, 20, 30],
            "storehouse_upgrade_seconds": [15, 30, 45],
            "storehouse_upgrade_settlers": [5, 10, 20]
        }
        xml_str = self.config_engine._modify_storehouse_xml(config)
        root = ET.fromstring(xml_str)

        caps = [int(x.text) for x in root.findall(".//OutStockCapacity")]
        self.assertEqual(caps, [54, 250, 500, 1000])

        max_amt = int(root.find(".//MaxAmountOnStock").text)
        self.assertEqual(max_amt, 80)

    def test_modify_castle_xml(self):
        config = {
            "castle_soldier_limits": [30, 60, 90, 150],
            "castle_treasury_capacities": [50000, 50000, 50000, 50000],
            "castle_hitpoints": [1000, 2000, 3000, 4000]
        }
        xml_str = self.config_engine._modify_castle_xml("b_castle_me.xml", config)
        root = ET.fromstring(xml_str)

        limits = [int(x.text) for x in root.findall(".//SoldierLimits/Limit")]
        self.assertEqual(limits, [30, 60, 90, 150])

    def test_modify_resource_mine_xml(self):
        xml_str = self.config_engine._modify_resource_mine_xml("r_stonemine.xml", 999999)
        root = ET.fromstring(xml_str)
        cap = int(root.find(".//Capacity").text)
        self.assertEqual(cap, 999999)

    def test_modify_barracks_xml(self):
        xml_str = self.config_engine._modify_barracks_xml("b_barracks.xml", 12)
        root = ET.fromstring(xml_str)
        b_size = int(root.find(".//BattalionSize").text)
        self.assertEqual(b_size, 12)

    def test_generate_all_xmls(self):
        preset = self.config_engine.load_preset("Extended_Balanced.json")
        all_xmls = self.config_engine.generate_all_xmls(preset)
        self.assertIn(os.path.normpath("config/logic.xml"), all_xmls)
        self.assertIn(os.path.normpath("config/entities/b_storehouse.xml"), all_xmls)
        self.assertIn(os.path.normpath("config/entities/b_castle_me.xml"), all_xmls)
        self.assertIn(os.path.normpath("config/entities/r_stonemine.xml"), all_xmls)
        self.assertIn(os.path.normpath("config/entities/b_barracks.xml"), all_xmls)

        # Alle generierten XMLs parsen und auf Syntaxfehler prüfen
        for rel_path, content in all_xmls.items():
            try:
                ET.fromstring(content)
            except Exception as e:
                self.fail(f"Fehlerhaftes XML in {rel_path}: {e}")


if __name__ == "__main__":
    unittest.main()

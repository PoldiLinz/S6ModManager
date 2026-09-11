"""
Unit Tests für ScenarioEngine
"""

import os
import unittest
from ModManager.engines.system_engine import SystemEngine
from ModManager.engines.scenario_engine import ScenarioEngine


class TestScenarioEngine(unittest.TestCase):

    def setUp(self):
        self.system = SystemEngine()
        self.scenario_engine = ScenarioEngine(self.system)

    def test_list_supported_maps(self):
        maps = self.scenario_engine.list_supported_maps()
        self.assertGreaterEqual(len(maps), 1)
        map_ids = [m["map_id"] for m in maps]
        self.assertIn("me_fairtrade", map_ids)

    def test_list_variations_for_fairtrade(self):
        variations = self.scenario_engine.list_variations_for_map("me_fairtrade")
        self.assertGreaterEqual(len(variations), 2)
        var_ids = [v["id"] for v in variations]
        self.assertIn("vanilla", var_ids)
        self.assertIn("hostile_edition", var_ids)

        hostile = next(v for v in variations if v["id"] == "hostile_edition")
        self.assertEqual(hostile["title"], "Feindseliger Freihandel (Hostile Edition)")
        self.assertFalse(hostile["is_vanilla"])

    def test_list_usermaps(self):
        usermaps = self.scenario_engine.list_available_usermaps()
        self.assertIsInstance(usermaps, list)


if __name__ == "__main__":
    unittest.main()

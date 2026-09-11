"""
Unit Tests für ScenarioEngine
"""

import os
import shutil
import tempfile
import json
import unittest
from ModManager.engines.system_engine import SystemEngine
from ModManager.engines.scenario_engine import ScenarioEngine


class TestScenarioEngine(unittest.TestCase):

    def setUp(self):
        self.system = SystemEngine()
        self.test_dir = tempfile.mkdtemp(prefix="test_scenarios_")
        self.system.scenarios_path = self.test_dir

        # Erstelle ein Mock-Szenario für isolierte Tests
        sample_map = os.path.join(self.test_dir, "sample_map")
        os.makedirs(os.path.join(sample_map, "vanilla"), exist_ok=True)
        with open(os.path.join(sample_map, "vanilla", "scenario.json"), "w", encoding="utf-8") as f:
            json.dump({"id": "vanilla", "title": "Original: Sample Map (Vanilla)", "is_vanilla": True}, f)

        os.makedirs(os.path.join(sample_map, "custom_variant"), exist_ok=True)
        with open(os.path.join(sample_map, "custom_variant", "scenario.json"), "w", encoding="utf-8") as f:
            json.dump({"id": "custom_variant", "title": "Custom Variant Edition", "is_vanilla": False}, f)

        self.scenario_engine = ScenarioEngine(self.system)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_list_supported_maps(self):
        maps = self.scenario_engine.list_supported_maps()
        self.assertEqual(len(maps), 1)
        self.assertEqual(maps[0]["map_id"], "sample_map")

    def test_list_variations_for_map(self):
        variations = self.scenario_engine.list_variations_for_map("sample_map")
        self.assertEqual(len(variations), 2)
        var_ids = [v["id"] for v in variations]
        self.assertIn("vanilla", var_ids)
        self.assertIn("custom_variant", var_ids)

        custom = next(v for v in variations if v["id"] == "custom_variant")
        self.assertEqual(custom["title"], "Custom Variant Edition")
        self.assertFalse(custom["is_vanilla"])

    def test_list_usermaps(self):
        usermaps = self.scenario_engine.list_available_usermaps()
        self.assertIsInstance(usermaps, list)


if __name__ == "__main__":
    unittest.main()

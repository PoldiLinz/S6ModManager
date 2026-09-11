"""
Vollständiger End-to-End-Validierungstest für die Phasen 1 bis 3
"""

import os
import sys
import unittest
import xml.etree.ElementTree as ET

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from ModManager.app_window import MainWindow
from ModManager.engines.system_engine import SystemEngine
from ModManager.engines.config_engine import ConfigEngine
from ModManager.engines.scenario_engine import ScenarioEngine
from ModManager.engines.sandbox_engine import SandboxEngine


class TestEndToEndValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
        theme_path = os.path.join(
            os.path.dirname(__file__), "..", "styles", "theme.qss"
        )
        if os.path.exists(theme_path):
            with open(theme_path, "r", encoding="utf-8") as f:
                cls.app.setStyleSheet(f.read())

    def setUp(self):
        self.system = SystemEngine()
        self.config_engine = ConfigEngine(self.system)
        self.scenario_engine = ScenarioEngine(self.system)
        self.sandbox_engine = SandboxEngine(self.system)
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()

    def test_phase1_backend_integrity(self):
        """Validiert alle Backend-Engines aus Phase 1."""
        # 1. System-Engine
        self.assertTrue(os.path.exists(self.system.presets_path))
        self.assertTrue(os.path.exists(self.system.scenarios_path))
        status, patcher_files = self.system.check_s6patcher_integrity()
        self.assertIn(status, ["OK", "WARNING", "ERROR"])
        self.assertEqual(len(patcher_files), 8)

        # 2. Config-Engine & Presets
        presets = self.config_engine.list_presets()
        self.assertGreaterEqual(len(presets), 3)
        for p_info in presets:
            p_data = self.config_engine.load_preset(p_info["filename"])
            self.assertIn("settler_limits", p_data)
            self.assertIn("storehouse_capacities", p_data)
            self.assertIn("mine_stone_capacity", p_data)
            self.assertIn("battalion_size", p_data)

            # Generiere alle XMLs und prüfe Syntax
            all_xmls = self.config_engine.generate_all_xmls(p_data)
            self.assertGreaterEqual(len(all_xmls), 15)
            for rel_p, content in all_xmls.items():
                try:
                    ET.fromstring(content)
                except Exception as ex:
                    self.fail(
                        f"Syntaxfehler in Preset {p_info['filename']} bei Datei {rel_p}: {ex}"
                    )

        # 3. Scenario-Engine
        maps = self.scenario_engine.list_supported_maps()
        self.assertIsInstance(maps, list)
        if maps:
            self.assertGreaterEqual(maps[0]["variations_count"], 1)

        # 4. Sandbox-Engine
        opts = {
            "title_level": 3,
            "resources": {"G_Gold": 50000},
            "reveal_fog": True,
        }
        lua_code = self.sandbox_engine.generate_lua_sandbox_code(opts)
        self.assertIn("Logic.KnightUpgrade", lua_code)
        self.assertIn("Display.SetRenderFogOfWar(-1)", lua_code)

    def test_phase2_gui_functionality(self):
        """Validiert alle Registerkarten und Signale der PyQt6 GUI aus Phase 2."""
        # 1. Hauptfenster
        self.assertEqual(self.window.tab_widget.count(), 4)

        # 2. Tab 1: Config Tab
        cfg_tab = self.window.tab_config
        self.assertIsNotNone(cfg_tab.preset_combo)
        cfg_tab.preset_combo.setCurrentIndex(0)
        collected = cfg_tab._collect_data_from_widgets()
        self.assertIsInstance(collected["settler_limits"], list)

        # 3. Tab 2: Scenario Tab
        scen_tab = self.window.tab_scenarios
        self.assertIsInstance(scen_tab.list_maps.count(), int)

        # 4. Tab 3: Sandbox Tab
        sand_tab = self.window.tab_sandbox
        self.assertIsInstance(sand_tab.list_maps.count(), int)
        self.assertTrue(len(sand_tab.txt_preview.toPlainText()) > 20)

        # 5. Tab 4: System Tab
        sys_tab = self.window.tab_system
        self.assertGreaterEqual(sys_tab.table_patcher.rowCount(), 8)

        # 6. Log-Konsole
        test_text = "End-to-End Test erfolgreich"
        self.window.log(test_text, "success")
        self.assertIn(test_text, self.window.log_console.toPlainText())

    def test_phase3_launcher_file(self):
        """Validiert die Starter-Batchdatei START_MOD_MANAGER.bat aus Phase 3."""
        bat_path = os.path.join(self.system.workspace_path, "START_MOD_MANAGER.bat")
        if not os.path.isfile(bat_path):
            from ModManager.utils import get_base_path
            bat_path = os.path.abspath(os.path.join(get_base_path(), "..", "..", "START_MOD_MANAGER.bat"))
        self.assertTrue(
            os.path.isfile(bat_path), f"START_MOD_MANAGER.bat existiert nicht unter {bat_path}!"
        )

        with open(bat_path, "r", encoding="utf-8", errors="ignore") as f:
            bat_content = f.read()

        self.assertIn("net session", bat_content)
        self.assertIn("Start-Process", bat_content)
        self.assertIn("RunAs", bat_content)
        self.assertIn("ModManager\\main.py", bat_content)


if __name__ == "__main__":
    unittest.main()

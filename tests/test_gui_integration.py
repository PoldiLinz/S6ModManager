"""
UI- und Integrationstests für Phase 2 (PyQt6 MainWindow & Tabs)
"""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ModManager.app_window import MainWindow
from ModManager.tab_config import ConfigTab
from ModManager.tab_scenarios import ScenarioTab
from ModManager.tab_sandbox import SandboxTab
from ModManager.tab_system import SystemTab


class TestGuiIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialisiere QApplication einmalig für die Test-Suite
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

        # Lade Theme QSS
        theme_path = os.path.join(
            os.path.dirname(__file__), "..", "styles", "theme.qss"
        )
        if os.path.exists(theme_path):
            with open(theme_path, "r", encoding="utf-8") as f:
                cls.app.setStyleSheet(f.read())

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()

    def test_main_window_initialization(self):
        """Prüft, ob das Hauptfenster, die Titel und alle 4 Tabs existieren."""
        self.assertEqual(
            self.window.windowTitle(),
            "Die Siedler 6 - Mod & Map Manager (S6Patcher Edition)",
        )
        self.assertEqual(self.window.tab_widget.count(), 4)
        self.assertEqual(
            self.window.tab_widget.tabText(0), "⚙️ Konfigurationen & Limits"
        )
        self.assertEqual(
            self.window.tab_widget.tabText(1), "🗺️ Karten & Szenario-Varianten"
        )
        self.assertEqual(
            self.window.tab_widget.tabText(2), "🧪 Testmap & Sandbox-Injektor"
        )
        self.assertEqual(
            self.window.tab_widget.tabText(3), "🛡️ System & ModLoader-Status"
        )

    def test_config_tab_widgets_and_presets(self):
        """Prüft die Funktionsfähigkeit von Tab 1 (Config Editor & Presets)."""
        cfg_tab: ConfigTab = self.window.tab_config
        self.assertGreaterEqual(cfg_tab.preset_combo.count(), 3)

        # Preset 'Vanilla_Default.json' auswählen
        idx = cfg_tab.preset_combo.findData("Vanilla_Default.json")
        self.assertGreaterEqual(idx, 0)
        cfg_tab.preset_combo.setCurrentIndex(idx)

        # Werte prüfen
        self.assertEqual(cfg_tab.spin_settler_1.value(), 50)
        self.assertEqual(cfg_tab.spin_settler_4.value(), 200)
        self.assertEqual(cfg_tab.spin_store_1.value(), 54)
        self.assertEqual(cfg_tab.spin_mine_stone.value(), 250)
        self.assertTrue(cfg_tab.radio_bat_6.isChecked())

        # Preset 'Extreme_Megacity.json' auswählen
        idx_ext = cfg_tab.preset_combo.findData("Extreme_Megacity.json")
        self.assertGreaterEqual(idx_ext, 0)
        cfg_tab.preset_combo.setCurrentIndex(idx_ext)

        self.assertEqual(cfg_tab.spin_settler_4.value(), 1500)
        self.assertEqual(cfg_tab.spin_mine_stone.value(), 999999)
        self.assertTrue(cfg_tab.radio_bat_12.isChecked())

        # Daten-Export testen
        collected = cfg_tab._collect_data_from_widgets()
        self.assertIn("settler_limits", collected)
        self.assertEqual(collected["settler_limits"][-1], 1500)
        self.assertEqual(collected["battalion_size"], 12)

    def test_scenario_tab_widgets_and_selection(self):
        """Prüft die Funktionsfähigkeit von Tab 2 (Karten & Szenarien)."""
        scen_tab: ScenarioTab = self.window.tab_scenarios
        self.assertGreaterEqual(scen_tab.list_maps.count(), 1)

        # Erste Karte auswählen
        scen_tab.list_maps.setCurrentRow(0)
        self.assertIsNotNone(scen_tab.current_map_data)
        self.assertEqual(scen_tab.current_map_data["map_id"], "me_fairtrade")

        # Varianten Radiobuttons prüfen
        radio_buttons = scen_tab.btn_group_vars.buttons()
        self.assertGreaterEqual(len(radio_buttons), 2)

    def test_sandbox_tab_widgets_and_lua_preview(self):
        """Prüft die Funktionsfähigkeit von Tab 3 (Sandbox Injektor)."""
        sand_tab: SandboxTab = self.window.tab_sandbox
        self.assertGreaterEqual(sand_tab.combo_maps.count(), 1)

        # Optionen umschalten und Lua-Vorschau prüfen
        sand_tab.chk_duke.setChecked(True)
        sand_tab.spin_gold.setValue(75000)
        sand_tab._update_lua_preview()

        preview_text = sand_tab.txt_lua_preview.toPlainText()
        self.assertIn("Logic.KnightUpgrade", preview_text)
        self.assertIn("75000", preview_text)

    def test_system_tab_widgets(self):
        """Prüft die Funktionsfähigkeit von Tab 4 (System & ModLoader Status)."""
        sys_tab: SystemTab = self.window.tab_system
        self.assertTrue(bool(sys_tab.lbl_game_path.text()))
        self.assertGreaterEqual(sys_tab.table_patcher.rowCount(), 8)

    def test_log_console_signal(self):
        """Prüft, ob Signale aus den Tabs sauber in der Log-Konsole ankommen."""
        test_msg = "Test-Nachricht an Konsole"
        self.window.tab_config.status_message.emit(test_msg, "success")
        console_content = self.window.log_console.toPlainText()
        self.assertIn(test_msg, console_content)
    def test_menu_bar_actions(self):
        """Prüft, ob die obere Menüleiste und alle Menüs vorhanden sind."""
        menubar = self.window.menuBar()
        self.assertIsNotNone(menubar)
        actions = menubar.actions()
        menu_titles = [a.text() for a in actions]
        self.assertIn("▶ Start", menu_titles)
        self.assertIn("⚙️ Einstellungen", menu_titles)
        self.assertIn("❓ Hilfe", menu_titles)

    def test_lightroom_revert_button(self):
        """Prüft die Lightroom-Style Revert-Funktionalität auf Vanilla-Werte."""
        cfg_tab: ConfigTab = self.window.tab_config
        # Ändere Wert für Kathedrale Stufe 1 (Vanilla: 50)
        cfg_tab.spin_settler_1.setValue(750)
        self.assertEqual(cfg_tab.spin_settler_1.value(), 750)

        # Klicke auf den Revert Button (Siedler Stufe 1)
        cfg_tab.btn_revert_settler_1.click()
        self.assertEqual(cfg_tab.spin_settler_1.value(), 50)

    def test_settings_dialog(self):
        """Prüft, ob der allgemeine Einstellungsdialog korrekt instanziiert werden kann."""
        from ModManager.dialog_settings import SettingsDialog
        dlg = SettingsDialog(self.window.system_engine, self.window)
        self.assertEqual(dlg.windowTitle(), "⚙️ Allgemeine Einstellungen & Pfade")
        dlg.close()


if __name__ == "__main__":
    unittest.main()


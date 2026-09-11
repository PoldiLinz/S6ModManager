"""
Unit Tests für SystemEngine
"""

import os
import unittest
from ModManager.engines.system_engine import SystemEngine


class TestSystemEngine(unittest.TestCase):

    def setUp(self):
        self.engine = SystemEngine()

    def test_paths_initialized(self):
        self.assertTrue(os.path.exists(self.engine.workspace_path))
        self.assertTrue(os.path.exists(self.engine.presets_path))
        self.assertTrue(os.path.exists(self.engine.scenarios_path))
        self.assertTrue(os.path.exists(self.engine.backups_path))

    def test_protected_files_recognition(self):
        self.assertTrue(self.engine.is_protected_file("config/models.xml"))
        self.assertTrue(self.engine.is_protected_file(r"config\entities\u_knightredprince.xml"))
        self.assertTrue(self.engine.is_protected_file("graphics/effects/road.fx"))
        self.assertFalse(self.engine.is_protected_file("config/entities/b_storehouse.xml"))
        self.assertFalse(self.engine.is_protected_file("maps/singleplayer/me_fairtrade/mapscript.lua"))

    def test_check_s6patcher_integrity(self):
        status, results = self.engine.check_s6patcher_integrity()
        self.assertIn(status, ["OK", "WARNING", "ERROR"])
        self.assertEqual(len(results), len(SystemEngine.PROTECTED_S6PATCHER_FILES))

    def test_list_backups(self):
        backups = self.engine.list_backups()
        self.assertIsInstance(backups, list)

        # Test mit einer temporären Backup-ZIP-Datei
        test_zip = os.path.join(self.engine.backups_path, "test_dummy_backup.zip")
        try:
            import zipfile
            with zipfile.ZipFile(test_zip, "w") as zf:
                zf.writestr("dummy.txt", "test content")
            backups = self.engine.list_backups()
            self.assertGreaterEqual(len(backups), 1)
            found = next((b for b in backups if b["filename"] == "test_dummy_backup.zip"), None)
            self.assertIsNotNone(found)
            self.assertGreater(found["size_bytes"], 0)
            self.assertIn("KB", found["size_str"])
            self.assertNotEqual(found["created"], "Unbekannt")
        finally:
            if os.path.exists(test_zip):
                os.remove(test_zip)

    def test_documents_and_workspace_derivation(self):
        self.assertIsNotNone(self.engine.documents_path)
        self.assertTrue(self.engine.documents_path.endswith("DIE SIEDLER - Aufstieg eines Königreichs") or 
                        self.engine.documents_path.endswith("The Settlers - Rise of an Empire"))
        self.assertEqual(self.engine.workspace_path, os.path.join(self.engine.documents_path, "UserMods"))
        self.assertEqual(self.engine.user_maps_path, os.path.join(self.engine.documents_path, "UserMaps"))
        self.assertEqual(self.engine.user_script_path, os.path.join(self.engine.documents_path, "Script"))

    def test_has_modloader_check(self):
        has_ml = self.engine.has_modloader()
        self.assertIsInstance(has_ml, bool)

    def test_save_and_load_settings_independence(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_docs = os.path.join(temp_dir, "CustomDocs", "DIE SIEDLER - Aufstieg eines Königreichs")
            test_game = os.path.join(temp_dir, "CustomGame")
            os.makedirs(test_docs, exist_ok=True)
            os.makedirs(test_game, exist_ok=True)

            engine = SystemEngine(documents_path=test_docs, game_path=test_game)
            self.assertEqual(engine.documents_path, os.path.abspath(test_docs))
            self.assertEqual(engine.workspace_path, os.path.abspath(os.path.join(test_docs, "UserMods")))
            self.assertEqual(engine.game_path, os.path.abspath(test_game))
            self.assertEqual(engine.modloader_path, os.path.abspath(os.path.join(test_game, "modloader", "shr", "mod")))

    def test_bundled_s6packer_resolution(self):
        packer_path = self.engine.get_bundled_s6packer_path()
        self.assertIsNotNone(packer_path)
        self.assertTrue(packer_path.endswith("S6Packer.exe"))

    def test_modloader_root_path_and_directories(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            test_docs = os.path.join(temp_dir, "Docs", "DIE SIEDLER - Aufstieg eines Königreichs")
            test_game = os.path.join(temp_dir, "Game")
            os.makedirs(test_docs, exist_ok=True)
            os.makedirs(test_game, exist_ok=True)

            engine = SystemEngine(documents_path=test_docs, game_path=test_game)
            self.assertEqual(engine.modloader_root_path, os.path.join(engine.game_path, "modloader"))
            self.assertEqual(engine.modloader_path, os.path.join(engine.modloader_root_path, "shr", "mod"))

            # Prüfen ob ensure_workspace_directories die Modloader-Ordner anlegt
            engine.ensure_workspace_directories()
            self.assertTrue(os.path.isdir(engine.modloader_root_path))
            self.assertTrue(os.path.isdir(engine.modloader_path))
            self.assertTrue(os.path.isdir(os.path.join(engine.modloader_root_path, "base")))


if __name__ == "__main__":
    unittest.main()

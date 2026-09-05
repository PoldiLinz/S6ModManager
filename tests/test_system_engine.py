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


if __name__ == "__main__":
    unittest.main()

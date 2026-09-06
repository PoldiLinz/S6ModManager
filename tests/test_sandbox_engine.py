"""
Unit Tests für SandboxEngine
"""

import os
import shutil
import tempfile
import unittest
from ModManager.engines.system_engine import SystemEngine
from ModManager.engines.sandbox_engine import SandboxEngine


class TestSandboxEngine(unittest.TestCase):

    def setUp(self):
        self.system = SystemEngine()
        self.sandbox = SandboxEngine(self.system)
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_lua_sandbox_code(self):
        options = {
            "title_level": 3,
            "resources": {"G_Gold": 50000},
            "reveal_fog": True
        }
        lua_code = self.sandbox.generate_lua_sandbox_code(options)
        self.assertIn("Logic.KnightUpgrade", lua_code)
        self.assertIn("Logic.AddGoodToStock(hq, Goods.G_Gold, 50000", lua_code)
        self.assertIn("Display.SetRenderFogOfWar(-1)", lua_code)
        self.assertIn(SandboxEngine.INJECTION_START_MARKER, lua_code)
        self.assertIn(SandboxEngine.INJECTION_END_MARKER, lua_code)

    def test_inject_and_remove_sandbox(self):
        # Erstelle ein temporäres mapscript.lua
        sample_script = os.path.join(self.test_dir, "mapscript.lua")
        sample_content = """
function Mission_InitPlayers()
    AddResourcesToPlayer(Goods.G_Gold, 100, 1)
end

function Mission_FirstMapAction()
    StartSimpleJob("CheckMonth")
end
"""
        with open(sample_script, "w", encoding="utf-8") as f:
            f.write(sample_content)

        self.assertFalse(self.sandbox.is_script_injected(sample_script))

        # Injektion
        options = {"title_level": 3, "resources": {"G_Gold": 50000}, "reveal_fog": True}
        self.sandbox.inject_sandbox_into_script(sample_script, options)
        self.assertTrue(self.sandbox.is_script_injected(sample_script))

        # Bereinigung
        self.sandbox.remove_sandbox_from_script(sample_script)
        self.assertFalse(self.sandbox.is_script_injected(sample_script))

        # Inhalt prüfen
        with open(sample_script, "r", encoding="utf-8") as f:
            cleaned = f.read()
        self.assertIn("function Mission_FirstMapAction()", cleaned)
        self.assertNotIn("Logic.KnightUpgrade", cleaned)


if __name__ == "__main__":
    unittest.main()

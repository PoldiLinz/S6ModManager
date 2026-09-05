"""
Siedler 6 Mod Manager - Sandbox Engine
Injiziert High-Tier-Testcode und Cheat-Funktionen temporär in Kartenskripte (mapscript.lua).
"""

import os
import re
import shutil
from typing import Dict, List, Any, Optional, Tuple
from ModManager.engines.system_engine import SystemEngine


class SandboxEngine:
    """Verwaltet Testmap-Injektionen und Cheat-Sandboxen für schnelles High-Tier-Testing."""

    INJECTION_START_MARKER = "-- === S6_SANDBOX_INJECTION_START ==="
    INJECTION_END_MARKER = "-- === S6_SANDBOX_INJECTION_END ==="

    def __init__(self, system_engine: Optional[SystemEngine] = None):
        self.system = system_engine or SystemEngine()

    def list_testable_maps(self) -> List[Dict[str, Any]]:
        """Listet alle testbaren Karten aus UserMaps und ModLoader auf."""
        maps = []

        # 1. UserMaps
        if os.path.exists(self.system.user_maps_path):
            for item in os.listdir(self.system.user_maps_path):
                f_path = os.path.join(self.system.user_maps_path, item)
                script_path = os.path.join(f_path, "mapscript.lua")
                if os.path.isdir(f_path) and os.path.exists(script_path):
                    is_injected = self.is_script_injected(script_path)
                    maps.append({
                        "name": f"[UserMap] {item}",
                        "map_id": item,
                        "script_path": script_path,
                        "folder_path": f_path,
                        "is_injected": is_injected,
                        "source": "UserMaps"
                    })

        # 2. ModLoader Singleplayer Karten
        mod_maps_dir = os.path.join(self.system.modloader_path, "maps", "singleplayer")
        if os.path.exists(mod_maps_dir):
            for item in os.listdir(mod_maps_dir):
                f_path = os.path.join(mod_maps_dir, item)
                script_path = os.path.join(f_path, "mapscript.lua")
                if os.path.isdir(f_path) and os.path.exists(script_path):
                    is_injected = self.is_script_injected(script_path)
                    maps.append({
                        "name": f"[ModLoader SP] {item}",
                        "map_id": item,
                        "script_path": script_path,
                        "folder_path": f_path,
                        "is_injected": is_injected,
                        "source": "ModLoader"
                    })

        # 3. Scenarios library
        if os.path.exists(self.system.scenarios_path):
            for map_id in os.listdir(self.system.scenarios_path):
                map_folder = os.path.join(self.system.scenarios_path, map_id)
                if not os.path.isdir(map_folder):
                    continue
                for var_id in os.listdir(map_folder):
                    var_folder = os.path.join(map_folder, var_id)
                    script_path = os.path.join(var_folder, "map", "mapscript.lua")
                    if os.path.exists(script_path):
                        is_injected = self.is_script_injected(script_path)
                        maps.append({
                            "name": f"[Szenario] {map_id} ({var_id})",
                            "map_id": f"{map_id}/{var_id}",
                            "script_path": script_path,
                            "folder_path": var_folder,
                            "is_injected": is_injected,
                            "source": "Scenarios"
                        })

        return maps

    def is_script_injected(self, script_path: str) -> bool:
        """Prüft, ob in das angegebene mapscript.lua bereits Sandbox-Code injiziert ist."""
        if not os.path.exists(script_path):
            return False
        try:
            with open(script_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                return self.INJECTION_START_MARKER in content
        except Exception:
            return False

    def generate_lua_sandbox_code(self, options: Dict[str, Any]) -> str:
        """Erzeugt den gekapselten Lua-Sandbox-Codeblock."""
        upgrade_knight = options.get("upgrade_knight", True)
        add_resources = options.get("add_resources", True)
        fill_storehouse = options.get("fill_storehouse", True)
        reveal_fog = options.get("reveal_fog", True)
        gold_amount = options.get("gold_amount", 50000)
        res_amount = options.get("resources_amount", 500)

        lines = [
            self.INJECTION_START_MARKER,
            "-- Automatisch generierter Sandbox-Testcode für Siedler 6 High-Tier Testing",
            "if not _G.__S6_Sandbox_Injected then",
            "    _G.__S6_Sandbox_Injected = true",
            "",
            "    local _Orig_Mission_FirstMapAction = Mission_FirstMapAction",
            "    function Mission_FirstMapAction()",
            "        if _Orig_Mission_FirstMapAction then",
            "            _Orig_Mission_FirstMapAction()",
            "        end",
            "",
            "        local humanPlayerID = 1",
            "        if GUI and GUI.GetPlayerID then",
            "            local pid = GUI.GetPlayerID()",
            "            if pid and pid > 0 then humanPlayerID = pid end",
            "        end",
            ""
        ]

        # 1. Herzog-Titel
        if upgrade_knight:
            lines.extend([
                "        -- 1. Ritter-Beförderung auf Herzog (Stufe 6)",
                "        for i = 1, 6 do",
                "            Logic.KnightUpgrade(humanPlayerID)",
                "        end",
                ""
            ])

        # 2. Ressourcen
        if add_resources:
            lines.extend([
                f"        -- 2. Start-Ressourcen ({gold_amount} Gold, {res_amount} Rohstoffe)",
                f"        AddResourcesToPlayer(Goods.G_Gold, {gold_amount}, humanPlayerID)",
                f"        AddResourcesToPlayer(Goods.G_Wood, {res_amount}, humanPlayerID)",
                f"        AddResourcesToPlayer(Goods.G_Stone, {res_amount}, humanPlayerID)",
                f"        AddResourcesToPlayer(Goods.G_Iron, {res_amount}, humanPlayerID)",
                f"        AddResourcesToPlayer(Goods.G_Grain, {res_amount}, humanPlayerID)",
                f"        AddResourcesToPlayer(Goods.G_Milk, {res_amount}, humanPlayerID)",
                f"        AddResourcesToPlayer(Goods.G_Wool, {res_amount}, humanPlayerID)",
                f"        AddResourcesToPlayer(Goods.G_Honeycomb, {res_amount}, humanPlayerID)",
                f"        AddResourcesToPlayer(Goods.G_Carcass, {res_amount}, humanPlayerID)",
                f"        AddResourcesToPlayer(Goods.G_RawFish, {res_amount}, humanPlayerID)",
                f"        AddResourcesToPlayer(Goods.G_Herb, {res_amount}, humanPlayerID)",
                ""
            ])

        # 3. Lagerhaus befüllen
        if fill_storehouse:
            lines.extend([
                "        -- 3. Start-Lagerhäuser befüllen",
                "        local buildings = { Logic.GetBuildingsByPlayer(humanPlayerID) }",
                "        for i = 1, #buildings do",
                "            local bId = buildings[i]",
                "            if Logic.IsBuilding(bId) == 1 then",
                f"                Logic.AddGoodToStock(bId, Goods.G_Wood, {res_amount}, true, true)",
                f"                Logic.AddGoodToStock(bId, Goods.G_Stone, {res_amount}, true, true)",
                f"                Logic.AddGoodToStock(bId, Goods.G_Iron, {res_amount}, true, true)",
                "            end",
                "        end",
                ""
            ])

        # 4. Fog of War Reveal
        if reveal_fog:
            lines.extend([
                "        -- 4. Nebel des Krieges aufdecken (Fog of War Reveal)",
                "        Logic.SetExplorationStatus(-1)",
                "        Logic.ExecuteInLuaLocalState('Display.SetRenderFogOfWar(-1)')",
                "        Logic.ExecuteInLuaLocalState('GUI.MiniMap_SetRenderFogOfWar(-1)')",
                ""
            ])

        # 5. InGame Feedback Note
        lines.extend([
            "        -- InGame Feedback anzeigen",
            "        if GUI and GUI.AddNote then",
            '            GUI.AddNote("🧪 SANDBOX-MODUS AKTIV: Herzog-Titel, 50.000 Gold & Rohstoffe bereitgestellt!")',
            "        end",
            "    end",
            "end",
            self.INJECTION_END_MARKER,
            ""
        ])

        return "\n".join(lines)

    def inject_sandbox_into_script(self, script_path: str, options: Dict[str, Any]) -> bool:
        """Injiziert den Sandbox-Codeblock in das angegebene mapscript.lua."""
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Skriptdatei nicht gefunden: {script_path}")

        # Zuerst bereits vorhandene Injektion entfernen, falls vorhanden
        if self.is_script_injected(script_path):
            self.remove_sandbox_from_script(script_path)

        # Sauberes Backup erstellen, falls noch keines existiert
        backup_path = script_path + ".clean_backup"
        if not os.path.exists(backup_path):
            shutil.copy2(script_path, backup_path)

        # Original-Inhalt lesen
        with open(script_path, "r", encoding="utf-8", errors="ignore") as f:
            original_content = f.read()

        lua_injection = self.generate_lua_sandbox_code(options)

        new_content = original_content.rstrip() + "\n\n" + lua_injection

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True

    def remove_sandbox_from_script(self, script_path: str) -> bool:
        """Entfernt den injizierten Sandbox-Block restlos aus dem Skript."""
        if not os.path.exists(script_path):
            return False

        # Prüfe, ob sauberes Backup vorliegt
        backup_path = script_path + ".clean_backup"
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, script_path)
            try:
                os.remove(backup_path)
            except Exception:
                pass
            return True

        # Fallback: Per Regex den Marker-Block entfernen
        with open(script_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        pattern = re.compile(
            re.escape(self.INJECTION_START_MARKER) + r".*?" + re.escape(self.INJECTION_END_MARKER),
            re.DOTALL
        )

        cleaned_content = re.sub(pattern, "", content).rstrip() + "\n"

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(cleaned_content)

        return True

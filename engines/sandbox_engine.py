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
        """Erzeugt den gekapselten Lua-Sandbox-Codeblock basierend auf Startbedingungen."""
        title_level = options.get("title_level", 1) # 1=Ritter, ..., 6=Herzog
        b_castle = options.get("b_castle", 1)
        b_storehouse = options.get("b_storehouse", 1)
        b_church = options.get("b_church", 1)
        resources = options.get("resources", {})
        troops = options.get("troops", {})
        reveal_fog = options.get("reveal_fog", False)
        instant_victory = options.get("instant_victory", False)

        lines = [
            self.INJECTION_START_MARKER,
            "-- Automatisch generierter Sandbox-Testcode für Siedler 6",
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
            "        local hq = Logic.GetHeadquarters(humanPlayerID)",
            ""
        ]

        # 1. Titel
        if title_level > 1:
            lines.extend([
                f"        -- 1. Ritter-Beförderung auf Stufe {title_level}",
                f"        for i = 1, {title_level - 1} do",
                "            Logic.KnightUpgrade(humanPlayerID)",
                "        end",
                ""
            ])

        # 2. Rohstoffe
        if resources:
            lines.append("        -- 2. Start-Rohstoffe (In Burg/Lagerhaus einlagern)")
            for good, amount in resources.items():
                if amount > 0:
                    lines.append(f"        if hq > 0 then Logic.AddGoodToStock(hq, Goods.{good}, {amount}, true, true) end")
            lines.append("")

        # 3. Truppen
        if troops:
            lines.append("        -- 3. Start-Truppen")
            lines.extend([
                "        local px, py = 0, 0",
                "        if hq > 0 then px, py = Logic.GetEntityPosition(hq) end",
            ])
            for ent_type, amount in troops.items():
                if amount > 0:
                    lines.extend([
                        f"        for i = 1, {amount} do",
                        f"            Logic.CreateEntity(Entities.{ent_type}, px+400, py+400, 0, humanPlayerID)",
                        "        end"
                    ])
            lines.append("")

        # 4. Fog of War Reveal
        if reveal_fog:
            lines.extend([
                "        -- 4. Nebel des Krieges aufdecken",
                "        Logic.SetExplorationStatus(-1)",
                "        Logic.ExecuteInLuaLocalState('Display.SetRenderFogOfWar(-1)')",
                "        Logic.ExecuteInLuaLocalState('GUI.MiniMap_SetRenderFogOfWar(-1)')",
                ""
            ])

        # 5. Instant Victory
        if instant_victory:
            lines.extend([
                "        -- 5. Sofortiger Sieg",
                "        Logic.ExecuteInLuaLocalState('GUI.AddNote(\\'Instant Victory Cheat aktiviert.\\')')",
                "        Logic.PlayerSetGameStateToWon(humanPlayerID)",
                ""
            ])

        # 6. Gebäude-Upgrades
        if b_castle > 1 or b_storehouse > 1 or b_church > 1:
            lines.extend([
                "        -- 6. Gebäude-Upgrades (Verzögert auf Sekunde 2, damit Gebäude existieren)",
                "        Trigger.RequestTrigger(Events.LOGIC_EVENT_EVERY_SECOND, nil, 'Sandbox_UpgradeBuildings_Job', 1, nil, {",
                f"            c={b_castle}, s={b_storehouse}, ch={b_church}, p=humanPlayerID",
                "        })",
                ""
            ])

        lines.extend([
            "        -- InGame Feedback anzeigen",
            "        if GUI and GUI.AddNote then",
            '            GUI.AddNote("🧪 SANDBOX-MODUS AKTIV: Startbedingungen wurden injiziert!")',
            "        end",
            "    end",
            "",
            "    function Sandbox_UpgradeBuildings_Job(data)",
            "        local hq = Logic.GetHeadquarters(data.p)",
            "        local store = Logic.GetStoreHouse(data.p)",
            "        local church = 0",
            "        local buildings = {Logic.GetPlayerEntitiesInCategory(data.p, EntityCategories.Church)}",
            "        if #buildings > 0 then church = buildings[1] end",
            "",
            "        if data.c > 1 and hq > 0 then",
            "            for i=1, data.c-1 do Logic.UpgradeBuilding(hq) end",
            "        end",
            "        if data.s > 1 and store > 0 then",
            "            for i=1, data.s-1 do Logic.UpgradeBuilding(store) end",
            "        end",
            "        if data.ch > 1 and church > 0 then",
            "            for i=1, data.ch-1 do Logic.UpgradeBuilding(church) end",
            "        end",
            "        return true -- Trigger beenden",
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

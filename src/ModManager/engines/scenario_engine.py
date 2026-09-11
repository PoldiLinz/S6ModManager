"""
Siedler 6 Mod Manager - Scenario Engine
Verwaltet Karten-Bibliotheken, Szenario-Varianten, ModLoader-Synchronisation und UserMap-Import.
"""

import os
import json
import shutil
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from ModManager.engines.system_engine import SystemEngine


class ScenarioEngine:
    """Verwaltet Szenario-Varianten und schaltet Karten im ModLoader um."""

    def __init__(self, system_engine: Optional[SystemEngine] = None):
        self.system = system_engine or SystemEngine()
        self.scenarios_dir = self.system.scenarios_path
        self.user_maps_dir = self.system.user_maps_path

    # -------------------------------------------------------------------------
    # Scenario Discovery & Metadata
    # -------------------------------------------------------------------------

    def list_supported_maps(self) -> List[Dict[str, Any]]:
        """
        Listet alle in Scenarios/ definierten Karten auf und prüft,
        welche Variante aktuell im ModLoader aktiv ist.
        """
        maps = []
        if not os.path.exists(self.scenarios_dir):
            return maps

        for map_id in os.listdir(self.scenarios_dir):
            map_folder = os.path.join(self.scenarios_dir, map_id)
            if not os.path.isdir(map_folder):
                continue

            variations = self.list_variations_for_map(map_id)
            active_variant = self.get_active_variant_id(map_id)

            # Versuchen, einen lesbaren Kartennamen zu finden
            friendly_name = map_id
            for v in variations:
                if v.get("is_vanilla"):
                    friendly_name = v.get("title", map_id).replace("Original: ", "").replace(" (Vanilla)", "")
                    break

            maps.append({
                "map_id": map_id,
                "friendly_name": friendly_name,
                "variations_count": len(variations),
                "active_variant_id": active_variant,
                "is_mod_active": active_variant is not None and active_variant != "vanilla",
                "variations": variations
            })

        return sorted(maps, key=lambda x: x["map_id"])

    def list_variations_for_map(self, map_id: str) -> List[Dict[str, Any]]:
        """Listet alle Abwandlungen/Varianten für eine bestimmte Karten-ID auf."""
        variations = []
        map_dir = os.path.join(self.scenarios_dir, map_id)
        if not os.path.exists(map_dir):
            return variations

        # Einen Fallback für die Vorschau suchen (falls z.B. Vanilla kein eigenes Bild hat,
        # aber ein Mod-Ordner ein mappreview.png mitliefert).
        fallback_preview = None
        for root, dirs, files in os.walk(map_dir):
            if "mappreview.png" in files:
                fallback_preview = os.path.join(root, "mappreview.png")
                break

        for var_id in os.listdir(map_dir):
            var_dir = os.path.join(map_dir, var_id)
            if not os.path.isdir(var_dir):
                continue

            json_path = os.path.join(var_dir, "scenario.json")
            preview_path = os.path.join(var_dir, "mappreview.png")
            if not os.path.exists(preview_path):
                # Auch im map-Unterordner prüfen
                preview_sub = os.path.join(var_dir, "map", "mappreview.png")
                if os.path.exists(preview_sub):
                    preview_path = preview_sub
                else:
                    preview_path = fallback_preview

            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    meta = {}
            else:
                meta = {
                    "id": var_id,
                    "title": var_id.replace("_", " ").title(),
                    "author": "Unbekannt",
                    "description": "Keine Beschreibung vorhanden.",
                    "is_vanilla": var_id.lower() == "vanilla"
                }

            meta["id"] = var_id
            meta["map_id"] = map_id
            meta["folder_path"] = var_dir
            meta["preview_image"] = preview_path
            variations.append(meta)

        # Vanilla immer an erster Stelle
        return sorted(variations, key=lambda x: (not x.get("is_vanilla", False), x.get("id", "")))

    def get_active_variant_id(self, map_id: str) -> Optional[str]:
        """
        Ermittelt, welche Variante einer Karte im ModLoader aktiv ist.
        Wenn im ModLoader keine Kartendateien liegen, ist 'vanilla' aktiv.
        """
        mod_map_dir = os.path.join(self.system.modloader_path, "maps", "singleplayer", map_id)
        if not os.path.exists(mod_map_dir) or not os.listdir(mod_map_dir):
            return "vanilla"

        # Prüfe anhand von mapscript.lua Hash oder info.xml
        mod_script = os.path.join(mod_map_dir, "mapscript.lua")
        if not os.path.exists(mod_script):
            return "unknown_mod"

        mod_hash = self._file_hash(mod_script)
        variations = self.list_variations_for_map(map_id)

        for v in variations:
            if v.get("is_vanilla"):
                continue
            var_script = os.path.join(v["folder_path"], "map", "mapscript.lua")
            if os.path.exists(var_script) and self._file_hash(var_script) == mod_hash:
                return v["id"]

        return "custom_mod"

    @staticmethod
    def _file_hash(filepath: str) -> str:
        """Berechnet MD5-Hash einer Datei."""
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    # -------------------------------------------------------------------------
    # Activation & Revert
    # -------------------------------------------------------------------------

    def activate_scenario(self, map_id: str, variant_id: str) -> bool:
        """
        Aktiviert eine bestimmte Szenario-Variante für eine Karte im ModLoader.
        Wenn variant_id == 'vanilla', wird der ModLoader-Eintrag entfernt.
        """
        if variant_id == "vanilla":
            return self.revert_map_to_vanilla(map_id)

        var_dir = os.path.join(self.scenarios_dir, map_id, variant_id)
        if not os.path.exists(var_dir):
            raise FileNotFoundError(f"Szenario-Variante nicht gefunden: {var_dir}")

        # 1. Map-Dateien kopieren
        src_map_dir = os.path.join(var_dir, "map")
        target_map_dir = os.path.join(self.system.modloader_path, "maps", "singleplayer", map_id)
        
        if os.path.exists(src_map_dir):
            os.makedirs(target_map_dir, exist_ok=True)
            for item in os.listdir(src_map_dir):
                s = os.path.join(src_map_dir, item)
                d = os.path.join(target_map_dir, item)
                if os.path.isfile(s):
                    shutil.copy2(s, d)

        # 2. Lokalisierungstexte kopieren
        src_text_ingame = os.path.join(var_dir, "text", "de", "ingame")
        target_text_ingame = os.path.join(self.system.modloader_path, "text", "de", "ingame")
        if os.path.exists(src_text_ingame):
            os.makedirs(target_text_ingame, exist_ok=True)
            for item in os.listdir(src_text_ingame):
                shutil.copy2(os.path.join(src_text_ingame, item), os.path.join(target_text_ingame, item))

        src_text_maps = os.path.join(var_dir, "text", "de", "maps")
        target_text_maps = os.path.join(self.system.modloader_path, "text", "de", "maps")
        if os.path.exists(src_text_maps):
            os.makedirs(target_text_maps, exist_ok=True)
            for item in os.listdir(src_text_maps):
                shutil.copy2(os.path.join(src_text_maps, item), os.path.join(target_text_maps, item))

        # 3. Änderungen in die mod.bba verpacken
        from ModManager.patcher.bba_packer import BBAPacker
        packer = BBAPacker(self.system.workspace_path)
        packer.prepare_mutation_staging(self.system)
        
        pack_map_dir = os.path.join(packer.pack_dir, "maps", "singleplayer", map_id)
        if os.path.exists(src_map_dir):
            os.makedirs(pack_map_dir, exist_ok=True)
            for item in os.listdir(src_map_dir):
                s = os.path.join(src_map_dir, item)
                d = os.path.join(pack_map_dir, item)
                if os.path.isfile(s):
                    shutil.copy2(s, d)

        pack_text_ingame = os.path.join(packer.pack_dir, "text", "de", "ingame")
        if os.path.exists(src_text_ingame):
            os.makedirs(pack_text_ingame, exist_ok=True)
            for item in os.listdir(src_text_ingame):
                shutil.copy2(os.path.join(src_text_ingame, item), os.path.join(pack_text_ingame, item))

        pack_text_maps = os.path.join(packer.pack_dir, "text", "de", "maps")
        if os.path.exists(src_text_maps):
            os.makedirs(pack_text_maps, exist_ok=True)
            for item in os.listdir(src_text_maps):
                shutil.copy2(os.path.join(src_text_maps, item), os.path.join(pack_text_maps, item))
                
        packer.pack_and_deploy(self.system.game_path)

        return True

    def revert_map_to_vanilla(self, map_id: str) -> bool:
        """
        Entfernt die Modifikationsdateien einer Karte aus dem ModLoader,
        sodass die Original-BBA des Spiels unverändert lädt.
        """
        target_map_dir = os.path.join(self.system.modloader_path, "maps", "singleplayer", map_id)
        if os.path.exists(target_map_dir):
            shutil.rmtree(target_map_dir, ignore_errors=True)

        # Lokalisierungsdateien der Map entfernen
        map_text_file = f"map_{map_id}.xml"
        for sub in ["ingame", "maps"]:
            t_file = os.path.join(self.system.modloader_path, "text", "de", sub, map_text_file)
            if os.path.exists(t_file):
                try:
                    os.remove(t_file)
                except Exception:
                    pass

        # 2. Änderungen in die mod.bba verpacken
        from ModManager.patcher.bba_packer import BBAPacker
        packer = BBAPacker(self.system.workspace_path)
        packer.prepare_mutation_staging(self.system)
        
        pack_map_dir = os.path.join(packer.pack_dir, "maps", "singleplayer", map_id)
        if os.path.exists(pack_map_dir):
            shutil.rmtree(pack_map_dir, ignore_errors=True)
            
        for sub in ["ingame", "maps"]:
            t_file = os.path.join(packer.pack_dir, "text", "de", sub, map_text_file)
            if os.path.exists(t_file):
                try:
                    os.remove(t_file)
                except Exception:
                    pass
                    
        packer.pack_and_deploy(self.system.game_path)

        return True

    # -------------------------------------------------------------------------
    # UserMap Import & Variation Creation
    # -------------------------------------------------------------------------

    def list_available_usermaps(self) -> List[Dict[str, Any]]:
        """Listet alle Karten auf, die sich im UserMaps-Ordner des Benutzers befinden."""
        usermaps = []
        if not os.path.exists(self.user_maps_dir):
            return usermaps

        for item in os.listdir(self.user_maps_dir):
            full_path = os.path.join(self.user_maps_dir, item)
            if os.path.isdir(full_path):
                # Prüfe auf Kartendateien (info.xml oder mapscript.lua)
                has_script = os.path.exists(os.path.join(full_path, "mapscript.lua"))
                has_info = os.path.exists(os.path.join(full_path, "info.xml"))
                preview = os.path.join(full_path, "mappreview.png")

                usermaps.append({
                    "name": item,
                    "folder_path": full_path,
                    "is_valid_map": has_script or has_info,
                    "preview_image": preview if os.path.exists(preview) else None
                })
            elif item.endswith(".s6map"):
                usermaps.append({
                    "name": item,
                    "folder_path": full_path,
                    "is_valid_map": True,
                    "preview_image": None
                })

        return sorted(usermaps, key=lambda x: x["name"])

    def import_usermap_as_scenario_variation(
        self,
        target_map_id: str,
        variant_id: str,
        title: str,
        description: str,
        source_usermap_folder: str,
        author: str = "User Modder"
    ) -> str:
        """
        Importiert eine User-Karte aus UserMaps als neue Variante/Abwandlung
        einer eingebauten Kampagnen-/Einzelspielerkarte.
        """
        if not os.path.exists(source_usermap_folder):
            raise FileNotFoundError(f"Quell-Kartenordner nicht gefunden: {source_usermap_folder}")

        target_var_dir = os.path.join(self.scenarios_dir, target_map_id, variant_id)
        target_map_files = os.path.join(target_var_dir, "map")
        target_text_ingame = os.path.join(target_var_dir, "text", "de", "ingame")
        target_text_maps = os.path.join(target_var_dir, "text", "de", "maps")

        os.makedirs(target_map_files, exist_ok=True)
        os.makedirs(target_text_ingame, exist_ok=True)
        os.makedirs(target_text_maps, exist_ok=True)

        # 1. Kartendateien kopieren
        for item in os.listdir(source_usermap_folder):
            s = os.path.join(source_usermap_folder, item)
            d = os.path.join(target_map_files, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)

        # 2. scenario.json Metadaten erstellen
        meta = {
            "id": variant_id,
            "map_id": target_map_id,
            "title": title,
            "author": author,
            "version": "1.0",
            "is_vanilla": False,
            "description": description,
            "features": [
                f"Ersetzt die Originalkarte {target_map_id}",
                f"Basiert auf UserMap: {os.path.basename(source_usermap_folder)}"
            ]
        }
        with open(os.path.join(target_var_dir, "scenario.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)

        # 3. Falls mappreview vorhanden, kopieren
        preview_src = os.path.join(source_usermap_folder, "mappreview.png")
        if os.path.exists(preview_src):
            shutil.copy2(preview_src, os.path.join(target_var_dir, "mappreview.png"))

        # 4. Standard Sprachdatei anlegen, falls nicht vorhanden
        text_filename = f"map_{target_map_id}.xml"
        text_content = f"""<?xml version="1.0" encoding="utf-8"?>
<root>
    <StringTable>
        <Map_{target_map_id}>
            <MapName>{title}</MapName>
            <MapDescription>{description}</MapDescription>
        </Map_{target_map_id}>
    </StringTable>
</root>
"""
        with open(os.path.join(target_text_ingame, text_filename), "w", encoding="utf-8") as f:
            f.write(text_content)
        with open(os.path.join(target_text_maps, text_filename), "w", encoding="utf-8") as f:
            f.write(text_content)

        return target_var_dir

"""
Siedler 6 Mod Manager - System Engine
Verwaltet Pfade, UAC-Rechte, S6Patcher-Schutzdateien und ModLoader-Dateistatus.
"""

import os
import sys
import ctypes
import shutil
import zipfile
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class SystemEngine:
    """Verwaltet Spielpfade, UAC-Berechtigungen, S6Patcher-Integrität und Backups."""

    PROTECTED_S6PATCHER_FILES = [
        os.path.normpath("config/models.xml"),
        os.path.normpath("config/modelsex.xml"),
        os.path.normpath("config/entities/u_knightredprince.xml"),
        os.path.normpath("config/entities/u_knightsabatta.xml"),
        os.path.normpath("config/entities/b_npc_barracks_me.xml"),
        os.path.normpath("config/sound/playlistevents.xml"),
        os.path.normpath("graphics/effects/road.fx"),
        os.path.normpath("script/mainmenu/mainmenudefault_background.lua"),
    ]

    DEFAULT_GAME_PATH = r"C:\Program Files (x86)\Ubisoft\DIE SIEDLER - Aufstieg eines Königreichs"

    def __init__(self, workspace_path: Optional[str] = None, game_path: Optional[str] = None):
        if workspace_path:
            self.workspace_path = os.path.abspath(workspace_path)
        else:
            self.workspace_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..")
            )

        self.game_path = game_path or self._detect_game_path()
        self.modloader_path = os.path.join(self.game_path, "modloader", "shr", "mod")
        self.user_maps_path = self._detect_user_maps_path()
        self.presets_path = os.path.join(self.workspace_path, "Presets")
        self.scenarios_path = os.path.join(self.workspace_path, "Scenarios")
        self.backups_path = os.path.join(self.workspace_path, "Backups")

        os.makedirs(self.backups_path, exist_ok=True)

    def _detect_game_path(self) -> str:
        """Sucht nach dem Spielverzeichnis."""
        if os.path.exists(self.DEFAULT_GAME_PATH):
            return self.DEFAULT_GAME_PATH
        
        # Alternative Pfade prüfen
        alt_paths = [
            r"D:\Ubisoft\DIE SIEDLER - Aufstieg eines Königreichs",
            r"C:\Spiele\DIE SIEDLER - Aufstieg eines Königreichs",
            r"D:\Games\The Settlers - Rise of an Empire",
            r"C:\Program Files (x86)\Ubisoft\The Settlers - Rise of an Empire",
        ]
        for p in alt_paths:
            if os.path.exists(p):
                return p
        return self.DEFAULT_GAME_PATH

    def _detect_user_maps_path(self) -> str:
        """Ermittelt den Pfad zu den UserMaps im Dokumenten-Verzeichnis."""
        user_docs = os.path.join(
            os.path.expanduser("~"), "Documents", "DIE SIEDLER - Aufstieg eines Königreichs", "UserMaps"
        )
        if os.path.exists(user_docs):
            return user_docs
        
        # Fallback auf relatives Verzeichnis zu workspace
        rel_docs = os.path.abspath(os.path.join(self.workspace_path, "..", "UserMaps"))
        if os.path.exists(rel_docs):
            return rel_docs
        return user_docs

    @staticmethod
    def is_admin() -> bool:
        """Prüft, ob der aktuelle Prozess über Windows Administratorrechte verfügt."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def check_s6patcher_integrity(self) -> Tuple[str, List[Dict[str, any]]]:
        """
        Überprüft den Zustand der unverzichtbaren S6Patcher-Kerndateien.
        Rückgabe: (Status: 'OK'|'WARNING'|'ERROR', Liste der Dateistatus)
        """
        results = []
        missing_count = 0

        for rel_file in self.PROTECTED_S6PATCHER_FILES:
            full_path = os.path.join(self.modloader_path, rel_file)
            exists = os.path.isfile(full_path)
            size = os.path.getsize(full_path) if exists else 0
            
            if not exists:
                missing_count += 1

            results.append({
                "relative_path": rel_file,
                "full_path": full_path,
                "exists": exists,
                "size_bytes": size,
                "status": "OK" if exists else "FEHLT"
            })

        if missing_count == 0:
            status = "OK"
        elif missing_count < len(self.PROTECTED_S6PATCHER_FILES):
            status = "WARNING"
        else:
            status = "ERROR"

        return status, results

    def is_protected_file(self, rel_path: str) -> bool:
        """Prüft, ob eine relative Datei eine geschützte S6Patcher-Datei ist."""
        norm = os.path.normpath(rel_path).lower()
        for protected in self.PROTECTED_S6PATCHER_FILES:
            if norm == protected.lower():
                return True
        return False

    def list_active_modloader_files(self) -> List[Dict[str, any]]:
        """Listet alle aktuell im ModLoader vorhandenen Dateien auf."""
        files_list = []
        if not os.path.exists(self.modloader_path):
            return files_list

        for root, _, files in os.walk(self.modloader_path):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, self.modloader_path)
                size = os.path.getsize(full_path)
                try:
                    mtime_val = os.path.getmtime(full_path)
                    if mtime_val > 0:
                        mtime = datetime.fromtimestamp(mtime_val).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        mtime = "Unbekannt"
                except Exception:
                    mtime = "Unbekannt"
                is_prot = self.is_protected_file(rel_path)

                files_list.append({
                    "relative_path": rel_path,
                    "full_path": full_path,
                    "size_bytes": size,
                    "size_str": f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B",
                    "modified": mtime,
                    "is_protected": is_prot,
                    "category": "S6Patcher System" if is_prot else self._categorize_file(rel_path)
                })

        return sorted(files_list, key=lambda x: (x["is_protected"], x["category"], x["relative_path"]))

    def _categorize_file(self, rel_path: str) -> str:
        """Kategorisiert eine Datei nach Verwendungszweck."""
        p = rel_path.lower()
        if "config" in p:
            return "Konfiguration / XML"
        if "maps" in p:
            return "Karten / Szenarien"
        if "text" in p:
            return "Lokalisierung & Texte"
        if "graphics" in p or "effects" in p:
            return "Grafik & Effekte"
        if "sound" in p:
            return "Audio & Musik"
        return "Sonstige Mod-Dateien"

    def create_modloader_backup(self, backup_name: Optional[str] = None) -> str:
        """Erstellt ein ZIP-Backup des gesamten modloader/shr/mod-Verzeichnisses."""
        if not os.path.exists(self.modloader_path):
            raise FileNotFoundError(f"ModLoader-Pfad nicht gefunden: {self.modloader_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = backup_name or f"ModLoader_Backup_{timestamp}"
        zip_path = os.path.join(self.backups_path, f"{name}.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(self.modloader_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.modloader_path)
                    zipf.write(full_path, rel_path)

        return zip_path

    def restore_modloader_backup(self, zip_path: str, preserve_protected: bool = True) -> int:
        """Stellt den Inhalt eines ModLoader-Backups wieder her."""
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Backup-Datei nicht gefunden: {zip_path}")

        # Temporär entpacken und kopieren
        restored_count = 0
        with zipfile.ZipFile(zip_path, "r") as zipf:
            for member in zipf.infolist():
                rel_path = os.path.normpath(member.filename)
                if preserve_protected and self.is_protected_file(rel_path):
                    continue
                
                target_file = os.path.join(self.modloader_path, rel_path)
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                with zipf.open(member) as src, open(target_file, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                restored_count += 1

        return restored_count

    def list_backups(self) -> List[Dict[str, any]]:
        """Listet alle vorhandenen Backups auf."""
        backups = []
        if not os.path.exists(self.backups_path):
            return backups

        for f in os.listdir(self.backups_path):
            if f.endswith(".zip"):
                p = os.path.join(self.backups_path, f)
                try:
                    mtime_val = os.path.getmtime(p)
                    if mtime_val > 0:
                        mtime = datetime.fromtimestamp(mtime_val).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        mtime = "Unbekannt"
                except Exception:
                    mtime = "Unbekannt"
                backups.append({
                    "filename": f,
                    "full_path": p,
                    "size_bytes": size,
                    "size_str": f"{size / (1024 * 1024):.2f} MB" if size >= 1048576 else f"{size / 1024:.1f} KB",
                    "created": mtime
                })
        return sorted(backups, key=lambda x: x["created"], reverse=True)

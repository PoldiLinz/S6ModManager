"""
Siedler 6 Mod Manager - System Engine
Verwaltet Pfade, UAC-Rechte, S6Patcher-Schutzdateien und ModLoader-Dateistatus.
"""

import os
import sys
import json
import ctypes
import shutil
import zipfile
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class SystemEngine:
    """Verwaltet Spielpfade, UAC-Berechtigungen, S6Patcher-Integrität und Backups."""

    PROTECTED_S6PATCHER_FILES = [
        os.path.normpath("config/models.xml"),
        os.path.normpath("config/modelsex.xml"),
        os.path.normpath("config/entities/u_knightredprince.xml"),
        os.path.normpath("config/entities/u_knightsabatta.xml"),
        os.path.normpath("config/entities/b_npc_barracks_me.xml"),
        os.path.normpath("config/sound/playlisteventfestival.xml"),
        os.path.normpath("graphics/effects/road.fx"),
        os.path.normpath("script/mainmenu/mainmenudev.lua"),
    ]

    DEFAULT_GAME_PATH = r"C:\Program Files (x86)\Ubisoft\DIE SIEDLER - Aufstieg eines Königreichs"

    def __init__(
        self,
        workspace_path: Optional[str] = None,
        game_path: Optional[str] = None,
        documents_path: Optional[str] = None
    ):
        self._custom_workspace = workspace_path is not None
        self._custom_game = game_path is not None
        self._custom_docs = documents_path is not None

        self.documents_path = os.path.abspath(documents_path) if documents_path else self._detect_settlers_docs_path()

        # Workspace ist standardmäßig UserMods im Dokumenten-Ordner, es sei denn ein Pfad wurde explizit übergeben
        if workspace_path:
            self.workspace_path = os.path.abspath(workspace_path)
        else:
            self.workspace_path = os.path.abspath(
                os.path.join(self.documents_path, "UserMods")
            )

        self.game_path = os.path.abspath(game_path) if game_path else self._detect_game_path()

        self.language = "en"
        self.window_width = 1120
        self.window_height = 820
        self.preferred_launch_mode = None

        # Alle abgeleiteten Pfade initialisieren
        self._derive_paths()

        # Einstellungen aus settings.json laden (überschreibt ggf. Pfade & Sprache)
        self.load_settings()

        # Verzeichnisse anlegen falls nötig
        self.ensure_workspace_directories()

    def _derive_paths(self):
        """Leitet alle internen Pfade sauber aus game_path, documents_path und workspace_path ab."""
        if not hasattr(self, "modloader_root_path") or not self.modloader_root_path:
            self.modloader_root_path = os.path.join(self.game_path, "modloader")
        self.modloader_path = os.path.join(self.modloader_root_path, "shr", "mod")
        self.original_mods_path = os.path.join(self.workspace_path, "Original Mod Files")
        self.base_game_files_path = os.path.join(self.workspace_path, "Original Game Files", "base", "bba")
        self.user_maps_path = os.path.join(self.documents_path, "UserMaps")
        self.user_script_path = os.path.join(self.documents_path, "Script")
        try:
            from ModManager.utils import get_base_path
        except ImportError:
            from utils import get_base_path
        app_dir = get_base_path()
        bundled_presets = os.path.join(app_dir, "Presets")
        self.presets_path = bundled_presets if os.path.exists(bundled_presets) else os.path.join(self.workspace_path, "Presets")
        bundled_scenarios = os.path.join(app_dir, "Scenarios")
        self.scenarios_path = bundled_scenarios if os.path.exists(bundled_scenarios) else os.path.join(self.workspace_path, "Scenarios")
        self.backups_path = os.path.join(self.workspace_path, "Backups")

    def get_bundled_s6packer_path(self) -> str:
        """Gibt den Pfad zum gebündelten S6Packer.exe zurück (prüft mehrere mögliche Speicherorte)."""
        try:
            from ModManager.utils import get_base_path
        except ImportError:
            from utils import get_base_path
        base_dir = get_base_path()
        candidates = [
            os.path.abspath(os.path.join(base_dir, "tools", "S6Packer.exe")),
            os.path.abspath(os.path.join(base_dir, "tools", "S6Packer", "S6Packer.exe")),
            os.path.abspath(os.path.join(self.workspace_path, "tools", "S6Packer", "S6Packer.exe")),
            os.path.abspath(os.path.join(self.workspace_path, "tools", "S6Packer.exe")),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return candidates[0]

    def ensure_workspace_directories(self):
        """Stellt sicher, dass alle benötigten Workspace-Ordner und Modloader-Verzeichnisse existieren."""
        for p in [
            self.workspace_path,
            self.backups_path,
            self.original_mods_path,
            self.base_game_files_path,
            self.user_maps_path,
            self.user_script_path,
            self.presets_path,
            self.scenarios_path,
            self.modloader_root_path,
            self.modloader_path,
            os.path.join(self.modloader_root_path, "base"),
            os.path.join(self.modloader_root_path, "extra1")
        ]:
            try:
                os.makedirs(p, exist_ok=True)
            except Exception:
                pass

    def get_settings_path(self) -> str:
        """Gibt den Pfad zur settings.json im Workspace zurück."""
        return os.path.join(self.workspace_path, "settings.json")

    def load_settings(self):
        """Lädt benutzerdefinierte Pfade und Einstellungen aus settings.json falls vorhanden."""
        from ModManager.engines.i18n_engine import I18nEngine
        settings_file = self.get_settings_path()
        # Fallback auf lokales Verzeichnis nur zur einmaligen Migration alter Installationen
        if not os.path.exists(settings_file) and not self._custom_workspace and not self._custom_docs:
            try:
                from ModManager.utils import get_base_path
            except ImportError:
                from utils import get_base_path
            alt_settings = os.path.abspath(os.path.join(os.path.dirname(get_base_path()), "settings.json"))
            if os.path.exists(alt_settings):
                settings_file = alt_settings

        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not self._custom_game and "game_path" in data and data["game_path"]:
                        self.game_path = os.path.normpath(data["game_path"])
                    if "modloader_root_path" in data and data["modloader_root_path"]:
                        self.modloader_root_path = os.path.normpath(data["modloader_root_path"])
                    elif "modloader_path" in data and data["modloader_path"]:
                        mlp = os.path.normpath(data["modloader_path"])
                        if mlp.lower().endswith(os.path.normpath("shr/mod").lower()):
                            self.modloader_root_path = os.path.dirname(os.path.dirname(mlp))
                        else:
                            self.modloader_root_path = mlp
                    if not self._custom_docs and "documents_path" in data and data["documents_path"]:
                        self.documents_path = os.path.normpath(data["documents_path"])
                    if not self._custom_workspace and "workspace_path" in data and data["workspace_path"]:
                        self.workspace_path = os.path.normpath(data["workspace_path"])

                    # Pfade mit neuen Werten aktualisieren
                    self._derive_paths()

                    if "preferred_launch_mode" in data:
                        self.preferred_launch_mode = data["preferred_launch_mode"]
                    if "language" in data and data["language"]:
                        self.language = data["language"]
                    if "window_width" in data:
                        self.window_width = data["window_width"]
                    if "window_height" in data:
                        self.window_height = data["window_height"]
            except Exception:
                pass
        I18nEngine.get_instance().set_language(self.language)

    def save_settings(self, settings_data: Dict[str, Any]):
        """Speichert benutzerdefinierte Einstellungen und Pfade in settings.json."""
        from ModManager.engines.i18n_engine import I18nEngine
        os.makedirs(self.workspace_path, exist_ok=True)
        settings_file = self.get_settings_path()
        try:
            data = {}
            if os.path.exists(settings_file):
                try:
                    with open(settings_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}

            path_keys = {"game_path", "documents_path", "workspace_path", "modloader_path", "modloader_root_path", "original_mods_path", "base_game_files_path", "user_maps_path", "user_script_path", "presets_path"}
            for k, v in settings_data.items():
                if k in path_keys:
                    if v:
                        norm_v = os.path.normpath(v)
                        data[k] = norm_v
                        if k == "modloader_path" or k == "modloader_root_path":
                            if norm_v.lower().endswith(os.path.normpath("shr/mod").lower()):
                                self.modloader_root_path = os.path.dirname(os.path.dirname(norm_v))
                            else:
                                self.modloader_root_path = norm_v
                            self.modloader_path = os.path.join(self.modloader_root_path, "shr", "mod")
                        else:
                            setattr(self, k, norm_v)
                else:
                    data[k] = v

            # Bei Änderungen an Hauptpfaden alle abgeleiteten Pfade synchronisieren
            self._derive_paths()
            self.ensure_workspace_directories()

            if "language" in settings_data:
                self.language = settings_data["language"]
                I18nEngine.get_instance().set_language(self.language)

            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise IOError(f"Konnte Einstellungen nicht speichern: {e}")

    @staticmethod
    def _is_valid_game_dir(path: str) -> bool:
        """Prüft, ob in dem Verzeichnis die Siedler 6 Spieldateien liegen."""
        if not path or not os.path.isdir(path):
            return False
        indicators = [
            os.path.join(path, "bin", "Settlers6.exe"),
            os.path.join(path, "bin", "Settlers6_extra1.exe"),
            os.path.join(path, "base", "bin", "Settlers6.exe"),
            os.path.join(path, "base", "bba", "shrgcfg0.bba"),
            os.path.join(path, "base", "bba", "shrgdata0.bba"),
        ]
        return any(os.path.exists(p) for p in indicators)

    @classmethod
    def _search_registry_game_path(cls) -> Optional[str]:
        """Sucht in der Windows Registry nach dem Installationspfad von Siedler 6."""
        if sys.platform != "win32":
            return None
        try:
            import winreg
        except ImportError:
            return None

        reg_roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        for root_key, sub_key in reg_roots:
            try:
                with winreg.OpenKey(root_key, sub_key) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as app_key:
                                try:
                                    display_name = winreg.QueryValueEx(app_key, "DisplayName")[0]
                                except OSError:
                                    display_name = ""

                                dn_lower = display_name.lower()
                                if any(token in dn_lower for token in ["siedler", "settlers"]):
                                    if any(sub in dn_lower for sub in ["aufstieg", "rise of an empire", "history", "6"]):
                                        for loc_val in ["InstallLocation", "InstallSource"]:
                                            try:
                                                path_val, _ = winreg.QueryValueEx(app_key, loc_val)
                                                if path_val and os.path.isdir(path_val):
                                                    norm = os.path.normpath(path_val)
                                                    if cls._is_valid_game_dir(norm):
                                                        return norm
                                            except OSError:
                                                pass
                        except OSError:
                            continue
            except OSError:
                continue

        ubi_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Ubisoft\Launcher\Installs"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Ubisoft\Launcher\Installs"),
        ]
        for root_key, sub_key in ubi_keys:
            try:
                with winreg.OpenKey(root_key, sub_key) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as app_key:
                                try:
                                    inst_dir, _ = winreg.QueryValueEx(app_key, "InstallDir")
                                    if inst_dir and os.path.isdir(inst_dir):
                                        norm = os.path.normpath(inst_dir)
                                        if cls._is_valid_game_dir(norm):
                                            return norm
                                except OSError:
                                    pass
                        except OSError:
                            continue
            except OSError:
                continue

        return None

    @classmethod
    def _detect_game_path(cls) -> str:
        """Sucht intelligent nach dem Spielverzeichnis (Registry, Standardpfade, Laufwerke)."""
        reg_path = cls._search_registry_game_path()
        if reg_path:
            return reg_path

        candidates = [
            cls.DEFAULT_GAME_PATH,
            r"C:\Program Files\Ubisoft\DIE SIEDLER - Aufstieg eines Königreichs",
            r"C:\Program Files (x86)\Ubisoft\The Settlers - Rise of an Empire",
            r"C:\Program Files\Ubisoft\The Settlers - Rise of an Empire",
            r"C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\games\The Settlers - Rise of an Empire - History Edition",
            r"C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\games\THE SETTLERS - RISE OF AN EMPIRE - History Edition",
            r"C:\Program Files (x86)\Steam\steamapps\common\The Settlers 6",
            r"C:\Program Files (x86)\GOG Galaxy\Games\The Settlers - Rise of an Empire",
            r"C:\GOG Games\The Settlers - Rise of an Empire",
            r"D:\Ubisoft\DIE SIEDLER - Aufstieg eines Königreichs",
            r"D:\Games\The Settlers - Rise of an Empire",
            r"D:\Spiele\DIE SIEDLER - Aufstieg eines Königreichs",
            r"E:\Ubisoft\DIE SIEDLER - Aufstieg eines Königreichs",
            r"E:\Games\The Settlers - Rise of an Empire",
        ]

        valid_scored = []
        for cand in candidates:
            if cls._is_valid_game_dir(cand):
                score = 1
                if os.path.exists(os.path.join(cand, "modloader", "base", "mod.bba")) or \
                   os.path.exists(os.path.join(cand, "modloader", "shr", "mod")):
                    score += 10
                valid_scored.append((score, cand))

        if valid_scored:
            valid_scored.sort(key=lambda x: x[0], reverse=True)
            return valid_scored[0][1]

        return cls.DEFAULT_GAME_PATH

    @staticmethod
    def _detect_documents_path() -> str:
        """Ermittelt den Windows 'Eigene Dokumente' Pfad zuverlässig."""
        docs = os.path.join(os.path.expanduser("~"), "Documents")
        if sys.platform == "win32":
            try:
                import ctypes.wintypes
                buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)
                if buf.value and os.path.isdir(buf.value):
                    docs = buf.value
            except Exception:
                pass
        return docs

    @classmethod
    def _detect_settlers_docs_path(cls) -> str:
        """Ermittelt das Siedler 6 Benutzerverzeichnis im Dokumenten-Ordner."""
        base_docs = cls._detect_documents_path()
        candidates = [
            os.path.join(base_docs, "DIE SIEDLER - Aufstieg eines Königreichs"),
            os.path.join(base_docs, "The Settlers - Rise of an Empire"),
        ]
        for c in candidates:
            if os.path.isdir(c):
                return c
        return candidates[0]

    def has_modloader(self) -> bool:
        """Prüft, ob der Community Modloader im Spielverzeichnis vorhanden ist."""
        return self.get_modloader_bba_path() is not None

    def get_modloader_bba_path(self) -> Optional[str]:
        """Gibt den Pfad zur mod.bba des Modloaders zurück, falls vorhanden."""
        candidates = [
            os.path.join(self.modloader_root_path, "base", "mod.bba"),
            os.path.join(self.modloader_root_path, "shr", "mod.bba"),
            os.path.join(self.modloader_root_path, "extra1", "mod.bba"),
            os.path.join(self.game_path, "modloader", "base", "mod.bba"),
            os.path.join(self.game_path, "modloader", "shr", "mod.bba"),
            os.path.join(self.game_path, "modloader", "extra1", "mod.bba"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

    def get_base_shrgcfg0_bba_path(self) -> Optional[str]:
        """Gibt den Pfad zur Vanilla shrgcfg0.bba im Spielverzeichnis zurück."""
        p = os.path.join(self.game_path, "base", "bba", "shrgcfg0.bba")
        return p if os.path.isfile(p) else None

    @staticmethod
    def is_admin() -> bool:
        """Prüft, ob der aktuelle Prozess über Windows Administratorrechte verfügt."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def check_s6patcher_integrity(self) -> Tuple[str, List[Dict[str, Any]]]:
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

    def list_active_modloader_files(self) -> List[Dict[str, Any]]:
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

        return sorted(files_list, key=lambda x: (not x["is_protected"], x["category"], x["relative_path"]))

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

    def list_backups(self) -> List[Dict[str, Any]]:
        """Listet alle vorhandenen Backups auf."""
        backups = []
        if not os.path.exists(self.backups_path):
            return backups

        for f in os.listdir(self.backups_path):
            if f.endswith(".zip"):
                p = os.path.join(self.backups_path, f)
                try:
                    size = os.path.getsize(p)
                except Exception:
                    size = 0
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

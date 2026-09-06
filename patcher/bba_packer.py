import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class BBAPacker:
    def __init__(self, user_mods_dir: str):
        self.user_mods_dir = Path(user_mods_dir).resolve()
        self.patcher_dir = self.user_mods_dir / "ModManager" / "patcher"
        self.processing_dir = self.user_mods_dir / "ModManager" / "processing"
        
        # Strikte Trennung von Pack- und Unpack-Verzeichnissen
        self.pack_dir = self.processing_dir / "pack"
        self.unpack_dir = self.processing_dir / "unpack"
        
        # Sicherungsordner für Mod-Stand-Backups
        self.bba_backups_dir = self.user_mods_dir / "Backups" / "bba"
        
        self.tools_dir = self.user_mods_dir / "tools" / "S6Packer"
        self.s6packer_exe = self.tools_dir / "S6Packer.exe"
        
        self.original_mod_files_dir = self.user_mods_dir / "Original Mod Files"
        self.original_mod_dir = self.original_mod_files_dir / "mod"

    def prepare_pack_staging(self):
        """
        Leert processing/pack/ vollständig vor jedem neuen Packvorgang,
        um jegliche Vermischung alter Stände auszuschließen.
        Kopiert anschließend die Original-Mod-Dateien (Bugfixes) hinein.
        """
        if self.pack_dir.exists():
            try:
                shutil.rmtree(self.pack_dir)
            except Exception as e:
                print(f"[Warning] Failed to fully clear pack dir: {e}")
                time.sleep(0.3)
                if self.pack_dir.exists():
                    shutil.rmtree(self.pack_dir, ignore_errors=True)
                    
        self.pack_dir.mkdir(parents=True, exist_ok=True)

        # Bugfix-Dateien als Basis nach processing/pack/ kopieren
        if self.original_mod_dir.exists():
            shutil.copytree(self.original_mod_dir, self.pack_dir, dirs_exist_ok=True)
            
    def prepare_staging_dir(self):
        """Alias für Abwärtskompatibilität."""
        return self.prepare_pack_staging()

    def pack(self) -> Path:
        """
        Packt den Inhalt von processing/pack/ mit S6Packer.exe.
        Erzeugt processing/pack.bba im übergeordneten processing/-Ordner.
        """
        if not self.s6packer_exe.exists():
            raise FileNotFoundError(f"S6Packer.exe not found at {self.s6packer_exe}. Please download it.")

        # S6Packer erzeugt <Ordnername>.bba im übergeordneten Ordner (also processing/pack.bba)
        expected_output = self.processing_dir / "pack.bba"

        if expected_output.exists():
            expected_output.unlink()

        print(f"[BBAPacker] Packing {self.pack_dir} into .bba...")
        proc = subprocess.Popen(
            [str(self.s6packer_exe), str(self.pack_dir), "--Type: .bba"],
        )

        # Poll auf die fertige .bba Datei (S6Packer schreibt sie vor ReadKey)
        max_wait = 60  # Sekunden
        elapsed = 0.0
        while elapsed < max_wait:
            if expected_output.exists():
                time.sleep(1.0)
                break
            time.sleep(0.5)
            elapsed += 0.5

        if proc.poll() is None:
            proc.kill()
            proc.wait()

        if not expected_output.exists():
            raise RuntimeError(f"S6Packer failed to generate the archive at {expected_output}")
            
        print(f"[BBAPacker] Archive created: {expected_output}")
        return expected_output

    def save_bba_backup(self, bba_path: Path) -> Path:
        """
        Sichert den neu erzeugten Mod-Stand als Backup mit Zeitstempel in Backups/bba/.
        Wird ausschließlich nach erfolgreichem Packen aufgerufen.
        """
        self.bba_backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.bba_backups_dir / f"mod_{timestamp}.bba"
        
        shutil.copy2(bba_path, backup_file)
        print(f"[BBAPacker] Mod-Stand Backup gesichert: {backup_file.name}")
        
        # Ältere Backups auf max. 25 begrenzen, um Speicherplatz zu schonen
        try:
            backups = sorted(self.bba_backups_dir.glob("mod_*.bba"), key=os.path.getmtime, reverse=True)
            for old_bba in backups[25:]:
                old_bba.unlink(missing_ok=True)
        except Exception as e:
            print(f"[Warning] Failed to prune old bba backups: {e}")

        return backup_file

    def list_bba_backups(self) -> List[Dict[str, Any]]:
        """Listet alle vorhandenen Mod-Stand-Backups absteigend nach Erstelldatum auf."""
        if not self.bba_backups_dir.exists():
            return []
        res = []
        for f in sorted(self.bba_backups_dir.glob("*.bba"), key=os.path.getmtime, reverse=True):
            try:
                mtime_val = os.path.getmtime(f)
                created_str = datetime.fromtimestamp(mtime_val).strftime("%Y-%m-%d %H:%M:%S")
                size = os.path.getsize(f)
                size_str = f"{size / 1024:.1f} KB" if size < 1048576 else f"{size / 1048576:.2f} MB"
                res.append({
                    "filename": f.name,
                    "path": str(f),
                    "created": created_str,
                    "timestamp": mtime_val,
                    "size_str": size_str,
                    "size_bytes": size,
                })
            except Exception:
                pass
        return res

    def deploy_and_cleanup(self, bba_path: Path, base_game_dir: str):
        """
        1. Sichert ein Snapshot-Backup des neuen Mod-Stands in Backups/bba/.
        2. Verteilt die .bba als mod.bba nach modloader/base/, modloader/extra1/ und modloader/shr/.
        3. Räumt processing/pack/ und die temporäre pack.bba restlos auf.
        """
        # 1. Backup erstellen
        self.save_bba_backup(bba_path)

        # 2. In die ModLoader-Verzeichnisse des Spiels kopieren
        modloader_dir = Path(base_game_dir) / "modloader"
        base_bba = modloader_dir / "base" / "mod.bba"
        extra1_bba = modloader_dir / "extra1" / "mod.bba"
        shr_bba = modloader_dir / "shr" / "mod.bba"
        
        print(f"[BBAPacker] Deploying to {base_bba}")
        base_bba.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bba_path, base_bba)
        
        print(f"[BBAPacker] Deploying to {extra1_bba}")
        extra1_bba.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bba_path, extra1_bba)

        print(f"[BBAPacker] Deploying to {shr_bba}")
        shr_bba.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bba_path, shr_bba)
        
        # 3. Aufräumen von pack.bba und processing/pack/
        print("[BBAPacker] Cleaning up pack staging...")
        try:
            if bba_path.exists():
                bba_path.unlink()
            if self.pack_dir.exists():
                shutil.rmtree(self.pack_dir, ignore_errors=True)
        except Exception as e:
            print(f"[Warning] Failed to clean up pack dir: {e}")

    def pack_and_deploy(self, base_game_dir: str):
        """Hilfsmethode: Packt processing/pack/ und deployt das Archiv."""
        bba_path = self.pack()
        self.deploy_and_cleanup(bba_path, base_game_dir)

    def unpack_archive(self, bba_path: Path) -> Path:
        """
        Entpackt ein .bba Archiv isoliert in processing/unpack/.
        Löscht vorher processing/unpack/ vollständig, um Altbestände zu verhindern.
        Gibt den Pfad zum entpackten Ordner (z. B. processing/unpack/mod_Extracted) zurück.
        """
        if not self.s6packer_exe.exists():
            raise FileNotFoundError(f"S6Packer.exe not found at {self.s6packer_exe}.")

        if not bba_path.exists():
            raise FileNotFoundError(f"Archive not found: {bba_path}")

        # Vor jedem Entpacken: processing/unpack/ restlos leeren
        if self.unpack_dir.exists():
            shutil.rmtree(self.unpack_dir, ignore_errors=True)
            time.sleep(0.1)
        self.unpack_dir.mkdir(parents=True, exist_ok=True)

        # Zu entpackende BBA isoliert in unpack_dir kopieren
        temp_bba = self.unpack_dir / bba_path.name
        shutil.copy2(bba_path, temp_bba)

        print(f"[BBAPacker] Unpacking {bba_path.name} in clean directory {self.unpack_dir}...")

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE

        proc = subprocess.Popen(
            [str(self.s6packer_exe), str(temp_bba)],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            startupinfo=startupinfo,
        )

        expected_folder_extracted = self.unpack_dir / f"{bba_path.stem}_Extracted"
        expected_folder_stem = self.unpack_dir / bba_path.stem

        max_wait = 20  # Sekunden
        elapsed = 0.0
        last_count = -1
        stable_iterations = 0
        actual_folder = None
        
        while elapsed < max_wait:
            if expected_folder_extracted.exists():
                actual_folder = expected_folder_extracted
            elif expected_folder_stem.exists():
                actual_folder = expected_folder_stem
                
            if actual_folder:
                count = sum(1 for _ in actual_folder.rglob('*'))
                if count > 0 and count == last_count:
                    stable_iterations += 1
                    # Wenn sich die Dateianzahl 1 Sekunde lang nicht ändert, ist er fertig
                    if stable_iterations >= 2:
                        break
                else:
                    stable_iterations = 0
                    last_count = count
                    
            time.sleep(0.5)
            elapsed += 0.5

        if proc.poll() is None:
            proc.kill()
            proc.wait()

        if not actual_folder or not actual_folder.exists():
            raise RuntimeError(f"S6Packer failed to unpack the archive {bba_path}")

        print(f"[BBAPacker] Unpacked successfully to {actual_folder}")
        return actual_folder

    def cleanup_unpack(self):
        """Löscht processing/unpack/ restlos nach dem Auslesen."""
        if self.unpack_dir.exists():
            shutil.rmtree(self.unpack_dir, ignore_errors=True)

    def unpack(self, bba_path: Path, output_dir: Path):
        """Abwärtskompatibler Wrapper: Entpackt und verschiebt das Ergebnis nach output_dir."""
        extracted = self.unpack_archive(bba_path)
        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
        shutil.move(str(extracted), str(output_dir))
        self.cleanup_unpack()

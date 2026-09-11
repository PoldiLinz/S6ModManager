import os
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ModManager.engines.system_engine import SystemEngine
from ModManager.engines.i18n_engine import t
from ModManager.patcher.bba_packer import BBAPacker


class SetupWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, system_engine: SystemEngine):
        super().__init__()
        self.system = system_engine

    def run(self):
        try:
            packer = BBAPacker(self.system.workspace_path)
            
            # 1. ModLoader mod.bba prüfen und entpacken falls vorhanden
            mod_bba_path = self.system.get_modloader_bba_path()
            out_mod = Path(self.system.original_mods_path) / "mod"
            
            if mod_bba_path and os.path.isfile(mod_bba_path):
                self.progress.emit(15, t("setup.extracting_mod", default="Entpacke Original Mod Files..."))
                if not out_mod.exists():
                    packer.unpack(Path(mod_bba_path), out_mod)
                # Kopie von mod.bba für spätere Restores sichern
                original_bba_dest = Path(self.system.original_mods_path) / "mod.bba"
                if not original_bba_dest.exists():
                    try:
                        shutil.copy2(mod_bba_path, original_bba_dest)
                    except Exception:
                        pass
            else:
                out_mod.mkdir(parents=True, exist_ok=True)
                self.progress.emit(25, t("setup.modloader_missing_notice", default="ModLoader nicht vorhanden - verwende Basis-Spieldateien..."))
                
            # 1b. Script Ordner sichern falls vorhanden
            user_script_src = Path(self.system.user_script_path)
            original_script_dest = Path(self.system.original_mods_path) / "Script"
            if user_script_src.exists() and user_script_src.is_dir():
                if not original_script_dest.exists():
                    try:
                        shutil.copytree(user_script_src, original_script_dest, dirs_exist_ok=True)
                    except Exception:
                        pass

            # 2. Basis-Konfigurationsdatei (shrgcfg0.bba) entpacken
            self.progress.emit(50, t("setup.extracting_game_files", default="Entpacke Basis-Spieldateien..."))
            
            base_bba_path = self.system.get_base_shrgcfg0_bba_path()
            if not base_bba_path or not os.path.isfile(base_bba_path):
                raise FileNotFoundError(f"Basis-Konfigurationsdatei (shrgcfg0.bba) nicht gefunden im Spielverzeichnis ({self.system.game_path})!")
                
            out_base_extracted = Path(self.system.base_game_files_path) / "shrgcfg0_Extracted"
            out_base_shrgcfg0 = Path(self.system.base_game_files_path) / "shrgcfg0"
            
            if not out_base_extracted.exists() and not out_base_shrgcfg0.exists():
                packer.unpack(Path(base_bba_path), out_base_extracted)
                
            # Sicherstellen, dass sowohl shrgcfg0_Extracted als auch shrgcfg0 existieren
            if out_base_extracted.exists() and not out_base_shrgcfg0.exists():
                try:
                    shutil.copytree(out_base_extracted, out_base_shrgcfg0, dirs_exist_ok=True)
                except Exception:
                    pass
            elif out_base_shrgcfg0.exists() and not out_base_extracted.exists():
                try:
                    shutil.copytree(out_base_shrgcfg0, out_base_extracted, dirs_exist_ok=True)
                except Exception:
                    pass
                
            self.progress.emit(100, t("setup.finished", default="Einrichtung abgeschlossen!"))
            self.finished.emit(True, "")
            
        except Exception as e:
            self.finished.emit(False, str(e))


class StartupSetupDialog(QDialog):
    def __init__(self, system_engine: SystemEngine, parent=None):
        super().__init__(parent)
        self.system = system_engine
        self.setWindowTitle(t("setup.title", default="Siedler 6 ModManager - Erstkonfiguration"))
        self.setFixedSize(500, 250)
        
        # Sicherstellen, dass der Dialog keinen Close-Button oben rechts hat, damit der Nutzer nicht abbricht ohne Entscheidung
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        lbl_title = QLabel(t("setup.dialog_heading", default="Automatische Arbeitsplatz-Einrichtung"))
        lbl_title.setObjectName("HeaderTitle")
        layout.addWidget(lbl_title)
        
        self.lbl_info = QLabel(
            t(
                "setup.consent_text",
                default=(
                    "Um den ModManager nutzen zu können, müssen kleine Konfigurationsdateien aus "
                    "deinem Spielverzeichnis in den Workspace (Dokumente/UserMods) entpackt werden "
                    "(Speicherbedarf: ca. 50 MB). Es werden keine großen Grafikdateien kopiert.\n\n"
                    "Möchtest du jetzt fortfahren?"
                )
            )
        )
        self.lbl_info.setWordWrap(True)
        layout.addWidget(self.lbl_info)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)
        
        self.lbl_status = QLabel("")
        self.lbl_status.hide()
        layout.addWidget(self.lbl_status)
        
        layout.addStretch()
        
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch()
        
        self.btn_ok = QPushButton(t("setup.btn_consent", default="OK, Einverstanden"))
        self.btn_ok.setObjectName("PrimaryButton")
        self.btn_ok.setMinimumWidth(150)
        self.btn_ok.clicked.connect(self.start_setup)
        self.btn_layout.addWidget(self.btn_ok)
        
        self.btn_cancel = QPushButton(t("setup.btn_cancel", default="Abbrechen"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(self.btn_layout)
        
    def start_setup(self):
        self.btn_ok.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.lbl_info.hide()
        
        self.progress.show()
        self.lbl_status.show()
        
        self.worker = SetupWorker(self.system)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.setup_finished)
        self.worker.start()
        
    def update_progress(self, val: int, text: str):
        self.progress.setValue(val)
        self.lbl_status.setText(text)
        
    def setup_finished(self, success: bool, error: str):
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Fehler", f"Ein Fehler ist bei der Einrichtung aufgetreten:\n\n{error}")
            self.reject()

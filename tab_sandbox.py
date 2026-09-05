"""
Siedler 6 Mod Manager - Tab 3: Testmap & Sandbox-Modifikator
Ermöglicht High-Tier-Testing durch temporäre Injektion von Cheats und Entwicklerfunktionen.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QCheckBox, QSpinBox, QFrame,
    QGroupBox, QPlainTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, List, Any, Optional

from ModManager.engines.sandbox_engine import SandboxEngine
from ModManager.engines.system_engine import SystemEngine
from ModManager.engines import t


class SandboxTab(QWidget):
    """Registerkarte für Testmap-Injektion und Sandbox-Cheats."""

    status_message = pyqtSignal(str, str)

    def __init__(self, sandbox_engine: SandboxEngine, system_engine: SystemEngine, parent=None):
        super().__init__(parent)
        self.sandbox = sandbox_engine
        self.system = system_engine
        self.current_maps: List[Dict[str, Any]] = []

        self._init_ui()
        self.refresh_maps()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # 1. Zielkarten-Auswahl
        card_map = QFrame()
        card_map.setObjectName("CardFrame")
        l_map = QVBoxLayout(card_map)

        l_map.addWidget(QLabel(t("sandbox_tab.lbl_select_map")))

        h_pick = QHBoxLayout()
        self.combo_maps = QComboBox()
        self.combo_maps.currentIndexChanged.connect(self._on_map_changed)
        h_pick.addWidget(self.combo_maps, 1)

        btn_refresh = QPushButton(t("sandbox_tab.btn_refresh"))
        btn_refresh.clicked.connect(self.refresh_maps)
        h_pick.addWidget(btn_refresh)

        l_map.addLayout(h_pick)

        self.lbl_inject_status = QLabel("")
        l_map.addWidget(self.lbl_inject_status)

        layout.addWidget(card_map)

        # 2. Sandbox-Optionen
        card_opts = QFrame()
        card_opts.setObjectName("CardFrame")
        l_opts = QVBoxLayout(card_opts)

        lbl_opts_title = QLabel(t("sandbox_tab.lbl_options"))
        lbl_opts_title.setObjectName("SectionHeader")
        l_opts.addWidget(lbl_opts_title)

        v_opts = QVBoxLayout()
        v_opts.setSpacing(10)

        self.chk_duke = QCheckBox(t("sandbox_tab.chk_duke"))
        self.chk_duke.setChecked(True)
        self.chk_duke.stateChanged.connect(self._update_lua_preview)
        v_opts.addWidget(self.chk_duke)

        self.chk_resources = QCheckBox(t("sandbox_tab.chk_resources"))
        self.chk_resources.setChecked(True)
        self.chk_resources.stateChanged.connect(self._update_lua_preview)
        v_opts.addWidget(self.chk_resources)

        h_amounts = QHBoxLayout()
        h_amounts.setContentsMargins(24, 0, 0, 0) # Indent spinboxes to sit nicely below the checkbox
        h_amounts.addWidget(QLabel(t("sandbox_tab.lbl_gold")))
        self.spin_gold = QSpinBox()
        self.spin_gold.setRange(1000, 500000)
        self.spin_gold.setValue(50000)
        self.spin_gold.setSingleStep(5000)
        self.spin_gold.valueChanged.connect(self._update_lua_preview)
        h_amounts.addWidget(self.spin_gold)

        h_amounts.addWidget(QLabel(t("sandbox_tab.lbl_resources")))
        self.spin_res = QSpinBox()
        self.spin_res.setRange(50, 5000)
        self.spin_res.setValue(500)
        self.spin_res.setSingleStep(50)
        self.spin_res.valueChanged.connect(self._update_lua_preview)
        h_amounts.addWidget(self.spin_res)
        h_amounts.addStretch()
        v_opts.addLayout(h_amounts)

        self.chk_storehouse = QCheckBox(t("sandbox_tab.chk_storehouse"))
        self.chk_storehouse.setChecked(True)
        self.chk_storehouse.stateChanged.connect(self._update_lua_preview)
        v_opts.addWidget(self.chk_storehouse)

        self.chk_fog = QCheckBox(t("sandbox_tab.chk_fog"))
        self.chk_fog.setChecked(True)
        self.chk_fog.stateChanged.connect(self._update_lua_preview)
        v_opts.addWidget(self.chk_fog)

        l_opts.addLayout(v_opts)
        layout.addWidget(card_opts)

        # 3. Lua Code Vorschau
        card_preview = QFrame()
        card_preview.setObjectName("SubCardFrame")
        l_prev = QVBoxLayout(card_preview)
        l_prev.addWidget(QLabel(t("sandbox_tab.lbl_preview")))

        self.txt_lua_preview = QPlainTextEdit()
        self.txt_lua_preview.setObjectName("LogConsole")
        self.txt_lua_preview.setReadOnly(True)
        self.txt_lua_preview.setMaximumHeight(140)
        l_prev.addWidget(self.txt_lua_preview)

        layout.addWidget(card_preview)

        # 4. Action Buttons
        h_actions = QHBoxLayout()

        self.btn_clean = QPushButton(t("sandbox_tab.btn_clean"))
        self.btn_clean.setObjectName("DangerButton")
        self.btn_clean.clicked.connect(self._on_remove_sandbox)
        h_actions.addWidget(self.btn_clean)

        h_actions.addStretch()

        self.btn_inject = QPushButton(t("sandbox_tab.btn_inject"))
        self.btn_inject.setObjectName("PrimaryButton")
        self.btn_inject.clicked.connect(self._on_inject_sandbox)
        h_actions.addWidget(self.btn_inject)

        layout.addLayout(h_actions)
        layout.addStretch()

        self._update_lua_preview()

    # -------------------------------------------------------------------------
    # Logik & Events
    # -------------------------------------------------------------------------

    def refresh_maps(self):
        self.combo_maps.clear()
        self.current_maps = self.sandbox.list_testable_maps()

        for m in self.current_maps:
            status_tag = t("sandbox_tab.injected_tag") if m["is_injected"] else ""
            self.combo_maps.addItem(f"{m['name']}{status_tag}", m)

        self._on_map_changed(self.combo_maps.currentIndex())

    def _on_map_changed(self, index: int):
        if index < 0 or index >= len(self.current_maps):
            self.lbl_inject_status.setText("")
            return

        map_info = self.current_maps[index]
        is_injected = self.sandbox.is_script_injected(map_info["script_path"])

        if is_injected:
            self.lbl_inject_status.setText(t("sandbox_tab.status_active"))
            self.lbl_inject_status.setObjectName("BadgeSuccess")
            self.btn_inject.setText(t("sandbox_tab.btn_update"))
        else:
            self.lbl_inject_status.setText(t("sandbox_tab.status_clean"))
            self.lbl_inject_status.setObjectName("BadgeWarning")
            self.btn_inject.setText(t("sandbox_tab.btn_inject"))

        self.lbl_inject_status.style().unpolish(self.lbl_inject_status)
        self.lbl_inject_status.style().polish(self.lbl_inject_status)

    def _collect_options(self) -> Dict[str, Any]:
        return {
            "upgrade_knight": self.chk_duke.isChecked(),
            "add_resources": self.chk_resources.isChecked(),
            "fill_storehouse": self.chk_storehouse.isChecked(),
            "reveal_fog": self.chk_fog.isChecked(),
            "gold_amount": self.spin_gold.value(),
            "resources_amount": self.spin_res.value()
        }

    def _update_lua_preview(self):
        opts = self._collect_options()
        code = self.sandbox.generate_lua_sandbox_code(opts)
        self.txt_lua_preview.setPlainText(code)

    def _on_inject_sandbox(self):
        idx = self.combo_maps.currentIndex()
        if idx < 0 or idx >= len(self.current_maps):
            return

        map_info = self.current_maps[idx]
        script_path = map_info["script_path"]
        opts = self._collect_options()

        try:
            self.sandbox.inject_sandbox_into_script(script_path, opts)
            msg = t("sandbox_tab.msg_inject_success").format(name=map_info['name'])
            self.status_message.emit(t("sandbox_tab.log_inject_success").format(name=map_info['name']), "success")
            QMessageBox.information(self, t("sandbox_tab.title_active"), msg)
            self.refresh_maps()
        except Exception as e:
            err = t("sandbox_tab.msg_inject_error").format(err=e)
            self.status_message.emit(err, "error")
            QMessageBox.critical(self, t("app.error") if t("app.error") != "app.error" else "Error", err)

    def _on_remove_sandbox(self):
        idx = self.combo_maps.currentIndex()
        if idx < 0 or idx >= len(self.current_maps):
            return

        map_info = self.current_maps[idx]
        script_path = map_info["script_path"]

        try:
            self.sandbox.remove_sandbox_from_script(script_path)
            msg = t("sandbox_tab.msg_remove_success").format(name=map_info['name'])
            self.status_message.emit(t("sandbox_tab.log_remove_success").format(name=map_info['name']), "warning")
            QMessageBox.information(self, t("sandbox_tab.title_clean"), msg)
            self.refresh_maps()
        except Exception as e:
            err = t("sandbox_tab.msg_remove_error").format(err=e)
            self.status_message.emit(err, "error")
            QMessageBox.critical(self, t("app.error") if t("app.error") != "app.error" else "Error", err)

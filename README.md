# 👑 The Settlers 6: Mod & Map Manager (S6Patcher Edition)

> **The Settlers 6 - Mod Manager**  
> Presented by **Leopold Walli AI Software Productions**  
> **Version 1.1** (Build `20260911`)  
>  
> *Notice:* This software was implemented with high quality standards, nevertheless it is vibe coded fully by AI only, therefore I fully understand the risks of using it. I can test and verify code correctness by using AI Tools myself. The author is not responsible for any software damage.

[![Language: English](https://img.shields.io/badge/Language-English-blue.svg)](README.md)
[![Language: Deutsch](https://img.shields.io/badge/Language-Deutsch-red.svg)](README.de.md)

**Language / Sprache:** [🇬🇧 English](README.md) | [🇩🇪 Deutsch](README.de.md)

A modern, standalone desktop manager built with **PyQt6** for *The Settlers: Rise of an Empire* (Die Siedler: Aufstieg eines Königreichs).  
Provides live game configuration (population limits, warehouses, castles, mines), scenario and map switching with multiple variants, and a high-tier sandbox injector for rapid development and testing.

---

## ✨ Key Features

### 1. ⚙️ Live Configuration Editor & Game Limits
* **Global Settler Limit (`logic.xml`):** Increase population cap from 200 (Vanilla) up to 500 – 5,000+ settlers per cathedral tier.
* **Warehouse & Castles (Tiers 1–4):** Fully customizable storage capacities (up to 5,000), increased soldier limits (up to 500), 99,000 gold treasury, and configurable upgrade costs (Gold & Stone).
* **Infinite Resource Mines:** 1-click option to set stone quarries and iron mines to inexhaustible capacity (999,999).
* **Military & Fortifications:** Configurable battalion sizes (6, 9, or 12 soldiers per squad), tripled hitpoints for gates, turrets, and city walls.
* **Preset Management:** Pre-configured profiles (`Vanilla`, `Extended`, `Extreme`) and ability to save custom tuning presets.

### 2. 🗺️ Maps & Scenario Variants Manager
* **Map Library:** Direct overview of supported single-player and campaign maps.
* **Variants & Sub-Scenarios:** Manage multiple modifications for the same map (e.g., *Vanilla* vs. *Hostile Fair Trade* with aggressive raid waves and grace period).
* **UserMap Import:** 1-click assignment of custom maps from `UserMaps` as replacements or variants of an original map.
* **Non-Destructive:** Restoring vanilla only removes ModLoader overrides, keeping original game archives untouched.

### 3. 🧪 Test Map & Sandbox Injector (High-Tier Testing)
* **Instant Duke Title (Tier 6):** Unlocks all building tiers and upgrades immediately upon game start.
* **Starting Capital & Resources:** Grants 50,000 gold and 500 units of every trade good.
* **Stocked Warehouse:** Instantly fills the starting storehouse with wood, stone, and iron.
* **Fog of War Reveal:** Completely reveals the entire map for testing and scouting.
* **Clean Rollback:** Automatically restores original map scripts upon deactivation.

### 4. 🛡️ System Status, S6Patcher Protection & Backups
* **Integrity Guard:** Protects essential S6Patcher core files from accidental deletion or corruption.
* **File Inspector:** Lists all active mod files currently injected into the ModLoader.
* **1-Click Backups:** Create and restore compressed ZIP snapshots of your ModLoader state anytime.

## 📋 Pre-Installation Requirements (Crucial!)

Before setting up and running the ModManager, make sure your game is updated and the ModLoader is activated:

1. **Patch The Settlers 6 to the Latest Version:**
   * Ensure your base game and the expansion (*The Settlers: Eastern Realm*) are updated to their latest official patches (e.g. Patch 1.7.1 for the base game / Patch 2.1 for the expansion).
2. **Launch the Game Once:**
   * Run *The Settlers 6* at least once to the main menu before installing any mods. This initializes the user documents directory (`Documents\THE SETTLERS - Rise of an Empire` or `Documents\DIE SIEDLER...`), local configuration, and registry paths.
3. **Run the Settlers 6 Modloader (S6Patcher):**
   * Run the official **S6Patcher** (Settlers 6 ModLoader).
   * Patch the game binaries and **activate mods** (this creates the `modloader\` directory in your game directory).
4. **Proceed with ModManager Setup:**
   * Once the ModLoader is present and active, continue with the ModManager setup below.

---

## 🚀 Installation & Quick Start (Standalone & Portable)

The Settlers 6 ModManager is designed as a **completely standalone and portable application**.

### Recommended Location:
Extract or copy the **`ModManager`** folder into your Settlers 6 mod directory:  
📁 `Documents\THE SETTLERS - Rise of an Empire\UserMods\ModManager`  
*(or `Documents\DIE SIEDLER - Aufstieg eines Königreichs\UserMods\ModManager` on German game editions)*  
*Note:* The tool can run from any folder (e.g. Desktop). Game backups and safe checkpoints are preserved under your Documents folder so your progress is never lost.

### 1. Setup & First-Time Installation
Run the installer script for automated dependency checks:
```cmd
INSTALL.bat
```
* **Automated:** Verifies Python and PyQt6, automatically installing any missing dependencies.
* **Setup Assistant:** Offers a bilingual interface (English / German), desktop shortcut generation, and optional local `.exe` compilation.

### 2. Launching the Manager
Simply double-click the launcher:
```cmd
START_MOD_MANAGER.bat
```
Or launch directly using Python:
```bash
python src/ModManager/main.py
```

---

## 📁 Project & Directory Structure

```text
ModManager/
├── INSTALL.bat                     # Setup assistant with UAC & auto-dependency check
├── START_MOD_MANAGER.bat           # 1-click launcher
├── README.md                       # English documentation
├── README.de.md                    # German documentation
├── LICENSE                         # Open-source license (MIT)
├── .gitignore                      # Git ignore rules (clean repository)
│
└── src/ModManager/                 # Application source code & resources
    ├── main.py                     # Main application entry point
    ├── app_window.py               # Main window with tab system & log console
    ├── setup_assistant.py          # Bilingual setup assistant dialog
    ├── utils.py                    # Path and runtime helper functions
    ├── tab_config.py               # Tab 1: Live Config Editor & Presets
    ├── tab_scenarios.py            # Tab 2: Scenario & Map Manager
    ├── tab_sandbox.py              # Tab 3: Sandbox Injector
    ├── tab_system.py               # Tab 4: System Status & Backup Manager
    ├── dialog_settings.py          # Settings dialog
    ├── dialog_startup_setup.py     # Initial workspace extraction dialog
    ├── engines/                    # Backend business logic
    │   ├── system_engine.py
    │   ├── config_engine.py
    │   ├── scenario_engine.py
    │   ├── sandbox_engine.py
    │   └── i18n_engine.py
    ├── patcher/                    # BBA packer & archive routines
    ├── locales/                    # Bilingual dictionary (dictionary.json)
    ├── styles/                     # Modern dark theme stylesheet (theme.qss)
    ├── assets/                     # Graphical assets & icons
    ├── tools/                      # Bundled utilities (e.g., S6Packer)
    ├── Presets/                    # Balancing profiles (Vanilla, Extended, Extreme)
    ├── Scenarios/                  # Scenario library & variant maps
    └── tests/                      # Automated test suite (34 tests)
```

---

## 🧪 Running Automated Tests

Run the full automated test suite using:
```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s "src\ModManager\tests" -p "test_*.py" -v
```

---

## 📜 License & Credits

**The Settlers 6 - Mod Manager**  
Presented by **Leopold Walli AI Software Productions**  
Version 1.1 (Build 20260911)

This project is open source and licensed under the [MIT License](LICENSE).

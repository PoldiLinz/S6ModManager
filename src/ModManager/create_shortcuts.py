"""
Erstellt Windows-Verknüpfungen (.lnk) mit Icon für den Siedler 6 Mod Manager.
"""

import os
import subprocess


def create_shortcuts():
    workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bat_path = os.path.join(workspace, "START_MOD_MANAGER.bat")
    ico_path = os.path.join(workspace, "ModManager", "assets", "icon.ico")

    # PowerShell-Script zur Verknüpfungserstellung
    ps_cmd = f"""
$WshShell = New-Object -ComObject WScript.Shell

# 1. Verknüpfung im UserMods Ordner
$p1 = '{workspace}\\Die Siedler 6 Mod Manager.lnk'
$s1 = $WshShell.CreateShortcut($p1)
$s1.TargetPath = '{bat_path}'
$s1.WorkingDirectory = '{workspace}'
$s1.IconLocation = '{ico_path}, 0'
$s1.Description = 'Die Siedler 6 - Mod und Map Manager'
$s1.Save()

# Administrator-Flag (SLDF_RUNAS_USER / Byte 0x15 |= 0x20) setzen
$b1 = [System.IO.File]::ReadAllBytes($p1)
$b1[0x15] = $b1[0x15] -bor 0x20
[System.IO.File]::WriteAllBytes($p1, $b1)
Write-Host "Verknüpfung erstellt (mit Admin-Flag): $p1"

# 2. Verknüpfung auf dem Desktop
$desktop = [Environment]::GetFolderPath('Desktop')
if (Test-Path $desktop) {{
    $p2 = "$desktop\\Die Siedler 6 Mod Manager.lnk"
    $s2 = $WshShell.CreateShortcut($p2)
    $s2.TargetPath = '{bat_path}'
    $s2.WorkingDirectory = '{workspace}'
    $s2.IconLocation = '{ico_path}, 0'
    $s2.Description = 'Die Siedler 6 - Mod und Map Manager'
    $s2.Save()

    $b2 = [System.IO.File]::ReadAllBytes($p2)
    $b2[0x15] = $b2[0x15] -bor 0x20
    [System.IO.File]::WriteAllBytes($p2, $b2)
    Write-Host "Desktop-Verknüpfung erstellt (mit Admin-Flag): $p2"
}}
"""

    res = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
    )
    print(res.stdout)
    if res.stderr:
        print("Meldung:", res.stderr)


if __name__ == "__main__":
    create_shortcuts()

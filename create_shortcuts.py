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
$s1 = $WshShell.CreateShortcut('{workspace}\\Die Siedler 6 Mod Manager.lnk')
$s1.TargetPath = '{bat_path}'
$s1.WorkingDirectory = '{workspace}'
$s1.IconLocation = '{ico_path}, 0'
$s1.Description = 'Die Siedler 6 - Mod & Map Manager'
$s1.Save()
Write-Host "Verknüpfung erstellt: {workspace}\\Die Siedler 6 Mod Manager.lnk"

# 2. Verknüpfung auf dem Desktop
$desktop = [Environment]::GetFolderPath('Desktop')
if (Test-Path $desktop) {{
    $s2 = $WshShell.CreateShortcut("$desktop\\Die Siedler 6 Mod Manager.lnk")
    $s2.TargetPath = '{bat_path}'
    $s2.WorkingDirectory = '{workspace}'
    $s2.IconLocation = '{ico_path}, 0'
    $s2.Description = 'Die Siedler 6 - Mod & Map Manager'
    $s2.Save()
    Write-Host "Desktop-Verknüpfung erstellt: $desktop\\Die Siedler 6 Mod Manager.lnk"
}}
"""

    res = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        capture_output=True,
        text=True,
    )
    print(res.stdout)
    if res.stderr:
        print("Meldung:", res.stderr)


if __name__ == "__main__":
    create_shortcuts()

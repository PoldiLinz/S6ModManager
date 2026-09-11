@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title The Settlers 6 - Mod and Map Manager
mode con: cols=100 lines=30

:: ============================================================================
:: 1. UAC Admin-Rechte pruefen und anfordern
:: ============================================================================
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ======================================================================
    echo   Administrator privileges required!
    echo   Requesting permission... Please confirm in Windows dialog.
    echo ======================================================================
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: ============================================================================
:: 2. Arbeitsverzeichnis und Log-Datei initialisieren
:: ============================================================================
cd /d "%~dp0"
set "LOGFILE=%~dp0launcher_debug.log"
echo ====================================================================== > "%LOGFILE%"
echo   Settlers 6 Mod Manager - Startprotokoll: %DATE% %TIME% >> "%LOGFILE%"
echo   Skriptpfad: %~f0 >> "%LOGFILE%"
echo ====================================================================== >> "%LOGFILE%"
echo [OK] Administrator privileges confirmed. >> "%LOGFILE%"
echo [OK] Working directory: %CD% >> "%LOGFILE%"

:: ============================================================================
:: 3. Python-Executable lokalisieren
:: ============================================================================
set "PYTHON_EXE="
if exist "C:\Program Files\Python314\python.exe" set "PYTHON_EXE=C:\Program Files\Python314\python.exe"
if not defined PYTHON_EXE if exist "C:\Program Files\Python313\python.exe" set "PYTHON_EXE=C:\Program Files\Python313\python.exe"
if not defined PYTHON_EXE if exist "C:\Program Files\Python312\python.exe" set "PYTHON_EXE=C:\Program Files\Python312\python.exe"
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not defined PYTHON_EXE (
    where py.exe >nul 2>&1
    if !errorlevel! equ 0 set "PYTHON_EXE=py.exe"
)
if not defined PYTHON_EXE (
    where python.exe >nul 2>&1
    if !errorlevel! equ 0 set "PYTHON_EXE=python.exe"
)

:: Fallback: Wenn Python fehlt, leite nahtlos zum Setup (INSTALL.bat) weiter
if not defined PYTHON_EXE (
    echo [INFO] Python not found. Redirecting to INSTALL.bat... >> "%LOGFILE%"
    echo ======================================================================
    echo   Python nicht gefunden. Starte Setup-Assistenten...
    echo ======================================================================
    call "%~dp0INSTALL.bat"
    exit /b !errorlevel!
)
echo [OK] Using Python: "!PYTHON_EXE!" >> "%LOGFILE%"

:: ============================================================================
:: 4. PyQt6 Verfuegbarkeit pruefen (Fallback zu INSTALL.bat bei Fehlen)
:: ============================================================================
"!PYTHON_EXE!" -c "import PyQt6" >nul 2>&1
if !errorlevel! neq 0 (
    echo [INFO] PyQt6 missing. Redirecting to INSTALL.bat... >> "%LOGFILE%"
    echo ======================================================================
    echo   Benoetigte Bibliothek PyQt6 fehlt. Starte Setup-Assistenten...
    echo ======================================================================
    call "%~dp0INSTALL.bat"
    exit /b !errorlevel!
)
echo [OK] PyQt6 verified. >> "%LOGFILE%"

:: ============================================================================
:: 5. ModManager direkt starten
:: ============================================================================
echo [INFO] Launching main.py... >> "%LOGFILE%"
echo ======================================================================
echo   THE SETTLERS 6 - MOD AND MAP MANAGER
echo   Status: Running
echo ======================================================================
echo.

"!PYTHON_EXE!" "%~dp0src\ModManager\main.py" 2>> "%LOGFILE%"
set "EXIT_CODE=!errorlevel!"

echo [INFO] ModManager exited with code: %EXIT_CODE% >> "%LOGFILE%"
if %EXIT_CODE% neq 0 (
    echo.
    echo ======================================================================
    echo   [FEHLER] ModManager wurde mit Fehlercode %EXIT_CODE% beendet.
    echo ======================================================================
    echo   Details siehe Logdatei: "%LOGFILE%"
    echo.
    type "%LOGFILE%"
    echo.
    pause
    exit /b %EXIT_CODE%
)

echo [OK] ModManager erfolgreich beendet. >> "%LOGFILE%"
exit /b 0

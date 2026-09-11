@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title The Settlers 6 - Mod and Map Manager - Setup Assistant
mode con: cols=100 lines=30

:: ============================================================================
:: 1. UAC Admin-Rechte pruefen und anfordern
::    WICHTIG: Log-Datei wird erst NACH der Elevation initialisiert,
::    damit keine Dateisperren entstehen.
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
::    Ab hier laeuft alles mit Admin-Rechten.
:: ============================================================================
cd /d "%~dp0"
set "LOGFILE=%~dp0install_debug.log"
echo ====================================================================== > "%LOGFILE%"
echo   Settlers 6 Mod Manager - Setup-Protokoll: %DATE% %TIME% >> "%LOGFILE%"
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
if not defined PYTHON_EXE (
    echo [ERROR] Python not found. >> "%LOGFILE%"
    echo.
    echo ======================================================================
    echo   FEHLER: Python konnte nicht gefunden werden!
    echo   Bitte installiere Python 3.12 oder neuer.
    echo ======================================================================
    echo.
    pause
    exit /b 1
)
echo [OK] Using Python: "!PYTHON_EXE!" >> "%LOGFILE%"

:: ============================================================================
:: 4. PyQt6 Verfuegbarkeit pruefen und installieren
:: ============================================================================
"!PYTHON_EXE!" -c "import PyQt6" >nul 2>&1
if !errorlevel! neq 0 (
    echo [INFO] PyQt6 not found. Installing... >> "%LOGFILE%"
    echo Installing required libraries [PyQt6]...
    "!PYTHON_EXE!" -m pip install PyQt6 >> "%LOGFILE%" 2>&1
)
echo [OK] PyQt6 check completed. >> "%LOGFILE%"

:: ============================================================================
:: 5. Setup-Assistenten starten
:: ============================================================================
echo [INFO] Launching Setup Assistant... >> "%LOGFILE%"
echo ======================================================================
echo   THE SETTLERS 6 - MOD AND MAP MANAGER
echo   Status: Launching Setup Assistant...
echo ======================================================================
echo.

"!PYTHON_EXE!" "%~dp0src\ModManager\setup_assistant.py" 2>> "%LOGFILE%"
set "EXIT_CODE=!errorlevel!"

echo [INFO] Setup Assistant exited with code: %EXIT_CODE% >> "%LOGFILE%"
if %EXIT_CODE% equ 99 (
    echo [INFO] Direct Launch requested. Starting ModManager... >> "%LOGFILE%"
    call "%~dp0START_MOD_MANAGER.bat"
    exit /b !errorlevel!
)
if %EXIT_CODE% neq 0 (
    echo.
    echo ======================================================================
    echo   [FEHLER] Setup Assistant wurde mit Fehlercode %EXIT_CODE% beendet.
    echo ======================================================================
    echo   Details siehe Logdatei: "%LOGFILE%"
    echo.
    type "%LOGFILE%"
    echo.
    pause
    exit /b %EXIT_CODE%
)

echo [OK] Setup Assistant erfolgreich beendet. >> "%LOGFILE%"
exit /b 0

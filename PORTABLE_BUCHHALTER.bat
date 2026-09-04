@echo off
REM ---------------------------------------------------------------------
REM  Portabler KI-Buchhalter - Start ohne gebaute EXE.
REM
REM  Diese Datei ist der Weg fuer Entwicklung und Tests. Das bevorzugte
REM  Endprodukt ist PORTABLE_BUCHHALTER.exe (siehe build\build_windows.ps1).
REM  Sie benoetigt eine vorhandene Python-Installation ab Version 3.11.
REM ---------------------------------------------------------------------
setlocal
cd /d "%~dp0"

set PYTHON=
if exist "runtime\python\python.exe" set PYTHON=runtime\python\python.exe
if "%PYTHON%"=="" (
    where python >nul 2>nul && set PYTHON=python
)
if "%PYTHON%"=="" (
    where py >nul 2>nul && set PYTHON=py -3
)
if "%PYTHON%"=="" (
    echo.
    echo Es wurde kein Python gefunden.
    echo.
    echo Bitte entweder Python 3.11 oder neuer installieren
    echo oder die gebaute PORTABLE_BUCHHALTER.exe verwenden.
    echo.
    pause
    exit /b 1
)

%PYTHON% portable_buchhalter.py %*
if errorlevel 1 pause

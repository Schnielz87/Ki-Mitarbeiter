@echo off
REM Startet den Windows-Build. Doppelklick genuegt.
setlocal
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "build\build_windows.ps1" %*
echo.
pause

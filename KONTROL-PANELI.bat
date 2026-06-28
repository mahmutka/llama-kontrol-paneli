@echo off
chcp 65001 >nul
title llama.cpp - Control Panel
cd /d "%~dp0"

echo ============================================================
echo   llama.cpp CONTROL PANEL  (local LLM lab)
echo   Your browser will open shortly:  http://127.0.0.1:8080
echo   Don't close this window! (press Ctrl+C to stop the panel)
echo ============================================================
echo.

REM Open the browser once the panel is up
start "" /min cmd /c "timeout /t 3 >nul && start http://127.0.0.1:8080"

REM Run the Python control panel
python kontrol_paneli.py

echo.
echo Panel closed.
pause

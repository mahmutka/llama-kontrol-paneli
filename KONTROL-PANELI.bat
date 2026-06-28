@echo off
chcp 65001 >nul
title llama.cpp - Kontrol Paneli
cd /d "%~dp0"

echo ============================================================
echo   llama.cpp KONTROL PANELI  (yerel LLM laboratuvari)
echo   Tarayici birazdan acilacak:  http://127.0.0.1:8080
echo   Bu pencereyi kapatma! (paneli kapatmak icin Ctrl+C)
echo ============================================================
echo.

REM Panel acilinca tarayiciyi ac
start "" /min cmd /c "timeout /t 3 >nul && start http://127.0.0.1:8080"

REM Python kontrol panelini calistir
python kontrol_paneli.py

echo.
echo Panel kapandi.
pause

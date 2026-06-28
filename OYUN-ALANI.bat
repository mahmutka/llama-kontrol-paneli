@echo off
chcp 65001 >nul
title llama.cpp - Oyun Alani (sunucu)
cd /d "%~dp0"

REM --- models\ icindeki ilk .gguf'u sec (adinda "mmproj" geceni ayir) ---
set "MODEL="
set "MMPROJ="
for %%f in (models\*.gguf) do (
  echo %%~nxf | find /i "mmproj" >nul
  if errorlevel 1 (
    if not defined MODEL set "MODEL=%%f"
  ) else (
    set "MMPROJ=%%f"
  )
)
if not defined MODEL (
  echo [!] models\ klasorunde .gguf model bulunamadi. Once bir model indir.
  pause & exit /b 1
)
set "MMARG="
if defined MMPROJ set MMARG=--mmproj "%MMPROJ%"

echo ============================================================
echo   Oyun Alani baslatiliyor...
echo   Model: %MODEL%
echo   Arayuz adresi:  http://127.0.0.1:8080
echo   Kapatmak icin bu pencereyi kapat (veya Ctrl+C).
echo ============================================================
echo.

REM --- Sunucu hazir olunca tarayiciyi ac (gecikmeli) ---
start "" /min cmd /c "timeout /t 14 >nul && start http://127.0.0.1:8080"

REM --- llama.cpp sunucusu (kendi web arayuzunu --path ile sunar) ---
bin\llama-server.exe -m "%MODEL%" %MMARG% --path playground -ngl 40 -c 4096 --host 127.0.0.1 --port 8080

echo.
echo Sunucu durdu.
pause

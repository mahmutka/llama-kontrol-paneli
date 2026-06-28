@echo off
chcp 65001 >nul
title llama.cpp - Playground (server)
cd /d "%~dp0"

REM --- pick the first .gguf in models\ (separate the "mmproj" one) ---
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
  echo [!] No .gguf model found in models\. Download a model first.
  pause & exit /b 1
)
set "MMARG="
if defined MMPROJ set MMARG=--mmproj "%MMPROJ%"

echo ============================================================
echo   Starting playground...
echo   Model: %MODEL%
echo   URL:  http://127.0.0.1:8080
echo   Close this window (or Ctrl+C) to stop.
echo ============================================================
echo.

REM --- open the browser once the server is ready (delayed) ---
start "" /min cmd /c "timeout /t 14 >nul && start http://127.0.0.1:8080"

REM --- llama.cpp server (serves its own web UI via --path) ---
bin\llama-server.exe -m "%MODEL%" %MMARG% --path playground -ngl 40 -c 4096 --host 127.0.0.1 --port 8080

echo.
echo Server stopped.
pause

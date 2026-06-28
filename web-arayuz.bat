@echo off
chcp 65001 >nul
REM === llama.cpp built-in web UI ===
REM After running, open this in your browser:  http://127.0.0.1:8080
cd /d "%~dp0"

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
if not defined MODEL ( echo [!] No .gguf model in models\. & pause & exit /b 1 )
set "MMARG="
if defined MMPROJ set MMARG=--mmproj "%MMPROJ%"

bin\llama-server.exe -m "%MODEL%" %MMARG% -ngl 40 -c 4096 --host 127.0.0.1 --port 8080
pause

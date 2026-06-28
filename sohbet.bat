@echo off
chcp 65001 >nul
REM === Chat in the terminal (llama-cli) ===
cd /d "%~dp0"

set "MODEL="
for %%f in (models\*.gguf) do (
  echo %%~nxf | find /i "mmproj" >nul
  if errorlevel 1 if not defined MODEL set "MODEL=%%f"
)
if not defined MODEL ( echo [!] No .gguf model in models\. & pause & exit /b 1 )

bin\llama-cli.exe -m "%MODEL%" -ngl 40 -c 4096 --jinja -cnv
pause

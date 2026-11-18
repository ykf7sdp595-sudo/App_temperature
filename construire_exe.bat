@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm App_temperature.spec
) else (
    "..\.venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm App_temperature.spec
)
pause


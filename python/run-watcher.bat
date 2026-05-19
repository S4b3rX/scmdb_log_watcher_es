@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No virtualenv found. Run install.bat first.
    pause
    exit /b 1
)

start "" ".venv\Scripts\python.exe" launcher.py %*

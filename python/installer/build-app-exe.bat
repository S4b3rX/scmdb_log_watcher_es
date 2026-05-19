@echo off
setlocal

cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No virtualenv found. Run install.bat first.
    exit /b 1
)

echo Installing build dependencies ...
".venv\Scripts\python.exe" -m pip install --upgrade pyinstaller
if errorlevel 1 exit /b 1

set "ROOT_RELEASE_DIR=%CD%\..\release\py"
if not exist "%ROOT_RELEASE_DIR%" mkdir "%ROOT_RELEASE_DIR%"
set "ROOT_RELEASE_LANG_DIR=%ROOT_RELEASE_DIR%\lang"

set "ICON_ARG="
if exist "assets\scmdb.ico" set "ICON_ARG=--icon assets\scmdb.ico"

if exist "dist\SCMDB-Watcher-Core.exe" del /q "dist\SCMDB-Watcher-Core.exe"
if exist "dist\SCMDB-Watcher-Installer.exe" del /q "dist\SCMDB-Watcher-Installer.exe"

echo Building SCMDB Watcher single EXE ...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name SCMDB-Watcher %ICON_ARG% launcher.py
if errorlevel 1 exit /b 1

copy /y "dist\SCMDB-Watcher.exe" "%ROOT_RELEASE_DIR%\SCMDB-Watcher.exe" >nul
copy /y "README.md" "%ROOT_RELEASE_DIR%\README.md" >nul
if exist "%ROOT_RELEASE_LANG_DIR%" rd /s /q "%ROOT_RELEASE_LANG_DIR%"
xcopy /E /I /Y "..\lang" "%ROOT_RELEASE_LANG_DIR%" >nul

echo.
echo Done. EXE created at:
echo   dist\SCMDB-Watcher.exe
echo Mirrored release at:
echo   ..\release\py\SCMDB-Watcher.exe
echo   ..\release\py\lang\
echo.

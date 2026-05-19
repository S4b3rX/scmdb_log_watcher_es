@echo off
setlocal

cd /d "%~dp0\.."

set "ISCC_EXE="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE (
    for /f "delims=" %%I in ('where iscc 2^>nul') do if not defined ISCC_EXE set "ISCC_EXE=%%I"
)
if not defined ISCC_EXE (
    echo [ERROR] Inno Setup compiler not found.
    echo Install Inno Setup 6+ and rerun this script.
    exit /b 1
)

echo Building app binaries used by the installer ...
call installer\build-app-exe.bat
if errorlevel 1 exit /b 1

set "ROOT_INSTALLER_DIR=%CD%\..\release\cs\installer"
if not exist "%ROOT_INSTALLER_DIR%" mkdir "%ROOT_INSTALLER_DIR%"

echo Compiling final installer package ...
"%ISCC_EXE%" /O"%ROOT_INSTALLER_DIR%" installer\INNO_SETUP_TEMPLATE.iss
if errorlevel 1 exit /b 1

echo.
echo Done. Installer created at: ..\release\cs\installer\SCMDB-Watcher-CSharp-Setup.exe
echo.

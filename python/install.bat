@echo off
setlocal EnableExtensions

REM SCMDB Log Watcher — one-time installer
REM Creates a local virtualenv and installs dependencies.

cd /d "%~dp0"

call :detect_python
if not defined PYTHON_CMD (
    call :handle_missing_python
    exit /b 1
)

call :ensure_python_ready
if errorlevel 1 exit /b 1

echo Launching installation wizard ...
call %PYTHON_CMD% installer_gui.py
if errorlevel 1 (
    echo.
    echo [INFO] Installation cancelled by user.
    echo.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Creating virtual environment in .venv ...
    call %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtualenv.
        pause
        exit /b 1
    )
)

echo Installing dependencies ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

echo.
echo Installation complete.
echo Run the watcher with: run-watcher.bat
echo.
pause
exit /b 0

:detect_python
set "PYTHON_CMD="

where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)

if defined PYTHON_CMD goto :eof

where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)
goto :eof

:ensure_python_ready
call :check_python_ready
if not errorlevel 1 goto :eof

if "%errorlevel%"=="10" (
    echo.
    echo [ERROR] Python 3.10 or newer is required.
    echo.
    call :handle_missing_python
    exit /b 1
)

if "%errorlevel%"=="11" (
    echo.
    echo [ERROR] Python is installed but missing required standard modules ^(venv^).
    echo.
    call :handle_python_repair
    exit /b 1
)

exit /b 1

:check_python_ready
set "PYTHON_OK="
for /f %%I in ('%PYTHON_CMD% -c "import sys; print(1 if sys.version_info[:2] ^>= (3, 10) else 0)" 2^>nul') do set "PYTHON_OK=%%I"
if not "%PYTHON_OK%"=="1" exit /b 10

set "PYTHON_STD_OK="
for /f %%I in ('%PYTHON_CMD% -c "import importlib.util; required=('venv',); print(1 if all(importlib.util.find_spec(name) for name in required) else 0)" 2^>nul') do set "PYTHON_STD_OK=%%I"
if not "%PYTHON_STD_OK%"=="1" exit /b 11
exit /b 0

:handle_missing_python
echo [ERROR] Python 3.10+ is not installed or not available on PATH.
echo.
call :prompt_python_action install
goto :eof

:handle_python_repair
echo [ERROR] Python needs to be repaired or reinstalled before setup can continue.
echo.
call :prompt_python_action repair
goto :eof

:prompt_python_action
set "ACTION_LABEL=%~1"
set "HAS_WINGET=0"
where winget >nul 2>&1
if not errorlevel 1 set "HAS_WINGET=1"

echo Prerequisite options:
echo   [1] Open Microsoft Store Python page
if "%HAS_WINGET%"=="1" echo   [2] Install Python automatically with winget
if "%HAS_WINGET%"=="1" (
    echo   [3] Open python.org downloads
    echo   [4] Cancel
    choice /c 1234 /n /m "Choose an option: "
    set "USER_CHOICE=%errorlevel%"
) else (
    echo   [2] Open python.org downloads
    echo   [3] Cancel
    choice /c 123 /n /m "Choose an option: "
    set "USER_CHOICE=%errorlevel%"
)

if "%HAS_WINGET%"=="1" (
    if "%USER_CHOICE%"=="1" start "" "ms-windows-store://pdp/?productid=9PNRBTZXMB4Z"
    if "%USER_CHOICE%"=="2" call :run_winget_python_install
    if "%USER_CHOICE%"=="3" start "" "https://www.python.org/downloads/windows/"
    if "%USER_CHOICE%"=="4" goto :prompt_done
) else (
    if "%USER_CHOICE%"=="1" start "" "ms-windows-store://pdp/?productid=9PNRBTZXMB4Z"
    if "%USER_CHOICE%"=="2" start "" "https://www.python.org/downloads/windows/"
    if "%USER_CHOICE%"=="3" goto :prompt_done
)

:prompt_done
call :detect_python
if defined PYTHON_CMD (
    call :check_python_ready
    if not errorlevel 1 goto :eof
)

echo.
echo Rerun install.bat after Python %ACTION_LABEL% completes.
echo.
pause
goto :eof

:run_winget_python_install
echo.
echo Installing Python with winget ...
winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
echo.
goto :eof

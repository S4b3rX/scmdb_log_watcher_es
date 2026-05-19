@echo off
setlocal

cd /d "%~dp0\.."

where dotnet >nul 2>nul
if errorlevel 1 (
    echo [ERROR] dotnet SDK not found.
    exit /b 1
)

set "PUBLISH_DIR=%CD%\build\publish\desktop"
set "ROOT_RELEASE_DIR=%CD%\..\release\cs"

if exist "%PUBLISH_DIR%" rd /s /q "%PUBLISH_DIR%"
if not exist "%PUBLISH_DIR%" mkdir "%PUBLISH_DIR%"
if not exist "%ROOT_RELEASE_DIR%" mkdir "%ROOT_RELEASE_DIR%"

echo Publishing SCMDB Watcher Desktop single-file build ...
dotnet publish .\src\SCMDB.Watcher.Desktop\SCMDB.Watcher.Desktop.csproj -c Release -r win-x64 -p:PublishSingleFile=true -p:SelfContained=true -o "%PUBLISH_DIR%"
if errorlevel 1 exit /b 1

copy /y "%PUBLISH_DIR%\SCMDB.Watcher.Desktop.exe" "%ROOT_RELEASE_DIR%\SCMDB.Watcher.Desktop.exe" >nul
if exist "%PUBLISH_DIR%\SCMDB.Watcher.Desktop.pdb" copy /y "%PUBLISH_DIR%\SCMDB.Watcher.Desktop.pdb" "%ROOT_RELEASE_DIR%\SCMDB.Watcher.Desktop.pdb" >nul
copy /y "README.md" "%ROOT_RELEASE_DIR%\README.md" >nul

echo.
echo Done. EXE created at:
echo   build\publish\desktop\SCMDB.Watcher.Desktop.exe
echo Mirrored release at:
echo   ..\release\cs\SCMDB.Watcher.Desktop.exe
echo.

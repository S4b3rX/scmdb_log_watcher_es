# Installer Build Guide

This documentation applies to the Python implementation under `python/`.
Run the commands below from inside that folder.

This folder contains scripts and templates to package SCMDB Log Watcher as EXE and a single final installer.

## 1) Build app EXEs

Run:

```bat
installer\build-app-exe.bat
```

Output:

- dist\\SCMDB-Watcher.exe
- ..\\release\\py\\SCMDB-Watcher.exe
- ..\\release\\py\\lang\\

The packaged app is a single binary:

- SCMDB-Watcher.exe: GUI by default, with internal subcommands for live/import

## 2) Build the final installer package

Run:

```bat
installer\build-installer-exe.bat
```

Output:

- ..\\release\\py\\installer\\SCMDB-Log-Watcher-Setup.exe

## What the final installer contains

The final installer is a single Inno Setup executable that installs:

- SCMDB-Watcher.exe
- README.md
- lang\\*.json
- lang\\README.md

It also creates the Start Menu and Desktop shortcuts for the main app.

The first-run configuration happens inside the app, not as a separate installer wizard.

The installer requests elevation so the app is installed under Program Files
instead of a user-local Programs folder.

User runtime data, logs and imports are created on first launch under each
user's LocalAppData by the app itself.

Language files are installed under `Program Files\\SCMDB Log Watcher\\lang` so users can edit or add translations without rebuilding the app.

## 3) Manual Inno Setup compilation (optional)

Use Inno Setup (ISCC.exe) with template:

- installer\\INNO_SETUP_TEMPLATE.iss

Typical command (update path to your Inno Setup installation):

```bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\INNO_SETUP_TEMPLATE.iss
```

Output installer EXE is generated in `..\\release\\py\\installer\\SCMDB-Log-Watcher-Setup.exe`.

## Rebuild after code changes

1. Run tests or manual checks.
2. Re-run EXE build scripts.
3. Re-run Inno Setup compile.

## Suggested VS Code workflow

1. Open this workspace in VS Code.
2. Run install.bat after pulling changes.
3. Run installer\build-app-exe.bat to rebuild the app binaries used by the installer.
4. Run installer\build-installer-exe.bat to rebuild the final single-file installer.
5. If needed, compile installer\INNO_SETUP_TEMPLATE.iss directly with Inno Setup.

## Notes

- Current setup uses default icons.
- You can later replace icons by adding --icon in PyInstaller commands and IconFilename in Inno Setup.
- Inno Setup creates empty runtime/, runtime/logs/ and runtime/scmdb-import/ folders so installed builds keep the same local layout as dev/runtime.
- watcher-config.json is still created on first run so each installation keeps its own local runtime configuration.

# C# Installer Build Guide

This documentation applies to the C# implementation under `csharp/`.
Run the commands below from inside that folder.

## 1) Build desktop EXE

Run:

```bat
installer\build-app-exe.bat
```

Outputs:

- build\publish\desktop\SCMDB.Watcher.Desktop.exe
- ..\release\cs\SCMDB.Watcher.Desktop.exe

## 2) Build final installer

Run:

```bat
installer\build-installer-exe.bat
```

Output:

- ..\release\cs\installer\SCMDB-Watcher-CSharp-Setup.exe

## Notes

- The installer packages the single-file WinForms desktop build plus the C# README.
- The current C# build shares runtime/config storage with the Python watcher under LocalAppData, so the installer does not wipe LocalAppData on uninstall.

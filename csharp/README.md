# SCMDB Watcher .NET Prototype (Archived)

This folder contains the archived C#/.NET prototype.
It is intentionally preserved as reference material, but it is no longer the active product target.

Production work continues in [python/README.md](python/README.md).

## Current status

- Archived for day-to-day development.
- Not the release target.
- Kept to preserve the porting work, packaging experiments and future Avalonia exploration.
- Only reactivate if there is a deliberate decision to replace the Python desktop app.

## Why C# / .NET desktop and not ASP.NET

This app is primarily a Windows desktop utility, not a web application:

- it needs a tray-capable desktop UI
- it watches a local file in real time
- it detects local processes like StarCitizen.exe
- it exposes a small localhost API for SCMDB
- it benefits from single-file, self-contained Windows publishing

ASP.NET only solves the local HTTP part. It does not solve the desktop UX, tray integration or packaging story by itself.

C# with .NET is a better fit because it gives you:

- native Windows desktop support via WinForms or WPF
- self-contained publish so end users do not need Python installed
- a mature installer story with Inno Setup, WiX or MSIX
- straightforward access to Windows APIs and process inspection
- a built-in web stack for the localhost endpoints when needed

## Recommended target shape

- SCMDB.Watcher.Core: parsing, config, process detection, import logic
- SCMDB.Watcher.Desktop: tray app, settings UI, start/stop UX
- SCMDB.Watcher.Core.Tests: parser and correlation tests

## What this prototype already proved

Already ported in this fork:

- watcher-config.json loading, normalization and persistence
- runtime/data/config path resolution aligned with the Python watcher
- Game.log mission and blueprint parser
- in-memory mission state tracking
- localhost API with /ping, /state and /events SSE
- live log tailing and runtime host wiring
- historical import scanning and export payload generation
- WinForms desktop shell wired to the runtime host

## Why it is archived now

The Python implementation reached the point where keeping a second watcher in parallel no longer makes maintenance sense. Every feature, packaging change, UI improvement and translation update would otherwise need to be repeated twice.

Because of that, this folder is intentionally frozen as a prototype instead of being removed.

## Remaining work if it is ever reactivated

If the .NET path is revived later, the main pending areas remain:

1. Replace the temporary desktop shell with the full watcher UX: settings, start/stop flow, status colors, import action and tray behavior.
2. Verify the new packaging flow end to end with the real installer output.
3. Add process detection and any remaining startup/runtime diagnostics used by the Python app.
4. Verify the C# localhost runtime against the real SCMDB website end to end.

## Packaging commands

These are preserved for reference. They are not part of the current production release flow.

Build the desktop EXE into the shared release tree:

```bat
installer\build-app-exe.bat
```

Build the final installer into the shared release tree:

```bat
installer\build-installer-exe.bat
```

Outputs:

- ..\release\cs\SCMDB.Watcher.Desktop.exe
- ..\release\cs\installer\SCMDB-Watcher-CSharp-Setup.exe

## Example publish command

```powershell
dotnet publish .\src\SCMDB.Watcher.Desktop\SCMDB.Watcher.Desktop.csproj -c Release -r win-x64 -p:PublishSingleFile=true -p:SelfContained=true
```

That output can be packaged with Inno Setup without requiring Python on the target machine.

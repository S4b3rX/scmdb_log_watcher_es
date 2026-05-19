; Inno Setup template for SCMDB Watcher C# desktop build
; Requires Inno Setup 6+

[Setup]
AppId={{72570D5A-6607-4037-8D56-E6D904B7276E}
AppName=SCMDB Watcher C#
AppVersion=0.1.2
AppPublisher=SCMDB
DefaultDirName={autopf}\SCMDB Watcher C#
DefaultGroupName=SCMDB Watcher C#
UninstallDisplayName=SCMDB Watcher C#
UninstallDisplayIcon={app}\SCMDB.Watcher.Desktop.exe
OutputBaseFilename=SCMDB-Watcher-CSharp-Setup
OutputDir=..\..\release\cs\installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Files]
Source: "..\..\release\cs\SCMDB.Watcher.Desktop.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SCMDB Watcher C#"; Filename: "{app}\SCMDB.Watcher.Desktop.exe"
Name: "{autodesktop}\SCMDB Watcher C#"; Filename: "{app}\SCMDB.Watcher.Desktop.exe"

[Run]
Filename: "{app}\SCMDB.Watcher.Desktop.exe"; Description: "Launch SCMDB Watcher C#"; Flags: nowait postinstall skipifsilent

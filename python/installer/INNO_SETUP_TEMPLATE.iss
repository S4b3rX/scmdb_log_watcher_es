; Inno Setup template for SCMDB Watcher
; Requires Inno Setup 6+

[Setup]
AppId={{63A82168-B5C2-4A3E-8B96-EA1A952F94A0}
AppName=SCMDB Log Watcher
AppVersion=0.1.2
AppPublisher=SCMDB
DefaultDirName={autopf}\SCMDB Log Watcher
DefaultGroupName=SCMDB Log Watcher
UninstallDisplayName=SCMDB Log Watcher
UninstallDisplayIcon={app}\SCMDB-Watcher.exe
OutputBaseFilename=SCMDB-Log-Watcher-Setup
OutputDir=..\release
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Files]
Source: "..\dist\SCMDB-Watcher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\lang\*"; DestDir: "{app}\lang"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SCMDB Watcher"; Filename: "{app}\SCMDB-Watcher.exe"
Name: "{autodesktop}\SCMDB Watcher"; Filename: "{app}\SCMDB-Watcher.exe"

[Run]
Filename: "{app}\SCMDB-Watcher.exe"; Description: "Launch SCMDB Watcher"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\SCMDB Log Watcher"

[Code]
procedure ForceCloseWatcherProcesses();
var
	ResultCode: Integer;
begin
	Exec(ExpandConstant('{cmd}'), '/C taskkill /IM SCMDB-Watcher.exe /F /T >nul 2>&1', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
	if CurStep = ssInstall then
		ForceCloseWatcherProcesses();
end;

function InitializeUninstall(): Boolean;
begin
	ForceCloseWatcherProcesses();
	Result := True;
end;

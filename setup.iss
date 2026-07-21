; Inno Setup script for ResiControl
; Requires Inno Setup 6+ (https://jrsoftware.org/isdl.php)

#define MyAppName "ResiControl"
#define MyAppVersion "2.3.0"
#define MyAppPublisher "ResiControl"
#define MyAppURL "https://resicontrol.app"
#define MyAppExeName "ResiControl.exe"

[Setup]
AppId={{B8F4C9A1-3E2D-4F5A-8B7C-9D0E1F2A3B4C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
InfoBeforeFile=
OutputDir=installer
OutputBaseFilename=ResiControl_v{#MyAppVersion}_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
Source: "dist\ResiControl\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    CreateDir(ExpandConstant('{userappdata}\ResiControl'));
    CreateDir(ExpandConstant('{userappdata}\ResiControl\qrs'));
    CreateDir(ExpandConstant('{userappdata}\ResiControl\reportes'));
    CreateDir(ExpandConstant('{userappdata}\ResiControl\logs'));
    CreateDir(ExpandConstant('{userappdata}\ResiControl\backups'));
  end;
end;

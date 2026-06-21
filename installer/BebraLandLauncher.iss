#define MyAppName "BebraLand Launcher"
#define MyAppPublisher "BebraLand Team"
#define MyAppExeName "BebraLandLauncher.exe"
#define MyUpdaterExeName "BebraLandUpdater.exe"
#define MyAppCopyright "(c) " + GetDateTimeString("yyyy", "", "") + " BebraLand Team"
#define BuildVersion GetEnv("BEBRALAND_BUILD_VERSION")
#define WindowsFileVersion GetEnv("BEBRALAND_WINDOWS_FILE_VERSION")
#if BuildVersion == ""
#define MyAppVersion "0.1.0"
#else
#define MyAppVersion BuildVersion
#endif
#if WindowsFileVersion == ""
#define WindowsFileVersion "0.1.0.0"
#endif

[Setup]
AppId={{9B5A9A11-5A96-4C02-94C8-3E5230C0C92B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\BebraLand Launcher
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=BebraLand-Launcher-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
SetupIconFile=..\resources\gml\Images\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=BebraLand Launcher Setup
VersionInfoTextVersion={#MyAppVersion}
VersionInfoVersion={#WindowsFileVersion}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoCopyright={#MyAppCopyright}

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\{#MyUpdaterExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{userprograms}\{#MyAppName}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

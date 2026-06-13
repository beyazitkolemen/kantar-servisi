#define AppName "Kantar Servisi"
#define AppPublisher "LISDEP"
#define AppExeName "KantarServisi.exe"

#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif

[Setup]
AppId={{9A6443EA-27E3-4AF4-BD65-C3A907AFC103}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/beyazitkolemen/kantar-servisi
AppSupportURL=https://github.com/beyazitkolemen/kantar-servisi/issues
AppUpdatesURL=https://github.com/beyazitkolemen/kantar-servisi/releases
DefaultDirName={localappdata}\Programs\Kantar Servisi
DefaultGroupName=Kantar Servisi
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\..\release
OutputBaseFilename=Kantar-Servisi-Setup
SetupIconFile=..\..\.build-assets\app.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
AppMutex=Local\KantarServisi
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} Windows Kurulumu
VersionInfoProductName={#AppName}

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaustune kisayol olustur"; GroupDescription: "Ek kisayollar:"; Flags: unchecked
Name: "startup"; Description: "Windows acildiginda sistem tepsisinde baslat"; GroupDescription: "Baslangic:"; Flags: checkedonce

[Files]
Source: "..\..\dist\KantarServisi\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Kantar Servisi"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Kantar Servisi Web Paneli"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\Kantar Servisi"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartup}\Kantar Servisi"; Filename: "{app}\{#AppExeName}"; Parameters: "--minimized"; WorkingDir: "{app}"; Tasks: startup

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Kantar Servisini baslat"; Flags: nowait postinstall skipifsilent

; Instalador do FileDocs (Inno Setup 6). Gerado por installer\build.ps1.
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{8C3B6F2E-6E1D-4F7A-9B1C-FD0C5D0C1A11}
AppName=FileDocs
AppVersion={#AppVersion}
AppPublisher=Levi Mota
DefaultDirName={localappdata}\Programs\FileDocs
DefaultGroupName=FileDocs
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=FileDocs-Setup-{#AppVersion}
SetupIconFile=..\assets\filedocs.ico
UninstallDisplayIcon={app}\FileDocs.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"
Name: "contextmenu"; Description: "Adicionar FileDocs ao menu de clique-direito"

[Files]
Source: "..\dist\FileDocs\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\FileDocs"; Filename: "{app}\FileDocs.exe"
Name: "{userdesktop}\FileDocs"; Filename: "{app}\FileDocs.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\FileDocs.exe"; Parameters: "--install-menu"; Tasks: contextmenu; Flags: runhidden
Filename: "{app}\FileDocs.exe"; Description: "Abrir o FileDocs"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\FileDocs.exe"; Parameters: "--uninstall-menu"; Flags: runhidden; RunOnceId: "menu"

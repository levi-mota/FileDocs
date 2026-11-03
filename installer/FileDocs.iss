; Instalador do FileDocs (Inno Setup 6). Gerado por installer\build.ps1.
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
; LibreOffice oficial, baixado durante a instalação (opcional) para converter Word/Excel/PowerPoint
#define LOVersion "26.2.7"
#define LOUrl "https://download.documentfoundation.org/libreoffice/stable/" + LOVersion + "/win/x86_64/LibreOffice_" + LOVersion + "_Win_x86-64.msi"
#define LOSha256 "480fecf759fc6393bd614fbf43753eb95a8198fc1a065d41b727e3b664cd1e59"

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
Name: "libreoffice"; Description: "Conversão de Word, Excel e PowerPoint para PDF (baixa o LibreOffice do site oficial, cerca de 360 MB)"; Flags: unchecked

[Files]
Source: "..\dist\FileDocs\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "libreoffice.ps1"; DestDir: "{app}\tools"; Flags: ignoreversion

[UninstallDelete]
Type: filesandordirs; Name: "{app}\libreoffice"

[Icons]
Name: "{group}\FileDocs"; Filename: "{app}\FileDocs.exe"
Name: "{userdesktop}\FileDocs"; Filename: "{app}\FileDocs.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\FileDocs.exe"; Parameters: "--install-menu"; Tasks: contextmenu; Flags: runhidden
Filename: "{app}\FileDocs.exe"; Description: "Abrir o FileDocs"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\FileDocs.exe"; Parameters: "--uninstall-menu"; Flags: runhidden; RunOnceId: "menu"

[Code]
var
  TasksAdjusted: Boolean;

function HasMSOffice: Boolean;
begin
  Result := RegKeyExists(HKCR, 'Word.Application\CLSID');
end;

{ Sem Microsoft Office, o download vem marcado; com ele a conversão já funciona.
  Instalação silenciosa: só baixa se pedido em /TASKS. }
procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpSelectTasks) and not TasksAdjusted then begin
    TasksAdjusted := True;
    if not HasMSOffice then WizardSelectTasks('libreoffice');
  end;
end;

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  if ProgressMax > 0 then begin
    WizardForm.StatusLabel.Caption := Format('Baixando o LibreOffice do site oficial... %d de %d MB', [Integer(Progress div 1048576), Integer(ProgressMax div 1048576)]);
    WizardForm.ProgressGauge.Max := 1000;
    WizardForm.ProgressGauge.Position := Integer(Progress * 1000 div ProgressMax);
  end;
  Result := True;
end;

procedure SetupLibreOffice;
var
  Msi: String;
  Code: Integer;
begin
  if FileExists(ExpandConstant('{app}\libreoffice\program\soffice.exe')) then Exit;
  try
    DownloadTemporaryFile('{#LOUrl}', 'libreoffice.msi', '{#LOSha256}', @OnDownloadProgress);
  except
    SuppressibleMsgBox('Não foi possível baixar o LibreOffice (' + GetExceptionMessage + ').' + #13#10 +
      'O FileDocs funciona normalmente; só a conversão de Word/Excel/PowerPoint fica indisponível.' + #13#10 +
      'Para tentar de novo, execute o instalador outra vez.', mbInformation, MB_OK, IDOK);
    Exit;
  end;
  Msi := ExpandConstant('{tmp}\libreoffice.msi');
  WizardForm.StatusLabel.Caption := 'Preparando a conversão de documentos do Office...';
  WizardForm.ProgressGauge.Style := npbstMarquee;
  Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\tools\libreoffice.ps1') +
    '" -Msi "' + Msi + '" -Target "' + ExpandConstant('{app}\libreoffice') + '"', '', SW_HIDE, ewWaitUntilTerminated, Code);
  WizardForm.ProgressGauge.Style := npbstNormal;
  DeleteFile(Msi);
  if not FileExists(ExpandConstant('{app}\libreoffice\program\soffice.exe')) then
    SuppressibleMsgBox('Não foi possível preparar o LibreOffice. A conversão de Word/Excel/PowerPoint fica indisponível.',
      mbInformation, MB_OK, IDOK);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('libreoffice') then SetupLibreOffice;
end;

[Setup]
AppName=Məzuniyyət İdarəetmə Sistemi
AppVersion=7.1
DefaultDirName={userappdata}\MezuniyyetSistemi
DefaultGroupName=Məzuniyyət Sistemi
OutputDir=dist
OutputBaseFilename=MezuniyyetSistemi_Setup_v7.1_NoAdmin
SetupIconFile=..\src\icons\icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "azerbaijani"; MessagesFile: "compiler:Languages\Azerbaijani.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Əsas proqram
Source: "dist\MezuniyyetSistemi.exe"; DestDir: "{app}"; Flags: ignoreversion

; Konfiqurasiya faylları
; Source: "..\src\config\version.txt"; DestDir: "{app}\src\config"; Flags: ignoreversion
; Source: "..\src\config\requirements.txt"; DestDir: "{app}\src\config"; Flags: ignoreversion
; Source: "..\src\config\theme.json"; DestDir: "{app}\src\config"; Flags: ignoreversion
; Source: "..\src\api\requirements.txt"; DestDir: "{app}\src\api"; Flags: ignoreversion

; Sənəd faylları (installer-ə daxil edilmir)
; Source: "..\oxu\README.md"; DestDir: "{app}"; Flags: ignoreversion
; Source: "..\oxu\STRUCTURE.md"; DestDir: "{app}"; Flags: ignoreversion
; Source: "..\oxu\INSTALLATION_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion

; Veritaban faylları - REMOVED (tenant sistemi istifadə olunur)
; Source: "..\src\database\*.db"; DestDir: "{app}\src\database"; Flags: ignoreversion

[Icons]
Name: "{group}\Məzuniyyət Sistemi"; Filename: "{app}\MezuniyyetSistemi.exe"
Name: "{group}\{cm:UninstallProgram,Məzuniyyət Sistemi}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Məzuniyyət Sistemi"; Filename: "{app}\MezuniyyetSistemi.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MezuniyyetSistemi.exe"; Description: "{cm:LaunchProgram,Məzuniyyət Sistemi}"; Flags: nowait postinstall skipifsilent

[InstallDelete]
; Keçmiş quraşdırmalardan qalan lazımsız faylları sil
Type: files; Name: "{app}\email_config.json"
Type: files; Name: "{app}\README.md"
Type: files; Name: "{app}\STRUCTURE.md"
Type: files; Name: "{app}\INSTALLATION_GUIDE.md"
Type: files; Name: "{app}\unified_app_debug.log"

[UninstallDelete]
; Uninstall zamanı cache fayllarını da təmizlə
Type: files; Name: "{app}\*cache*.json"
Type: files; Name: "{app}\tenant_cache.json"
Type: files; Name: "{app}\user_data.json"

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Proqramın adı: MezuniyyetSistemi.exe
  // Taskkill ilə bağlamağa cəhd edirik
  Exec('taskkill.exe', '/IM MezuniyyetSistemi.exe /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  
  Result := True;
end;
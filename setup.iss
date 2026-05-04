; ─────────────────────────────────────────────────────────────────
;  Itchy YouTube Downloader — Inno Setup Script
;  Inno Setup 6.x ile derleyin: https://jrsoftware.org/isinfo.php
; ─────────────────────────────────────────────────────────────────

#define AppName      "Itchy YouTube Downloader"
#define AppVersion   "1.3"
#define AppPublisher "Itchy"
#define AppExeName   "ItchyDownloader.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL=https://github.com
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\ItchyDownloader
DefaultGroupName={#AppName}
OutputDir=.\installer_output
OutputBaseFilename=ItchyDownloader_Setup_v{#AppVersion}
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardImageFile=compiler:WizModernImage.bmp
WizardSmallImageFile=compiler:WizModernSmallImage.bmp
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

[Languages]
Name: "turkish";  MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english";  MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek görevler:"; Flags: unchecked

[Files]
; Ana uygulama (PyInstaller --onedir çıktısı)
Source: "dist\ItchyDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Logo
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}";          Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\logo.ico"
Name: "{group}\Kaldır";              Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";    Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Itchy Downloader'ı başlat"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

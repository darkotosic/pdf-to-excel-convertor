#define AppName "PDF to Excel Converter"
#define AppVersion "1.0.0"
[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\PDF to Excel Converter
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputBaseFilename=PDF-to-Excel-Setup
Compression=lzma2
SolidCompression=yes
[Files]
Source: "..\dist\PDF-to-Excel\*"; DestDir: "{app}"; Flags: recursesubdirs
[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\PDF-to-Excel.exe"
[Run]
Filename: "{app}\PDF-to-Excel.exe"; Description: "Launch {#AppName}"; Flags: postinstall nowait skipifsilent

[Setup]
AppName=xdev Toolchain
AppVersion=v0.1.0-alpha
DefaultDirName={autopf}\xdev
DefaultGroupName=xdev Toolchain
OutputBaseFilename=xdev-setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
; Point directly to single-file dist\xdev.exe
Source: "dist\xdev.exe"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "envPath"; Description: "Add xdev to System PATH"; Flags: checkedonce

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  Path: String;
begin
  if CurStep = ssPostInstall then
  begin
    if RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Path) then
    begin
      if Pos(ExpandConstant('{app}'), Path) = 0 then
      begin
        Path := Path + ';' + ExpandConstant('{app}');
        RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Path);
      end;
    end;
  end;
end;
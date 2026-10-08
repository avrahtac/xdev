;
; xdev Toolchain Installer Script
; Copyright (c) 2026 Atharva Chitale & XenevaOS Team
;

[Setup]
AppName=xdev Toolchain
AppVersion=v0.1.0-alpha
AppPublisher=Atharva Chitale
DefaultDirName={autopf}\xdev
DefaultGroupName=xdev Toolchain
OutputBaseFilename=xdev-setup
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
PrivilegesRequired=admin

[Files]
; Copy single-file xdev.exe CLI binary directly to install dir
Source: "dist\xdev.exe"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "envPath"; Description: "Add xdev and MSYS2 UCRT64 to System PATH"; Flags: checkedonce

[Code]
var
  RepoDirPage: TInputDirWizardPage;

procedure InitializeWizard;
begin
  // Custom Page to ask user for their XenevaOS repository location
  RepoDirPage := CreateInputDirPage(wpSelectDir,
    'Select XenevaOS Repository',
    'Where is your XenevaOS source code located?',
    'Select the folder where XenevaOS is cloned on your computer, then click Next.',
    False, '');
  RepoDirPage.Add('');
  RepoDirPage.Values[0] := 'D:\XenevaOS';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  UserPath, XenevaPath: String;
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // 1. Register XENEVA_PROJECT Environment Variable
    XenevaPath := RepoDirPage.Values[0];
    if XenevaPath <> '' then
    begin
      RegWriteStringValue(HKEY_LOCAL_MACHINE,
        'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
        'XENEVA_PROJECT', XenevaPath);
    end;

    // 2. Register System PATH
    if RegQueryStringValue(HKEY_LOCAL_MACHINE,
      'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
      'Path', UserPath) then
    begin
      if Pos(ExpandConstant('{app}'), UserPath) = 0 then
        UserPath := UserPath + ';' + ExpandConstant('{app}');
      if Pos('C:\msys64\ucrt64\bin', UserPath) = 0 then
        UserPath := UserPath + ';C:\msys64\ucrt64\bin';
      if Pos('C:\msys64\usr\bin', UserPath) = 0 then
        UserPath := UserPath + ';C:\msys64\usr\bin';

      RegWriteStringValue(HKEY_LOCAL_MACHINE,
        'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
        'Path', UserPath);
    end;

    // 3. Install MSYS2 if missing via Winget
    if not DirExists('C:\msys64') then
    begin
      Exec('cmd.exe', '/c winget install --id MSYS2.MSYS2 -e --silent --accept-package-agreements --accept-source-agreements', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;

    // 4. Install toolchain packages (clang, lld, qemu, make, mtools, dosfstools)
    if FileExists('C:\msys64\usr\bin\bash.exe') then
    begin
      Exec('C:\msys64\usr\bin\bash.exe', '-lc "pacman -Sy --noconfirm --needed mingw-w64-ucrt-x86_64-clang mingw-w64-ucrt-x86_64-lld mingw-w64-ucrt-x86_64-qemu mingw-w64-ucrt-x86_64-mtools make dosfstools"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
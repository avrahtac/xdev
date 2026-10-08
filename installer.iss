;
; xdev Toolchain Complete Installer Script
; Copyright (c) 2026 Atharva Chitale & XenevaOS Team
; Distributed under BSD 2-Clause License
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
LicenseFile=LICENSE

[Files]
; Copy xdev.exe CLI binary directly to target directory
Source: "dist\xdev.exe"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "envPath"; Description: "Add xdev and MSYS2 binaries to System PATH"; Flags: checkedonce

[Code]
var
  RepoDirPage: TInputDirWizardPage;

procedure InitializeWizard;
begin
  // Create interactive page asking user for XenevaOS repository location
  RepoDirPage := CreateInputDirPage(wpLicense,
    'Select XenevaOS Repository Location',
    'Where is your XenevaOS source code located?',
    'Select the folder where XenevaOS is cloned on your computer, then click Next.',
    False, '');
  RepoDirPage.Add('');
  RepoDirPage.Values[0] := 'D:\XenevaOS';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  UserPath, XenevaPath: String;
  ResultCode, I: Integer;
  BashBin, PacmanCmd: String;
begin
  if CurStep = ssPostInstall then
  begin
    // 1. Configure XENEVA_PROJECT Environment Variable
    XenevaPath := RepoDirPage.Values[0];
    if XenevaPath <> '' then
    begin
      RegWriteStringValue(HKEY_LOCAL_MACHINE,
        'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
        'XENEVA_PROJECT', XenevaPath);
    end;

    // 2. Configure System PATH (Includes xdev app dir and MSYS2 UCRT64 + USR binaries)
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

    // 3. Install MSYS2 via Winget if missing
    if not DirExists('C:\msys64') then
    begin
      WizardForm.StatusLabel.Caption := 'Installing MSYS2 environment via Winget...';
      Exec('cmd.exe', '/c winget install --id MSYS2.MSYS2 -e --silent --accept-package-agreements --accept-source-agreements', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    end;

    // 4. Wait for bash.exe to be ready (Retry up to 10 seconds if Winget background setup takes time)
    BashBin := 'C:\msys64\usr\bin\bash.exe';
    for I := 1 to 10 do
    begin
      if FileExists(BashBin) then Break;
      Sleep(1000);
    end;

    // 5. Install Full Toolchain via Pacman (Clang, LLD, LLVM, QEMU, Mtools, Make, Dosfstools)
    if FileExists(BashBin) then
    begin
      WizardForm.StatusLabel.Caption := 'Installing Toolchain (Clang, LLD, QEMU, Make, Mtools)...';
      PacmanCmd := '-lc "pacman -Syu --needed --noconfirm mingw-w64-ucrt-x86_64-clang mingw-w64-ucrt-x86_64-llvm mingw-w64-ucrt-x86_64-lld mingw-w64-ucrt-x86_64-qemu mingw-w64-ucrt-x86_64-mtools make dosfstools"';
      Exec(BashBin, PacmanCmd, '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
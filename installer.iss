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
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Update progress text on the installer UI
    WizardForm.StatusLabel.Caption := 'Checking and provisioning build toolchain dependencies...';

    // 1. Configure XENEVA_PROJECT
    XenevaPath := RepoDirPage.Values[0];
    if XenevaPath <> '' then
    begin
      RegWriteStringValue(HKEY_LOCAL_MACHINE,
        'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
        'XENEVA_PROJECT', XenevaPath);
    end;

    // 2. Configure System PATH
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

    // 3. Install MSYS2 if missing
    if not DirExists('C:\msys64') then
    begin
      WizardForm.StatusLabel.Caption := 'Installing MSYS2 base system via Winget...';
      Exec('cmd.exe', '/c winget install --id MSYS2.MSYS2 -e --silent --accept-package-agreements --accept-source-agreements', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    end;

    // 4. Install/Update pacman packages (Clang, LLD, QEMU, Make, Mtools, Dosfstools)
    if FileExists('C:\msys64\usr\bin\bash.exe') then
    begin
      WizardForm.StatusLabel.Caption := 'Syncing toolchain packages (Clang, LLD, QEMU, Mtools)...';
      Exec('C:\msys64\usr\bin\bash.exe', '-lc "pacman -Syu --needed --noconfirm mingw-w64-ucrt-x86_64-clang mingw-w64-ucrt-x86_64-lld mingw-w64-ucrt-x86_64-qemu mingw-w64-ucrt-x86_64-mtools make dosfstools"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
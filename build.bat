@echo off
REM Copyright (c) 2026 Manas Kamal Choudhary and XenevaOS Team
REM All rights reserved.

echo [INFO] Compiling xdev via MSYS2 UCRT64 environment...
set CURRENT_DIR=%~dp0
set CURRENT_DIR=%CURRENT_DIR:\=/%
set CURRENT_DIR=/%CURRENT_DIR::=%

if exist "C:\msys64\usr\bin\bash.exe" (
    C:\msys64\usr\bin\bash.exe -lc "export MSYSTEM=UCRT64; source /etc/profile; cd '%CURRENT_DIR%' && make"
) else (
    clang++ -std=c++20 -O3 -Iinclude -Wall src/main.cpp src/build.cpp src/doctor.cpp src/fetch.cpp src/installer.cpp src/run.cpp src/setup.cpp -o xdev.exe -lws2_32
)

if %errorlevel% neq 0 (
    echo [ERROR] Compilation failed.
    exit /b %errorlevel%
)
echo [INFO] Build successful! Generated xdev.exe
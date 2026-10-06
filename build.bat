@echo off
REM Copyright (c) 2026 Manas Kamal Choudhary and XenevaOS Team
REM All rights reserved.

echo [INFO] Compiling xdev via MSYS2 UCRT64 environment...
C:\msys64\ucrt64.exe -defterm -no-start -shell bash -c "cd /d/Projects/xdev && make"
if %errorlevel% neq 0 (
    echo [ERROR] Compilation failed.
    exit /b %errorlevel%
)
echo [INFO] Build successful! Generated xdev.exe
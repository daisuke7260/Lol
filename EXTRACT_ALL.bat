@echo off
title LOL Auto BAN Tool V4 - Complete Extraction (Complete Working)

echo ========================================
echo LOL Auto BAN Tool V4 - Complete Extraction (Complete Working)
echo ========================================
echo.

echo [INFO] Verifying file extraction...

if exist "lol_auto_ban_v4_main.py" (
    echo [SUCCESS] Main file found
) else (
    echo [ERROR] Main file missing
    echo [INFO] Please extract the ZIP file completely
    pause
    exit /b 1
)

if exist "src\lol_auto_ban_v4_integrated.py" (
    echo [SUCCESS] V4 integrated module found
) else (
    echo [ERROR] V4 integrated module missing
    echo [INFO] Please extract the ZIP file completely
    pause
    exit /b 1
)

echo [SUCCESS] All files verified
echo [INFO] You can now run install.bat
pause

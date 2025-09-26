@echo off
title LOL Auto BAN Tool V4 - Uninstall (Complete Working)

echo ========================================
echo LOL Auto BAN Tool V4 - Uninstall (Complete Working)
echo ========================================
echo.

echo [WARNING] This will completely uninstall LOL Auto BAN Tool V4
set /p CONFIRM="Continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo [INFO] Uninstall cancelled
    pause
    exit /b 0
)

echo [INFO] Starting uninstall...

REM === Remove Files ===
del lol_auto_ban_v4_main.py >nul 2>&1
del *.bat >nul 2>&1
del *.md >nul 2>&1
del *.json >nul 2>&1

rmdir /S /Q src >nul 2>&1
rmdir /S /Q data >nul 2>&1
rmdir /S /Q config >nul 2>&1
rmdir /S /Q tests >nul 2>&1
rmdir /S /Q logs >nul 2>&1
rmdir /S /Q cache >nul 2>&1
rmdir /S /Q backups >nul 2>&1

echo [SUCCESS] Uninstall completed
pause

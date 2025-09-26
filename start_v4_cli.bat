@echo off
title LOL Auto BAN Tool V4 - CLI (Complete Working)

echo ========================================
echo LOL Auto BAN Tool V4 - CLI Startup (Complete Working)
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo [INFO] Starting in CLI mode...
python lol_auto_ban_v4_main.py --cli

if errorlevel 1 (
    echo [ERROR] CLI startup failed
    pause
)

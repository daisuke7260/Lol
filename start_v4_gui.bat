@echo off
title LOL Auto BAN Tool V4 - GUI (Complete Working)

echo ========================================
echo LOL Auto BAN Tool V4 - GUI Startup (Complete Working)
echo ========================================
echo.

REM === Environment Check ===
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo [INFO] Please run install.bat first
    pause
    exit /b 1
)

if not exist "lol_auto_ban_v4_main.py" (
    echo [ERROR] Main file not found
    pause
    exit /b 1
)

if not exist "src\lol_auto_ban_v4_integrated.py" (
    echo [ERROR] V4 integrated module not found
    pause
    exit /b 1
)

REM === Create Log Directory ===
if not exist "logs" mkdir logs

REM === Startup ===
echo [INFO] Starting LOL Auto BAN Tool V4 (Complete Working)...
echo.

python lol_auto_ban_v4_main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application failed to start
    pause
)

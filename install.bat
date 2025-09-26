@echo off
title LOL Auto BAN Tool V4 - Complete Working Installation

echo ========================================
echo LOL Auto BAN Tool V4 - Complete Working Installation
echo ========================================
echo.

REM === Check Administrator Rights ===
net session >nul 2>&1
if errorlevel 1 (
    echo [INFO] Requesting administrator rights...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo [INFO] Starting installation with administrator privileges...
echo.

REM === Python Installation ===
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Python not found. Installing Python 3.11...
    
    powershell -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python-3.11.9.exe' -UseBasicParsing } catch { exit 1 }"
    if errorlevel 1 (
        echo [ERROR] Failed to download Python
        pause
        exit /b 1
    )
    
    echo [INFO] Installing Python...
    start /wait "" "%TEMP%\python-3.11.9.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    timeout /t 10 >nul
    
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python installation failed
        pause
        exit /b 1
    )
) else (
    echo [SUCCESS] Python is already installed
)

REM === Install Dependencies ===
echo [INFO] Installing required packages...
python -m pip install --upgrade pip
python -m pip install requests opencv-python scikit-learn pillow mss numpy pandas matplotlib psutil

REM === Create Directories ===
echo [INFO] Creating runtime directories...
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache
if not exist "backups" mkdir backups

echo.
echo [SUCCESS] Installation completed successfully!
echo [INFO] You can now run start_v4_gui.bat to start the application
echo.
pause

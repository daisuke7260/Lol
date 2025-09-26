@echo off
title LOL Auto BAN Tool V4 - Diagnostics (Complete Working)

echo ========================================
echo LOL Auto BAN Tool V4 - System Diagnostics (Complete Working)
echo ========================================
echo.

echo [System Check]
python --version
echo.

echo [File Check]
if exist "lol_auto_ban_v4_main.py" (echo OK Main file) else (echo MISSING Main file)
if exist "src\lol_auto_ban_v4_integrated.py" (echo OK V4 integrated) else (echo MISSING V4 integrated)
if exist "src\lol_auto_ban_v4_gui.py" (echo OK GUI module) else (echo MISSING GUI module)
if exist "data\champions_data.json" (echo OK Champion data) else (echo MISSING Champion data)
if exist "config\v4_config.json" (echo OK Config file) else (echo MISSING Config file)
echo.

echo [Import Test]
python -c "import sys; sys.path.insert(0, 'src'); from lol_auto_ban_v4_integrated import LOLAutoBanV4System; print('OK V4 System Import')" 2>nul
if errorlevel 1 (echo FAILED V4 System Import) else (echo OK V4 System Import)

python -c "import sys; sys.path.insert(0, 'src'); from lol_auto_ban_v4_gui import LOLV4GUI; print('OK GUI Import')" 2>nul
if errorlevel 1 (echo FAILED GUI Import) else (echo OK GUI Import)
echo.

echo [League of Legends Check]
tasklist /FI "IMAGENAME eq LeagueClient.exe" 2>NUL | find /I /N "LeagueClient.exe" >NUL
if errorlevel 1 (echo WARNING LoL not running) else (echo OK LoL running)
echo.

echo Diagnostics completed
pause

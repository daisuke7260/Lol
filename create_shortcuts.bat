@echo off
title LOL Auto BAN Tool V4 - Create Shortcuts (Complete Working)

echo [INFO] Creating shortcuts...

set INSTALL_DIR=%~dp0

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\LOL Auto BAN Tool V4.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%start_v4_gui.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

echo [SUCCESS] Desktop shortcut created
pause

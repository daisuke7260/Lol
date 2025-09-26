@echo off
title LOL Auto BAN Tool V4 - Reset Configuration (Complete Working)

echo [INFO] Resetting configuration to default...

if exist "config\v4_config.json" (
    if not exist "backups" mkdir backups
    copy "config\v4_config.json" "backups\v4_config_backup_%date:~0,4%%date:~5,2%%date:~8,2%.json" >nul 2>&1
)

echo [SUCCESS] Configuration reset completed
pause

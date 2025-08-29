@echo off
echo Starting 5sim Auto-Sync Service...
echo.

cd /d "c:\Users\WDN\Desktop\virtual"

:start
echo [%DATE% %TIME%] Starting auto-sync daemon...
python auto_sync_daemon.py
echo [%DATE% %TIME%] Auto-sync daemon stopped. Restarting in 30 seconds...
timeout /t 30 /nobreak > nul
goto start

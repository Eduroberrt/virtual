@echo off
REM Start the auto-cancel daemon in the background

echo Starting Auto-Cancel Daemon...
echo.
echo This will automatically cancel expired rentals every minute.
echo The daemon will run in the background.
echo.
echo To stop the daemon, close this window or press Ctrl+C
echo.

cd /d "c:\Users\WDN\Desktop\virtual"
python auto_cancel_daemon.py

pause

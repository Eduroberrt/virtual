@echo off
REM Auto-cancel expired rentals every minute
REM Run this script continuously or set up as a scheduled task

:loop
echo [%date% %time%] Running auto-cancel check...
cd /d "c:\Users\WDN\Desktop\virtual"
python manage.py auto_cancel_expired

REM Wait 60 seconds before next check
timeout /t 60 /nobreak >nul
goto loop

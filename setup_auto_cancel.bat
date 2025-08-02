@echo off
REM Setup script to create Windows Task Scheduler job for auto-cancelling expired rentals

echo Setting up automatic rental cancellation service...
echo.

REM Create the scheduled task
schtasks /create ^
    /tn "VirtualSMS_AutoCancel" ^
    /tr "python.exe \"c:\Users\WDN\Desktop\virtual\manage.py\" auto_cancel_expired" ^
    /sc minute ^
    /mo 1 ^
    /st 00:00 ^
    /sd %date% ^
    /ru "SYSTEM" ^
    /f

if %errorlevel% equ 0 (
    echo.
    echo ✅ SUCCESS! Auto-cancel service has been set up.
    echo.
    echo The system will now automatically:
    echo - Run every 1 minute
    echo - Cancel rentals older than 5 minutes
    echo - Refund users automatically
    echo.
    echo To manage the task:
    echo - View: schtasks /query /tn "VirtualSMS_AutoCancel"
    echo - Stop:  schtasks /end /tn "VirtualSMS_AutoCancel"
    echo - Delete: schtasks /delete /tn "VirtualSMS_AutoCancel" /f
    echo.
    echo The service is now ACTIVE and running!
) else (
    echo.
    echo ❌ ERROR: Failed to create scheduled task.
    echo Try running this script as Administrator.
)

pause

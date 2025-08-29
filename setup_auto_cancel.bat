@echo off
REM DEPRECATED: Setup script to create Windows Task Scheduler job for auto-cancelling expired rentals
REM This functionality is no longer needed since we now sync with DaisySMS API

echo.
echo ⚠️  DEPRECATED SCRIPT ⚠️
echo.
echo This auto-cancel setup script is no longer needed.
echo We now sync expiration status with DaisySMS API instead of time-based expiration.
echo.
echo If you already have the VirtualSMS_AutoCancel task installed, you can remove it with:
echo schtasks /delete /tn "VirtualSMS_AutoCancel" /f
echo.
pause
exit /b 0
    echo.
    echo The service is now ACTIVE and running!
) else (
    echo.
    echo ❌ ERROR: Failed to create scheduled task.
    echo Try running this script as Administrator.
)

pause

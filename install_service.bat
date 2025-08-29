@echo off
REM DEPRECATED: Start the auto-cancel daemon as a background Windows service using NSSM
REM This functionality is no longer needed since we now sync with DaisySMS API

echo.
echo ⚠️  DEPRECATED SCRIPT ⚠️
echo.
echo This auto-cancel service installation is no longer needed.
echo We now sync expiration status with DaisySMS API instead of time-based expiration.
echo.
echo If you already have the VirtualSMS-AutoCancel service installed, you can remove it with:
echo nssm remove "VirtualSMS-AutoCancel" confirm
echo.
pause
exit /b 0

REM Install the service
nssm install "VirtualSMS-AutoCancel" python "c:\Users\WDN\Desktop\virtual\auto_cancel_daemon.py"
nssm set "VirtualSMS-AutoCancel" AppDirectory "c:\Users\WDN\Desktop\virtual"
nssm set "VirtualSMS-AutoCancel" DisplayName "Virtual SMS Auto Cancel"
nssm set "VirtualSMS-AutoCancel" Description "Automatically cancels expired SMS rentals and refunds users"
nssm set "VirtualSMS-AutoCancel" Start SERVICE_AUTO_START

REM Start the service
nssm start "VirtualSMS-AutoCancel"

if %errorlevel% equ 0 (
    echo.
    echo ✅ SUCCESS! Auto-Cancel service is now running!
    echo.
    echo The service will:
    echo - Start automatically when Windows boots
    echo - Run continuously in the background
    echo - Check for expired rentals every minute
    echo - Automatically cancel and refund users
    echo.
    echo Service Management:
    echo - Stop:    nssm stop "VirtualSMS-AutoCancel"
    echo - Start:   nssm start "VirtualSMS-AutoCancel"
    echo - Remove:  nssm remove "VirtualSMS-AutoCancel" confirm
    echo - Status:  nssm status "VirtualSMS-AutoCancel"
    echo.
) else (
    echo.
    echo ❌ ERROR: Failed to install/start service
)

pause

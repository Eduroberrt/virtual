@echo off
REM Start the auto-cancel daemon as a background Windows service using NSSM

echo Setting up Auto-Cancel as Windows Service...
echo.

REM Check if NSSM is available
where nssm >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: NSSM ^(Non-Sucking Service Manager^) is not installed.
    echo.
    echo Please download NSSM from: https://nssm.cc/download
    echo Extract nssm.exe to a folder in your PATH
    echo.
    pause
    exit /b 1
)

echo Installing VirtualSMS Auto-Cancel Service...

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

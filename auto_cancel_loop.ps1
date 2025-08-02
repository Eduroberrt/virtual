# PowerShell script to auto-cancel expired rentals every minute
# Run this in PowerShell: .\auto_cancel_loop.ps1

$scriptPath = "c:\Users\WDN\Desktop\virtual"
Set-Location $scriptPath

Write-Host "Starting auto-cancel service..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow

while ($true) {
    try {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-Host "[$timestamp] Running auto-cancel check..." -ForegroundColor Cyan
        
        & python manage.py auto_cancel_expired
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[$timestamp] Auto-cancel completed successfully" -ForegroundColor Green
        } else {
            Write-Host "[$timestamp] Auto-cancel had errors (exit code: $LASTEXITCODE)" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "[$timestamp] Error running auto-cancel: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Wait 60 seconds before next check
    Start-Sleep -Seconds 60
}

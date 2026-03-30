@echo off
REM Check for expired MTelSMS rentals and issue automatic refunds
REM Run this every 5-10 minutes via Windows Task Scheduler

cd /d "%~dp0"
python manage.py check_expired_rentals --limit 100

REM Log completion
echo [%date% %time%] Expired rentals check completed >> logs\expired_check.log

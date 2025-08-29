@echo off
REM Windows batch file to run auto-refund
REM Save as: auto_refund.bat

cd /d "c:\Users\WDN\Desktop\virtual"
python manage.py auto_refund_expired_fivesim

REM Log the execution
echo %date% %time% - Auto refund executed >> refund_log.txt

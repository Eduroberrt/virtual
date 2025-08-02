"""
Windows Service for automatically cancelling expired SMS rentals
Install: python rental_service.py install
Start: python rental_service.py start
Stop: python rental_service.py stop
Remove: python rental_service.py remove
"""

import win32service
import win32serviceutil
import win32event
import win32api
import servicemanager
import logging
import time
import sys
import os
from threading import Thread

# Add Django project to Python path
sys.path.append(r'c:\Users\WDN\Desktop\virtual')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')

import django
django.setup()

from django.core.management import call_command

class RentalCancelService(win32serviceutil.ServiceFramework):
    _svc_name_ = "VirtualSMSAutoCancel"
    _svc_display_name_ = "Virtual SMS Auto Cancel Service"
    _svc_description_ = "Automatically cancels expired SMS rentals and refunds users"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        """Main service loop - runs auto_cancel_expired every 60 seconds"""
        logging.basicConfig(
            filename=r'c:\Users\WDN\Desktop\virtual\logs\auto_cancel_service.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        logging.info("Auto-cancel service started")
        
        while self.is_alive:
            try:
                # Run the auto-cancel command
                logging.info("Running auto_cancel_expired command...")
                call_command('auto_cancel_expired')
                logging.info("Auto_cancel_expired completed successfully")
                
            except Exception as e:
                logging.error(f"Error running auto_cancel_expired: {str(e)}")
            
            # Wait 60 seconds or until service stop is requested
            result = win32event.WaitForSingleObject(self.hWaitStop, 60000)  # 60 seconds
            if result == win32event.WAIT_OBJECT_0:
                break
        
        logging.info("Auto-cancel service stopped")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(RentalCancelService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(RentalCancelService)

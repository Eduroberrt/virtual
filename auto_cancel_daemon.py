"""
Background daemon for automatically cancelling expired SMS rentals
This runs continuously in the background and checks every minute
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add Django project to Python path
project_path = r'c:\Users\WDN\Desktop\virtual'
sys.path.append(project_path)
os.chdir(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')

import django
django.setup()

from django.core.management import call_command

# Setup logging - FILE ONLY to avoid Windows console Unicode issues
log_file = r'c:\Users\WDN\Desktop\virtual\logs\auto_cancel_daemon.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)

# Also create a simple print function that won't crash
def safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback to ASCII-only output
        print(message.encode('ascii', 'replace').decode('ascii'))

logger = logging.getLogger(__name__)

def main():
    """Main daemon loop"""
    safe_print("Auto-cancel daemon started")
    safe_print("Will check for expired rentals every 60 seconds")
    safe_print("Press Ctrl+C to stop")
    safe_print(f"Logging to: {log_file}")
    
    logger.info("Auto-cancel daemon started")
    logger.info("Will check for expired rentals every 60 seconds")
    
    try:
        while True:
            try:
                start_time = time.time()
                logger.info("Checking for expired rentals...")
                safe_print("Checking for expired rentals...")
                
                # Run the auto-cancel command
                call_command('auto_cancel_expired')
                
                execution_time = time.time() - start_time
                logger.info(f"Check completed in {execution_time:.2f} seconds")
                safe_print(f"Check completed in {execution_time:.2f} seconds")
                
            except KeyboardInterrupt:
                logger.info("Received stop signal")
                safe_print("Received stop signal")
                break
            except Exception as e:
                logger.error(f"Error during auto-cancel check: {str(e)}")
                safe_print(f"Error during auto-cancel check: {str(e)}")
            
            # Wait 60 seconds before next check
            logger.info("Waiting 60 seconds until next check...")
            safe_print("Waiting 60 seconds until next check...")
            time.sleep(60)
    
    except KeyboardInterrupt:
        pass
    
    logger.info("Auto-cancel daemon stopped")
    safe_print("Auto-cancel daemon stopped")

if __name__ == '__main__':
    main()

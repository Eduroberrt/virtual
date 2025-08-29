"""
DEPRECATED: Background daemon for automatically cancelling expired SMS rentals

This daemon is no longer needed because rental expiration now syncs with DaisySMS API status
instead of using time-based expiration. Use the DaisySMS polling system in dashboard-2.html instead.
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add Django project to Python path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)
os.chdir(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')

import django
django.setup()

# Setup logging - FILE ONLY to avoid Windows console Unicode issues
log_file = os.path.join(project_path, 'logs', 'auto_cancel_daemon.log')
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
    """DEPRECATED: This daemon is no longer needed"""
    safe_print("DEPRECATED: Auto-cancel daemon is no longer needed")
    safe_print("Rental expiration now syncs with DaisySMS API status")
    safe_print("Use the DaisySMS polling system in dashboard-2.html instead")
    safe_print("This daemon will now exit")
    
    logger.info("DEPRECATED: Auto-cancel daemon started but immediately exiting")
    logger.info("Rental expiration now syncs with DaisySMS API status")
    return

if __name__ == '__main__':
    main()

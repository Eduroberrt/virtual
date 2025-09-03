"""
Daisy SMS Status Sync Daemon for Production (PythonAnywhere)
This script runs continuously and syncs Daisy SMS rental statuses
"""
import os
import sys
import django
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from django.core.management import call_command

# Setup logging with rotation
logging.basicConfig(
    level=logging.WARNING,  # Less verbose for production
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/daisy_sync_daemon.log',
            maxBytes=5*1024*1024,  # 5MB per file
            backupCount=2          # Keep 2 backups = 15MB max total
        )
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main daemon loop for production"""
    logger.info("Daisy SMS Status Sync Daemon started (Production)")
    logger.info("Will check Daisy SMS status every 60 seconds")
    
    try:
        while True:
            try:
                start_time = time.time()
                logger.info("Syncing Daisy SMS rental statuses...")
                
                # Run the sync command
                call_command('sync_daisy_status')
                
                execution_time = time.time() - start_time
                logger.info(f"Sync completed in {execution_time:.2f} seconds")
                
            except KeyboardInterrupt:
                logger.info("Received stop signal")
                break
            except Exception as e:
                logger.error(f"Error during Daisy SMS sync: {str(e)}")
            
            # Wait 60 seconds before next check (production interval)
            logger.info("Waiting 60 seconds until next check...")
            time.sleep(60)
    
    except KeyboardInterrupt:
        pass
    
    logger.info("Daisy SMS Status Sync Daemon stopped")

if __name__ == '__main__':
    main()

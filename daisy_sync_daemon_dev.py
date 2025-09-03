"""
Daisy SMS Status Sync Daemon for Development
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

# Setup logging with rotation (more verbose for dev)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/daisy_sync_daemon.log',
            maxBytes=10*1024*1024,  # 10MB per file for dev
            backupCount=3           # Keep 3 backups = 40MB max total
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def safe_print(message):
    """Safe print function that handles Unicode characters"""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode('ascii', 'ignore').decode('ascii'))

def main():
    """Main daemon loop"""
    safe_print("Daisy SMS Status Sync Daemon started (Development)")
    safe_print("Will check Daisy SMS status every 30 seconds")
    safe_print("Press Ctrl+C to stop")
    safe_print("Logging to: logs/daisy_sync_daemon.log")
    
    logger.info("Daisy SMS Status Sync Daemon started (Development)")
    logger.info("Will check Daisy SMS status every 30 seconds")
    
    try:
        while True:
            try:
                start_time = time.time()
                logger.info("Syncing Daisy SMS rental statuses...")
                safe_print("Syncing Daisy SMS rental statuses...")
                
                # Run the sync command
                call_command('sync_daisy_status')
                
                execution_time = time.time() - start_time
                logger.info(f"Sync completed in {execution_time:.2f} seconds")
                safe_print(f"Sync completed in {execution_time:.2f} seconds")
                
            except KeyboardInterrupt:
                logger.info("Received stop signal")
                safe_print("Received stop signal")
                break
            except Exception as e:
                logger.error(f"Error during Daisy SMS sync: {str(e)}")
                safe_print(f"Error during Daisy SMS sync: {str(e)}")
            
            # Wait 30 seconds before next check (faster for development)
            logger.info("Waiting 30 seconds until next check...")
            safe_print("Waiting 30 seconds until next check...")
            time.sleep(30)
    
    except KeyboardInterrupt:
        pass
    
    logger.info("Daisy SMS Status Sync Daemon stopped")
    safe_print("Daisy SMS Status Sync Daemon stopped")

if __name__ == '__main__':
    main()

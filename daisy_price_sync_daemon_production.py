"""
DaisySMS Price Sync Daemon for Production (PythonAnywhere)
This script runs continuously and syncs services and prices from DaisySMS API
"""
import os
import sys
import django
import time
import logging
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from django.core.management import call_command

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daisy_price_sync_daemon.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main daemon loop for production"""
    logger.info("DaisySMS Price Sync Daemon started (Production)")
    logger.info("Will sync services and prices every 2 hours")
    
    try:
        # Do an initial sync on startup
        try:
            logger.info("Performing initial price sync...")
            call_command('sync_daisy_prices')
            logger.info("Initial sync completed successfully")
        except Exception as e:
            logger.error(f"Initial sync failed: {str(e)}")
        
        while True:
            try:
                start_time = time.time()
                logger.info("Starting scheduled DaisySMS price sync...")
                
                # Run the sync command
                call_command('sync_daisy_prices')
                
                execution_time = time.time() - start_time
                logger.info(f"Price sync completed in {execution_time:.2f} seconds")
                
            except KeyboardInterrupt:
                logger.info("Received stop signal")
                break
            except Exception as e:
                logger.error(f"Error during DaisySMS price sync: {str(e)}")
            
            # Wait 2 hours before next sync (7200 seconds)
            wait_hours = 2
            logger.info(f"Waiting {wait_hours} hours until next sync...")
            time.sleep(wait_hours * 3600)
    
    except KeyboardInterrupt:
        pass
    
    logger.info("DaisySMS Price Sync Daemon stopped")

if __name__ == '__main__':
    main()

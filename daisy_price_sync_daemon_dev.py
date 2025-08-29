"""
DaisySMS Price Sync Daemon for Development
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
        logging.FileHandler('logs/daisy_price_sync_daemon.log'),
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
    safe_print("DaisySMS Price Sync Daemon started (Development)")
    safe_print("Will sync services and prices every 30 minutes")
    safe_print("Press Ctrl+C to stop")
    safe_print("Logging to: logs/daisy_price_sync_daemon.log")
    
    logger.info("DaisySMS Price Sync Daemon started (Development)")
    logger.info("Will sync services and prices every 30 minutes")
    
    try:
        # Do an initial sync on startup
        try:
            safe_print("Performing initial price sync...")
            logger.info("Performing initial price sync...")
            call_command('sync_daisy_prices', verbosity=2)
            safe_print("Initial sync completed successfully")
            logger.info("Initial sync completed successfully")
        except Exception as e:
            safe_print(f"Initial sync failed: {str(e)}")
            logger.error(f"Initial sync failed: {str(e)}")
        
        while True:
            try:
                start_time = time.time()
                logger.info("Starting scheduled DaisySMS price sync...")
                safe_print("Starting scheduled DaisySMS price sync...")
                
                # Run the sync command with verbose output
                call_command('sync_daisy_prices', verbosity=1)
                
                execution_time = time.time() - start_time
                logger.info(f"Price sync completed in {execution_time:.2f} seconds")
                safe_print(f"Price sync completed in {execution_time:.2f} seconds")
                
            except KeyboardInterrupt:
                logger.info("Received stop signal")
                safe_print("Received stop signal")
                break
            except Exception as e:
                logger.error(f"Error during DaisySMS price sync: {str(e)}")
                safe_print(f"Error during DaisySMS price sync: {str(e)}")
            
            # Wait 30 minutes before next sync (1800 seconds)
            wait_minutes = 30
            logger.info(f"Waiting {wait_minutes} minutes until next sync...")
            safe_print(f"Waiting {wait_minutes} minutes until next sync...")
            
            # Sleep in chunks so we can respond to Ctrl+C faster
            for i in range(wait_minutes * 60):
                time.sleep(1)
                if i % 300 == 0 and i > 0:  # Every 5 minutes
                    remaining_minutes = (wait_minutes * 60 - i) // 60
                    safe_print(f"Next sync in {remaining_minutes} minutes...")
    
    except KeyboardInterrupt:
        pass
    
    logger.info("DaisySMS Price Sync Daemon stopped")
    safe_print("DaisySMS Price Sync Daemon stopped")

if __name__ == '__main__':
    main()

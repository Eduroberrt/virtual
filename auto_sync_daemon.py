"""
Auto-sync daemon for 5sim services and pricing
This script runs continuously and syncs data at specified intervals
"""
import os
import sys
import django
import time
import logging
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from django.core.management import call_command
from django.conf import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_sync.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AutoSyncDaemon:
    def __init__(self):
        self.sync_interval_hours = getattr(settings, 'FIVESIM_SYNC_INTERVAL_HOURS', 6)  # Default: 6 hours
        self.price_update_interval_hours = getattr(settings, 'FIVESIM_PRICE_UPDATE_INTERVAL_HOURS', 1)  # Default: 1 hour
        self.last_full_sync = None
        self.last_price_update = None

    def should_run_full_sync(self):
        """Check if it's time for a full service sync"""
        if not self.last_full_sync:
            return True
        
        time_since_sync = datetime.now() - self.last_full_sync
        return time_since_sync >= timedelta(hours=self.sync_interval_hours)

    def should_run_price_update(self):
        """Check if it's time for a price update"""
        if not self.last_price_update:
            return True
        
        time_since_update = datetime.now() - self.last_price_update
        return time_since_update >= timedelta(hours=self.price_update_interval_hours)

    def run_full_sync(self):
        """Run full service sync"""
        try:
            logger.info("Starting full service sync...")
            call_command('sync_fivesim_services', '--force')
            self.last_full_sync = datetime.now()
            logger.info("Full service sync completed successfully")
        except Exception as e:
            logger.error(f"Full service sync failed: {str(e)}")

    def run_price_update(self):
        """Run price-only update"""
        try:
            logger.info("Starting price update...")
            call_command('update_fivesim_prices')
            self.last_price_update = datetime.now()
            logger.info("Price update completed successfully")
        except Exception as e:
            logger.error(f"Price update failed: {str(e)}")

    def run(self):
        """Main daemon loop"""
        logger.info("Starting 5sim Auto-Sync Daemon...")
        logger.info(f"Full sync interval: {self.sync_interval_hours} hours")
        logger.info(f"Price update interval: {self.price_update_interval_hours} hours")

        while True:
            try:
                if self.should_run_full_sync():
                    self.run_full_sync()
                elif self.should_run_price_update():
                    self.run_price_update()

                # Sleep for 10 minutes before checking again
                time.sleep(600)

            except KeyboardInterrupt:
                logger.info("Auto-sync daemon stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in daemon: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying

if __name__ == '__main__':
    daemon = AutoSyncDaemon()
    daemon.run()

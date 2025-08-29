"""
Task for PythonAnywhere to sync DaisySMS prices
Add this to your PythonAnywhere Tasks tab to run every 2 hours
"""

# Set the command: python3.11 /home/yourusername/mysite/pythonanywhere_daisy_price_sync_task.py

import os
import sys
import django

# Setup Django environment
sys.path.append('/home/yourusername/mysite')  # Update with your actual path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual.settings')
django.setup()

from django.core.management import call_command
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/yourusername/mysite/logs/daisy_price_sync_daemon.log')  # Update with your actual path
    ]
)

logger = logging.getLogger(__name__)

try:
    logger.info("PythonAnywhere DaisySMS price sync task started")
    call_command('sync_daisy_prices')
    logger.info("PythonAnywhere DaisySMS price sync task completed")
except Exception as e:
    logger.error(f"PythonAnywhere DaisySMS price sync task failed: {str(e)}")

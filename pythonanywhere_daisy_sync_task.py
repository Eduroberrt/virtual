"""
Task for PythonAnywhere to run Daisy SMS sync daemon
Add this to your PythonAnywhere Tasks tab
"""

# Set the command: python3.11 /home/yourusername/mysite/daisy_sync_daemon_production.py

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
        logging.FileHandler('/home/yourusername/mysite/logs/daisy_sync_daemon.log')  # Update with your actual path
    ]
)

logger = logging.getLogger(__name__)

try:
    logger.info("PythonAnywhere Daisy SMS sync task started")
    call_command('sync_daisy_status')
    logger.info("PythonAnywhere Daisy SMS sync task completed")
except Exception as e:
    logger.error(f"PythonAnywhere Daisy SMS sync task failed: {str(e)}")
